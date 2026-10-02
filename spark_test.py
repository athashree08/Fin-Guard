from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("FinGuard") \
    .master("local[*]") \
    .getOrCreate()

print("Spark started successfully!")
print("Spark version:", spark.version)

spark.stop()