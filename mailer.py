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

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_HOST = "imap.gmail.com"
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

STATE_FILE = "state.json"

STEP1 = """Subject: Quick question about {name}

Hi,

I was looking up restaurants in {city} and came across {name}.

Quick question — do you ever lose reservations because calls go unanswered during rush hour or after close?

Asking because I built an AI receptionist that handles calls 24/7 for restaurants. Wanted to see if it's something that'd be useful for you.

— Jesse"""

STEP2 = """Subject: Re: Quick question about {name}

Hey again,

Didn't hear back so wanted to follow up quick.

We built an AI that answers your restaurant's calls 24/7 — books reservations, handles menu questions, works after hours. Sounds like a real person.

You can hear it live right now: call (563) 287-1146

No commitment, just see if it's what you need.

— Jesse"""

STEP3 = """Subject: Re: Quick question about {name}

Last one, promise.

If missing calls is costing you reservations, calldone.org has everything you need. Takes 48 hours to go live.

— Jesse"""

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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False

def get_ai_reply(thread_history, restaurant_name):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = f"""You are Jesse, a 21-year-old who built an AI phone receptionist called CallDone for restaurants.
A restaurant owner replied to your cold email. Your goal is to move them toward visiting calldone.org or calling the demo at (563) 287-1146.
Be conversational, short, and direct. No more than 3 sentences. Don't be salesy.
Restaurant: {restaurant_name}
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
        mail.select("inbox")
        _, data = mail.search(None, "UNSEEN")
        for num in data[0].split():
            _, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            sender = email.utils.parseaddr(msg["From"])[1].lower()
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = msg.get_payload(decode=True).decode()

            if sender in state:
                print(f"Reply from {sender}, generating AI response...")
                thread = state[sender].get("thread", "") + f"\nThem: {body}"
                ai_reply = get_ai_reply(thread, state[sender].get("name", ""))
                send_email(sender, "Re: Quick question about " + state[sender].get("name", ""), ai_reply)
                state[sender]["thread"] = thread + f"\nYou: {ai_reply}"
                state[sender]["step"] = "replied"
                save_state(state)
        mail.logout()
    except Exception as e:
        print(f"IMAP error: {e}")

def run():
    state = load_state()
    now = datetime.now()

    # Load leads
    leads = []
    with open("leads_with_email.csv") as f:
        for row in csv.DictReader(f):
            if row.get("Email") and "@" in row["Email"]:
                leads.append(row)

    print(f"Loaded {len(leads)} leads with emails")

    for lead in leads:
        email_addr = lead["Email"].lower()
        name = lead["Name"]
        city = lead["City"]

        if email_addr not in state:
            state[email_addr] = {"step": 0, "name": name, "city": city, "thread": "", "last_sent": ""}

        entry = state[email_addr]
        if entry["step"] == "replied":
            continue

        last_sent = datetime.fromisoformat(entry["last_sent"]) if entry["last_sent"] else None
        step = entry["step"]

        if step == 0:
            body = STEP1.format(name=name, city=city)
            subject = f"Quick question about {name}"
            if send_email(email_addr, subject, body):
                entry["step"] = 1
                entry["last_sent"] = now.isoformat()
                entry["thread"] = f"You: {body}"
                print(f"Step 1 sent → {email_addr}")
                save_state(state)
                time.sleep(30)

        elif step == 1 and last_sent and now - last_sent > timedelta(days=2):
            body = STEP2.format(name=name, city=city)
            if send_email(email_addr, "Re: Quick question about " + name, body):
                entry["step"] = 2
                entry["last_sent"] = now.isoformat()
                entry["thread"] += f"\nYou: {body}"
                print(f"Step 2 sent → {email_addr}")
                save_state(state)
                time.sleep(30)

        elif step == 2 and last_sent and now - last_sent > timedelta(days=2):
            body = STEP3.format(name=name, city=city)
            if send_email(email_addr, "Re: Quick question about " + name, body):
                entry["step"] = 3
                entry["last_sent"] = now.isoformat()
                entry["thread"] += f"\nYou: {body}"
                print(f"Step 3 sent → {email_addr}")
                save_state(state)
                time.sleep(30)

    # Check for replies
    check_replies(state)
    print("Cycle complete.")

if __name__ == "__main__":
    while True:
        run()
        print("Sleeping 1 hour...")
        time.sleep(3600)