import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TBILISI = ZoneInfo("Asia/Tbilisi")

HEADERS = {
    "User-Agent": "GeorgiaWeatherApp/1.0 (local@georgiaweather.local)"
}


def fetch_openmeteo(city, lat, lon, model, days=10):
    """Fetch a single model from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "model": model,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean,wind_speed_10m_max",
        "forecast_days": days,
        "timezone": "Asia/Tbilisi",
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()
    daily = data.get("daily", {})
    times = daily.get("time", [])
    records = []
    today = datetime.now(TBILISI).date()
    for i, t in enumerate(times):
        target = datetime.strptime(t, "%Y-%m-%d").date()
        lead = (target - today).days
        records.append(
            {
                "city": city,
                "model": model,
                "fetched_at": datetime.now(TBILISI).isoformat(),
                "target_date": t,
                "lead_days": lead,
                "temp_max": _val(daily.get("temperature_2m_max"), i),
                "temp_min": _val(daily.get("temperature_2m_min"), i),
                "precipitation": _val(daily.get("precipitation_sum"), i),
                "humidity": _val(daily.get("relative_humidity_2m_mean"), i),
                "wind_speed": _val(daily.get("wind_speed_10m_max"), i),
            }
        )
    return records


def fetch_metno(city, lat, lon):
    """Fetch from MET Norway (yr.no backend) and aggregate to daily values."""
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    params = {"lat": lat, "lon": lon}
    r = requests.get(url, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()
    timeseries = data.get("properties", {}).get("timeseries", [])

    days = {}
    for entry in timeseries:
        t = entry.get("time", "")
        date = t[:10]
        if date not in days:
            days[date] = {
                "temps": [],
                "precips": [],
                "humids": [],
                "winds": [],
            }

        d = entry.get("data", {})
        inst = d.get("instant", {}).get("details", {})
        next1 = d.get("next_1_hours", {}).get("details", {})
        next6 = d.get("next_6_hours", {}).get("details", {})
        next12 = d.get("next_12_hours", {}).get("details", {})

        # Temperatures — prefer explicit max/min from period summaries
        if "air_temperature_max" in next6 and "air_temperature_min" in next6:
            days[date]["temps"].append(next6["air_temperature_max"])
            days[date]["temps"].append(next6["air_temperature_min"])
        elif "air_temperature_max" in next12 and "air_temperature_min" in next12:
            days[date]["temps"].append(next12["air_temperature_max"])
            days[date]["temps"].append(next12["air_temperature_min"])
        else:
            temp = inst.get("air_temperature")
            if temp is not None:
                days[date]["temps"].append(temp)

        # Precipitation — use the finest granularity available
        precip = None
        if "precipitation_amount" in next1:
            precip = next1["precipitation_amount"]
        elif "precipitation_amount" in next6:
            precip = next6["precipitation_amount"]
        elif "precipitation_amount" in next12:
            precip = next12["precipitation_amount"]
        if precip is not None:
            days[date]["precips"].append(precip)

        # Humidity
        hum = inst.get("relative_humidity")
        if hum is not None:
            days[date]["humids"].append(hum)

        # Wind
        wind = inst.get("wind_speed")
        if wind is not None:
            days[date]["winds"].append(wind)

    records = []
    today = datetime.now(TBILISI).date()
    for date_str, vals in sorted(days.items()):
        if not vals["temps"]:
            continue
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        lead = (target - today).days
        if lead < 0 or lead > 10:
            continue
        records.append(
            {
                "city": city,
                "model": "yr.no",
                "fetched_at": datetime.now(TBILISI).isoformat(),
                "target_date": date_str,
                "lead_days": lead,
                "temp_max": max(vals["temps"]) if vals["temps"] else None,
                "temp_min": min(vals["temps"]) if vals["temps"] else None,
                "precipitation": sum(vals["precips"]) if vals["precips"] else 0,
                "humidity": sum(vals["humids"]) / len(vals["humids"])
                if vals["humids"]
                else None,
                "wind_speed": max(vals["winds"]) if vals["winds"] else None,
            }
        )
    return records


def _val(arr, idx):
    """Safely extract array element, returning None if missing."""
    if not arr or idx >= len(arr):
        return None
    v = arr[idx]
    return v if v is not None else None
