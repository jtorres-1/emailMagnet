import csv
import json
import os
import time
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import anthropic

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
IMAP_HOST = "imap.gmail.com"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

STATE_FILE = os.path.join(BASE_DIR, "state.json")
LEADS_FILE = os.path.join(BASE_DIR, "leads_with_email.csv")

SUBJECT_STEP1 = "tool that pulls 100 local business leads in 60 seconds"
SUBJECT_FOLLOWUP = "Re: tool that pulls 100 local business leads in 60 seconds"

STEP1 = """Hi {name},

Found your business while looking up {vertical}s in {city}.

Built a tool called MapZap that pulls 100 local business leads as a CSV in about 60 seconds. You type a business type and city, it returns names, phone numbers, addresses, and websites.

$49 one time, no subscription. Thought it might be useful for client prospecting or outreach lists.

mapzap.org if you want to check it out.

Jesse"""

STEP2 = """Hey {name},

Just following up in case this got buried.

MapZap pulls 100 local business leads as a CSV in 60 seconds — names, phones, addresses. $49 one time, no monthly fee.

If you ever need a quick list for a client campaign or outreach push, mapzap.org

Jesse"""

STEP3 = """Last one from me {name}.

If you do any kind of local outreach or client prospecting, MapZap saves hours of manual list building. 100 leads, any niche, any city, 60 seconds, $49 flat.

mapzap.org

Jesse"""

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_email(to, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False

def get_ai_reply(thread_history, business_name, vertical=""):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    vertical_line = f"They are a {vertical}." if vertical else ""
    prompt = f"""You are Jesse, a 21-year-old developer who built MapZap — a tool that pulls 100 local business leads as a CSV in 60 seconds. $49 one time at mapzap.org.

A business owner or marketer replied to your cold email. Your goal is to answer their question and move them toward buying at mapzap.org.

Be short, direct, conversational. Max 3 sentences. No corporate language. If they ask about price it's $49 one time. If they ask how it works: type a business type and city, get 100 leads with names, phones, addresses as a CSV instantly.

Business: {business_name}
{vertical_line}

Thread:
{thread_history}

Write only the reply body, no subject line."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def check_replies(state):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select(
