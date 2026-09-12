"""AI Career Coach chatbot engine with full dashboard context awareness."""
from typing import Optional, List
from backend.models import CandidateProfile, JobPosting, ATSAnalysis, GapAnalysis, ApplicationRecord, CoachMessage
from backend.config import get_api_key, logger

try:
    from groq import Groq
except ImportError:
    Groq = None


def ask_career_coach(
    user_query: str,
    history: List[CoachMessage],
    candidate: Optional[CandidateProfile] = None,
    job: Optional[JobPosting] = None,
    ats: Optional[ATSAnalysis] = None,
    gap: Optional[GapAnalysis] = None,
    applications: Optional[List[ApplicationRecord]] = None,
) -> str:
    """Query the CareerBridge AI Coach with full context."""
    api_key = get_api_key()

    if api_key and Groq:
        try:
            client = Groq(api_key=api_key)

            # Build context summary
            ctx_parts = []
            if candidate:
                ctx_parts.append(f"CANDIDATE: {candidate.name}, Skills: {', '.join(candidate.skills[:10])}, Exp: {len(candidate.experience)} roles")
            if job:
                ctx_parts.append(f"TARGET JOB: {job.title} at {job.company} ({job.location})")
            if ats:
                ctx_parts.append(f"ATS SCORE: {ats.overall_score}/100 (Skills: {ats.skills_match}%, Keywords: {ats.keyword_match}%)")
            if gap:
                missing_names = [s.name for s in gap.missing_skills]
                verified_names = [s.name for s in gap.verified_skills]
                ctx_parts.append(f"VERIFIED SKILLS: {', '.join(verified_names[:6])}")
                ctx_parts.append(f"MISSING SKILLS: {', '.join(missing_names[:6])}")
            if applications:
                ctx_parts.append(f"TOTAL APPLICATIONS: {len(applications)} tracked")

            context_str = "\n".join(ctx_parts)

            system_prompt = f"""You are CareerBridge AI Coach, an expert AI HR consultant and career strategist.
You provide clear, practical, actionable advice to job candidates.

CURRENT CANDIDATE DASHBOARD CONTEXT:
{context_str}

GUARDRAILS:
1. Ground your advice strictly in the candidate's verified skills and experience. Do not fabricate qualifications.
2. Be concise, encouraging, and highly tactical.
3. Use markdown bullet points for readability.
"""

            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-6:]:  # include last 6 turns
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": user_query})

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.4,
                max_tokens=800,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Career Coach LLM failed: {e}")

    # Contextual Deterministic Fallback Coach
    return _generate_fallback_coach_response(user_query, candidate, job, ats, gap, applications)


def _generate_fallback_coach_response(
    query: str,
    candidate: Optional[CandidateProfile],
    job: Optional[JobPosting],
    ats: Optional[ATSAnalysis],
    gap: Optional[GapAnalysis],
    applications: Optional[List[ApplicationRecord]],
) -> str:
    """Deterministic, context-aware fallback response generator."""
    q_lower = query.lower()

    if "job" in q_lower or "fit" in q_lower or "role" in q_lower or "recommend" in q_lower:
        if candidate and candidate.skills:
            sk_str = ", ".join(candidate.skills[:5])
            return f"**Job Fit Analysis for {candidate.name or 'Candidate'}:**\n\n" \
                   f"Based on your profile, your top verified skills are **{sk_str}**.\n\n" \
                   f"💡 **Coach Recommendation:**\n" \
                   f"- Roles like **Software Engineer**, **ML Engineer**, and **Backend Developer** align best with your technical background.\n" \
                   f"- Search the **Find Jobs** tab for live opportunities and target roles with match scores above 70%."
        return "Select **Find Jobs** in the sidebar to search live openings tailored to your target role and skill set."

    elif "ats" in q_lower or "score" in q_lower or "low" in q_lower:
        if ats:
            return f"**ATS Breakdown Analysis ({ats.overall_score}/100):**\n" \
                   f"- **Skills Match:** {ats.skills_match}%\n" \
                   f"- **Keyword Match:** {ats.keyword_match}%\n" \
                   f"- **Experience Match:** {ats.experience_match}%\n" \
                   f"- **Format Score:** {ats.format_score}%\n\n" \
                   f"**Key Recommendations to Boost Score:**\n" + \
                   "\n".join(f"- {r}" for r in ats.recommendations[:3])
        return "Your ATS score is computed from skill overlap, keyword match, and experience relevance against target job postings. Select a target job in the ATS Scanner page to view your breakdown."

    elif "missing" in q_lower or "gap" in q_lower or "skill" in q_lower:
        if gap and gap.missing_skills:
            missing_str = ", ".join(s.name for s in gap.missing_skills)
            return f"Based on your gap analysis against **{job.title if job else 'target jobs'}**, you are currently missing:\n\n" \
                   f"❌ **Missing Skills:** {missing_str}\n\n" \
                   f"💡 **Coach Advice:** Add evidence or projects demonstrating these skills in your CV, or focus on roles emphasizing your verified skills ({', '.join(s.name for s in gap.verified_skills[:5])})."
        return "To analyze your missing skills, select a target job from the **Find Jobs** tab and run the **ATS Scanner**."

    elif "apply" in q_lower or "should i" in q_lower:
        if job and ats:
            if ats.overall_score >= 70:
                return f"**Yes, strong match!** Your ATS score for **{job.title}** at **{job.company}** is **{ats.overall_score}/100** ({ats.skills_match}% skills match). You have verified core skills in {', '.join(job.required_skills[:3])}. Apply today!"
            elif ats.overall_score >= 50:
                return f"**Moderate match ({ats.overall_score}/100).** You match key requirements for **{job.title}**, but review the missing skills tab first. Run **Improve CV** to optimize your resume bullets before applying."
            else:
                return f"**Careful ({ats.overall_score}/100).** There are significant skill gaps for **{job.title}**. Consider applying to entry-level or adjacent roles first."
        return "Select a job posting in **Find Jobs** to evaluate whether you should apply based on your match score."

    elif "improve" in q_lower or "bullet" in q_lower or "resume" in q_lower or "cv" in q_lower:
        return "**Resume Bullet Optimization Strategy:**\n" \
               "1. Use the **Action Verb + Task + Impact (Metric)** structure.\n" \
               "2. Ensure metrics come strictly from real project data (X-Y-Z guardrail).\n" \
               "3. Navigate to **Improve CV** in the sidebar to view side-by-side Before/After bullet enhancements."

    elif any(kw in q_lower for kw in ["hi", "hello", "hey", "greetings"]):
        name = candidate.name if candidate and candidate.name else "Candidate"
        return f"Hello {name}! I am your **CareerBridge AI Coach**. Ask me about your ATS score, missing skills, resume bullets, or job recommendations!"

    else:
        name = candidate.name if candidate and candidate.name else "Candidate"
        skills_str = ", ".join(candidate.skills[:5]) if candidate and candidate.skills else "Software Engineering"
        return f"I am actively tracking your profile context (**{skills_str}**). How can I assist your career strategy today?"

