import re
import time
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.api.dependencies.auth import CurrentUser
from app.db.mongodb import get_database
from app.core.logging import get_logger

router = APIRouter(prefix="/search", tags=["search"])
logger = get_logger(__name__)

EXCLUDE_WORDS = {
    "the", "and", "for", "with", "from", "that", "this", "show", "find", "get",
    "report", "reports", "findings", "case", "cases", "patient", "patients",
    "all", "any", "are", "has", "have", "chest", "xray", "scan",
}


class SearchRequest(BaseModel):
    query: str
    k: int = 10
    severity_filter: Optional[str] = None
    min_score: float = 0.30


class SearchResult(BaseModel):
    report_id: str
    patient_id: Optional[str] = None
    report_type: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[float] = None
    summary: Optional[str] = None
    findings_count: int = 0
    has_critical_findings: bool = False
    created_at: Optional[str] = None
    institution: Optional[str] = None
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str
    inference_ms: float
    index_ready: bool
    index_size: Optional[int] = None
    cache_hit_rate_pct: Optional[float] = None


async def _mongo_search(
    query: str,
    k: int = 10,
    severity_filter: Optional[str] = None,
) -> tuple[list[dict], float]:
    start = time.monotonic()
    db = get_database()

    words = [
        w.strip().lower()
        for w in re.split(r"[\s,]+", query)
        if len(w.strip()) > 2 and w.strip().lower() not in EXCLUDE_WORDS
    ]

    word_conditions: list[dict] = []
    if words:
        for word in words:
            word_conditions.append({
                "$or": [
                    {"tags": {"$regex": word, "$options": "i"}},
                    {"ai_summary": {"$regex": word, "$options": "i"}},
                    {"severity": {"$regex": word, "$options": "i"}},
                    {"patient_id": {"$regex": word, "$options": "i"}},
                ]
            })

    mongo_query: dict = {"$or": word_conditions} if word_conditions else {}
    if severity_filter:
        mongo_query["severity"] = severity_filter

    projection = {"raw_text": 0, "cleaned_text": 0}
    cursor = db["reports"].find(mongo_query, projection).sort("created_at", -1).limit(k)
    docs = await cursor.to_list(k)

    results = []
    for d in docs:
        tags = [t.lower() for t in d.get("tags", [])]
        findings = (d.get("findings") or d.get("ai_summary") or "").lower()
        severity_val = (d.get("severity") or "").lower()

        ai_summary_val = (d.get("ai_summary") or "").lower()
        matched = 0
        for word in words:
            if any(word in t for t in tags):
                matched += 2
            if word in findings or word in ai_summary_val:
                matched += 1
            if word in severity_val:
                matched += 1

        score = min(1.0, matched / max(len(words) * 2, 1)) if words else 0.5

        created = d.get("created_at")
        results.append({
            "report_id": d.get("report_id") or str(d["_id"]),
            "patient_id": d.get("patient_id"),
            "report_type": d.get("report_type", "chest_xray"),
            "severity": d.get("severity"),
            "risk_score": d.get("risk_score"),
            "summary": d.get("findings") or d.get("ai_summary") or "No summary available.",
            "findings_count": d.get("findings_count", 0),
            "has_critical_findings": d.get("has_critical_findings", False),
            "created_at": created.isoformat() if created else None,
            "institution": d.get("institution"),
            "score": round(score, 4),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    elapsed = (time.monotonic() - start) * 1000
    return results, elapsed


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest, current_user: CurrentUser):
    results, inference_ms = await _mongo_search(
        request.query, k=request.k, severity_filter=request.severity_filter
    )
    return SearchResponse(
        results=results,
        total=len(results),
        query=request.query,
        inference_ms=inference_ms,
        index_ready=True,
        index_size=None,
        cache_hit_rate_pct=None,
    )


@router.post("/index/rebuild", status_code=202)
async def trigger_index_rebuild(current_user: CurrentUser):
    return {"status": "ok", "message": "Using MongoDB search — no index rebuild needed."}


@router.get("/stats")
async def search_stats(current_user: CurrentUser):
    db = get_database()
    count = await db["reports"].count_documents({})
    return {
        "index_ready": True,
        "index_size": count,
        "backend": "mongodb",
    }
