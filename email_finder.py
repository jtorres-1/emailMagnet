import csv
import requests
import re
import time
import socket
import dns.resolver
from urllib.parse import urljoin, urlparse
# =========================
# FILTERS
# =========================
BLOCKED_DOMAINS = {
    # placeholders
    "your-domain.com", "domain.com", "address.com", "example.com",
    "example.org", "email.com", "yourdomain.com", "test.com",
    "yourcompany.com", "company.com", "site.com", "mysite.com",
    "website.com",
    # platform / vendor noise
    "sentry.io", "wixpress.com", "squarespace.com", "godaddy.com",
    "wordpress.com", "shopify.com",
    # corporate parents that aren't real business inboxes
    "hilton.com", "hyatt.com", "marriott.com", "ihg.com",
    "wyndham.com", "choicehotels.com",
    # known dead/bounce sources from past cycles
    "bjsrestaurants.com", "fogodechao.com", "claimjumper.com", "moxies.ca",
    "fuegosla.com",
}
BLOCKED_LOCAL_PARTS = {
    "email", "name", "you", "your", "username", "user",
    "test", "demo", "sample", "admin", "webmaster",
    "noreply", "no-reply", "donotreply", "postmaster",
    "accessibility", "privacy", "legal", "press", "media",
    "careers", "jobs", "hr", "investor", "investors",
    "unsubscribe", "abuse",
}
BLOCKED_EMAILS = {
    "email@address.com", "info@your-domain.com", "user@domain.com",
    "name@email.com", "you@example.com", "hello@calldone.org",
}
PLACEHOLDER_PATTERNS = [
    r"your[-_]?domain",
    r"your[-_]?company",
    r"example\.",
    r"^email@",
    r"^name@",
    r"^you@",
    r"@.*\.(png|jpg|jpeg|gif|svg|webp)$",
]
FREE_MAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"}
PRIORITY_PREFIXES = ("info@", "contact@", "hello@", "service@", "office@", "manager@", "owner@", "dispatch@")
# =========================
# HELPERS
# =========================
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
    except Exception:
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
                emails = re.findall(
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text
                )
                found += emails
            except:
                continue
        valid = []
        for e in set(found):
            e = e.lower().strip()
            if not is_valid_email(e):
                continue
            domain = e.split("@")[-1]
            # Must match the business's own domain OR be a free-mail address
            if business_domain:
                if domain != business_domain and domain not in FREE_MAIL:
                    continue
            if not has_mx(domain):
                continue
            valid.append(e)
        # Prefer business-facing inboxes on the business's own domain
        def sort_key(x):
            x_domain = x.split("@")[-1]
            same_domain = 0 if (business_domain and x_domain == business_domain) else 1
            priority = 0 if x.startswith(PRIORITY_PREFIXES) else 1
            return (same_domain, priority)
        valid.sort(key=sort_key)
        return valid[0] if valid else ""
    except:
        return ""
# =========================
# MAIN
# =========================
rows = []
with open("leads.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)
fieldnames = ["Name", "Address", "Phone", "Website", "City", "Vertical", "Email", "Source"]
# Write header once
with open("leads_with_email.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
kept = 0
skipped = 0
for i, row in enumerate(rows):
    website = row.get("Website", "")
    domain = get_domain(website)
    email = scrape_emails(website, business_domain=domain)
    if email and is_valid_email(email):
        source = "scraped"
        kept += 1
    else:
        email = ""
        source = "none"
        skipped += 1
    row["Email"] = email
    row["Source"] = source
    # Ensure Vertical field exists even if leads.csv is from old scraper run
    if "Vertical" not in row:
        row["Vertical"] = ""
    print(f"[{i+1}/{len(rows)}] {row['Name']} → {email or 'no email'} ({source})")
    with open("leads_with_email.csv", "a", newline="") as fa:
        writer2 = csv.DictWriter(fa, fieldnames=fieldnames, extrasaction="ignore")
        writer2.writerow(row)
    time.sleep(0.3)
print(f"\nDone. Kept: {kept}  Skipped: {skipped}")
print("Output: leads_with_email.csv")
