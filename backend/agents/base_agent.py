"""Abstract base class for all LeafyMind specialist agents."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from services.knowledge_base import KnowledgeBase
from services.llm_provider import LLMService

logger = logging.getLogger(__name__)

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
MAX_INPUT_LENGTH = 8000


class BaseAgent(ABC):
    """Base class providing shared LLM, knowledge-base, and utility methods."""

    agent_name: str = "BaseAgent"

    def __init__(self, llm_service: LLMService, knowledge_base: KnowledgeBase) -> None:
        self._llm = llm_service
        self._kb = knowledge_base

    @abstractmethod
    async def process(self, payload: dict[str, Any], session_context: dict[str, Any]) -> dict[str, Any]:
        """Process a request and return an agent-specific result dict."""

    def _build_messages(
        self,
        system_prompt: str,
        conversation_history: list[dict[str, Any]],
        user_message: str,
    ) -> list[BaseMessage]:
        """Build a LangChain message list from system prompt, history, and latest user turn."""
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        for turn in conversation_history:
            role = turn.get("role", "user")
            content = self._sanitize_input(str(turn.get("content", "")))
            if not content:
                continue
            if role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        messages.append(HumanMessage(content=self._sanitize_input(user_message)))
        return messages

    def _sanitize_input(self, text: str) -> str:
        """Strip HTML tags and cap input length before sending to the LLM."""
        if not text:
            return ""
        cleaned = HTML_TAG_PATTERN.sub("", text).strip()
        return cleaned[:MAX_INPUT_LENGTH]

    def _log_agent_call(
        self,
        agent_name: str,
        input_summary: str,
        output_summary: str,
    ) -> None:
        """Log a concise summary of an agent invocation."""
        logger.info(
            "Agent [%s] input=%s output=%s",
            agent_name,
            input_summary[:200],
            output_summary[:200],
        )
