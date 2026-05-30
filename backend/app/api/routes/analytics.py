from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, Query
from app.api.dependencies.auth import CurrentUser
from app.db.mongodb import get_database
from app.services.aggregator import (
    get_kpi_summary,
    get_severity_distribution,
    get_disease_prevalence,
    get_daily_report_counts,
    get_processing_metrics,
    get_confidence_distribution,
    get_daily_processing_stats,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _moving_average(series, window=7):
    result = []
    for i in range(len(series)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(round(float(np.mean(series[i - window + 1:i + 1])), 4))
    return result


@router.get("/kpis")
async def kpis(current_user: CurrentUser):
    db = get_database()
    return await get_kpi_summary(db)


@router.get("/severity")
async def severity(current_user: CurrentUser, days: int = Query(30)):
    db = get_database()
    return await get_severity_distribution(db, days=days)


@router.get("/diseases")
async def diseases(current_user: CurrentUser, days: int = Query(30), limit: int = Query(10)):
    db = get_database()
    return await get_disease_prevalence(db, days=days, limit=limit)


@router.get("/trends")
async def trends(current_user: CurrentUser, days: int = Query(90), window: int = Query(7)):
    db = get_database()
    daily = await get_daily_report_counts(db, days=days)
    if not daily:
        return {"trend_data": [], "direction": "insufficient_data", "current_velocity": 0}

    df = pd.DataFrame(daily).sort_values("date").reset_index(drop=True)
    dates = df["date"].tolist()
    total_series = df["total_reports"].fillna(0).tolist() if "total_reports" in df.columns else [0] * len(df)
    critical_series = df["critical_count"].fillna(0).astype(int).tolist() if "critical_count" in df.columns else [0] * len(df)

    ma_total = _moving_average(total_series, window)

    trend_rows = [
        {
            "date": dates[i],
            "count": int(total_series[i]),
            "sma7": ma_total[i],
            "critical_count": critical_series[i],
        }
        for i in range(len(dates))
    ]
    return {"trend_data": trend_rows, "window": window}


@router.get("/forecast")
async def forecast(
    current_user: CurrentUser,
    days_history: int = Query(90),
    periods: int = Query(30),
    disease: Optional[str] = Query(None),
):
    from datetime import datetime, timedelta
    db = get_database()
    daily = await get_daily_report_counts(db, days=days_history)
    if not daily:
        return {"forecast": []}

    series = [d["total_reports"] for d in daily]
    if len(series) < 7:
        return {"forecast": []}

    avg = float(np.mean(series[-14:])) if len(series) >= 14 else float(np.mean(series))
    std = float(np.std(series[-14:])) if len(series) >= 14 else float(np.std(series))

    last_date = datetime.strptime(daily[-1]["date"], "%Y-%m-%d")
    result = []
    for i in range(1, periods + 1):
        d = last_date + timedelta(days=i)
        noise = float(np.random.normal(0, std * 0.3))
        fc = max(0.0, avg + noise)
        result.append({
            "ds": d.strftime("%Y-%m-%d"),
            "yhat": round(fc, 1),
            "yhat_lower": round(max(0.0, fc - std), 1),
            "yhat_upper": round(fc + std, 1),
            "trend": round(avg, 1),
        })
    return {"forecast": result}


@router.get("/anomalies")
async def anomalies(current_user: CurrentUser, days: int = Query(90)):
    return {"anomalies": []}


@router.get("/processing")
async def processing(
    current_user: CurrentUser,
    days: int = Query(30),
):
    db = get_database()
    hours = days * 24
    metrics = await get_processing_metrics(db, hours=hours)
    daily = await get_daily_processing_stats(db, days=days)

    summary = {
        "total_processed": metrics.get("completed", 0),
        "success_rate_pct": metrics.get("success_rate_pct", 0.0),
        "avg_ms": metrics.get("avg_processing_ms", 0.0),
        "p95_ms": metrics.get("p95_processing_ms", 0.0),
        "failure_count": metrics.get("failed", 0),
    }

    return {"summary": summary, "latency_by_day": daily}


@router.get("/confidence")
async def confidence(current_user: CurrentUser, days: int = Query(30)):
    db = get_database()
    data = await get_confidence_distribution(db, days=days)
    return {"distribution": data}
