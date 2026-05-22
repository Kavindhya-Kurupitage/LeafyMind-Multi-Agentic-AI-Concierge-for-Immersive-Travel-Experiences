"""Provider-agnostic LangChain LLM and embeddings service — all AI calls go through here."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from config import LLMProvider as ConfigLLMProvider
from config import settings

logger = logging.getLogger(__name__)

# Re-export for convenience (canonical enum lives in config.py)
LLMProvider = ConfigLLMProvider

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0

# Provider-specific chat models (per LeafyMind specification)
CHAT_MODELS = {
    LLMProvider.GEMINI: "gemini-1.5-flash",
    LLMProvider.GROQ: "llama-3.1-8b-instant",
    LLMProvider.OPENAI: "gpt-4o-mini",
}

CHAT_TEMPERATURE = 0.7


def _resolve_chat_model(provider: LLMProvider) -> str:
    """Use LLM_MODEL from .env when set, otherwise the provider default."""
    configured = (settings.llm_model or "").strip()
    if configured:
        return configured
    return CHAT_MODELS[provider]


def get_llm() -> BaseChatModel:
    """Return the LangChain chat model for the configured LLM_PROVIDER."""
    provider = settings.llm_provider
    model = _resolve_chat_model(provider)

    if provider == LLMProvider.GROQ:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model,
            groq_api_key=settings.groq_api_key,
            temperature=CHAT_TEMPERATURE,
            max_tokens=settings.llm_max_tokens,
        )

    if provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=CHAT_MODELS[LLMProvider.OPENAI],
            api_key=settings.openai_api_key,
            temperature=CHAT_TEMPERATURE,
            max_tokens=settings.llm_max_tokens,
        )

    if provider == LLMProvider.GEMINI:
        raise ValueError(
            "LLM_PROVIDER=GEMINI is no longer supported. Set LLM_PROVIDER=GROQ and GROQ_API_KEY in .env"
        )
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def get_embeddings() -> Embeddings:
    """Return embeddings for FAISS (local HuggingFace model when using Groq without OpenAI)."""
    provider = settings.llm_provider

    if provider == LLMProvider.OPENAI and settings.openai_api_key.strip():
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(api_key=settings.openai_api_key)

    if settings.openai_api_key.strip():
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(api_key=settings.openai_api_key)

    from langchain_community.embeddings import HuggingFaceEmbeddings

    logger.info("Using HuggingFace embeddings for knowledge base (no OpenAI key configured)")
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _is_rate_limit_error(exc: BaseException) -> bool:
    """Detect rate-limit errors across provider SDKs."""
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    rate_limit_names = ("ratelimiterror", "resourceexhausted", "toomanyrequests")
    if any(token in name for token in rate_limit_names):
        return True
    return "rate limit" in message or "429" in message or "quota" in message


def _extract_content(result: Any) -> str:
    """Normalise LLM response content to a plain string."""
    content = getattr(result, "content", result)
    if isinstance(content, list):
        return " ".join(str(part) for part in content)
    return str(content)


def _log_token_usage(result: Any, operation: str) -> None:
    """Log token usage from response metadata when available."""
    metadata = getattr(result, "response_metadata", None) or {}
    usage = metadata.get("token_usage") or metadata.get("usage_metadata") or {}
    if usage:
        logger.info("LLM token usage [%s]: %s", operation, usage)
    else:
        logger.debug("LLM call completed [%s] (no token metadata returned)", operation)


def _normalize_history(messages: list[Any]) -> list[BaseMessage]:
    """Convert dict or BaseMessage history into LangChain messages."""
    normalised: list[BaseMessage] = []
    for msg in messages:
        if isinstance(msg, BaseMessage):
            normalised.append(msg)
            continue
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                normalised.append(AIMessage(content=content))
            elif role == "system":
                normalised.append(SystemMessage(content=content))
            else:
                normalised.append(HumanMessage(content=content))
    return normalised


class LLMService:
    """Centralised async LLM and embeddings interface with retries and logging."""

    def __init__(self) -> None:
        self._llm = get_llm()
        self._embeddings: Embeddings | None = None
        self._provider = settings.llm_provider
        logger.info(
            "LLMService initialised — provider=%s chat_model=%s",
            self._provider.value,
            _resolve_chat_model(self._provider),
        )

    @property
    def embeddings(self) -> Embeddings:
        """Lazy-load embeddings so Groq-only setups do not require OpenAI."""
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings

    @property
    def provider(self) -> LLMProvider:
        return self._provider

    async def _call_with_retry(self, coro_factory, operation: str) -> Any:
        """Execute an async LLM call with exponential backoff on rate limits."""
        last_error: BaseException | None = None
        for attempt in range(MAX_RETRIES):
            try:
                result = await coro_factory()
                _log_token_usage(result, operation)
                return result
            except Exception as exc:
                last_error = exc
                if _is_rate_limit_error(exc) and attempt < MAX_RETRIES - 1:
                    delay = BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "Rate limit on %s (attempt %d/%d), retrying in %.1fs: %s",
                        operation,
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
        raise last_error  # type: ignore[misc]

    async def invoke(self, prompt: str, system: str) -> str:
        """Call the LLM with a system prompt and user message."""
        messages = [SystemMessage(content=system), HumanMessage(content=prompt)]

        async def _call():
            return await self._llm.ainvoke(messages)

        result = await self._call_with_retry(_call, "invoke")
        return _extract_content(result)

    async def invoke_with_history(self, messages: list[Any], system: str) -> str:
        """Call the LLM with full conversation history plus a system message."""
        history = _normalize_history(messages)
        full_messages: list[BaseMessage] = [SystemMessage(content=system), *history]
        return await self.invoke_messages_direct(full_messages)

    async def invoke_messages_direct(self, messages: list[BaseMessage]) -> str:
        """Call the LLM with a pre-built LangChain message list."""

        async def _call():
            return await self._llm.ainvoke(messages)

        result = await self._call_with_retry(_call, "invoke_messages_direct")
        return _extract_content(result)

    async def stream_invoke_with_messages(
        self,
        messages: list[BaseMessage],
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response tokens from a pre-built message list."""
        async def _stream():
            async for chunk in self._llm.astream(messages):
                token = _extract_content(chunk)
                if token:
                    yield token

        last_error: BaseException | None = None
        for attempt in range(MAX_RETRIES):
            try:
                async for token in _stream():
                    yield token
                return
            except Exception as exc:
                last_error = exc
                if _is_rate_limit_error(exc) and attempt < MAX_RETRIES - 1:
                    delay = BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "Rate limit on stream_invoke (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
        raise last_error  # type: ignore[misc]

    async def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for the given text."""
        loop = asyncio.get_event_loop()

        def _embed() -> list[float]:
            return self.embeddings.embed_query(text)

        return await loop.run_in_executor(None, _embed)


# Singleton used across the application
llm_service = LLMService()


# Backward-compatible helpers for existing agents
async def invoke_prompt(system: str, human: str) -> str:
    """Run a simple system/human prompt through the shared LLM service."""
    return await llm_service.invoke(human, system)


async def invoke_messages(messages: list[BaseMessage], system: str) -> str:
    """Invoke the LLM with a pre-built message list."""
    return await llm_service.invoke_with_history(messages, system)
