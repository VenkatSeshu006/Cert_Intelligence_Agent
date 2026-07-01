import requests
from typing import Dict

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

    def get_all_badges_raw(self, user_id: str) -> Dict:
        native = self._get_native(user_id)
        external = self._get_external(user_id)
        return {"native": native, "external": external}

    def _get_native(self, username: str):
        url = f"https://www.credly.com/users/{username}/badges.json"
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()

    def _get_external(self, user_id: str):
        url = (
            f"https://www.credly.com/api/v1/users/{user_id}"
            f"/external_badges/open_badges/public"
            f"?page=1&page_size=100"
        )
        try:
            r = self.session.get(url)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  Warning: External badges failed — {e}")
            return {"data": []}