import pandas as pd
import numpy as np
from faker import Faker
import random

fake = Faker()

NUM_CUSTOMERS = 5000
NUM_MERCHANTS = 500


# -------------------------
# CUSTOMER GENERATOR
# -------------------------

def generate_customers(n):
    customers = []

    segments = ["Regular", "Gold", "Platinum", "Corporate"]
    segment_weights = [0.60, 0.20, 0.10, 0.10]

    cities = [
        "Pune", "Mumbai", "Delhi", "Bangalore",
        "Hyderabad", "Chennai", "Kolkata", "Ahmedabad"
    ]

    for i in range(n):
        segment = random.choices(
            segments,
            weights=segment_weights
        )[0]

        annual_income = random.randint(200000, 5000000)

        customers.append({
            "customer_id": f"CUST_{i+1:05d}",
            "age": random.randint(18, 70),
            "city": random.choice(cities),
            "country": "India",
            "annual_income": annual_income,
            "customer_segment": segment,
            "account_age_days": random.randint(30, 3000),
            "trusted_device_id": f"DEV_{random.randint(1, 10000):05d}",
            "avg_transaction_amount": round(
                random.uniform(500, 10000), 2
            )
        })

    return pd.DataFrame(customers)


# -------------------------
# MERCHANT GENERATOR
# -------------------------

def generate_merchants(n):
    merchants = []

    categories = [
        "Grocery",
        "Restaurant",
        "Fuel",
        "Electronics",
        "Travel",
        "Hotel",
        "Jewellery",
        "Pharmacy",
        "ATM",
        "Shopping"
    ]

    risk_levels = ["LOW", "MEDIUM", "HIGH"]

    for i in range(n):

        risk = random.choices(
            risk_levels,
            weights=[0.65, 0.25, 0.10]
        )[0]

        merchants.append({
            "merchant_id": f"MERCH_{i+1:05d}",
            "merchant_name": fake.company(),
            "merchant_category": random.choice(categories),
            "city": random.choice([
                "Pune", "Mumbai", "Delhi",
                "Bangalore", "Hyderabad"
            ]),
            "country": "India",
            "risk_level": risk,
            "blacklisted": random.random() < 0.05
        })

    return pd.DataFrame(merchants)


# -------------------------
# MAIN
# -------------------------

if __name__ == "__main__":

    customers = generate_customers(NUM_CUSTOMERS)
    merchants = generate_merchants(NUM_MERCHANTS)

    customers.to_csv(
        "data/customers.csv",
        index=False
    )

    merchants.to_csv(
        "data/merchants.csv",
        index=False
    )

    print(f"Generated {len(customers)} customers")
    print(f"Generated {len(merchants)} merchants")

    print("\nCustomer sample:")
    print(customers.head())

    print("\nMerchant sample:")
    print(merchants.head())