import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = "37990847-712a-4d68-9f36-bb6f54482d35"
TENANT_ID = "dc1693df-d65a-491e-bced-e17803feaf5e"
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost:8000/auth/callback"
SCOPES = ["User.Read"]