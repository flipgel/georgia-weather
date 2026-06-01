# 🌤️ Georgia Weather Consensus Engine

A lightweight, self-learning weather aggregator built specifically for Georgia. It pulls from **7 sources** (6 global supercomputer models + yr.no), tracks which ones are most accurate for each city, and blends them into a single **Consensus Forecast** that gets smarter over time.

---

## Why this exists

yr.no is excellent, but it is just *one* model (ECMWF). Sometimes GFS is better for Kutaisi, sometimes ICON beats everyone in Batumi, and sometimes yr.no overpredicts rain in Telavi. This tool collects **all of them**, learns from actual outcomes, and weights the best performers higher.

---

## Requirements

- Python 3.7+ (pre-installed on most Linux/Mac systems)
- Internet connection
- Any computer from the last 15 years

---

## Quick Start

Open a terminal in this folder and run:

```bash
./run.sh
```

That's it. It will:
1. Create a tiny Python virtual environment (first time only)
2. Download fresh forecasts for all 10 cities
3. Update accuracy scores against historical weather data
4. Generate `dashboard.html`

**Open `dashboard.html` in any browser.** No web server needed.

---

## Windows users

If you are on Windows, open PowerShell in this folder and run:

```powershell
python -m venv venv
venv\Scripts\pip install requests
venv\Scripts\python collect.py
venv\Scripts\python verify.py
venv\Scripts\python report.py
```

Then open `dashboard.html`.

---

## How the learning works

1. **Collect** (`collect.py`) — Runs twice a day. Fetches 10-day forecasts from every model for every city. Stores them in `weather.db`.
2. **Verify** (`verify.py`) — Runs every few days. Downloads actual historical weather (ERA5 reanalysis) and compares it to what each model predicted. Stores Mean Absolute Error per city/model/lead-time.
3. **Blend** (`blend.py`) — When building the dashboard, each model is weighted by `1 / error`. Accurate models dominate the consensus; bad models are muted.

After 2–3 weeks of data, the consensus will consistently outperform any single model for your specific cities.

---

## Automation (Linux/Mac)

To run this automatically every 6 hours, add a cron job:

```bash
crontab -e
```

Add this line (adjust the path to your folder):

```
0 6,12,18 * * * cd /home/k56/georgia-weather && ./run.sh >> run.log 2>&1
```

This fetches fresh data at 06:00, 12:00, and 18:00 daily.

---

## Data sources (all free, no API keys needed)

| Source | Model | Resolution | Provider |
|--------|-------|------------|----------|
| ecmwf_ifs04 | ECMWF IFS | 0.4° | European Centre (yr.no uses this) |
| gfs_global | NOAA GFS | 0.25° | US National Weather Service |
| icon_global | DWD ICON | 0.11° Europe / global | German Weather Service |
| ukmo_global_default | UK Met Office UM | global | UK Met Office |
| meteofrance_arpege_world | Arpege | global | MeteoFrance |
| gem_global | GEM | global | Canadian Meteorological Centre |
| yr.no | HARMONIE/ECMWF blend | ~2.5km (local) | Norwegian Met Institute |

All accessed via [Open-Meteo](https://open-meteo.com) and [MET Norway](https://api.met.no) free APIs.

---

## Files

| File | Purpose |
|------|---------|
| `config.py` | City coordinates and model list |
| `db.py` | SQLite database handling |
| `fetch.py` | API clients for Open-Meteo and MET Norway |
| `collect.py` | Fetch and store new forecasts |
| `verify.py` | Compare forecasts to reality and score them |
| `blend.py` | Generate the weighted consensus |
| `report.py` | Build `dashboard.html` |
| `run.sh` | One-click Linux/Mac runner |
| `weather.db` | Local database (created automatically) |
| `dashboard.html` | Your personal weather dashboard |

---

## Limitations

- **Archive lag**: ERA5 reanalysis (ground truth) is delayed ~5 days. The scoring gets better after the first week of use.
- **No real-time radar**: This is model + post-processing, not satellite nowcasting. For instant rain, look out the window or use a radar app.
- **Local extremes**: Georgia has dramatic microclimates (valleys vs mountains). A 25km grid model will never perfectly predict your exact backyard without local sensors.

---

## Future upgrades you can add

- **Local sensor**: A $25 BME280 sensor on USB can feed current temperature/humidity directly into the database, giving you "now" data no website can match.
- **Telegram bot**: A 20-line Python script can message you the consensus every morning.
- **Rain alert**: If 3+ models agree on >5mm rain tomorrow, send yourself a notification.

---

Built for Georgia. 🇬🇪
