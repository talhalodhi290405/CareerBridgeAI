"""Prompt templates for CareerBridge AI LLM calls."""

ATS_ANALYSIS_PROMPT = """You are an expert ATS analyst. Analyze this candidate's resume against the target job.

Provide a semantic assessment to supplement the deterministic scores already computed.

Return ONLY a JSON object with this exact structure:
{{
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "summary": "One sentence summary of overall fit"
}}

CANDIDATE RESUME:
{resume_text}

TARGET JOB:
{job_title} at {company}
{job_description}

Required Skills: {required_skills}
"""

OPTIMIZATION_PROMPT = """You are an expert resume optimizer. Improve the candidate's profile for the target job.

RULES — YOU MUST FOLLOW THESE:
- ONLY use information that exists in the resume. NEVER fabricate skills, companies, metrics, certifications, or achievements.
- Improve wording, clarity, and keyword alignment.
- Use action verbs and clear, concise language.
- If using X-Y-Z format ("Accomplished X as measured by Y by doing Z"), ONLY include Y (the metric) if an actual number exists in the resume.
- Do NOT invent percentages, user counts, revenue figures, or time savings.

Return ONLY a JSON object:
{{
    "optimized_summary": "An improved professional summary (2-3 sentences)",
    "optimized_bullets": [
        "Improved bullet point 1 based on existing experience",
        "Improved bullet point 2 based on existing experience",
        "Improved bullet point 3 based on existing experience",
        "Improved bullet point 4 based on existing experience",
        "Improved bullet point 5 based on existing experience"
    ],
    "improvements_made": [
        "Description of improvement 1",
        "Description of improvement 2",
        "Description of improvement 3"
    ]
}}

CANDIDATE RESUME:
{resume_text}

CANDIDATE SKILLS: {skills}

TARGET JOB: {job_title} at {company}
Required Skills: {required_skills}
"""

RECRUITER_EMAIL_PROMPT = """Write a professional recruiter outreach email for this candidate applying to this role.

RULES:
- Only reference skills and experience that exist in the resume.
- Do NOT fabricate any claims.
- Keep it concise (150-200 words).
- Professional but personable tone.

Return ONLY a JSON object:
{{
    "subject": "Email subject line",
    "body": "The full email body"
}}

CANDIDATE: {candidate_name}
SKILLS: {skills}
EXPERIENCE HIGHLIGHTS: {experience}

TARGET ROLE: {job_title} at {company}
Required Skills: {required_skills}
"""

RECRUITER_INMAIL_PROMPT = """Write a short LinkedIn InMail message for this candidate reaching out about this role.

RULES:
- Only reference verified skills and experience.
- Do NOT fabricate any claims.
- Keep it brief (80-120 words).
- Conversational but professional tone.

Return ONLY a JSON object:
{{
    "message": "The InMail message text"
}}

CANDIDATE: {candidate_name}
SKILLS: {skills}
KEY EXPERIENCE: {experience}

TARGET ROLE: {job_title} at {company}
"""

INTERVIEW_QUESTIONS_PROMPT = """Generate exactly 3 technical interview questions for this candidate interviewing for this role.

RULES:
- Questions must be specific to the role's technical requirements.
- Questions should be relevant to the candidate's experience level.
- Do NOT ask generic behavioral questions.
- Each question should test a different technical area.

Return ONLY a JSON object:
{{
    "questions": [
        "Technical question 1",
        "Technical question 2",
        "Technical question 3"
    ]
}}

CANDIDATE SKILLS: {skills}
CANDIDATE EXPERIENCE: {experience}

TARGET ROLE: {job_title}
Required Skills: {required_skills}
Job Description: {job_description}
"""
