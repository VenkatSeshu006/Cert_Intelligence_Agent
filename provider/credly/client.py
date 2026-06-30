"""
Single Credly client responsible for ALL network communication.

IMPORTANT FIX (v3):
--------------------
The previous version called `/api/v1/users/{id}/badges` — this looked like
a plausible REST endpoint, but it's actually part of Credly's OAuth-gated
Developer API (see credly.com/docs/oauth). Without a Bearer token it
correctly returns 401 Unauthorized. There is no way to make this endpoint
work without an organization API key.

The endpoint that ACTUALLY works without authentication is a different one,
unrelated to /api/v1/ — it's the route Credly's own frontend uses to render
your public badge wallet page, exposed as JSON via a `.json` suffix:

    https://www.credly.com/users/{user_id_or_username}/badges.json

This is NOT officially documented, but is publicly reachable by design
(no auth required) because it powers the public-facing badge wallet page
itself. It accepts either your Credly username OR your numeric/UUID
user_id interchangeably.

This single endpoint already returns BOTH natively-issued badges (Oracle,
AWS, etc.) AND externally-uploaded OpenBadges in one unified list — so the
previous two-endpoint approach (native vs external) is no longer needed.
"""

import requests
from typing import List


class CredlyClient:

    PAGE_SIZE = 48

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        })

    # ── Public entrypoint ───────────────────────────────────────────────

    def get_all_badges_raw(self, user_id: str) -> List[dict]:
        """
        Fetches every badge for a public Credly profile, across all pages.
        `user_id` can be either the UUID or the username — both work.
        """
        return self._get_all_pages(user_id)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _get_all_pages(self, user_id: str) -> List[dict]:
        all_items: List[dict] = []
        page = 1

        while True:
            url = (
                f"https://www.credly.com/users/{user_id}/badges.json"
                f"?page={page}&page_size={self.PAGE_SIZE}"
            )
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                status = response.status_code
                if status == 403:
                    raise PermissionError(
                        "Credly blocked this request (403). This typically happens "
                        "when calling from a datacenter/cloud IP (Credly blocks those) "
                        "rather than a residential/local connection. Run this script "
                        "from your own machine on your normal home/office network."
                    )
                if status == 404:
                    raise ValueError(
                        f"No public Credly profile found for '{user_id}'. "
                        "Double check the user_id/username and that the profile "
                        "is set to public in Credly privacy settings."
                    )
                raise RuntimeError(f"Credly request failed ({status}): {e}")
            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Network error calling Credly: {e}")

            payload = response.json()
            items = payload.get("data", [])
            all_items.extend(items)

            meta = payload.get("metadata", {})
            total_count = meta.get("total_count", len(items))

            if not items or len(all_items) >= total_count:
                break

            page += 1

        return all_items

    def close(self):
        self.session.close()
