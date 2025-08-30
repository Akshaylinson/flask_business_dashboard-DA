import os
from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd

# -----------------------------
# Paths & App
# -----------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_NAME = "business_owners_cache.csv"
DATA_PATH = os.path.join(APP_DIR, CSV_NAME)

app = Flask(__name__)

# -----------------------------
# Data Loading
# -----------------------------
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"{CSV_NAME} not found in {APP_DIR}. "
        "Export your Excel to this CSV (same columns) or regenerate the cache."
    )

df = pd.read_csv(DATA_PATH)

# Ensure required columns
EXPECTED_COLS = ['Business Name', 'Owner Name', 'City', 'State', 'Mobile Number']
missing = [c for c in EXPECTED_COLS if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing expected columns: {missing}")

def clean_df(d: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: strip whitespace and normalize blank values."""
    out = d.copy()
    for c in EXPECTED_COLS:
        out[c] = out[c].astype(str).str.strip()
    out = out.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return out

df = clean_df(df)

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/summary")
def api_summary():
    d = df
    total = int(len(d))
    unique_states = int(d['State'].nunique(dropna=True))
    unique_cities = int(d['City'].nunique(dropna=True))
    owners = int(d['Owner Name'].nunique(dropna=True))

    phones_present = int(d['Mobile Number'].notna().sum())
    phones_missing = int(d['Mobile Number'].isna().sum())

    # Rough duplicate heuristic: same Business Name + City + State
    dup_count = int(d.duplicated(subset=['Business Name', 'City', 'State'], keep=False).sum())

    return jsonify({
        "total_records": total,
        "unique_states": unique_states,
        "unique_cities": unique_cities,
        "unique_owners": owners,
        "phones_present": phones_present,
        "phones_missing": phones_missing,
        "potential_duplicates": dup_count
    })

@app.route("/api/top-states")
def api_top_states():
    limit = int(request.args.get("limit", 10))
    counts = (
        df.groupby('State', dropna=False)
          .size()
          .reset_index(name='count')
          .sort_values('count', ascending=False)
          .head(limit)
    )
    counts['State'] = counts['State'].fillna('Unknown')
    return jsonify(counts.to_dict(orient='records'))

@app.route("/api/top-cities")
def api_top_cities():
    limit = int(request.args.get("limit", 20))
    counts = (
        df.groupby(['State', 'City'], dropna=False)
          .size()
          .reset_index(name='count')
          .sort_values('count', ascending=False)
          .head(limit)
    )
    counts['State'] = counts['State'].fillna('Unknown')
    counts['City'] = counts['City'].fillna('Unknown')
    return jsonify(counts.to_dict(orient='records'))

@app.route("/api/table")
def api_table():
    """
    Server-side endpoint for DataTables.
    Accepts:
      - start: offset
      - length: page size
      - search[value]: search term
    """
    start = int(request.args.get('start', 0))
    length = int(request.args.get('length', 25))
    search = request.args.get('search[value]', '').strip().lower()

    filtered = df
    if search:
        mask = (
            df['Business Name'].astype(str).str.lower().str.contains(search, na=False) |
            df['Owner Name'].astype(str).str.lower().str.contains(search, na=False) |
            df['City'].astype(str).str.lower().str.contains(search, na=False) |
            df['State'].astype(str).str.lower().str.contains(search, na=False) |
            df['Mobile Number'].astype(str).str.lower().str.contains(search, na=False)
        )
        filtered = df[mask]

    total_records = len(df)
    total_filtered = len(filtered)

    page = filtered.iloc[start:start + length].fillna("")
    data = page.to_dict(orient='records')

    return jsonify({
        "recordsTotal": total_records,
        "recordsFiltered": total_filtered,
        "data": data
    })

@app.route("/download/csv")
def download_csv():
    return send_file(DATA_PATH, as_attachment=True, download_name="business_owners.csv")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Use debug=False for production
    app.run(host="0.0.0.0", port=5000, debug=True)
