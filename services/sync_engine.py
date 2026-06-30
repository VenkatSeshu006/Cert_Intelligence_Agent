from database.repository import EmployeeRepository, CertificationRepository, SkillRepository
from provider.credly.user_service import UserService


class SyncEngine:

    def __init__(self):
        self.user_service = UserService()
        self.employee_repo = EmployeeRepository()
        self.cert_repo = CertificationRepository()
        self.skill_repo = SkillRepository()

    def run(self, user_id: str):
        print("=" * 60)
        print("Starting Synchronization")
        print("=" * 60)

        employee = self.user_service.load_employee(user_id)

        if not employee.certifications:
            print("⚠️  No certifications returned from Credly for this user_id.")
            print("    Check that the profile is public and the user_id is correct.")
            return employee

        employee_id = self.employee_repo.save(employee)

        cert_count = 0
        skill_count = 0
        no_expiry_count = 0

        for cert in employee.certifications:
            cert_id = self.cert_repo.save(employee_id, cert)
            cert_count += 1

            if not cert.expiry_date:
                no_expiry_count += 1

            for skill in cert.skills:
                self.skill_repo.save(cert_id, skill)
                skill_count += 1

        print()
        print("Synchronization Complete")
        print(f"Employee            : {employee.full_name}")
        print(f"Certifications      : {cert_count}")
        print(f"  - Native (Credly) : {sum(1 for c in employee.certifications if c.source == 'native')}")
        print(f"  - External        : {sum(1 for c in employee.certifications if c.source == 'external')}")
        print(f"  - No expiry date  : {no_expiry_count}")
        print(f"Skill links saved   : {skill_count}")
        print(f"Unique skills       : {len(employee.unique_skills)}")
        print("=" * 60)

        return employee
