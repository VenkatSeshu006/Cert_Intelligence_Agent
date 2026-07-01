# Project Documentation

## Overview
This document provides an overview of all the scripts used in the Cert Intelligence Agent project.

## Scripts

### 1. `main.py`
- **Description**: The main entry point of the application.
- **Usage**: This script initializes the application and starts the execution.

### 2. `ai_agent/__init__.py`
- **Description**: Initializes the `ai_agent` package.

### 3. `ai_agent/client.py`
- **Description**: Contains the client logic for interacting with external services.

### 4. `ai_agent/copilot.py`
- **Description**: Manages the interaction with the AI copilot functionalities.

### 5. `ai_agent/memory.py`
- **Description**: Handles memory management for the AI agent.

### 6. `ai_agent/prompts.py`
- **Description**: Contains predefined prompts for the AI agent.

### 7. `ai_agent/terminal.py`
- **Description**: Manages terminal interactions for the AI agent.

### 8. `config/__init__.py`
- **Description**: Initializes the `config` package.

### 9. `config/settings.py`
- **Description**: Contains configuration settings for the application.

### 10. `data/`
- **Description**: Directory for data-related scripts and resources.

### 11. `database/__init__.py`
- **Description**: Initializes the `database` package.

### 12. `database/database.py`
- **Description**: Contains database connection and management logic.

### 13. `database/repository.py`
- **Description**: Manages data repositories and interactions.

### 14. `database/schema.py`
- **Description**: Defines the database schema.

### 15. `provider/__init__.py`
- **Description**: Initializes the `provider` package.

### 16. `provider/credly/__init__.py`
- **Description**: Initializes the `credly` provider package.

### 17. `provider/credly/client.py`
- **Description**: Client logic for interacting with the Credly API.

### 18. `provider/credly/models.py`
- **Description**: Defines data models for the Credly API.

### 19. `provider/credly/parser.py`
- **Description**: Contains logic for parsing responses from the Credly API.

### 20. `provider/credly/user_service.py`
- **Description**: Manages user-related services for the Credly API.

### 21. `services/__init__.py`
- **Description**: Initializes the `services` package.

### 22. `services/expiry_engine.py`
- **Description**: Manages expiry logic for credentials or tokens.

### 23. `services/sync_engine.py`
- **Description**: Handles synchronization tasks within the application.

### 24. `tests/test_pipeline.py`
- **Description**: Contains tests for the pipeline functionality.

### 25. `tests/test_pulling.py`
- **Description**: Contains tests for the pulling functionality.

### Code Snippets

#### 1. `main.py`
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from database.schema import Schema
from services.sync_engine import SyncEngine
from services.expiry_engine import ExpiryEngine
from ai_agent.copilot import Copilot

USER_ID = "38056054-049b-4ad2-8929-82dc0ca985d0"

def print_expiry_report(employee):
    engine = ExpiryEngine()
    statuses = engine.get_status(employee)

    print()
    print("-" * 60)
    print("CERTIFICATION EXPIRY STATUS")
    print("-" * 60)
```

#### 2. `ai_agent/__init__.py`
```python

```

#### 3. `ai_agent/client.py`
```python
from google import genai
from config.settings import Settings

class GeminiClient:

    def __init__(self):
        self.client = genai.Client(api_key=Settings.GEMINI_API_KEY)

    def ask(self, system_prompt, user_prompt):
        response = self.client.models.generate_content(
            model=Settings.MODEL,
            contents=f"{system_prompt}\n\n{user_prompt}"
        )
        return response.text
```

#### 4. `ai_agent/copilot.py`
```python
from ai_agent.client import GeminiClient
from ai_agent.memory import Memory
from ai_agent.prompts import SYSTEM_PROMPT

class Copilot:

    def __init__(self, employee):
        self.client = GeminiClient()
        self.memory = Memory()
        self.memory.load_employee(employee)

    def chat(self, question):
        self.memory.add_user_message(question)
        prompt = self.memory.build_prompt(question)
        answer = self.client.ask(SYSTEM_PROMPT, prompt)
        self.memory.add_ai_message(answer)
        return answer

    def show_context(self):
```

#### 5. `ai_agent/memory.py`
```python
from datetime import datetime

class Memory:

    def __init__(self):
        self.employee_context = ""
        self.chat_history = []
        self.created_at = datetime.now()

    def load_employee(self, employee):
        """
        Builds the full context string given to the AI.

        FIX vs original: previously this only ever saw whatever certifications
        happened to be in employee.certifications — which was incomplete because
        the sync only pulled from one Credly endpoint. Now that UserService pulls
        BOTH native + external badges, this naturally sees everything.

        FIX 2: skill listing now shows occurrence count (how many certs cover
```

#### 6. `ai_agent/prompts.py`
```python
SYSTEM_PROMPT = """
You are Certificate Intelligence Copilot.

You help employees understand their certifications, skills,
certification status, and professional development.

Rules:

1. ONLY answer using the supplied employee context.

2. Never invent certifications or badges. In this system,
   "certification" and "badge" refer to the SAME thing — if asked
   about "badges", answer using the certifications listed in the context.

3. Never invent skills.

4. Never assume expiry dates. If a certification has no expiry date,
   say explicitly that it does not expire — do not guess or omit it.

5. If information is unavailable, say so honestly.
"""
```

#### 7. `ai_agent/terminal.py`
```python
from provider.credly.user_service import UserService
from ai_agent.copilot import Copilot

def print_banner():
    print()
    print("=" * 60)
    print("      CERTIFICATE INTELLIGENCE COPILOT")
    print("=" * 60)
    print()

def print_employee(employee):
    print(f"Employee         : {employee.full_name}")
    print(f"Certifications   : {len(employee.certifications)}")
    print(f"  - Native       : {sum(1 for c in employee.certifications if c.source == 'native')}")
    print(f"  - External     : {sum(1 for c in employee.certifications if c.source == 'external')}")
    print(f"Unique Skills    : {len(employee.unique_skills)}")
    no_expiry = sum(1 for c in employee.certifications if not c.expiry_date)
    if no_expiry:
```

#### 8. `config/__init__.py`
```python

```

#### 9. `config/settings.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")
    APP_NAME = "Certificate Intelligence Platform"
```

#### 10. `database/__init__.py`
```python

```

#### 11. `database/database.py`
```python
import sqlite3
import os

class Database:

    _instance = None

    def __new__(cls):
        """Singleton — avoid opening a new SQLite connection per repository."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
```

#### 12. `database/repository.py`
```python
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
```

#### 13. `database/schema.py`
```python
from .database import Database

class Schema:

    def __init__(self):
        self.db = Database()

    def create_tables(self):

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credly_user_id TEXT UNIQUE,
                full_name TEXT,
                synced_at TEXT DEFAULT (datetime('now'))
            )
        """)

        self.db.execute("""
```

#### 14. `provider/__init__.py`
```python

```

#### 15. `provider/credly/__init__.py`
```python

```

#### 16. `provider/credly/client.py`
```python
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
```

#### 17. `provider/credly/models.py`
```python
"""
Core data models for the Certificate Intelligence Agent.
These are plain dataclasses — no framework dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Skill:
    name: str

@dataclass
class Certification:
    id: str
    name: str
    issuer: str
    description: str
```

#### 18. `provider/credly/parser.py`
```python
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
"""
```

#### 19. `provider/credly/user_service.py`
```python
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
```

#### 20. `services/__init__.py`
```python

```

#### 21. `services/expiry_engine.py`
```python
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
```

#### 22. `services/sync_engine.py`
```python
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
```

#### 23. `tests/test_pipeline.py`
```python
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

```

#### 24. `tests/test_pulling.py`
```python
import requests

USER_ID = "38056054-049b-4ad2-8929-82dc0ca985d0"
url = f"https://www.credly.com/api/v1/users/{USER_ID}/external_badges/open_badges/public?page=1&page_size=48"

r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
print(r.status_code)
print(r.text[:500])
```

## Conclusion
This document serves as a comprehensive overview of the scripts utilized in the Cert Intelligence Agent project. Each script is designed to fulfill specific functionalities, contributing to the overall operation of the application.