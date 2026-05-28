import re
import time
import torch
import torch.nn.functional as F
from typing import Dict, List, Tuple
from core.model_registry import registry
import structlog

logger = structlog.get_logger(__name__)

LABELS = ["normal", "abnormal", "critical"]

CRITICAL_KEYWORDS = [
    "tension pneumothorax", "massive hemorrhage", "acute respiratory failure",
    "critical", "life-threatening", "immediate", "urgent intervention",
    "cardiac tamponade", "massive pulmonary embolism", "aortic dissection",
]

ABNORMAL_KEYWORDS = [
    "pneumonia", "effusion", "edema", "consolidation", "infiltrate",
    "cardiomegaly", "atelectasis", "nodule", "mass", "fracture",
    "opacity", "fibrosis", "emphysema", "pneumothorax", "lesion",
]

NORMAL_KEYWORDS = [
    "no acute", "clear", "unremarkable", "within normal limits",
    "no evidence", "no focal", "normal", "no pneumothorax",
    "no effusion", "no infiltrate",
]


def _rule_based_classify(text: str) -> Tuple[str, float, Dict[str, float]]:
    text_lower = text.lower()

    critical_score = sum(1 for kw in CRITICAL_KEYWORDS if kw in text_lower)
    abnormal_score = sum(1 for kw in ABNORMAL_KEYWORDS if kw in text_lower)
    normal_score = sum(1 for kw in NORMAL_KEYWORDS if kw in text_lower)

    if critical_score >= 1:
        confidence = min(0.75 + critical_score * 0.05, 0.95)
        return "critical", confidence, {"normal": 0.05, "abnormal": 0.15, "critical": confidence}

    if abnormal_score > normal_score:
        ratio = abnormal_score / max(abnormal_score + normal_score, 1)
        confidence = min(0.60 + ratio * 0.25, 0.90)
        return "abnormal", confidence, {"normal": 1 - confidence, "abnormal": confidence, "critical": 0.05}

    if normal_score > 0:
        confidence = min(0.65 + normal_score * 0.05, 0.92)
        return "normal", confidence, {"normal": confidence, "abnormal": 1 - confidence, "critical": 0.02}

    return "abnormal", 0.55, {"normal": 0.30, "abnormal": 0.55, "critical": 0.15}


def _model_based_classify(text: str) -> Tuple[str, float, Dict[str, float]]:
    tokenizer, model = registry.load_clinicalbert()

    truncated = " ".join(text.split()[:400])
    inputs = tokenizer(
        truncated,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=-1).squeeze()
    prob_list = probs.tolist()

    if len(prob_list) != 3:
        prob_list = [prob_list[0] if prob_list else 0.33] * 3

    scores = {label: round(float(p), 4) for label, p in zip(LABELS, prob_list)}
    pred_label = max(scores, key=scores.get)
    confidence = scores[pred_label]

    return pred_label, confidence, scores


def classify_report(text: str, use_model: bool = True) -> Dict:
    t0 = time.perf_counter()

    rule_label, rule_conf, rule_scores = _rule_based_classify(text)

    if use_model and len(text.split()) >= 15:
        try:
            model_label, model_conf, model_scores = _model_based_classify(text)
            if model_conf > 0.70:
                final_label = model_label
                final_conf = model_conf * 0.6 + rule_conf * 0.4
                blended = {
                    k: round(model_scores[k] * 0.6 + rule_scores.get(k, 0) * 0.4, 4)
                    for k in LABELS
                }
            else:
                final_label = rule_label
                final_conf = rule_conf
                blended = rule_scores
        except Exception as e:
            logger.warning("Model classification failed, using rule-based", error=str(e))
            final_label = rule_label
            final_conf = rule_conf
            blended = rule_scores
    else:
        final_label = rule_label
        final_conf = rule_conf
        blended = rule_scores

    elapsed_ms = (time.perf_counter() - t0) * 1000

    urgency_map = {"normal": "routine", "abnormal": "standard", "critical": "urgent"}

    return {
        "classification": final_label,
        "confidence": round(final_conf, 4),
        "scores": blended,
        "urgency": urgency_map[final_label],
        "inference_ms": round(elapsed_ms, 2),
        "explainability": {
            "rule_label": rule_label,
            "rule_confidence": round(rule_conf, 4),
            "critical_keywords_found": [kw for kw in CRITICAL_KEYWORDS if kw in text.lower()],
            "abnormal_keywords_found": [kw for kw in ABNORMAL_KEYWORDS if kw in text.lower()][:5],
        },
    }


def classify_batch(texts: List[str]) -> List[Dict]:
    return [classify_report(text) for text in texts]
