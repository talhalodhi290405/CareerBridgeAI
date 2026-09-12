"""Centralized Job Search Service abstraction supporting Adzuna, Jobicy, Remotive, Arbeitnow, and Demo fallback."""
import json
import os
import re
import urllib.request
import urllib.parse
from typing import List, Optional, Dict, Any

from backend.models import JobPosting, JobSearchFilters
from backend.config import logger
from backend.rag_engine import load_jobs


def get_adzuna_credentials() -> tuple[Optional[str], Optional[str]]:
    """Retrieve Adzuna credentials from Streamlit secrets or environment variables."""
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    
    try:
        import streamlit as st
        if not app_id:
            app_id = st.secrets.get("ADZUNA_APP_ID")
        if not app_key:
            app_key = st.secrets.get("ADZUNA_APP_KEY")
    except Exception:
        pass

    if app_id == "your_adzuna_app_id" or not app_id:
        app_id = None
    if app_key == "your_adzuna_app_key" or not app_key:
        app_key = None

    return app_id, app_key


def _clean_html(raw_html: str) -> str:
    """Remove HTML tags from job description text."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    return " ".join(clean.split())


def _extract_skills_from_description(text: str) -> tuple[list[str], list[str]]:
    """Basic heuristic skill extraction from job text."""
    text_lower = text.lower()
    common_skills = [
        "Python", "Java", "C++", "SQL", "PostgreSQL", "Docker", "Kubernetes",
        "AWS", "GCP", "Azure", "React", "TypeScript", "JavaScript", "Node.js",
        "TensorFlow", "PyTorch", "Git", "Linux", "REST API", "FastAPI",
        "Machine Learning", "Deep Learning", "NLP", "Pandas", "NumPy",
        "Spark", "Hadoop", "Airflow", "CI/CD", "DevOps", "Microservices"
    ]
    matched = [s for s in common_skills if re.search(r'\b' + re.escape(s.lower()) + r'\b', text_lower)]
    req = matched[:min(4, len(matched))]
    pref = matched[min(4, len(matched)):min(8, len(matched))]
    return req if req else ["Software Development", "Problem Solving"], pref


def fetch_adzuna_jobs(query: str = "software engineer", location: str = "", country_code: str = "us", limit: int = 15) -> list[JobPosting]:
    """Fetch jobs from Adzuna API."""
    app_id, app_key = get_adzuna_credentials()
    if not app_id or not app_key:
        logger.info("Adzuna API credentials not configured. Skipping Adzuna.")
        return []

    valid_country_codes = {"us", "gb", "ca", "de", "fr", "au", "in", "pk"}
    c_code = country_code.lower() if country_code.lower() in valid_country_codes else "us"

    url = f"https://api.adzuna.com/v1/api/jobs/{c_code}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": limit,
        "what": query,
    }
    if location:
        params["where"] = location

    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    logger.info(f"Querying Adzuna API: {full_url}")

    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "CareerBridgeAI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        raw_results = data.get("results", [])
        postings = []
        for item in raw_results:
            desc = _clean_html(item.get("description", ""))
            req_s, pref_s = _extract_skills_from_description(desc)
            loc_area = item.get("location", {}).get("display_name", location or "Remote/Onsite")
            title = item.get("title", query.title())
            company = item.get("company", {}).get("display_name", "Tech Company")
            job_url = item.get("redirect_url") or item.get("url")
            if not job_url or not str(job_url).startswith("http"):
                job_url = f"https://www.google.com/search?q={urllib.parse.quote(title + ' ' + company + ' apply')}"
            
            posting = JobPosting(
                id=f"adzuna_{item.get('id')}",
                title=title,
                company=company,
                location=loc_area,
                country=country_code.upper() if country_code else "US",
                city=location if location else loc_area.split(",")[0],
                remote="remote" in desc.lower() or "remote" in loc_area.lower(),
                work_arrangement="Remote" if ("remote" in desc.lower() or "remote" in loc_area.lower()) else "On-site",
                employment_type="Full-time",
                experience_level="Mid-level",
                description=desc,
                description_is_snippet=True,
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                salary_currency="USD" if c_code == "us" else "GBP" if c_code == "gb" else "EUR",
                posted_date=item.get("created", "")[:10],
                url=job_url,
                source="Adzuna",
                required_skills=req_s,
                preferred_skills=pref_s,
            )
            postings.append(posting)
        
        logger.info(f"Successfully retrieved {len(postings)} jobs from Adzuna.")
        return postings
    except Exception as e:
        logger.error(f"Adzuna API request failed: {e}")
        return []


def fetch_jobicy_jobs(query: str = "", limit: int = 15) -> list[JobPosting]:
    """Fetch jobs from Jobicy free REST API."""
    url = f"https://jobicy.com/api/v2/remote-jobs?count={limit}"
    if query:
        url += f"&geo={urllib.parse.quote(query)}"
    
    logger.info(f"Querying Jobicy API: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        raw_jobs = data.get("jobs", [])
        postings = []
        for item in raw_jobs:
            title = item.get("jobTitle", "")
            company = item.get("companyName", "Tech Company")
            desc = _clean_html(item.get("jobDescription", ""))
            req_s, pref_s = _extract_skills_from_description(desc)

            emp_type = item.get("jobType", "Full-time")
            if isinstance(emp_type, list):
                emp_type = ", ".join(str(x) for x in emp_type)

            job_url = item.get("url")
            if not job_url or not str(job_url).startswith("http"):
                job_url = f"https://www.google.com/search?q={urllib.parse.quote(title + ' ' + company + ' apply')}"

            posting = JobPosting(
                id=f"jobicy_{item.get('id', title[:15])}",
                title=title,
                company=company,
                location=item.get("jobGeo", "Worldwide Remote"),
                remote=True,
                work_arrangement="Remote",
                employment_type=emp_type,
                experience_level=item.get("jobLevel", "Mid-level") or "Mid-level",
                description=desc[:2000] if desc else f"{title} remote position at {company}.",
                description_is_snippet=False,
                salary_min=float(item.get("annualSalaryMin")) if item.get("annualSalaryMin") else None,
                salary_max=float(item.get("annualSalaryMax")) if item.get("annualSalaryMax") else None,
                salary_currency=item.get("salaryCurrency", "USD"),
                posted_date=str(item.get("pubDate", ""))[:10],
                url=job_url,
                source="Jobicy",
                required_skills=req_s,
                preferred_skills=pref_s,
            )
            postings.append(posting)
        
        logger.info(f"Retrieved {len(postings)} jobs from Jobicy.")
        return postings
    except Exception as e:
        logger.error(f"Jobicy API failed: {e}")
        return []


def fetch_arbeitnow_jobs(query: str = "", limit: int = 15) -> list[JobPosting]:
    """Fetch jobs from Arbeitnow free REST API."""
    url = "https://www.arbeitnow.com/api/v1/jobs"
    logger.info("Querying Arbeitnow API...")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            if raw.startswith(b'<!DOCTYPE') or raw.startswith(b'<html'):
                logger.warning("Arbeitnow returned HTML instead of JSON.")
                return []
            data = json.loads(raw.decode("utf-8"))
        
        raw_jobs = data.get("data", [])
        postings = []
        
        query_lower = query.lower().strip()
        for item in raw_jobs:
            title = item.get("title", "")
            company = item.get("company_name", "Tech Company")
            desc_html = item.get("description", "")
            desc = _clean_html(desc_html)
            
            if query_lower and (query_lower not in title.lower() and query_lower not in desc.lower()):
                continue

            req_s, pref_s = _extract_skills_from_description(desc)
            is_remote = item.get("remote", False) or "remote" in desc.lower()

            job_url = item.get("url")
            if not job_url or not str(job_url).startswith("http"):
                job_url = f"https://www.google.com/search?q={urllib.parse.quote(title + ' ' + company + ' apply')}"

            posting = JobPosting(
                id=f"arbeitnow_{item.get('slug', title[:15])}",
                title=title,
                company=company,
                location=item.get("location", "Europe / Remote"),
                remote=is_remote,
                work_arrangement="Remote" if is_remote else "On-site",
                employment_type="Full-time",
                experience_level="Mid-level",
                description=desc if len(desc) > 100 else f"{title} position at {company}.",
                description_is_snippet=False,
                posted_date=str(item.get("created_at", ""))[:10] if item.get("created_at") else "",
                url=job_url,
                source="Arbeitnow",
                required_skills=req_s,
                preferred_skills=pref_s,
            )
            postings.append(posting)
            if len(postings) >= limit:
                break
        
        logger.info(f"Retrieved {len(postings)} jobs from Arbeitnow.")
        return postings
    except Exception as e:
        logger.error(f"Arbeitnow API failed: {e}")
        return []


def fetch_remotive_jobs(query: str = "", limit: int = 15) -> list[JobPosting]:
    """Fetch jobs from Remotive free remote jobs API."""
    base_url = "https://remotive.com/api/remote-jobs"
    params = {}
    if query:
        params["search"] = query
    params["limit"] = limit

    full_url = f"{base_url}?{urllib.parse.urlencode(params)}" if params else base_url
    logger.info(f"Querying Remotive API: {full_url}")
    
    try:
        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        raw_jobs = data.get("jobs", [])
        postings = []
        for item in raw_jobs:
            title = item.get("title", "")
            company = item.get("company_name", "Remote Enterprise")
            desc = _clean_html(item.get("description", ""))
            req_s, pref_s = _extract_skills_from_description(desc)

            job_url = item.get("url")
            if not job_url or not str(job_url).startswith("http"):
                job_url = f"https://www.google.com/search?q={urllib.parse.quote(title + ' ' + company + ' apply')}"

            posting = JobPosting(
                id=f"remotive_{item.get('id')}",
                title=title,
                company=company,
                location=item.get("candidate_required_location", "Worldwide Remote"),
                remote=True,
                work_arrangement="Remote",
                employment_type=item.get("job_type", "Full-time").replace("_", " ").title(),
                experience_level="Mid-level",
                description=desc[:2000] if desc else f"{title} remote position.",
                description_is_snippet=False,
                salary_currency="USD",
                posted_date=str(item.get("publication_date", ""))[:10],
                url=job_url,
                source="Remotive",
                required_skills=req_s,
                preferred_skills=pref_s,
            )
            postings.append(posting)
            if len(postings) >= limit:
                break
        
        logger.info(f"Retrieved {len(postings)} jobs from Remotive.")
        return postings
    except Exception as e:
        logger.error(f"Remotive API failed: {e}")
        return []



def _deduplicate_jobs(jobs: list[JobPosting]) -> list[JobPosting]:
    """Deduplicate job postings by normalized (title, company)."""
    seen = set()
    unique_jobs = []
    for j in jobs:
        key = (j.title.lower().strip(), j.company.lower().strip())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(j)
    return unique_jobs


def search_live_jobs(filters: Optional[JobSearchFilters] = None) -> tuple[list[JobPosting], str]:
    """Execute provider fallback chain for job search.
    Returns: (list of JobPostings, source provider status message)
    """
    if filters is None:
        filters = JobSearchFilters()

    query = filters.desired_role.strip() or "Software Engineer"
    location = filters.city.strip() or filters.country.strip()

    # Step 1: Try Adzuna API
    adzuna_jobs = fetch_adzuna_jobs(query=query, location=location, country_code="us", limit=15)
    if adzuna_jobs:
        filtered = _apply_local_filters(adzuna_jobs, filters)
        if filtered:
            return filtered, "🟢 LIVE — Adzuna API"

    # Step 2: Try Remotive API
    remotive_jobs = fetch_remotive_jobs(query=query, limit=15)
    if remotive_jobs:
        filtered = _apply_local_filters(remotive_jobs, filters)
        if filtered:
            return filtered, "🟢 LIVE — Remotive API"

    # Step 3: Try Jobicy API
    jobicy_jobs = fetch_jobicy_jobs(query=query, limit=15)
    if jobicy_jobs:
        filtered = _apply_local_filters(jobicy_jobs, filters)
        if filtered:
            return filtered, "🟢 LIVE — Jobicy API"

    # Step 4: Try Arbeitnow API
    arbeitnow_jobs = fetch_arbeitnow_jobs(query=query if query != "Software Engineer" else "", limit=15)
    if arbeitnow_jobs:
        filtered = _apply_local_filters(arbeitnow_jobs, filters)
        if filtered:
            return filtered, "🟢 LIVE — Arbeitnow API"

    # Step 5: Emergency Fallback — Demo Backup JSON
    logger.info("Live job APIs returned no matches. Falling back to Demo Backup.")
    demo_jobs = load_jobs()
    for dj in demo_jobs:
        dj.source = "Demo Backup"
    filtered_demo = _apply_local_filters(demo_jobs, filters)
    return filtered_demo if filtered_demo else demo_jobs, "Live job providers are currently unavailable. Showing verified Demo Mode results."


def _apply_local_filters(jobs: list[JobPosting], filters: JobSearchFilters) -> list[JobPosting]:
    """Apply client-side filtering for location, work arrangement, and employment type."""
    filtered = jobs
    
    # Work arrangement filter
    if filters.work_arrangement != "Any":
        target = filters.work_arrangement.lower()
        filtered = [j for j in filtered if target in j.work_arrangement.lower() or (target == "remote" and j.remote)]

    # Employment type filter
    if filters.employment_type != "Any":
        target = filters.employment_type.lower()
        filtered = [j for j in filtered if target in j.employment_type.lower() or target in j.type.lower()]

    # Experience level filter
    if filters.experience_level != "Any":
        target = filters.experience_level.lower()
        filtered = [j for j in filtered if target in j.experience_level.lower()]

    # Deduplicate
    return _deduplicate_jobs(filtered)
