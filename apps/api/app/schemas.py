from datetime import date
from decimal import Decimal
from typing import Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, ConfigDict

Category = Literal["infrastructure", "sanitation", "mobility", "education", "health", "environment"]
Status = Literal["reported", "corroborated", "in_progress", "declared_resolved", "verified_resolved", "contested"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(StrictModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        import re
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Informe um e-mail válido.")
        return value.lower()


class Register(Login):
    display_name: str = Field(min_length=2, max_length=80)


class SourceInput(StrictModel):
    title: str = Field(min_length=3, max_length=240)
    url: str = Field(max_length=2048)
    publisher: str = Field(min_length=2, max_length=160)
    source_type: Literal["official", "journalistic", "community"]
    published_at: date | None = None

    @field_validator("source_type")
    @classmethod
    def official_domain(cls, value, info):
        host = urlparse(info.data.get("url", "")).hostname or ""
        if value == "official" and not host.endswith((".gov.br", ".leg.br", ".jus.br", ".mp.br", ".def.br")):
            raise ValueError("Uma fonte oficial deve pertencer a um domínio governamental brasileiro. Classifique outras referências como comunitárias ou jornalísticas.")
        return value

    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        import ipaddress
        if "\\" in value or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("A URL não pode conter barras invertidas, espaços ou caracteres de controle.")
        p = urlparse(value)
        host = (p.hostname or "").lower()
        if p.scheme != "https" or not host or "%" in p.netloc or p.username or p.password or p.port not in (None, 443) or host == "localhost" or host.endswith((".local", ".internal")) or "." not in host:
            raise ValueError("Use uma URL HTTPS pública, sem credenciais.")
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            return value
        if not ip.is_global:
            raise ValueError("Endereços internos não são aceitos.")
        return value


class ReportInput(StrictModel):
    title: str = Field(min_length=8, max_length=180)
    description: str = Field(min_length=20, max_length=6000)
    category: Category
    state_code: str = Field(pattern=r"^\d{2}$")
    municipality_code: str = Field(pattern=r"^\d{7}$")
    neighborhood: str = Field(default="", max_length=160)
    latitude: float = Field(ge=-34, le=6, allow_inf_nan=False)
    longitude: float = Field(ge=-74, le=-28, allow_inf_nan=False)
    occurrence_date: date | None = None
    anonymous: bool = True
    evidence_ids: list[str] = Field(default_factory=list, max_length=5)
    sources: list[SourceInput] = Field(default_factory=list, max_length=5)
    existing_issue_id: str | None = None
    is_demo: bool = False

    @field_validator("occurrence_date")
    @classmethod
    def valid_date(cls, value):
        from zoneinfo import ZoneInfo
        from datetime import datetime
        if value and value > datetime.now(ZoneInfo("America/Sao_Paulo")).date():
            raise ValueError("A data da ocorrência não pode estar no futuro.")
        return value


class VoteInput(StrictModel):
    vote: Literal["RESOLVED", "UNRESOLVED"]


class Reason(StrictModel):
    reason: str = Field(min_length=8, max_length=2000)


class Approval(Reason):
    issue_id: str | None = None


class StatusInput(Reason):
    status: Status


class Restore(Reason):
    version: int = Field(ge=1)


class Merge(Reason):
    target_id: str


class SimulationInput(StrictModel):
    municipality_code: str = Field(pattern=r"^\d{7}$")
    category: Category
    budget: Decimal = Field(ge=0, le=100000000000, decimal_places=2, allow_inf_nan=False)
    unit_cost: Decimal = Field(gt=0, le=1000000000, decimal_places=2, allow_inf_nan=False)
    strategy: Literal["priority", "recent", "reports"] = "priority"
    demo: bool = False


class DeleteAccount(StrictModel):
    password: str | None = None


class Clarification(StrictModel):
    description: str = Field(min_length=20, max_length=3000)
