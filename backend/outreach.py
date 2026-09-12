"""Recruiter outreach and interview question generation."""
from typing import Optional
from pydantic import BaseModel, Field

from backend.models import CandidateProfile, JobPosting, OutreachPackage
from backend.llm_service import call_llm_structured
from backend.prompts import RECRUITER_EMAIL_PROMPT, RECRUITER_INMAIL_PROMPT, INTERVIEW_QUESTIONS_PROMPT
from backend.config import logger


class _EmailResponse(BaseModel):
    subject: str = ""
    body: str = ""


class _InMailResponse(BaseModel):
    message: str = ""


class _QuestionsResponse(BaseModel):
    questions: list[str] = Field(default_factory=list)


def _generate_deterministic_email(candidate: CandidateProfile, job: JobPosting) -> str:
    """Generate a recruiter email without LLM."""
    name = candidate.name or "the candidate"
    skills_highlight = ', '.join(candidate.skills[:3]) if candidate.skills else "relevant technical skills"
    exp_highlight = candidate.experience[0][:100] if candidate.experience else "demonstrated technical aptitude"
    
    return f"""Subject: Strong Candidate for {job.title} Position

Dear Hiring Manager,

I am writing to express interest in the {job.title} position at {job.company}.

With a background in {skills_highlight}, I believe I bring relevant experience to this role. {exp_highlight.strip().rstrip('.')}, which aligns well with your team's needs.

I am particularly drawn to this opportunity because of {job.company}'s work in {job.required_skills[0] if job.required_skills else 'this domain'}. My hands-on experience with {skills_highlight} has prepared me to contribute meaningfully from day one.

I would welcome the opportunity to discuss how my background aligns with your team's goals. I am available for a conversation at your convenience.

Best regards,
{name}"""


def _generate_deterministic_inmail(candidate: CandidateProfile, job: JobPosting) -> str:
    """Generate a LinkedIn InMail without LLM."""
    name = candidate.name or "Hi"
    skills_highlight = ', '.join(candidate.skills[:3]) if candidate.skills else "relevant skills"
    
    return f"""Hi,

I came across the {job.title} opening at {job.company} and wanted to reach out. With experience in {skills_highlight}, I believe my background aligns well with what you're looking for.

I'd love to connect and learn more about the role and team. Would you be open to a brief conversation?

Best,
{name}"""


def _generate_deterministic_questions(candidate: CandidateProfile, job: JobPosting) -> list[str]:
    """Generate 3 technical interview questions without LLM."""
    questions = []
    req_skills = job.required_skills[:3] if job.required_skills else ["the core technology"]
    
    # Question 1: Based on primary required skill
    skill1 = req_skills[0] if req_skills else "your primary technical stack"
    questions.append(
        f"Can you walk me through a project where you used {skill1}? "
        f"What technical challenges did you face and how did you solve them?"
    )
    
    # Question 2: Based on second skill or system design
    if len(req_skills) > 1:
        skill2 = req_skills[1]
        questions.append(
            f"How would you approach building a system that integrates {skill2} "
            f"into an existing {job.title.lower()} workflow? What trade-offs would you consider?"
        )
    else:
        questions.append(
            f"Describe how you would design the architecture for a key component "
            f"in a {job.title.lower()} role. What patterns and tools would you choose?"
        )
    
    # Question 3: Problem-solving with third skill
    if len(req_skills) > 2:
        skill3 = req_skills[2]
        questions.append(
            f"You encounter a performance bottleneck in a system using {skill3}. "
            f"Walk me through your debugging and optimization process."
        )
    else:
        questions.append(
            f"Tell me about a time you had to debug a complex technical issue. "
            f"What tools and methodology did you use to identify and resolve it?"
        )
    
    return questions[:3]


def generate_outreach(
    candidate: CandidateProfile,
    job: JobPosting,
) -> OutreachPackage:
    """Generate recruiter email, InMail, and interview questions.
    Uses LLM when available, falls back to deterministic generation."""
    
    name = candidate.name or "Candidate"
    skills_str = ', '.join(candidate.skills[:10]) if candidate.skills else "N/A"
    exp_str = ' | '.join(candidate.experience[:3]) if candidate.experience else "N/A"
    req_skills_str = ', '.join(job.required_skills) if job.required_skills else "N/A"
    
    # --- Recruiter Email ---
    email_text = None
    try:
        prompt = RECRUITER_EMAIL_PROMPT.format(
            candidate_name=name,
            skills=skills_str,
            experience=exp_str,
            job_title=job.title,
            company=job.company,
            required_skills=req_skills_str,
        )
        result = call_llm_structured(prompt, _EmailResponse)
        if result and result.body:
            email_text = f"Subject: {result.subject}\n\n{result.body}"
    except Exception as e:
        logger.warning(f"LLM email generation failed: {e}")
    
    if not email_text:
        email_text = _generate_deterministic_email(candidate, job)
    
    # --- Recruiter InMail ---
    inmail_text = None
    try:
        prompt = RECRUITER_INMAIL_PROMPT.format(
            candidate_name=name,
            skills=skills_str,
            experience=exp_str,
            job_title=job.title,
            company=job.company,
        )
        result = call_llm_structured(prompt, _InMailResponse)
        if result and result.message:
            inmail_text = result.message
    except Exception as e:
        logger.warning(f"LLM InMail generation failed: {e}")
    
    if not inmail_text:
        inmail_text = _generate_deterministic_inmail(candidate, job)
    
    # --- Interview Questions ---
    questions = None
    try:
        prompt = INTERVIEW_QUESTIONS_PROMPT.format(
            skills=skills_str,
            experience=exp_str,
            job_title=job.title,
            required_skills=req_skills_str,
            job_description=job.description[:500],
        )
        result = call_llm_structured(prompt, _QuestionsResponse)
        if result and len(result.questions) >= 3:
            questions = result.questions[:3]
    except Exception as e:
        logger.warning(f"LLM question generation failed: {e}")
    
    if not questions:
        questions = _generate_deterministic_questions(candidate, job)
    
    return OutreachPackage(
        recruiter_email=email_text,
        recruiter_inmail=inmail_text,
        interview_questions=questions[:3],
    )
