"""Pydantic models for the CareerBridge AI pipeline."""
from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SkillClassification(str, Enum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    MISSING = "missing"


class ClassifiedSkill(BaseModel):
    name: str
    classification: SkillClassification
    evidence: Optional[str] = None


class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    raw_text: str = ""


class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    country: Optional[str] = None
    city: Optional[str] = None
    remote: bool = False
    work_arrangement: str = "Any"  # Remote, Hybrid, On-site, Any
    employment_type: str = "Full-time"  # Full-time, Part-time, Internship, Contract, Freelance, Any
    experience_level: str = "Mid-level"  # Any, Internship, Entry-level, Junior, Mid-level
    type: str = "Full-time"  # legacy alias
    description: str
    description_is_snippet: bool = True  # True if preview snippet, False if full description
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    posted_date: Optional[str] = None
    url: Optional[str] = None
    source: str = "Demo Backup"  # Adzuna, Arbeitnow, Remotive, Demo Backup
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)


class JobSearchFilters(BaseModel):
    desired_role: str = ""
    country: str = ""
    city: str = ""
    work_arrangement: str = "Any"  # Any, Remote, Hybrid, On-site
    employment_type: str = "Any"   # Any, Full-time, Part-time, Internship, Contract, Freelance
    experience_level: str = "Any"  # Any, Internship, Entry-level, Junior, Mid-level
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: str = "USD"


class ApplicationStatus(str, Enum):
    SAVED = "Saved"
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"


class ApplicationRecord(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    job_url: Optional[str] = None
    source: str = "Demo"
    status: ApplicationStatus = ApplicationStatus.SAVED
    date: str = ""
    notes: str = ""
    ats_score: Optional[int] = None
    match_score: Optional[float] = None


class CoverLetter(BaseModel):
    content: str = ""
    tone: str = "Standard"  # Standard, Concise, Technical, Formal
    job_title: str = ""
    company: str = ""


class CoachMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = ""


class MatchResult(BaseModel):
    job: JobPosting
    overall_score: float = 0.0
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    relevant_keywords: List[str] = Field(default_factory=list)


class ATSAnalysis(BaseModel):
    overall_score: int = 0
    keyword_match: int = 0
    skills_match: int = 0
    experience_match: int = 0
    format_score: int = 0
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    summary: str = ""


class GapAnalysis(BaseModel):
    verified_skills: List[ClassifiedSkill] = Field(default_factory=list)
    inferred_skills: List[ClassifiedSkill] = Field(default_factory=list)
    missing_skills: List[ClassifiedSkill] = Field(default_factory=list)
    keyword_gaps: List[str] = Field(default_factory=list)
    experience_gaps: List[str] = Field(default_factory=list)
    profile_weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class OptimizedProfile(BaseModel):
    original_summary: str = ""
    optimized_summary: str = ""
    original_bullets: List[str] = Field(default_factory=list)
    optimized_bullets: List[str] = Field(default_factory=list)
    before_score: int = 0
    after_score: int = 0
    improvements_made: List[str] = Field(default_factory=list)


class OutreachPackage(BaseModel):
    recruiter_email: str = ""
    recruiter_inmail: str = ""
    interview_questions: List[str] = Field(default_factory=list)
