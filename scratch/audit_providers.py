"""Independent Job Provider Audit Script for CareerBridge AI.
Tests Adzuna, Arbeitnow, Remotive, and Jobicy providers independently.
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.job_service import (
    fetch_adzuna_jobs, fetch_arbeitnow_jobs, fetch_remotive_jobs,
    fetch_jobicy_jobs, get_adzuna_credentials, _deduplicate_jobs
)

def run_provider_audit():
    print("==================================================")
    print("LIVE JOB PROVIDER VERIFICATION AUDIT")
    print("==================================================")

    results = {}

    # Provider 1: Adzuna
    print("\n[1] Testing Provider: Adzuna")
    app_id, app_key = get_adzuna_credentials()
    if not app_id or not app_key:
        print("  Status: NOT CONFIGURED — requires ADZUNA_APP_ID and ADZUNA_APP_KEY.")
        results["Adzuna"] = "NOT CONFIGURED — requires ADZUNA_APP_ID and ADZUNA_APP_KEY"
    else:
        try:
            jobs = fetch_adzuna_jobs(query="Software Engineer", limit=5)
            if jobs:
                j = jobs[0]
                assert j.title and j.company and j.url and j.source == "Adzuna"
                print(f"  Status: PASS ({len(jobs)} jobs returned)")
                print(f"  Sample: '{j.title}' at {j.company} | Source: {j.source} | URL: {j.url[:40]}...")
                results["Adzuna"] = "PASS"
            else:
                print("  Status: FAIL (0 jobs returned)")
                results["Adzuna"] = "FAIL"
        except Exception as e:
            print(f"  Status: FAIL ({e})")
            results["Adzuna"] = f"FAIL: {e}"

    # Provider 2: Arbeitnow
    print("\n[2] Testing Provider: Arbeitnow")
    try:
        jobs = fetch_arbeitnow_jobs(query="", limit=5)
        if jobs:
            j = jobs[0]
            assert j.title and j.company and j.source == "Arbeitnow"
            print(f"  Status: PASS ({len(jobs)} jobs returned)")
            print(f"  Sample: '{j.title}' at {j.company} | Source: {j.source}")
            results["Arbeitnow"] = "PASS"
        else:
            print("  Status: FAIL / BYPASSED BY CLOUDFLARE (Handled gracefully by fallback)")
            results["Arbeitnow"] = "FAIL (Cloudflare HTML Protection - Fallback engaged)"
    except Exception as e:
        print(f"  Status: FAIL ({e})")
        results["Arbeitnow"] = f"FAIL: {e}"

    # Provider 3: Remotive
    print("\n[3] Testing Provider: Remotive")
    try:
        jobs = fetch_remotive_jobs(query="Python", limit=5)
        if jobs:
            j = jobs[0]
            assert j.title and j.company and j.url and j.source == "Remotive"
            assert j.remote is True
            print(f"  Status: PASS ({len(jobs)} jobs returned)")
            print(f"  Sample: '{j.title}' at {j.company} | Source: {j.source} | URL: {j.url[:40]}...")
            results["Remotive"] = "PASS"
        else:
            print("  Status: FAIL (0 jobs returned)")
            results["Remotive"] = "FAIL"
    except Exception as e:
        print(f"  Status: FAIL ({e})")
        results["Remotive"] = f"FAIL: {e}"

    # Provider 4: Jobicy
    print("\n[4] Testing Provider: Jobicy")
    try:
        jobs = fetch_jobicy_jobs(query="", limit=5)
        if jobs:
            j = jobs[0]
            assert j.title and j.company and j.url and j.source == "Jobicy"
            print(f"  Status: PASS ({len(jobs)} jobs returned)")
            print(f"  Sample: '{j.title}' at {j.company} | Source: {j.source} | URL: {j.url[:40]}...")
            results["Jobicy"] = "PASS"
        else:
            print("  Status: FAIL (0 jobs returned)")
            results["Jobicy"] = "FAIL"
    except Exception as e:
        print(f"  Status: FAIL ({e})")
        results["Jobicy"] = f"FAIL: {e}"

    # Deduplication Verification
    print("\n[5] Testing Deduplication Logic")
    try:
        from backend.models import JobPosting
        dup1 = JobPosting(id="1", title="Python Dev", company="Acme", location="US", description="d")
        dup2 = JobPosting(id="2", title="Python Dev", company="Acme", location="US", description="d")
        deduped = _deduplicate_jobs([dup1, dup2])
        assert len(deduped) == 1
        print("  Status: PASS (Deduplication verified)")
    except Exception as e:
        print(f"  Status: FAIL ({e})")

    print("\n==================================================")
    print("PROVIDER AUDIT SUMMARY:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("==================================================")

if __name__ == "__main__":
    run_provider_audit()
