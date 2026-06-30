"""
test_pipeline.py
-----------------
Validates the full pipeline WITHOUT needing live Credly access
(this sandbox environment gets 403'd by Credly — same as it would
from any cloud/datacenter IP; it works fine from your local machine).

Tests:
  1. Parser correctly merges native + external badge shapes
  2. Certs with NO expiry date are preserved, not dropped
  3. Database round-trip (save + retrieve)
  4. Expiry engine reports "No Expiry" instead of skipping
  5. Memory context includes ALL skills with frequency counts
  6. Skill frequency counts duplicates correctly

Run:
  cd CIA
  python tests/test_pipeline.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from provider.credly.parser import CredlyParser
from provider.credly.models import Employee, Certification, Skill
from database.schema import Schema
from database.repository import EmployeeRepository, CertificationRepository, SkillRepository
from services.expiry_engine import ExpiryEngine
from ai_agent.memory import Memory


def sep(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


# ── Mock raw Credly API responses (real shapes, fake data) ─────────────────

MOCK_NATIVE_RESPONSE = [
    {
        "id": "native-001",
        "recipient_name": "Venkat Seshu Chembeti",
        "issued_at_date": "2025-01-15",
        "expires_at_date": "2027-01-15",
        "public_url": "https://credly.com/badges/native-001",
        "badge_template": {
            "name": "Oracle Cloud Infrastructure 2025 Certified Generative AI Professional",
            "description": "Validates GenAI skills on OCI",
            "image_url": "",
            "issuer": {"summary": "Oracle"},
            "skills": [
                {"name": "Generative AI"},
                {"name": "Large Language Models (LLMs)"},
                {"name": "Cloud Architecture"},
            ],
        },
    },
    {
        # This cert has NO expiry — the exact case that was being silently dropped
        "id": "native-002",
        "recipient_name": "Venkat Seshu Chembeti",
        "issued_at_date": "2024-06-01",
        "expires_at_date": None,
        "public_url": "https://credly.com/badges/native-002",
        "badge_template": {
            "name": "AWS Certified Cloud Practitioner",
            "description": "Foundational AWS knowledge",
            "image_url": "",
            "issuer": {"summary": "Amazon Web Services"},
            "skills": [
                {"name": "Cloud Computing"},
                {"name": "AWS"},
            ],
        },
    },
    {
        "id": "native-003",
        "recipient_name": "Venkat Seshu Chembeti",
        "issued_at_date": "2025-03-01",
        "expires_at_date": "2026-08-01",  # expiring soon (for reminder test)
        "public_url": "https://credly.com/badges/native-003",
        "badge_template": {
            "name": "Microsoft Certified: Azure AI Engineer",
            "description": "Azure AI engineering skills",
            "image_url": "",
            "issuer": {"summary": "Microsoft"},
            "skills": [
                {"name": "Generative AI"},   # duplicate skill, different cert — tests frequency counting
                {"name": "Machine Learning (ML)"},
            ],
        },
    },
]

MOCK_EXTERNAL_RESPONSE = [
    {
        "id": "external-001",
        "external_badge": {
            "recipient_name": "Venkat Seshu Chembeti",
            "badge_name": "Oracle Cloud Infrastructure 2025 Certified Foundations Associate",
            "issuer_name": "Oracle",
            "badge_description": "Foundational OCI knowledge",
            "issued_at_date": "2025-02-10",
            "expires_at_date": "2027-02-10",
            "badge_url": "https://credly.com/badges/external-001",
            "image_url": "",
            "skills": [
                {"name": "Cloud Infrastructure"},
                {"name": "Oracle Applications"},
            ],
        },
    },
    {
        "id": "external-002",
        "external_badge": {
            "recipient_name": "Venkat Seshu Chembeti",
            "badge_name": "Oracle Cloud Infrastructure 2025 Certified AI Foundations Associate",
            "issuer_name": "Oracle",
            "badge_description": "Foundational AI knowledge on OCI",
            "issued_at_date": "2025-02-20",
            "expires_at_date": "2027-02-20",
            "badge_url": "https://credly.com/badges/external-002",
            "image_url": "",
            "skills": [
                {"name": "Artificial Intelligence (AI)"},
                {"name": "Machine Learning (ML)"},  # duplicate again
            ],
        },
    },
]


def test_parser():
    sep("TEST 1: Parser handles unified badges.json list (native + external shapes mixed)")

    parser = CredlyParser()
    # badges.json returns a single flat list; we simulate a mix of native-shaped
    # and external_badge-wrapped items in the same list, as a real account could have
    raw = MOCK_NATIVE_RESPONSE + MOCK_EXTERNAL_RESPONSE
    employee = parser.parse("test-user-id", raw)

    total = len(employee.certifications)
    print(f"Total certifications parsed: {total}")
    assert total == 5, f"Expected 5 certs (3 native + 2 external), got {total}"
    print("✅ All 5 certifications parsed (previously only 3 external were found)")

    print(f"Employee name resolved: {employee.full_name}")
    assert employee.full_name == "Venkat Seshu Chembeti"
    print("✅ Name correctly extracted from badge data")

    return employee


def test_no_expiry_preserved(employee):
    sep("TEST 2: Certifications with NO expiry date are preserved")

    no_expiry_certs = [c for c in employee.certifications if not c.expiry_date]
    print(f"Certs with no expiry date: {len(no_expiry_certs)}")
    for c in no_expiry_certs:
        print(f"  • {c.name}")

    assert len(no_expiry_certs) == 1, "Expected exactly 1 cert with no expiry (AWS Cloud Practitioner)"
    print("✅ No-expiry cert preserved, not silently dropped")


def test_database(employee):
    sep("TEST 3: Database round-trip")

    Schema().create_tables()
    emp_repo = EmployeeRepository()
    cert_repo = CertificationRepository()
    skill_repo = SkillRepository()

    employee_id = emp_repo.save(employee)
    print(f"Employee saved, id={employee_id}")

    for cert in employee.certifications:
        cert_id = cert_repo.save(employee_id, cert)
        for skill in cert.skills:
            skill_repo.save(cert_id, skill)

    stored_certs = cert_repo.get_by_employee(employee_id)
    print(f"Certifications retrieved from DB: {len(stored_certs)}")
    assert len(stored_certs) == 5
    print("✅ All certs round-tripped through SQLite correctly")

    stored_skills = skill_repo.get_by_employee(employee_id)
    print(f"\nSkill frequency from DB:")
    for s in stored_skills:
        print(f"  • {s['name']} (x{s['occurrences']})")

    return employee_id


def test_expiry_engine(employee):
    sep("TEST 4: Expiry engine reports 'No Expiry' instead of skipping")

    engine = ExpiryEngine()
    statuses = engine.get_status(employee)

    print(f"Total statuses returned: {len(statuses)}")
    assert len(statuses) == 5, "Expiry engine should report ALL certs, including no-expiry ones"
    print("✅ Expiry engine covers every certification")

    for s in statuses:
        print(f"  • {s.certification[:50]:<50} → {s.status} ({s.days_remaining if s.days_remaining is not None else 'N/A'} days)")

    no_expiry_status = [s for s in statuses if s.status == "No Expiry"]
    assert len(no_expiry_status) == 1
    print("\n✅ 'No Expiry' status correctly assigned (was previously skipped via `continue`)")


def test_skill_frequency(employee):
    sep("TEST 5: Skill frequency counts duplicates correctly")

    freq = employee.skill_frequency
    print("Skill frequency map:")
    for name, count in sorted(freq.items(), key=lambda x: -x[1]):
        print(f"  • {name}: {count}")

    assert freq.get("Generative AI") == 2, "Generative AI appears in 2 certs"
    assert freq.get("Machine Learning (ML)") == 2, "ML appears in 2 certs"
    print("\n✅ Duplicate skills across certs are counted, not collapsed to 1")

    print(f"\nTotal skill instances (with duplicates): {len(employee.all_skills)}")
    print(f"Total unique skills: {len(employee.unique_skills)}")
    assert len(employee.all_skills) > len(employee.unique_skills)
    print("✅ all_skills (with dupes) > unique_skills, as expected")


def test_memory_context(employee):
    sep("TEST 6: AI Memory context includes ALL data")

    memory = Memory()
    memory.load_employee(employee)

    ctx = memory.employee_context

    # Every cert name should appear in context
    for cert in employee.certifications:
        assert cert.name in ctx, f"Missing cert in context: {cert.name}"
    print(f"✅ All {len(employee.certifications)} certifications present in AI context")

    # No-expiry cert should say so explicitly, not be blank/missing
    assert "No expiry (does not expire)" in ctx
    print("✅ No-expiry certs explicitly labeled in AI context (AI won't hallucinate a date)")

    # Skill frequency markers present
    assert "(x2)" in ctx
    print("✅ Skill frequency counts (e.g. 'x2') included in AI context")

    print(f"\nContext length: {len(ctx)} characters")
    print("\n--- Context preview (first 600 chars) ---")
    print(ctx[:600])
    print("...")


if __name__ == "__main__":
    print("\n🤖 CERTIFICATE INTELLIGENCE — PIPELINE TEST SUITE")
    print("   (Using mock Credly data — sandbox network can't reach credly.com,")
    print("    same as it would be blocked from any cloud/datacenter IP)")

    employee = test_parser()
    test_no_expiry_preserved(employee)
    test_database(employee)
    test_expiry_engine(employee)
    test_skill_frequency(employee)
    test_memory_context(employee)

    print(f"\n{'='*60}")
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print("""
This confirms the FIXES work correctly:
  1. Native + external badges are merged (was: only external)
  2. No-expiry certs are preserved (was: silently dropped)
  3. Skill frequency counts duplicates (was: deduplicated, losing signal)
  4. AI context includes full detail (was: incomplete)

NEXT STEP — run against YOUR real Credly data:
  This sandbox cannot reach credly.com (blocked at network level).
  On YOUR machine, run:
      python main.py
  This now uses the correct public endpoint (badges.json) instead of the
  OAuth-gated /api/v1/ route that returned 401 — it should return ALL your
  badges (Oracle certs that were missing before, plus the ones you already had).
""")
