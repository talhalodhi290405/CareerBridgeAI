"""Phase 3 Integration Test Suite for CareerBridge AI Product UX + Live Job Search."""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_phase3_tests():
    print("==================================================")
    print("CAREERBRIDGE AI — PHASE 3 INTEGRATION TEST SUITE")
    print("==================================================")

    test_results = {}

    # Test 1: Live Job Search & Fallback Chain
    print("\n[Test 1] Live Job Search & Provider Abstraction")
    try:
        from backend.job_service import search_live_jobs, JobSearchFilters
        filters = JobSearchFilters(desired_role="Python")
        jobs, status_msg = search_live_jobs(filters)
        assert len(jobs) > 0, "No jobs returned by job service"
        assert jobs[0].title is not None
        assert jobs[0].company is not None
        assert jobs[0].source in ["Adzuna", "Arbeitnow", "Remotive", "Demo Backup"]
        print(f"  [OK] Retrived {len(jobs)} jobs. Source Status: '{status_msg.encode('ascii', 'ignore').decode('ascii')}'")
        print(f"  [OK] Job 1: '{jobs[0].title}' at {jobs[0].company} (Source: {jobs[0].source})")
        test_results[1] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        test_results[1] = f"FAIL: {e}"

    # Test 2: Job Filtering Logic
    print("\n[Test 2] Job Search Filtering")
    try:
        from backend.job_service import search_live_jobs, JobSearchFilters
        remote_filters = JobSearchFilters(desired_role="Developer", work_arrangement="Remote")
        r_jobs, _ = search_live_jobs(remote_filters)
        assert len(r_jobs) > 0, "No remote jobs returned"
        assert all(j.remote or "remote" in j.work_arrangement.lower() for j in r_jobs)
        print(f"  [OK] Remote filter verified: {len(r_jobs)} remote jobs returned")
        test_results[2] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        test_results[2] = f"FAIL: {e}"

    # Test 3: Application Tracking Models & Visual Pipeline
    print("\n[Test 3] Application Record Tracking")
    try:
        from backend.models import ApplicationRecord, ApplicationStatus
        app = ApplicationRecord(
            id="app_100", job_id="job_1", job_title="ML Engineer", company="TechNova",
            source="Remotive", status=ApplicationStatus.SAVED, date="2026-09-12"
        )
        assert app.status == ApplicationStatus.SAVED
        # Transition status
        app.status = ApplicationStatus.APPLIED
        assert app.status == ApplicationStatus.APPLIED
        app.status = ApplicationStatus.INTERVIEW
        assert app.status == ApplicationStatus.INTERVIEW
        print(f"  [OK] Application status transitions verified: Saved -> Applied -> Interview")
        test_results[3] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        test_results[3] = f"FAIL: {e}"

    # Test 4: Cover Letter Generation & Tone Control
    print("\n[Test 4] Cover Letter Generation with Tones")
    try:
        from backend.demo import get_demo_candidate
        from backend.rag_engine import load_jobs
        from backend.cover_letter import generate_cover_letter

        cand = get_demo_candidate()
        job = load_jobs()[0]

        for tone in ["Standard", "Concise", "Technical", "Formal"]:
            cl = generate_cover_letter(cand, job, tone=tone)
            assert cl.content is not None and len(cl.content) > 50
            assert cl.tone == tone
            print(f"  [OK] Cover Letter tone '{tone}' generated ({len(cl.content)} chars)")
        test_results[4] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        test_results[4] = f"FAIL: {e}"

    # Test 5: AI Career Coach Chatbot Engine
    print("\n[Test 5] AI Career Coach Context Awareness")
    try:
        from backend.demo import get_demo_candidate, get_demo_ats_analysis, get_demo_gap_analysis
        from backend.rag_engine import load_jobs
        from backend.coach import ask_career_coach

        cand = get_demo_candidate()
        job = load_jobs()[0]
        ats = get_demo_ats_analysis()
        gap = get_demo_gap_analysis()

        reply = ask_career_coach("Why is my ATS score low?", [], cand, job, ats, gap, [])
        assert reply is not None and len(reply) > 50
        print(f"  [OK] Coach response received ({len(reply)} chars):")
        print(f"      '{reply[:120]}...'")
        test_results[5] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        test_results[5] = f"FAIL: {e}"

    # Test 6: CV Profile Editor Data Model Mutability
    print("\n[Test 6] CV Profile Editor Mutability")
    try:
        from backend.demo import get_demo_candidate
        cand = get_demo_candidate()
        orig_name = cand.name
        cand.name = "Alex Chen Updated"
        cand.skills.append("Kubernetes")
        assert cand.name == "Alex Chen Updated"
        assert "Kubernetes" in cand.skills
        print(f"  [OK] Candidate profile mutation verified: '{orig_name}' -> '{cand.name}'")
        test_results[6] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        test_results[6] = f"FAIL: {e}"

    print("\n==================================================")
    print("PHASE 3 TEST SUMMARY:")
    passed_count = sum(1 for v in test_results.values() if v == "PASS")
    total_count = len(test_results)
    print(f"PASSED: {passed_count}/{total_count}")
    print("==================================================")

if __name__ == "__main__":
    run_phase3_tests()
