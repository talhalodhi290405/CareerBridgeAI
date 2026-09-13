import json
import re
import io
from typing import Optional, List, Dict, Any

import pdfplumber

from backend.models import CandidateProfile, DocumentValidationResult
from backend.config import get_api_key, logger

try:
    from groq import Groq
except ImportError:
    Groq = None


COMMON_TECH_SKILLS = [
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C", "Go", "Rust", "SQL",
    "R", "PHP", "Swift", "Kotlin", "Ruby", "Bash", "Shell", "HTML", "CSS",
    # AI / ML / Data Science
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "Scikit-Learn", "Transformers", "Neural Networks", "Keras",
    "HuggingFace", "OpenCV", "Data Science", "Data Analysis", "Data Mining",
    # Agentic AI & LLMs
    "LangChain", "LangGraph", "RAG", "Vector Database", "ChromaDB", "FAISS", "Agents",
    "LLM", "Large Language Models", "Prompt Engineering", "Ollama", "OpenAI", "Llama",
    # Backend / Web
    "FastAPI", "Django", "Flask", "Node.js", "Express", "REST API", "GraphQL", "Microservices",
    "Spring Boot", "ASP.NET", "gRPC", "WebSockets",
    # Frontend
    "React", "Next.js", "Angular", "Vue", "Tailwind", "Bootstrap", "Redux", "Svelte",
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Elasticsearch", "DynamoDB", "Cassandra", "Firebase",
    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "CI/CD",
    "Linux", "Terraform", "Ansible", "Jenkins", "Nginx",
    # Data Engineering & BI
    "Pandas", "NumPy", "Matplotlib", "Seaborn", "Power BI", "Tableau", "Spark", "Hadoop",
    "Airflow", "Snowflake", "Databricks",
    # Robotics & Hardware / Embedded
    "ROS", "ROS2", "Arduino", "Raspberry Pi", "Embedded Systems", "Microcontrollers", "RTOS", "Verilog",
    # Soft & Management Skills
    "Project Management", "Agile", "Scrum", "Jira", "Figma", "SDLC", "System Design",
    "Team Leadership", "Problem Solving", "Communication"
]

CANONICAL_SKILL_MAP = {s.lower(): s for s in COMMON_TECH_SKILLS}
# Aliases
CANONICAL_SKILL_MAP.update({
    "py": "Python",
    "js": "JavaScript",
    "ts": "TypeScript",
    "cpp": "C++",
    "cnet": "C#",
    "reactjs": "React",
    "nextjs": "Next.js",
    "nodejs": "Node.js",
    "vuejs": "Vue",
    "scikit": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "k8s": "Kubernetes",
    "aws cloud": "AWS",
    "amazon web services": "AWS",
    "google cloud": "GCP",
    "azure cloud": "Azure",
    "ros 2": "ROS2",
    "powerbi": "Power BI",
    "open cv": "OpenCV"
})



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
    Checks signature, parsability, text length, and CV keywords."""
    file_size_mb = round(len(file_bytes) / (1024 * 1024), 2) if file_bytes else 0.0

    # 1. File Type Check: Inspect incoming file_bytes signature
    if not file_bytes or not file_bytes.startswith(b'%PDF'):
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="Invalid File Type",
            user_message="Invalid file format. Only PDF files are accepted.",
            file_size_mb=file_size_mb,
            is_pdf=False,
            is_parsable=False,
            text_length=0,
            confidence=0.0
        )

    # 2. PDF Parsability Check
    raw_text = extract_text_from_pdf(file_bytes) or ""
    if not raw_text:
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

    # 3. Content Check: Convert text to lowercase & verify >= 2 standard CV keywords
    text_lower = raw_text.lower()
    cv_keywords = ['experience', 'education', 'skills', 'summary', 'work', 'university', 'resume', 'projects', 'employment', 'profile', 'contact', 'curriculum vitae']
    matched_keywords = [kw for kw in cv_keywords if kw in text_lower]

    if len(matched_keywords) < 2:
        return DocumentValidationResult(
            accepted=False,
            document_type="UNKNOWN",
            reason="Not a CV",
            user_message="This document does not appear to be a professional CV. Please upload a valid resume.",
            file_size_mb=file_size_mb,
            is_pdf=True,
            is_parsable=True,
            text_length=len(raw_text),
            confidence=0.0
        )

    # 4. Document Classification check
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

    # ACCEPTED CV
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
    headers_regex = '|'.join(re.escape(h) for h in headers)
    section_pattern = r'^\s*(?:' + headers_regex + r')\s*[:\-]?\s*(.*)$'
    
    all_headers = [
        'education', 'experience', 'work experience', 'professional experience', 'employment history',
        'skills', 'technical skills', 'core skills', 'key skills', 'skills & competencies', 'technologies',
        'tools & technologies', 'tech stack', 'programming languages', 'frameworks', 'tools', 'projects',
        'personal projects', 'key projects', 'certifications', 'certificates', 'achievements', 'awards',
        'summary', 'professional summary', 'objective', 'profile', 'contact', 'references', 'publications',
        'languages', 'interests', 'volunteer', 'activities', 'competencies', 'domain expertise'
    ]
    all_headers_regex = '|'.join(re.escape(h) for h in all_headers)
    next_section_pattern = r'^\s*(?:' + all_headers_regex + r')\s*[:\-]?\s*$'
    
    lines = text.split('\n')
    capturing = False
    captured = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        m_start = re.match(section_pattern, stripped, re.IGNORECASE)
        if m_start:
            capturing = True
            inline_remainder = m_start.group(1).strip()
            if inline_remainder:
                captured.append(inline_remainder)
            continue
        
        if capturing and re.match(next_section_pattern, stripped, re.IGNORECASE):
            break
        
        if capturing:
            captured.append(stripped)
    
    return captured


def _extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from dedicated skill sections AND scan entire text for canonical controlled vocabulary."""
    skill_headers = [
        'skills', 'technical skills', 'core skills', 'key skills', 'skills & competencies',
        'technical expertise', 'technologies', 'tools & technologies', 'tech stack',
        'programming languages', 'frameworks', 'tools', 'skills & expertise', 'competencies',
        'domain expertise', 'expertise', 'technical proficiencies', 'key competencies'
    ]
    section_items = _extract_section(text, skill_headers)
    
    found_skills = set()

    # 1. Parse tokens from extracted skills section
    for item in section_items:
        cleaned_item = re.sub(r'^\s*(?:[a-zA-Z\s&/]+\s*[:\-])', '', item).strip()
        parts = re.split(r'[,;|•·/\n]', cleaned_item)
        for part in parts:
            cleaned = part.strip().strip('-').strip('•').strip('·').strip('*').strip()
            if not cleaned or len(cleaned) > 40:
                continue
            
            low_cleaned = cleaned.lower()
            if low_cleaned in CANONICAL_SKILL_MAP:
                found_skills.add(CANONICAL_SKILL_MAP[low_cleaned])
            elif len(cleaned) > 1 and not low_cleaned.startswith(('skill', 'technical', 'core', 'competenc', 'proficienc', 'programm', 'language', 'tool', 'framework', 'cloud', 'database')):
                found_skills.add(cleaned.title())

    # 2. Comprehensive vocabulary scan across full resume raw text
    for tech in COMMON_TECH_SKILLS:
        if tech.lower() in ["c++", "c#"]:
            pattern = re.escape(tech)
        else:
            pattern = r'\b' + re.escape(tech) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.add(CANONICAL_SKILL_MAP.get(tech.lower(), tech))

    return sorted(list(found_skills))



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
        raw_tech_found = [t for t in COMMON_TECH_SKILLS if re.search(r'\b' + re.escape(t) + r'\b', cand.raw_text, re.IGNORECASE)]
        if raw_tech_found:
            flags.append(f"Skill extraction incomplete ({len(raw_tech_found)} potential tech terms detected in text)")
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



def _extract_skills_with_llm(raw_text: str) -> List[str]:
    """Fallback skill extraction mechanism using Groq LLM service when deterministic extraction yields 0 skills."""
    if not raw_text or not raw_text.strip():
        return []

    api_key = get_api_key()
    if api_key and Groq:
        try:
            client = Groq(api_key=api_key)
            prompt = (
                "Extract all technical skills from this resume text and return them strictly as a JSON list of strings.\n\n"
                "RESUME TEXT:\n"
                f"{raw_text[:3500]}\n\n"
                "Return strictly a valid JSON array of strings, e.g. [\"Python\", \"Docker\", \"AWS\"]. Do not include markdown formatting or commentary."
            )
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert HR resume parser. Extract all technical skills and return strictly as a JSON list of strings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=400,
            )
            content = response.choices[0].message.content.strip()
            if "```" in content:
                content = re.sub(r'```(?:json)?\s*', '', content).split('```')[0].strip()
            
            parsed = json.loads(content)
            if isinstance(parsed, list):
                clean_skills = [str(s).strip() for s in parsed if str(s).strip() and len(str(s).strip()) < 40]
                if clean_skills:
                    logger.info(f"Groq LLM skill extraction fallback succeeded: {len(clean_skills)} skills extracted.")
                    return sorted(list(set(clean_skills)))
        except Exception as e:
            logger.error(f"Groq LLM skill extraction fallback failed: {e}")

    # Fallback heuristic if LLM is unavailable: return any vocabulary terms present
    fallback_skills = set()
    for tech in COMMON_TECH_SKILLS:
        if re.search(r'\b' + re.escape(tech) + r'\b', raw_text, re.IGNORECASE):
            fallback_skills.add(tech)

    return sorted(list(fallback_skills))


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
    if not skills:
        logger.info("Deterministic skill extraction returned 0 skills — triggering Groq LLM fallback...")
        skills = _extract_skills_with_llm(raw_text)

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

