"""Generate sample competitor data CSV for testing the market comparison engine."""
import csv
import os

COMPETITORS = [
    # Water Heaters (matches existing product categories)
    {"competitor_name": "Joven", "product_name": "Joven 830 Water Heater", "category": "water_heater", "price": "289.00", "features": "instant, 3300W", "brand_tier": "mid"},
    {"competitor_name": "Alpha", "product_name": "Alpha IM-9EP", "category": "water_heater", "price": "299.00", "features": "instant, DC pump, 5-year warranty", "brand_tier": "mid"},
    {"competitor_name": "Panasonic", "product_name": "Panasonic DH-3JL3", "category": "water_heater", "price": "359.00", "features": "instant, 3500W, antibacterial", "brand_tier": "premium"},
    {"competitor_name": "Ariston", "product_name": "Ariston Aures SM33", "category": "water_heater", "price": "349.00", "features": "DC pump, 3300W, 10-year tank warranty", "brand_tier": "premium"},

    # Solar Systems
    {"competitor_name": "Solarmate", "product_name": "Solarmate 66G", "category": "solar_system", "price": "2899.00", "features": "66 gallon, evacuated tube", "brand_tier": "budget"},
    {"competitor_name": "Solarmate", "product_name": "Solarmate 80G Premium", "category": "solar_system", "price": "3299.00", "features": "80 gallon, stainless tank", "brand_tier": "mid"},
    {"competitor_name": "Alpha", "product_name": "Alpha Solar 300L", "category": "solar_system", "price": "3599.00", "features": "300L, flat plate, 10-year warranty", "brand_tier": "premium"},

    # Water Pumps
    {"competitor_name": "Grundfos", "product_name": "Grundfos CM Booster", "category": "water_pump", "price": "1199.00", "features": "centrifugal, stainless", "brand_tier": "premium"},
    {"competitor_name": "Wilo", "product_name": "Wilo PB-201SEA", "category": "water_pump", "price": "489.00", "features": "auto booster, compact", "brand_tier": "mid"},
    {"competitor_name": "Panasonic", "product_name": "Panasonic A-130FAX", "category": "water_pump", "price": "399.00", "features": "auto booster, quiet operation", "brand_tier": "mid"},

    # Pipe & Fittings
    {"competitor_name": "Legrand", "product_name": "Legrand CPVC Pipe 1/2", "category": "pipe_fittings", "price": "12.50", "features": "1/2 inch, CPVC, hot water rated", "brand_tier": "premium"},
    {"competitor_name": "Era Piping", "product_name": "Era PVC Pipe 3/4", "category": "pipe_fittings", "price": "8.90", "features": "3/4 inch, PVC, cold water", "brand_tier": "budget"},
]


def main():
    out_path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_competitor_data.csv")
    out_path = os.path.normpath(out_path)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["competitor_name", "product_name", "category", "price", "features", "brand_tier"])
        writer.writeheader()
        writer.writerows(COMPETITORS)

    print(f"Generated {len(COMPETITORS)} competitor rows → {out_path}")


if __name__ == "__main__":
    main()
