"""
Entrance-exam AI provider pool. Fans out to every configured, under-quota
provider SIMULTANEOUSLY (concurrent.futures.ThreadPoolExecutor -- the
Python equivalent of JavaScript's Promise.allSettled(), since this
backend is entirely FastAPI/Python, not Node) and collects every
provider's outcome, success or failure, without one slow/failing
provider blocking the rest. Scoped to entrance-exam question generation
only -- every other AI feature in the app keeps calling _call_gemini
directly (see backend/app/api/tutor.py).

Every real attempt (not a skip) is logged to AIProviderAttempt, which
drives both the admin panel's green/red status history and this module's
own per-provider daily cap (see _attempts_since_midnight_utc). A provider
whose required API key(s) aren't set in .env, or that's already hit
today's cap, is skipped instantly -- no network call, no waiting on the
20s timeout -- so this works today with just the existing Gemini key,
and each new key added to .env lights up that provider immediately with
no code changes.
"""

import time as time_module
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, time as midnight_time
from typing import Callable, Optional

import httpx
from sqlalchemy.orm import Session

from app.api.tutor import _call_gemini
from app.core.config import settings
from app.models.ai_provider_attempt import AIProviderAttempt

REQUEST_TIMEOUT_SECONDS = 20.0

# Applied uniformly to all 14 providers -- real free-tier request ceilings
# vary per provider and change over time (some, like Groq, comfortably
# support thousands/day; others, like Cohere's trial key, are closer to a
# few dozen). 200 is a deliberately generous shared default: a provider
# that's actually capped lower just fails those extra calls gracefully
# (logged, router moves to the next provider) rather than under-using
# providers with real headroom. Tune down per-provider if a specific one
# turns out to be wasting calls against a much lower real limit.
PROVIDER_DAILY_LIMIT = 200

FALLBACK_MESSAGE = (
    "All providers exhausted. Questions saved so far are preserved. Try again later."
)


class AIProvidersExhaustedError(Exception):
    pass


def extract_json_object(text: str) -> str:
    """Gemini's response_mime_type="application/json" enforces clean output,
    but not every provider has an equivalent structured-output mode -- some
    wrap the JSON in markdown code fences or a leading sentence. Strip those
    so json.JSONDecoder().raw_decode (which requires valid JSON starting at
    position 0) has a clean string to work with."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    brace_index = text.find("{")
    if brace_index > 0:
        text = text[brace_index:]
    return text


ProviderCall = Callable[[str, str, Optional[str]], str]


@dataclass
class Provider:
    name: str
    is_configured: Callable[[], bool]
    call: ProviderCall


def _openai_compatible(url: str, api_key_attr: str, model: str) -> ProviderCall:
    """Shared adapter for the 9 providers whose chat-completions API is
    OpenAI-compatible (Groq, Cerebras, SambaNova, Together, Fireworks,
    Mistral, DeepInfra, DeepSeek, OpenRouter) -- same request/response
    shape, just a different base URL/model/key per provider."""

    def call(system_prompt: str, user_message: str, response_mime_type: Optional[str] = None) -> str:
        api_key = getattr(settings, api_key_attr)
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    return call


def _cohere_call(system_prompt: str, user_message: str, response_mime_type: Optional[str] = None) -> str:
    # Cohere retired the v1 Chat API (POST /v1/chat, message+preamble body) --
    # this uses the current v2 shape (POST /v2/chat, a messages array).
    response = httpx.post(
        "https://api.cohere.com/v2/chat",
        headers={"Authorization": f"Bearer {settings.cohere_api_key}", "Content-Type": "application/json"},
        json={
            "model": "command-r",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["message"]["content"][0]["text"]


def _cloudflare_call(system_prompt: str, user_message: str, response_mime_type: Optional[str] = None) -> str:
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{settings.cf_account_id}"
        "/ai/run/@cf/meta/llama-3-8b-instruct"
    )
    response = httpx.post(
        url,
        headers={"Authorization": f"Bearer {settings.cf_api_key}"},
        json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["result"]["response"]


def _huggingface_call(system_prompt: str, user_message: str, response_mime_type: Optional[str] = None) -> str:
    response = httpx.post(
        "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
        headers={"Authorization": f"Bearer {settings.hf_api_key}"},
        json={"inputs": f"{system_prompt}\n\n{user_message}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data[0]["generated_text"]


def _ollama_call(system_prompt: str, user_message: str, response_mime_type: Optional[str] = None) -> str:
    response = httpx.post(
        f"{settings.ollama_base_url}/api/chat",
        json={
            "model": "llama3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def _gemini_call(system_prompt: str, user_message: str, response_mime_type: Optional[str] = None) -> str:
    return _call_gemini(system_prompt, user_message, response_mime_type=response_mime_type, max_output_tokens=8000)


def _build_providers() -> list[Provider]:
    return [
        Provider(
            "Groq",
            lambda: bool(settings.groq_api_key),
            # llama3-8b-8192 was decommissioned by Groq; llama-3.1-8b-instant
            # is the current small/fast production model.
            _openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions", "groq_api_key", "llama-3.1-8b-instant"
            ),
        ),
        Provider(
            "Cerebras",
            lambda: bool(settings.cerebras_api_key),
            # Cerebras no longer offers a small Llama model on this endpoint;
            # gpt-oss-120b is their current production model.
            _openai_compatible("https://api.cerebras.ai/v1/chat/completions", "cerebras_api_key", "gpt-oss-120b"),
        ),
        Provider(
            "SambaNova",
            lambda: bool(settings.sambanova_api_key),
            # SambaNova's smallest current Llama offering is the 3.3 70B model
            # -- no 8B model remains in their catalog.
            _openai_compatible(
                "https://api.sambanova.ai/v1/chat/completions", "sambanova_api_key", "Meta-Llama-3.3-70B-Instruct"
            ),
        ),
        Provider(
            "Together AI",
            lambda: bool(settings.together_api_key),
            _openai_compatible(
                "https://api.together.xyz/v1/chat/completions", "together_api_key", "meta-llama/Llama-3-8b-hf"
            ),
        ),
        Provider(
            "Fireworks AI",
            lambda: bool(settings.fireworks_api_key),
            # llama-v3-8b-instruct 404s (model path retired); Fireworks' own
            # naming convention has since moved to "v3p1" for 3.1 models.
            # Lower confidence than the other fixes here -- verify against
            # https://fireworks.ai/models if this still fails.
            _openai_compatible(
                "https://api.fireworks.ai/inference/v1/chat/completions",
                "fireworks_api_key",
                "accounts/fireworks/models/llama-v3p1-8b-instruct",
            ),
        ),
        Provider(
            "Mistral AI",
            lambda: bool(settings.mistral_api_key),
            _openai_compatible("https://api.mistral.ai/v1/chat/completions", "mistral_api_key", "mistral-small-latest"),
        ),
        Provider("Cohere", lambda: bool(settings.cohere_api_key), _cohere_call),
        Provider(
            "DeepInfra",
            lambda: bool(settings.deepinfra_api_key),
            _openai_compatible(
                "https://api.deepinfra.com/v1/openai/chat/completions",
                "deepinfra_api_key",
                "meta-llama/Meta-Llama-3-8B-Instruct",
            ),
        ),
        Provider(
            "Cloudflare Workers AI",
            lambda: bool(settings.cf_api_key and settings.cf_account_id),
            _cloudflare_call,
        ),
        Provider(
            "DeepSeek",
            lambda: bool(settings.deepseek_api_key),
            _openai_compatible("https://api.deepseek.com/v1/chat/completions", "deepseek_api_key", "deepseek-chat"),
        ),
        Provider("Hugging Face", lambda: bool(settings.hf_api_key), _huggingface_call),
        Provider(
            "OpenRouter",
            lambda: bool(settings.openrouter_api_key),
            # That Llama model is no longer on OpenRouter's free tier --
            # nemotron-nano-9b-v2:free is confirmed currently free via
            # GET https://openrouter.ai/api/v1/models (OpenRouter's free
            # lineup changes over time; re-check that endpoint if this
            # 404s again).
            _openai_compatible(
                "https://openrouter.ai/api/v1/chat/completions",
                "openrouter_api_key",
                "nvidia/nemotron-nano-9b-v2:free",
            ),
        ),
        Provider("Gemini", lambda: bool(settings.google_api_key), _gemini_call),
        Provider("Ollama (local)", lambda: True, _ollama_call),
    ]


PROVIDERS = _build_providers()


@dataclass
class ProviderRunResult:
    provider: str
    status: str  # "success" | "failed" | "skipped_no_key" | "skipped_daily_limit"
    raw_text: Optional[str] = None
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


def _attempts_since_midnight_utc(db: Session, provider_name: str) -> int:
    since = datetime.combine(date.today(), midnight_time.min)
    return (
        db.query(AIProviderAttempt)
        .filter(AIProviderAttempt.provider == provider_name, AIProviderAttempt.created_at >= since)
        .count()
    )


def _run_one_provider(
    provider: Provider, system_prompt: str, user_message: str, response_mime_type: Optional[str]
) -> ProviderRunResult:
    start = time_module.monotonic()
    try:
        text = provider.call(system_prompt, user_message, response_mime_type)
        return ProviderRunResult(
            provider=provider.name, status="success", raw_text=text, elapsed_seconds=time_module.monotonic() - start
        )
    except Exception as exc:
        return ProviderRunResult(
            provider=provider.name,
            status="failed",
            error=str(exc)[:500],
            elapsed_seconds=time_module.monotonic() - start,
        )


def call_ai_router_parallel(
    db: Session,
    system_prompt: str,
    user_message: str,
    response_mime_type: str | None = None,
) -> list[ProviderRunResult]:
    """Fires every configured, under-quota provider at once and waits for
    all of them (20s timeout each, enforced inside each adapter's own
    httpx call). Returns one ProviderRunResult per provider in PROVIDERS
    order (including skipped ones), for the admin results table. Logs
    only real attempts -- not skips -- to AIProviderAttempt."""
    results_by_name: dict[str, ProviderRunResult] = {}
    eligible: list[Provider] = []

    for provider in PROVIDERS:
        if not provider.is_configured():
            results_by_name[provider.name] = ProviderRunResult(provider=provider.name, status="skipped_no_key")
        elif _attempts_since_midnight_utc(db, provider.name) >= PROVIDER_DAILY_LIMIT:
            results_by_name[provider.name] = ProviderRunResult(provider=provider.name, status="skipped_daily_limit")
        else:
            eligible.append(provider)

    if eligible:
        with ThreadPoolExecutor(max_workers=len(eligible)) as executor:
            futures = {
                executor.submit(_run_one_provider, provider, system_prompt, user_message, response_mime_type): provider
                for provider in eligible
            }
            for future in as_completed(futures):
                result = future.result()
                results_by_name[result.provider] = result
                db.add(
                    AIProviderAttempt(
                        provider=result.provider,
                        success=(result.status == "success"),
                        error=result.error,
                    )
                )
        db.commit()

    return [results_by_name[provider.name] for provider in PROVIDERS]
