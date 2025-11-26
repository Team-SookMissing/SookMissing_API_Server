import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ANALYZER_URL = os.getenv("ANALYZER_URL", "http://localhost:9000/analyze")

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "sookmissing_db")

settings = Settings()