from .models import Employee, Certification, Skill

class CredlyParser:

    def parse(self, user_id: str, raw: dict) -> Employee:
        employee = None
        records = []

        for badge in raw["native"].get("data", []):
            try:
                emp, cert = self._parse_native(badge)
                if employee is None:
                    employee = emp
                records.append(cert)
            except Exception as e:
                print(f"  Skipping native badge: {e}")

        for badge in raw["external"].get("data", []):
            try:
                emp, cert = self._parse_external(badge)
                if employee is None:
                    employee = emp
                records.append(cert)
            except Exception as e:
                print(f"  Skipping external badge: {e}")

        if employee is None:
            raise ValueError("No employee data found.")

        employee.certifications = records
        return employee

    def _parse_native(self, badge):
        template = badge.get("badge_template", {})
        issuer_obj = template.get("issuer", {})

        emp = Employee(
            user_id=badge.get("user", {}).get("id", ""),
            full_name=badge.get("recipient_name", ""),
            certifications=[]
        )

        cert = Certification(
            id=badge.get("id", ""),
            source="native",
            name=template.get("name", "Unknown"),
            issuer=issuer_obj.get("name", "Unknown"),
            description=template.get("description", ""),
            issue_date=self._date(badge.get("issued_at_date")),
            expiry_date=self._date(badge.get("expires_at_date")),
            badge_url=badge.get("public_url", ""),
            image_url=template.get("image_url", ""),
            skills=[Skill(s["name"]) for s in template.get("skills", [])],
            tags=[t["name"] for t in template.get("tags", [])]
        )
        return emp, cert

    def _parse_external(self, badge):
        ext = badge.get("external_badge", {})

        emp = Employee(
            user_id=badge.get("user_id", ""),
            full_name=ext.get("recipient_name", ""),
            certifications=[]
        )

        cert = Certification(
            id=badge.get("id", ""),
            source="external",
            name=ext.get("badge_name", "Unknown"),
            issuer=ext.get("issuer_name", "Unknown"),
            description=ext.get("badge_description", ""),
            issue_date=self._date(ext.get("issued_at_date")),
            expiry_date=self._date(ext.get("expires_at_date")),
            badge_url=ext.get("badge_url", ""),
            image_url=ext.get("image_url", ""),
            skills=[Skill(s["name"]) for s in ext.get("skills", [])],
            tags=[t["name"] for t in ext.get("tags", [])]
        )
        return emp, cert

    def _date(self, value):
        return str(value)[:10] if value else None