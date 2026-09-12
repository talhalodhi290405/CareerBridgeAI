"""Centralized configuration for CareerBridge AI."""
import os
import logging

logger = logging.getLogger("careerbridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- LLM Configuration ---
DEFAULT_MODEL = "llama-3.1-8b-instant"
LLM_TIMEOUT = 30  # seconds
LLM_MAX_RETRIES = 2
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 2048


def get_api_key() -> str | None:
    """Retrieve Groq API key from Streamlit secrets or environment variables.
    Returns None if no key is available (triggers demo mode)."""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        import streamlit as st
        key = st.secrets.get("GROQ_API_KEY")
        if key and key != "your_groq_api_key_here":
            return key
    except Exception:
        pass
    
    # Fall back to environment variable
    key = os.environ.get("GROQ_API_KEY")
    if key and key != "your_groq_api_key_here":
        return key
    
    return None


def is_demo_mode() -> bool:
    """Check if the application should run in demo mode (no API key available)."""
    return get_api_key() is None


def get_model_name() -> str:
    """Get the configured LLM model name."""
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)
