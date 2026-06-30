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

        db_path = os.path.join(data_dir, "certificate_intelligence.db")
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def execute(self, query, params=()):
        cur = self.connection.cursor()
        cur.execute(query, params)
        self.connection.commit()
        return cur

    def fetchone(self, query, params=()):
        cur = self.connection.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetchall(self, query, params=()):
        cur = self.connection.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.connection.close()
