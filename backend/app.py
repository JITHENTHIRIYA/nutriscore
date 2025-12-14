"""
NutriScore+ Flask Backend API
Authors: Harish Suresh, Jithenthiriya C. Kathirvel, Abirami Saravanan
Date: November 2025

This API provides endpoints for the NutriScore+ nutrition tracking application.
All CRUD operations are implemented with proper error handling.
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# --- psycopg v3 (replacement for psycopg2) ---
import psycopg
from psycopg.rows import dict_row  # returns rows as dictionaries (like RealDictCursor)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Sessions (cookie-based)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Enable CORS for React frontend (session cookies)
CORS(app, supports_credentials=True)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'nutriscore'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

def dsn_from_env() -> str:
    """Build a DSN string from DB_CONFIG for psycopg.connect()."""
    return (
        f"host={DB_CONFIG['host']} "
        f"dbname={DB_CONFIG['database']} "
        f"user={DB_CONFIG['user']} "
        f"password={DB_CONFIG['password']}"
    )

def get_conn():
    """
    psycopg v3 connection helper.
    row_factory=dict_row makes fetches return dicts (similar to RealDictCursor).
    """
    # #region agent log
    try:
        import json
        import urllib.request
        log_data = {
            "location": "app.py:get_conn",
            "message": "Attempting database connection",
            "data": {"host": DB_CONFIG['host'], "database": DB_CONFIG['database'], "user": DB_CONFIG['user']},
            "timestamp": int(datetime.now().timestamp() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A"
        }
        urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
            data=json.dumps(log_data).encode(), 
            headers={'Content-Type': 'application/json'}).read()
    except: pass
    # #endregion
    try:
        conn = psycopg.connect(dsn_from_env(), row_factory=dict_row)
        # #region agent log
        try:
            log_data = {
                "location": "app.py:get_conn",
                "message": "Database connection successful",
                "data": {},
                "timestamp": int(datetime.now().timestamp() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A"
            }
            urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
                data=json.dumps(log_data).encode(), 
                headers={'Content-Type': 'application/json'}).read()
        except: pass
        # #endregion
        return conn
    except Exception as e:
        # #region agent log
        try:
            log_data = {
                "location": "app.py:get_conn",
                "message": "Database connection failed",
                "data": {"error": str(e), "dsn": dsn_from_env().replace(DB_CONFIG['password'], '***')},
                "timestamp": int(datetime.now().timestamp() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A"
            }
            urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
                data=json.dumps(log_data).encode(), 
                headers={'Content-Type': 'application/json'}).read()
        except: pass
        # #endregion
        raise

# ============================================================================
# AUTH / RBAC
# ============================================================================

def _current_user():
    return session.get("user")  # {user_id, username, role}

def _column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s;
                """,
                (table_name, column_name)
            )
            return cur.fetchone() is not None
    except:
        return False

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _current_user():
            return jsonify({"error": "Not authenticated"}), 401
        return fn(*args, **kwargs)
    return wrapper

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _current_user()
        if not user:
            return jsonify({"error": "Not authenticated"}), 401
        if user.get("role") != "admin":
            return jsonify({"error": "You don't have permission"}), 403
        return fn(*args, **kwargs)
    return wrapper

def ensure_admin_bootstrap():
    """
    Ensure there is at least one admin user and that the default admin has a password set.
    Uses ADMIN_BOOTSTRAP_PASSWORD env var (default: admin123).
    """
    admin_password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "admin123")
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, username, role, password_hash FROM users WHERE role='admin' ORDER BY user_id LIMIT 1;")
                admin = cur.fetchone()
                if not admin:
                    cur.execute(
                        """
                        INSERT INTO users (username, role, password_hash, dietary_goal, target_calories, created_at)
                        VALUES (%s, 'admin', %s, 'maintain', 2000, %s)
                        RETURNING user_id, username, role;
                        """,
                        ("admin", generate_password_hash(admin_password), datetime.utcnow()),
                    )
                else:
                    if not admin.get("password_hash"):
                        cur.execute(
                            "UPDATE users SET password_hash=%s WHERE user_id=%s;",
                            (generate_password_hash(admin_password), admin["user_id"]),
                        )

                # Ensure demo users have a password hash if missing
                demo_password = os.getenv("DEMO_USER_PASSWORD", "password")
                cur.execute("UPDATE users SET password_hash=%s WHERE password_hash IS NULL AND username <> 'admin';", (generate_password_hash(demo_password),))
    except Exception:
        # Don't crash the server if bootstrap fails; login will surface errors.
        pass

@app.before_request
def _bootstrap_once():
    if not getattr(app, "_bootstrap_done", False):
        ensure_admin_bootstrap()
        setattr(app, "_bootstrap_done", True)


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    # #region agent log
    try:
        import json
        import urllib.request
        log_data = {
            "location": "app.py:login",
            "message": "Login attempt",
            "data": {"username": username},
            "timestamp": int(datetime.now().timestamp() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "AUTH"
        }
        urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498',
            data=json.dumps(log_data).encode(),
            headers={'Content-Type': 'application/json'}).read()
    except: pass
    # #endregion

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, username, role, password_hash FROM users WHERE username=%s;", (username,))
                user = cur.fetchone()
        if not user or not user.get("password_hash") or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid username or password"}), 401

        session["user"] = {"user_id": user["user_id"], "username": user["username"], "role": user["role"]}
        return jsonify(session["user"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/auth/me")
def me():
    user = _current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    # Check if profile is complete (has height and weight)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT height_value, weight_value FROM users WHERE user_id=%s;",
                    (user["user_id"],)
                )
                profile = cur.fetchone()
                profile_complete = bool(profile and profile.get("height_value") and profile.get("weight_value"))
        user["profile_complete"] = profile_complete
    except Exception:
        user["profile_complete"] = False
    return jsonify(user)


@app.post("/api/auth/logout")
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})


@app.post("/api/auth/signup")
def signup():
    """
    Signup for normal users.
    Required: username, password
    Profile (height/weight/goal) is collected during onboarding after first login.
    """
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Check if username already exists
                cur.execute("SELECT user_id FROM users WHERE username=%s;", (username,))
                if cur.fetchone():
                    return jsonify({"error": "Username already exists"}), 400
                
                # Create user with default values (profile incomplete)
                cur.execute(
                    """
                    INSERT INTO users
                      (username, role, password_hash, dietary_goal, target_calories, created_at)
                    VALUES (%s, 'user', %s, 'maintain', 2000, %s)
                    RETURNING user_id, username, role;
                    """,
                    (
                        username,
                        generate_password_hash(password),
                        datetime.utcnow(),
                    ),
                )
                user = cur.fetchone()
        # Auto-login after registration
        session["user"] = {"user_id": user["user_id"], "username": user["username"], "role": user["role"]}
        return jsonify(session["user"]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/profile")
@require_auth
def get_profile():
    """Profile for current logged-in user."""
    current = _current_user()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit, created_at
                    FROM users WHERE user_id=%s;
                    """,
                    (current["user_id"],),
                )
                row = cur.fetchone()
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/profile/preview")
@require_auth
def preview_profile_target():
    """Compute preview target_calories for current user without saving."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        dietary_goal = data.get("dietary_goal", "maintain")
        h = data.get("height_value")
        w = data.get("weight_value")
        if h is None or w is None:
            return jsonify({"error": "Please provide height and weight"}), 400
        h_unit = data.get("height_unit", "cm")
        w_unit = data.get("weight_unit", "kg")
        h_cm = _to_cm(float(h), h_unit)
        w_kg = _to_kg(float(w), w_unit)
        preview = calculate_target_calories(h, h_unit, w, w_unit, dietary_goal)
        return jsonify({
            "preview_target_calories": preview,
            "requires_confirmation": _unrealistic(h_cm, w_kg),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.put("/api/profile")
@require_auth
def update_profile():
    """Update own profile (height/weight/dietary_goal). target_calories auto-recalculates."""
    current = _current_user()
    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "No fields to update"}), 400

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, role, dietary_goal, target_calories,
                           height_value, height_unit, weight_value, weight_unit, created_at
                    FROM users WHERE user_id=%s;
                """, (current["user_id"],))
                old_row = cur.fetchone()
        if old_row is None:
            return jsonify({"error": "Not found"}), 404

        new_row = dict(old_row)
        for k in ["dietary_goal", "height_value", "height_unit", "weight_value", "weight_unit"]:
            if k in data and data[k] is not None:
                new_row[k] = data[k]

        # Require height & weight
        if not new_row.get("height_value") or not new_row.get("weight_value"):
            return jsonify({"error": "Please enter both height and weight to update your goal."}), 400

        h_cm = _to_cm(float(new_row["height_value"]), new_row.get("height_unit","cm"))
        w_kg = _to_kg(float(new_row["weight_value"]), new_row.get("weight_unit","kg"))
        if _unrealistic(h_cm, w_kg) and not data.get("confirm_unrealistic"):
            return jsonify({
                "error": "Your height/weight look unusual. Please confirm to continue.",
                "requires_confirmation": True,
                "preview_target_calories": calculate_target_calories(new_row["height_value"], new_row.get("height_unit","cm"), new_row["weight_value"], new_row.get("weight_unit","kg"), new_row.get("dietary_goal","maintain")),
            }), 400

        new_row["target_calories"] = calculate_target_calories(
            new_row["height_value"], new_row.get("height_unit","cm"),
            new_row["weight_value"], new_row.get("weight_unit","kg"),
            new_row.get("dietary_goal","maintain"),
        )

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET dietary_goal=%s, target_calories=%s,
                        height_value=%s, height_unit=%s, weight_value=%s, weight_unit=%s
                    WHERE user_id=%s
                    RETURNING user_id, username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit, created_at;
                    """,
                    (
                        new_row.get("dietary_goal"),
                        new_row.get("target_calories"),
                        new_row.get("height_value"),
                        new_row.get("height_unit"),
                        new_row.get("weight_value"),
                        new_row.get("weight_unit"),
                        current["user_id"],
                    ),
                )
                row = cur.fetchone()

        _audit_profile_change(current["user_id"], current, old_row, row)
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/profile/complete")
@require_auth
def complete_profile():
    """
    Complete user profile during onboarding.
    Required: height_value, height_unit, weight_value, weight_unit, dietary_goal
    Calculates and saves target_calories.
    """
    current = _current_user()
    data = request.get_json(force=True, silent=True) or {}
    
    required = ("height_value", "height_unit", "weight_value", "weight_unit", "dietary_goal")
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    
    try:
        height_value = float(data["height_value"])
        weight_value = float(data["weight_value"])
        height_unit = data["height_unit"]
        weight_unit = data["weight_unit"]
        dietary_goal = data["dietary_goal"]
        
        # Validate units
        if height_unit not in ["cm", "in"]:
            return jsonify({"error": "height_unit must be 'cm' or 'in'"}), 400
        if weight_unit not in ["kg", "lb"]:
            return jsonify({"error": "weight_unit must be 'kg' or 'lb'"}), 400
        if dietary_goal not in ["weight_gain", "weight_loss", "maintain", "eat_healthy"]:
            return jsonify({"error": "Invalid dietary_goal"}), 400
        
        # Check for unrealistic values
        h_cm = _to_cm(height_value, height_unit)
        w_kg = _to_kg(weight_value, weight_unit)
        if _unrealistic(h_cm, w_kg) and not data.get("confirm_unrealistic"):
            return jsonify({
                "error": "Your height/weight look unusual. Please confirm to continue.",
                "requires_confirmation": True,
                "preview_target_calories": calculate_target_calories(height_value, height_unit, weight_value, weight_unit, dietary_goal),
            }), 400
        
        # Calculate target calories
        target_calories = calculate_target_calories(height_value, height_unit, weight_value, weight_unit, dietary_goal)
        
        # Get old values for audit (before update)
        old_row = None
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT height_value, height_unit, weight_value, weight_unit, dietary_goal, target_calories FROM users WHERE user_id=%s;",
                        (current["user_id"],)
                    )
                    old_row = cur.fetchone()
        except Exception:
            pass  # Don't fail if we can't get old values
        
        # Update user profile
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET height_value=%s, height_unit=%s, weight_value=%s, weight_unit=%s,
                        dietary_goal=%s, target_calories=%s
                    WHERE user_id=%s
                    RETURNING user_id, username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit, created_at;
                    """,
                    (height_value, height_unit, weight_value, weight_unit, dietary_goal, target_calories, current["user_id"]),
                )
                row = cur.fetchone()
        
        # Audit the change
        if old_row:
            try:
                _audit_profile_change(current["user_id"], current, old_row, row)
            except Exception:
                pass  # Don't fail if audit fails
        
        return jsonify({**row, "profile_complete": True})
    except ValueError:
        return jsonify({"error": "height_value and weight_value must be valid numbers"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# HEALTH / INFO
# ============================================================================

@app.get("/")
def root():
    # Simple landing so "/" doesn't 403 if you visit http://127.0.0.1:5000
    return "NutriScore+ API is running. Try /api/health", 200

@app.get("/api/health")
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok;")
                row = cur.fetchone()
        return jsonify({"status": "ok", "db": bool(row["ok"])})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_health_score(calories, protein, fiber, sugars):
    """
    Calculate health score: 70 + 50 * (Protein/Calories) + 5 * Fiber - 2.5 * Sugars
    Clamped to 0-100 range.
    """
    if calories <= 0:
        return 0
    protein_score = (protein / calories) * 50 if calories > 0 else 0
    fiber_score = fiber * 5
    sugar_penalty = sugars * 2.5
    score = 70 + protein_score + fiber_score - sugar_penalty
    return max(0, min(100, round(score, 2)))

def _to_cm(height_value: float, height_unit: str) -> float:
    return float(height_value) * 2.54 if height_unit == "in" else float(height_value)

def _to_kg(weight_value: float, weight_unit: str) -> float:
    return float(weight_value) * 0.45359237 if weight_unit == "lb" else float(weight_value)

def calculate_target_calories(height_value, height_unit, weight_value, weight_unit, dietary_goal):
    """
    Baseline calories derived from height+weight, then goal multiplier applied.
    - weight_loss: 0.80
    - maintain/eat_healthy: 1.00
    - weight_gain: 1.15
    Rounded to nearest 10 and clamped to [1200, 4000].
    """
    h_cm = _to_cm(float(height_value), height_unit)
    w_kg = _to_kg(float(weight_value), weight_unit)

    # Stable baseline (simple, consistent)
    baseline = (22.0 * w_kg) + (6.0 * h_cm)

    multipliers = {
        "weight_loss": 0.80,
        "maintain": 1.00,
        "eat_healthy": 1.00,
        "weight_gain": 1.15,
    }
    mult = multipliers.get(dietary_goal, 1.00)
    raw = baseline * mult

    # Round to nearest 10
    rounded = int(round(raw / 10.0) * 10)
    return max(1200, min(4000, rounded))

def _unrealistic(height_cm: float, weight_kg: float) -> bool:
    return height_cm < 100 or height_cm > 250 or weight_kg < 30 or weight_kg > 300

def _audit_profile_change(target_user_id: int, changed_by: dict, old_row: dict, new_row: dict):
    changed = {}
    for k in ["height_value", "height_unit", "weight_value", "weight_unit", "dietary_goal", "target_calories"]:
        if str(old_row.get(k)) != str(new_row.get(k)):
            changed[k] = {"from": old_row.get(k), "to": new_row.get(k)}
    if not changed:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_profile_changes (user_id, changed_by_user_id, changed_by_role, changed_fields, changed_at)
                VALUES (%s, %s, %s, %s::jsonb, %s);
                """,
                (
                    target_user_id,
                    changed_by.get("user_id"),
                    changed_by.get("role"),
                    __import__("json").dumps(changed),
                    datetime.utcnow(),
                ),
            )

# ============================================================================
# FOOD ITEMS CRUD
# ============================================================================

@app.get("/api/foods")
@require_auth
def list_foods():
    """
    Get list of food items with optional search filter.
    Query params: search (food name pattern), limit, offset
    """
    try:
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        with get_conn() as conn:
            # Check if created_by_user_id column exists (for backward compatibility)
            has_ownership = _column_exists(conn, "food_items", "created_by_user_id")
            ownership_col = ", created_by_user_id" if has_ownership else ""
            
            with conn.cursor() as cur:
                query = f"SELECT food_id, food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at{ownership_col} FROM food_items WHERE 1=1"
                params = []
                
                if search:
                    # Search by both food_name and food_id (if search is numeric)
                    search_conditions = ["food_name ILIKE %s"]
                    params.append(f"%{search}%")
                    
                    # If search term is numeric, also search by food_id
                    try:
                        food_id_search = int(search)
                        search_conditions.append("food_id = %s")
                        params.append(food_id_search)
                    except ValueError:
                        pass  # Not numeric, only search by name
                    
                    query += " AND (" + " OR ".join(search_conditions) + ")"
                
                query += " ORDER BY food_name LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                # Add null created_by_user_id for backward compatibility if column doesn't exist
                if not has_ownership:
                    for row in rows:
                        row["created_by_user_id"] = None
                        
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/foods")
@require_auth
def create_food():
    """
    Create a new food item.
    Required: food_name, calories, protein, carbs, fat, fiber, sugars
    Optional: nutrition_density
    Stores created_by_user_id from current session.
    """
    current = _current_user()
    data = request.get_json(force=True, silent=True) or {}
    required = ("food_name", "calories", "protein", "carbs", "fat", "fiber", "sugars")
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    
    try:
        with get_conn() as conn:
            # Check if created_by_user_id column exists (for backward compatibility)
            has_ownership = _column_exists(conn, "food_items", "created_by_user_id")
            
            with conn.cursor() as cur:
                if has_ownership:
                    cur.execute(
                        """
                        INSERT INTO food_items 
                        (food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at, created_by_user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING food_id, food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at, created_by_user_id;
                        """,
                        (
                            data["food_name"],
                            data["calories"],
                            data["protein"],
                            data["carbs"],
                            data["fat"],
                            data["fiber"],
                            data["sugars"],
                            data.get("nutrition_density", 0),
                            datetime.utcnow(),
                            current["user_id"],
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO food_items 
                        (food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING food_id, food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at;
                        """,
                        (
                            data["food_name"],
                            data["calories"],
                            data["protein"],
                            data["carbs"],
                            data["fat"],
                            data["fiber"],
                            data["sugars"],
                            data.get("nutrition_density", 0),
                            datetime.utcnow(),
                        ),
                    )
                new_row = cur.fetchone()
                if not has_ownership:
                    new_row["created_by_user_id"] = None
        return jsonify(new_row), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/foods/<int:food_id>")
@require_auth
def get_food(food_id: int):
    """Get a single food item by ID."""
    try:
        with get_conn() as conn:
            # Check if created_by_user_id column exists (for backward compatibility)
            has_ownership = _column_exists(conn, "food_items", "created_by_user_id")
            ownership_col = ", created_by_user_id" if has_ownership else ""
            
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT food_id, food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at{ownership_col} 
                    FROM food_items WHERE food_id = %s;
                    """,
                    (food_id,),
                )
                row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Not found"}), 404
        if not has_ownership:
            row["created_by_user_id"] = None
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.put("/api/foods/<int:food_id>")
@require_auth
def update_food(food_id: int):
    """
    Update a food item. All fields optional.
    Users can only update their own food items. Admins can update any food item.
    """
    current = _current_user()
    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "No fields to update"}), 400
    
    try:
        with get_conn() as conn:
            # Check if created_by_user_id column exists (for backward compatibility)
            has_ownership = _column_exists(conn, "food_items", "created_by_user_id")
            
            with conn.cursor() as cur:
                # First, check if food exists and ownership (if column exists)
                if has_ownership:
                    cur.execute(
                        "SELECT created_by_user_id FROM food_items WHERE food_id = %s",
                        (food_id,)
                    )
                    food = cur.fetchone()
                    if food is None:
                        return jsonify({"error": "Not found"}), 404
                    
                    # Check permission: user must own the food OR be admin
                    if current["role"] != "admin" and food["created_by_user_id"] != current["user_id"]:
                        return jsonify({"error": "You can only edit food items you created"}), 403
                else:
                    # If column doesn't exist, check if food exists
                    cur.execute(
                        "SELECT food_id FROM food_items WHERE food_id = %s",
                        (food_id,)
                    )
                    if cur.fetchone() is None:
                        return jsonify({"error": "Not found"}), 404
                
                # Build dynamic UPDATE query
                fields = []
                values = []
                for key in ["food_name", "calories", "protein", "carbs", "fat", "fiber", "sugars", "nutrition_density"]:
                    if key in data:
                        fields.append(f"{key} = %s")
                        values.append(data[key])
                
                if not fields:
                    return jsonify({"error": "No valid fields to update"}), 400
                
                values.append(food_id)
                ownership_col = ", created_by_user_id" if has_ownership else ""
                query = f"UPDATE food_items SET {', '.join(fields)} WHERE food_id = %s RETURNING food_id, food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at{ownership_col};"
                
                cur.execute(query, values)
                row = cur.fetchone()
                if not has_ownership:
                    row["created_by_user_id"] = None
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.delete("/api/foods/<int:food_id>")
@require_auth
def delete_food(food_id: int):
    """
    Delete a food item. Will fail if food is referenced in consumption table (RESTRICT).
    Users can only delete their own food items. Admins can delete any food item.
    """
    current = _current_user()
    try:
        with get_conn() as conn:
            # Check if created_by_user_id column exists (for backward compatibility)
            has_ownership = _column_exists(conn, "food_items", "created_by_user_id")
            
            with conn.cursor() as cur:
                # First, check if food exists and ownership (if column exists)
                if has_ownership:
                    cur.execute(
                        "SELECT created_by_user_id FROM food_items WHERE food_id = %s",
                        (food_id,)
                    )
                    food = cur.fetchone()
                    if food is None:
                        return jsonify({"error": "Not found"}), 404
                    
                    # Check permission: user must own the food OR be admin
                    if current["role"] != "admin" and food["created_by_user_id"] != current["user_id"]:
                        return jsonify({"error": "You can only delete food items you created"}), 403
                else:
                    # If column doesn't exist, check if food exists
                    cur.execute(
                        "SELECT food_id FROM food_items WHERE food_id = %s",
                        (food_id,)
                    )
                    if cur.fetchone() is None:
                        return jsonify({"error": "Not found"}), 404
                
                ownership_col = ", created_by_user_id" if has_ownership else ""
                cur.execute(
                    f"DELETE FROM food_items WHERE food_id = %s RETURNING food_id, food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at{ownership_col};",
                    (food_id,)
                )
                row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Not found"}), 404
        if not has_ownership:
            row["created_by_user_id"] = None
        return jsonify({"deleted": row})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# USERS CRUD
# ============================================================================

@app.post("/api/users")
@require_admin
def create_user():
    """
    Create a new user account.
    Required: username
    Required: height_value, height_unit, weight_value, weight_unit
    Optional: dietary_goal (default: maintain), role (default: user)
    target_calories is auto-calculated and saved.
    """
    data = request.get_json(force=True, silent=True) or {}
    if "username" not in data:
        return jsonify({"error": "Missing required field: username"}), 400
    
    try:
        required_profile = ("height_value", "height_unit", "weight_value", "weight_unit")
        missing_profile = [k for k in required_profile if k not in data]
        if missing_profile:
            return jsonify({"error": f"Missing fields: {', '.join(missing_profile)}"}), 400

        dietary_goal = data.get("dietary_goal", "maintain")
        h_cm = _to_cm(float(data["height_value"]), data.get("height_unit", "cm"))
        w_kg = _to_kg(float(data["weight_value"]), data.get("weight_unit", "kg"))
        if _unrealistic(h_cm, w_kg) and not data.get("confirm_unrealistic"):
            return jsonify({
                "error": "Your height/weight look unusual. Please confirm to continue.",
                "requires_confirmation": True,
                "preview_target_calories": calculate_target_calories(data["height_value"], data.get("height_unit","cm"), data["weight_value"], data.get("weight_unit","kg"), dietary_goal),
            }), 400

        target_calories = calculate_target_calories(
            data["height_value"], data.get("height_unit","cm"),
            data["weight_value"], data.get("weight_unit","kg"),
            dietary_goal
        )

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users
                      (username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING user_id, username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit, created_at;
                    """,
                    (
                        data["username"],
                        data.get("role", "user"),
                        dietary_goal,
                        target_calories,
                        data["height_value"],
                        data.get("height_unit", "cm"),
                        data["weight_value"],
                        data.get("weight_unit", "kg"),
                        datetime.utcnow(),
                    ),
                )
                new_row = cur.fetchone()
        return jsonify(new_row), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/users")
@require_admin
def list_users():
    """Get list of all users."""
    # #region agent log
    try:
        import json
        import urllib.request
        log_data = {
            "location": "app.py:list_users",
            "message": "GET /api/users endpoint called",
            "data": {},
            "timestamp": int(datetime.now().timestamp() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "B"
        }
        urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
            data=json.dumps(log_data).encode(), 
            headers={'Content-Type': 'application/json'}).read()
    except: pass
    # #endregion
    try:
        # #region agent log
        try:
            log_data = {
                "location": "app.py:list_users",
                "message": "Before database query",
                "data": {},
                "timestamp": int(datetime.now().timestamp() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B"
            }
            urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
                data=json.dumps(log_data).encode(), 
                headers={'Content-Type': 'application/json'}).read()
        except: pass
        # #endregion
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, role, dietary_goal, target_calories,
                           height_value, height_unit, weight_value, weight_unit, created_at
                    FROM users
                    ORDER BY username;
                """)
                rows = cur.fetchall()
        # #region agent log
        try:
            log_data = {
                "location": "app.py:list_users",
                "message": "Query successful, returning users",
                "data": {"count": len(rows)},
                "timestamp": int(datetime.now().timestamp() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B"
            }
            urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
                data=json.dumps(log_data).encode(), 
                headers={'Content-Type': 'application/json'}).read()
        except: pass
        # #endregion
        return jsonify(rows)
    except Exception as e:
        # #region agent log
        try:
            log_data = {
                "location": "app.py:list_users",
                "message": "Error in list_users",
                "data": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": int(datetime.now().timestamp() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B"
            }
            urllib.request.urlopen('http://127.0.0.1:7242/ingest/dc3212a0-ad75-46bc-aba2-933df0bd5498', 
                data=json.dumps(log_data).encode(), 
                headers={'Content-Type': 'application/json'}).read()
        except: pass
        # #endregion
        return jsonify({"error": str(e), "error_type": type(e).__name__}), 500


@app.get("/api/users/<int:user_id>")
@require_admin
def get_user(user_id: int):
    """
    Get user profile with statistics from user_progress view.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Get user basic info
                cur.execute("""
                    SELECT user_id, username, role, dietary_goal, target_calories,
                           height_value, height_unit, weight_value, weight_unit, created_at
                    FROM users
                    WHERE user_id = %s;
                """, (user_id,))
                user = cur.fetchone()
                
                if user is None:
                    return jsonify({"error": "Not found"}), 404
                
                # Get progress stats
                cur.execute("SELECT * FROM user_progress WHERE user_id = %s;", (user_id,))
                progress = cur.fetchone()
                
                result = dict(user)
                if progress:
                    result["progress"] = dict(progress)
                else:
                    result["progress"] = {
                        "days_tracked": 0,
                        "total_entries": 0,
                        "avg_daily_calories": 0,
                        "avg_daily_protein": 0,
                        "avg_health_score": 0,
                        "last_entry_date": None
                    }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.put("/api/users/<int:user_id>")
@require_admin
def update_user(user_id: int):
    """Admin: update user profile fields; target_calories auto-recalculates when inputs change."""
    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "No fields to update"}), 400
    
    try:
        changed_by = _current_user()

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, role, dietary_goal, target_calories,
                           height_value, height_unit, weight_value, weight_unit, created_at
                    FROM users WHERE user_id=%s;
                """, (user_id,))
                current_row = cur.fetchone()
        if current_row is None:
            return jsonify({"error": "Not found"}), 404

        # Compose new row
        new_row = dict(current_row)
        for k in ["role", "dietary_goal", "height_value", "height_unit", "weight_value", "weight_unit"]:
            if k in data and data[k] is not None:
                new_row[k] = data[k]

        # Recalculate target_calories if any input changed
        inputs_changed = any(k in data for k in ["dietary_goal", "height_value", "height_unit", "weight_value", "weight_unit"])
        if inputs_changed:
            if not new_row.get("height_value") or not new_row.get("weight_value"):
                return jsonify({"error": "Please set height and weight before setting a goal."}), 400
            h_cm = _to_cm(float(new_row["height_value"]), new_row.get("height_unit", "cm"))
            w_kg = _to_kg(float(new_row["weight_value"]), new_row.get("weight_unit", "kg"))
            if _unrealistic(h_cm, w_kg) and not data.get("confirm_unrealistic"):
                return jsonify({
                    "error": "Height/weight look unusual. Please confirm to continue.",
                    "requires_confirmation": True,
                    "preview_target_calories": calculate_target_calories(new_row["height_value"], new_row.get("height_unit","cm"), new_row["weight_value"], new_row.get("weight_unit","kg"), new_row.get("dietary_goal","maintain")),
                }), 400
            new_row["target_calories"] = calculate_target_calories(
                new_row["height_value"], new_row.get("height_unit","cm"),
                new_row["weight_value"], new_row.get("weight_unit","kg"),
                new_row.get("dietary_goal","maintain"),
            )

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET role=%s,
                        dietary_goal=%s,
                        target_calories=%s,
                        height_value=%s,
                        height_unit=%s,
                        weight_value=%s,
                        weight_unit=%s
                    WHERE user_id=%s
                    RETURNING user_id, username, role, dietary_goal, target_calories, height_value, height_unit, weight_value, weight_unit, created_at;
                    """,
                    (
                        new_row.get("role"),
                        new_row.get("dietary_goal"),
                        new_row.get("target_calories"),
                        new_row.get("height_value"),
                        new_row.get("height_unit"),
                        new_row.get("weight_value"),
                        new_row.get("weight_unit"),
                        user_id,
                    ),
                )
                row = cur.fetchone()

        _audit_profile_change(user_id, changed_by, current_row, row)
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.delete("/api/users/<int:user_id>")
@require_admin
def delete_user(user_id: int):
    """
    Delete a user account. CASCADE deletes all consumption entries.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE user_id = %s RETURNING *;", (user_id,))
                row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"deleted": row})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# CONSUMPTION CRUD
# ============================================================================

@app.post("/api/consumption")
@require_auth
def create_consumption():
    """
    Log a food consumption entry.
    Required: user_id, food_id, date, portion_size (default: 1.0)
    Optional: meal_type
    Calculates: calories, protein, carbs, fat, fiber, sugars, health_score
    """
    data = request.get_json(force=True, silent=True) or {}
    required = ("food_id", "date")
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    
    try:
        current = _current_user()
        # For normal users, force user_id from session (ignore any client-supplied user_id)
        if current["role"] == "admin":
            if "user_id" not in data:
                return jsonify({"error": "Missing field: user_id"}), 400
            user_id = int(data["user_id"])
        else:
            user_id = int(current["user_id"])
        portion_size = float(data.get("portion_size", 1.0))
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Get food item to calculate nutrition values
                cur.execute("SELECT * FROM food_items WHERE food_id = %s;", (data["food_id"],))
                food = cur.fetchone()
                if food is None:
                    return jsonify({"error": "Food item not found"}), 404
                
                # Calculate nutrition values based on portion size
                calories = float(food["calories"]) * portion_size
                protein = float(food["protein"]) * portion_size
                carbs = float(food["carbs"]) * portion_size
                fat = float(food["fat"]) * portion_size
                fiber = float(food["fiber"]) * portion_size
                sugars = float(food["sugars"]) * portion_size
                
                # Calculate health score
                health_score = calculate_health_score(calories, protein, fiber, sugars)
                
                # Insert consumption entry
                cur.execute(
                    """
                    INSERT INTO consumption 
                    (user_id, food_id, date, portion_size, calories, protein, carbs, fat, fiber, sugars, health_score, meal_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *;
                    """,
                    (
                        user_id,
                        data["food_id"],
                        data["date"],
                        portion_size,
                        calories,
                        protein,
                        carbs,
                        fat,
                        fiber,
                        sugars,
                        health_score,
                        data.get("meal_type"),
                        datetime.utcnow(),
                    ),
                )
                new_row = cur.fetchone()
        return jsonify(new_row), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/consumption")
@require_auth
def list_consumption():
    """
    Get consumption entries with filters.
    Query params: user_id (required), date, meal_type, limit, offset
    """
    try:
        current = _current_user()
        if current["role"] == "admin":
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({"error": "user_id query parameter is required for admin"}), 400
        else:
            user_id = str(current["user_id"])
        
        date = request.args.get('date')
        meal_type = request.args.get('meal_type')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT c.*, f.food_id, f.food_name
                    FROM consumption c
                    JOIN food_items f ON c.food_id = f.food_id
                    WHERE c.user_id = %s
                """
                params = [user_id]
                
                if date:
                    query += " AND c.date = %s"
                    params.append(date)
                
                if meal_type:
                    query += " AND c.meal_type = %s"
                    params.append(meal_type)
                
                query += " ORDER BY c.date DESC, c.created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/consumption/<int:entry_id>")
@require_auth
def get_consumption(entry_id: int):
    """Get a single consumption entry by ID."""
    try:
        current = _current_user()
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.*, f.food_id, f.food_name
                    FROM consumption c
                    JOIN food_items f ON c.food_id = f.food_id
                    WHERE c.entry_id = %s;
                    """,
                    (entry_id,),
                )
                row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Not found"}), 404
        if current["role"] != "admin" and int(row["user_id"]) != int(current["user_id"]):
            return jsonify({"error": "You don't have permission"}), 403
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.put("/api/consumption/<int:entry_id>")
@require_auth
def update_consumption(entry_id: int):
    """
    Update a consumption entry. Can update portion_size, date, or meal_type.
    If portion_size changes, nutrition values and health_score are recalculated.
    """
    data = request.get_json(force=True, silent=True) or {}
    if not data:
        return jsonify({"error": "No fields to update"}), 400
    
    try:
        current_user = _current_user()
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Get current entry
                cur.execute("SELECT * FROM consumption WHERE entry_id = %s;", (entry_id,))
                entry = cur.fetchone()
                if entry is None:
                    return jsonify({"error": "Not found"}), 404
                if current_user["role"] != "admin" and int(entry["user_id"]) != int(current_user["user_id"]):
                    return jsonify({"error": "You don't have permission"}), 403
                
                # If portion_size is being updated, recalculate nutrition
                if "portion_size" in data:
                    cur.execute("SELECT * FROM food_items WHERE food_id = %s;", (entry["food_id"],))
                    food = cur.fetchone()
                    portion_size = float(data["portion_size"])
                    
                    calories = float(food["calories"]) * portion_size
                    protein = float(food["protein"]) * portion_size
                    carbs = float(food["carbs"]) * portion_size
                    fat = float(food["fat"]) * portion_size
                    fiber = float(food["fiber"]) * portion_size
                    sugars = float(food["sugars"]) * portion_size
                    health_score = calculate_health_score(calories, protein, fiber, sugars)
                    
                    data["calories"] = calories
                    data["protein"] = protein
                    data["carbs"] = carbs
                    data["fat"] = fat
                    data["fiber"] = fiber
                    data["sugars"] = sugars
                    data["health_score"] = health_score
                
                # Build update query
                fields = []
                values = []
                for key in ["date", "portion_size", "calories", "protein", "carbs", "fat", "fiber", "sugars", "health_score", "meal_type"]:
                    if key in data:
                        fields.append(f"{key} = %s")
                        values.append(data[key])
                
                if not fields:
                    return jsonify({"error": "No valid fields to update"}), 400
                
                values.append(entry_id)
                query = f"UPDATE consumption SET {', '.join(fields)} WHERE entry_id = %s RETURNING *;"
                
                cur.execute(query, values)
                row = cur.fetchone()
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.delete("/api/consumption/<int:entry_id>")
@require_auth
def delete_consumption(entry_id: int):
    """Delete a consumption entry."""
    try:
        current_user = _current_user()
        # Load entry first for authz
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM consumption WHERE entry_id = %s;", (entry_id,))
                entry = cur.fetchone()
                if entry is None:
                    return jsonify({"error": "Not found"}), 404
                if current_user["role"] != "admin" and int(entry["user_id"]) != int(current_user["user_id"]):
                    return jsonify({"error": "You don't have permission"}), 403
                cur.execute("DELETE FROM consumption WHERE entry_id = %s RETURNING *;", (entry_id,))
                row = cur.fetchone()
        return jsonify({"deleted": row})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ANALYTICAL ENDPOINTS
# ============================================================================

@app.get("/api/analytics/food-nutrition")
@require_auth
def get_food_nutrition():
    """
    Average nutrition by food (for bar chart).
    Returns average calories, protein, carbs, fat per food item.
    """
    try:
        limit = int(request.args.get('limit', 20))
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        food_id,
                        food_name,
                        ROUND(calories::NUMERIC, 2) as avg_calories,
                        ROUND(protein::NUMERIC, 2) as avg_protein,
                        ROUND(carbs::NUMERIC, 2) as avg_carbs,
                        ROUND(fat::NUMERIC, 2) as avg_fat
                    FROM food_items
                    ORDER BY food_name
                    LIMIT %s;
                """, (limit,))
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/analytics/top-foods")
@require_auth
def get_top_foods():
    """
    Top 20 most nutritious foods based on health score and nutrition density.
    Query params: limit (default: 20)
    """
    try:
        limit = int(request.args.get('limit', 20))
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        food_id,
                        food_name,
                        calories,
                        protein,
                        fiber,
                        sugars,
                        nutrition_density
                    FROM food_items
                    ORDER BY nutrition_density DESC, food_name ASC
                    LIMIT %s;
                """, (limit,))
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/analytics/user-progress/<int:user_id>")
@require_auth
def get_user_progress(user_id: int):
    """
    User progress over time (for line chart).
    Returns daily summary data for the user.
    Query params: days (number of days back, default: 30)
    """
    try:
        current = _current_user()
        if current["role"] != "admin":
            user_id = int(current["user_id"])
        days = int(request.args.get('days', 30))
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        date,
                        meals_count,
                        total_calories,
                        total_protein,
                        total_carbs,
                        total_fat,
                        total_fiber,
                        total_sugars,
                        avg_health_score,
                        target_calories,
                        (total_calories - target_calories) as calorie_difference
                    FROM daily_summary
                    WHERE user_id = %s
                        AND date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY date ASC;
                """, (user_id, days))
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/analytics/daily-health-score/<int:user_id>")
@require_auth
def get_daily_health_score(user_id: int):
    """
    Daily health score for a user (for line chart).
    Query params: days (default: 30)
    """
    try:
        current = _current_user()
        if current["role"] != "admin":
            user_id = int(current["user_id"])
        days = int(request.args.get("days", 30))
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT date, daily_health_score, entries_count
                    FROM daily_health_score
                    WHERE user_id = %s
                      AND date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY date ASC;
                    """,
                    (user_id, days),
                )
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/analytics/overall-health-score/<int:user_id>")
@require_auth
def get_overall_health_score(user_id: int):
    """
    Overall (lifetime) health score for a user.
    """
    try:
        current = _current_user()
        if current["role"] != "admin":
            user_id = int(current["user_id"])
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, overall_health_score, entries_count, days_tracked
                    FROM overall_health_score
                    WHERE user_id = %s;
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Not found"}), 404
        return jsonify(row)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/analytics/meal-distribution")
@require_auth
def get_meal_distribution():
    """
    Meal type distribution analysis (for pie chart).
    Query params: user_id (required), days (default: 30)
    """
    try:
        current = _current_user()
        if current["role"] == "admin":
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({"error": "user_id query parameter is required for admin"}), 400
        else:
            user_id = str(current["user_id"])
        
        days = int(request.args.get('days', 30))
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        meal_type,
                        COUNT(*) as count,
                        ROUND(SUM(calories)::NUMERIC, 2) as total_calories,
                        ROUND(AVG(health_score)::NUMERIC, 0) as avg_health_score
                    FROM consumption
                    WHERE user_id = %s
                        AND date >= CURRENT_DATE - INTERVAL '%s days'
                        AND meal_type IS NOT NULL
                    GROUP BY meal_type
                    ORDER BY count DESC;
                """, (user_id, days))
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/analytics/popular-foods")
@require_auth
def get_popular_foods():
    """
    Most consumed foods (popularity tracking).
    Query params: user_id (optional), limit (default: 20)
    """
    try:
        current = _current_user()
        limit = int(request.args.get('limit', 20))
        if current["role"] == "admin":
            user_id = request.args.get('user_id')
        else:
            user_id = str(current["user_id"])
        
        with get_conn() as conn:
            with conn.cursor() as cur:
                if user_id:
                    # User-specific popular foods
                    cur.execute("""
                        SELECT 
                            f.food_id,
                            f.food_name,
                            COUNT(c.entry_id) as times_consumed,
                            ROUND(AVG(c.health_score)::NUMERIC, 0) as avg_health_score,
                            ROUND(SUM(c.calories)::NUMERIC, 2) as total_calories_consumed
                        FROM food_items f
                        JOIN consumption c ON f.food_id = c.food_id
                        WHERE c.user_id = %s
                        GROUP BY f.food_id, f.food_name
                        ORDER BY times_consumed DESC
                        LIMIT %s;
                    """, (user_id, limit))
                else:
                    # Global popular foods from view
                    cur.execute("""
                        SELECT * FROM food_popularity
                        WHERE times_consumed > 0
                        ORDER BY times_consumed DESC
                        LIMIT %s;
                    """, (limit,))
                rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("  NutriScore+ Flask API Server")
    print("="*60)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}")
    print("Starting server on http://127.0.0.1:5000")
    print("="*60)
    app.run(debug=True, port=5000)