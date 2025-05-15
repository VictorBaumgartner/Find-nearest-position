from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import math
import os # Import os for file path handling
from typing import List, Dict, Any

# Initialize FastAPI app
app = FastAPI()

# Define the filenames for input JSON data
GEODATA_FILE = "geopoints.json"
USER_LOCATION_FILE = "user_location.json" # Assuming a fixed filename for user location

# Variable to store loaded geopoints
geopoints: List[Dict[str, Any]] = []

# Haversine formula to calculate distance between two lat/lon points in kilometers
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

# Function to load geopoints from the JSON file
def load_geopoints(filename: str):
    """Loads geopoints from a JSON file."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Geopoints file not found: {filename}")
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Geopoints file must contain a list of locations.")
            # Basic validation for each location entry
            for item in data:
                if not all(k in item for k in ("id", "name", "latitude", "longitude")):
                     raise ValueError(f"Invalid format in geopoints file. Each item must have 'id', 'name', 'latitude', 'longitude'. Problem item: {item}")
                if not isinstance(item['latitude'], (int, float)) or not isinstance(item['longitude'], (int, float)):
                     raise ValueError(f"Invalid latitude or longitude type in geopoints file. Problem item: {item}")

            return data
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding JSON from geopoints file: {filename}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while loading geopoints: {e}")

# Function to load user location from the JSON file
def load_user_location(filename: str):
    """Loads user location from a JSON file."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"User location file not found: {filename}")
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                 raise ValueError("User location file must contain a single object.")
            if not all(k in data for k in ("latitude", "longitude")):
                 raise ValueError("User location file must have 'latitude' and 'longitude'.")
            if not isinstance(data['latitude'], (int, float)) or not isinstance(data['longitude'], (int, float)):
                 raise ValueError("Invalid latitude or longitude type in user location file.")
            return data
    except json.JSONDecodeError:
        raise ValueError(f"Error decoding JSON from user location file: {filename}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while loading user location: {e}")


# Load geopoints when the application starts
@app.on_event("startup")
async def startup_event():
    """Loads geopoints from the file when the app starts."""
    global geopoints
    try:
        geopoints = load_geopoints(GEODATA_FILE)
        print(f"Successfully loaded {len(geopoints)} geopoints from {GEODATA_FILE}")
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error during startup: {e}")
        # Depending on your needs, you might want to exit or handle this differently
        # For now, we'll just print the error and continue with an empty geopoints list
        geopoints = []


# API endpoint to find the nearest geopoints based on user location from file
@app.get("/nearest_geopoints_from_file/")
async def find_nearest_geopoints_from_file():
    """
    Finds the 10 nearest geopoints to the user's location,
    reading both geopoints and user location from predefined JSON files.

    Returns:
        List[Dict[str, Any]]: A list of the top 10 nearest geopoints,
                               sorted by distance, including their distance.
    """
    if not geopoints:
        raise HTTPException(status_code=500, detail="Geopoints data not loaded. Check geopoints.json.")

    try:
        user_location_data = load_user_location(USER_LOCATION_FILE)
        user_latitude = user_location_data["latitude"]
        user_longitude = user_location_data["longitude"]
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=f"Error loading user location: {e}")

    distances = []
    for geopoint in geopoints:
        distance = haversine_distance(
            user_latitude, user_longitude,
            geopoint["latitude"], geopoint["longitude"]
        )
        distances.append({"geopoint": geopoint, "distance_km": round(distance, 2)})

    # Sort by distance
    distances.sort(key=lambda x: x["distance_km"])

    # Return the top 10
    return distances[:10]

# To run this application:
# 1. Save the code as a Python file (e.g., main.py).
# 2. Create the 'geopoints.json' and 'user_location.json' files in the same directory.
# 3. Make sure you have FastAPI and uvicorn installed:
#    pip install fastapi uvicorn pydantic
# 4. Run the application using uvicorn:
#    uvicorn main:app --reload
# 5. Access the endpoint by making a GET request to http://127.0.0.1:8000/nearest_geopoints_from_file/
#    The API will read the data from the JSON files and return the result.
