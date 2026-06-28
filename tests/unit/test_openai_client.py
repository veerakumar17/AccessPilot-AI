import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, RateLimitError

from app.core.exceptions import OpenAIException
from app.engines.openai_client import (
    ExplanationResponse,
    FixResponse,
    OpenAIClient,
    _OpenAIClientSingleton,
    _backoff_seconds,
    _extract_fields,
    _parse_explanation,
    _parse_fix,
    get_openai_client,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chat_response(content: str) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage.total_tokens = 120
    return response


def make_client(mock_response_content: str = "") -> tuple[OpenAIClient, AsyncMock]:
    """Returns an OpenAIClient with a mocked internal _client."""
    with patch("app.engines.openai_client.settings") as mock_settings:
        mock_settings.openai_api_key = "sk-test"
        mock_settings.openai_model = "gpt-4o"
        mock_settings.openai_max_tokens = 512
        mock_settings.openai_request_timeout = 30
        mock_settings.openai_max_retries = 3
        client = OpenAIClient.__new__(OpenAIClient)

    mock_inner = AsyncMock()
    mock_inner.chat.completions.create.return_value = make_chat_response(mock_response_content)
    client._client = mock_inner
    return client, mock_inner


# ---------------------------------------------------------------------------
# _extract_fields
# ---------------------------------------------------------------------------

def test_extract_fields_single_line_values():
    raw = "EXPLANATION: Images must have alt text.\nAFFECTED_USERS: Blind users.\nWHY_IT_MATTERS: WCAG 1.1.1."
    result = _extract_fields(raw, ["EXPLANATION", "AFFECTED_USERS", "WHY_IT_MATTERS"])
    assert result["EXPLANATION"] == "Images must have alt text."
    assert result["AFFECTED_USERS"] == "Blind users."
    assert result["WHY_IT_MATTERS"] == "WCAG 1.1.1."


def test_extract_fields_multiline_value():
    raw = "FIX_CODE:\n<img src='hero.jpg'\n     alt='Hero banner'>"
    result = _extract_fields(raw, ["FIX_TYPE", "DESCRIPTION", "FIX_CODE"])
    assert "<img src='hero.jpg'" in result["FIX_CODE"]
    assert "alt='Hero banner'>" in result["FIX_CODE"]


def test_extract_fields_missing_key_returns_empty():
    raw = "EXPLANATION: Some text."
    result = _extract_fields(raw, ["EXPLANATION", "AFFECTED_USERS", "WHY_IT_MATTERS"])
    assert result.get("AFFECTED_USERS") is None


def test_extract_fields_case_insensitive_matching():
    raw = "explanation: Lower case key."
    result = _extract_fields(raw, ["EXPLANATION"])
    assert result.get("EXPLANATION") == "Lower case key."


def test_extract_fields_empty_raw():
    assert _extract_fields("", ["EXPLANATION"]) == {}


def test_extract_fields_value_on_same_line_as_key():
    raw = "FIX_TYPE: jsx\nDESCRIPTION: Add aria-label."
    result = _extract_fields(raw, ["FIX_TYPE", "DESCRIPTION"])
    assert result["FIX_TYPE"] == "jsx"


# ---------------------------------------------------------------------------
# _parse_explanation
# ---------------------------------------------------------------------------

def test_parse_explanation_full_format():
    raw = (
        "EXPLANATION: The image has no alt text.\n"
        "AFFECTED_USERS: Blind users using screen readers.\n"
        "WHY_IT_MATTERS: Violates WCAG 1.1.1."
    )
    result = _parse_explanation(raw)
    assert isinstance(result, ExplanationResponse)
    assert result.explanation == "The image has no alt text."
    assert "Blind users" in result.affected_users
    assert "WCAG" in result.why_it_matters


def test_parse_explanation_fallback_on_malformed_response():
    raw = "This image needs alt text."
    result = _parse_explanation(raw)
    assert result.explanation == raw.strip()
    assert result.affected_users == "Users with disabilities"
    assert result.why_it_matters == ""


def test_parse_explanation_to_dict():
    result = ExplanationResponse(
        explanation="Missing alt text.",
        affected_users="Blind users.",
        why_it_matters="WCAG 1.1.1 compliance.",
    )
    d = result.to_dict()
    assert d["explanation"] == "Missing alt text."
    assert d["affected_users"] == "Blind users."
    assert d["why_it_matters"] == "WCAG 1.1.1 compliance."


# ---------------------------------------------------------------------------
# _parse_fix
# ---------------------------------------------------------------------------

def test_parse_fix_full_format():
    raw = (
        "FIX_TYPE: html\n"
        "DESCRIPTION: Add alt attribute to the image element.\n"
        "FIX_CODE:\n"
        '<img src="hero.jpg" alt="Hero banner promoting our product">'
    )
    result = _parse_fix(raw)
    assert isinstance(result, FixResponse)
    assert result.fix_type == "html"
    assert result.description == "Add alt attribute to the image element."
    assert 'alt="Hero banner' in result.fix_code


def test_parse_fix_normalises_fix_type_to_lowercase():
    raw = "FIX_TYPE: JSX\nDESCRIPTION: Fix.\nFIX_CODE:\n<button>"
    result = _parse_fix(raw)
    assert result.fix_type == "jsx"


def test_parse_fix_defaults_unknown_fix_type_to_html():
    raw = "FIX_TYPE: unknown_type\nDESCRIPTION: Fix.\nFIX_CODE:\n<button>"
    result = _parse_fix(raw)
    assert result.fix_type == "html"


def test_parse_fix_fallback_on_malformed_response():
    raw = '<img src="a.jpg" alt="description">'
    result = _parse_fix(raw)
    assert result.fix_code == raw
    assert result.fix_type == "html"


def test_parse_fix_to_dict():
    result = FixResponse(fix_code="<button>Submit</button>", fix_type="html", description="Added text.")
    d = result.to_dict()
    assert d["fix_code"] == "<button>Submit</button>"
    assert d["fix_type"] == "html"
    assert d["description"] == "Added text."


def test_parse_fix_accepts_all_valid_types():
    for fix_type in ("html", "css", "jsx", "aria"):
        raw = f"FIX_TYPE: {fix_type}\nDESCRIPTION: Fix.\nFIX_CODE:\ncode"
        result = _parse_fix(raw)
        assert result.fix_type == fix_type


# ---------------------------------------------------------------------------
# _backoff_seconds
# ---------------------------------------------------------------------------

def test_backoff_increases_with_attempt():
    assert _backoff_seconds(1) < _backoff_seconds(2) < _backoff_seconds(3)


def test_backoff_capped_at_30():
    assert _backoff_seconds(100) == 30


# ---------------------------------------------------------------------------
# OpenAIClient — raises on missing API key
# ---------------------------------------------------------------------------

def test_client_raises_on_missing_api_key():
    with patch("app.engines.openai_client.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        with pytest.raises(OpenAIException, match="OPENAI_API_KEY"):
            OpenAIClient()


# ---------------------------------------------------------------------------
# generate_explanation — success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_explanation_returns_structured_response():
    raw = (
        "EXPLANATION: The button has no accessible label.\n"
        "AFFECTED_USERS: Screen reader users cannot identify the button.\n"
        "WHY_IT_MATTERS: Violates WCAG 4.1.2."
    )
    client, mock_inner = make_client(raw)

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        mock_inner.chat.completions.create.return_value = make_chat_response(raw)
        client._client = mock_inner

        result = await client.generate_explanation("button-name violation")

    assert isinstance(result, ExplanationResponse)
    assert "button" in result.explanation.lower()
    assert result.affected_users != ""


@pytest.mark.asyncio
async def test_generate_explanation_calls_openai_with_correct_system_prompt():
    client, mock_inner = make_client("EXPLANATION: x\nAFFECTED_USERS: y\nWHY_IT_MATTERS: z")

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        await client.generate_explanation("image-alt violation on <img>")

    call_args = mock_inner.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_msg = next(m for m in messages if m["role"] == "system")
    user_msg = next(m for m in messages if m["role"] == "user")

    assert "accessibility" in system_msg["content"].lower()
    assert "image-alt" in user_msg["content"]


# ---------------------------------------------------------------------------
# generate_fix — success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_fix_returns_structured_response():
    raw = (
        "FIX_TYPE: html\n"
        "DESCRIPTION: Add descriptive alt attribute.\n"
        "FIX_CODE:\n"
        '<img src="hero.jpg" alt="Team working in office">'
    )
    client, mock_inner = make_client(raw)

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        mock_inner.chat.completions.create.return_value = make_chat_response(raw)
        client._client = mock_inner

        result = await client.generate_fix("image-alt on <img src='hero.jpg'>")

    assert isinstance(result, FixResponse)
    assert result.fix_type == "html"
    assert "alt=" in result.fix_code


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authentication_error_raises_openai_exception_immediately():
    client, mock_inner = make_client()

    mock_inner.chat.completions.create.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body={}
    )

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        with pytest.raises(OpenAIException, match="authentication"):
            await client.generate_explanation("test")

    # Must not retry on auth error
    assert mock_inner.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_bad_request_error_raises_openai_exception_immediately():
    client, mock_inner = make_client()

    mock_inner.chat.completions.create.side_effect = BadRequestError(
        message="Content policy violation", response=MagicMock(), body={}
    )

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        with pytest.raises(OpenAIException, match="rejected"):
            await client.generate_explanation("test")

    assert mock_inner.chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_rate_limit_retries_then_raises():
    client, mock_inner = make_client()

    mock_inner.chat.completions.create.side_effect = RateLimitError(
        message="Rate limited", response=MagicMock(), body={}
    )

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        with patch("app.engines.openai_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(OpenAIException, match="rate limit"):
                await client.generate_explanation("test")

    assert mock_inner.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_timeout_retries_then_raises():
    client, mock_inner = make_client()
    mock_inner.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        with patch("app.engines.openai_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(OpenAIException, match="timed out"):
                await client.generate_explanation("test")

    assert mock_inner.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_connection_error_retries_then_raises():
    client, mock_inner = make_client()
    mock_inner.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        with patch("app.engines.openai_client.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(OpenAIException, match="connect"):
                await client.generate_explanation("test")

    assert mock_inner.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_succeeds_on_second_attempt_after_rate_limit():
    raw = "EXPLANATION: Fixed.\nAFFECTED_USERS: All.\nWHY_IT_MATTERS: WCAG."
    client, mock_inner = make_client()

    mock_inner.chat.completions.create.side_effect = [
        RateLimitError(message="Rate limited", response=MagicMock(), body={}),
        make_chat_response(raw),
    ]

    with patch("app.engines.openai_client.settings") as s:
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_max_retries = 3
        s.openai_request_timeout = 30
        client._client = mock_inner

        with patch("app.engines.openai_client.asyncio.sleep", new_callable=AsyncMock):
            result = await client.generate_explanation("test")

    assert isinstance(result, ExplanationResponse)
    assert mock_inner.chat.completions.create.call_count == 2


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_openai_client_returns_same_instance():
    _OpenAIClientSingleton.reset()

    with patch("app.engines.openai_client.settings") as s:
        s.openai_api_key = "sk-test"
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_request_timeout = 30
        s.openai_max_retries = 3

        instance_a = await get_openai_client()
        instance_b = await get_openai_client()

    assert instance_a is instance_b
    _OpenAIClientSingleton.reset()


@pytest.mark.asyncio
async def test_singleton_reset_creates_new_instance():
    _OpenAIClientSingleton.reset()

    with patch("app.engines.openai_client.settings") as s:
        s.openai_api_key = "sk-test"
        s.openai_model = "gpt-4o"
        s.openai_max_tokens = 512
        s.openai_request_timeout = 30
        s.openai_max_retries = 3

        instance_a = await get_openai_client()
        _OpenAIClientSingleton.reset()
        instance_b = await get_openai_client()

    assert instance_a is not instance_b
    _OpenAIClientSingleton.reset()
