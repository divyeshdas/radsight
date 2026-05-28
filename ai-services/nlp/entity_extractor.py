import re
import time
from typing import List, Dict, Optional
from core.model_registry import registry
import structlog

logger = structlog.get_logger(__name__)

MEDICAL_KEYWORDS = {
    "disease": [
        "pneumonia", "edema", "effusion", "atelectasis", "pneumothorax",
        "cardiomegaly", "infiltrate", "consolidation", "nodule", "lesion",
        "mass", "fracture", "opacity", "fibrosis", "emphysema", "bronchitis",
    ],
    "severity": [
        "mild", "moderate", "severe", "critical", "minimal", "trace",
        "small", "large", "massive", "extensive", "bilateral",
    ],
    "anatomy": [
        "lung", "lobe", "pleura", "mediastinum", "heart", "rib", "trachea",
        "bronchus", "diaphragm", "costophrenic", "perihilar", "hilar",
        "right upper lobe", "right lower lobe", "left upper lobe", "left lower lobe",
        "right middle lobe", "bilateral", "apical", "basal",
    ],
    "negation": [
        "no", "without", "absent", "negative", "unremarkable",
        "not identified", "not seen", "not detected", "clear",
    ],
}

ENTITY_LABEL_MAP = {
    "DISEASE": "disease",
    "DIS": "disease",
    "B-Disease": "disease",
    "I-Disease": "disease",
    "CHEMICAL": "medication",
    "CHEM": "medication",
    "B-Chemical": "medication",
    "ANATOMY": "anatomy",
    "B-Anatomy": "anatomy",
    "SYMPTOM": "symptom",
    "SIGN_SYMPTOM": "symptom",
}


def _is_negated(text: str, entity_start: int, window: int = 60) -> bool:
    preceding = text[max(0, entity_start - window):entity_start].lower()
    for neg in MEDICAL_KEYWORDS["negation"]:
        if re.search(rf"\b{re.escape(neg)}\b", preceding):
            return True
    return False


def extract_with_scispacy(text: str) -> List[Dict]:
    nlp = registry.load_spacy()
    doc = nlp(text[:10000])
    entities = []

    for ent in doc.ents:
        label = ent.label_.lower()
        if label not in ("disease_or_syndrome", "sign_or_symptom", "body_part_organ_or_organ_component",
                          "anatomical_structure", "clinical_attribute", "finding"):
            continue

        entity_type = "anatomy" if "body_part" in label or "anatomical" in label else "finding"
        negated = _is_negated(text, ent.start_char)

        entities.append({
            "entity_text": ent.text,
            "entity_type": entity_type,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
            "confidence": 0.78,
            "source": "scispacy",
            "negated": negated,
        })

    return entities


def extract_with_biobert(text: str) -> List[Dict]:
    ner_pipeline = registry.load_biobert()
    chunks = _chunk_text(text, max_tokens=450, overlap=50)
    all_entities = []

    for chunk_text, offset in chunks:
        try:
            results = ner_pipeline(chunk_text)
            for r in results:
                mapped_type = ENTITY_LABEL_MAP.get(r["entity_group"], r["entity_group"].lower())
                negated = _is_negated(text, r["start"] + offset)

                all_entities.append({
                    "entity_text": r["word"],
                    "entity_type": mapped_type,
                    "label": r["entity_group"],
                    "start": r["start"] + offset,
                    "end": r["end"] + offset,
                    "confidence": round(float(r["score"]), 4),
                    "source": "biobert",
                    "negated": negated,
                })
        except Exception as e:
            logger.warning("BioBERT chunk failed", error=str(e))

    return _deduplicate_entities(all_entities)


def _chunk_text(text: str, max_tokens: int = 450, overlap: int = 50) -> List[tuple]:
    words = text.split()
    chunks = []
    step = max_tokens - overlap

    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_tokens]
        chunk_text = " ".join(chunk_words)
        char_offset = len(" ".join(words[:i])) + (1 if i > 0 else 0)
        chunks.append((chunk_text, char_offset))

    return chunks if chunks else [(text, 0)]


def _deduplicate_entities(entities: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []
    for e in sorted(entities, key=lambda x: -x["confidence"]):
        key = (e["entity_text"].lower(), e["start"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def extract_rule_based(text: str) -> List[Dict]:
    entities = []
    text_lower = text.lower()

    for category, keywords in MEDICAL_KEYWORDS.items():
        if category in ("negation", "severity"):
            continue
        for keyword in keywords:
            for match in re.finditer(rf"\b{re.escape(keyword)}\b", text_lower):
                negated = _is_negated(text, match.start())
                entities.append({
                    "entity_text": text[match.start():match.end()],
                    "entity_type": category,
                    "label": category.upper(),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.70,
                    "source": "rule",
                    "negated": negated,
                })

    return entities


def extract_entities(
    text: str,
    use_biobert: bool = True,
    use_scispacy: bool = True,
    min_confidence: float = 0.65,
) -> Dict:
    t0 = time.perf_counter()
    all_entities = []

    if use_scispacy:
        scispacy_entities = extract_with_scispacy(text)
        all_entities.extend(scispacy_entities)

    rule_entities = extract_rule_based(text)

    if use_biobert and len(text.split()) >= 10:
        biobert_entities = extract_with_biobert(text)
        all_entities.extend(biobert_entities)
    else:
        all_entities.extend(rule_entities)

    if not all_entities:
        all_entities.extend(rule_entities)

    filtered = [e for e in all_entities if e["confidence"] >= min_confidence]
    deduped = _deduplicate_entities(filtered)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    diseases = [e for e in deduped if e["entity_type"] == "disease" and not e["negated"]]
    anatomy = [e for e in deduped if e["entity_type"] == "anatomy"]
    symptoms = [e for e in deduped if e["entity_type"] in ("symptom", "finding")]
    negated = [e for e in deduped if e["negated"]]

    return {
        "entities": deduped,
        "diseases": diseases,
        "anatomy": anatomy,
        "symptoms": symptoms,
        "negated_entities": negated,
        "entity_count": len(deduped),
        "disease_count": len(diseases),
        "inference_ms": round(elapsed_ms, 2),
    }
