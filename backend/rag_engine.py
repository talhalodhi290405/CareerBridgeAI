"""Job matching engine with ChromaDB enhancement and deterministic fallback."""
import json
import os
from typing import Optional

from backend.models import JobPosting, MatchResult, CandidateProfile
from backend.config import logger

_jobs_cache: Optional[list[JobPosting]] = None


def load_jobs(jobs_path: str = None) -> list[JobPosting]:
    """Load and cache job postings from the JSON file."""
    global _jobs_cache
    if _jobs_cache is not None:
        return _jobs_cache
    
    if jobs_path is None:
        # Try multiple paths for compatibility
        for candidate_path in ["data/jobs.json", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs.json")]:
            if os.path.exists(candidate_path):
                jobs_path = candidate_path
                break
    
    if not jobs_path or not os.path.exists(jobs_path):
        logger.error("jobs.json not found")
        return []
    
    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            raw_jobs = json.load(f)
        _jobs_cache = [JobPosting.model_validate(j) for j in raw_jobs]
        logger.info(f"Loaded {len(_jobs_cache)} jobs from {jobs_path}")
        return _jobs_cache
    except Exception as e:
        logger.error(f"Failed to load jobs: {e}")
        return []


def _normalize(text: str) -> set[str]:
    """Normalize text into a set of lowercase tokens for matching."""
    return set(text.lower().replace(',', ' ').replace('.', ' ').replace('/', ' ').split())


def _compute_skill_overlap(candidate_skills: list[str], job_skills: list[str]) -> tuple[list[str], list[str]]:
    """Compute matched and missing skills between candidate and job."""
    candidate_lower = {s.lower().strip() for s in candidate_skills}
    candidate_tokens = set()
    for s in candidate_skills:
        candidate_tokens.update(_normalize(s))
    
    matched = []
    missing = []
    for skill in job_skills:
        skill_lower = skill.lower().strip()
        skill_tokens = _normalize(skill)
        # Direct match or token overlap
        if skill_lower in candidate_lower or skill_tokens.issubset(candidate_tokens):
            matched.append(skill)
        else:
            missing.append(skill)
    
    return matched, missing


def match_candidate_to_jobs(
    candidate: CandidateProfile,
    jobs: Optional[list[JobPosting]] = None,
    top_k: int = 5,
) -> list[MatchResult]:
    """Match a candidate profile against job postings using deterministic skill/keyword scoring.
    This is the primary matching engine — no external service dependency."""
    if jobs is None:
        jobs = load_jobs()
    
    if not jobs:
        return []
    
    # Build candidate token set from skills + raw text
    candidate_skills = candidate.skills
    candidate_tokens = _normalize(candidate.raw_text)
    
    results = []
    for job in jobs:
        all_job_skills = job.required_skills + job.preferred_skills
        matched, missing = _compute_skill_overlap(candidate_skills, all_job_skills)
        
        # Score components
        req_matched, req_missing = _compute_skill_overlap(candidate_skills, job.required_skills)
        pref_matched, pref_missing = _compute_skill_overlap(candidate_skills, job.preferred_skills)
        
        # Weighted scoring
        req_total = max(len(job.required_skills), 1)
        pref_total = max(len(job.preferred_skills), 1)
        
        req_score = len(req_matched) / req_total  # 60% weight
        pref_score = len(pref_matched) / pref_total  # 20% weight
        
        # Keyword overlap from raw text (20% weight)
        job_keywords = _normalize(job.description)
        keyword_overlap = len(candidate_tokens & job_keywords) / max(len(job_keywords), 1)
        keyword_score = min(keyword_overlap * 5, 1.0)  # scale up, cap at 1
        
        overall = round((req_score * 0.6 + pref_score * 0.2 + keyword_score * 0.2) * 100, 1)
        
        # Collect relevant keywords found
        relevant_kw = sorted(list(candidate_tokens & job_keywords - {'and', 'the', 'with', 'for', 'in', 'of', 'to', 'a', 'an', 'is', 'are', 'be', 'or'}))[:10]
        
        results.append(MatchResult(
            job=job,
            overall_score=overall,
            matched_skills=matched,
            missing_skills=missing,
            relevant_keywords=relevant_kw,
        ))
    
    results.sort(key=lambda r: r.overall_score, reverse=True)
    return results[:top_k]
