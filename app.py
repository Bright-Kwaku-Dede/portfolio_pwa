from functools import wraps
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, Response
import os
import time
import sqlite3
import re
import secrets
from urllib.parse import urlparse
from contextlib import closing
from datetime import datetime

import requests


app = Flask(__name__)

# -------------------------
# Core Pages
# -------------------------






# 2) Replace your whole index() route (the @app.route("/") block) with this:
@app.route("/")
def index():
    featured_projects = [
        {
            "title": "Unified Data Dashboard",
            "icon": "📊",
            "description": (
                "Interactive R Shiny analytics platform combining several public "
                "data tools in one app."
            ),
            "details": (
                "Includes sentiment analysis, a cardiovascular risk calculator, "
                "stock trends, and a minimum wage policy simulator."
            ),
            "tags": ["R Shiny", "Plotly", "Leaflet"],
            "url": "/dashboard",
        },
        {
            "title": "Spare Parts Inventory Tracker",
            "icon": "📦",
            "description": (
                "Inventory management system designed to prevent critical spare-part "
                "shortages in industrial environments."
            ),
            "details": (
                "Includes SKU search, low-stock alerts, and persistent inventory tracking. "
                "Demonstrates backend business logic and database design."
            ),
            "tags": ["Flask", "SQLite", "Inventory Systems", "CRUD"],
            "url": "/inventory",
        },
        {
            "title": "Task Manager",
            "icon": "✅",
            "description": (
                "Full CRUD application with task categories, priority levels, "
                "due dates, and statistics."
            ),
            "details": "Demonstrates database design and RESTful API development.",
            "tags": ["CRUD", "SQLite", "REST API"],
            "url": "/tasks",
        },
        {
            "title": "Weather Dashboard",
            "icon": "🌤️",
            "description": (
                "Live weather data from the Open-Meteo API with 5-day forecasts "
                "and search history."
            ),
            "details": "Demonstrates third-party API integration, caching, and data display.",
            "tags": ["API Integration", "Open-Meteo", "Real-time Data"],
            "url": "/weather",
        },
        {
            "title": "URL Shortener",
            "icon": "🔗",
            "description": (
                "Link shortener with custom short codes and click tracking."
            ),
            "details": "Demonstrates backend routing, redirects, and data persistence.",
            "tags": ["Python", "Flask", "SQLite"],
            "url": "/urlshort",
        },
    ]

    return render_template("index.html", featured_projects=featured_projects)




         # Add this line
@app.route("/dashboard")
@app.route("/dashboard.html")
def dashboard():
    return render_template("dashboard.html")


# -------------------------
# Feature Pages
# -------------------------

@app.route("/inventory")
def inventory():
    return render_template("inventory/inventory.html")


@app.route("/tasks")
def tasks():
    return render_template("tasks/tasks.html")


@app.route("/urlshort")
def urlshort():
    return render_template("urlshort/urlshort.html")


@app.route("/weather")
def weather():
    return render_template("weather/weather.html")


# -------------------------
# API Endpoints
# -------------------------

# -------------------------
# Weather (Open-Meteo, no API key needed)
# -------------------------

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

# WMO weather code -> (description, OpenWeatherMap icon prefix), so weather.js works unchanged
WMO = {
    0: ("Clear sky", "01"), 1: ("Mainly clear", "02"), 2: ("Partly cloudy", "03"),
    3: ("Overcast", "04"), 45: ("Fog", "50"), 48: ("Rime fog", "50"),
    51: ("Light drizzle", "09"), 53: ("Drizzle", "09"), 55: ("Heavy drizzle", "09"),
    56: ("Freezing drizzle", "09"), 57: ("Freezing drizzle", "09"),
    61: ("Light rain", "10"), 63: ("Rain", "10"), 65: ("Heavy rain", "10"),
    66: ("Freezing rain", "10"), 67: ("Freezing rain", "10"),
    71: ("Light snow", "13"), 73: ("Snow", "13"), 75: ("Heavy snow", "13"),
    77: ("Snow grains", "13"), 80: ("Rain showers", "09"), 81: ("Rain showers", "09"),
    82: ("Violent rain showers", "09"), 85: ("Snow showers", "13"), 86: ("Snow showers", "13"),
    95: ("Thunderstorm", "11"), 96: ("Thunderstorm with hail", "11"),
    99: ("Thunderstorm with hail", "11"),
}


def describe(code, is_day=True):
    desc, prefix = WMO.get(code, ("Unknown", "03"))
    return desc, prefix + ("d" if is_day else "n")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---- 1) Replace your existing DB_PATH line with this ----
# Lets a host point the app at a persistent disk via the DATABASE_PATH
# environment variable. Locally it behaves exactly as before.
DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db"),
)


# ---- 2) Delete init_weather_table(), init_contacts_table() and their calls,
#         then paste this in their place (after get_db() is defined) ----
SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'Personal',
    priority TEXT DEFAULT 'Medium',
    due_date TEXT,
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT NOT NULL,
    short_code TEXT UNIQUE NOT NULL,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_name TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    category TEXT,
    quantity INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 2,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    country TEXT,
    temperature REAL,
    weather_description TEXT,
    searched_at TEXT NOT NULL
);
"""


def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with closing(get_db()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


init_db()   # runs at import time, so it also runs under gunicorn


# ---- 3) Contacts: let the table's own default set created_at (UTC) ----
# In submit_contact(), replace the INSERT with:
#
#     conn.execute(
#         "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
#         (name, email, message),
#     )
#
# In list_contacts(), replace the return line with:
#
#     contacts = []
#     for r in rows:
#         d = dict(r)
#         if d["created_at"]:
#             d["created_at"] = d["created_at"].replace(" ", "T") + "Z"
#         contacts.append(d)
#     return jsonify(success=True, contacts=contacts)

# ---- 3) Simple password protection for the admin side ----
# Set ADMIN_PASSWORD as an environment variable. If it is not set,
# the admin pages stay locked for everyone.
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        ok = (
            ADMIN_PASSWORD
            and auth
            and secrets.compare_digest((auth.username or "").encode(), ADMIN_USER.encode())
            and secrets.compare_digest((auth.password or "").encode(), ADMIN_PASSWORD.encode())
        )
        if not ok:
            return Response(
                "Admin login required", 401,
                {"WWW-Authenticate": 'Basic realm="Admin"'},
            )
        return view(*args, **kwargs)
    return wrapped


# ---- 4) Routes ----
# Remove @app.route("/admin") from your dashboard() function, then add:
@app.route("/admin")
@require_admin
def admin():
    return render_template("admin.html")


@app.route("/api/contact", methods=["POST"])
def submit_contact():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    message = str(data.get("message", "")).strip()

    if not name or not email or not message:
        return jsonify(success=False, error="Name, email and message are required"), 400
    if "@" not in email or len(email) > 254:
        return jsonify(success=False, error="Enter a valid email address"), 400
    if len(name) > 100 or len(message) > 5000:
        return jsonify(success=False, error="Name or message is too long"), 400

    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO contacts (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    return jsonify(success=True), 201


@app.route("/api/contacts", methods=["GET"])
@require_admin
def list_contacts():
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT id, name, email, message, created_at FROM contacts ORDER BY id DESC"
        ).fetchall()
    return jsonify(success=True, contacts=[dict(r) for r in rows])
# -------------------------
# Inventory (uses the existing `inventory` table)
# -------------------------

@app.route("/api/inventory", methods=["GET"])
def list_inventory():
    q = request.args.get("search", "").strip()
    sql = (
        "SELECT part_name, sku, "
        "COALESCE(quantity, 0) AS quantity, "
        "COALESCE(location, '') AS location, "
        "COALESCE(category, 'General') AS category, "
        "COALESCE(min_stock_level, 2) AS min_stock_level "
        "FROM inventory"
    )
    params = ()
    if q:
        like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        sql += " WHERE part_name LIKE ? ESCAPE '\\' OR sku LIKE ? ESCAPE '\\'"
        params = (like, like)
    # low-stock parts first, then alphabetical
    sql += (" ORDER BY (COALESCE(quantity, 0) <= COALESCE(min_stock_level, 2)) DESC,"
            " part_name COLLATE NOCASE")
    with closing(get_db()) as conn:
        rows = conn.execute(sql, params).fetchall()
    return jsonify(success=True, parts=[dict(r) for r in rows])


@app.route("/api/inventory", methods=["POST"])
def add_part():
    data = request.get_json(silent=True) or {}
    name = str(data.get("part_name", "")).strip()
    sku = str(data.get("sku", "")).strip()
    if not name or not sku:
        return jsonify(success=False, error="Part name and SKU are required"), 400
    try:
        qty = int(data.get("quantity") or 0)
        min_stock = int(data.get("min_stock_level", 2))
    except (TypeError, ValueError):
        return jsonify(success=False, error="Quantity must be a whole number"), 400
    if qty < 0 or min_stock < 0:
        return jsonify(success=False, error="Quantity can't be negative"), 400

    try:
        with closing(get_db()) as conn:
            dup = conn.execute(
                "SELECT 1 FROM inventory WHERE lower(sku) = lower(?)", (sku,)
            ).fetchone()
            if dup:
                return jsonify(success=False, error=f"SKU '{sku}' already exists"), 409
            conn.execute(
                "INSERT INTO inventory "
                "(part_name, sku, category, quantity, min_stock_level, location) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, sku,
                 str(data.get("category", "General")).strip() or "General",
                 qty, min_stock,
                 str(data.get("location", "")).strip()),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify(success=False, error=f"SKU '{sku}' already exists"), 409
    return jsonify(success=True), 201

_cache = {}
CACHE_SECONDS = 600

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


def matches_hint(place, hint):
    """True if the hint (state, province, country, or country code) fits this place."""
    h = hint.strip().lower()
    wanted = {h}
    if h.upper() in US_STATES:
        wanted.add(US_STATES[h.upper()].lower())
    fields = {
        str(place.get(k, "")).lower()
        for k in ("admin1", "admin2", "admin3", "country", "country_code")
    }
    return bool(wanted & fields)


def find_place(query):
    """'Albany' or 'Albany, Georgia' or 'Albany, GA, US' -> best matching place, or None."""
    parts = [p.strip() for p in query.split(",") if p.strip()]
    if not parts:
        return None
    name, hints = parts[0], parts[1:]

    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": name, "count": 20, "language": "en"},
        timeout=8,
    )
    geo.raise_for_status()
    for place in geo.json().get("results") or []:
        if all(matches_hint(place, h) for h in hints):
            return place
    return None


def get_weather(query):
    """Returns (place, weather_json), or None if no place matches.
    Raises requests.RequestException if the service is unreachable."""
    key = query.lower()
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]

    place = find_place(query)
    if not place:
        return None
    # "Albany, Georgia" so the page and history show which Albany was used
    place["label"] = (
        f"{place['name']}, {place['admin1']}" if place.get("admin1") else place["name"]
    )

    wx = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                       "is_day,weather_code,surface_pressure,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "wind_speed_unit": "ms",
            "forecast_days": 5,
            "timezone": "auto",
        },
        timeout=8,
    )
    wx.raise_for_status()
    result = (place, wx.json())
    _cache[key] = (time.time(), result)
    return result


def lookup_or_error(city):
    """Shared by the endpoints. Returns (data, error_response)."""
    if not city:
        return None, (jsonify(success=False, error="No city provided"), 400)
    try:
        data = get_weather(city)
    except requests.RequestException:
        return None, (jsonify(success=False, error="Weather service unavailable. Try again."), 502)
    if data is None:
        return None, (jsonify(success=False, error=f"City '{city}' not found"), 404)
    return data, None


@app.route("/api/weather/current", methods=["GET"])
def get_current_weather():
    city = request.args.get("city", "").strip()
    data, err = lookup_or_error(city)
    if err:
        return err
    place, wx = data
    cur = wx["current"]
    description, icon = describe(cur["weather_code"], bool(cur["is_day"]))
    country = place.get("country", "")
    label = place.get("label", place["name"])

    with closing(get_db()) as conn:
        conn.execute("DELETE FROM weather_searches WHERE lower(city) = lower(?)", (label,))
        conn.execute(
            "INSERT INTO weather_searches (city, country, temperature, weather_description, searched_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (label, country, round(cur["temperature_2m"]), description,
             datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()

    return jsonify(
        success=True,
        city=label,
        country=country,
        description=description,
        temperature=round(cur["temperature_2m"]),
        feels_like=round(cur["apparent_temperature"]),
        humidity=cur["relative_humidity_2m"],
        wind_speed=round(cur["wind_speed_10m"], 1),
        pressure=round(cur["surface_pressure"]),
        icon=icon,
    )


@app.route("/api/weather/forecast", methods=["GET"])
def get_weather_forecast():
    city = request.args.get("city", "").strip()
    data, err = lookup_or_error(city)
    if err:
        return err
    _, wx = data
    d = wx["daily"]
    forecasts = []
    for i, day in enumerate(d["time"]):
        description, icon = describe(d["weather_code"][i])
        hi, lo = d["temperature_2m_max"][i], d["temperature_2m_min"][i]
        forecasts.append({
            "date": day,
            "icon": icon,
            "description": description,
            "temperature": round((hi + lo) / 2),
            "temp_max": round(hi),
            "temp_min": round(lo),
        })
    return jsonify(success=True, forecasts=forecasts)


@app.route("/api/weather/history", methods=["GET"])
def get_weather_history():
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT city, country, temperature, weather_description, searched_at "
            "FROM weather_searches ORDER BY id DESC LIMIT 5"
        ).fetchall()
    return jsonify(success=True, history=[dict(r) for r in rows])





# -------------------------
# Tasks (uses the existing `tasks` table)
# -------------------------

PRIORITIES = {"low": "Low", "medium": "Medium", "high": "High"}


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT id, title, COALESCE(description, '') AS description, "
            "COALESCE(category, 'Personal') AS category, "
            "COALESCE(priority, 'Medium') AS priority, "
            "COALESCE(due_date, '') AS due_date, "
            "COALESCE(completed, 0) AS completed "
            "FROM tasks ORDER BY completed ASC, id DESC"
        ).fetchall()
    return jsonify(success=True, tasks=[dict(r) for r in rows])


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(success=False, error="Title is required"), 400
    priority = PRIORITIES.get(str(data.get("priority", "Medium")).strip().lower(), "Medium")
    category = str(data.get("category", "Personal")).strip() or "Personal"
    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO tasks (title, description, category, priority, due_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, str(data.get("description", "")).strip(), category, priority,
             str(data.get("due_date", "")).strip() or None),
        )
        conn.commit()
    return jsonify(success=True), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    if "completed" not in data:
        return jsonify(success=False, error="Nothing to update"), 400
    with closing(get_db()) as conn:
        cur = conn.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (1 if data["completed"] else 0, task_id),
        )
        conn.commit()
    if cur.rowcount == 0:
        return jsonify(success=False, error="Task not found"), 404
    return jsonify(success=True)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with closing(get_db()) as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    if cur.rowcount == 0:
        return jsonify(success=False, error="Task not found"), 404
    return jsonify(success=True)


@app.route("/api/tasks/stats", methods=["GET"])
def task_stats():
    with closing(get_db()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(CASE WHEN COALESCE(completed, 0) = 1 THEN 1 ELSE 0 END), 0) AS completed "
            "FROM tasks"
        ).fetchone()
    total, completed = row["total"], row["completed"]
    return jsonify(success=True,
                   stats={"total": total, "completed": completed, "pending": total - completed})
    # -------------------------
# URL Shortener (uses the existing `urls` table)
# -------------------------

CODE_RE = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
CODE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def is_http_url(value):
    try:
        p = urlparse(value)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


def short_url_for(code):
    return request.host_url + "s/" + code


@app.route("/api/urls", methods=["GET"])
def list_urls():
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT id, original_url, short_code, COALESCE(clicks, 0) AS clicks, created_at "
            "FROM urls ORDER BY id DESC"
        ).fetchall()
    urls = []
    for r in rows:
        d = dict(r)
        d["short_url"] = short_url_for(d["short_code"])
        # CURRENT_TIMESTAMP is stored in UTC without a zone marker
        d["created_at"] = (d["created_at"] or "").replace(" ", "T") + "Z" if d["created_at"] else None
        urls.append(d)
    return jsonify(success=True, urls=urls)


@app.route("/api/urls", methods=["POST"])
def create_url():
    data = request.get_json(silent=True) or {}
    original = str(data.get("url", "")).strip()
    custom = str(data.get("custom_code", "")).strip()

    if not is_http_url(original):
        return jsonify(success=False, error="Enter a valid http:// or https:// URL"), 400
    if custom and not CODE_RE.match(custom):
        return jsonify(success=False,
                       error="Custom code: 1-20 letters, numbers, hyphens or underscores"), 400

    with closing(get_db()) as conn:
        if custom:
            code = custom
            try:
                conn.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                             (original, code))
                conn.commit()
            except sqlite3.IntegrityError:
                return jsonify(success=False, error=f"Code '{code}' is already taken"), 409
        else:
            for _ in range(10):
                code = "".join(secrets.choice(CODE_CHARS) for _ in range(6))
                try:
                    conn.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                                 (original, code))
                    conn.commit()
                    break
                except sqlite3.IntegrityError:
                    continue
            else:
                return jsonify(success=False, error="Could not generate a unique code"), 500

    return jsonify(success=True, short_url=short_url_for(code), original_url=original), 201


@app.route("/api/urls/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    with closing(get_db()) as conn:
        cur = conn.execute("DELETE FROM urls WHERE id = ?", (url_id,))
        conn.commit()
    if cur.rowcount == 0:
        return jsonify(success=False, error="URL not found"), 404
    return jsonify(success=True)


@app.route("/s/<code>")
def follow_short_url(code):
    with closing(get_db()) as conn:
        row = conn.execute(
            "SELECT original_url FROM urls WHERE short_code = ?", (code,)
        ).fetchone()
        if row is None or not is_http_url(row["original_url"]):
            return "Short link not found", 404
        conn.execute("UPDATE urls SET clicks = COALESCE(clicks, 0) + 1 WHERE short_code = ?", (code,))
        conn.commit()
    return redirect(row["original_url"], code=302)



# -------------------------
# PWA Manifest
# -------------------------

@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def service_worker():
    response = send_from_directory("static", "sw.js")
    response.headers["Cache-Control"] = "no-cache"
    return response


# -------------------------
# Run App
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)
