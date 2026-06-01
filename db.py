import sqlite3
import os
from config import DB_NAME

DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)


def get_conn():
    return sqlite3.connect(DB_PATH)


def init():
    """Create SQLite tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        model TEXT,
        fetched_at TEXT,
        target_date TEXT,
        lead_days INTEGER,
        temp_max REAL,
        temp_min REAL,
        precipitation REAL,
        humidity REAL,
        wind_speed REAL
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS actuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        date TEXT,
        temp_max REAL,
        temp_min REAL,
        precipitation REAL,
        humidity REAL,
        wind_speed REAL,
        fetched_at TEXT,
        UNIQUE(city, date)
    )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        model TEXT,
        lead_days INTEGER,
        mae_temp_max REAL,
        mae_temp_min REAL,
        rain_bias REAL,
        samples INTEGER,
        updated_at TEXT,
        UNIQUE(city, model, lead_days)
    )"""
    )
    conn.commit()
    conn.close()


def insert_forecasts(records):
    conn = get_conn()
    c = conn.cursor()
    for r in records:
        c.execute(
            """INSERT INTO forecasts
            (city, model, fetched_at, target_date, lead_days,
             temp_max, temp_min, precipitation, humidity, wind_speed)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                r["city"],
                r["model"],
                r["fetched_at"],
                r["target_date"],
                r["lead_days"],
                r.get("temp_max"),
                r.get("temp_min"),
                r.get("precipitation"),
                r.get("humidity"),
                r.get("wind_speed"),
            ),
        )
    conn.commit()
    conn.close()


def insert_actuals(records):
    conn = get_conn()
    c = conn.cursor()
    for r in records:
        c.execute(
            """INSERT OR REPLACE INTO actuals
            (city, date, temp_max, temp_min, precipitation,
             humidity, wind_speed, fetched_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                r["city"],
                r["date"],
                r.get("temp_max"),
                r.get("temp_min"),
                r.get("precipitation"),
                r.get("humidity"),
                r.get("wind_speed"),
                r.get("fetched_at"),
            ),
        )
    conn.commit()
    conn.close()


def get_scores(city=None):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if city:
        c.execute(
            "SELECT * FROM scores WHERE city=? ORDER BY model, lead_days",
            (city,),
        )
    else:
        c.execute("SELECT * FROM scores ORDER BY city, model, lead_days")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
