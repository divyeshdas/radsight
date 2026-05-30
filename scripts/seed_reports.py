#!/usr/bin/env python3
import asyncio, os, random, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://radsight:divyesh03@cluster0.aq0rakd.mongodb.net/?appName=Cluster0")
DB_NAME = "radsight"

SEVERITIES = ["normal", "low", "moderate", "high", "critical"]
SEV_WEIGHTS = [0.35, 0.25, 0.20, 0.12, 0.08]
DISEASES = [
    "pneumonia", "pleural_effusion", "cardiomegaly", "pneumothorax",
    "atelectasis", "consolidation", "nodule", "mass", "fracture",
    "pulmonary_edema", "emphysema", "fibrosis",
]
STATUSES = ["completed", "completed", "completed", "pending", "failed"]
MODALITIES = ["CT", "X-Ray", "MRI", "Ultrasound"]
PATIENT_IDS = [f"PAT{i:05d}" for i in range(1, 201)]

def random_report(i: int, created_at: datetime) -> dict:
    severity = random.choices(SEVERITIES, SEV_WEIGHTS)[0]
    risk = {"normal": 0.1, "low": 0.25, "moderate": 0.5, "high": 0.75, "critical": 0.92}[severity]
    risk += random.uniform(-0.08, 0.08)
    risk = round(max(0.01, min(0.99, risk)), 4)
    n_tags = random.randint(1, 4)
    tags = random.sample(DISEASES, n_tags)
    tags.append(severity)
    status = random.choices(STATUSES)[0]
    processing_ms = random.randint(800, 8000) if status == "completed" else None
    confidence = round(random.uniform(0.72, 0.99), 4) if status == "completed" else None
    return {
        "report_id": f"RPT{i:06d}",
        "patient_id": random.choice(PATIENT_IDS),
        "modality": random.choice(MODALITIES),
        "severity": severity,
        "risk_score": risk,
        "status": status,
        "flagged_for_review": severity in ("high", "critical") and random.random() < 0.6,
        "tags": tags,
        "classification_confidence": confidence,
        "processing_time_ms": processing_ms,
        "findings": f"AI-generated finding for report {i}.",
        "created_at": created_at,
        "updated_at": created_at,
    }

async def main():
    client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    db = client[DB_NAME]

    existing = await db["reports"].count_documents({})
    if existing > 0:
        print(f"Already have {existing} reports — dropping and re-seeding.")
        await db["reports"].drop()

    now = datetime.now(timezone.utc)
    reports = []
    i = 1
    for days_ago in range(90, 0, -1):
        base = now - timedelta(days=days_ago)
        count = random.randint(8, 28)
        for _ in range(count):
            offset = timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            reports.append(random_report(i, base + offset))
            i += 1

    await db["reports"].insert_many(reports)
    print(f"Inserted {len(reports)} reports into '{DB_NAME}'.")

    await db["reports"].create_index([("created_at", -1)])
    await db["reports"].create_index([("severity", 1)])
    await db["reports"].create_index([("status", 1)])
    print("Indexes created.")
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
