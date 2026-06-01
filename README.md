# 🌤️ Georgia Weather Consensus Engine

A lightweight, self-learning weather aggregator built specifically for Georgia. It pulls from **7 sources** (6 global supercomputer models + yr.no), tracks which ones are most accurate for each city, and blends them into a single **Consensus Forecast** that gets smarter over time.

---

## Why this exists

yr.no is excellent, but it is just *one* model (ECMWF). Sometimes GFS is better for Kutaisi, sometimes ICON beats everyone in Batumi, and sometimes yr.no overpredicts rain in Telavi. This tool collects **all of them**, learns from actual outcomes, and weights the best performers higher.

---

## Requirements

- Python 3.9+ (pre-installed on most Linux/Mac systems)
- Internet connection
- Any computer from the last 15 years

---

## Quick Start (Local)

Open a terminal in this folder and run:

```bash
./run.sh
```

That's it. It will:
1. Create a tiny Python virtual environment (first time only)
2. Download fresh forecasts for all 10 cities
3. Update accuracy scores against historical weather data
4. Generate `index.html` and `dashboard.html`

**Open `index.html` in any browser.** No web server needed.

You also have a desktop shortcut named **"Georgia Weather"** on your desktop for one-click access.

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

Then open `index.html`.

---

## ☁️ Host it online (GitHub Pages) — for mobile & wife access

You can host this **for free** on GitHub so you and your wife can check it from your phones anywhere. GitHub will run the updates automatically every 6 hours — your laptop doesn't even need to be on.

### Step 1: Create a GitHub account & repo

1. Go to [github.com](https://github.com) and sign up (or log in).
2. Click the **+** button (top right) → **New repository**.
3. Name it exactly: `georgia-weather`
4. Make it **Public** (required for free GitHub Pages).
5. **Do NOT** initialize it with a README — leave all checkboxes empty.
6. Click **Create repository**.

### Step 2: Push your code from this computer

Copy and paste these commands **one by one** into your terminal (replace `YOUR_USERNAME` with your actual GitHub username):

```bash
cd ~/georgia-weather
git remote add origin https://github.com/YOUR_USERNAME/georgia-weather.git
git branch -M main
git push -u origin main
```

It will ask for your GitHub username and password. **Use a Personal Access Token as the password** (see below).

#### Getting a Personal Access Token (one-time setup)

1. On GitHub, click your profile picture → **Settings**.
2. Scroll down to **Developer settings** (bottom left).
3. Click **Personal access tokens** → **Tokens (classic)**.
4. Click **Generate new token (classic)**.
5. Give it a name like "weather".
6. Check the box for **repo** (full control of private repositories).
7. Click **Generate token** at the bottom.
8. **Copy the token immediately** — you can't see it again.
9. Use this token as your password when `git push` asks.

### Step 3: Enable GitHub Pages

1. On your new repo page, click **Settings** (top tab).
2. In the left sidebar, click **Pages**.
3. Under **Source**, select **Deploy from a branch**.
4. Under **Branch**, select **main** and folder **/(root)**.
5. Click **Save**.
6. Wait 1–2 minutes, then your site will be live at:
   ```
   https://YOUR_USERNAME.github.io/georgia-weather/
   ```

### Step 4: Allow the robot to update itself

1. In your repo, click **Settings** → **Actions** → **General** (left sidebar).
2. Scroll to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

This lets GitHub automatically run the weather fetcher and update your site every 6 hours.

### Step 5: Test it

1. Go to the **Actions** tab in your repo.
2. You should see a workflow called **Update Weather Dashboard**.
3. Click it, then click **Run workflow** → **Run workflow** (manual trigger).
4. Wait ~2 minutes for it to finish.
5. Visit `https://YOUR_USERNAME.github.io/georgia-weather/` on your phone. Done!

---

## 🤖 Automation (local laptop)

If you want your local laptop to keep updating even without GitHub, a background timer is already installed. It runs automatically every 6 hours at 00:00, 06:00, 12:00, and 18:00 (Tbilisi time).

Check if it's running:
```bash
systemctl --user status georgia-weather.timer
```

View the log:
```bash
cat ~/georgia-weather/automation.log
```

Stop it:
```bash
systemctl --user stop georgia-weather.timer
systemctl --user disable georgia-weather.timer
```

---

## How the learning works

1. **Collect** (`collect.py`) — Runs twice a day. Fetches 10-day forecasts from every model for every city. Stores them in `weather.db`.
2. **Verify** (`verify.py`) — Runs every few days. Downloads actual historical weather (ERA5 reanalysis) and compares it to what each model predicted. Stores Mean Absolute Error per city/model/lead-time.
3. **Blend** (`blend.py`) — When building the dashboard, each model is weighted by `1 / error`. Accurate models dominate the consensus; bad models are muted.

After 2–3 weeks of data, the consensus will consistently outperform any single model for your specific cities.

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
| `report.py` | Build `index.html` + `dashboard.html` |
| `run.sh` | One-click Linux/Mac runner |
| `weather.db` | Local database (created automatically) |
| `index.html` | Your personal weather dashboard (for GitHub Pages) |

---

## Limitations

- **Archive lag**: ERA5 reanalysis (ground truth) is delayed ~5 days. The scoring gets better after the first week of use.
- **No real-time radar**: This is model + post-processing, not satellite nowcasting. For instant rain, look out the window or use a radar app.
- **Local extremes**: Georgia has dramatic microclimates (valleys vs mountains). A 25km grid model will never perfectly predict your exact backyard without local sensors.

---

## Future upgrades you can add

- **Local sensor**: A $25 BME280 sensor on USB can feed current temperature/humidity directly into the database, giving you "now" data no website has.
- **Telegram bot**: A 20-line Python script can message you the consensus every morning.
- **Rain alert**: If 3+ models agree on >5mm rain tomorrow, send yourself a notification.

---

Built for Georgia. 🇬🇪
