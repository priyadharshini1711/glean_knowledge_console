"""
Base Glean API client — handles auth headers and base URL construction.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

COMPANY = os.getenv("GLEAN_COMPANY", "aws-sasandbox-be")
DATASOURCE = os.getenv("GLEAN_DATASOURCE", "interviewds")
INDEXING_TOKEN = os.getenv("GLEAN_INDEXING_TOKEN", "")
CLIENT_TOKEN = os.getenv("GLEAN_CLIENT_TOKEN", "")
DOCUMENT_BASE_URL = os.getenv("GLEAN_DOCUMENT_BASE_URL", "https://www.example.com/docs")

BACKEND_URL = f"https://{COMPANY}.glean.com"
INDEXING_BASE = f"{BACKEND_URL}/api/index/v1"
CLIENT_BASE = f"{BACKEND_URL}/rest/api/v1"

TIMEOUT = httpx.Timeout(60.0)

print(f"Using Glean API backend: {BACKEND_URL}")


def indexing_headers() -> dict:
    return {
        "Authorization": f"Bearer {INDEXING_TOKEN}",
        "Content-Type": "application/json",
    }


def client_headers() -> dict:
    return {
        "Authorization": f"Bearer {CLIENT_TOKEN}",
        "Content-Type": "application/json",
    }


def get_indexing_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=INDEXING_BASE,
        headers=indexing_headers(),
        timeout=TIMEOUT,
    )


def get_client_api_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=CLIENT_BASE,
        headers=client_headers(),
        timeout=TIMEOUT,
    )
