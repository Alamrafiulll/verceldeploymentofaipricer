import argparse
import random

import pandas as pd


def generate(rows: int, output: str) -> None:
    records = []
    for _ in range(rows):
        customer_tier_score = random.uniform(0.2, 0.9)
        channel_score = random.uniform(0.2, 0.9)
        category_score = random.uniform(0.2, 0.9)
        quantity = random.randint(1, 300)
        discount_percent = random.uniform(0, 20)
        stock_age_days = random.randint(1, 365)
        stock_on_hand = random.randint(1, 1000)
        days_to_delivery = random.randint(1, 45)
        strategy_score = random.uniform(0.2, 0.9)
        elasticity_score = random.uniform(0.2, 0.9)

        linear = (
            -1.8
            + 0.11 * discount_percent
            + 0.0013 * quantity
            + 0.004 * stock_age_days
            - 0.0007 * stock_on_hand
            - 0.05 * days_to_delivery
            + 0.7 * customer_tier_score
            + 0.5 * channel_score
            + 0.4 * category_score
            + 0.45 * strategy_score
            + 0.25 * elasticity_score
        )
        prob = 1 / (1 + pow(2.71828, -linear))
        won = 1 if random.random() < prob else 0

        records.append(
            {
                "customer_tier_score": customer_tier_score,
                "channel_score": channel_score,
                "category_score": category_score,
                "quantity": quantity,
                "discount_percent": discount_percent,
                "stock_age_days": stock_age_days,
                "stock_on_hand": stock_on_hand,
                "days_to_delivery": days_to_delivery,
                "strategy_score": strategy_score,
                "elasticity_score": elasticity_score,
                "won": won,
            }
        )

    pd.DataFrame(records).to_csv(output, index=False)
    print(f"Synthetic dataset generated at {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic win-rate training data")
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--output", default="app/ml/synthetic_training.csv")
    args = parser.parse_args()

    generate(args.rows, args.output)
