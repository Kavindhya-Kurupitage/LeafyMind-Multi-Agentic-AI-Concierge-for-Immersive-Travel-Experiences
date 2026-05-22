"""LLM prompt-injection sanitisation for guest-supplied text."""

import logging
import re

logger = logging.getLogger(__name__)

MAX_USER_INPUT_LENGTH = 2000

_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I), "[filtered]"),
    (re.compile(r"disregard\s+(all\s+)?(previous|prior)\s+instructions?", re.I), "[filtered]"),
    (re.compile(r"forget\s+(everything|all)\s+(you\s+)?(know|were told)", re.I), "[filtered]"),
    (re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.I), "[filtered] "),
    (re.compile(r"act\s+as\s+(a|an)\s+", re.I), "[filtered] "),
    (re.compile(r"system\s*:", re.I), "[filtered]:"),
    (re.compile(r"assistant\s*:", re.I), "[filtered]:"),
    (re.compile(r"user\s*:", re.I), "[filtered]:"),
    (re.compile(r"<\s*/?\s*(system|assistant|user|instruction|prompt)\s*>", re.I), ""),
    (re.compile(r"\[INST\]|\[/INST\]", re.I), ""),
    (re.compile(r"```\s*system", re.I), "``` [filtered]"),
]

_DETECTION_PATTERNS: list[re.Pattern[str]] = [p for p, _ in _INJECTION_PATTERNS] + [
    re.compile(r"<\s*script", re.I),
    re.compile(r"jailbreak", re.I),
]


def _detect_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _DETECTION_PATTERNS)


def sanitize_user_input(text: str) -> str:
    """
    Sanitise guest text before it reaches any LLM prompt.

    - Enforces 2000 character hard limit
    - Strips/neutralises common injection phrases and role markers
    - Logs WARNING when suspicious patterns are detected
    """
    if not text:
        return ""

    cleaned = text.strip()
    if len(cleaned) > MAX_USER_INPUT_LENGTH:
        cleaned = cleaned[:MAX_USER_INPUT_LENGTH]

    if _detect_injection(cleaned):
        logger.warning(
            "Possible prompt-injection pattern detected in user input (length=%d)",
            len(cleaned),
        )

    for pattern, replacement in _INJECTION_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)

    # Remove remaining XML-like tags
    cleaned = re.sub(r"<[^>]+>", "", cleaned)

    return cleaned.strip()
