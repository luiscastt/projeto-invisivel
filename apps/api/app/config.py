from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT / ".env"), extra="ignore")
    app_env: str = "development"
    database_url: str = f"sqlite:///{(ROOT / 'data/invisivel.db').as_posix()}"
    data_dir: Path = ROOT / "data"
    official_dir: Path = ROOT / "data/official"
    auth_provider: str = "local"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    portal_transparencia_api_key: str = ""
    admin_emails: str = ""
    public_origin: str = "http://127.0.0.1:5173"
    seed_demo: bool = True
    rate_limit: int = 180
    session_days: int = 7

    def check_production(self):
        if self.app_env == "production":
            if self.auth_provider != "supabase" or not self.supabase_url.startswith("https://") or not self.supabase_anon_key:
                raise RuntimeError("Produção exige Supabase Auth configurado, com e-mail verificado.")
            if not self.database_url.startswith("postgresql"):
                raise RuntimeError("Produção exige PostgreSQL.")
            if not self.public_origin.startswith("https://"):
                raise RuntimeError("Produção exige PUBLIC_ORIGIN HTTPS.")
