import time
from typing import Dict, List, Optional
from datetime import datetime, timezone

from nlp.entity_extractor import extract_entities
from nlp.report_classifier import classify_report
from nlp.summarizer import summarize
from nlp.risk_scorer import score_from_classification
from embeddings.sentence_bert import generate_embedding
import structlog

logger = structlog.get_logger(__name__)


async def run_full_pipeline(
    report_id: str,
    text: str,
    use_biobert: bool = True,
    use_embeddings: bool = True,
) -> Dict:
    t_start = time.perf_counter()
    pipeline_log = []

    t0 = time.perf_counter()
    entity_result = extract_entities(text, use_biobert=use_biobert)
    pipeline_log.append({"stage": "ner", "ms": round((time.perf_counter() - t0) * 1000, 2)})

    t0 = time.perf_counter()
    classification_result = classify_report(text, use_model=True)
    pipeline_log.append({"stage": "classification", "ms": round((time.perf_counter() - t0) * 1000, 2)})

    t0 = time.perf_counter()
    summary_result = summarize(text, max_sentences=3, use_embeddings=False)
    pipeline_log.append({"stage": "summarization", "ms": round((time.perf_counter() - t0) * 1000, 2)})

    t0 = time.perf_counter()
    risk_result = score_from_classification(
        classification=classification_result["classification"],
        confidence=classification_result["confidence"],
        entities=entity_result["entities"],
        text=text,
    )
    pipeline_log.append({"stage": "risk_scoring", "ms": round((time.perf_counter() - t0) * 1000, 2)})

    embedding_result = {"embedding": None, "cache_hit": False, "inference_ms": 0.0}
    if use_embeddings:
        t0 = time.perf_counter()
        embed_text = summary_result["summary"] or text[:500]
        embedding_result = await generate_embedding(embed_text)
        pipeline_log.append({"stage": "embedding", "ms": round((time.perf_counter() - t0) * 1000, 2)})

    total_ms = round((time.perf_counter() - t_start) * 1000, 2)

    return {
        "report_id": report_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "classification": classification_result["classification"],
        "classification_confidence": classification_result["confidence"],
        "classification_scores": classification_result["scores"],
        "urgency": classification_result["urgency"],
        "severity": _map_to_severity(risk_result["risk_level"]),
        "risk_score": risk_result["overall_score"],
        "urgency_score": risk_result["urgency_score"],
        "risk_level": risk_result["risk_level"],
        "ai_summary": summary_result["summary"],
        "entities": entity_result["entities"],
        "diseases": entity_result["diseases"],
        "anatomy": entity_result["anatomy"],
        "symptoms": entity_result["symptoms"],
        "findings_count": entity_result["disease_count"],
        "has_critical_findings": bool(risk_result["critical_findings"]),
        "critical_findings": risk_result["critical_findings"],
        "recommendations": risk_result["recommendations"],
        "embedding": embedding_result.get("embedding"),
        "embedding_cache_hit": embedding_result.get("cache_hit", False),
        "risk_explainability": risk_result["explainability"],
        "classification_explainability": classification_result["explainability"],
        "pipeline_stages": pipeline_log,
        "total_inference_ms": total_ms,
    }


async def run_batch_pipeline(
    reports: List[Dict],
    use_biobert: bool = True,
) -> List[Dict]:
    results = []
    for report in reports:
        try:
            result = await run_full_pipeline(
                report_id=report.get("report_id", ""),
                text=report.get("text", ""),
                use_biobert=use_biobert,
                use_embeddings=True,
            )
            results.append(result)
        except Exception as e:
            logger.error("Pipeline failed for report", report_id=report.get("report_id"), error=str(e))
            results.append({
                "report_id": report.get("report_id", ""),
                "error": str(e),
                "total_inference_ms": 0.0,
            })
    return results


def _map_to_severity(risk_level: str) -> str:
    mapping = {
        "normal": "normal",
        "low": "mild",
        "moderate": "moderate",
        "high": "severe",
        "critical": "critical",
    }
    return mapping.get(risk_level, "moderate")
