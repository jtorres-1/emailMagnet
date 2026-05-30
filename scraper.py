import requests
import csv
import time
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Agency verticals to scrape per city -- MapZap target market
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
    # California
    "Los Angeles, CA", "San Diego, CA", "San Jose, CA", "San Francisco, CA",
    "Fresno, CA", "Sacramento, CA", "Long Beach, CA", "Oakland, CA",
    "Bakersfield, CA", "Anaheim, CA", "Santa Ana, CA", "Riverside, CA",
    "Stockton, CA", "Irvine, CA", "Chula Vista, CA", "Fremont, CA",
    "San Bernardino, CA", "Modesto, CA", "Fontana, CA", "Moreno Valley, CA",
    # Texas
    "Houston, TX", "San Antonio, TX", "Dallas, TX", "Austin, TX",
    "Fort Worth, TX", "El Paso, TX", "Arlington, TX", "Corpus Christi, TX",
    "Plano, TX", "Lubbock, TX", "Laredo, TX", "Irving, TX",
    "Garland, TX", "Amarillo, TX", "McKinney, TX", "Frisco, TX",
    # Florida
    "Miami, FL", "Jacksonville, FL", "Tampa, FL", "Orlando, FL",
    "St. Petersburg, FL", "Hialeah, FL", "Tallahassee, FL", "Fort Lauderdale, FL",
    "Port St. Lucie, FL", "Cape Coral, FL", "Pembroke Pines, FL", "Hollywood, FL",
    # New York
    "New York, NY", "Buffalo, NY", "Rochester, NY", "Yonkers, NY",
    "Syracuse, NY", "Albany, NY", "New Rochelle, NY", "Mount Vernon, NY",
    # Illinois
    "Chicago, IL", "Aurora, IL", "Joliet, IL", "Naperville, IL",
    "Rockford, IL", "Springfield, IL", "Elgin, IL", "Peoria, IL",
    # Pennsylvania
    "Philadelphia, PA", "Pittsburgh, PA", "Allentown, PA", "Erie, PA",
    "Reading, PA", "Scranton, PA", "Bethlehem, PA", "Lancaster, PA",
    # Arizona
    "Phoenix, AZ", "Tucson, AZ", "Mesa, AZ", "Chandler, AZ",
    "Scottsdale, AZ", "Glendale, AZ", "Gilbert, AZ", "Tempe, AZ",
    # Ohio
    "Columbus, OH", "Cleveland, OH", "Cincinnati, OH", "Toledo, OH",
    "Akron, OH", "Dayton, OH", "Parma, OH", "Canton, OH",
    # North Carolina
    "Charlotte, NC", "Raleigh, NC", "Greensboro, NC", "Durham, NC",
    "Winston-Salem, NC", "Fayetteville, NC", "Cary, NC", "Wilmington, NC",
    # Georgia
    "Atlanta, GA", "Augusta, GA", "Columbus, GA", "Macon, GA",
    "Savannah, GA", "Athens, GA", "Sandy Springs, GA", "Roswell, GA",
    # Michigan
    "Detroit, MI", "Grand Rapids, MI", "Warren, MI", "Sterling Heights, MI",
    "Ann Arbor, MI", "Lansing, MI", "Flint, MI", "Dearborn, MI",
    # Washington
    "Seattle, WA", "Spokane, WA", "Tacoma, WA", "Vancouver, WA",
    "Bellevue, WA", "Kent, WA", "Everett, WA", "Renton, WA",
    # Colorado
    "Denver, CO", "Colorado Springs, CO", "Aurora, CO", "Fort Collins, CO",
    "Lakewood, CO", "Thornton, CO", "Arvada, CO", "Westminster, CO",
    # Tennessee
    "Nashville, TN", "Memphis, TN", "Knoxville, TN", "Chattanooga, TN",
    "Clarksville, TN", "Murfreesboro, TN", "Franklin, TN", "Jackson, TN",
    # Indiana
    "Indianapolis, IN", "Fort Wayne, IN", "Evansville, IN", "South Bend, IN",
    "Carmel, IN", "Fishers, IN", "Bloomington, IN", "Hammond, IN",
    # Nevada
    "Las Vegas, NV", "Henderson, NV", "Reno, NV", "North Las Vegas, NV",
    "Sparks, NV", "Carson City, NV",
    # Missouri
    "Kansas City, MO", "St. Louis, MO", "Springfield, MO", "Columbia, MO",
    "Independence, MO", "Lee's Summit, MO", "O'Fallon, MO", "St. Joseph, MO",
    # Maryland
    "Baltimore, MD", "Frederick, MD", "Rockville, MD", "Gaithersburg, MD",
    "Bowie, MD", "Hagerstown, MD", "Annapolis, MD", "College Park, MD",
    # Wisconsin
    "Milwaukee, WI", "Madison, WI", "Green Bay, WI", "Kenosha, WI",
    "Racine, WI", "Appleton, WI", "Waukesha, WI", "Eau Claire, WI",
    # Minnesota
    "Minneapolis, MN", "St. Paul, MN", "Rochester, MN", "Duluth, MN",
    "Bloomington, MN", "Brooklyn Park, MN", "Plymouth, MN", "Maple Grove, MN",
    # Oregon
    "Portland, OR", "Salem, OR", "Eugene, OR", "Gresham, OR",
    "Hillsboro, OR", "Beaverton, OR", "Bend, OR", "Medford, OR",
    # Louisiana
    "New Orleans, LA", "Baton Rouge, LA", "Shreveport, LA", "Metairie, LA",
    "Lafayette, LA", "Lake Charles, LA", "Kenner, LA", "Bossier City, LA",
    # Alabama
    "Birmingham, AL", "Montgomery, AL", "Huntsville, AL", "Mobile, AL",
    "Tuscaloosa, AL", "Hoover, AL", "Dothan, AL", "Auburn, AL",
    # South Carolina
    "Columbia, SC", "Charleston, SC", "North Charleston, SC", "Mount Pleasant, SC",
    "Rock Hill, SC", "Greenville, SC", "Summerville, SC", "Spartanburg, SC",
    # Kentucky
    "Louisville, KY", "Lexington, KY", "Bowling Green, KY", "Owensboro, KY",
    "Covington, KY", "Richmond, KY", "Georgetown, KY", "Florence, KY",
    # Oklahoma
    "Oklahoma City, OK", "Tulsa, OK", "Norman, OK", "Broken Arrow, OK",
    "Lawton, OK", "Edmond, OK", "Moore, OK", "Midwest City, OK",
    # Virginia
    "Virginia Beach, VA", "Norfolk, VA", "Chesapeake, VA", "Richmond, VA",
    "Newport News, VA", "Alexandria, VA", "Hampton, VA", "Roanoke, VA",
    # New Jersey
    "Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Elizabeth, NJ",
    "Edison, NJ", "Woodbridge, NJ", "Lakewood, NJ", "Toms River, NJ",
    # Massachusetts
    "Boston, MA", "Worcester, MA", "Springfield, MA", "Lowell, MA",
    "Cambridge, MA", "New Bedford, MA", "Brockton, MA", "Quincy, MA",
    # Utah
    "Salt Lake City, UT", "West Valley City, UT", "Provo, UT", "West Jordan, UT",
    "Orem, UT", "Sandy, UT", "Ogden, UT", "St. George, UT",
    # Iowa
    "Des Moines, IA", "Cedar Rapids, IA", "Davenport, IA", "Sioux City, IA",
    "Iowa City, IA", "Waterloo, IA", "Council Bluffs, IA", "Ames, IA",
    # Kansas
    "Wichita, KS", "Overland Park, KS", "Kansas City, KS", "Olathe, KS",
    "Topeka, KS", "Lawrence, KS", "Shawnee, KS", "Manhattan, KS",
    # New Mexico
    "Albuquerque, NM", "Las Cruces, NM", "Rio Rancho, NM", "Santa Fe, NM",
    "Roswell, NM", "Farmington, NM", "Clovis, NM", "Hobbs, NM",
    # Nebraska
    "Omaha, NE", "Lincoln, NE", "Bellevue, NE", "Grand Island, NE",
    "Kearney, NE", "Fremont, NE", "Hastings, NE", "Norfolk, NE",
    # Idaho
    "Boise, ID", "Meridian, ID", "Nampa, ID", "Idaho Falls, ID",
    "Pocatello, ID", "Caldwell, ID", "Coeur d'Alene, ID", "Twin Falls, ID",
    # Hawaii
    "Honolulu, HI", "Pearl City, HI", "Hilo, HI", "Kailua, HI",
    # Mississippi
    "Jackson, MS", "Gulfport, MS", "Southaven, MS", "Hattiesburg, MS",
    # Arkansas
    "Little Rock, AR", "Fort Smith, AR", "Fayetteville, AR", "Springdale, AR",
    # Connecticut
    "Bridgeport, CT", "New Haven, CT", "Hartford, CT", "Stamford, CT",
]


def search_places(query, city):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.id"
    }
    body = {"textQuery": f"{query} in {city}", "maxResultCount": 20}
    response = requests.post(url, headers=headers, json=body)
    return response.json()


def save_to_csv(places, city, vertical):
    with open("leads.csv", "a", newline="") as f:
        writer = csv.writer(f)
        for p in places:
            name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            phone = p.get("nationalPhoneNumber", "")
            website = p.get("websiteUri", "")
            writer.writerow([name, address, phone, website, city, vertical])
    print(f"Saved {len(places)} {vertical}s from {city}")


# Write header
with open("leads.csv", "w", newline="") as f:
    csv.writer(f).writerow(["Name", "Address", "Phone", "Website", "City", "Vertical"])

for city in CITIES:
    for query in QUERIES:
        print(f"Scraping {query} in {city}...")
        data = search_places(query, city)
        places = data.get("places", [])
        if places:
            save_to_csv(places, city, query)
        time.sleep(1)

print("Done. Check leads.csv")    "Syracuse, NY", "Albany, NY", "New Rochelle, NY", "Mount Vernon, NY",
    # Illinois
    "Chicago, IL", "Aurora, IL", "Joliet, IL", "Naperville, IL",
    "Rockford, IL", "Springfield, IL", "Elgin, IL", "Peoria, IL",
    # Pennsylvania
    "Philadelphia, PA", "Pittsburgh, PA", "Allentown, PA", "Erie, PA",
    "Reading, PA", "Scranton, PA", "Bethlehem, PA", "Lancaster, PA",
    # Arizona
    "Phoenix, AZ", "Tucson, AZ", "Mesa, AZ", "Chandler, AZ",
    "Scottsdale, AZ", "Glendale, AZ", "Gilbert, AZ", "Tempe, AZ",
    # Ohio
    "Columbus, OH", "Cleveland, OH", "Cincinnati, OH", "Toledo, OH",
    "Akron, OH", "Dayton, OH", "Parma, OH", "Canton, OH",
    # North Carolina
    "Charlotte, NC", "Raleigh, NC", "Greensboro, NC", "Durham, NC",
    "Winston-Salem, NC", "Fayetteville, NC", "Cary, NC", "Wilmington, NC",
    # Georgia
    "Atlanta, GA", "Augusta, GA", "Columbus, GA", "Macon, GA",
    "Savannah, GA", "Athens, GA", "Sandy Springs, GA", "Roswell, GA",
    # Michigan
    "Detroit, MI", "Grand Rapids, MI", "Warren, MI", "Sterling Heights, MI",
    "Ann Arbor, MI", "Lansing, MI", "Flint, MI", "Dearborn, MI",
    # Washington
    "Seattle, WA", "Spokane, WA", "Tacoma, WA", "Vancouver, WA",
    "Bellevue, WA", "Kent, WA", "Everett, WA", "Renton, WA",
    # Colorado
    "Denver, CO", "Colorado Springs, CO", "Aurora, CO", "Fort Collins, CO",
    "Lakewood, CO", "Thornton, CO", "Arvada, CO", "Westminster, CO",
    # Tennessee
    "Nashville, TN", "Memphis, TN", "Knoxville, TN", "Chattanooga, TN",
    "Clarksville, TN", "Murfreesboro, TN", "Franklin, TN", "Jackson, TN",
    # Indiana
    "Indianapolis, IN", "Fort Wayne, IN", "Evansville, IN", "South Bend, IN",
    "Carmel, IN", "Fishers, IN", "Bloomington, IN", "Hammond, IN",
    # Nevada
    "Las Vegas, NV", "Henderson, NV", "Reno, NV", "North Las Vegas, NV",
    "Sparks, NV", "Carson City, NV",
    # Missouri
    "Kansas City, MO", "St. Louis, MO", "Springfield, MO", "Columbia, MO",
    "Independence, MO", "Lee's Summit, MO", "O'Fallon, MO", "St. Joseph, MO",
    # Maryland
    "Baltimore, MD", "Frederick, MD", "Rockville, MD", "Gaithersburg, MD",
    "Bowie, MD", "Hagerstown, MD", "Annapolis, MD", "College Park, MD",
    # Wisconsin
    "Milwaukee, WI", "Madison, WI", "Green Bay, WI", "Kenosha, WI",
    "Racine, WI", "Appleton, WI", "Waukesha, WI", "Eau Claire, WI",
    # Minnesota
    "Minneapolis, MN", "St. Paul, MN", "Rochester, MN", "Duluth, MN",
    "Bloomington, MN", "Brooklyn Park, MN", "Plymouth, MN", "Maple Grove, MN",
    # Oregon
    "Portland, OR", "Salem, OR", "Eugene, OR", "Gresham, OR",
    "Hillsboro, OR", "Beaverton, OR", "Bend, OR", "Medford, OR",
    # Louisiana
    "New Orleans, LA", "Baton Rouge, LA", "Shreveport, LA", "Metairie, LA",
    "Lafayette, LA", "Lake Charles, LA", "Kenner, LA", "Bossier City, LA",
    # Alabama
    "Birmingham, AL", "Montgomery, AL", "Huntsville, AL", "Mobile, AL",
    "Tuscaloosa, AL", "Hoover, AL", "Dothan, AL", "Auburn, AL",
    # South Carolina
    "Columbia, SC", "Charleston, SC", "North Charleston, SC", "Mount Pleasant, SC",
    "Rock Hill, SC", "Greenville, SC", "Summerville, SC", "Spartanburg, SC",
    # Kentucky
    "Louisville, KY", "Lexington, KY", "Bowling Green, KY", "Owensboro, KY",
    "Covington, KY", "Richmond, KY", "Georgetown, KY", "Florence, KY",
    # Oklahoma
    "Oklahoma City, OK", "Tulsa, OK", "Norman, OK", "Broken Arrow, OK",
    "Lawton, OK", "Edmond, OK", "Moore, OK", "Midwest City, OK",
    # Virginia
    "Virginia Beach, VA", "Norfolk, VA", "Chesapeake, VA", "Richmond, VA",
    "Newport News, VA", "Alexandria, VA", "Hampton, VA", "Roanoke, VA",
    # New Jersey
    "Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Elizabeth, NJ",
    "Edison, NJ", "Woodbridge, NJ", "Lakewood, NJ", "Toms River, NJ",
    # Massachusetts
    "Boston, MA", "Worcester, MA", "Springfield, MA", "Lowell, MA",
    "Cambridge, MA", "New Bedford, MA", "Brockton, MA", "Quincy, MA",
    # Utah
    "Salt Lake City, UT", "West Valley City, UT", "Provo, UT", "West Jordan, UT",
    "Orem, UT", "Sandy, UT", "Ogden, UT", "St. George, UT",
    # Iowa
    "Des Moines, IA", "Cedar Rapids, IA", "Davenport, IA", "Sioux City, IA",
    "Iowa City, IA", "Waterloo, IA", "Council Bluffs, IA", "Ames, IA",
    # Kansas
    "Wichita, KS", "Overland Park, KS", "Kansas City, KS", "Olathe, KS",
    "Topeka, KS", "Lawrence, KS", "Shawnee, KS", "Manhattan, KS",
    # New Mexico
    "Albuquerque, NM", "Las Cruces, NM", "Rio Rancho, NM", "Santa Fe, NM",
    "Roswell, NM", "Farmington, NM", "Clovis, NM", "Hobbs, NM",
    # Nebraska
    "Omaha, NE", "Lincoln, NE", "Bellevue, NE", "Grand Island, NE",
    "Kearney, NE", "Fremont, NE", "Hastings, NE", "Norfolk, NE",
    # Idaho
    "Boise, ID", "Meridian, ID", "Nampa, ID", "Idaho Falls, ID",
    "Pocatello, ID", "Caldwell, ID", "Coeur d'Alene, ID", "Twin Falls, ID",
    # Hawaii
    "Honolulu, HI", "Pearl City, HI", "Hilo, HI", "Kailua, HI",
    # Mississippi
    "Jackson, MS", "Gulfport, MS", "Southaven, MS", "Hattiesburg, MS",
    # Arkansas
    "Little Rock, AR", "Fort Smith, AR", "Fayetteville, AR", "Springdale, AR",
    # Connecticut
    "Bridgeport, CT", "New Haven, CT", "Hartford, CT", "Stamford, CT",
]


def search_places(query, city):
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.id"
    }
    body = {"textQuery": f"{query} in {city}", "maxResultCount": 20}
    response = requests.post(url, headers=headers, json=body)
    return response.json()


def save_to_csv(places, city, vertical):
    with open("leads.csv", "a", newline="") as f:
        writer = csv.writer(f)
        for p in places:
            name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            phone = p.get("nationalPhoneNumber", "")
            website = p.get("websiteUri", "")
            writer.writerow([name, address, phone, website, city, vertical])
    print(f"Saved {len(places)} {vertical}s from {city}")


# Write header (extra column for vertical so we know what each lead is)
with open("leads.csv", "w", newline="") as f:
    csv.writer(f).writerow(["Name", "Address", "Phone", "Website", "City", "Vertical"])

for city in CITIES:
    for query in QUERIES:
        print(f"Scraping {query} in {city}...")
        data = search_places(query, city)
        places = data.get("places", [])
        if places:
            save_to_csv(places, city, query)
        time.sleep(1)

print("Done. Check leads.csv")
