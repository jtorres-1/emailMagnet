import subprocess
import time
import os
import json
import csv
from datetime import datetime
LOG_FILE = "pipeline.log"
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
def run_scraper():
    log("Starting scraper...")
    result = subprocess.run(["python3", "scraper.py"], capture_output=True, text=True)
    log(f"Scraper done. {result.stdout.strip().splitlines()[-1] if result.stdout else 'no output'}")
def run_email_finder():
    log("Starting email finder...")
    result = subprocess.run(["python3", "email_finder.py"], capture_output=True, text=True)
    log(f"Email finder done. {result.stdout.strip().splitlines()[-1] if result.stdout else 'no output'}")
def merge_new_leads():
    log("Merging new leads into mailer queue...")
    
    # Load existing state
    state = {}
    if os.path.exists("state.json"):
        with open("state.json") as f:
            state = json.load(f)
    # Load new leads
    new_count = 0
    if not os.path.exists("leads_with_email.csv"):
        log("No leads_with_email.csv found, skipping merge.")
        return
    with open("leads_with_email.csv") as f:
        for row in csv.DictReader(f):
            email = row.get("Email", "").lower().strip()
            if not email or "@" not in email:
                continue
            if email not in state:
                state[email] = {
                    "step": 0,
                    "name": row.get("Name", ""),
                    "city": row.get("City", ""),
                    "vertical": row.get("Vertical", ""),
                    "thread": "",
                    "last_sent": ""
                }
                new_count += 1
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)
    log(f"Merged {new_count} new leads into queue. Total: {len(state)}")
def run_pipeline():
    while True:
        log("=== PIPELINE CYCLE START ===")
        run_scraper()
        run_email_finder()
        merge_new_leads()
        log("=== PIPELINE CYCLE DONE. Sleeping 3 days. ===")
        time.sleep(3 * 24 * 3600)  # 3 days
if __name__ == "__main__":
    run_pipeline()
