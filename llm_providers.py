"""
llm_providers.py — LLM API Adapters for Cogni CISLF Advisor
============================================================
Provides a unified interface for multiple LLM providers.
Supported providers:
  - Google Gemini (google-generativeai)
  - OpenAI (openai)

Author: Cogni CISLF Advisor Project
Framework Reference: Quasif, M. (2025). Strategic Leadership for AI-Driven
  Business Transformation: A Cross-Industry Framework for Technology Executives.
  DBA Thesis. Kennedy University of Baptist, France.
"""

import time
from google import genai
from google.genai import types as genai_types
from openai import OpenAI, AuthenticationError, RateLimitError, APITimeoutError
import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 480  # 8 min — single-call pipeline; reasoning models (o1, DeepSeek-R1, claude-opus) can be slow
MAX_RETRIES = 2                # Number of retry attempts on transient errors
RETRY_DELAY_SECONDS = 5        # Wait between retries


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------
class LLMProviderError(Exception):
    """Raised for provider-level errors (auth, rate-limit, timeout, etc.)."""
    pass


# ---------------------------------------------------------------------------
# Gemini Provider
# ---------------------------------------------------------------------------
class GeminiProvider:
    """
    Adapter for Google Gemini via the google-generativeai SDK.

    Supports:
      - gemini-1.5-flash  (faster, cost-effective)
      - gemini-1.5-pro    (more capable, higher quota usage)
    """

    SUPPORTED_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro"]

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "Gemini API key is missing. Please enter your key in the sidebar."
            )

        # Instantiate the new google-genai client
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key.strip())

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a system + user prompt to Gemini and return the response text.

        Gemini does not have a distinct system-role; we prepend the system
        prompt as a leading user turn for compatibility.

        Args:
            system_prompt: Instructions describing CISLF role and behaviour.
            user_prompt:   The executive's challenge description.

        Returns:
            The generated report as a plain string.

        Raises:
            LLMProviderError: On auth failure, rate limit, timeout, or other errors.
        """
        # Merge system and user prompts into a single content string
        combined_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"

        generation_config = genai_types.GenerateContentConfig(
            temperature=0.3,          # Lower temp = faster, more focused output
            max_output_tokens=6000,   # Full CISLF report fits in 5-6k tokens
        )

        for attempt in range(1, MAX_RETRIES + 2):  # +2 for initial + retries
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=combined_prompt,
                    config=generation_config,
                )
                # Extract text safely
                if response.text:
                    return response.text.strip()
                else:
                    raise LLMProviderError(
                        "Gemini returned an empty response. "
                        "Try rephrasing your challenge description."
                    )

            except Exception as e:
                err_str = str(e).lower()

                # Authentication error — no point retrying
                if "api key" in err_str or "invalid" in err_str or "401" in err_str:
                    raise LLMProviderError(
                        "Invalid Gemini API key. Please check the key in the sidebar."
                    ) from e

                # Rate limit — retry after delay
                if "quota" in err_str or "rate" in err_str or "429" in err_str:
                    if attempt <= MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS * attempt)
                        continue
                    raise LLMProviderError(
                        "Gemini API rate limit reached. Please wait a moment and try again."
                    ) from e

                # Timeout — retry
                if "timeout" in err_str or "deadline" in err_str:
                    if attempt <= MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS)
                        continue
                    raise LLMProviderError(
                        "Request timed out. The model took too long to respond. "
                        "Please try again or switch to a faster model."
                    ) from e

                # Unknown error — surface it
                raise LLMProviderError(
                    f"Gemini API error: {str(e)}"
                ) from e

        raise LLMProviderError("Failed to get a response from Gemini after retries.")


# ---------------------------------------------------------------------------
# OpenAI Provider
# ---------------------------------------------------------------------------
class OpenAIProvider:
    """
    Adapter for OpenAI Chat Completions API.

    Supports:
      - gpt-4o-mini  (cost-effective, fast)
      - gpt-4o       (most capable)
    """

    SUPPORTED_MODELS = ["gpt-4o-mini", "gpt-4o"]

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "OpenAI API key is missing. Please enter your key in the sidebar."
            )

        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key.strip(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a system + user message to OpenAI Chat Completions.

        Args:
            system_prompt: CISLF role and output format instructions.
            user_prompt:   The executive's challenge description.

        Returns:
            The generated report as a plain string.

        Raises:
            LLMProviderError: On auth failure, rate limit, timeout, or other errors.
        """
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=6000,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                else:
                    raise LLMProviderError(
                        "OpenAI returned an empty response. "
                        "Try rephrasing your challenge description."
                    )

            except AuthenticationError as e:
                raise LLMProviderError(
                    "Invalid OpenAI API key. Please check the key in the sidebar."
                ) from e

            except RateLimitError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue
                raise LLMProviderError(
                    "OpenAI rate limit reached. Please wait a moment and try again."
                ) from e

            except APITimeoutError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise LLMProviderError(
                    "Request timed out. Please try again or switch to a faster model."
                ) from e

            except Exception as e:
                raise LLMProviderError(f"OpenAI API error: {str(e)}") from e

        raise LLMProviderError("Failed to get a response from OpenAI after retries.")


# ---------------------------------------------------------------------------
# DeepSeek Provider
# ---------------------------------------------------------------------------
class DeepSeekProvider:
    """
    Adapter for DeepSeek API (OpenAI-compatible).

    Supports:
      - deepseek-chat      (DeepSeek-V3, general completions)
      - deepseek-reasoner  (DeepSeek-R1, reasoning/thinking model)
    """

    SUPPORTED_MODELS = ["deepseek-chat", "deepseek-reasoner"]

    def __init__(self, api_key: str, model_name: str = "deepseek-chat"):
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "DeepSeek API key is missing. Please enter your key in settings."
            )

        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key.strip(),
            base_url="https://api.deepseek.com",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a system + user message to DeepSeek Chat Completions.
        """
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                # deepseek-reasoner does not support temperature customization
                kwargs = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "max_tokens": 6000,
                }
                if self.model_name == "deepseek-chat":
                    kwargs["temperature"] = 0.3

                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                else:
                    raise LLMProviderError(
                        "DeepSeek returned an empty response. "
                        "Try rephrasing your challenge description."
                    )

            except AuthenticationError as e:
                raise LLMProviderError(
                    "Invalid DeepSeek API key. Please check the key in settings."
                ) from e

            except RateLimitError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue
                raise LLMProviderError(
                    "DeepSeek rate limit reached. Please wait a moment and try again."
                ) from e

            except APITimeoutError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise LLMProviderError(
                    "Request timed out. Please try again or switch to a faster model."
                ) from e

            except Exception as e:
                raise LLMProviderError(f"DeepSeek API error: {str(e)}") from e

        raise LLMProviderError("Failed to get a response from DeepSeek after retries.")


# ---------------------------------------------------------------------------
# Anthropic Provider
# ---------------------------------------------------------------------------
class AnthropicProvider:
    """
    Adapter for Anthropic Claude API.

    Supports:
      - claude-3-7-sonnet-20250219 (Latest Sonnet)
      - claude-3-5-sonnet-latest   (3.5 Sonnet)
      - claude-3-opus-latest       (Opus)
    """

    SUPPORTED_MODELS = [
        "claude-3-7-sonnet-20250219", 
        "claude-3-5-sonnet-latest", 
        "claude-3-opus-latest"
    ]

    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-latest"):
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "Anthropic API key is missing. Please enter your key in the sidebar."
            )

        self.model_name = model_name
        self.client = anthropic.Anthropic(
            api_key=api_key.strip(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a system + user message to Anthropic Claude.
        """
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=6000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                )
                
                content = response.content[0].text
                if content:
                    return content.strip()
                else:
                    raise LLMProviderError(
                        "Anthropic returned an empty response. "
                        "Try rephrasing your challenge description."
                    )

            except anthropic.AuthenticationError as e:
                raise LLMProviderError(
                    "Invalid Anthropic API key. Please check the key in the sidebar."
                ) from e

            except anthropic.RateLimitError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue
                raise LLMProviderError(
                    "Anthropic rate limit reached. Please wait a moment and try again."
                ) from e

            except anthropic.APITimeoutError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue
                raise LLMProviderError(
                    "Request timed out. Please try again."
                ) from e

            except Exception as e:
                raise LLMProviderError(f"Anthropic API error: {str(e)}") from e

        raise LLMProviderError("Failed to get a response from Anthropic after retries.")


# ---------------------------------------------------------------------------
# Groq Provider
# ---------------------------------------------------------------------------
class GroqProvider:
    """Adapter for Groq API (OpenAI-compatible)."""

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        if not api_key or not api_key.strip():
            raise LLMProviderError("Groq API key is missing.")
        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key.strip(),
            base_url="https://api.groq.com/openai/v1",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=6000,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                raise LLMProviderError("Groq returned an empty response.")
            except Exception as e:
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str:
                    if attempt <= MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS * attempt)
                        continue
                raise LLMProviderError(f"Groq API error: {str(e)}") from e
        raise LLMProviderError("Failed to get a response from Groq after retries.")


# ---------------------------------------------------------------------------
# OpenRouter Provider
# ---------------------------------------------------------------------------
class OpenRouterProvider:
    """Adapter for OpenRouter API (OpenAI-compatible)."""

    def __init__(self, api_key: str, model_name: str = "openai/o3-mini"):
        if not api_key or not api_key.strip():
            raise LLMProviderError("OpenRouter API key is missing.")
        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key.strip(),
            base_url="https://openrouter.ai/api/v1",
            timeout=REQUEST_TIMEOUT_SECONDS,
            default_headers={
                "HTTP-Referer": "https://cognicislf.com",
                "X-Title": "Cogni CISLF Advisor",
            }
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    max_tokens=6000,
                    temperature=0.3,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
                raise LLMProviderError("OpenRouter returned an empty response.")
            except Exception as e:
                err_str = str(e).lower()
                if "rate limit" in err_str or "429" in err_str:
                    if attempt <= MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS * attempt)
                        continue
                raise LLMProviderError(f"OpenRouter API error: {str(e)}") from e
        raise LLMProviderError("Failed to get a response from OpenRouter after retries.")


# ---------------------------------------------------------------------------
# Provider Factory
# ---------------------------------------------------------------------------
def get_provider(provider_name: str, api_key: str, model_name: str):
    if provider_name == "Google Gemini":
        return GeminiProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "OpenAI":
        return OpenAIProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "DeepSeek":
        return DeepSeekProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "Anthropic Claude":
        return AnthropicProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "Groq":
        return GroqProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "OpenRouter":
        return OpenRouterProvider(api_key=api_key, model_name=model_name)
    else:
        raise LLMProviderError(f"Unknown provider '{provider_name}'.")

# ---------------------------------------------------------------------------
# Live Model Fetching
# ---------------------------------------------------------------------------
def fetch_live_models(provider_name: str, api_key: str) -> tuple[list[str], str]:
    """
    Fetch a live list of models from the provider's API.
    Returns (models_list, error_message).
    """
    if not api_key:
        return [], "API Key is missing."

    try:
        if provider_name == "OpenAI":
            client = OpenAI(api_key=api_key.strip())
            return sorted([m.id for m in client.models.list().data]), ""
        elif provider_name == "DeepSeek":
            client = OpenAI(api_key=api_key.strip(), base_url="https://api.deepseek.com")
            return sorted([m.id for m in client.models.list().data]), ""
        elif provider_name == "Groq":
            client = OpenAI(api_key=api_key.strip(), base_url="https://api.groq.com/openai/v1")
            models = sorted([m.id for m in client.models.list().data if 'llama' in m.id.lower() or 'mixtral' in m.id.lower() or 'gemma' in m.id.lower() or 'deepseek' in m.id.lower()])
            return models, ""
        elif provider_name == "OpenRouter":
            client = OpenAI(api_key=api_key.strip(), base_url="https://openrouter.ai/api/v1")
            return sorted([m.id for m in client.models.list().data]), ""
        elif provider_name == "Google Gemini":
            client = genai.Client(api_key=api_key.strip())
            return sorted([m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_actions]), ""
        elif provider_name == "Anthropic Claude":
            client = anthropic.Anthropic(api_key=api_key.strip())
            return sorted([m.id for m in client.models.list().data]), ""
        else:
            return [], f"Live fetch not supported for {provider_name}"
    except Exception as e:
        return [], str(e)
