"""ASGI entrypoint for the root FastAPI service on Vercel."""
import os
from pathlib import Path
import sys

# Preview deployments are public too: never expose the local demo accounts.
if os.environ.get("VERCEL") == "1" and os.environ.get("VERCEL_ENV") != "development":
    if os.environ.get("APP_ENV") != "production":
        raise RuntimeError("Vercel deployments require APP_ENV=production and production credentials.")

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "apps" / "api"))
from app.main import app  # noqa: E402, F401
