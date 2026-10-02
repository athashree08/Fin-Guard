import pandas as pd
import numpy as np
import random
from datetime import datetime
import time
import json
from kafka import KafkaProducer
customers = pd.read_csv("data/customers.csv")
merchants = pd.read_csv("data/merchants.csv")

print(f"Loaded {len(customers)} customers and {len(merchants)} merchants")
producer = KafkaProducer(
    bootstrap_servers="localhost:9092"
)
def generate_transactions():
    customer = customers.sample(1).iloc[0]
    merchant = merchants.sample(1).iloc[0]

    transaction = {
        "transaction_id": f"TXN_{random.randint(1, 999999):06d}",
        "customer_id": customer["customer_id"],
        "merchant_id": merchant["merchant_id"],
        "amount": round(random.uniform(100,50000),2),
        "transaction_type": random.choice(["PURCHASE", "TRANSFER", "WITHDRAWAL"]),
        "payment_channel": random.choice(["UPI", "CARD", "NET_BANKING", "WALLET"]),
        "city": random.choice([
            "Pune", "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad"
        ]),
        "device_id": f"DEV_{random.randint(1,10000):05d}",
        "timestamp": datetime.now().isoformat()
    }
    return transaction
while True:
    transaction = generate_transactions()
    message = json.dumps(transaction).encode("utf-8")
    producer.send("payment_transactions", value= message)
    time.sleep(1)
   # Sleep for 1 second before generating the next transaction