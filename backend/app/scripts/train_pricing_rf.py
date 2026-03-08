import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import create_engine

from app.core.config import get_settings


QUERY = """
SELECT
    product_id,
    customer_id,
    quantity,
    selling_price,
    discount_percent,
    margin_percent,
    channel
FROM pricing_engine.sales_history
"""


def train_from_db(out_model: str, out_meta: str) -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    df = pd.read_sql(QUERY, engine)

    required = {
        "product_id",
        "customer_id",
        "quantity",
        "selling_price",
        "discount_percent",
        "margin_percent",
        "channel",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns in sales_history query result: {sorted(missing)}")
    if len(df) < 5:
        raise ValueError("Not enough rows in pricing_engine.sales_history. Insert at least 5 rows.")

    encoder = LabelEncoder()
    df["channel_encoded"] = encoder.fit_transform(df["channel"].astype(str))

    features = df[
        [
            "product_id",
            "customer_id",
            "quantity",
            "discount_percent",
            "channel_encoded",
        ]
    ]
    target = df["selling_price"]

    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    mae = float(mean_absolute_error(y_test, predictions))

    model_path = Path(out_model)
    meta_path = Path(out_meta)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "channel_classes": list(encoder.classes_),
        "feature_order": [
            "product_id",
            "customer_id",
            "quantity",
            "discount_percent",
            "channel_encoded",
        ],
    }
    joblib.dump(artifact, model_path)

    meta = {
        "model_type": "RandomForestRegressor",
        "target": "selling_price",
        "mae": round(mae, 4),
        "rows_used": int(len(df)),
        "feature_order": artifact["feature_order"],
        "channel_classes": artifact["channel_classes"],
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Model saved: {model_path}")
    print(f"Metadata saved: {meta_path}")
    print(f"MAE: {mae:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train RandomForest pricing model from PostgreSQL.")
    parser.add_argument("--out-model", default="app/ml/pricing_model.pkl")
    parser.add_argument("--out-meta", default="app/ml/pricing_model_meta.json")
    args = parser.parse_args()
    train_from_db(args.out_model, args.out_meta)

