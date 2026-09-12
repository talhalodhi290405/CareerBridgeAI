"""Resume parser using pdfplumber with structured extraction and intelligent keyword matching."""
import re
import io
from typing import Optional, List, Dict, Any

import pdfplumber

from backend.models import CandidateProfile, DocumentValidationResult
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


def classify_document_type(text: str) -> Dict[str, Any]:
    """Deterministically classify text into CV, COVER_LETTER, JOB_DESCRIPTION, GENERAL_DOCUMENT, or UNKNOWN."""
    if not text or len(text.strip()) < 30:
        return {"document_type": "UNKNOWN", "confidence": 0.0, "reason": "Insufficient text length"}

    low_text = text.lower()

    # 1. Negative Signals (General Documents like Invoices, Research Papers, Syllabi)
    gen_doc_keywords = [
        "invoice", "tax invoice", "total due", "balance due", "bill to", "invoice number",
        "payment terms", "receipt", "purchase order", "research paper", "abstract",
        "introduction", "methodology", "references cited", "bibliography", "table of contents",
        "chapter 1", "terms and conditions", "privacy policy", "user manual", "syllabus",
        "assignment 1", "homework", "course code", "lecture notes"
    ]
    gen_matches = [kw for kw in gen_doc_keywords if kw in low_text]

    # 2. Cover Letter Signals
    cover_letter_keywords = [
        "dear hiring manager", "dear recruiter", "dear sir", "dear madam", "dear selection committee",
        "i am writing to apply", "i am writing to express my interest", "please accept this letter",
        "enclosed is my resume", "thank you for your consideration", "sincerely,", "respectfully,",
        "best regards,", "cover letter", "application for the position of", "re: application"
    ]
    cl_matches = [kw for kw in cover_letter_keywords if kw in low_text]

    # 3. Job Description Signals
    jd_keywords = [
        "job description", "about the role", "key responsibilities", "responsibilities:",
        "what you'll do", "what you will do", "requirements:", "minimum qualifications",
        "preferred qualifications", "who you are", "we are looking for", "about our company",
        "equal opportunity employer", "salary range:", "benefits & perks", "how to apply:"
    ]
    jd_matches = [kw for kw in jd_keywords if kw in low_text]

    # 4. CV / Resume Signals
    cv_heading_keywords = [
        "work experience", "professional experience", "employment history", "career history",
        "technical skills", "core competencies", "education", "academic background",
        "personal projects", "key projects", "certifications", "professional summary",
        "curriculum vitae", "resume"
    ]
    cv_heading_matches = [kw for kw in cv_heading_keywords if kw in low_text]

    email_present = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
    phone_present = bool(re.search(r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text))
    date_range_present = bool(re.search(r'\b(19|20)\d{2}\s*[\-–—\to]\s*((19|20)\d{2}|present|current)\b', low_text))

    cv_score = len(cv_heading_matches) * 2.0 + (2.0 if email_present else 0) + (1.5 if phone_present else 0) + (2.0 if date_range_present else 0)
    cl_score = len(cl_matches) * 2.5
    jd_score = len(jd_matches) * 2.5
    gen_score = len(gen_matches) * 3.0

    # Decision Matrix
    if gen_score >= 3.0 and gen_score > cv_score:
        return {"document_type": "GENERAL_DOCUMENT", "confidence": min(1.0, gen_score / 5.0), "signals": gen_matches}

    if cl_score >= 2.5 and cl_score > cv_score and len(cv_heading_matches) < 2:
        return {"document_type": "COVER_LETTER", "confidence": min(1.0, cl_score / 5.0), "signals": cl_matches}

    if jd_score >= 2.5 and jd_score > cv_score and not (email_present and date_range_present):
        return {"document_type": "JOB_DESCRIPTION", "confidence": min(1.0, jd_score / 5.0), "signals": jd_matches}

    if cv_score >= 2.0 or (cv_heading_matches and (email_present or date_range_present)):
        return {"document_type": "CV", "confidence": min(1.0, cv_score / 6.0), "signals": cv_heading_matches}

    if gen_matches:
        return {"document_type": "GENERAL_DOCUMENT", "confidence": 0.6, "signals": gen_matches}

    return {"document_type": "UNKNOWN", "confidence": 0.3, "signals": []}


def validate_pdf_resume(file_bytes: bytes, filename: str = "") -> DocumentValidationResult:
    """Validate a file upload for CV resume parsing.
    Checks size, signature, parsability, text length, and document classification."""
    file_size_mb = round(len(file_bytes) / (1024 * 1024), 2)

    # 1. Size Guard (100 MB max)
    if file_size_mb > 100.0:
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="EXCEEDS_MAX_SIZE",
            user_message="File is too large. Maximum allowed size is 100 MB.",
            file_size_mb=file_size_mb,
            is_pdf=False,
            is_parsable=False,
            text_length=0,
            confidence=0.0
        )

    # 2. Empty File Check
    if len(file_bytes) == 0:
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="EMPTY_FILE",
            user_message="The uploaded file is empty. Please choose a valid PDF resume.",
            file_size_mb=0.0,
            is_pdf=False,
            is_parsable=False,
            text_length=0,
            confidence=0.0
        )

    # 3. Filename Extension Check (if provided)
    if filename:
        clean_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if clean_ext and clean_ext != 'pdf':
            return DocumentValidationResult(
                accepted=False,
                document_type="UNKNOWN",
                reason="INVALID_FILE_FORMAT",
                user_message="PDF files only. Please upload your CV as a PDF.",
                file_size_mb=file_size_mb,
                is_pdf=False,
                is_parsable=False,
                text_length=0,
                confidence=0.0
            )

    # 4. File Magic Signature Check
    is_pdf_signature = b"%PDF-" in file_bytes[:1024]
    if not is_pdf_signature:
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="INVALID_PDF_SIGNATURE",
            user_message="This file is not a valid PDF. Please upload a valid PDF resume.",
            file_size_mb=file_size_mb,
            is_pdf=False,
            is_parsable=False,
            text_length=0,
            confidence=0.0
        )

    # 5. PDF Parsability Check
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    pages_text.append(txt)
            raw_text = "\n".join(pages_text) if pages_text else ""
    except Exception as e:
        logger.warning(f"Corrupted PDF detection: {e}")
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="CORRUPTED_PDF",
            user_message="This PDF could not be read. Please upload a valid, non-corrupted resume PDF.",
            file_size_mb=file_size_mb,
            is_pdf=True,
            is_parsable=False,
            text_length=0,
            confidence=0.0
        )

    # 6. Image-only / Text Length Check
    if not raw_text or len(raw_text.strip()) < 30 or len(raw_text.split()) < 8:
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="IMAGE_ONLY_OR_NO_TEXT",
            user_message="This PDF contains little or no extractable text. Please upload a text-based CV PDF or use manual profile entry.",
            file_size_mb=file_size_mb,
            is_pdf=True,
            is_parsable=True,
            text_length=len(raw_text) if raw_text else 0,
            confidence=0.0
        )

    # 7. Document Classification
    cls_res = classify_document_type(raw_text)
    doc_type = cls_res["document_type"]
    conf = cls_res["confidence"]

    if doc_type == "COVER_LETTER":
        return DocumentValidationResult(
            accepted=False,
            document_type="COVER_LETTER",
            reason="REJECTED_COVER_LETTER",
            user_message="This looks like a cover letter, not a CV. Please upload your resume/CV.",
            file_size_mb=file_size_mb,
            is_pdf=True,
            is_parsable=True,
            text_length=len(raw_text),
            confidence=conf
        )

    if doc_type == "JOB_DESCRIPTION":
        return DocumentValidationResult(
            accepted=False,
            document_type="JOB_DESCRIPTION",
            reason="REJECTED_JOB_DESCRIPTION",
            user_message="This looks like a job description, not a CV. Please upload your resume/CV.",
            file_size_mb=file_size_mb,
            is_pdf=True,
            is_parsable=True,
            text_length=len(raw_text),
            confidence=conf
        )

    if doc_type in ["GENERAL_DOCUMENT", "UNKNOWN"]:
        return DocumentValidationResult(
            accepted=False,
            document_type=doc_type,
            reason="REJECTED_UNRELATED_DOC",
            user_message="This PDF does not appear to be a CV/resume. Please upload your resume/CV.",
            file_size_mb=file_size_mb,
            is_pdf=True,
            is_parsable=True,
            text_length=len(raw_text),
            confidence=conf
        )

    # ACCEPTED CV!
    return DocumentValidationResult(
        accepted=True,
        document_type="CV",
        reason="OK",
        user_message="CV processed successfully",
        file_size_mb=file_size_mb,
        is_pdf=True,
        is_parsable=True,
        text_length=len(raw_text),
        confidence=conf
    )


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


def assess_extraction_quality(cand: CandidateProfile) -> Dict[str, Any]:
    """Calculate profile completeness score and extraction quality warning flags."""
    if not cand or not cand.raw_text:
        return {
            "completeness_score": 0,
            "is_low_quality": True,
            "flags": ["No resume loaded"],
            "detected_skills_count": 0,
            "experience_entries_count": 0,
        }

    score = 0
    flags = []
    
    if cand.name and cand.name != "Candidate Profile":
        score += 15
    else:
        flags.append("Name unconfirmed")

    if cand.email:
        score += 15
    else:
        flags.append("Missing email")

    if cand.skills and len(cand.skills) >= 3:
        score += 30
    elif cand.skills:
        score += 15
        flags.append("Few skills detected")
    else:
        flags.append("No explicit skills detected")

    if cand.experience and len(cand.experience) >= 1:
        score += 25
    else:
        flags.append("Experience section sparse")

    if cand.summary and len(cand.summary) > 20:
        score += 15
    else:
        flags.append("Summary sparse")

    is_low_quality = (score < 45) or (len(cand.skills) < 2) or (len(cand.experience) < 1)
    
    return {
        "completeness_score": min(100, score),
        "is_low_quality": is_low_quality,
        "flags": flags,
        "detected_skills_count": len(cand.skills),
        "experience_entries_count": len(cand.experience),
    }


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
