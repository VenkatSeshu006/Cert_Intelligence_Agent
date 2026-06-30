"""
Parses raw Credly badges.json responses into the unified
Employee / Certification / Skill models.

The badges.json endpoint returns a single unified list. Each item is
normally shaped like:

    badge["id"]
    badge["recipient_name"]
    badge["issued_at_date"]
    badge["expires_at_date"]
    badge["public_url"]
    badge["badge_template"]["name"]
    badge["badge_template"]["description"]
    badge["badge_template"]["image_url"]
    badge["badge_template"]["issuer"]["summary"]
    badge["badge_template"]["skills"][n]["name"]

Some accounts also have badges uploaded as external OpenBadges, which can
appear wrapped under an "external_badge" key instead. Both shapes are
handled here so nothing gets silently dropped regardless of which one
a given badge uses.
"""

from .models import Employee, Certification, Skill


class CredlyParser:

    def parse(self, user_id: str, raw_badges: list) -> Employee:
        employee = Employee(user_id=user_id, full_name="")
        certifications = []

        for badge in raw_badges:
            if "external_badge" in badge:
                cert, name = self._parse_external(badge)
            else:
                cert, name = self._parse_native(badge)

            if cert:
                certifications.append(cert)
            if name and not employee.full_name:
                employee.full_name = name

        # Deduplicate by badge id, just in case
        seen_ids = set()
        deduped = []
        for cert in certifications:
            if cert.id not in seen_ids:
                seen_ids.add(cert.id)
                deduped.append(cert)

        employee.certifications = deduped
        return employee

    # ── Native badge shape (badge_template at top level) ────────────────

    def _parse_native(self, badge: dict):
        template = badge.get("badge_template", {}) or {}
        issuer = template.get("issuer", {}) or {}

        recipient_name = badge.get("recipient_name") or badge.get("issued_to") or ""

        cert = Certification(
            id=str(badge.get("id", "")),
            name=template.get("name", "Unknown Certification"),
            issuer=issuer.get("summary", "") or template.get("issuer_org_name", ""),
            description=template.get("description", "") or "",
            issue_date=self._clean_date(badge.get("issued_at_date") or badge.get("issued_at")),
            expiry_date=self._clean_date(badge.get("expires_at_date") or badge.get("expires_at")),
            badge_url=badge.get("public_url", "") or "",
            image_url=template.get("image_url", "") or "",
            skills=[Skill(s.get("name", "")) for s in template.get("skills", []) if s.get("name")],
            source="native",
        )
        return cert, recipient_name

    # ── External (OpenBadge) shape, if it appears ───────────────────────

    def _parse_external(self, badge: dict):
        external = badge.get("external_badge", {}) or {}

        cert = Certification(
            id=str(badge.get("id", "")),
            name=external.get("badge_name", "Unknown Certification"),
            issuer=external.get("issuer_name", "") or "",
            description=external.get("badge_description", "") or "",
            issue_date=self._clean_date(external.get("issued_at_date")),
            expiry_date=self._clean_date(external.get("expires_at_date")),
            badge_url=external.get("badge_url", "") or "",
            image_url=external.get("image_url", "") or "",
            skills=[Skill(s.get("name", "")) for s in external.get("skills", []) if s.get("name")],
            source="external",
        )
        recipient_name = external.get("recipient_name", "")
        return cert, recipient_name

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _clean_date(value):
        """Returns YYYY-MM-DD or None. Missing/empty expiry dates are kept as
        None explicitly, rather than dropping the certification."""
        if not value:
            return None
        return str(value)[:10]
