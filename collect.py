#!/usr/bin/env python3
"""Fetch fresh forecasts from all sources and store them."""

from config import CITIES, MODELS, FORECAST_DAYS
from fetch import fetch_openmeteo, fetch_metno
from db import init, insert_forecasts


def main():
    init()
    print("🌤️  Georgia Weather Consensus — Collecting forecasts...\n")
    all_records = []

    for city, info in CITIES.items():
        print(f"📍 {city}")
        # Open-Meteo models (6 sources in one API family)
        for model in MODELS:
            try:
                recs = fetch_openmeteo(
                    city, info["lat"], info["lon"], model, days=FORECAST_DAYS
                )
                all_records.extend(recs)
                print(f"   ✅ {model}")
            except Exception as e:
                print(f"   ❌ {model} — {e}")

        # MET Norway / yr.no native
        try:
            recs = fetch_metno(city, info["lat"], info["lon"])
            all_records.extend(recs)
            print(f"   ✅ yr.no")
        except Exception as e:
            print(f"   ❌ yr.no — {e}")
        print()

    insert_forecasts(all_records)
    print(f"💾 Done. Saved {len(all_records)} forecast records to weather.db")


if __name__ == "__main__":
    main()
