import requests

# Your Space-Track username and password (replace with your credentials)
USERNAME = "useofonline@gmail.com"
PASSWORD = "susinginonlineeeee-25"

# Base URL for Space-Track API
BASE_URL = "https://www.space-track.org/ajaxauth/login"

# Authentication payload
payload = {
    'identity': USERNAME,
    'password': PASSWORD
}

# Start a session
session = requests.Session()
response = session.post(BASE_URL, data=payload)

# Check if login was successful
if response.status_code == 200:
    print("✅ Successfully logged in to Space-Track!")
else:
    print("❌ Login failed. Check credentials.")

# Space-Track TLE request URL for space debris
TLE_URL = "https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/OBJECT_TYPE/DEBRIS/format/tle"

# Fetch TLE data
response = session.get(TLE_URL)

# Save to a file
if response.status_code == 200:
    with open("space_debris.tle", "w") as file:
        file.write(response.text)
    print("✅ Space debris TLE data downloaded successfully!")
else:
    print("❌ Failed to fetch data.")