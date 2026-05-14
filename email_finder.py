import csv
import requests
import re
import time
import socket
import smtplib
from urllib.parse import urljoin, urlparse

COMMON_PREFIXES = ["info", "contact", "reservations", "hello", "admin", "manager", "owner"]

def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return ""

def verify_email(email):
    try:
        domain = email.split("@")[1]
        records = socket.getaddrinfo(domain, None)
        return True if records else False
    except:
        return False

def scrape_emails(url):
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
        filtered = [e for e in set(found) if not any(x in e.lower() for x in
            ["example", "sentry", "wix", "schema", "png", "jpg", "svg", "noreply", "wordpress"])]
        return filtered[0] if filtered else ""
    except:
        return ""

def guess_emails(domain):
    if not domain:
        return ""
    for prefix in COMMON_PREFIXES:
        email = f"{prefix}@{domain}"
        if verify_email(email):
            return email
    return ""

rows = []
with open("leads.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

with open("leads_with_email.csv", "w", newline="") as f:
    fieldnames = ["Name", "Address", "Phone", "Website", "City", "Email", "Source"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for i, row in enumerate(rows):
        website = row.get("Website", "")
        domain = get_domain(website)

        # Try scraping first
        email = scrape_emails(website)
        source = "scraped"

        # Fall back to guessing
        if not email and domain:
            email = guess_emails(domain)
            source = "guessed"

        row["Email"] = email
        row["Source"] = source
        print(f"[{i+1}/{len(rows)}] {row['Name']} → {email or 'no email'} ({source})")

        with open("leads_with_email.csv", "a", newline="") as fa:
            writer2 = csv.DictWriter(fa, fieldnames=fieldnames)
            writer2.writerow(row)

        time.sleep(0.3)

print("Done. Check leads_with_email.csv")