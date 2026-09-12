"""FastAPI Backend Entrypoint for CareerBridge AI deployment."""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from typing import Optional, List, Dict, Any

from backend.models import (
    CandidateProfile, JobPosting, ATSAnalysis, GapAnalysis,
    OptimizedProfile, OutreachPackage, ApplicationRecord, CoverLetter
)
from backend.parser import parse_resume, validate_pdf_resume, assess_extraction_quality
from backend.rag_engine import load_jobs, match_candidate_to_jobs
from backend.ats_engine import analyze_ats, analyze_gaps
from backend.optimizer import optimize_profile
from backend.job_service import search_live_jobs
from backend.cover_letter import generate_cover_letter
from backend.coach import ask_career_coach
from backend.demo import get_demo_candidate, get_demo_ats_analysis

app = FastAPI(
    title="CareerBridge AI Backend API",
    description="AI Career Intelligence & ATS Strategy Engine API",
    version="1.0.0"
)

@app.get("/")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "CareerBridge AI API"}

@app.post("/api/resume/parse", response_model=Dict[str, Any])
async def api_parse_resume(file: UploadFile = File(...)):
    contents = await file.read()
    val = validate_pdf_resume(contents, filename=file.filename)
    if not val.accepted:
        raise HTTPException(status_code=400, detail=val.user_message)
    profile = parse_resume(contents)
    if not profile:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
    quality = assess_extraction_quality(profile)
    return {"profile": profile.model_dump(), "quality": quality}

@app.get("/api/jobs/search", response_model=List[Dict[str, Any]])
def api_search_jobs(role: str = "Software Engineer", location: str = ""):
    jobs = search_live_jobs(role=role, location=location)
    return [j.model_dump() for j in jobs]
