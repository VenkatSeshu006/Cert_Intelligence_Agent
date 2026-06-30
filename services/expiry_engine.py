from datetime import datetime
from provider.credly.models import ExpiryStatus


class ExpiryEngine:

    def get_status(self, employee):
        today = datetime.today().date()
        results = []

        for cert in employee.certifications:

            if not cert.expiry_date:
                # FIX: previously these were silently skipped (continue).
                # Now they're reported explicitly so the user can see them.
                results.append(
                    ExpiryStatus(
                        certification=cert.name,
                        expiry_date=None,
                        days_remaining=None,
                        status="No Expiry"
                    )
                )
                continue

            expiry = datetime.strptime(cert.expiry_date, "%Y-%m-%d").date()
            remaining = (expiry - today).days

            if remaining < 0:
                status = "Expired"
            elif remaining <= 30:
                status = "Expiring Soon"
            elif remaining <= 90:
                status = "Renew Soon"
            else:
                status = "Healthy"

            results.append(
                ExpiryStatus(
                    certification=cert.name,
                    expiry_date=cert.expiry_date,
                    days_remaining=remaining,
                    status=status
                )
            )

        return results
