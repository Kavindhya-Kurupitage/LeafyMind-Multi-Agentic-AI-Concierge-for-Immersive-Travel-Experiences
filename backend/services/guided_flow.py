"""Orchestrate scripted guided steps for Agent Hub threads."""

from __future__ import annotations

import uuid
from typing import Any

from agents.guided_steps import (
    GUIDED_AGENTS,
    GuidedStepDef,
    apply_preference_answer,
    apply_profile_answer,
    build_turn_payload,
    format_answer_label,
    get_step,
    get_steps,
    is_generate_trigger,
    is_profile_complete,
    next_step_index,
    total_steps,
)
from agents.profile_builder import ProfileBuilderAgent
from models.agent_thread import AgentThread
from models.enums import AgentThreadStatus
from models.guest_profile import GuestProfile
from services.specialist_interview import OPTIONAL_PLANNING_AGENTS


def _get_step_index(ctx: dict[str, Any]) -> int:
    return int(ctx.get("guided_step_index") or 0)


def _set_step_index(ctx: dict[str, Any], index: int) -> None:
    ctx["guided_step_index"] = index


class GuidedFlowResult:
    """Result of processing one guided answer or initial load."""

    def __init__(
        self,
        *,
        guided_turn: dict[str, Any] | None = None,
        user_content: str = "",
        assistant_content: str = "",
        profile: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
        ready_to_generate: bool = False,
        profile_complete: bool = False,
        survey_complete: bool = False,
        feedback_ratings: dict[str, Any] | None = None,
        advance_index: bool = True,
    ) -> None:
        self.guided_turn = guided_turn
        self.user_content = user_content
        self.assistant_content = assistant_content
        self.profile = profile
        self.preferences = preferences
        self.ready_to_generate = ready_to_generate
        self.profile_complete = profile_complete
        self.survey_complete = survey_complete
        self.feedback_ratings = feedback_ratings or {}
        self.advance_index = advance_index


class GuidedFlowService:
    """State machine for hub agent guided interviews."""

    @staticmethod
    def supports(agent_id: str) -> bool:
        return agent_id in GUIDED_AGENTS

    def get_initial_turn(self, thread: AgentThread) -> GuidedFlowResult:
        """First guided turn when opening a thread (no user message yet)."""
        agent_id = thread.agent_id
        ctx = dict(thread.context or {})
        index = _get_step_index(ctx)
        steps = get_steps(agent_id)
        if not steps:
            return GuidedFlowResult(assistant_content="How can I help?")
        if index >= len(steps):
            index = len(steps) - 1
        step = steps[index]
        profile = thread.get_guest_profile()
        prefs = thread.get_agent_preferences()
        turn = build_turn_payload(agent_id, step, profile, prefs, step_index=index)
        intro = step.intro
        return GuidedFlowResult(
            guided_turn=turn,
            assistant_content=f"{intro}\n\n{turn['question']}",
            profile=profile,
            preferences=prefs,
        )

    def process_answer(
        self,
        thread: AgentThread,
        *,
        step_id: str | None,
        selected: list[str],
        free_text: str | None,
        raw_message: str,
    ) -> GuidedFlowResult:
        """Apply guest answer and return next turn or generate signal."""
        agent_id = thread.agent_id
        ctx = dict(thread.context or {})
        index = _get_step_index(ctx)
        steps = get_steps(agent_id)
        if not steps:
            return GuidedFlowResult(user_content=raw_message, assistant_content="")

        current_step = steps[min(index, len(steps) - 1)]
        if step_id:
            resolved = get_step(agent_id, step_id)
            if resolved:
                current_step = resolved
                index = next(
                    (i for i, s in enumerate(steps) if s.step_id == step_id),
                    index,
                )

        profile = thread.get_guest_profile()
        prefs = thread.get_agent_preferences()

        if current_step.allow_skip and "skip" in selected:
            pass
        elif agent_id == "profile_builder":
            profile = apply_profile_answer(profile, current_step, selected, free_text)
        elif agent_id == "feedback_collector":
            prefs = apply_preference_answer(prefs, current_step, selected, free_text, profile)
        else:
            prefs = apply_preference_answer(prefs, current_step, selected, free_text, profile)

        user_label = format_answer_label(current_step, selected, free_text) or raw_message
        ready = is_generate_trigger(current_step, selected)
        survey_done = False
        prof_complete = False

        if agent_id == "profile_builder" and current_step.step_id == "profile_confirm":
            if "confirm" in selected:
                prof_complete = is_profile_complete(profile)
                if prof_complete:
                    thread.status = AgentThreadStatus.COMPLETED
                if not prof_complete:
                    index = 0
                    _set_step_index(ctx, index)
                    thread.context = ctx
                    thread.set_guest_profile(profile)
                    step = steps[0]
                    turn = build_turn_payload(agent_id, step, profile, prefs, step_index=index)
                    return GuidedFlowResult(
                        guided_turn=turn,
                        user_content=user_label,
                        assistant_content=(
                            "Some required fields are still missing — let's fill them in.\n\n"
                            f"{turn['question']}"
                        ),
                        profile=profile,
                        preferences=prefs,
                        advance_index=False,
                    )
                return GuidedFlowResult(
                    user_content=user_label,
                    assistant_content=(
                        "Your travel profile is complete. Return to the dashboard "
                        "to use Package, Food, and Itinerary specialists."
                    ),
                    profile=profile,
                    preferences=prefs,
                    profile_complete=prof_complete,
                    advance_index=False,
                )
            index = 0
            _set_step_index(ctx, index)
            thread.context = ctx
            thread.set_guest_profile(profile)
            thread.set_agent_preferences(prefs)
            step = steps[0]
            turn = build_turn_payload(agent_id, step, profile, prefs, step_index=index)
            return GuidedFlowResult(
                guided_turn=turn,
                user_content=user_label,
                assistant_content=f"Let's adjust your profile.\n\n{turn['question']}",
                profile=profile,
                preferences=prefs,
            )

        if agent_id == "feedback_collector" and current_step.step_id == "feedback_comment":
            survey_done = True
            ratings = {
                k: prefs.get(k)
                for k in (
                    "package_rating",
                    "food_rating",
                    "itinerary_rating",
                    "ai_helpfulness_rating",
                )
                if prefs.get(k) is not None
            }
            return GuidedFlowResult(
                user_content=user_label,
                assistant_content="Thank you — your feedback has been recorded.",
                profile=profile,
                preferences=prefs,
                survey_complete=True,
                feedback_ratings=ratings,
                advance_index=False,
            )

        if ready and agent_id in OPTIONAL_PLANNING_AGENTS:
            thread.set_interview_phase("generate")
            thread.set_guest_profile(profile)
            thread.set_agent_preferences(prefs)
            _set_step_index(ctx, index)
            thread.context = ctx
            return GuidedFlowResult(
                user_content=user_label,
                assistant_content="",
                profile=profile,
                preferences=prefs,
                ready_to_generate=True,
                advance_index=False,
            )

        new_index = next_step_index(agent_id, index, current_step, selected)
        if new_index >= len(steps):
            new_index = len(steps) - 1
        _set_step_index(ctx, new_index)
        thread.context = ctx
        thread.set_guest_profile(profile)
        thread.set_agent_preferences(prefs)

        next_step = steps[new_index]
        turn = build_turn_payload(agent_id, next_step, profile, prefs, step_index=new_index)
        return GuidedFlowResult(
            guided_turn=turn,
            user_content=user_label,
            assistant_content=f"{next_step.intro}\n\n{turn['question']}",
            profile=profile,
            preferences=prefs,
        )
