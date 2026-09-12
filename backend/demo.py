"""Demo data loader for CareerBridge AI fallback mode."""
import json
import os
from typing import Optional

from backend.models import (
    CandidateProfile, JobPosting, MatchResult, ATSAnalysis,
    GapAnalysis, OptimizedProfile, OutreachPackage, ClassifiedSkill,
    SkillClassification,
)
from backend.config import logger


_demo_data: Optional[dict] = None


def _load_demo_file() -> dict:
    """Load and cache the demo backup JSON."""
    global _demo_data
    if _demo_data is not None:
        return _demo_data

    for path in [
        "data/demo_backup.json",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo_backup.json"),
    ]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _demo_data = json.load(f)
                logger.info(f"Demo backup loaded from {path}")
                return _demo_data
            except Exception as e:
                logger.error(f"Failed to load demo backup: {e}")

    logger.error("demo_backup.json not found")
    _demo_data = {}
    return _demo_data


def get_demo_candidate() -> CandidateProfile:
    """Get the demo candidate profile."""
    data = _load_demo_file()
    return CandidateProfile.model_validate(data.get("candidate", {}))


def get_demo_target_job_id() -> str:
    """Get the target job ID for the demo."""
    data = _load_demo_file()
    return data.get("target_job_id", "job_1")


def get_demo_ats_analysis() -> ATSAnalysis:
    """Get pre-computed demo ATS analysis."""
    data = _load_demo_file()
    return ATSAnalysis.model_validate(data.get("ats_analysis", {}))


def get_demo_gap_analysis() -> GapAnalysis:
    """Get pre-computed demo gap analysis."""
    data = _load_demo_file()
    raw = data.get("gap_analysis", {})

    # Convert skill classification strings to enums
    def _parse_skills(skill_list: list) -> list[ClassifiedSkill]:
        result = []
        for s in skill_list:
            result.append(ClassifiedSkill(
                name=s["name"],
                classification=SkillClassification(s["classification"]),
                evidence=s.get("evidence"),
            ))
        return result

    return GapAnalysis(
        verified_skills=_parse_skills(raw.get("verified_skills", [])),
        inferred_skills=_parse_skills(raw.get("inferred_skills", [])),
        missing_skills=_parse_skills(raw.get("missing_skills", [])),
        keyword_gaps=raw.get("keyword_gaps", []),
        experience_gaps=raw.get("experience_gaps", []),
        profile_weaknesses=raw.get("profile_weaknesses", []),
        recommendations=raw.get("recommendations", []),
    )


def get_demo_optimized_profile() -> OptimizedProfile:
    """Get pre-computed demo optimized profile."""
    data = _load_demo_file()
    return OptimizedProfile.model_validate(data.get("optimized_profile", {}))


def get_demo_outreach() -> OutreachPackage:
    """Get pre-computed demo outreach package."""
    data = _load_demo_file()
    raw = data.get("outreach", {})
    return OutreachPackage.model_validate(raw)


def get_demo_match_result(job: JobPosting) -> MatchResult:
    """Get pre-computed demo match result."""
    data = _load_demo_file()
    raw = data.get("match_result", {})
    return MatchResult(
        job=job,
        overall_score=raw.get("overall_score", 62.5),
        matched_skills=raw.get("matched_skills", []),
        missing_skills=raw.get("missing_skills", []),
        relevant_keywords=raw.get("relevant_keywords", []),
    )
