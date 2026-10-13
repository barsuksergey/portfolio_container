from datetime import datetime
from airflow.decorators import dag, task
import os
import json
import logging
import requests
import concurrent.futures
import threading


dag_description = """
This DAG calls Flask API backened and requests 10 records at a time.
The endpoint has a rate limiter of 10 calls per minute, while DAG is sending 15 requests.
Once first 429 is received, stop event is set, executor waits for threads and cancels future ones.
You are still guranteed to receive your 100 records and not submit unnecessary API calls.
"""

def fetch_data(stop_event) -> tuple:
    """Sends a GET request to the local API endpoint, checking the stop event first."""
    if stop_event.is_set():
        logging.info("429 status code was detected. Not sending calls.")
        return []

    url = "http://host.docker.internal:5001/api/data"
    params = {"records": 10}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 429:
            stop_event.set()
            return []
            
        response.raise_for_status()
        logging.info(f"Succesfull request: {response.status_code}")
        return response.json().get("data", [])
        
    except requests.exceptions.RequestException as e:
        logging.info(f"Request failed: {e}")
        return []

@dag(
    dag_id="api_to_storage",
    start_date=datetime(2026, 9, 15),
    schedule=None,
    catchup=False,
    description=dag_description
)
def api_data_pipeline():

    @task
    def send_threaded_requests_with_stop_event(**context):
        max_workers = 5
        stop_event = threading.Event()
        results = []
    
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        
        try:
            future_to_index = {
                executor.submit(fetch_data, stop_event): i 
                for i in range(15)
            }
    
            for future in concurrent.futures.as_completed(future_to_index):
                data = future.result()
                results += data
    
        finally:
            # shutdown executor and cancel future threads
            executor.shutdown(cancel_futures=True)
            logging.info("Shutdown the executor and future threads due to 429 response")

        subdir = f"data/{context['logical_date'].strftime('%Y-%m-%d_%H-%M-%S')}"
        os.makedirs(subdir, exist_ok=True)
    
        file_path = os.path.join(subdir, "response.json")
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=4)
            
        logging.info(f"Successfully saved {len(results)} total records to {file_path}")

    send_threaded_requests_with_stop_event()

api_dag = api_data_pipeline()