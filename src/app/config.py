import os, sqlite3

DEBUG = os.environ.get("DEBUG", "1") == "1"

SECRET_KEY = os.getenv("SECRET_KEY")

SOURCE_HOST = os.getenv("SOURCE_HOST", "localhost:8080")
SOURCE_SCHEME = os.getenv("SOURCE_SCHEME", "http")

LOG_PATH = os.getenv("LOG_PATH", "./logs")
LOGDB_PATH = os.getenv("LOGDB_PATH", "logs.sqlite")
LOGDB = sqlite3.connect(LOGDB_PATH)
LOGDB.executescript(
    """
    CREATE TABLE IF NOT EXISTS logs (
        id TEXT PRIMARY KEY,
        log TEXT
    );
    """
)

ADMINDB_PATH = os.getenv("ADMINDB_PATH", "admin.sqlite")
ADMINDB = sqlite3.connect(ADMINDB_PATH)
ADMINDB.executescript(
    """
    CREATE TABLE IF NOT EXISTS users (
        email TEXT,
        username TEXT,
        password TEXT,
        disabled BOOLEAN
    );
    CREATE UNIQUE INDEX IF NOT EXISTS users_email_uindex ON users (email);
    CREATE TABLE IF NOT EXISTS tokens (user TEXT, token TEXT);
    PRAGMA journal_mode = WAL;
"""
)
