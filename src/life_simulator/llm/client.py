"""LLM client wrapper supporting multiple providers with retry logic."""

import json
import logging
import os
import re
import time

logger = logging.getLogger(__name__)

# Per-million-token pricing: (input, output)
_PRICING = {
    "claude-sonnet-4-20250514": (3, 15),
    "claude-haiku-4-5-20251001": (0.8, 4),
    "gpt-4o": (2.5, 10),
    "gpt-4o-mini": (0.15, 0.6),
}

# Provider registry: prefix → (base_url, env_var_for_key)
_PROVIDERS = {
    "ollama": ("http://localhost:11434/v1", None),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "together": ("https://api.together.xyz/v1", "TOGETHER_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1", "MISTRAL_API_KEY"),
    "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
    "fireworks": ("https://api.fireworks.ai/inference/v1", "FIREWORKS_API_KEY"),
    "lmstudio": ("http://localhost:1234/v1", None),
}

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry


class LLMClient:
    """Unified LLM client supporting 10+ providers with retry logic.

    Provider is auto-detected from the model string:
      - "ollama/llama3.1"        → Ollama (local, free)
      - "groq/llama-3.1-70b..."  → Groq (fast, free tier)
      - "together/meta-llama/..." → Together AI
      - "mistral/mistral-large"  → Mistral
      - "deepseek/deepseek-chat" → DeepSeek
      - "openai/gpt-4o"          → OpenAI
      - "openrouter/..."         → OpenRouter (100+ models)
      - "fireworks/..."          → Fireworks AI
      - "lmstudio/..."           → LM Studio (local)
      - "claude-sonnet-..."      → Anthropic (default)
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Parse provider prefix
        if "/" in model and not model.startswith("claude"):
            self.provider, self.model = model.split("/", 1)
        elif model.startswith("claude"):
            self.provider = "anthropic"
            self.model = model
        else:
            self.provider = "ollama"
            self.model = model

        if self.provider == "anthropic":
            self._init_anthropic(api_key)
        elif self.provider in _PROVIDERS:
            default_url, env_var = _PROVIDERS[self.provider]
            resolved_key = api_key or (os.environ.get(env_var, "") if env_var else "no-key-needed")
            self._init_openai_compat(
                base_url=base_url or default_url,
                api_key=resolved_key,
            )
        else:
            # Generic OpenAI-compatible
            self._init_openai_compat(
                base_url=base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"),
                api_key=api_key or os.environ.get("OPENAI_API_KEY", "no-key-needed"),
            )

    def _init_anthropic(self, api_key: str | None):
        import anthropic
        self._backend = "anthropic"
        self._anthropic = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def _init_openai_compat(self, base_url: str, api_key: str):
        from openai import OpenAI
        self._backend = "openai"
        self._openai = OpenAI(base_url=base_url, api_key=api_key)

    def generate_transition(self, prompt: str) -> dict:
        """Generate a state transition with retry logic, returning parsed JSON."""
        text, usage = self._call_with_retry(prompt, max_tokens=1500)
        self.total_input_tokens += usage[0]
        self.total_output_tokens += usage[1]
        return self._extract_json(text)

    def generate_text(self, prompt: str) -> str:
        """Generate free-form text (for narratives)."""
        text, usage = self._call_with_retry(prompt, max_tokens=500)
        self.total_input_tokens += usage[0]
        self.total_output_tokens += usage[1]
        return text.strip()

    def _call_with_retry(self, prompt: str, max_tokens: int) -> tuple[str, tuple[int, int]]:
        """Call LLM with exponential backoff retry."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return self._call(prompt, max_tokens)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Don't retry auth errors
                if any(kw in error_str for kw in ("auth", "api key", "unauthorized", "forbidden", "401", "403")):
                    raise LLMAuthError(f"Authentication failed for {self.provider}: {e}") from e

                # Don't retry model-not-found
                if any(kw in error_str for kw in ("model not found", "does not exist", "404")):
                    raise LLMModelError(
                        f"Model '{self.model}' not found on {self.provider}. "
                        f"Check the model name or pull it first."
                    ) from e

                wait = RETRY_BACKOFF * (2 ** attempt)
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s. Retrying in %.1fs...",
                    attempt + 1, MAX_RETRIES, e, wait,
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)

        raise LLMConnectionError(
            f"Failed after {MAX_RETRIES} attempts ({self.provider}/{self.model}): {last_error}"
        ) from last_error

    def _call(self, prompt: str, max_tokens: int) -> tuple[str, tuple[int, int]]:
        """Route to the right backend. Returns (text, (input_tokens, output_tokens))."""
        if self._backend == "anthropic":
            response = self._anthropic.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )
            return (
                response.content[0].text,
                (response.usage.input_tokens, response.usage.output_tokens),
            )
        else:
            response = self._openai.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}],
            )
            usage = response.usage
            in_tok = usage.prompt_tokens if usage else 0
            out_tok = usage.completion_tokens if usage else 0
            text = response.choices[0].message.content or ""
            return text, (in_tok, out_tok)

    @property
    def estimated_cost(self) -> float:
        """Rough cost estimate in USD. Free for local models."""
        if self.provider in ("ollama", "lmstudio"):
            return 0.0
        pricing = _PRICING.get(self.model, (3, 15))
        return (self.total_input_tokens * pricing[0] + self.total_output_tokens * pricing[1]) / 1_000_000

    @property
    def display_name(self) -> str:
        if self.provider in ("ollama", "lmstudio"):
            return f"{self.provider.title()} ({self.model})"
        if self.provider == "anthropic":
            return f"Claude ({self.model.split('-')[1].title()})"
        return f"{self.provider}/{self.model}"

    @property
    def is_local(self) -> bool:
        return self.provider in ("ollama", "lmstudio")

    def _extract_json(self, text: str) -> dict:
        """Robustly extract JSON from LLM response."""
        # Try code fence first
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1)

        # Find JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        # Strip JS-style comments
        text = re.sub(r"//[^\n]*", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fix trailing commas
        cleaned = re.sub(r",\s*([}\]])", r"\1", text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fix single quotes
        cleaned2 = text.replace("'", '"')
        try:
            return json.loads(cleaned2)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON. Raw output: %s", text[:1000])
            raise LLMParseError(f"Failed to parse JSON from LLM: {e}") from e


# Custom exceptions for actionable error messages
class LLMError(Exception):
    """Base class for LLM errors."""


class LLMAuthError(LLMError):
    """API key is missing or invalid."""


class LLMModelError(LLMError):
    """Model not found or not available."""


class LLMConnectionError(LLMError):
    """Failed to connect after retries."""


class LLMParseError(LLMError):
    """Failed to parse LLM output as JSON."""
