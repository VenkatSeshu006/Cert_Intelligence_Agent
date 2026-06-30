import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MODEL = os.getenv("MODEL", "meta-llama/llama-3.3-70b-instruct")
    APP_NAME = "Certificate Intelligence Platform"
    VERSION = "2.0"
