import subprocess
import time
import os
import json
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

LOG_FILE = os.path.join(BASE_DIR, "pipeline.log")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_script(script):
    log(f"Starting {script}...")
    result = subprocess.run(
        ["python3", os.path.join(BASE_DIR, script)],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    last_line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "no output"
    if result.stderr.strip():
        log(f"{script} error: {result.stderr.strip().splitlines()[-1]}")
    log(f"{script} done. {last_line}")

def run_pipeline():
    while True:
        log("=== PIPELINE CYCLE START ===")
        run_script("scraper.py")
        run_script("email_finder.py")
        run_script("mailer.py")
        log("=== PIPELINE CYCLE DONE. Sleeping 24 hours. ===")
        time.sleep(24 * 3600)

if __name__ == "__main__":
    run_pipeline()
