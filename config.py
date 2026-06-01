# Georgia Weather Consensus Engine - Configuration

CITIES = {
    "Tbilisi": {"lat": 41.7151, "lon": 44.8271},
    "Kutaisi": {"lat": 42.2679, "lon": 42.6946},
    "Batumi": {"lat": 41.6168, "lon": 41.6367},
    "Rustavi": {"lat": 41.5495, "lon": 44.9932},
    "Gori": {"lat": 42.0500, "lon": 44.1167},
    "Zugdidi": {"lat": 42.5088, "lon": 41.8709},
    "Poti": {"lat": 42.1462, "lon": 41.6719},
    "Telavi": {"lat": 41.9198, "lon": 45.4732},
    "Akhaltsikhe": {"lat": 41.6390, "lon": 42.9826},
    "Mestia": {"lat": 43.0446, "lon": 42.7278},
}

# Open-Meteo model identifiers (all free, global coverage including Georgia)
MODELS = [
    "ecmwf_ifs04",              # ECMWF IFS 0.4° — the engine behind yr.no
    "gfs_global",               # NOAA GFS 0.25°
    "icon_global",              # DWD ICON Global
    "ukmo_global_default",      # UK Met Office Unified Model
    "meteofrance_arpege_world", # MeteoFrance Arpege
    "gem_global",               # Canadian GEM
]

FORECAST_DAYS = 10
DB_NAME = "weather.db"
