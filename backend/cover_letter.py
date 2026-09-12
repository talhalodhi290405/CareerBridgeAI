"""Cover Letter Generator with tone toggles and deterministic fallback grounding."""
from typing import Optional
from backend.models import CandidateProfile, JobPosting, CoverLetter
from backend.config import get_api_key, logger

try:
    from groq import Groq
except ImportError:
    Groq = None


def generate_cover_letter(
    candidate: CandidateProfile,
    job: JobPosting,
    tone: str = "Standard",
) -> CoverLetter:
    """Generate a tailored cover letter grounded strictly in candidate evidence."""
    api_key = get_api_key()

    if api_key and Groq:
        try:
            client = Groq(api_key=api_key)
            prompt = f"""
You are a professional executive resume writer. Write a tailored, persuasive cover letter for the candidate applying to the job below.

CANDIDATE NAME: {candidate.name or 'Candidate'}
CANDIDATE SUMMARY: {candidate.summary or 'N/A'}
CANDIDATE SKILLS: {', '.join(candidate.skills[:10])}
CANDIDATE EXPERIENCE: {'; '.join(candidate.experience[:3])}

TARGET JOB TITLE: {job.title}
TARGET COMPANY: {job.company}
JOB DESCRIPTION: {job.description[:1000]}
REQUIRED SKILLS: {', '.join(job.required_skills)}

TONE REQUIREMENT: {tone}
- If "Concise": Keep under 200 words, highly punchy.
- If "Technical": Highlight frameworks, metrics, tech stack, and engineering impact.
- If "Formal": Use traditional executive business language.
- If "Standard": Balanced, compelling 3-paragraph structure.

CRITICAL GUARDRAILS:
1. Do NOT invent companies, metrics, degrees, or skills not mentioned in candidate evidence.
2. Return ONLY the text of the cover letter (including Subject line if applicable).
"""
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            content = response.choices[0].message.content.strip()
            return CoverLetter(
                content=content,
                tone=tone,
                job_title=job.title,
                company=job.company,
            )
        except Exception as e:
            logger.error(f"Cover letter LLM generation failed: {e}")

    # Deterministic Fallback Generator
    return _generate_fallback_cover_letter(candidate, job, tone)


def _generate_fallback_cover_letter(
    candidate: CandidateProfile,
    job: JobPosting,
    tone: str = "Standard",
) -> CoverLetter:
    """Deterministic, anti-hallucination fallback cover letter generator."""
    name = candidate.name or "Candidate"
    email = candidate.email or ""
    phone = candidate.phone or ""
    skills = ", ".join(candidate.skills[:6]) if candidate.skills else "software engineering"
    exp_summary = candidate.experience[0] if candidate.experience else "relevant technical projects"

    if tone == "Concise":
        body = f"""Dear Hiring Team at {job.company},

I am writing to express my strong interest in the {job.title} position. With hands-on experience in {skills}, I have demonstrated technical execution in {exp_summary}.

My background directly aligns with your requirements for {', '.join(job.required_skills[:3]) if job.required_skills else 'this role'}. I welcome the opportunity to discuss how I can contribute immediately to {job.company}.

Sincerely,
{name}
{email} | {phone}"""

    elif tone == "Technical":
        body = f"""Subject: Application for {job.title} — {name}

Dear {job.company} Engineering Team,

I am applying for the {job.title} role at {job.company}. My technical stack includes {skills}, with proven implementation experience in {exp_summary}.

Key technical highlights matching your stack:
- Core proficiency: {skills}
- System experience: {exp_summary}
- Target alignment: {', '.join(job.required_skills[:4]) if job.required_skills else 'Core engineering standards'}

I look forward to discussing technical architecture and system contribution in an interview.

Best regards,
{name}
{email} | {phone}"""

    elif tone == "Formal":
        body = f"""Dear Hiring Manager,

Please accept this letter and accompanying resume as formal application for the position of {job.title} at {job.company}. 

Throughout my experience, I have developed key competencies in {skills}. Most recently, I have focused on {exp_summary}, demonstrating a commitment to technical excellence and operational impact.

I am confident that my qualification profile aligns closely with the core deliverables for the {job.title} role. Thank you for your time and consideration.

Sincerely,
{name}
{email} | {phone}"""

    else:  # Standard
        body = f"""Dear Hiring Manager at {job.company},

I am excited to submit my application for the {job.title} role at {job.company}. Having followed {job.company}'s work, I am eager to bring my expertise in {skills} to your team.

In my recent experience, I have successfully executed projects involving {exp_summary}. My background aligns directly with your need for candidates skilled in {', '.join(job.required_skills[:3]) if job.required_skills else 'key technical disciplines'}.

I would welcome the opportunity to connect and discuss how my skills and experience can support {job.company}'s goals.

Best regards,
{name}
{email} | {phone}"""

    return CoverLetter(
        content=body,
        tone=tone,
        job_title=job.title,
        company=job.company,
    )
