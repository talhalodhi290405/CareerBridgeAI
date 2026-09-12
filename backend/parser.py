"""Resume parser using pdfplumber with structured extraction and intelligent keyword matching."""
import re
import io
from typing import Optional, List

import pdfplumber

from backend.models import CandidateProfile
from backend.config import logger

COMMON_TECH_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "React", "Angular", "Vue",
    "Node.js", "Express", "FastAPI", "Django", "Flask", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "CI/CD",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas",
    "NumPy", "NLP", "Computer Vision", "REST API", "GraphQL", "HTML", "CSS", "Tailwind",
    "Bootstrap", "Data Analysis", "Agile", "Scrum", "Jira", "Figma", "Microservices", "Go",
    "Rust", "PHP", "Swift", "Kotlin", "Flutter", "Spark", "Hadoop", "Tableau", "PowerBI"
]


def extract_text_from_pdf(file_bytes: bytes) -> Optional[str]:
    """Extract text from PDF bytes. Returns None on failure."""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            if not pages:
                logger.warning("PDF contained no extractable text.")
                return None
            return "\n".join(pages)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return None


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    return match.group(0).strip() if match else None


def _extract_name(text: str) -> str:
    """Intelligently extract the candidate's name from the first few lines or email fallback."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        for line in lines[:5]:
            if len(line) < 50 and not any(kw in line.lower() for kw in ['resume', 'curriculum', 'objective', 'summary', 'http', '@', 'phone', 'page', 'github', 'linkedin', 'email']):
                if re.search(r'[a-zA-Z]{2,}', line):
                    return line

    # Email prefix fallback
    email = _extract_email(text)
    if email:
        prefix = email.split('@')[0]
        clean_prefix = re.sub(r'[^a-zA-Z]', ' ', prefix).title().strip()
        if clean_prefix and len(clean_prefix) > 2:
            return clean_prefix

    return "Candidate Profile"


def _extract_section(text: str, headers: List[str]) -> List[str]:
    """Extract content under a section header until the next section."""
    section_pattern = r'^\s*(?:' + '|'.join(re.escape(h) for h in headers) + r')\s*[:\-]?\s*$'
    all_headers = [
        'education', 'experience', 'work experience', 'professional experience', 'employment history',
        'skills', 'technical skills', 'core competencies', 'technologies', 'projects', 'certifications',
        'certificates', 'achievements', 'awards', 'summary', 'professional summary', 'objective', 'profile',
        'contact', 'references', 'publications', 'languages', 'interests', 'volunteer', 'activities',
    ]
    next_section_pattern = r'^\s*(?:' + '|'.join(re.escape(h) for h in all_headers) + r')\s*[:\-]?\s*$'
    
    lines = text.split('\n')
    capturing = False
    captured = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        if re.match(section_pattern, stripped, re.IGNORECASE):
            capturing = True
            continue
        
        if capturing and re.match(next_section_pattern, stripped, re.IGNORECASE):
            break
        
        if capturing:
            captured.append(stripped)
    
    return captured


def _extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from a skills section AND scan raw text for common technical keywords."""
    section_items = _extract_section(text, ['skills', 'technical skills', 'core competencies', 'technologies', 'tools', 'skills & expertise'])
    
    skills = set()
    for item in section_items:
        parts = re.split(r'[,;|•·/\n]', item)
        for part in parts:
            cleaned = part.strip().strip('-').strip('•').strip()
            if cleaned and len(cleaned) < 40 and not cleaned.lower().startswith(('skills', 'technical', 'core')):
                skills.add(cleaned)

    # Keyword extraction fallback / enrichment
    for tech in COMMON_TECH_SKILLS:
        pattern = r'\b' + re.escape(tech) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            skills.add(tech)

    return list(skills)


def parse_resume(file_bytes: bytes) -> Optional[CandidateProfile]:
    """Parse a PDF resume into a structured CandidateProfile.
    Returns None if the PDF cannot be read."""
    raw_text = extract_text_from_pdf(file_bytes)
    if not raw_text:
        return None
    
    return parse_resume_text(raw_text)


def parse_resume_text(raw_text: str) -> CandidateProfile:
    """Parse raw resume text into a structured CandidateProfile."""
    name = _extract_name(raw_text)
    email = _extract_email(raw_text)
    phone = _extract_phone(raw_text)
    summary_lines = _extract_section(raw_text, ['summary', 'professional summary', 'objective', 'profile', 'about me'])
    summary = " ".join(summary_lines) if summary_lines else None
    
    # If summary is missing, preview first few lines
    if not summary:
        lines = [l.strip() for l in raw_text.split('\n') if len(l.strip()) > 30][:3]
        if lines:
            summary = " ".join(lines)

    skills = _extract_skills_from_text(raw_text)
    exp = _extract_section(raw_text, ['experience', 'work experience', 'professional experience', 'employment', 'employment history'])
    edu = _extract_section(raw_text, ['education', 'academic background', 'academic'])
    proj = _extract_section(raw_text, ['projects', 'personal projects', 'key projects'])
    certs = _extract_section(raw_text, ['certifications', 'certificates', 'licenses'])
    achieve = _extract_section(raw_text, ['achievements', 'awards', 'honors'])

    return CandidateProfile(
        name=name,
        email=email,
        phone=phone,
        summary=summary,
        skills=skills,
        experience=exp if exp else [l.strip() for l in raw_text.split('\n') if len(l.strip()) > 40][:4],
        education=edu,
        projects=proj,
        certifications=certs,
        achievements=achieve,
        raw_text=raw_text,
    )
