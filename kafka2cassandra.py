import findspark

findspark.init()

from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import FloatType, IntegerType, StructField, StructType

odometrySchema = StructType(
    [
        StructField("id", IntegerType(), False),
        StructField("posex", FloatType(), False),
        StructField("posey", FloatType(), False),
        StructField("posez", FloatType(), False),
        StructField("orientx", FloatType(), False),
        StructField("orienty", FloatType(), False),
        StructField("orientz", FloatType(), False),
        StructField("orientw", FloatType(), False),
    ]
)

spark = (
    SparkSession.builder.appName("SparkStructuredStreaming")
    .config(
        "spark.jars.packages",
        "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:19092")
    .option("subscribe", "warty-odom")
    .option("delimeter", ",")
    .option("startingOffsets", "latest")
    .load()
)
df.printSchema()
df1 = (
    df.selectExpr("CAST(value AS STRING)")
    .select(from_json(col("value"), odometrySchema).alias("data"))
    .select("data.*")
)
df1.printSchema()


def writeToCassandra(writeDF, _):
    writeDF.write.format("org.apache.spark.sql.cassandra").mode("append").options(
        table="odometry", keyspace="ros"
    ).save()


df1.writeStream.option(
    "spark.cassandra.connection.host", "localhost:9042"
).foreachBatch(writeToCassandra).outputMode("update").start().awaitTermination()
