"""ATS Analysis Engine — hybrid deterministic + optional LLM scoring."""
from backend.models import CandidateProfile, JobPosting, ATSAnalysis, GapAnalysis, ClassifiedSkill, SkillClassification
from backend.config import logger


def _normalize_skill(skill: str) -> str:
    return skill.lower().strip()


def _skill_match(candidate_skill: str, job_skill: str) -> bool:
    """Check if a candidate skill matches a job skill (case-insensitive, token-based)."""
    cs = _normalize_skill(candidate_skill)
    js = _normalize_skill(job_skill)
    if cs == js:
        return True
    # Token containment: "machine learning" matches "ml" etc.
    cs_tokens = set(cs.replace('-', ' ').replace('/', ' ').split())
    js_tokens = set(js.replace('-', ' ').replace('/', ' ').split())
    if js_tokens and js_tokens.issubset(cs_tokens):
        return True
    if cs_tokens and cs_tokens.issubset(js_tokens):
        return True
    return False


def _find_matching_skills(candidate_skills: list[str], job_skills: list[str]) -> tuple[list[str], list[str]]:
    """Return (matched, missing) skills."""
    matched = []
    missing = []
    for js in job_skills:
        found = False
        for cs in candidate_skills:
            if _skill_match(cs, js):
                matched.append(js)
                found = True
                break
        if not found:
            missing.append(js)
    return matched, missing


def _compute_keyword_coverage(raw_text: str, job_description: str) -> tuple[int, list[str]]:
    """Compute how many job description keywords appear in the resume."""
    # Extract meaningful keywords from job description (3+ chars, not stopwords)
    stopwords = {'the', 'and', 'for', 'with', 'are', 'you', 'will', 'our', 'have', 'has',
                 'that', 'this', 'from', 'they', 'been', 'were', 'being', 'its', 'can',
                 'must', 'also', 'into', 'than', 'each', 'about', 'such', 'should',
                 'not', 'but', 'all', 'any', 'who', 'what', 'your', 'etc', 'more',
                 'looking', 'work', 'role', 'experience', 'required', 'preferred',
                 'strong', 'plus', 'years', 'ability', 'working', 'knowledge'}
    
    job_tokens = set()
    for word in job_description.lower().replace(',', ' ').replace('.', ' ').replace('/', ' ').split():
        word = word.strip('()')
        if len(word) >= 3 and word not in stopwords:
            job_tokens.add(word)
    
    resume_lower = raw_text.lower()
    resume_tokens = set(resume_lower.replace(',', ' ').replace('.', ' ').replace('/', ' ').split())
    
    if not job_tokens:
        return 100, []
    
    found = job_tokens & resume_tokens
    missing = sorted(list(job_tokens - resume_tokens))[:10]
    coverage = round(len(found) / len(job_tokens) * 100)
    return min(coverage, 100), missing


def _assess_section_completeness(candidate: CandidateProfile) -> int:
    """Score from 0-100 based on how many resume sections are populated."""
    sections = [
        bool(candidate.summary),
        len(candidate.skills) > 0,
        len(candidate.experience) > 0,
        len(candidate.education) > 0,
        len(candidate.projects) > 0,
        bool(candidate.name),
        bool(candidate.email),
    ]
    return round(sum(sections) / len(sections) * 100)


def analyze_ats(
    candidate: CandidateProfile,
    job: JobPosting,
    llm_enhancement: dict = None,
) -> ATSAnalysis:
    """Compute a deterministic ATS score with optional LLM enhancement.
    
    Scoring breakdown:
    - Required skills match: 35%
    - Preferred skills match: 15%
    - Keyword coverage: 25%
    - Section completeness: 10%
    - Experience relevance: 15%
    """
    # Required skills
    req_matched, req_missing = _find_matching_skills(candidate.skills, job.required_skills)
    req_total = max(len(job.required_skills), 1)
    skills_match_pct = round(len(req_matched) / req_total * 100)
    
    # Preferred skills
    pref_matched, pref_missing = _find_matching_skills(candidate.skills, job.preferred_skills)
    pref_total = max(len(job.preferred_skills), 1)
    pref_match_pct = round(len(pref_matched) / pref_total * 100)
    
    # Keyword coverage
    keyword_pct, keyword_gaps = _compute_keyword_coverage(candidate.raw_text, job.description)
    
    # Section completeness
    format_pct = _assess_section_completeness(candidate)
    
    # Experience relevance: check if job-related terms appear in experience section
    exp_text = ' '.join(candidate.experience).lower()
    job_title_words = set(job.title.lower().split()) - {'senior', 'junior', 'lead', 'staff', 'principal', 'intern'}
    exp_relevance = 50  # baseline
    if job_title_words:
        exp_overlap = sum(1 for w in job_title_words if w in exp_text)
        exp_relevance = min(round(exp_overlap / len(job_title_words) * 100), 100)
    if len(candidate.experience) == 0:
        exp_relevance = 20  # low but not zero (might be entry-level)
    
    # Weighted overall score
    overall = round(
        skills_match_pct * 0.35 +
        pref_match_pct * 0.15 +
        keyword_pct * 0.25 +
        format_pct * 0.10 +
        exp_relevance * 0.15
    )
    overall = max(0, min(overall, 100))
    
    # Build strengths and gaps
    strengths = []
    gaps = []
    
    if req_matched:
        strengths.append(f"Matches {len(req_matched)}/{req_total} required skills: {', '.join(req_matched[:5])}")
    if pref_matched:
        strengths.append(f"Has {len(pref_matched)} preferred skills: {', '.join(pref_matched[:3])}")
    if keyword_pct >= 60:
        strengths.append(f"Good keyword coverage ({keyword_pct}%) with job description")
    if candidate.projects:
        strengths.append(f"Includes {len(candidate.projects)} project(s) demonstrating hands-on experience")
    
    if req_missing:
        gaps.append(f"Missing {len(req_missing)} required skills: {', '.join(req_missing[:5])}")
    if pref_missing:
        gaps.append(f"Missing {len(pref_missing)} preferred skills: {', '.join(pref_missing[:3])}")
    if keyword_pct < 50:
        gaps.append(f"Low keyword coverage ({keyword_pct}%) — resume needs better terminology alignment")
    if not candidate.summary:
        gaps.append("No professional summary section found")
    
    # LLM enhancement (optional)
    recommendations = []
    summary = f"Candidate matches {overall}% of requirements for {job.title} at {job.company}."
    if llm_enhancement:
        if llm_enhancement.get('strengths'):
            strengths.extend(llm_enhancement['strengths'][:2])
        if llm_enhancement.get('recommendations'):
            recommendations = llm_enhancement['recommendations']
        if llm_enhancement.get('summary'):
            summary = llm_enhancement['summary']
    
    if not recommendations:
        # Generate deterministic recommendations
        if req_missing:
            recommendations.append(f"Add experience or projects demonstrating: {', '.join(req_missing[:3])}")
        if keyword_pct < 60:
            recommendations.append("Align resume terminology more closely with the job description")
        if not candidate.summary:
            recommendations.append("Add a professional summary tailored to this role")
        if len(candidate.experience) < 2:
            recommendations.append("Expand experience section with more detailed accomplishments")
    
    return ATSAnalysis(
        overall_score=overall,
        keyword_match=keyword_pct,
        skills_match=skills_match_pct,
        experience_match=exp_relevance,
        format_score=format_pct,
        strengths=strengths[:5],
        gaps=gaps[:5],
        recommendations=recommendations[:5],
        summary=summary,
    )


def analyze_gaps(
    candidate: CandidateProfile,
    job: JobPosting,
) -> GapAnalysis:
    """Classify skills as VERIFIED, INFERRED, or MISSING."""
    all_job_skills = list(set(job.required_skills + job.preferred_skills))
    candidate_skills_lower = {s.lower().strip() for s in candidate.skills}
    resume_lower = candidate.raw_text.lower()
    
    verified = []
    inferred = []
    missing = []
    
    for skill in all_job_skills:
        skill_lower = skill.lower().strip()
        
        # VERIFIED: explicitly listed in skills section
        if any(_skill_match(cs, skill) for cs in candidate.skills):
            verified.append(ClassifiedSkill(
                name=skill,
                classification=SkillClassification.VERIFIED,
                evidence=f"Listed in candidate's skills section",
            ))
        # INFERRED: mentioned in resume text but not in skills section
        elif skill_lower in resume_lower or any(token in resume_lower for token in skill_lower.split() if len(token) > 3):
            inferred.append(ClassifiedSkill(
                name=skill,
                classification=SkillClassification.INFERRED,
                evidence=f"Referenced in resume body but not in skills list",
            ))
        # MISSING: not found anywhere
        else:
            missing.append(ClassifiedSkill(
                name=skill,
                classification=SkillClassification.MISSING,
                evidence=None,
            ))
    
    # Identify keyword gaps
    _, keyword_gaps = _compute_keyword_coverage(candidate.raw_text, job.description)
    
    # Experience gaps
    experience_gaps = []
    if not candidate.experience:
        experience_gaps.append("No work experience section found")
    if job.experience_level in ["Senior", "Mid-level"] and len(candidate.experience) < 3:
        experience_gaps.append(f"Role requires {job.experience_level} experience; resume shows limited entries")
    
    # Profile weaknesses
    weaknesses = []
    if not candidate.summary:
        weaknesses.append("Missing professional summary")
    if len(candidate.skills) < 3:
        weaknesses.append("Very few skills listed")
    if not candidate.projects:
        weaknesses.append("No projects section to demonstrate hands-on work")
    if not candidate.education:
        weaknesses.append("No education section found")
    
    # Recommendations
    recs = []
    if missing:
        recs.append(f"Consider gaining experience in: {', '.join(s.name for s in missing[:3])}")
    if inferred:
        recs.append(f"Move these skills to your explicit skills section: {', '.join(s.name for s in inferred[:3])}")
    if weaknesses:
        recs.append(f"Address profile gaps: {'; '.join(weaknesses[:2])}")
    
    return GapAnalysis(
        verified_skills=verified,
        inferred_skills=inferred,
        missing_skills=missing,
        keyword_gaps=keyword_gaps[:10],
        experience_gaps=experience_gaps,
        profile_weaknesses=weaknesses,
        recommendations=recs,
    )
