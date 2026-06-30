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
            CREATE TABLE IF NOT EXISTS certifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_id TEXT UNIQUE,
                employee_id INTEGER,
                name TEXT,
                issuer TEXT,
                description TEXT,
                issue_date TEXT,
                expiry_date TEXT,        -- NULL is valid: many certs never expire
                badge_url TEXT,
                image_url TEXT,
                source TEXT DEFAULT 'native',
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS certification_skills (
                certification_id INTEGER,
                skill_id INTEGER,
                PRIMARY KEY (certification_id, skill_id),
                FOREIGN KEY(certification_id) REFERENCES certifications(id),
                FOREIGN KEY(skill_id) REFERENCES skills(id)
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                certification_id INTEGER,
                reminder_type TEXT,         -- expiry_warning | exam_reminder
                message TEXT,
                scheduled_for TEXT,
                sent_at TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY(employee_id) REFERENCES employees(id),
                FOREIGN KEY(certification_id) REFERENCES certifications(id)
            )
        """)

        print("✅ Database schema ready.")
