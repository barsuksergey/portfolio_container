from datetime import datetime, timedelta
from airflow.decorators import dag, task
import requests


@dag(
    dag_id="api_data_pipeline_flow",
    start_date=datetime(2026, 9, 15),
)
def api_data_pipeline():

    @task
    def fetch_data() -> list:
        """Sends a GET request to the local API endpoint."""
        url = "http://host.docker.internal:5000/api/data"
        params = {"records": 10}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        print(response.json())

    fetch_data()


# Instantiate the DAG
api_dag = api_data_pipeline()