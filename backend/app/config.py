import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _normalize_database_url(url: str) -> str:
    if not url or "://" not in url or "@" not in url:
        return url

    scheme, rest = url.split("://", 1)
    credentials, host_and_database = rest.rsplit("@", 1)

    if ":" not in credentials:
        return url

    username, password = credentials.split(":", 1)
    return (
        f"{scheme}://{quote(username, safe='')}:"
        f"{quote(password, safe='')}@{host_and_database}"
    )

CLIENT_ID = "37990847-712a-4d68-9f36-bb6f54482d35"
TENANT_ID = "dc1693df-d65a-491e-bced-e17803feaf5e"
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
DATABASE_URL = _normalize_database_url(os.environ.get("DATABASE_URL", ""))
DATABASE_SCHEMA = os.environ.get("DATABASE_SCHEMA", "gadm")
AUTO_CREATE_DATABASE_OBJECTS = (
    os.environ.get("AUTO_CREATE_DATABASE_OBJECTS", "false").lower() == "true"
)

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost:8000/auth/callback"
SCOPES = ["User.Read"]
