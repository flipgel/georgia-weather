#!/usr/bin/env python3
"""
Download actual historical weather (ERA5 reanalysis via Open-Meteo archive)
and compute per-model accuracy scores.

Note: ERA5 data lags ~5 days. If no archive data exists yet, the script
will tell you to wait. Accuracy scoring improves automatically as days pass.
"""

import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import CITIES
from db import init, insert_actuals, get_conn

TBILISI = ZoneInfo("Asia/Tbilisi")

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_archive(city, lat, lon, start, end):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max",
        "timezone": "Asia/Tbilisi",
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    daily = data.get("daily", {})
    times = daily.get("time", [])
    records = []
    for i, t in enumerate(times):
        records.append(
            {
                "city": city,
                "date": t,
                "temp_max": _val(daily.get("temperature_2m_max"), i),
                "temp_min": _val(daily.get("temperature_2m_min"), i),
                "precipitation": _val(daily.get("precipitation_sum"), i),
                "humidity": _val(daily.get("relative_humidity_2m_mean"), i),
                "wind_speed": _val(daily.get("wind_speed_10m_max"), i),
                "fetched_at": datetime.now(TBILISI).isoformat(),
            }
        )
    return records


def compute_scores():
    conn = get_conn()
    c = conn.cursor()
    # Aggregate absolute errors per city / model / lead-time
    c.execute(
        """SELECT
            f.city,
            f.model,
            f.lead_days,
            AVG(ABS(f.temp_max - a.temp_max)) AS mae_max,
            AVG(ABS(f.temp_min - a.temp_min)) AS mae_min,
            AVG(f.precipitation - a.precipitation) AS rain_bias,
            COUNT(*) AS n
        FROM forecasts f
        JOIN actuals a ON f.city = a.city AND f.target_date = a.date
        GROUP BY f.city, f.model, f.lead_days"""
    )
    rows = c.fetchall()
    now = datetime.now(TBILISI).isoformat()
    updated = 0
    for row in rows:
        city, model, lead, mae_max, mae_min, bias, n = row
        c.execute(
            """INSERT INTO scores
            (city, model, lead_days, mae_temp_max, mae_temp_min, rain_bias, samples, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(city, model, lead_days) DO UPDATE SET
                mae_temp_max=excluded.mae_temp_max,
                mae_temp_min=excluded.mae_temp_min,
                rain_bias=excluded.rain_bias,
                samples=excluded.samples,
                updated_at=excluded.updated_at""",
            (city, model, lead, mae_max, mae_min, bias, n, now),
        )
        updated += 1
    conn.commit()
    conn.close()
    return updated


def main():
    init()
    end = (datetime.now(TBILISI) - timedelta(days=1)).strftime("%Y-%m-%d")
    start = (datetime.now(TBILISI) - timedelta(days=14)).strftime("%Y-%m-%d")
    print(f"📥 Fetching archive actuals from {start} to {end}...\n")

    total_actuals = 0
    for city, info in CITIES.items():
        print(f"📍 {city}...", end=" ")
        try:
            recs = fetch_archive(city, info["lat"], info["lon"], start, end)
            insert_actuals(recs)
            total_actuals += len(recs)
            print(f"{len(recs)} days")
        except Exception as e:
            print(f"FAIL — {e}")

    print(f"\n🧮 Computing accuracy scores...")
    n = compute_scores()
    print(f"💾 Updated {n} city/model/lead-time score records.")
    print(
        "\n💡 Tip: Run this script once every few days. The longer it runs, "
        "the smarter the consensus becomes."
    )


def _val(arr, idx):
    if not arr or idx >= len(arr):
        return None
    return arr[idx]


if __name__ == "__main__":
    main()
