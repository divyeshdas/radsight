import re
from typing import List, Dict, Optional
import numpy as np
from core.model_registry import registry
import structlog

logger = structlog.get_logger(__name__)

CLINICAL_WEIGHT_TERMS = [
    "impression", "finding", "identified", "noted", "consistent with",
    "evidence of", "compatible with", "suggestive of", "demonstrates",
    "reveal", "show", "indicate", "present", "absent", "no acute",
]

IMPRESSION_PATTERN = re.compile(
    r"(?i)IMPRESSION\s*:?\s*(.*?)(?=\n[A-Z]{3,}:|$)",
    re.DOTALL,
)


def _extract_impression(text: str) -> Optional[str]:
    match = IMPRESSION_PATTERN.search(text)
    if match:
        impression = match.group(1).strip()
        impression = re.sub(r"\s+", " ", impression)
        return impression if len(impression) > 10 else None
    return None


def _sentence_split(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def _score_sentence(sentence: str, sentence_idx: int, total: int) -> float:
    score = 0.0
    lower = sentence.lower()

    for term in CLINICAL_WEIGHT_TERMS:
        if term in lower:
            score += 0.15

    position_weight = 1.2 if sentence_idx == 0 else (1.1 if sentence_idx >= total - 2 else 1.0)
    score *= position_weight

    words = sentence.split()
    if 8 <= len(words) <= 35:
        score += 0.1

    if re.search(r"\d+\.?\d*\s*(cm|mm|%)", lower):
        score += 0.1

    return score


def _embedding_based_score(sentences: List[str]) -> List[float]:
    try:
        model = registry.load_sentence_model()
        embeddings = model.encode(sentences, batch_size=16, show_progress_bar=False)

        doc_embedding = np.mean(embeddings, axis=0)
        scores = []
        for emb in embeddings:
            norm = np.linalg.norm(emb) * np.linalg.norm(doc_embedding)
            sim = float(np.dot(emb, doc_embedding) / norm) if norm > 0 else 0.0
            scores.append(sim)
        return scores
    except Exception as e:
        logger.warning("Embedding scoring failed, using heuristic only", error=str(e))
        return [0.5] * len(sentences)


def summarize(
    text: str,
    max_sentences: int = 3,
    use_embeddings: bool = True,
) -> Dict:
    impression = _extract_impression(text)
    if impression and len(impression.split()) >= 8:
        summary = impression[:500]
        return {
            "summary": summary,
            "method": "impression_extraction",
            "sentence_count": 1,
            "compression_ratio": round(len(summary) / max(len(text), 1), 3),
        }

    sentences = _sentence_split(text)
    if not sentences:
        return {
            "summary": text[:300],
            "method": "truncation",
            "sentence_count": 1,
            "compression_ratio": round(300 / max(len(text), 1), 3),
        }

    heuristic_scores = [
        _score_sentence(s, i, len(sentences))
        for i, s in enumerate(sentences)
    ]

    if use_embeddings and len(sentences) > 2:
        emb_scores = _embedding_based_score(sentences)
        final_scores = [h * 0.5 + e * 0.5 for h, e in zip(heuristic_scores, emb_scores)]
    else:
        final_scores = heuristic_scores

    ranked = sorted(
        range(len(sentences)),
        key=lambda i: final_scores[i],
        reverse=True,
    )[:max_sentences]

    selected = [sentences[i] for i in sorted(ranked)]
    summary = " ".join(selected)

    return {
        "summary": summary[:600],
        "method": "extractive",
        "sentence_count": len(selected),
        "compression_ratio": round(len(summary) / max(len(text), 1), 3),
    }


def batch_summarize(texts: List[str], max_sentences: int = 3) -> List[Dict]:
    return [summarize(t, max_sentences=max_sentences) for t in texts]
