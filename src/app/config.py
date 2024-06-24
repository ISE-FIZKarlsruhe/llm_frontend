import os

DEBUG = os.environ.get("DEBUG", "1") == "1"


SOURCE_HOST = os.getenv("SOURCE_HOST", "localhost:8080")
SOURCE_SCHEME = os.getenv("SOURCE_SCHEME", "http")
