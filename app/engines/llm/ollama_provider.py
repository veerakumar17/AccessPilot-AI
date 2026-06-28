"""
Ollama LLM provider.
Active by default during development (LLM_PROVIDER=ollama).
"""
from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

from app.config import get_settings
from app.engines.llm.base import LLMClient
from app.engines.llm.models import ExplanationResponse, FixResponse, SimulationResponse
from app.core.exceptions import OpenAIException

logger = structlog.get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# System prompts (same as OpenAI to ensure consistent output format)
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


class OllamaProvider(LLMClient):
    """
    Ollama implementation of LLMClient.
    Communicates with a local Ollama server via HTTP API.
    Active during development to avoid OpenAI API costs.
    """

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_request_timeout
        logger.info(
            "Ollama provider initialised",
            base_url=self.base_url,
            model=self.model,
            timeout=self.timeout,
        )

    async def generate_explanation(self, prompt: str) -> ExplanationResponse:
        """Generate a plain English explanation of an accessibility violation."""
        raw = await self._complete(
            system_prompt=_EXPLANATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="explanation",
        )
        return _parse_explanation(raw)

    async def generate_fix(self, prompt: str) -> FixResponse:
        """Generate an accessibility code fix."""
        raw = await self._complete(
            system_prompt=_FIX_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="fix",
        )
        return _parse_fix(raw)

    async def generate_simulation(self, prompt: str) -> SimulationResponse:
        """Generate a disability simulation description."""
        raw = await self._complete(
            system_prompt=_SIMULATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            label="simulation",
        )
        return _parse_simulation(raw)

    async def _complete(
        self,
        system_prompt: str,
        user_prompt: str,
        label: str,
    ) -> str:
        """
        Sends a chat completion request to the local Ollama server.
        Retries on connection errors with exponential backoff.
        """
        url = f"{self.base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": settings.openai_max_tokens,
            },
        }

        max_retries = 3
        last_error: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

                content = data.get("message", {}).get("content", "")
                logger.info(
                    "Ollama request succeeded",
                    label=label,
                    attempt=attempt,
                    model=self.model,
                )
                return content

            except httpx.ConnectError as exc:
                last_error = exc
                logger.warning(
                    "Ollama connection failed — is the server running?",
                    url=self.base_url,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(_backoff_seconds(attempt))
                continue

            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(
                    "Ollama request timed out",
                    attempt=attempt,
                    timeout=self.timeout,
                )
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(_backoff_seconds(attempt))
                continue

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Ollama returned error status",
                    status_code=exc.response.status_code,
                    body=exc.response.text,
                    label=label,
                )
                raise OpenAIException(
                    f"Ollama returned HTTP {exc.response.status_code}: {exc.response.text}"
                ) from exc

            except Exception as exc:
                logger.error(
                    "Unexpected Ollama error",
                    error=str(exc),
                    label=label,
                    exc_info=True,
                )
                raise OpenAIException(f"Unexpected error calling Ollama: {exc}") from exc

        raise OpenAIException(
            f"Ollama request failed after {max_retries} retries. "
            f"Last error: {last_error}. "
            f"Ensure Ollama is running at {self.base_url}"
        )


# ---------------------------------------------------------------------------
# Response parsers (shared with OpenAI provider — same format expected)
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
      - Single quotes (Python-style dict-like output from Ollama)
    """
    import json
    import re

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
    # Replace single quotes around keys and string values with double quotes
    # This handles Ollama returning dict-like text instead of strict JSON
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            data = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            # Fix trailing commas before/after closing braces/brackets
            cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
            # Replace single-quoted keys with double-quoted keys
            cleaned = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', cleaned)
            # Replace single-quoted string values with double-quoted values
            # Be careful not to replace already-escaped quotes
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
    import json
    import re

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
        from app.engines.llm.models import AffectedGroup
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
    """Parses KEY: value formatted responses."""
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