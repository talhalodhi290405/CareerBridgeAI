"""FastAPI Backend Entrypoint for CareerBridge AI deployment.

100% Stateless REST API endpoints. Every request is processed independently
without saving user profiles or uploaded resumes to global variables or disk storage.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from typing import Optional, List, Dict, Any

from backend.models import (
    CandidateProfile, JobPosting, ATSAnalysis, GapAnalysis,
    OptimizedProfile, OutreachPackage, ApplicationRecord, CoverLetter, CoachMessage
)
from backend.parser import parse_resume, validate_pdf_resume, assess_extraction_quality
from backend.rag_engine import load_jobs, match_candidate_to_jobs
from backend.ats_engine import analyze_ats, analyze_gaps
from backend.optimizer import optimize_profile
from backend.job_service import search_live_jobs, JobSearchFilters
from backend.cover_letter import generate_cover_letter
from backend.outreach import generate_outreach
from backend.coach import ask_career_coach
from backend.demo import get_demo_candidate, get_demo_ats_analysis

app = FastAPI(
    title="CareerBridge AI Backend API",
    description="AI Career Intelligence & ATS Strategy Engine API — 100% Stateless",
    version="1.0.0"
)


@app.get("/")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "CareerBridge AI API", "stateless": True}


@app.post("/api/resume/parse", response_model=Dict[str, Any])
async def api_parse_resume(file: UploadFile = File(...)):
    contents = await file.read()
    val = validate_pdf_resume(contents, filename=file.filename or "resume.pdf")
    if not val.accepted:
        raise HTTPException(status_code=400, detail=val.user_message)
    profile = parse_resume(contents)
    if not profile:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
    quality = assess_extraction_quality(profile)
    return {"profile": profile.model_dump(), "quality": quality}


@app.post("/api/jobs/search", response_model=List[Dict[str, Any]])
def api_search_jobs(filters: Optional[Dict[str, Any]] = Body(default=None)):
    search_filters = JobSearchFilters.model_validate(filters) if filters else JobSearchFilters()
    jobs, msg = search_live_jobs(search_filters)
    return [j.model_dump() for j in jobs]


@app.post("/api/ats/analyze", response_model=Dict[str, Any])
def api_analyze_ats(payload: Dict[str, Any] = Body(...)):
    if "candidate" not in payload or "job" not in payload:
        raise HTTPException(status_code=400, detail="Payload must include 'candidate' and 'job'")
    candidate = CandidateProfile.model_validate(payload["candidate"])
    job = JobPosting.model_validate(payload["job"])
    ats = analyze_ats(candidate, job)
    gaps = analyze_gaps(candidate, job)
    return {"ats": ats.model_dump(), "gaps": gaps.model_dump()}


@app.post("/api/optimizer/enhance", response_model=Dict[str, Any])
def api_optimize_profile(payload: Dict[str, Any] = Body(...)):
    if "candidate" not in payload or "job" not in payload:
        raise HTTPException(status_code=400, detail="Payload must include 'candidate' and 'job'")
    candidate = CandidateProfile.model_validate(payload["candidate"])
    job = JobPosting.model_validate(payload["job"])
    opt = optimize_profile(candidate, job)
    return opt.model_dump()


@app.post("/api/cover-letter/generate", response_model=Dict[str, Any])
def api_cover_letter(payload: Dict[str, Any] = Body(...)):
    if "candidate" not in payload or "job" not in payload:
        raise HTTPException(status_code=400, detail="Payload must include 'candidate' and 'job'")
    candidate = CandidateProfile.model_validate(payload["candidate"])
    job = JobPosting.model_validate(payload["job"])
    cl = generate_cover_letter(candidate, job)
    return cl.model_dump()


@app.post("/api/outreach/generate", response_model=Dict[str, Any])
def api_outreach(payload: Dict[str, Any] = Body(...)):
    if "candidate" not in payload or "job" not in payload:
        raise HTTPException(status_code=400, detail="Payload must include 'candidate' and 'job'")
    candidate = CandidateProfile.model_validate(payload["candidate"])
    job = JobPosting.model_validate(payload["job"])
    outreach = generate_outreach(candidate, job)
    return outreach.model_dump()


@app.post("/api/coach/ask", response_model=Dict[str, Any])
def api_coach_ask(payload: Dict[str, Any] = Body(...)):
    query = payload.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query string required")
    raw_hist = payload.get("history", [])
    history = [CoachMessage.model_validate(m) for m in raw_hist]
    candidate = CandidateProfile.model_validate(payload["candidate"]) if payload.get("candidate") else None
    job = JobPosting.model_validate(payload["job"]) if payload.get("job") else None
    ans = ask_career_coach(query, history, candidate, job)
    return ans.model_dump()
