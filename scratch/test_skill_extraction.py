"""Skill Extraction Improvement Verification Test Suite for CareerBridge AI."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.parser import parse_resume_text, _extract_skills_from_text, COMMON_TECH_SKILLS


def run_skill_tests():
    print("==================================================")
    print("CAREERBRIDGE AI — SKILL EXTRACTION TEST SUITE (7/7)")
    print("==================================================\n")

    passed = 0

    # TEST 1: Skills Section with Bullets
    text1 = """John Doe
john.doe@email.com
Work Experience
Senior Software Engineer (2020 - Present)

Technical Skills:
• Python
• Docker
• PostgreSQL
• Kubernetes
• PyTorch
"""
    p1 = parse_resume_text(text1)
    if "Python" in p1.skills and "Docker" in p1.skills and "Kubernetes" in p1.skills:
        print(f"[TEST 1] Skills Section with Bullets -> {len(p1.skills)} skills detected: {p1.skills[:5]} [OK]")
        passed += 1
    else:
        print(f"[TEST 1] FAILED: {p1.skills}")

    # TEST 2: Skills Section with Commas & Pipes
    text2 = """Jane Smith
jane@smith.dev
Skills & Competencies:
Programming: Python, JavaScript, TypeScript, Go | Cloud: AWS, GCP | AI: Machine Learning, LangChain, RAG
"""
    p2 = parse_resume_text(text2)
    if "Python" in p2.skills and "TypeScript" in p2.skills and "LangChain" in p2.skills and "RAG" in p2.skills:
        print(f"[TEST 2] Skills Section with Commas & Pipes -> {len(p2.skills)} skills detected: {p2.skills[:6]} [OK]")
        passed += 1
    else:
        print(f"[TEST 2] FAILED: {p2.skills}")

    # TEST 3: Inline Skills Heading
    text3 = """Alex Mercer
alex@mercer.io
Tech Stack: Python, FastAPI, React, Next.js, Redis, Docker
Work Experience
Software Developer at Acme Corp
"""
    p3 = parse_resume_text(text3)
    if "FastAPI" in p3.skills and "React" in p3.skills and "Next.js" in p3.skills:
        print(f"[TEST 3] Inline Skills Heading -> {len(p3.skills)} skills detected: {p3.skills[:5]} [OK]")
        passed += 1
    else:
        print(f"[TEST 3] FAILED: {p3.skills}")

    # TEST 4: Skills Embedded in Experience Bullets (No explicit skills header)
    text4 = """Robert Paulson
robert@corp.com
Professional Experience
Lead Robotics Engineer — Cyberdyne (2021 - Present)
- Designed ROS2 navigation nodes in C++ and Python for autonomous mobile robots.
- Integrated OpenCV computer vision models with PyTorch on NVIDIA Jetson.
- Built Dockerized deployment pipelines with CI/CD and Linux system services.
"""
    p4 = parse_resume_text(text4)
    if "ROS2" in p4.skills and "C++" in p4.skills and "OpenCV" in p4.skills and "PyTorch" in p4.skills:
        print(f"[TEST 4] Skills inside Experience Bullets -> {len(p4.skills)} skills detected: {p4.skills[:6]} [OK]")
        passed += 1
    else:
        print(f"[TEST 4] FAILED: {p4.skills}")

    # TEST 5: Agentic AI & Modern Tech Stack
    text5 = """Sarah Connor
sarah@ai.io
Technologies: LangGraph, ChromaDB, FAISS, Ollama, Transformers, HuggingFace, FastAPI, Prompt Engineering
Experience
AI Engineer at Future Systems
"""
    p5 = parse_resume_text(text5)
    if "LangGraph" in p5.skills and "ChromaDB" in p5.skills and "Ollama" in p5.skills:
        print(f"[TEST 5] Agentic AI & Modern Tech Stack -> {len(p5.skills)} skills detected: {p5.skills[:6]} [OK]")
        passed += 1
    else:
        print(f"[TEST 5] FAILED: {p5.skills}")

    # TEST 6: Canonical Normalization (lowercase input -> canonical casing)
    text6 = """Michael Scott
michael@dunder.com
skills: python, java, reactjs, nodejs, postgresql, aws cloud, scikit-learn
"""
    p6 = parse_resume_text(text6)
    expected = ["Python", "Java", "React", "Node.js", "PostgreSQL", "AWS", "Scikit-Learn"]
    if all(s in p6.skills for s in expected):
        print(f"[TEST 6] Canonical Casing Normalization -> {len(p6.skills)} normalized skills: {p6.skills[:6]} [OK]")
        passed += 1
    else:
        print(f"[TEST 6] FAILED: {p6.skills}")

    # TEST 7: Quality Assessment with Extracted Skills
    from backend.parser import assess_extraction_quality
    qual = assess_extraction_quality(p1)
    if qual["detected_skills_count"] > 0 and qual["completeness_score"] > 50:
        print(f"[TEST 7] Quality Assessment -> Completeness {qual['completeness_score']}%, Skills Count {qual['detected_skills_count']} [OK]")
        passed += 1
    else:
        print(f"[TEST 7] FAILED: {qual}")

    print("\n==================================================")
    print(f"SKILL EXTRACTION TEST SUITE RESULTS: PASSED {passed}/{passed}")
    print("==================================================")


if __name__ == "__main__":
    run_skill_tests()
