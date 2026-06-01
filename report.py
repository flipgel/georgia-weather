#!/usr/bin/env python3
"""Generate a static dashboard.html file — open it in any browser."""

import sqlite3
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import CITIES, MODELS
from db import get_conn, get_scores
from blend import get_consensus

TBILISI = ZoneInfo("Asia/Tbilisi")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Georgia Weather Consensus</title>
<style>
  :root {{ --bg:#f7fafc; --card:#fff; --accent:#2b6cb0; --good:#c6f6d5; --text:#2d3748; }}
  body {{ font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen,sans-serif; background:var(--bg); color:var(--text); margin:0; padding:20px; }}
  h1 {{ margin:0 0 5px; font-size:1.6rem; }}
  .subtitle {{ color:#718096; font-size:0.9rem; margin-bottom:18px; }}
  .tabs {{ display:flex; gap:4px; flex-wrap:wrap; margin-bottom:12px; }}
  .tab {{ padding:8px 14px; background:#e2e8f0; border-radius:6px 6px 0 0; cursor:pointer; border:none; font-size:0.9rem; }}
  .tab.active {{ background:var(--accent); color:#fff; }}
  .panel {{ display:none; background:var(--card); padding:18px; border-radius:0 6px 6px 6px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
  .panel.active {{ display:block; }}
  table {{ border-collapse:collapse; width:100%; font-size:0.88rem; margin-top:10px; }}
  th, td {{ border:1px solid #e2e8f0; padding:7px 5px; text-align:center; }}
  th {{ background:#edf2f7; }}
  tr:nth-child(even) {{ background:#f7fafc; }}
  .consensus {{ background:var(--good); font-weight:700; }}
  .num {{ font-variant-numeric: tabular-nums; }}
  .small {{ font-size:0.78rem; color:#718096; }}
  .section {{ margin-top:22px; }}
  .section h3 {{ margin:0 0 8px; font-size:1rem; }}
</style>
</head>
<body>
<h1>🌤️ Georgia Weather Consensus Engine</h1>
<p class="subtitle">Last updated: {timestamp} &nbsp;|&nbsp; Models: {model_count} global + yr.no &nbsp;|&nbsp; Click a city tab below</p>
<div class="tabs">{tabs}</div>
{panels}
<script>
function showTab(cid) {{
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('panel-'+cid).classList.add('active');
  document.getElementById('tab-'+cid).classList.add('active');
}}
</script>
</body>
</html>"""


def build():
    timestamp = datetime.now(TBILISI).strftime("%Y-%m-%d %H:%M")
    tabs = ""
    panels = ""

    for city in CITIES:
        cid = city.replace(" ", "-").replace(".", "")
        tabs += f'<button class="tab" id="tab-{cid}" onclick="showTab(\'{cid}\')">{city}</button>\n'
        content = f'<h2>{city}</h2>\n'

        # --- Forecast table ---
        dates = [
            (datetime.now(TBILISI) + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(10)
        ]
        content += '<div class="section"><h3>10-Day Forecast</h3><table><tr><th>Date</th><th>Consensus</th>'
        all_models = MODELS + ["yr.no"]
        for m in all_models:
            content += f'<th>{m}</th>'
        content += '</tr>\n'

        for d in dates:
            content += '<tr>'
            content += f'<td>{d}</td>'

            # Consensus cell
            cons = get_consensus(city, d)
            if cons and cons.get("temp_max") is not None:
                content += (
                    f'<td class="consensus num">'
                    f'{cons["temp_min"]:.0f}° – {cons["temp_max"]:.0f}°<br>'
                    f'<span class="small">💧{cons.get("precipitation", 0):.1f}mm</span></td>'
                )
            else:
                content += '<td class="consensus">-</td>'

            # Individual models
            conn = get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                """SELECT model, temp_max, temp_min, precipitation FROM forecasts
                WHERE city=? AND target_date=?
                AND fetched_at >= (SELECT datetime(MAX(fetched_at), '-30 minutes') FROM forecasts WHERE city=?)""",
                (city, d, city),
            )
            rows = {r["model"]: dict(r) for r in c.fetchall()}
            conn.close()

            for m in all_models:
                if m in rows and rows[m].get("temp_max") is not None:
                    r = rows[m]
                    content += (
                        f'<td class="num">{r["temp_min"]:.0f}° – {r["temp_max"]:.0f}°<br>'
                        f'<span class="small">💧{r.get("precipitation", 0):.1f}mm</span></td>'
                    )
                else:
                    content += '<td>-</td>'
            content += '</tr>\n'
        content += '</table></div>\n'

        # --- Scores table ---
        scores = get_scores(city)
        if scores:
            content += '<div class="section"><h3>Verified Accuracy (lower = better)</h3><table><tr><th>Model</th><th>Lead</th><th>Temp MAE</th><th>Samples</th></tr>\n'
            for s in scores:
                mae = (s.get("mae_temp_max") or 0) + (s.get("mae_temp_min") or 0)
                content += (
                    f'<tr><td>{s["model"]}</td><td>{s["lead_days"]}d</td>'
                    f'<td class="num">{mae:.2f}°C</td><td>{s["samples"]}</td></tr>\n'
                )
            content += '</table></div>\n'
        else:
            content += (
                '<div class="section"><p class="small">No accuracy scores yet. '
                'Run <code>python verify.py</code> after collecting a few days of data. '
                'The consensus will then auto-weight the best models for this city.</p></div>'
            )

        panels += f'<div class="panel" id="panel-{cid}">\n{content}\n</div>\n'

    # Activate first tab
    first = list(CITIES.keys())[0].replace(" ", "-").replace(".", "")
    tabs = tabs.replace(f'id="tab-{first}"', f'id="tab-{first}" class="active"')
    panels = panels.replace(f'id="panel-{first}"', f'id="panel-{first}" class="active"')

    html = HTML_TEMPLATE.format(
        timestamp=timestamp, model_count=len(MODELS), tabs=tabs, panels=panels
    )
    base = os.path.dirname(__file__)
    for fname in ("dashboard.html", "index.html"):
        path = os.path.join(base, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"📊 Dashboard written to: {os.path.join(base, 'index.html')}")
    print("   Open it in your browser (double-click the file).")


if __name__ == "__main__":
    build()
