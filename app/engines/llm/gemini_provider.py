"""
Google Gemini LLM provider.
Uses Gemini API — free tier available (60 requests/min, no credit card needed).
Set LLM_PROVIDER=gemini in .env.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Optional

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.config import get_settings
from app.engines.llm.base import LLMClient
from app.engines.llm.models import ExplanationResponse, FixResponse, SimulationResponse, AffectedGroup

logger = structlog.get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_EXPLANATION_SYSTEM_PROMPT = """You are an expert web accessibility consultant.
Your job is to explain accessibility violations in plain English to developers who are not accessibility experts.
Always respond in this exact format with no extra text:

EXPLANATION: <one or two sentences explaining what the issue is>
AFFECTED_USERS: <which disability groups are affected and how>
WHY_IT_MATTERS: <why this matters legally and ethically, one sentence>"""

_FIX_SYSTEM_PROMPT = """You are an expert web accessibility engineer.
Your job is to analyze accessibility violations and provide structured remediation guidance.
Always respond in this exact JSON format with no extra text:

{
  "problem": "A clear, one-sentence description of the accessibility issue",
  "recommended_fix": "Detailed step-by-step explanation of how to fix the issue, including which HTML attributes, CSS properties, or ARIA attributes to use, and why",
  "code_example": "A complete, ready-to-use code snippet showing the fixed version. Include the corrected HTML element with appropriate attributes, ARIA labels, or CSS",
  "implementation_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
  "priority": "critical" or "serious" or "moderate" or "minor"
}"""

_SIMULATION_SYSTEM_PROMPT = """You are an expert in accessibility and disability simulation.
Your job is to simulate how an accessibility violation affects different disability groups.
Always respond in this exact JSON format with no extra text:

{
  "affected_groups": [
    {
      "disability": "blind",
      "impact": "Describe the specific impact on blind users who rely on screen readers"
    },
    {
      "disability": "low_vision",
      "impact": "Describe the specific impact on users with low vision who may zoom or use high contrast"
    },
    {
      "disability": "motor",
      "impact": "Describe the specific impact on users with motor disabilities who navigate via keyboard"
    },
    {
      "disability": "cognitive",
      "impact": "Describe the specific impact on users with cognitive disabilities who need clear structure"
    }
  ],
  "general_user_impact": "Explain how this issue affects general users (users without disabilities) — focusing on overall usability, readability, navigation, efficiency, or user experience",
  "severity_explanation": "Explain the overall severity of this issue across disability groups",
  "user_experience": "Provide a step-by-step walkthrough of what a user with a disability experiences when encountering this barrier"
}

Use only these disability keys: blind, low_vision, motor, cognitive.
Always include all four disability groups in affected_groups, even if the impact is minimal for some.
Be specific and descriptive — avoid generic statements."""


# ---------------------------------------------------------------------------
# Rate limiter — token bucket for Gemini free tier
# ---------------------------------------------------------------------------

class GeminiRateLimiter:
    """
    Token-bucket rate limiter for Gemini API free tier.
    
    Free tier limits (as of 2026):
      - 60 requests per minute (1 req/sec sustained)
      - 30,000 input tokens per minute (500 tokens/sec sustained)
      - 1,500 requests per day
    
    Uses exponential backoff when approaching limits.
    """

    def __init__(
        self,
        max_requests_per_minute: int = 50,      # slightly under 60 to be safe
        max_input_tokens_per_minute: int = 25000, # slightly under 30k
        window_seconds: float = 60.0,
    ):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_input_tokens_per_minute = max_input_tokens_per_minute
        self.window_seconds = window_seconds

        # Sliding window tracking
        self._request_timestamps: list[float] = []
        self._token_log: list[tuple[float, int]] = []  # (timestamp, tokens)

        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 100) -> float:
        """
        Wait until a request is allowed under the rate limits.
        Returns the amount of time waited in seconds.
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        async with self._lock:
            # Prune old entries
            self._request_timestamps = [t for t in self._request_timestamps if t > cutoff]
            self._token_log = [(t, c) for t, c in self._token_log if t > cutoff]

            # Calculate current usage
            requests_in_window = len(self._request_timestamps)
            tokens_in_window = sum(c for _, c in self._token_log)

            # Calculate wait time needed
            wait_time = 0.0

            if requests_in_window >= self.max_requests_per_minute:
                # Need to wait for the oldest request to age out
                oldest = min(self._request_timestamps)
                wait_time = max(wait_time, oldest + self.window_seconds - now)

            if tokens_in_window + estimated_tokens >= self.max_input_tokens_per_minute:
                # Need to wait for token budget
                if self._token_log:
                    oldest_token = min(t for t, _ in self._token_log)
                    wait_time = max(wait_time, oldest_token + self.window_seconds - now)

            # Add small jitter to avoid thundering herd
            import random
            wait_time += random.uniform(0, 0.5)

        if wait_time > 0:
            logger.info(
                "Rate limiter waiting",
                wait_seconds=round(wait_time, 2),
                requests_in_window=requests_in_window,
                tokens_in_window=tokens_in_window,
            )
            await asyncio.sleep(wait_time)

        # Record this request (before it actually happens, but that's fine)
        async with self._lock:
            self._request_timestamps.append(time.monotonic())

        return wait_time

    def record_tokens(self, tokens: int) -> None:
        """Record the actual input token count after a request."""
        now = time.monotonic()
        self._token_log.append((now, tokens))


# Global rate limiter instance
_gemini_rate_limiter = GeminiRateLimiter()


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------

_RETRYABLE = (Exception,)  # Broad retry for Gemini API errors

_retry_policy = retry(
    retry=retry_if_exception_type(_RETRYABLE),
    stop=stop_after_attempt(5),   # Increased from 3 to 5
    wait=wait_exponential(multiplier=2, min=4, max=60),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=False,
)


def _extract_retry_delay(error_body: str) -> Optional[float]:
    """
    Parse the retryDelay from Gemini 429 error response details.
    The error body contains something like:
      'details': [{'@type': '...', 'retryDelay': '55s'}]
    Returns seconds as float, or None if not found.
    """
    try:
        # Try to find "retryDelay": "Xs" or "retryDelay": "X.Ys"
        match = re.search(r'retryDelay["\']\s*:\s*["\'](\d+\.?\d*)s["\']', error_body)
        if match:
            return float(match.group(1))
    except (ValueError, TypeError):
        pass
    return None


def _extract_quota_details(error_body: str) -> dict:
    """
    Extract structured quota violation info from the error body.
    Returns a dict with metric names and their limits.
    """
    details = {
        "metrics_exceeded": [],
        "retry_delay_seconds": None,
        "full_error_body": error_body,
    }

    # Extract retry delay
    delay = _extract_retry_delay(error_body)
    if delay is not None:
        details["retry_delay_seconds"] = delay

    # Extract quota metric violations
    # Pattern: "quotaMetric": "some.metric.name"
    metrics = re.findall(r'quotaMetric["\']:\s*["\']([^"\']+)["\']', error_body)
    details["metrics_exceeded"] = list(set(metrics))

    return details


class GeminiProvider(LLMClient):
    """
    Google Gemini implementation of LLMClient.
    Uses the Gemini API with free tier support.
    """

    def __init__(self) -> None:
        import google.genai as genai

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. "
                "Get a free API key from https://aistudio.google.com/apikey"
            )
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        logger.info("Gemini provider initialised", model=self._model)

    async def generate_explanation(self, prompt: str) -> ExplanationResponse:
        raw = await self._complete(
            system_prompt=_EXPLANATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="explanation",
        )
        return _parse_explanation(raw)

    async def generate_fix(self, prompt: str) -> FixResponse:
        raw = await self._complete(
            system_prompt=_FIX_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="fix",
        )
        return _parse_fix(raw)

    async def generate_simulation(self, prompt: str) -> SimulationResponse:
        raw = await self._complete(
            system_prompt=_SIMULATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="simulation",
        )
        return _parse_simulation(raw)

    async def _complete(self, system_prompt: str, user_prompt: str, label: str) -> str:
        """Send a request to Gemini and return the response text."""
        import google.genai as genai
        from google.genai.types import GenerateContentConfig

        estimated_tokens = len(system_prompt) + len(user_prompt) // 4  # rough estimate

        for attempt in range(1, 6):  # max 5 attempts
            try:
                # Apply rate limiter before sending the request
                await _gemini_rate_limiter.acquire(estimated_tokens=estimated_tokens)

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=f"{system_prompt}\n\n{user_prompt}",
                    config=GenerateContentConfig(
                        max_output_tokens=settings.gemini_max_tokens,
                        temperature=0.2,
                    ),
                )
                content = response.text or ""
                logger.info(
                    "Gemini request succeeded",
                    label=label,
                    attempt=attempt,
                    response_length=len(content),
                )
                return content

            except Exception as exc:
                error_str = str(exc)
                error_repr = repr(exc)
                logger.warning(
                    "Gemini request failed",
                    label=label,
                    attempt=attempt,
                    error=error_str[:500],  # Log first 500 chars
                    full_error=error_repr[:2000],  # Log full repr for diagnosis
                )

                # Extract retry delay from the error if present
                retry_delay = _extract_retry_delay(error_str)

                # Log quota details for diagnosis
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    quota_details = _extract_quota_details(error_str)
                    logger.error(
                        "Gemini quota exceeded — full diagnosis",
                        label=label,
                        attempt=attempt,
                        retry_delay_seconds=quota_details["retry_delay_seconds"],
                        metrics_exceeded=quota_details["metrics_exceeded"],
                        error_snippet=error_str[:1000],
                    )

                if attempt >= 5:
                    # Last attempt — log the complete error body for diagnosis
                    logger.error(
                        "Gemini request failed after all retries",
                        label=label,
                        final_error=error_repr[:3000],
                    )
                    raise

                # Wait before retrying — use server-suggested delay if available
                if retry_delay is not None:
                    # Add 2 seconds buffer to the server's suggested delay
                    wait_time = retry_delay + 2.0
                    logger.info(
                        "Waiting for retry delay from server",
                        label=label,
                        attempt=attempt,
                        server_delay=retry_delay,
                        actual_wait=round(wait_time, 1),
                    )
                else:
                    # Exponential backoff: 4s, 8s, 16s, 32s
                    wait_time = 2 ** (attempt + 1)
                    logger.info(
                        "Waiting with exponential backoff",
                        label=label,
                        attempt=attempt,
                        wait_time=wait_time,
                    )

                await asyncio.sleep(wait_time)

        return ""


# ---------------------------------------------------------------------------
# Response parsers (same as OpenAI provider)
# ---------------------------------------------------------------------------

def _extract_fields(raw: str, keys: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    lines = raw.strip().splitlines()
    current_key: str | None = None
    current_lines: list[str] = []

    for line in lines:
        matched_key = None
        for key in keys:
            if line.upper().startswith(f"{key}:"):
                matched_key = key
                break

        if matched_key:
            if current_key:
                result[current_key] = "\n".join(current_lines).strip()
            current_key = matched_key
            after_colon = line[len(matched_key) + 1:].strip()
            current_lines = [after_colon] if after_colon else []
        elif current_key:
            current_lines.append(line)

    if current_key:
        result[current_key] = "\n".join(current_lines).strip()

    return result


def _parse_explanation(raw: str) -> ExplanationResponse:
    fields = _extract_fields(raw, ["EXPLANATION", "AFFECTED_USERS", "WHY_IT_MATTERS"])
    return ExplanationResponse(
        explanation=fields.get("EXPLANATION") or raw.strip(),
        affected_users=fields.get("AFFECTED_USERS") or "Users with disabilities",
        why_it_matters=fields.get("WHY_IT_MATTERS") or "",
    )


def _parse_fix(raw: str) -> FixResponse:
    cleaned = raw.strip()

    fence_pattern = re.compile(r'```(?:json)?\s*\n?(.*?)```', re.DOTALL)
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    brace_start = cleaned.find('{')
    brace_end = cleaned.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        cleaned = cleaned[brace_start:brace_end + 1]

    data = None
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
            cleaned = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', cleaned)
            cleaned = re.sub(r":\s*'([^']*)'", r': "\1"', cleaned)
            try:
                data = json.loads(cleaned)
            except (json.JSONDecodeError, TypeError):
                data = None

    if data is not None and isinstance(data, dict):
        return FixResponse(
            problem=data.get("problem", ""),
            recommended_fix=data.get("recommended_fix", ""),
            code_example=data.get("code_example", ""),
            implementation_steps=data.get("implementation_steps", []),
            priority=data.get("priority", "moderate"),
        )

    fields = _extract_fields(raw, ["FIX_TYPE", "DESCRIPTION", "FIX_CODE"])
    return FixResponse(
        problem=fields.get("DESCRIPTION") or raw.strip(),
        recommended_fix=fields.get("DESCRIPTION") or "",
        code_example=fields.get("FIX_CODE") or raw.strip(),
        implementation_steps=[f"Apply the fix shown above."],
        priority="moderate",
    )


def _parse_simulation(raw: str) -> SimulationResponse:
    cleaned = raw.strip()

    fence_pattern = re.compile(r'```(?:json)?\s*\n?(.*?)```', re.DOTALL)
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    brace_start = cleaned.find('{')
    brace_end = cleaned.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        cleaned = cleaned[brace_start:brace_end + 1]

    data = None
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
            cleaned = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', cleaned)
            cleaned = re.sub(r":\s*'([^']*)'", r': "\1"', cleaned)
            try:
                data = json.loads(cleaned)
            except (json.JSONDecodeError, TypeError):
                data = None

    if data is not None and isinstance(data, dict):
        groups_raw = data.get("affected_groups", [])
        affected_groups = []
        for g in groups_raw:
            if isinstance(g, dict):
                affected_groups.append(AffectedGroup(
                    disability=g.get("disability", ""),
                    impact=g.get("impact", ""),
                ))
        return SimulationResponse(
            affected_groups=affected_groups,
            severity_explanation=data.get("severity_explanation", ""),
            user_experience=data.get("user_experience", ""),
            general_user_impact=data.get("general_user_impact", ""),
        )

    fields = _extract_fields(raw, ["DESCRIPTION", "USER_EXPERIENCE", "RECOMMENDATIONS"])
    return SimulationResponse(
        affected_groups=[],
        severity_explanation=fields.get("DESCRIPTION") or raw.strip(),
        user_experience=fields.get("USER_EXPERIENCE") or "",
    )