import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import CITIES, MODELS

st.set_page_config(
    page_title="Georgia Weather Consensus",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

TBILISI = ZoneInfo("Asia/Tbilisi")
ALL_MODELS = MODELS + ["yr.no"]


@st.cache_data(ttl=300)
def load_data(city: str):
    conn = sqlite3.connect("weather.db")

    # Latest forecast batch
    c = conn.cursor()
    c.execute(
        "SELECT MAX(fetched_at) FROM forecasts WHERE city=?", (city,)
    )
    latest = c.fetchone()[0]

    df_f = pd.read_sql_query(
        """SELECT * FROM forecasts
           WHERE city=? AND fetched_at=?
           ORDER BY target_date, model""",
        conn,
        params=(city, latest),
    )

    df_s = pd.read_sql_query(
        "SELECT * FROM scores WHERE city=? ORDER BY model, lead_days",
        conn,
        params=(city,),
    )

    conn.close()
    return df_f, df_s, latest


# ── Sidebar ──
st.sidebar.title("🌤️ Georgia Weather")
city = st.sidebar.selectbox("Select city", list(CITIES.keys()))
st.sidebar.caption(f"Coordinates: {CITIES[city]['lat']}, {CITIES[city]['lon']}")
st.sidebar.markdown("---")
st.sidebar.info(
    "This dashboard compares 7 weather models and blends them into a "
    "consensus weighted by proven accuracy."
)

# ── Load data ──
df_forecast, df_scores, latest_fetch = load_data(city)

if df_forecast.empty:
    st.warning("No forecast data yet. Run `./run.sh` or wait for GitHub Actions.")
    st.stop()

st.title(f"{city}")
st.caption(f"Last updated: {latest_fetch}  ·  Data: Open-Meteo + MET Norway")

# ── Consensus cards ──
today = datetime.now(TBILISI).date()
dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]

# Build consensus per day
consensus_rows = []
for d in dates:
    day_data = df_forecast[df_forecast["target_date"] == d]
    if day_data.empty:
        continue
    vals = {}
    for col in ["temp_max", "temp_min", "precipitation", "humidity", "wind_speed"]:
        items = day_data[col].dropna()
        vals[col] = round(items.mean(), 1) if not items.empty else None
    vals["date"] = d
    vals["lead"] = (datetime.strptime(d, "%Y-%m-%d").date() - today).days
    consensus_rows.append(vals)

df_cons = pd.DataFrame(consensus_rows)

st.subheader("📅 5-Day Consensus")
cols = st.columns(len(df_cons))
for idx, row in df_cons.iterrows():
    with cols[idx]:
        day_name = datetime.strptime(row["date"], "%Y-%m-%d").strftime("%a")
        st.metric(
            label=f"{day_name} {row['date']}",
            value=f"{row['temp_min']:.0f}° – {row['temp_max']:.0f}°C",
            delta=f"💧 {row['precipitation'] or 0:.1f} mm" if row["precipitation"] else None,
        )

st.markdown("---")

# ── Model comparison chart ──
st.subheader("📊 Model Comparison")

pivot_max = df_forecast.pivot(index="target_date", columns="model", values="temp_max")
pivot_min = df_forecast.pivot(index="target_date", columns="model", values="temp_min")

# Show only next 7 days
pivot_max = pivot_max.head(7)
pivot_min = pivot_min.head(7)

if not pivot_max.empty:
    tab1, tab2 = st.tabs(["High temp", "Low temp"])
    with tab1:
        st.line_chart(pivot_max, use_container_width=True)
    with tab2:
        st.line_chart(pivot_min, use_container_width=True)
else:
    st.info("Not enough data for chart yet.")

# ── Detailed table ──
st.subheader("🔍 Detailed Forecasts")

display = df_forecast[[
    "target_date", "model", "lead_days",
    "temp_max", "temp_min", "precipitation", "humidity", "wind_speed"
]].copy()
display.columns = [
    "Date", "Model", "Lead", "Max °C", "Min °C",
    "Rain mm", "Humidity %", "Wind km/h"
]
display = display.sort_values(["Date", "Model"])

# Highlight consensus per date
def highlight_consensus(row):
    date = row["Date"]
    day_vals = df_forecast[df_forecast["target_date"] == date]
    style = [""] * len(row)
    if row["Model"] == "consensus":
        return ["background-color: #c6f6d5"] * len(row)
    return style

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rain mm": st.column_config.NumberColumn(format="%.1f"),
        "Humidity %": st.column_config.NumberColumn(format="%.0f"),
        "Wind km/h": st.column_config.NumberColumn(format="%.1f"),
    },
)

# ── Accuracy scores ──
st.markdown("---")
st.subheader("🏆 Verified Accuracy (lower is better)")

if df_scores.empty:
    st.info(
        "No accuracy scores yet. The system needs ~1 week of historical data "
        "to learn which models are best for this city. Scores appear automatically."
    )
else:
    df_scores["Total MAE"] = (
        df_scores["mae_temp_max"].fillna(0) + df_scores["mae_temp_min"].fillna(0)
    )
    chart_data = df_scores.pivot_table(
        index="model", columns="lead_days", values="Total MAE", aggfunc="mean"
    )
    st.bar_chart(chart_data, use_container_width=True)

    with st.expander("See raw scores"):
        st.dataframe(
            df_scores[["model", "lead_days", "mae_temp_max", "mae_temp_min", "samples", "updated_at"]],
            use_container_width=True,
            hide_index=True,
        )

st.markdown("---")
st.caption(
    "Built with Open-Meteo & MET Norway data. "
    "[GitHub repo](https://github.com/flipgel/georgia-weather)"
)
