"""
Groq LLM provider.
Uses Groq's OpenAI-compatible API for fast inference.
Set LLM_PROVIDER=groq in .env.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re

import structlog
from groq import AsyncGroq
from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from groq.types.chat import ChatCompletion

from app.config import get_settings
from app.engines.llm.base import LLMClient
from app.engines.llm.models import (
    AffectedGroup,
    ExplanationResponse,
    FixResponse,
    SimulationResponse,
)

logger = structlog.get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# System prompts (reused from OpenAI provider)
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


class GroqProvider(LLMClient):
    """
    Groq implementation of LLMClient.
    Uses Groq's OpenAI-compatible API with retry and full error handling.
    """

    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Get a free API key from https://console.groq.com/keys"
            )
        self._client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=settings.groq_request_timeout,
            max_retries=0,  # retries handled manually for full control
        )
        self._model = settings.groq_model
        logger.info("Groq provider initialised", model=self._model)

    async def generate_explanation(self, prompt: str) -> ExplanationResponse:
        """Generate a plain English explanation of an accessibility violation."""
        raw = await self._complete_with_retry(
            system_prompt=_EXPLANATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="explanation",
        )
        return _parse_explanation(raw)

    async def generate_fix(self, prompt: str) -> FixResponse:
        """Generate an accessibility code fix."""
        raw = await self._complete_with_retry(
            system_prompt=_FIX_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="fix",
        )
        return _parse_fix(raw)

    async def generate_simulation(self, prompt: str) -> SimulationResponse:
        """Generate a disability simulation description."""
        raw = await self._complete_with_retry(
            system_prompt=_SIMULATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="simulation",
        )
        return _parse_simulation(raw)

    async def _complete_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        label: str,
    ) -> str:
        """
        Sends a chat completion request to Groq.
        Retries on transient errors (rate limit, timeout, connection).
        Raises ValueError on permanent errors.
        """
        max_retries = settings.groq_max_retries

        for attempt in range(1, max_retries + 1):
            try:
                response: ChatCompletion = await self._client.chat.completions.create(
                    model=self._model,
                    max_tokens=settings.groq_max_tokens,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or ""
                logger.info(
                    "Groq request succeeded",
                    label=label,
                    attempt=attempt,
                    model=self._model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                )
                return content

            except AuthenticationError as exc:
                logger.error("Groq authentication failed", error=str(exc))
                raise ValueError("Groq authentication failed. Check your API key.") from exc

            except BadRequestError as exc:
                logger.error("Groq bad request", error=str(exc), label=label)
                raise ValueError(f"Groq rejected the request: {exc.message}") from exc

            except RateLimitError as exc:
                wait = _backoff_seconds(attempt)
                logger.warning(
                    "Groq rate limited",
                    attempt=attempt,
                    wait_seconds=wait,
                    error=str(exc),
                )
                if attempt >= max_retries:
                    raise ValueError("Groq rate limit exceeded. Please retry later.") from exc
                await asyncio.sleep(wait)

            except APITimeoutError as exc:
                logger.warning(
                    "Groq request timed out",
                    attempt=attempt,
                    timeout=settings.groq_request_timeout,
                )
                if attempt >= max_retries:
                    raise ValueError(
                        f"Groq request timed out after {settings.groq_request_timeout}s."
                    ) from exc
                await asyncio.sleep(_backoff_seconds(attempt))

            except APIConnectionError as exc:
                logger.warning(
                    "Groq connection error",
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt >= max_retries:
                    raise ValueError("Could not connect to Groq API.") from exc
                await asyncio.sleep(_backoff_seconds(attempt))

            except Exception as exc:
                logger.error(
                    "Unexpected Groq error",
                    error=str(exc),
                    label=label,
                    exc_info=True,
                )
                raise ValueError(f"Unexpected error calling Groq: {exc}") from exc

        raise ValueError("Groq request failed after all retries.")


# ---------------------------------------------------------------------------
# Response parsers (reused from OpenAI provider)
# ---------------------------------------------------------------------------


def _parse_explanation(raw: str) -> ExplanationResponse:
    """Parses the EXPLANATION / AFFECTED_USERS / WHY_IT_MATTERS format."""
    fields = _extract_fields(raw, ["EXPLANATION", "AFFECTED_USERS", "WHY_IT_MATTERS"])
    return ExplanationResponse(
        explanation=fields.get("EXPLANATION") or raw.strip(),
        affected_users=fields.get("AFFECTED_USERS") or "Users with disabilities",
        why_it_matters=fields.get("WHY_IT_MATTERS") or "",
    )


def _parse_fix(raw: str) -> FixResponse:
    """
    Parses the JSON fix response format.

    Expected format:
    {
      "problem": "...",
      "recommended_fix": "...",
      "code_example": "...",
      "implementation_steps": ["...", "..."],
      "priority": "critical|serious|moderate|minor"
    }

    Robustly handles:
      - Markdown code fences (```json ... ```) anywhere in the response
      - Extra text before/after the JSON
      - Trailing commas
      - Single quotes (Python-style dict-like output from some LLMs)
    """
    cleaned = raw.strip()

    # --- Step 1: Extract JSON from markdown code fences anywhere in the text ---
    fence_pattern = re.compile(r'```(?:json)?\s*\n?(.*?)```', re.DOTALL)
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # --- Step 2: Find the outermost { ... } block (handle all text wrappers) ---
    brace_start = cleaned.find('{')
    brace_end = cleaned.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        cleaned = cleaned[brace_start:brace_end + 1]

    # --- Step 3: Normalise single-quote Python-style dicts to valid JSON ---
    data = None
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            # Fix trailing commas before/after closing braces/brackets
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
            # Replace single-quoted keys with double-quoted keys
            cleaned = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', cleaned)
            # Replace single-quoted string values with double-quoted values
            cleaned = re.sub(r":\s*'([^']*)'", r': "\1"', cleaned)
            try:
                data = json.loads(cleaned)
            except (json.JSONDecodeError, TypeError):
                data = None
    else:
        data = None

    if data is not None and isinstance(data, dict):
        return FixResponse(
            problem=data.get("problem", ""),
            recommended_fix=data.get("recommended_fix", ""),
            code_example=data.get("code_example", ""),
            implementation_steps=data.get("implementation_steps", []),
            priority=data.get("priority", "moderate"),
        )

    # --- Fallback: try the old KEY: VALUE format ---
    fields = _extract_fields(raw, ["FIX_TYPE", "DESCRIPTION", "FIX_CODE"])
    fix_type = (fields.get("FIX_TYPE") or "html").lower().strip()
    if fix_type not in ("html", "css", "jsx", "aria"):
        fix_type = "html"
    return FixResponse(
        problem=fields.get("DESCRIPTION") or raw.strip(),
        recommended_fix=fields.get("DESCRIPTION") or "",
        code_example=fields.get("FIX_CODE") or raw.strip(),
        implementation_steps=[f"Apply the {fix_type} fix shown above."],
        priority="moderate",
    )


def _parse_simulation(raw: str) -> SimulationResponse:
    """
    Parses the JSON simulation response format.

    Expected format:
    {
      "affected_groups": [
        {"disability": "blind", "impact": "..."},
        {"disability": "low_vision", "impact": "..."},
        {"disability": "motor", "impact": "..."},
        {"disability": "cognitive", "impact": "..."}
      ],
      "severity_explanation": "...",
      "user_experience": "..."
    }

    Robustly handles Markdown code fences and single-quote Python-style dicts.
    Falls back to the old KEY: VALUE format if JSON parsing fails.
    """
    cleaned = raw.strip()

    # Extract JSON from markdown code fences
    fence_pattern = re.compile(r'```(?:json)?\s*\n?(.*?)```', re.DOTALL)
    fence_match = fence_pattern.search(cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # Find the outermost { ... } block
    brace_start = cleaned.find('{')
    brace_end = cleaned.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        cleaned = cleaned[brace_start:brace_end + 1]

    data = None
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            # Fix trailing commas
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
            # Replace single-quoted keys with double-quoted keys
            cleaned = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', cleaned)
            # Replace single-quoted string values with double-quoted values
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

    # Fallback: try the old KEY: VALUE format
    fields = _extract_fields(raw, ["DESCRIPTION", "USER_EXPERIENCE", "RECOMMENDATIONS"])
    return SimulationResponse(
        affected_groups=[],
        severity_explanation=fields.get("DESCRIPTION") or raw.strip(),
        user_experience=fields.get("USER_EXPERIENCE") or "",
    )


def _extract_fields(raw: str, keys: list[str]) -> dict[str, str]:
    """
    Parses a response formatted as:
        KEY: value
        MULTILINE_KEY:
        line1
        line2
    """
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


def _backoff_seconds(attempt: int) -> float:
    """Exponential backoff: 2s, 4s, 8s ..."""
    return min(2 ** attempt, 30)