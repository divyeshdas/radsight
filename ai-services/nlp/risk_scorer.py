from typing import Dict, List, Tuple
import numpy as np

DISEASE_BASE_RISK = {
    "pneumothorax": 0.72,
    "tension pneumothorax": 0.95,
    "pulmonary edema": 0.68,
    "pleural effusion": 0.52,
    "pneumonia": 0.60,
    "pulmonary nodule": 0.55,
    "cardiomegaly": 0.48,
    "atelectasis": 0.35,
    "pulmonary infiltrate": 0.58,
    "rib fracture": 0.50,
    "normal": 0.05,
}

SEVERITY_MULTIPLIERS = {
    "mild": 0.5,
    "moderate": 0.75,
    "severe": 1.0,
    "critical": 1.35,
}

ANATOMY_RISK_BOOST = {
    "bilateral": 0.12,
    "mediastinum": 0.10,
    "cardiac silhouette": 0.08,
    "bilateral lungs": 0.12,
    "perihilar": 0.06,
}

CRITICAL_PHRASES = [
    "tension pneumothorax", "massive hemorrhage", "cardiac tamponade",
    "acute respiratory failure", "aortic dissection", "urgent", "immediate",
    "life-threatening",
]

RISK_THRESHOLDS = [
    (0.80, "critical"),
    (0.60, "high"),
    (0.35, "moderate"),
    (0.15, "low"),
    (0.00, "normal"),
]


def _check_critical_phrases(text: str) -> Tuple[bool, List[str]]:
    found = [p for p in CRITICAL_PHRASES if p in text.lower()]
    return bool(found), found


def score_from_entities(entities: List[Dict], text: str = "") -> Dict:
    if not entities:
        return _build_result(0.05, [], text)

    disease_entities = [e for e in entities if e.get("entity_type") == "disease" and not e.get("negated")]
    anatomy_entities = [e for e in entities if e.get("entity_type") == "anatomy"]

    disease_scores = []
    for ent in disease_entities:
        entity_text = ent["entity_text"].lower()
        base_risk = 0.40

        for disease, risk in DISEASE_BASE_RISK.items():
            if disease in entity_text or entity_text in disease:
                base_risk = risk
                break

        confidence = ent.get("confidence", 0.75)
        disease_scores.append(base_risk * confidence)

    anatomy_boost = 0.0
    for ent in anatomy_entities:
        anat_text = ent["entity_text"].lower()
        for anatomy, boost in ANATOMY_RISK_BOOST.items():
            if anatomy in anat_text:
                anatomy_boost = max(anatomy_boost, boost)

    is_critical, critical_found = _check_critical_phrases(text)

    if disease_scores:
        disease_scores_arr = np.array(disease_scores)
        base_score = float(np.max(disease_scores_arr) * 0.6 + np.mean(disease_scores_arr) * 0.4)
        if len(disease_scores) > 1:
            base_score = min(base_score + 0.05 * (len(disease_scores) - 1), 0.95)
    else:
        base_score = 0.10

    final_score = min(base_score + anatomy_boost + (0.15 if is_critical else 0.0), 1.0)

    return _build_result(final_score, critical_found, text, disease_entities)


def score_from_classification(
    classification: str,
    confidence: float,
    entities: List[Dict],
    text: str = "",
) -> Dict:
    class_base = {"normal": 0.08, "abnormal": 0.45, "critical": 0.82}
    class_score = class_base.get(classification, 0.45)

    entity_result = score_from_entities(entities, text)
    entity_score = entity_result["overall_score"]

    blended = class_score * 0.45 + entity_score * 0.45 + confidence * 0.10
    blended = float(np.clip(blended, 0.0, 1.0))

    result = _build_result(blended, entity_result.get("critical_findings", []), text, entities)
    result["component_scores"] = {
        "classification_score": round(class_score, 4),
        "entity_score": round(entity_score, 4),
        "confidence_weight": round(confidence * 0.10, 4),
    }
    return result


def _determine_risk_level(score: float) -> str:
    for threshold, level in RISK_THRESHOLDS:
        if score >= threshold:
            return level
    return "normal"


def _generate_recommendations(risk_level: str, diseases: List[str], critical_found: List[str]) -> List[str]:
    recs = []

    if critical_found:
        recs.append("Immediate clinical evaluation required.")

    level_recs = {
        "critical": ["Urgent radiologist review", "Notify attending physician immediately", "Consider emergency intervention"],
        "high":     ["Priority radiologist review within 1 hour", "Clinical correlation required", "Follow-up imaging recommended"],
        "moderate": ["Radiologist review within 4 hours", "Outpatient follow-up recommended", "Clinical correlation advised"],
        "low":      ["Routine radiologist review", "Follow-up as clinically indicated"],
        "normal":   ["No immediate action required", "Routine follow-up as clinically indicated"],
    }

    recs.extend(level_recs.get(risk_level, []))

    disease_recs = {
        "pneumothorax": "Chest tube placement if tension physiology present.",
        "pulmonary edema": "Echocardiogram and BNP level recommended.",
        "pleural effusion": "Thoracentesis if symptomatic.",
        "pneumonia": "Antibiotic therapy and follow-up imaging in 4-6 weeks.",
        "pulmonary nodule": "CT chest per Fleischner Society guidelines.",
    }

    for disease in diseases:
        for key, rec in disease_recs.items():
            if key in disease.lower():
                recs.append(rec)

    return list(dict.fromkeys(recs))[:5]


def _build_result(
    score: float,
    critical_found: List[str],
    text: str,
    disease_entities: List[Dict] | None = None,
) -> Dict:
    risk_level = _determine_risk_level(score)
    disease_names = [e["entity_text"] for e in (disease_entities or [])]
    recommendations = _generate_recommendations(risk_level, disease_names, critical_found)

    urgency_score = min(score * 1.1, 1.0) if critical_found else score
    complexity_score = min(len(disease_entities or []) * 0.15 + score * 0.5, 1.0)

    return {
        "overall_score": round(float(score), 4),
        "risk_level": risk_level,
        "urgency_score": round(float(urgency_score), 4),
        "complexity_score": round(float(complexity_score), 4),
        "critical_findings": critical_found,
        "recommendations": recommendations,
        "component_scores": {},
        "explainability": {
            "disease_count": len(disease_entities or []),
            "has_critical_phrases": bool(critical_found),
            "score_breakdown": {
                "entity_based": round(float(score), 4),
                "risk_level": risk_level,
            },
        },
    }
