#!/usr/bin/env python3
"""
Load the 5 FOOD CSVs into the schema table: food_items

- Uses psycopg v3 and pandas
- Reads only DATASET/FOOD-DATA-GROUP1..5.csv
- Cleans/normalizes columns and maps them to:
  food_name, category, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at
- Truncates food_items before loading (toggle TRUNCATE_BEFORE_LOAD)
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import pandas as pd
from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row

# --------------------------- CONFIG ---------------------------

# Folder shown in your screenshots:
DATA_ROOT = Path(__file__).resolve().parent.parent / "FINAL FOOD DATASET"
DATASET_DIR = DATA_ROOT 

TARGET_TABLE = "food_items"
TRUNCATE_BEFORE_LOAD = False  # set False to append instead of wipe

# Health score calculation: 50 + (Protein/Calories) × 10 + (Fiber - Sugars) / 5

# --------------------------- DB SETUP -------------------------

# Load .env from backend directory
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "nutriscore")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def dsn() -> str:
    return f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

def connect():
    return psycopg.connect(dsn(), row_factory=dict_row)

# ------------------------- CSV DISCOVERY ----------------------

def find_food_csvs() -> List[Path]:
    """Return exactly the 5 FOOD CSVs if present."""
    if not DATASET_DIR.exists():
        raise FileNotFoundError(f"DATASET folder not found: {DATASET_DIR}")
    files = []
    for i in range(1, 6):
        p = DATASET_DIR / f"FOOD-DATA-GROUP{i}.csv"
        if p.exists():
            files.append(p)
        else:
            print(f"⚠️  Missing expected file: {p}")
    if not files:
        raise FileNotFoundError("No FOOD-DATA-GROUP*.csv files found.")
    return files

# ----------------------- PREPROCESS + MAP ---------------------

def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Convert to numeric; invalid/empty → 0.0 (keeps CHECK >= 0 happy)."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0)

def build_fooditems_df(frames: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge frames and map CSV columns -> schema columns.
    We try common names from the Kaggle dataset; mapping is case-insensitive.
    """
    df = pd.concat(frames, ignore_index=True)

    # Case-insensitive header map
    lower_map: Dict[str, str] = {c.lower(): c for c in df.columns}

    def pick(*names, default=None):
        """Pick the first existing column by name (case-insensitive)."""
        for n in names:
            if n.lower() in lower_map:
                return df[lower_map[n.lower()]]
        return default

    # Select and rename to schema columns
    # Handle both space-separated and underscore-separated column names
    out = pd.DataFrame({
        "food_name":          pick("food", "food_name", "name"),
        "calories":           pick("caloric value", "caloric_value", "calories"),
        "protein":            pick("protein"),
        "carbs":              pick("carbohydrates", "carbs"),
        "fat":                pick("fat"),
        "fiber":              pick("dietary fiber", "dietary_fiber", "fiber"),
        "sugars":             pick("sugars", "sugar"),
        "nutrition_density":  pick("nutrition density", "nutrition_density"),
    })

    # Strip text fields
    out["food_name"] = out["food_name"].astype("string").str.strip()

    # Drop rows missing required fields (only food_name is required)
    out = out[out["food_name"].notna() & (out["food_name"] != "")]

    # Numerics
    for col in ["calories", "protein", "carbs", "fat", "fiber", "sugars", "nutrition_density"]:
        if col in out.columns:
            out[col] = _coerce_numeric(out[col])
        else:
            out[col] = 0.0  # ensure column exists

    # Timestamp
    out["created_at"] = datetime.utcnow()

    # De-duplicate by food_name to satisfy UNIQUE constraint in schema
    out = out.drop_duplicates(subset=["food_name"], keep="first")

    # Order columns exactly like table (no food_id — SERIAL PK)
    out = out[[
        "food_name", "calories", "protein", "carbs",
        "fat", "fiber", "sugars", "nutrition_density", "created_at"
    ]]
    return out

# --------------------------- LOADERS --------------------------

def truncate_food_items():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE food_items RESTART IDENTITY;")
    print("🧹 Truncated table: food_items (identity reset)")

import tempfile

def insert_food_items(df: pd.DataFrame):
    # Write to a temp CSV and stream it via COPY for maximum speed
    cols = [
        "food_name", "calories", "protein", "carbs",
        "fat", "fiber", "sugars", "nutrition_density", "created_at"
    ]
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", suffix=".csv") as tmp:
        df.to_csv(tmp.name, index=False, header=True)
        copy_sql = """
            COPY food_items (food_name, calories, protein, carbs, fat, fiber, sugars, nutrition_density, created_at)
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',')
        """
        with connect() as conn:
            with open(tmp.name, "r", encoding="utf-8") as f, conn.cursor() as cur:
                # psycopg v3 COPY API
                with cur.copy(copy_sql) as cp:
                    while chunk := f.read(1024 * 1024):
                        cp.write(chunk)
        print(f"✅ Loaded {len(df):,} rows into food_items via COPY")

# ----------------------------- MAIN ---------------------------

def main() -> int:
    print(f"🔎 Looking for FOOD files in: {DATASET_DIR}")
    csvs = find_food_csvs()
    print("• Found:", ", ".join(p.name for p in csvs))

    print("📥 Reading CSVs...")
    frames = [pd.read_csv(p, low_memory=False) for p in csvs]
    print(f"📊 Rows read (raw): {sum(len(f) for f in frames):,}")

    print("🧼 Building dataframe for food_items…")
    df = build_fooditems_df(frames)
    print(f"📦 Clean rows ready: {len(df):,}")

    if TRUNCATE_BEFORE_LOAD:
        truncate_food_items()

    print("⬆️  Loading into database…")
    insert_food_items(df)
    print("🎉 Done.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())