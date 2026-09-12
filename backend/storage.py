"""Lightweight JSON storage module for session persistence across Streamlit server restarts."""
import json
import os
from typing import Dict, Any, Optional

from backend.models import (
    CandidateProfile, JobPosting, ApplicationRecord,
    JobSearchFilters, CoachMessage, ApplicationStatus,
)
from backend.config import logger

STORAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "user_session.json")


def save_session_state(state_dict: Dict[str, Any]) -> bool:
    """Save session state variables to local JSON storage."""
    try:
        data = {}
        if "candidate" in state_dict and state_dict["candidate"]:
            data["candidate"] = state_dict["candidate"].model_dump()
        
        if "saved_jobs" in state_dict and state_dict["saved_jobs"]:
            data["saved_jobs"] = [j.model_dump() for j in state_dict["saved_jobs"]]
            
        if "applications" in state_dict and state_dict["applications"]:
            data["applications"] = [a.model_dump() for a in state_dict["applications"]]
            
        if "search_filters" in state_dict and state_dict["search_filters"]:
            data["search_filters"] = state_dict["search_filters"].model_dump()

        if "coach_history" in state_dict and state_dict["coach_history"]:
            data["coach_history"] = [m.model_dump() for m in state_dict["coach_history"]]

        data["is_demo"] = state_dict.get("is_demo", False)
        data["nav_section"] = state_dict.get("nav_section", "Dashboard")

        os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Saved user session state to local storage.")
        return True
    except Exception as e:
        logger.error(f"Failed to save session state: {e}")
        return False


def load_session_state() -> Dict[str, Any]:
    """Load session state variables from local JSON storage."""
    if not os.path.exists(STORAGE_FILE):
        return {}

    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        restored = {}
        if "candidate" in data:
            restored["candidate"] = CandidateProfile.model_validate(data["candidate"])
            
        if "saved_jobs" in data:
            restored["saved_jobs"] = [JobPosting.model_validate(j) for j in data["saved_jobs"]]
            
        if "applications" in data:
            restored["applications"] = [ApplicationRecord.model_validate(a) for a in data["applications"]]

        if "search_filters" in data:
            restored["search_filters"] = JobSearchFilters.model_validate(data["search_filters"])

        if "coach_history" in data:
            restored["coach_history"] = [CoachMessage.model_validate(m) for m in data["coach_history"]]

        if "is_demo" in data:
            restored["is_demo"] = data["is_demo"]

        if "nav_section" in data:
            restored["nav_section"] = data["nav_section"]

        logger.info("Loaded user session state from local storage.")
        return restored
    except Exception as e:
        logger.error(f"Failed to load session state: {e}")
        return {}
