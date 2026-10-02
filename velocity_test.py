import json
import time
import random
import pandas as pd
from kafka import KafkaProducer

customers = pd.read_csv("data/customers.csv")
merchants = pd.read_csv("data/merchants.csv")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092"
)

# Pick ONE customer
customer = customers.iloc[0]

print("Testing velocity for:", customer["customer_id"])

for i in range(6):

    merchant = merchants.sample(1).iloc[0]

    transaction = {
        "transaction_id": f"VEL_{random.randint(100000, 999999)}",
        "customer_id": customer["customer_id"],
        "merchant_id": merchant["merchant_id"],
        "amount": round(random.uniform(500, 3000), 2),
        "transaction_type": "PURCHASE",
        "payment_channel": "UPI",
        "city": customer["city"],
        "device_id": customer["trusted_device_id"],
        "timestamp": pd.Timestamp.now().isoformat()
    }

    producer.send(
        "payment_transactions",
        value=json.dumps(transaction).encode("utf-8")
    )

    print("Sent:", transaction["transaction_id"])

    # Small gap between transactions
    time.sleep(2)

producer.flush()

print("Velocity test complete.")