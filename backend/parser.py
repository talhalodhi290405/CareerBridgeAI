"""Resume parser using pdfplumber with structured extraction."""
import re
import io
from typing import Optional

import pdfplumber

from backend.models import CandidateProfile
from backend.config import logger


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


def _extract_name(text: str) -> Optional[str]:
    """Attempt to extract the candidate's name from the first few lines."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return None
    # The first non-empty line is usually the name
    first_line = lines[0]
    # Skip if it looks like a section header or contains common non-name patterns
    if len(first_line) < 60 and not any(kw in first_line.lower() for kw in ['resume', 'curriculum', 'objective', 'summary', 'http', '@', 'phone']):
        return first_line
    return None


def _extract_section(text: str, headers: list[str]) -> list[str]:
    """Extract content under a section header until the next section."""
    section_pattern = r'^\s*(?:' + '|'.join(headers) + r')\s*[:\-]?\s*$'
    all_headers = [
        'education', 'experience', 'work experience', 'professional experience',
        'skills', 'technical skills', 'projects', 'certifications', 'certificates',
        'achievements', 'awards', 'summary', 'professional summary', 'objective',
        'contact', 'references', 'publications', 'languages', 'interests',
        'volunteer', 'activities', 'training', 'courses',
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


def _extract_skills_from_text(text: str) -> list[str]:
    """Extract skills from a skills section or from the full text."""
    section_items = _extract_section(text, ['skills', 'technical skills', 'core competencies', 'technologies'])
    
    skills = []
    for item in section_items:
        # Split by common delimiters
        parts = re.split(r'[,;|•·]', item)
        for part in parts:
            cleaned = part.strip().strip('-').strip('•').strip()
            if cleaned and len(cleaned) < 50 and not cleaned.lower().startswith(('skills', 'technical')):
                skills.append(cleaned)
    
    return skills if skills else []


def parse_resume(file_bytes: bytes) -> Optional[CandidateProfile]:
    """Parse a PDF resume into a structured CandidateProfile.
    Returns None if the PDF cannot be read."""
    raw_text = extract_text_from_pdf(file_bytes)
    if not raw_text:
        return None
    
    return parse_resume_text(raw_text)


def parse_resume_text(raw_text: str) -> CandidateProfile:
    """Parse raw resume text into a structured CandidateProfile."""
    return CandidateProfile(
        name=_extract_name(raw_text),
        email=_extract_email(raw_text),
        phone=_extract_phone(raw_text),
        summary=" ".join(_extract_section(raw_text, ['summary', 'professional summary', 'objective', 'profile'])) or None,
        skills=_extract_skills_from_text(raw_text),
        experience=_extract_section(raw_text, ['experience', 'work experience', 'professional experience', 'employment']),
        education=_extract_section(raw_text, ['education', 'academic']),
        projects=_extract_section(raw_text, ['projects', 'personal projects', 'academic projects']),
        certifications=_extract_section(raw_text, ['certifications', 'certificates', 'licenses']),
        achievements=_extract_section(raw_text, ['achievements', 'awards', 'honors']),
        raw_text=raw_text,
    )
