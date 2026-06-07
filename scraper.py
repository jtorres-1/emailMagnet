import requests
import csv
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

API_KEY = os.getenv("GOOGLE_API_KEY")

QUERIES = [
    "marketing agency",
    "digital marketing agency",
    "lead generation agency",
    "sales consulting firm",
    "real estate agency",
    "insurance agency",
    "solar company",
    "roofing company",
    "mortgage broker",
    "financial advisor",
]

CITIES = [
    "Los Angeles, CA", "San Diego, CA", "San Jose, CA", "San Francisco, CA",
    "Fresno, CA", "Sacramento, CA", "Long Beach, CA", "Oakland, CA",
    "Houston, TX", "San Antonio, TX", "Dallas, TX", "Austin, TX",
    "Fort Worth, TX", "El Paso, TX", "Arlington, TX", "Plano, TX",
    "Miami, FL", "Jacksonville, FL", "Tampa, FL", "Orlando, FL",
    "Fort Lauderdale, FL", "St. Petersburg, FL", "Tallahassee, FL",
    "New York, NY", "Buffalo, NY", "Rochester, NY", "Yonkers, NY",
    "Chicago, IL", "Aurora, IL", "Joliet, IL", "Naperville, IL",
    "Philadelphia, PA", "Pittsburgh, PA", "Allentown, PA", "Erie, PA",
    "Phoenix, AZ", "Tucson, AZ", "Mesa, AZ", "Chandler, AZ",
    "Columbus, OH", "Cleveland, OH", "Cincinnati, OH", "Toledo, OH",
    "Charlotte, NC", "Raleigh, NC", "Greensboro, NC", "Durham, NC",
    "Atlanta, GA", "Augusta, GA", "Savannah, GA", "Athens, GA",
    "Detroit, MI", "Grand Rapids, MI", "Ann Arbor, MI", "Lansing, MI",
    "Seattle, WA", "Spokane, WA", "Tacoma, WA", "Bellevue, WA",
    "Denver, CO", "Colorado Springs, CO", "Aurora, CO", "Fort Collins, CO",
    "Nashville, TN", "Memphis, TN", "Knoxville, TN", "Chattanooga, TN",
    "Indianapolis, IN", "Fort Wayne, IN", "Evansville, IN", "South Bend, IN",
    "Las Vegas, NV", "Henderson, NV", "Reno, NV", "North Las Vegas, NV",
    "Kansas City, MO", "St. Louis, MO", "Springfield, MO", "Columbia, MO",
    "Baltimore, MD", "Frederick, MD", "Rockville, MD", "Annapolis, MD",
    "Milwaukee, WI", "Madison, WI", "Green Bay, WI", "Kenosha, WI",
    "Minneapolis, MN", "St. Paul, MN", "Rochester, MN", "Duluth, MN",
    "Portland, OR", "Salem, OR", "Eugene, OR", "Beaverton, OR",
    "New Orleans, LA", "Baton Rouge, LA", "Shreveport, LA", "Lafayette, LA",
    "Birmingham, AL", "Montgomery, AL", "Huntsville, AL", "Mobile, AL",
    "Columbia, SC", "Charleston, SC", "Greenville, SC", "Spartanburg, SC",
    "Louisville, KY", "Lexington, KY", "Bowling Green, KY", "Owensboro, KY",
    "Oklahoma City, OK", "Tulsa, OK", "Norman, OK", "Broken Arrow, OK",
    "Virginia Beach, VA", "Norfolk, VA", "Richmond, VA", "Alexandria, VA",
    "Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Edison, NJ",
    "Boston, MA", "Worcester, MA", "Springfield, MA", "Cambridge, MA",
    "Salt Lake City, UT", "Provo, UT", "West Jordan, UT", "Ogden, UT",
    "Des Moines, IA", "Cedar Rapids, IA", "Davenport, IA", "Sioux City, IA",
    "Wichita, KS", "Overland Park, KS", "Topeka, KS", "Lawrence, KS",
    "Albuquerque, NM", "Las Cruces, NM", "Santa Fe, NM", "Rio Rancho, NM",
    "Omaha, NE", "Lincoln, NE", "Bellevue, NE", "Grand Island, NE",
    "Boise, ID", "Meridian, ID", "Nampa, ID", "Idaho Falls, ID",
    "Honolulu, HI", "Pearl City, HI", "Hilo, HI", "Kailua, HI",
    "Jackson, MS", "Gulfport, MS", "Hattiesburg, MS", "Southaven, MS",
    "Little Rock, AR", "Fort Smith, AR", "Fayetteville, AR", "Springdale, AR",
    "Bridgeport, CT", "New Haven, CT", "Hartford, CT", "Stamford, CT",
]

STATE_FILE = os.path.join(BASE_DIR, "scraper_state.json")
LEADS_FILE = os.path.join(BASE_DIR, "leads.csv")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def search_places(query, city):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.id"
    }
    body = {"textQuery": f"{query} in {city}", "maxResultCount": 20}
    try:
        response = requests.post(url, headers=headers, json=body, timeout=10)
        return response.json()
    except Exception as e:
        print(f"API error: {e}")
        return {}

def save_to_csv(places, city, vertical):
    file_exists = os.path.exists(LEADS_FILE)
    with open(LEADS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Name", "Address", "Phone", "Website", "City", "Vertical"])
        for p in places:
            name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            phone = p.get("nationalPhoneNumber", "")
            website = p.get("websiteUri", "")
            writer.writerow([name, address, phone, website, city, vertical])
    print(f"Saved {len(places)} {vertical}s from {city}")

def run():
    state = load_state()
    total = 0

    for city in CITIES:
        for query in QUERIES:
            key = f"{city}|{query}"
            if state.get(key):
                continue
            print(f"Scraping {query} in {city}...")
            data = search_places(query, city)
            places = data.get("places", [])
            if places:
                save_to_csv(places, city, query)
                total += len(places)
            state[key] = True
            save_state(state)
            time.sleep(1)

    print(f"Scraper done. {total} new places saved.")

if __name__ == "__main__":
    run()
