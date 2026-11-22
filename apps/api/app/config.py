import base64
import json
import os
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore", hide_input_in_errors=True)
    app_env: str = "development"
    database_url: str = Field(default=f"sqlite:///{(ROOT / 'data/invisivel.db').as_posix()}", repr=False)
    database_schema: str = "invisivel"
    data_dir: Path = ROOT / "data"
    official_dir: Path = ROOT / "data/official"
    auth_provider: str = "local"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_secret_key: str = Field(default="", repr=False)
    storage_provider: str = "local"
    supabase_storage_bucket: str = "invisivel-evidence"
    portal_transparencia_api_key: str = ""
    admin_emails: str = ""
    public_origin: str = Field(default_factory=lambda: (
        "https://" + (os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") if os.environ.get("VERCEL_ENV") == "production" else os.environ.get("VERCEL_URL"))
        if (os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") if os.environ.get("VERCEL_ENV") == "production" else os.environ.get("VERCEL_URL"))
        else "http://127.0.0.1:5173"
    ))
    seed_demo: bool = True
    rate_limit: int = 180
    session_days: int = 7

    @model_validator(mode="after")
    def validate_storage(self):
        if self.supabase_anon_key.startswith("sb_secret_"):
            raise ValueError("Use a chave publishable no campo público de autenticação.")
        if self.supabase_anon_key.startswith("eyJ"):
            try:
                payload = self.supabase_anon_key.split(".")[1]
                role = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["role"]
            except (IndexError, KeyError, ValueError, UnicodeDecodeError):
                raise ValueError("Use uma chave publishable ou anon válida.") from None
            if role != "anon":
                raise ValueError("A configuração pública aceita apenas chave publishable ou anon.")
        if self.storage_provider not in {"local", "supabase"}:
            raise ValueError("STORAGE_PROVIDER deve ser local ou supabase.")
        if self.storage_provider == "supabase" and (not self.supabase_secret_key or not self.supabase_url.startswith("https://")):
            raise ValueError("Storage Supabase exige URL HTTPS e chave secreta no backend.")
        return self

    def check_production(self):
        if self.app_env == "production":
            if self.auth_provider != "supabase" or not self.supabase_url.startswith("https://") or not self.supabase_anon_key:
                raise RuntimeError("Produção exige Supabase Auth configurado, com e-mail verificado.")
            if not self.database_url.startswith("postgresql"):
                raise RuntimeError("Produção exige PostgreSQL.")
            if not self.public_origin.startswith("https://"):
                raise RuntimeError("Produção exige PUBLIC_ORIGIN HTTPS.")
