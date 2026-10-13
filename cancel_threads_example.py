import concurrent.futures
import threading
import requests

urls = [
    "https://httpbin.org/delay/2",
    "https://httpbin.org/status/429",  # Triggers 429 immediately
    "https://httpbin.org/delay/5",     # Will be cancelled/stopped
    "https://httpbin.org/delay/5",     # Will be cancelled/stopped
]

def fetch_data(url, stop_event):
    """Worker function that checks the stop event before and after execution."""
    if stop_event.is_set():
        return url, None, "Skipped"

    try:
        # Pass a reasonable timeout so requests don't hang indefinitely
        response = requests.get(url, timeout=10)
        
        if response.status_code == 429:
            print(f"\n[!] Rate limited (429) on {url}. Signaling stop...")
            stop_event.set()
            return url, None, "Rate Limited (429)"
            
        response.raise_for_status()
        return url, response.json(), "Success"
        
    except requests.exceptions.RequestException as e:
        if stop_event.is_set():
            return url, None, "Aborted"
        print(f"Failed to fetch {url}: {e}")
        return url, None, str(e)

def main():
    max_workers = 3
    stop_event = threading.Event()
    results = {}

    # Initialize executor manually (instead of using a 'with' block) 
    # so we can control shutdown parameters.
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    try:
        future_to_url = {
            executor.submit(fetch_data, url, stop_event): url 
            for url in urls
        }

        for future in concurrent.futures.as_completed(future_to_url):
            url, data, status = future.result()
            
            if data is not None:
                results[url] = data
                print(f"Successfully processed: {url}")
            else:
                print(f"Finished {url} with status: {status}")

            # If a 429 triggered the stop event, break out of the loop right now
            if stop_event.is_set():
                print("[!] 429 detected. Breaking out of processing loop...")
                break

    finally:
        # Shutdown the executor immediately:
        # wait=False: Do not block waiting for active threads to finish.
        # cancel_futures=True: Instantly cancel any tasks still sitting in the queue.
        executor.shutdown(wait=False, cancel_futures=True)
        print("[!] Thread pool shutdown. Remaining pending tasks cancelled.")

    print(f"Execution halted. Total successful results collected: {len(results)}")
    return results

if __name__ == "__main__":
    main()