from pathlib import Path
import json
import sqlite3
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "houses.csv"
INSTANCE = ROOT / "instance"
DB_PATH = INSTANCE / "houses.db"
MODEL_PATH = INSTANCE / "house_price_model.joblib"
REPORT_PATH = INSTANCE / "training_report.json"
RANDOM_STATE = 42

FEATURES = [
    "city", "locality", "sold_on", "area_sqft", "bedrooms",
    "bathrooms", "age_years", "floor", "parking", "furnishing"
]
NUMERIC = ["area_sqft", "bedrooms", "bathrooms", "age_years", "floor", "sale_month", "sale_year"]
CATEGORICAL = ["city", "locality", "parking", "furnishing"]


def normalize_city(value):
    if pd.isna(value):
        return np.nan
    value = " ".join(str(value).strip().lower().replace("_", " ").split())
    aliases = {
        "hyd": "Hyderabad", "hyderabad": "Hyderabad", "hyd.": "Hyderabad",
        "blr": "Bengaluru", "bangalore": "Bengaluru", "bengaluru": "Bengaluru",
        "vijayawada": "Vijayawada", "vijay wada": "Vijayawada"
    }
    return aliases.get(value, value.title())


def clean_data(raw):
    initial_rows = len(raw)
    df = raw.copy()
    df = df.drop_duplicates()
    exact_duplicates_removed = initial_rows - len(df)

    required = ["city", "area_sqft", "sale_price_inr"]
    for col in ["area_sqft", "bedrooms", "bathrooms", "age_years", "floor", "price_per_sqft", "sale_price_inr"]:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["city"] = df["city"].map(normalize_city)
    df["locality"] = df["locality"].astype("string").str.strip().replace({"": pd.NA, "nan": pd.NA})
    for col in ["parking", "furnishing"]:
        df[col] = df[col].astype("string").str.strip().str.lower().replace({"": pd.NA, "nan": pd.NA})

    df["sold_on"] = pd.to_datetime(df["sold_on"], errors="coerce")
    # Some records contain prices entered in lakhs rather than rupees.
    # The dataset's valid residential prices are in rupees; values under 100,000
    # are interpreted as lakh-based entries and multiplied by 100,000.
    lakh_price_rows = df["sale_price_inr"].between(1, 99999, inclusive="both")
    df.loc[lakh_price_rows, "sale_price_inr"] *= 100000

    before_validation = len(df)
    df = df.dropna(subset=required)
    df = df[(df["area_sqft"] > 100) & (df["area_sqft"] < 20000)]
    df = df[(df["sale_price_inr"] >= 500000) & (df["sale_price_inr"] <= 200000000)]
    df = df[df["city"].isin(["Hyderabad", "Bengaluru", "Vijayawada"])]
    invalid_rows_removed = before_validation - len(df)

    # Fill categorical gaps with explicit categories and numeric gaps later in pipeline.
    df["locality"] = df["locality"].fillna("Unknown")
    df["parking"] = df["parking"].fillna("unknown").replace({"0": "none"})
    df["furnishing"] = df["furnishing"].fillna("unknown")
    df["bedrooms"] = df["bedrooms"].where(df["bedrooms"].between(0, 20))
    df["bathrooms"] = df["bathrooms"].where(df["bathrooms"].between(0, 20))
    df["age_years"] = df["age_years"].where(df["age_years"].between(0, 200))
    df["floor"] = df["floor"].where(df["floor"].between(0, 200))

    df["sale_month"] = df["sold_on"].dt.month
    df["sale_year"] = df["sold_on"].dt.year
    df["sold_on"] = df["sold_on"].dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["sold_on"])
    df["bedrooms"] = df["bedrooms"].round().astype("Int64")
    df = df.reset_index(drop=True)

    report = {
        "rows_in_source": int(initial_rows),
        "exact_duplicate_rows_removed": int(exact_duplicates_removed),
        "invalid_or_out_of_range_rows_removed": int(invalid_rows_removed),
        "prices_scaled_from_lakhs": int(lakh_price_rows.sum()),
        "rows_after_cleaning": int(len(df)),
        "note": "price_per_sqft was excluded from model features because it is calculated after the sale."
    }
    return df, report


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {DATA_PATH.name}. Copy houses.csv into {ROOT} and rerun."
        )
    INSTANCE.mkdir(exist_ok=True)
    raw = pd.read_csv(DATA_PATH)
    df, cleaning_report = clean_data(raw)
    if len(df) < 30:
        raise ValueError(f"Only {len(df)} usable rows remain; inspect the cleaning rules and source data.")

    # Load cleaned records into SQLite.
    with sqlite3.connect(DB_PATH) as conn:
        df.drop(columns=["sale_month", "sale_year"], errors="ignore").to_sql(
            "houses", conn, if_exists="replace", index=False
        )
        conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))

    # Use sale date-derived month/year, but never use the sale price or price_per_sqft as inputs.
    X = df[FEATURES].copy()
    X["sale_month"] = df["sale_month"]
    X["sale_year"] = df["sale_year"]
    y = df["sale_price_inr"].astype(float)

    numeric_features = ["area_sqft", "bedrooms", "bathrooms", "age_years", "floor", "sale_month", "sale_year"]
    categorical_features = ["city", "locality", "parking", "furnishing"]
    X = X.drop(columns=["sold_on"])

    # Split by property so repeat sales of one house don't appear on both sides.
    groups = df["property_id"].fillna(df["listing_id"]).astype(str)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=RANDOM_STATE)
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler())
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])
    preprocess = ColumnTransformer([
        ("num", numeric_pipe, numeric_features),
        ("cat", categorical_pipe, categorical_features)
    ])
    model = Pipeline([
        ("preprocess", preprocess),
        ("regressor", RandomForestRegressor(
            n_estimators=250, min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=-1
        ))
    ])
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    predictions = model.predict(X.iloc[test_idx])
    mae = float(mean_absolute_error(y.iloc[test_idx], predictions))
    rmse = float(np.sqrt(mean_squared_error(y.iloc[test_idx], predictions)))
    r2 = float(r2_score(y.iloc[test_idx], predictions))

    joblib.dump({"model": model, "features": list(X.columns)}, MODEL_PATH)
    report = {
        **cleaning_report,
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "metrics": {"mae_inr": round(mae, 2), "rmse_inr": round(rmse, 2), "r2": round(r2, 4)},
        "model": "RandomForestRegressor",
        "split_method": "GroupShuffleSplit grouped by property_id",
        "features_used": list(X.columns),
        "target": "sale_price_inr"
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nDatabase: {DB_PATH}")
    print(f"Model:    {MODEL_PATH}")
    print(f"Report:   {REPORT_PATH}")


if __name__ == "__main__":
    main()
