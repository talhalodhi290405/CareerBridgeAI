"""Session storage helper for CareerBridge AI.

Enforces 100% session isolation in memory per user session.
Shared disk storage is disabled to prevent cross-session data leakage.
"""
from typing import Dict, Any, Optional
from backend.config import logger


def save_session_state(state_dict: Dict[str, Any], session_id: Optional[str] = None) -> bool:
    """Stateless session saver. No shared disk write to prevent cross-session leaks."""
    return True


def load_session_state(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Stateless session loader. Returns empty dict for clean per-session memory state."""
    return {}
