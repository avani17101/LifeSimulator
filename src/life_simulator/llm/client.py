"""LLM client wrapper supporting multiple providers."""

import json
import os
import re


# Per-million-token pricing: (input, output)
_PRICING = {
    "claude-sonnet-4-20250514": (3, 15),
    "claude-haiku-4-5-20251001": (0.8, 4),
}


class LLMClient:
    """Unified LLM client supporting Anthropic, Ollama, and any OpenAI-compatible API.

    Provider is auto-detected from the model string:
      - "ollama/llama3.1"        → Ollama (local, free)
      - "openai/gpt-4o"          → OpenAI
      - "openrouter/..."         → OpenRouter
      - "claude-sonnet-..."      → Anthropic (default)
      - anything else            → tries OpenAI-compatible with OPENAI_BASE_URL
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
        elif self.provider == "ollama":
            self._init_openai_compat(
                base_url=base_url or "http://localhost:11434/v1",
                api_key=api_key or "ollama",
            )
        elif self.provider == "openrouter":
            self._init_openai_compat(
                base_url=base_url or "https://openrouter.ai/api/v1",
                api_key=api_key or os.environ.get("OPENROUTER_API_KEY", ""),
            )
        elif self.provider == "openai":
            self._init_openai_compat(
                base_url=base_url or "https://api.openai.com/v1",
                api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            )
        else:
            # Generic OpenAI-compatible (vLLM, LM Studio, Together, etc.)
            self._init_openai_compat(
                base_url=base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"),
                api_key=api_key or os.environ.get("OPENAI_API_KEY", "none"),
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
        """Generate a state transition, returning parsed JSON."""
        text, usage = self._call(prompt, max_tokens=1500)
        self.total_input_tokens += usage[0]
        self.total_output_tokens += usage[1]
        return self._extract_json(text)

    def generate_text(self, prompt: str) -> str:
        """Generate free-form text (for narratives)."""
        text, usage = self._call(prompt, max_tokens=500)
        self.total_input_tokens += usage[0]
        self.total_output_tokens += usage[1]
        return text.strip()

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
            return response.choices[0].message.content, (in_tok, out_tok)

    @property
    def estimated_cost(self) -> float:
        """Rough cost estimate in USD. Free for local models."""
        if self.provider == "ollama":
            return 0.0
        pricing = _PRICING.get(self.model, (3, 15))
        return (self.total_input_tokens * pricing[0] + self.total_output_tokens * pricing[1]) / 1_000_000

    @property
    def display_name(self) -> str:
        if self.provider == "ollama":
            return f"Ollama ({self.model})"
        if self.provider == "anthropic":
            return f"Claude ({self.model.split('-')[1].title()})"
        return f"{self.provider}/{self.model}"

    def _extract_json(self, text: str) -> dict:
        """Robustly extract JSON from LLM response."""
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            text = match.group(1)

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            cleaned = re.sub(r",\s*([}\]])", r"\1", text)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse LLM JSON output: {e}\n{text[:500]}")
