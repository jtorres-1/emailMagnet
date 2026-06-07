import csv
import requests
import re
import time
import os
import json
import dns.resolver
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

LEADS_FILE = os.path.join(BASE_DIR, "leads.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "leads_with_email.csv")
STATE_FILE = os.path.join(BASE_DIR, "finder_state.json")

BLOCKED_DOMAINS = {
    "your-domain.com", "domain.com", "example.com", "example.org",
    "email.com", "yourdomain.com", "test.com", "website.com",
    "sentry.io", "wixpress.com", "squarespace.com", "godaddy.com",
    "wordpress.com", "shopify.com", "hilton.com", "hyatt.com",
    "marriott.com", "ihg.com", "wyndham.com",
}

BLOCKED_LOCAL_PARTS = {
    "email", "name", "you", "your", "username", "user", "test", "demo",
    "sample", "admin", "webmaster", "noreply", "no-reply", "donotreply",
    "postmaster", "accessibility", "privacy", "legal", "press", "media",
    "careers", "jobs", "hr", "investor", "investors", "unsubscribe", "abuse",
}

BLOCKED_EMAILS = {
    "email@address.com", "info@your-domain.com", "user@domain.com",
    "name@email.com", "you@example.com", "hello@calldone.org",
}

PLACEHOLDER_PATTERNS = [
    r"your[-_]?domain", r"your[-_]?company", r"example\.",
    r"^email@", r"^name@", r"^you@",
    r"@.*\.(png|jpg|jpeg|gif|svg|webp)$",
]

FREE_MAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"}
PRIORITY_PREFIXES = ("info@", "contact@", "hello@", "service@", "office@", "manager@", "owner@")

def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "").lower()
    except:
        return ""

def is_valid_email(email):
    email = (email or "").lower().strip()
    if not email or "@" not in email:
        return False
    if email in BLOCKED_EMAILS:
        return False
    local, _, domain = email.partition("@")
    if domain in BLOCKED_DOMAINS:
        return False
    if local in BLOCKED_LOCAL_PARTS:
        return False
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, email):
            return False
    return True

_mx_cache = {}
def has_mx(domain):
    if not domain:
        return False
    if domain in _mx_cache:
        return _mx_cache[domain]
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=4)
        result = len(answers) > 0
    except:
        result = False
    _mx_cache[domain] = result
    return result

def scrape_emails(url, business_domain=None):
    if not url:
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        found = []
        for path in ["", "/contact", "/about", "/contact-us"]:
            try:
                r = requests.get(urljoin(url, path), headers=headers, timeout=6)
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
                found += emails
            except:
                continue
        valid = []
        for e in set(found):
            e = e.lower().strip()
            if not is_valid_email(e):
                continue
            domain = e.split("@")[-1]
            if business_domain:
                if domain != business_domain and domain not in FREE_MAIL:
                    continue
            if not has_mx(domain):
                continue
            valid.append(e)

        def sort_key(x):
            x_domain = x.split("@")[-1]
            same_domain = 0 if (business_domain and x_domain == business_domain) else 1
            priority = 0 if x.startswith(PRIORITY_PREFIXES) else 1
            return (same_domain, priority)

        valid.sort(key=sort_key)
        return valid[0] if valid else ""
    except:
        return ""

def load_finder_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_finder_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run():
    if not os.path.exists(LEADS_FILE):
        print("No leads.csv found. Run scraper first.")
        return

    rows = []
    with open(LEADS_FILE) as f:
        rows = list(csv.DictReader(f))

    finder_state = load_finder_state()
    fieldnames = ["Name", "Address", "Phone", "Website", "City", "Vertical", "Email", "Source"]

    file_exists = os.path.exists(OUTPUT_FILE)
    kept = 0
    skipped = 0

    with open(OUTPUT_FILE, "a", newline="") as fa:
        writer = csv.DictWriter(fa, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()

        for i, row in enumerate(rows):
            website = row.get("Website", "")
            key = website.lower().strip()

            if not website or finder_state.get(key):
                skipped += 1
                continue

            domain = get_domain(website)
            email_found = scrape_emails(website, business_domain=domain)

            if email_found and is_valid_email(email_found):
                row["Email"] = email_found
                row["Source"] = "scraped"
                kept += 1
                writer.writerow(row)
                print(f"[{i+1}/{len(rows)}] {row['Name']} → {email_found}")
            else:
                skipped += 1
                print(f"[{i+1}/{len(rows)}] {row['Name']} → no email")
