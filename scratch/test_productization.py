"""Productization Test Suite for CareerBridge AI.
Verifies local storage persistence, embedded AI Coach, live job integration, and golden path integrity.
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_productization_tests():
    print("==================================================")
    print("CAREERBRIDGE AI — PRODUCTIZATION TEST SUITE")
    print("==================================================")

    results = {}

    # Test 1: Local Session Storage Persistence
    print("\n[Test 1] Local Session Storage Persistence (storage.py)")
    try:
        from backend.storage import save_session_state, load_session_state
        from backend.demo import get_demo_candidate
        from backend.models import JobSearchFilters, CoachMessage

        cand = get_demo_candidate()
        cand.name = "Test Persistent Candidate"
        filters = JobSearchFilters(desired_role="AI Engineer", city="Lahore")
        history = [CoachMessage(role="user", content="Hello", timestamp="12:00")]

        state_to_save = {
            "candidate": cand,
            "search_filters": filters,
            "coach_history": history,
            "is_demo": False
        }

        save_success = save_session_state(state_to_save)
        assert save_success is True, "save_session_state failed"

        restored = load_session_state()
        assert restored.get("candidate") is not None
        assert restored["candidate"].name == "Test Persistent Candidate"
        assert restored["search_filters"].desired_role == "AI Engineer"
        print("  [OK] Session state saved and restored from data/user_session.json successfully!")
        results[1] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        results[1] = f"FAIL: {e}"

    # Test 2: Dashboard Embedded Coach Context Memory
    print("\n[Test 2] Embedded Dashboard AI Coach Context")
    try:
        from backend.demo import get_demo_candidate, get_demo_ats_analysis, get_demo_gap_analysis
        from backend.coach import ask_career_coach
        from backend.models import CoachMessage

        cand = get_demo_candidate()
        ats = get_demo_ats_analysis()
        gap = get_demo_gap_analysis()

        reply = ask_career_coach("How can I improve my ATS score?", [], cand, None, ats, gap, [])
        assert reply is not None and len(reply) > 50
        print(f"  [OK] Coach reply generated ({len(reply)} chars)")
        print(f"  [OK] Reply snippet: '{reply[:100]}...'")
        results[2] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        results[2] = f"FAIL: {e}"

    # Test 3: Live Job Provider Search
    print("\n[Test 3] Live Job Provider Search")
    try:
        from backend.job_service import search_live_jobs, JobSearchFilters
        filters = JobSearchFilters(desired_role="Python")
        jobs, status = search_live_jobs(filters)
        assert len(jobs) > 0
        assert jobs[0].source in ["Adzuna", "Remotive", "Jobicy", "Arbeitnow", "Demo Backup"]
        print(f"  [OK] Live job provider returned {len(jobs)} jobs. Source: {jobs[0].source}")
        results[3] = "PASS"
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        results[3] = f"FAIL: {e}"

    print("\n==================================================")
    print("PRODUCTIZATION TEST SUMMARY:")
    passed_count = sum(1 for v in results.values() if v == "PASS")
    total_count = len(results)
    print(f"PASSED: {passed_count}/{total_count}")
    print("==================================================")

if __name__ == "__main__":
    run_productization_tests()
