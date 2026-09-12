"""Centralized LLM service with provider abstraction and fallback."""
import json
import re
import time
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from backend.config import get_api_key, get_model_name, logger, LLM_TIMEOUT, LLM_MAX_RETRIES, LLM_TEMPERATURE, LLM_MAX_TOKENS

T = TypeVar("T", bound=BaseModel)


def _get_groq_client():
    """Lazily create a Groq client. Returns None if unavailable."""
    api_key = get_api_key()
    if not api_key:
        logger.warning("No Groq API key available — LLM calls will use fallback.")
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key, timeout=LLM_TIMEOUT)
    except ImportError:
        logger.warning("groq package not installed — LLM calls will use fallback.")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in code blocks first
    patterns = [
        r'```json\s*\n?(.*?)\n?```',
        r'```\s*\n?(.*?)\n?```',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # Try to find raw JSON object or array
    # Find first { or [ and match to last } or ]
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
    
    return text.strip()


ANTIGRAVITY_SYSTEM_PROMPT = "You are an elite, autonomous Digital FTE Career Architect (Antigravity System). You solve problems in real-time. You do not hallucinate. You provide precise, actionable career optimization based strictly on the user's provided CV and the real-time job market data provided in your context. Never generate fake job links."


def call_llm(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Call the LLM with retry logic. Returns raw text or None on failure."""
    client = _get_groq_client()
    if client is None:
        return None
    
    sys_p = system_prompt if system_prompt else ANTIGRAVITY_SYSTEM_PROMPT
    messages = [{"role": "system", "content": sys_p}, {"role": "user", "content": prompt}]

    
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=get_model_name(),
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            content = response.choices[0].message.content
            if content:
                return content
            logger.warning(f"LLM returned empty content (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"LLM call failed (attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}): {e}")
            if attempt < LLM_MAX_RETRIES:
                time.sleep(1.0 * (attempt + 1))  # simple backoff
    
    return None


def call_llm_structured(prompt: str, schema: Type[T], system_prompt: str = "") -> Optional[T]:
    """Call the LLM and parse/validate response into a Pydantic model.
    Returns None on failure (caller should use fallback)."""
    raw = call_llm(prompt, system_prompt)
    if raw is None:
        return None
    
    try:
        json_str = _extract_json(raw)
        data = json.loads(json_str)
        return schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Failed to parse LLM response into {schema.__name__}: {e}")
        logger.debug(f"Raw LLM response: {raw[:500]}")
        return None
