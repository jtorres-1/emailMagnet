import requests
import csv
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

CITIES = [
    "Los Angeles, CA", "Houston, TX", "Phoenix, AZ", "San Antonio, TX",
    "San Diego, CA", "Dallas, TX", "San Jose, CA", "Austin, TX",
    "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "Indianapolis, IN", "San Francisco, CA", "Seattle, WA", "Denver, CO",
    "Nashville, TN", "Oklahoma City, OK", "Las Vegas, NV", "Miami, FL"
]

def search_restaurants(city):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.id"
    }
    body = {"textQuery": f"restaurant in {city}", "maxResultCount": 20}
    response = requests.post(url, headers=headers, json=body)
    return response.json()

def save_to_csv(places, city):
    with open("leads.csv", "a", newline="") as f:
        writer = csv.writer(f)
        for p in places:
            name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            phone = p.get("nationalPhoneNumber", "")
            website = p.get("websiteUri", "")
            writer.writerow([name, address, phone, website, city])
    print(f"Saved {len(places)} from {city}")

with open("leads.csv", "w", newline="") as f:
    csv.writer(f).writerow(["Name", "Address", "Phone", "Website", "City"])

for city in CITIES:
    print(f"Scraping {city}...")
    data = search_restaurants(city)
    places = data.get("places", [])
    if places:
        save_to_csv(places, city)
    time.sleep(1)

print("Done. Check leads.csv")