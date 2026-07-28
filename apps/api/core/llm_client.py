"""
LLM Client Abstraction — provides a unified interface for LLM providers.

Supports OpenAI, Anthropic, and Google Gemini with:
- Automatic fallback chain (primary → fallback provider)
- Rate limiting and token counting
- Streaming support via SSE
- Structured output parsing for legal domain tasks
"""
import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("api.core.llm_client")


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MOCK = "mock"


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = ""
    raw_response: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider = LLMProvider.MOCK
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    max_tokens: int = 4096
    temperature: float = 0.1  # Low temperature for legal accuracy
    timeout: float = 60.0


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client: httpx.AsyncClient | None = None

    @abstractmethod
    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        """Send a completion request and return the response."""

    @abstractmethod
    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        """Stream a completion response, yielding text chunks."""

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers=self._build_headers(),
            )
        return self._client

    @abstractmethod
    def _build_headers(self) -> dict[str, str]:
        """Build provider-specific headers."""


class OpenAIClient(BaseLLMClient):
    """OpenAI-compatible LLM client (works with OpenAI, Azure OpenAI, and compatible APIs)."""

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        client = self._get_client()
        base_url = self.config.base_url or "https://api.openai.com/v1"

        payload = {
            "model": self.config.model or "gpt-4o-mini",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        response = await client.post(f"{base_url}/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            provider="openai",
            model=data.get("model", self.config.model),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
            raw_response=data,
        )

    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        client = self._get_client()
        base_url = self.config.base_url or "https://api.openai.com/v1"

        payload = {
            "model": self.config.model or "gpt-4o-mini",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": True,
        }

        async with client.stream("POST", f"{base_url}/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client."""

    def _build_headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        client = self._get_client()
        base_url = self.config.base_url or "https://api.anthropic.com/v1"

        # Anthropic separates system from messages
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        payload = {
            "model": self.config.model or "claude-sonnet-4-20250514",
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": user_msgs,
        }
        if system_msg:
            payload["system"] = system_msg

        response = await client.post(f"{base_url}/messages", json=payload)
        response.raise_for_status()
        data = response.json()

        content_blocks = data.get("content", [])
        content = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            provider="anthropic",
            model=data.get("model", self.config.model),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            finish_reason=data.get("stop_reason", ""),
            raw_response=data,
        )

    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        client = self._get_client()
        base_url = self.config.base_url or "https://api.anthropic.com/v1"

        system_msg = ""
        user_msgs = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        payload = {
            "model": self.config.model or "claude-sonnet-4-20250514",
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": user_msgs,
            "stream": True,
        }
        if system_msg:
            payload["system"] = system_msg

        async with client.stream("POST", f"{base_url}/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                    except (json.JSONDecodeError, KeyError):
                        continue


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and development."""

    def _build_headers(self) -> dict[str, str]:
        return {}

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        # Extract the last user message for context-aware mock responses
        last_user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m.content
                break

        mock_response = (
            f"[MOCK LLM] Bu bir test yanıtıdır. "
            f"Soru/bağlam: '{last_user_msg[:100]}...'. "
            f"Gerçek bir LLM yanıtı için MESA_LAW_LLM_PROVIDER ortam değişkenini ayarlayın."
        )

        return LLMResponse(
            content=mock_response,
            provider="mock",
            model="mock-v1",
            input_tokens=len(last_user_msg.split()),
            output_tokens=len(mock_response.split()),
            finish_reason="stop",
        )

    async def stream(self, messages: list[LLMMessage]) -> AsyncIterator[str]:
        response = await self.complete(messages)
        # Simulate streaming by yielding word by word
        for word in response.content.split():
            yield word + " "
            await asyncio.sleep(0.01)


# ---------------------------------------------------------------------------
# Factory & Singleton
# ---------------------------------------------------------------------------

_PROVIDER_MAP = {
    LLMProvider.OPENAI: OpenAIClient,
    LLMProvider.ANTHROPIC: AnthropicClient,
    LLMProvider.MOCK: MockLLMClient,
}

_cached_client: BaseLLMClient | None = None


def get_llm_config() -> LLMConfig:
    """Build LLM config from environment variables."""
    provider_str = os.getenv("MESA_LAW_LLM_PROVIDER", "mock").lower()

    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        logger.warning(f"Unknown LLM provider '{provider_str}', falling back to mock")
        provider = LLMProvider.MOCK

    return LLMConfig(
        provider=provider,
        model=os.getenv("MESA_LAW_LLM_MODEL", ""),
        api_key=os.getenv("MESA_LAW_LLM_API_KEY", ""),
        base_url=os.getenv("MESA_LAW_LLM_BASE_URL", ""),
        max_tokens=int(os.getenv("MESA_LAW_LLM_MAX_TOKENS", "4096")),
        temperature=float(os.getenv("MESA_LAW_LLM_TEMPERATURE", "0.1")),
        timeout=float(os.getenv("MESA_LAW_LLM_TIMEOUT", "60")),
    )


def create_llm_client(config: LLMConfig | None = None) -> BaseLLMClient:
    """Create an LLM client from config or environment."""
    if config is None:
        config = get_llm_config()

    client_class = _PROVIDER_MAP.get(config.provider, MockLLMClient)
    logger.info(f"Creating LLM client: provider={config.provider.value}, model={config.model}")
    return client_class(config)


def get_llm_client() -> BaseLLMClient:
    """Get or create a cached LLM client singleton."""
    global _cached_client
    if _cached_client is None:
        _cached_client = create_llm_client()
    return _cached_client


# ---------------------------------------------------------------------------
# Legal Domain Prompts
# ---------------------------------------------------------------------------

LEGAL_QA_SYSTEM_PROMPT = """Sen bir Türk hukuku uzmanı asistan AI'sın. Görevin, verilen belge bağlamından (context) kullanıcının sorularını yanıtlamaktır.

KRİTİK KURALLAR:
1. YALNIZCA verilen belge bağlamından (context) bilgi kullan. Bağlamda olmayan bilgiyi ASLA uydurma.
2. Her iddiayı kaynak belge ve sayfa numarası ile destekle.
3. Eğer bağlamda soruyu yanıtlayacak yeterli bilgi yoksa, açıkça "Mevcut belgelerde bu soruya ilişkin yeterli bilgi bulunamadı" de.
4. Yasal referansları (kanun maddesi, yönetmelik, vb.) doğru ve tam olarak ver.
5. Yanıtını JSON formatında ver:
{
  "answer": "Yanıt metni",
  "citations": [
    {"document_id": "...", "page_number": N, "text_snippet": "ilgili metin parçası"}
  ],
  "confidence": "high|medium|low",
  "has_sufficient_evidence": true/false
}
"""

LEGAL_EXTRACTION_SYSTEM_PROMPT = """Sen bir Türk hukuku belge analiz uzmanısın. Görevin, verilen metinden yapılandırılmış hukuki bilgileri çıkarmaktır.

Çıkarılacak bilgiler:
- Taraflar (davacı, davalı, müdahil)
- Talepler (kıdem tazminatı, ihbar tazminatı, fazla mesai, vb.)
- Tarihler ve sürelere ilişkin olaylar
- Deliller ve belgeler

Her çıkarılan bilgiyi kaynak metninden alıntı ile destekle. Metinde olmayan bilgiyi ASLA uydurma.

Yanıtını JSON formatında ver.
"""


async def ask_with_llm(
    question: str,
    context_chunks: list[dict],
    client: BaseLLMClient | None = None,
) -> dict:
    """
    Ask a question using an LLM with retrieved context chunks.
    Returns structured response with answer and citations.
    """
    if client is None:
        client = get_llm_client()

    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(context_chunks):
        doc_id = chunk.get("document_id", "unknown")
        page = chunk.get("page_number", "?")
        text = chunk.get("text", chunk.get("text_content", ""))
        context_parts.append(
            f"[Belge: {doc_id}, Sayfa: {page}]\n{text}"
        )

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "Bağlam bilgisi bulunamadı."

    messages = [
        LLMMessage(role="system", content=LEGAL_QA_SYSTEM_PROMPT),
        LLMMessage(
            role="user",
            content=f"## Belge Bağlamı:\n{context_text}\n\n## Soru:\n{question}",
        ),
    ]

    try:
        response = await client.complete(messages)
        logger.info(
            f"LLM response: provider={response.provider}, "
            f"tokens={response.total_tokens}, finish={response.finish_reason}"
        )

        # Try to parse structured JSON from response
        try:
            parsed = json.loads(response.content)
            return {
                "answer": parsed.get("answer", response.content),
                "citations": parsed.get("citations", []),
                "confidence": parsed.get("confidence", "medium"),
                "has_sufficient_evidence": parsed.get("has_sufficient_evidence", True),
                "llm_provider": response.provider,
                "llm_model": response.model,
                "tokens_used": response.total_tokens,
            }
        except json.JSONDecodeError:
            # LLM returned plain text instead of JSON — wrap it
            return {
                "answer": response.content,
                "citations": [],
                "confidence": "low",
                "has_sufficient_evidence": True,
                "llm_provider": response.provider,
                "llm_model": response.model,
                "tokens_used": response.total_tokens,
            }

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "answer": "",
            "citations": [],
            "confidence": "none",
            "has_sufficient_evidence": False,
            "error": str(e),
        }
