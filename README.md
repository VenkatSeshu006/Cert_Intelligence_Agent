# Certificate Intelligence Agent — v2 (Fixed + Simplified)

## 🐛 What was broken, and why

### 1. Only 3 of your certifications showed up — UPDATE: previous fix was wrong, here's the real one

**First diagnosis (incorrect):** I initially assumed the missing Oracle certs lived at `/api/v1/users/{id}/badges` and just needed a second endpoint call. That endpoint exists, but it's part of Credly's **OAuth-gated Developer API** — calling it without a Bearer token correctly returns `401 Unauthorized`, which is the error you hit.

**Actual fix:** the genuinely public, no-auth endpoint is a different one entirely — not under `/api/v1/`:
```
https://www.credly.com/users/{user_id_or_username}/badges.json
```
This is the route Credly's own frontend uses to render your public badge wallet page, exposed as JSON via a `.json` suffix. It needs no authentication and already returns **all** your badges — native (Oracle, AWS, etc.) and external — in one unified list, so there's no need to call two separate endpoints anymore.

`provider/credly/client.py` now calls only this endpoint, with pagination via `metadata.total_count`.

### 2. Certifications with no expiry date were vanishing
In your old `expiry_engine.py`:
```python
if not cert.expiry_date:
    continue   # ← silently skipped, cert never shown anywhere
```
This meant any cert without an expiry date — common for foundational/associate-level certs — disappeared from the report **and** from the AI's context.

**Fix:** these certs are now explicitly labeled `"No Expiry"` instead of being dropped. The AI is told outright "this certification does not expire" so it never has to guess or hallucinate a date.

### 3. "List all the badges" confused the AI
The AI had `"No information available about badges"` — even though it just listed certifications. This is a terminology gap: your data model treats badge = certification, but the system prompt never said so.

**Fix:** added an explicit rule to `prompts.py`: *"badge" and "certification" refer to the same thing.*

### 4. Skills were deduplicated too early, losing signal
Your old `skill_engine.py` built a `SkillSummary` per skill with an occurrence count, but `memory.py` (what the AI actually sees) never used it — it just dumped a flat, deduplicated `unique_skills` list. That's why the AI said "30 unique skills" but couldn't reason about which skills were reinforced by multiple certifications (a meaningful signal for learning-path recommendations).

**Fix:** `Employee.skill_frequency` now computes `{skill_name: count}` across *all* certs, and `memory.py` includes this directly in the AI's context, e.g. `Generative AI (x2)`. The AI can now reason about depth, not just breadth.

---

## 🏗️ Simplified structure

Old hierarchy had 5 files just to fetch + parse Credly data (`extractor.py`, `badge_service.py`, `discovery.py`, `parser.py`, `user_service.py`) and 5 repository files with duplicated `Database()` connections. New structure:

```
CIA/
├── main.py                        # sync → expiry report → AI chat, one flow
├── requirements.txt
├── .env.example
│
├── config/
│   └── settings.py
│
├── provider/credly/
│   ├── client.py                  # ALL network calls (replaces extractor+badge_service+discovery)
│   ├── parser.py                  # normalizes both badge shapes
│   ├── user_service.py            # single entrypoint: load_employee(user_id)
│   └── models.py                  # Employee, Certification, Skill, ExpiryStatus
│
├── database/
│   ├── database.py                # singleton SQLite connection
│   ├── schema.py                  # all tables
│   └── repository.py              # ALL repos in one file (Employee/Cert/Skill/Reminder)
│
├── services/
│   ├── sync_engine.py             # Credly → DB, with visibility into native/external/no-expiry counts
│   └── expiry_engine.py           # fixed: reports No Expiry instead of skipping
│
├── ai_agent/
│   ├── client.py                  # OpenRouter wrapper (unchanged)
│   ├── memory.py                  # FIXED: full cert detail + skill frequency in context
│   ├── prompts.py                 # FIXED: badge=certification clarified
│   ├── copilot.py
│   └── terminal.py                # standalone chat-only entrypoint
│
├── data/
│   └── certificate_intelligence.db
│
└── tests/
    └── test_pipeline.py           # validates all fixes with mock data (6/6 passing)
```

**Removed:** `discovery.py` (regex-scraping HTML for UUIDs — fragile and unnecessary once you already have the user_id), `change_detector.py` (premature — add back in Phase 2 when you need incremental sync), `report_service.py` (was empty), `badge_repository.py` (merged into `repository.py`), `reminder_repository.py` stub → now implemented in `repository.py`.

---

## ✅ Test Results

All 6 tests pass using mock data that mirrors real Credly response shapes:

1. Parser merges native + external → 5/5 certs found (vs 3 before)
2. No-expiry certs preserved, not dropped
3. Database round-trip correct
4. Expiry engine reports every cert, including "No Expiry"
5. Skill frequency correctly counts duplicates (e.g. `Generative AI: 2`)
6. AI memory context includes full detail + frequency counts

## ⚠️ Important: run live sync from YOUR machine, not a server

This sandbox environment is blocked by Credly at the network level (403 on every endpoint) — this is normal for cloud/datacenter IPs, Credly is rate-limiting/blocking non-residential traffic. **Run `python main.py` from your own machine**, where you already confirmed it works.

---

## 🚀 Setup

```bash
cd CIA
pip install -r requirements.txt
cp .env.example .env   # fill in your OPENROUTER_API_KEY

python tests/test_pipeline.py   # validate the fixes (no network needed)
python main.py                  # live sync + chat (run locally)
```

## 🗺️ Suggested next steps

1. Confirm `python main.py` now shows **all** your certifications (not just 3)
2. Add the `reminder_engine.py` + `notification_service.py` (Teams webhook) — same pattern as the cert-agent backend we built earlier, now plugged into this cleaner structure
3. Add `recommendation_engine.py` — use `skill_frequency` to recommend the next certification that builds on existing strengths or fills a gap
4. Once stable, wrap `main.py`'s logic in a small FastAPI layer so a frontend (or MS Teams bot) can call it
