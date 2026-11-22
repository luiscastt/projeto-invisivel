"""Deterministic advisory methods; scores are not a probability of truth."""
import math
import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from difflib import SequenceMatcher


def normalize(text):
    return re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))).strip()


def distance(a, b):
    lat1, lat2 = map(math.radians, [a[0], b[0]])
    dlat = lat2 - lat1
    dlon = math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))


def similarity(a, b):
    if a["municipality_code"] != b["municipality_code"]:
        return {"score": 0, "distance_meters": None, "interpretation": "different_municipality"}
    has_points = all(v is not None for v in [a.get("latitude"), a.get("longitude"), b.get("latitude"), b.get("longitude")])
    meters = distance((a["latitude"], a["longitude"]), (b["latitude"], b["longitude"])) if has_points else None
    text_a, text_b = normalize(a.get("description", a.get("summary", ""))), normalize(b.get("description", b.get("summary", "")))
    words_a, words_b = set(text_a.split()), set(text_b.split())
    overlap = len(words_a & words_b) / max(1, len(words_a | words_b))
    textual = max(overlap, SequenceMatcher(None, text_a, text_b).ratio())
    temporal = .5
    if a.get("created_at") and b.get("created_at"):
        days = abs((datetime.fromisoformat(a["created_at"]) - datetime.fromisoformat(b["created_at"])).total_seconds()) / 86400
        temporal = max(0, 1 - days / 180)
    score = (.4 * max(0, 1 - meters / 750) if meters is not None else 0) + .35 * textual + .15 * (a["category"] == b["category"]) + .1 * temporal
    # Distinct categories are never a strong suggestion, even at the same point.
    if a["category"] != b["category"]:
        score = min(score, .64)
    return {"score": round(score, 4), "distance_meters": round(meters) if meters is not None else None, "interpretation": "strong" if score >= .85 else "review" if score >= .65 else "distinct"}


def detect_flags(text):
    flags = []
    if re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\b(?:\+55\s*)?\(?\d{2}\)?[\s-]*9?\d{4}[\s-]*\d{4}\b", text, re.I):
        flags.append("possible_personal_data")
    if re.search(r"\b(crime|roubo|trafic|corrup|assassin|ameaça|ameaca)", text, re.I):
        flags.append("sensitive_content")
    if len(set(normalize(text).split())) < 5 or len(re.findall(r"https?://", text)) > 4:
        flags.append("possible_spam")
    return flags


def allocate(issues, budget, unit_cost, strategy):
    cents = int((Decimal(budget) * 100).to_integral_value())
    cost = int((Decimal(unit_cost) * 100).to_integral_value())
    if cents < 0 or cost <= 0:
        raise ValueError("Orçamento deve ser não negativo e custo deve ser positivo.")
    if strategy == "reports":
        ordered = sorted(issues, key=lambda i: (-i.get("reports_count", 0), i["id"]))
    elif strategy == "recent":
        ordered = sorted(issues, key=lambda i: (i.get("last_activity_at", ""), i["id"]), reverse=True)
    else:
        ordered = sorted(issues, key=lambda i: (-(i.get("priority", {}).get("score") or 0), i["id"]))
    capacity = cents // cost
    chosen = ordered[:capacity]
    spent = len(chosen) * cost
    return {"capacity": capacity, "selected_count": len(chosen), "spent": spent / 100, "balance": (cents - spent) / 100, "issue_ids": [i["id"] for i in chosen]}
