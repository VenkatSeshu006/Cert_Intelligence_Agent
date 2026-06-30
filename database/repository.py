"""
All repository classes in one file. With 5 tables this is easier to navigate
than 5 separate files, and avoids the circular-import risk of each repo
opening its own Database() connection (Database is now a singleton anyway).
"""

from .database import Database
from provider.credly.models import Employee, Certification, Skill


class EmployeeRepository:

    def __init__(self):
        self.db = Database()

    def save(self, employee: Employee) -> int:
        existing = self.db.fetchone(
            "SELECT id FROM employees WHERE credly_user_id = ?",
            (employee.user_id,)
        )
        if existing:
            self.db.execute(
                "UPDATE employees SET full_name = ?, synced_at = datetime('now') WHERE id = ?",
                (employee.full_name, existing["id"])
            )
            return existing["id"]

        self.db.execute(
            "INSERT INTO employees (credly_user_id, full_name) VALUES (?, ?)",
            (employee.user_id, employee.full_name)
        )
        row = self.db.fetchone(
            "SELECT id FROM employees WHERE credly_user_id = ?",
            (employee.user_id,)
        )
        return row["id"]

    def get_all(self):
        return self.db.fetchall("SELECT * FROM employees")

    def get_by_credly_id(self, credly_user_id):
        return self.db.fetchone(
            "SELECT * FROM employees WHERE credly_user_id = ?",
            (credly_user_id,)
        )


class CertificationRepository:

    def __init__(self):
        self.db = Database()

    def save(self, employee_id: int, cert: Certification) -> int:
        existing = self.db.fetchone(
            "SELECT id FROM certifications WHERE badge_id = ?",
            (cert.id,)
        )

        if existing:
            self.db.execute("""
                UPDATE certifications SET
                    name = ?, issuer = ?, description = ?,
                    issue_date = ?, expiry_date = ?,
                    badge_url = ?, image_url = ?, source = ?
                WHERE badge_id = ?
            """, (
                cert.name, cert.issuer, cert.description,
                cert.issue_date, cert.expiry_date,
                cert.badge_url, cert.image_url, cert.source,
                cert.id
            ))
            return existing["id"]

        self.db.execute("""
            INSERT INTO certifications
                (badge_id, employee_id, name, issuer, description,
                 issue_date, expiry_date, badge_url, image_url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cert.id, employee_id, cert.name, cert.issuer, cert.description,
            cert.issue_date, cert.expiry_date, cert.badge_url, cert.image_url,
            cert.source
        ))

        row = self.db.fetchone(
            "SELECT id FROM certifications WHERE badge_id = ?",
            (cert.id,)
        )
        return row["id"]

    def get_all(self):
        return self.db.fetchall("SELECT * FROM certifications")

    def get_by_employee(self, employee_id):
        return self.db.fetchall(
            "SELECT * FROM certifications WHERE employee_id = ? ORDER BY issue_date",
            (employee_id,)
        )

    def get_expiring(self, days_ahead: int = 90):
        return self.db.fetchall("""
            SELECT c.*, e.full_name as employee_name
            FROM certifications c
            JOIN employees e ON e.id = c.employee_id
            WHERE c.expiry_date IS NOT NULL
              AND date(c.expiry_date) BETWEEN date('now') AND date('now', ? || ' days')
            ORDER BY c.expiry_date ASC
        """, (f"+{days_ahead}",))


class SkillRepository:

    def __init__(self):
        self.db = Database()

    def save(self, certification_id: int, skill: Skill):
        existing = self.db.fetchone(
            "SELECT id FROM skills WHERE name = ?", (skill.name,)
        )
        if existing:
            skill_id = existing["id"]
        else:
            self.db.execute("INSERT INTO skills(name) VALUES (?)", (skill.name,))
            skill_id = self.db.fetchone(
                "SELECT id FROM skills WHERE name = ?", (skill.name,)
            )["id"]

        relation = self.db.fetchone("""
            SELECT * FROM certification_skills
            WHERE certification_id = ? AND skill_id = ?
        """, (certification_id, skill_id))

        if not relation:
            self.db.execute("""
                INSERT INTO certification_skills (certification_id, skill_id)
                VALUES (?, ?)
            """, (certification_id, skill_id))

        return skill_id

    def get_all(self):
        return self.db.fetchall("SELECT * FROM skills ORDER BY name")

    def get_by_employee(self, employee_id):
        """All skill rows for an employee, WITH duplicates collapsed but a count attached."""
        return self.db.fetchall("""
            SELECT s.name, COUNT(*) as occurrences,
                   GROUP_CONCAT(c.name, ' | ') as certifications
            FROM certification_skills cs
            JOIN skills s ON s.id = cs.skill_id
            JOIN certifications c ON c.id = cs.certification_id
            WHERE c.employee_id = ?
            GROUP BY s.name
            ORDER BY occurrences DESC, s.name ASC
        """, (employee_id,))


class ReminderRepository:

    def __init__(self):
        self.db = Database()

    def save(self, employee_id, certification_id, reminder_type, message, scheduled_for):
        self.db.execute("""
            INSERT INTO reminders
                (employee_id, certification_id, reminder_type, message, scheduled_for)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, certification_id, reminder_type, message, scheduled_for))

    def get_pending(self):
        return self.db.fetchall("""
            SELECT r.*, e.full_name as employee_name, c.name as cert_name
            FROM reminders r
            JOIN employees e ON e.id = r.employee_id
            LEFT JOIN certifications c ON c.id = r.certification_id
            WHERE r.status = 'pending' AND r.scheduled_for <= datetime('now')
            ORDER BY r.scheduled_for
        """)

    def mark_sent(self, reminder_id):
        self.db.execute(
            "UPDATE reminders SET status = 'sent', sent_at = datetime('now') WHERE id = ?",
            (reminder_id,)
        )
