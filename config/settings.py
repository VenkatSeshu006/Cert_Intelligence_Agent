import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")
    USERNAME = os.getenv("USERNAME")
    USER_ID = os.getenv("USER_ID")
    APP_NAME = "Certificate Intelligence Platform"