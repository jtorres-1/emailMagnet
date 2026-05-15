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

# Subject lines (kept as variables so follow-ups thread correctly)
SUBJECT_STEP1 = "missed any reservations this week?"
SUBJECT_FOLLOWUP = "Re: missed any reservations this week?"

STEP1 = """Hi,

Found {name} while looking up {city} restaurants and had a quick question.

How often do calls go to voicemail during your dinner rush — or after you close? Every missed call is usually a missed reservation.

I built an AI receptionist that answers your phone 24/7, books reservations, and texts you a summary after each call. Sounds like a real person.

You can hear it right now — call (563) 287-1146. Takes 30 seconds.

If it sounds useful, full setup is at calldone.org.

— Jesse"""

STEP2 = """Hey,

Wanted to bump this in case it got buried.

If you haven't yet, call (563) 287-1146 and hear what your customers would hear. It's a real demo of the AI — make a reservation, ask about hours, try to trip it up.

Most restaurant owners I've shown this to thought it was a person for the first 20 seconds.

calldone.org if you want to set yours up. Live in 48 hours.

— Jesse"""

STEP3 = """Last note from me.

Math on missing calls: average reservation is around $180. If you miss 3 a week, that's $28k a year walking out the door.

CallDone fixes it for $1,000 setup + $500/month. Less than what one missed table per week costs you.

Call (563) 287-1146 to hear it. Sign up at calldone.org.

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
                        try:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            body = ""
                        break
            else:
                try:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                except Exception:
                    body = ""
            if sender in state:
                print(f"Reply from {sender}, generating AI response...")
                thread = state[sender].get("thread", "") + f"\nThem: {body}"
                ai_reply = get_ai_reply(thread, state[sender].get("name", ""))
                send_email(sender, SUBJECT_FOLLOWUP, ai_reply)
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

        # New lead → start at step 0
        if email_addr not in state:
            state[email_addr] = {
                "step": 0,
                "name": name,
                "city": city,
                "thread": "",
                "last_sent": ""
            }

        entry = state[email_addr]

        if entry["step"] == "replied":
            continue

        last_sent = datetime.fromisoformat(entry["last_sent"]) if entry["last_sent"] else None
        step = entry["step"]

        if step == 0:
            # Brand new lead - send Step 1
            body = STEP1.format(name=name, city=city)
            if send_email(email_addr, SUBJECT_STEP1, body):
                entry["step"] = 1
                entry["last_sent"] = now.isoformat()
                entry["thread"] = f"You: {body}"
                print(f"Step 1 sent → {email_addr}")
                save_state(state)
                time.sleep(30)

        elif step == 1 and last_sent and now - last_sent > timedelta(days=2):
            # Already got Step 1 (old or new copy) - send Step 2
            body = STEP2.format(name=name, city=city)
            if send_email(email_addr, SUBJECT_FOLLOWUP, body):
                entry["step"] = 2
                entry["last_sent"] = now.isoformat()
                entry["thread"] += f"\nYou: {body}"
                print(f"Step 2 sent → {email_addr}")
                save_state(state)
                time.sleep(30)

        elif step == 2 and last_sent and now - last_sent > timedelta(days=2):
            # Already got Step 2 - send Step 3
            body = STEP3.format(name=name, city=city)
            if send_email(email_addr, SUBJECT_FOLLOWUP, body):
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
