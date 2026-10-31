from pathlib import Path
import sqlite3
import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent
INSTANCE = ROOT / "instance"
MODEL_PATH = INSTANCE / "house_price_model.joblib"
DB_PATH = INSTANCE / "houses.db"

app = Flask(__name__)


def load_bundle():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def make_features(payload):
    sold_on = pd.to_datetime(payload.get("sold_on") or pd.Timestamp.today().strftime("%Y-%m-%d"), errors="coerce")
    if pd.isna(sold_on):
        raise ValueError("sold_on must be a valid date such as 2026-10-29")
    return pd.DataFrame([{
        "city": str(payload.get("city", "Hyderabad")).strip().title(),
        "locality": str(payload.get("locality", "Unknown")).strip() or "Unknown",
        "area_sqft": float(payload["area_sqft"]),
        "bedrooms": float(payload["bedrooms"]),
        "bathrooms": float(payload["bathrooms"]),
        "age_years": float(payload.get("age_years", 5)),
        "floor": float(payload.get("floor", 0)),
        "parking": str(payload.get("parking", "none")).strip().lower(),
        "furnishing": str(payload.get("furnishing", "unfurnished")).strip().lower(),
        "sale_month": int(sold_on.month),
        "sale_year": int(sold_on.year)
    }])


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_ready": MODEL_PATH.exists(), "database_ready": DB_PATH.exists()})


@app.route("/api/localities", methods=["GET"])
def localities():
    """Return only locality names present in the cleaned dataset for the selected city."""
    city = (request.args.get("city") or "").strip().lower()
    city_aliases = {
        "hyd": "Hyderabad", "hyderabad": "Hyderabad",
        "blr": "Bengaluru", "bangalore": "Bengaluru", "bengaluru": "Bengaluru",
        "vijayawada": "Vijayawada", "vijay wada": "Vijayawada"
    }
    normalized_city = city_aliases.get(city, city.title())
    if not DB_PATH.exists():
        return jsonify({"localities": [], "error": "Database not found. Run train_model.py first."}), 503
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT DISTINCT locality FROM houses WHERE city = ? AND locality IS NOT NULL "
            "AND TRIM(locality) <> '' AND LOWER(locality) <> 'unknown' ORDER BY locality COLLATE NOCASE",
            (normalized_city,)
        ).fetchall()
    return jsonify({"localities": [row[0] for row in rows]})


@app.route("/predict", methods=["POST"])
def predict():
    bundle = load_bundle()
    if bundle is None:
        return jsonify({"error": "Model not found. Run `python train_model.py` first."}), 503
    payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    payload = payload or {}
    try:
        for required in ["area_sqft", "bedrooms", "bathrooms"]:
            if payload.get(required) in (None, ""):
                raise ValueError(f"{required} is required")
        features = make_features(payload)
        price = float(bundle["model"].predict(features)[0])
        return jsonify({
            "predicted_price_inr": round(price, 2),
            "predicted_price_lakh": round(price / 100000, 2),
            "currency": "INR",
            "note": "Estimate based on historical data; not a formal property valuation."
        })
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/summary", methods=["GET"])
def summary():
    if not DB_PATH.exists():
        return jsonify({"error": "Database not found. Run train_model.py first."}), 503
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        by_city = [dict(row) for row in conn.execute("""
            SELECT city, COUNT(*) AS sales_count,
                   ROUND(AVG(sale_price_inr), 0) AS average_price_inr
            FROM houses GROUP BY city ORDER BY average_price_inr DESC
        """)]
        count = conn.execute("SELECT COUNT(*) FROM houses").fetchone()[0]
    return jsonify({"clean_sales_count": count, "average_price_by_city": by_city})


if __name__ == "__main__":
    if not MODEL_PATH.exists():
        print("Model not found. Run `python train_model.py` first.")
    app.run(host="127.0.0.1", port=5000, debug=True)
