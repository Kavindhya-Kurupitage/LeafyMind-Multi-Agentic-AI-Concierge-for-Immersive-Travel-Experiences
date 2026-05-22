"""Agent Hub registry — metadata for each specialist agent."""

from dataclasses import dataclass
from typing import Literal

AgentId = Literal[
    "profile_builder",
    "package_recommender",
    "food_guide",
    "itinerary_planner",
    "feedback_collector",
    "concierge",
]


@dataclass(frozen=True)
class AgentDefinition:
    """Public metadata exposed to the guest dashboard."""

    id: AgentId
    name: str
    tagline: str
    description: str
    icon: str
    color: str
    capabilities: tuple[str, ...]
    artifact_kind: str | None


AGENT_REGISTRY: dict[str, AgentDefinition] = {
    "profile_builder": AgentDefinition(
        id="profile_builder",
        name="Profile Builder",
        tagline="Tell us about your dream trip",
        description=(
            "Build your travel profile through warm conversation — dates, style, "
            "group, budget, and dietary needs — so every recommendation fits you."
        ),
        icon="🌿",
        color="from-forest-light to-forest",
        capabilities=("Preference extraction", "Contact details", "Trip context"),
        artifact_kind="profile",
    ),
    "package_recommender": AgentDefinition(
        id="package_recommender",
        name="Package Planner",
        tagline="Find your perfect cabana stay",
        description=(
            "Compare Leafy Cave packages matched to your profile with honest pricing "
            "and personalised reasons each stay suits you."
        ),
        icon="🏡",
        color="from-gold/90 to-gold",
        capabilities=("Package matching", "Business rules", "USD pricing"),
        artifact_kind="packages",
    ),
    "food_guide": AgentDefinition(
        id="food_guide",
        name="Food Guide",
        tagline="Taste Sri Lanka with confidence",
        description=(
            "Discover must-try dishes, spice guidance, and safe starters — with cultural "
            "notes written for international guests."
        ),
        icon="🍛",
        color="from-forest-muted to-forest-dark",
        capabilities=("Dish discovery", "Dietary filters", "Cultural notes"),
        artifact_kind="food",
    ),
    "itinerary_planner": AgentDefinition(
        id="itinerary_planner",
        name="Itinerary Planner",
        tagline="Map your daily adventures",
        description=(
            "Day-by-day plans blending curated attractions and live discoveries near "
            "Leafy Cave — temples, waterfalls, wildlife, and more."
        ),
        icon="🗺️",
        color="from-forest to-forest-dark",
        capabilities=("Day plans", "Attraction data", "Cost estimates"),
        artifact_kind="itinerary",
    ),
    "feedback_collector": AgentDefinition(
        id="feedback_collector",
        name="Feedback Collector",
        tagline="Share your stay experience",
        description=(
            "A gentle post-stay conversation to capture ratings, highlights, and "
            "suggestions that help Leafy Cave welcome future guests."
        ),
        icon="✨",
        color="from-cream-dark to-forest-light/80",
        capabilities=("Ratings", "Sentiment", "Owner alerts"),
        artifact_kind="feedback",
    ),
    "concierge": AgentDefinition(
        id="concierge",
        name="Full Concierge",
        tagline="End-to-end journey in one flow",
        description=(
            "The complete LeafyMind journey — profiling, recommendations, itinerary, "
            "and follow-up — coordinated across all specialists."
        ),
        icon="🛎️",
        color="from-gold via-forest-light to-forest",
        capabilities=("Multi-agent routing", "Escalation", "Full journey"),
        artifact_kind="journey",
    ),
}


def get_agent(agent_id: str) -> AgentDefinition | None:
    """Return agent metadata if registered."""
    return AGENT_REGISTRY.get(agent_id)


def list_agents() -> list[AgentDefinition]:
    """Return all agents for the hub dashboard."""
    return list(AGENT_REGISTRY.values())
