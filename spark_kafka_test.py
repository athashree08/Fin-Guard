from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json,
    col,
    when,
    round,
    window
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    TimestampType
)

# ==================================================
# 1. START SPARK
# ==================================================

spark = SparkSession.builder \
    .appName("FinGuardFinalRiskEngine") \
    .master("local[*]") \
    .config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.13:4.2.0,"
        "org.postgresql:postgresql:42.7.8"
    ) \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")


# ==================================================
# 2. TRANSACTION SCHEMA
# ==================================================

transaction_schema = StructType([
    StructField("transaction_id", StringType()),
    StructField("customer_id", StringType()),
    StructField("merchant_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("transaction_type", StringType()),
    StructField("payment_channel", StringType()),
    StructField("city", StringType()),
    StructField("device_id", StringType()),
    StructField("timestamp", TimestampType())
])


# ==================================================
# 3. LOAD CUSTOMER DATA
# ==================================================

customers = spark.read.csv(
    "data/customers.csv",
    header=True,
    inferSchema=True
).select(
    "customer_id",
    "age",
    "annual_income",
    "customer_segment",
    "account_age_days",
    "avg_transaction_amount",
    col("city").alias("customer_city")
)


# ==================================================
# 4. LOAD MERCHANT DATA
# ==================================================

merchants = spark.read.csv(
    "data/merchants.csv",
    header=True,
    inferSchema=True
).select(
    "merchant_id",
    "merchant_name",
    "merchant_category",
    "risk_level",
    "blacklisted",
    col("city").alias("merchant_city")
)


# ==================================================
# 5. READ KAFKA STREAM
# ==================================================

transactions = spark.readStream \
    .format("kafka") \
    .option(
        "kafka.bootstrap.servers",
        "localhost:9092"
    ) \
    .option(
        "subscribe",
        "payment_transactions"
    ) \
    .option(
        "startingOffsets",
        "latest"
    ) \
    .load()


# ==================================================
# 6. KAFKA VALUE → JSON STRING
# ==================================================

json_transactions = transactions.select(
    col("value")
    .cast("string")
    .alias("json")
)


# ==================================================
# 7. PARSE JSON
# ==================================================

parsed_transactions = json_transactions.select(
    from_json(
        col("json"),
        transaction_schema
    ).alias("data")
)


# ==================================================
# 8. FLATTEN JSON
# ==================================================

clean_transactions = parsed_transactions.select(
    "data.*"
)


# ==================================================
# 9. VALIDATE TRANSACTIONS
# ==================================================

validated_transactions = clean_transactions.withColumn(
    "is_valid",

    (
        col("transaction_id").isNotNull()
        &
        col("customer_id").isNotNull()
        &
        col("merchant_id").isNotNull()
        &
        col("amount").isNotNull()
        &
        (col("amount") > 0)
        &
        col("transaction_type").isin(
            "PURCHASE",
            "TRANSFER",
            "WITHDRAWAL"
        )
        &
        col("payment_channel").isin(
            "UPI",
            "CARD",
            "NET_BANKING",
            "WALLET"
        )
        &
        col("city").isNotNull()
        &
        col("device_id").isNotNull()
        &
        col("timestamp").isNotNull()
    )
)


# ==================================================
# 10. CUSTOMER JOIN
# ==================================================

enriched_transactions = validated_transactions.join(
    customers,
    on="customer_id",
    how="left"
)


# ==================================================
# 11. MERCHANT JOIN
# ==================================================

enriched_transactions = enriched_transactions.join(
    merchants,
    on="merchant_id",
    how="left"
)


# ==================================================
# 12. AMOUNT RATIO
# ==================================================

enriched_transactions = enriched_transactions.withColumn(
    "amount_ratio",

    round(
        col("amount")
        / col("avg_transaction_amount"),
        2
    )
)


# ==================================================
# 13. BASE RISK SCORE
# ==================================================

risk_transactions = enriched_transactions.withColumn(
    "base_risk_score",

    # Blacklisted merchant
    when(
        col("blacklisted") == True,
        50
    ).otherwise(0)

    +

    # Merchant risk
    when(
        col("risk_level") == "HIGH",
        30
    )
    .when(
        col("risk_level") == "MEDIUM",
        15
    )
    .otherwise(0)

    +

    # Amount anomaly
    when(
        col("amount_ratio") >= 5,
        20
    )
    .when(
        col("amount_ratio") >= 3,
        10
    )
    .otherwise(0)

    +

    # Location mismatch
    when(
        col("city") != col("customer_city"),
        10
    )
    .otherwise(0)
)


# ==================================================
# 14. CREATE 1-MINUTE WINDOW
# ==================================================

# ==================================================
# 14. PROCESS EACH MICRO-BATCH
# ==================================================

def process_batch(batch_df, batch_id):

    print("\n")
    print("=" * 100)
    print(f"PROCESSING BATCH {batch_id}")
    print("=" * 100)

    # ----------------------------------------------
    # Ignore empty batches
    # ----------------------------------------------

    if batch_df.isEmpty():
        print("No transactions in this batch.")
        return

    # ----------------------------------------------
    # Calculate velocity inside this batch
    # ----------------------------------------------

    velocity = batch_df \
        .groupBy(
            window(
                col("timestamp"),
                "1 minute"
            ),
            col("customer_id")
        ) \
        .count() \
        .withColumnRenamed(
            "count",
            "transaction_count"
        )

    # ----------------------------------------------
    # Calculate velocity risk
    # ----------------------------------------------

    velocity = velocity.withColumn(
        "velocity_risk",

        when(
            col("transaction_count") >= 5,
            20
        )
        .when(
            col("transaction_count") >= 3,
            10
        )
        .otherwise(0)
    )
    velocity = velocity.withColumnRenamed(
    "window",
    "time_window"
)

    # ----------------------------------------------
    # Join velocity to current micro-batch
    # ----------------------------------------------

    batch_with_window = batch_df.withColumn(
        "time_window",
        window(
            col("timestamp"),
            "1 minute"
        )
    )

    final_df = batch_with_window.join(
        velocity,
        on=[
            "customer_id",
            "time_window"
        ],
        how="left"
    )

    # ----------------------------------------------
    # Missing velocity = 0
    # ----------------------------------------------

    final_df = final_df.withColumn(
        "velocity_risk",

        when(
            col("velocity_risk").isNull(),
            0
        )
        .otherwise(
            col("velocity_risk")
        )
    )

    # ----------------------------------------------
    # Final risk score
    # ----------------------------------------------

    final_df = final_df.withColumn(
        "final_risk_score",

        col("base_risk_score")
        +
        col("velocity_risk")
    )

    # ----------------------------------------------
    # Final risk level
    # ----------------------------------------------

    final_df = final_df.withColumn(
        "final_risk_level",

        when(
            col("final_risk_score") >= 60,
            "HIGH"
        )
        .when(
            col("final_risk_score") >= 30,
            "MEDIUM"
        )
        .otherwise(
            "LOW"
        )
    )

    # ----------------------------------------------
    # Display results
    # ----------------------------------------------

    final_df.select(
        "transaction_id",
        "customer_id",
        "merchant_id",
        "amount",
        "transaction_type",
        "payment_channel",
        "city",
        "customer_city",
        "merchant_name",
        "merchant_category",
        "risk_level",
        "blacklisted",
        "amount_ratio",
        "base_risk_score",
        "transaction_count",
        "velocity_risk",
        "final_risk_score",
        "final_risk_level"
    ).show(
        20,
        truncate=False
    )

    # ----------------------------------------------
    # Prepare data for PostgreSQL
    # ----------------------------------------------

    postgres_df = final_df.select(
        "transaction_id",
        "customer_id",
        "merchant_id",
        "amount",
        "transaction_type",
        "payment_channel",
        "city",
        "device_id",
        col("timestamp").alias("transaction_timestamp"),

        "customer_city",
        "customer_segment",
        "annual_income",
        "avg_transaction_amount",

        "merchant_name",
        "merchant_category",
        col("risk_level").alias("merchant_risk_level"),
        col("blacklisted").alias("merchant_blacklisted"),

        "amount_ratio",
        "base_risk_score",
        "velocity_risk",
        "final_risk_score",
        "final_risk_level"
    )

    # ----------------------------------------------
    # Write processed transactions to PostgreSQL
    # ----------------------------------------------

    jdbc_url = "jdbc:postgresql://localhost:5432/finguard"

    jdbc_properties = {
        "user": "postgres",
        "password": "athashree@11",
        "driver": "org.postgresql.Driver"
    }

    postgres_df.write \
        .jdbc(
            url=jdbc_url,
            table="transactions",
            mode="append",
            properties=jdbc_properties
        )

    print("Batch successfully written to PostgreSQL.")

# ==================================================
# 15. START STREAM
# ==================================================

query = risk_transactions.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .start()


# ==================================================
# 16. KEEP STREAM RUNNING
# ==================================================

query.awaitTermination()