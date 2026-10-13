from airflow.decorators import dag, task
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode
from airflow.hooks.base import BaseHook


@dag(
    dag_id="spark_to_postgres",
    start_date=datetime(2026, 10, 12),
    schedule=None,
    catchup=False
)
def spark_data_pipeline():

    @task
    def run_spark_job():

        conn = BaseHook.get_connection("postgres_sink")
        db_url = f"jdbc:postgresql://{conn.host}:{conn.port}/{conn.schema}"
        db_properties = {
            "user": conn.login,
            "password": conn.password,
            "driver": "org.postgresql.Driver"
        }
        spark = SparkSession.builder \
            .appName("CustomerOrdersETL") \
            .master("local[*]") \
            .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3") \
            .getOrCreate()

        file_path = "file:/opt/airflow/data/2026-10-13_03-15-38/response.json"
        df_raw = spark.read.option("multiLine", "true").json(file_path)

        customers_df = df_raw.select(
            col("id"),
            col("first_name"),
            col("last_name"),
            col("address"),
            col("email")
        )

        orders_df = df_raw.select(
            col("id").alias("customer_id"),
            explode(col("orders")).alias("order")
        ).select(
            col("customer_id"),
            col("order.order_id").alias("order_id"),
            col("order.item_id").alias("item_id"),
            col("order.color").alias("color"),
            col("order.cc_number").alias("cc_number"),
            col("order.total").alias("total")
        )

        customers_df.write \
            .jdbc(url=db_url, table="customers", mode="append", properties=db_properties)

        orders_df.write \
            .jdbc(url=db_url, table="orders", mode="append", properties=db_properties)

        spark.stop()

    run_spark_job()

spark_data_pipeline()