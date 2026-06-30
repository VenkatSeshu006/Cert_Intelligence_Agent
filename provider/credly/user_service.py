"""
UserService — the single entrypoint for loading an employee's full
Credly profile (native + external badges combined).

Replaces: badge_service.py + user_service.py (collapsed into one).
"""

from .client import CredlyClient
from .parser import CredlyParser


class UserService:

    def __init__(self):
        self.client = CredlyClient()
        self.parser = CredlyParser()

    def load_employee(self, user_id: str):
        raw = self.client.get_all_badges_raw(user_id)
        employee = self.parser.parse(user_id, raw)
        return employee

    def close(self):
        self.client.close()
