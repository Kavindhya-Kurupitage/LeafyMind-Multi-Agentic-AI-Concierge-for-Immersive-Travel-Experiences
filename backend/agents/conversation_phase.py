"""Concierge conversation phases for the orchestrator."""

from enum import Enum


class ConversationPhase(str, Enum):
    """Phased guest journey through specialist agents."""

    GREETING = "GREETING"
    PROFILING = "PROFILING"
    CONTACT_COLLECTION = "CONTACT_COLLECTION"
    RECOMMENDING = "RECOMMENDING"
    ITINERARY = "ITINERARY"
    FOLLOWUP = "FOLLOWUP"
    FEEDBACK = "FEEDBACK"
    ESCALATED = "ESCALATED"
