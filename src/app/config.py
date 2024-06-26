import os, sqlite3

DEBUG = os.environ.get("DEBUG", "1") == "1"


SOURCE_HOST = os.getenv("SOURCE_HOST", "localhost:8080")
SOURCE_SCHEME = os.getenv("SOURCE_SCHEME", "http")

LOG_PATH = os.getenv("LOG_PATH", "./logs")
LOGDB_PATH = os.getenv("LOGDB_PATH", "logs.sqlite")
DB = sqlite3.connect(LOGDB_PATH)
DB.executescript(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id TEXT PRIMARY KEY,
        log TEXT
    );
    """
)
