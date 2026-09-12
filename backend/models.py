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
    remote: bool = False
    experience_level: str = "Mid-level"
    type: str = "Full-time"
    description: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)


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
