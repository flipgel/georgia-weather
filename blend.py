#!/usr/bin/env python3
"""
Generate the 'Kimi Consensus' forecast by weighting each model
according to its recent verified accuracy for that city and lead time.
"""

from db import get_conn, get_scores
from config import CITIES, MODELS
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TBILISI = ZoneInfo("Asia/Tbilisi")


def get_consensus(city, target_date):
    """Return blended forecast dict for a given city and target date."""
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    c = conn.cursor()
    c.execute(
        """SELECT * FROM forecasts
        WHERE city=? AND target_date=?
        AND fetched_at >= (SELECT datetime(MAX(fetched_at), '-30 minutes') FROM forecasts WHERE city=?)
        ORDER BY model""",
        (city, target_date, city),
    )
    forecasts = [dict(r) for r in c.fetchall()]
    conn.close()

    if not forecasts:
        return None

    # Build weight lookup: inverse of total temperature MAE
    scores = get_scores(city)
    weights = {}
    for s in scores:
        key = (s["city"], s["model"], s["lead_days"])
        mae = (s.get("mae_temp_max") or 0) + (s.get("mae_temp_min") or 0)
        weights[key] = 1.0 / (mae + 0.1)  # +0.1 avoids div-by-zero

    # Weighted average per variable
    consensus = {}
    for var in ("temp_max", "temp_min", "precipitation", "humidity", "wind_speed"):
        items = []
        for f in forecasts:
            v = f.get(var)
            if v is None:
                continue
            w = weights.get((city, f["model"], f["lead_days"]), 1.0)
            items.append((v, w))
        if not items:
            consensus[var] = None
            continue
        total_w = sum(w for _, w in items)
        consensus[var] = round(sum(v * w for v, w in items) / total_w, 2)

    consensus["city"] = city
    consensus["target_date"] = target_date
    consensus["lead_days"] = forecasts[0]["lead_days"]
    consensus["models_used"] = len(forecasts)
    return consensus


if __name__ == "__main__":
    print("🧠 Kimi Consensus sample output:\n")
    for city in list(CITIES.keys())[:3]:
        for i in range(3):
            d = (datetime.now(TBILISI) + timedelta(days=i)).strftime("%Y-%m-%d")
            c = get_consensus(city, d)
            if c:
                print(
                    f"{city:12} {d} | T {c['temp_min']:.0f}°–{c['temp_max']:.0f}° | "
                    f"Rain {c['precipitation']:.1f}mm | ({c['models_used']} models)"
                )
