from datetime import datetime, date
from database.repository import ReminderRepository, CertificationRepository

THRESHOLDS = [90, 30, 7]

class ReminderEngine:

    def __init__(self):
        self.reminder_repo = ReminderRepository()
        self.cert_repo = CertificationRepository()

    def run(self, employee, employee_id):
        today = date.today()
        reminders_created = 0

        for cert in employee.certifications:

            if not cert.expiry_date:
                continue

            expiry = datetime.strptime(cert.expiry_date, "%Y-%m-%d").date()
            days_remaining = (expiry - today).days

            # Get the DB id for this cert
            db_cert = self.cert_repo.get_by_badge_id(cert.id)
            if not db_cert:
                continue
            cert_id = db_cert["id"]

            for threshold in THRESHOLDS:
                if 0 <= days_remaining <= threshold:
                    reminder_type = f"{threshold}_day"
                    message = (
                        f"⚠️ {cert.name} expires in {days_remaining} day(s) "
                        f"(on {cert.expiry_date}). Please renew soon."
                    )
                    self.reminder_repo.save(
                        employee_id=employee_id,
                        certification_id=cert_id,
                        reminder_type=reminder_type,
                        message=message,
                        scheduled_for=str(today)
                    )
                    reminders_created += 1

        return reminders_created