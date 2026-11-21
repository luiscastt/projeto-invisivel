"""Clearly isolated sample scenarios. No demonstration record is a real allegation."""
from sqlalchemy import select
from .models import User, Issue, Report
from .security import hash_password
from .db import uid, now
from .moderation import record_update


def bootstrap(db, settings):
    if settings.app_env == "development" and settings.auth_provider == "local":
        for email, name, role in [("admin@invisivel.local", "Equipe de moderação (teste local)", "admin"), ("cidadao@invisivel.local", "Cidadão de teste", "citizen")]:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, display_name=name, password_hash=hash_password("Invisivel!2026"), role=role))
        db.flush()
    if not settings.seed_demo or settings.app_env != "development" or db.scalar(select(Issue.id).where(Issue.is_demo == True)):
        return
    author = db.scalar(select(User).where(User.email == "cidadao@invisivel.local"))
    admin = db.scalar(select(User).where(User.email == "admin@invisivel.local"))
    if not author or not admin:
        return
    examples = [
        ("Iluminação na travessia de pedestres", "infrastructure", "3205002", -20.2044, -40.2676),
        ("Drenagem em trecho de via urbana", "sanitation", "3205002", -20.2257, -40.2785),
        ("Acessibilidade em ponto de ônibus", "mobility", "3205002", -20.1886, -40.2529),
        ("Pavimento em trecho de circulação", "infrastructure", "3205002", -20.1590, -40.2740),
        ("Iluminação em área de circulação", "infrastructure", "3205309", -20.2976, -40.2920),
        ("Travessia e acessibilidade urbana", "mobility", "3205309", -20.3047, -40.3094),
    ]
    for title, category, code, lat, lng in examples:
        description = "CENÁRIO FICTÍCIO PARA DEMONSTRAÇÃO. Este registro ilustra o fluxo de participação e não descreve um problema confirmado neste local. As coordenadas servem apenas para testar a visualização no mapa."
        issue = Issue(title=title + " (demonstração)", summary=description, category=category, municipality_code=code, neighborhood="", latitude=lat, longitude=lng, is_demo=True, sources=[])
        db.add(issue)
        db.flush()
        report = Report(author_id=author.id, issue_id=issue.id, tracking_code="DEMO-" + uid()[:8].upper(), moderation_status="approved", reason="Cenário fictício isolado para testes locais.", payload={"title": issue.title, "description": description, "category": category, "municipality_code": code, "state_code": "32", "latitude": lat, "longitude": lng, "neighborhood": "", "anonymous": True, "is_demo": True, "sources": [], "evidence_ids": []}, flags=[])
        db.add(report)
        db.flush()
        record_update(db, issue, admin.id, "published", "Cenário fictício para exploração local.", "Registro ilustrativo de demonstração, sem caráter factual.", report.id, initial=True)
