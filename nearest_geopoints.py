from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import math
import os
from typing import List, Dict, Any
from contextlib import asynccontextmanager # Import asynccontextmanager

# Define the filenames for input JSON data
GEODATA_FILE = "geopoints.json"
USER_LOCATION_FILE = "user_location.json"

# Variable to store loaded geopoints
geopoints: List[Dict[str, Any]] = []

# Haversine formula to calculate distance between two lat/lon points in kilometers
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the distance between two geographic points using the Haversine formula.

    Args:
        lat1: Latitude of the first point.
        lon1: Longitude of the first point.
        lat2: Latitude of the second point.
        lon2: Longitude of the second point.

    Returns:
        The distance between the two points in kilometers.
    """
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
    """
    Loads geopoints from a JSON file.

    Args:
        filename: The path to the JSON file.

    Returns:
        A list of dictionaries representing the geopoints, or an empty list if loading fails.
    """
    if not os.path.exists(filename):
        # In a real app, you might want to log this error properly
        print(f"Error: Geopoints file not found: {filename}")
        return [] # Return empty list if file not found
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Error: Geopoints file must contain a list of locations. File: {filename}")
                return []
            # Basic validation for each location entry
            validated_data = []
            for item in data:
                # Check for required keys and correct types
                if not all(k in item for k in ("id", "name", "latitude", "longitude")):
                     print(f"Warning: Skipping invalid item (missing keys) in geopoints file: {item}")
                     continue # Skip invalid items instead of raising error
                if not isinstance(item['latitude'], (int, float)) or not isinstance(item['longitude'], (int, float)):
                     print(f"Warning: Skipping item with invalid lat/lon types: {item}")
                     continue # Skip invalid items
                validated_data.append(item)
            return validated_data
    except json.JSONDecodeError:
        print(f"Error decoding JSON from geopoints file: {filename}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading geopoints: {e}")
        return []

# Function to load user location from the JSON file
def load_user_location(filename: str):
    """
    Loads user location from a JSON file.

    Args:
        filename: The path to the JSON file.

    Returns:
        A dictionary containing the user's latitude and longitude.
    """
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

# Lifespan event handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Loads geopoints when the application starts.
    """
    # Startup: Load geopoints
    global geopoints
    print(f"Attempting to load geopoints from {GEODATA_FILE}...")
    geopoints = load_geopoints(GEODATA_FILE)
    if geopoints:
        print(f"Successfully loaded {len(geopoints)} geopoints.")
    else:
        print("No geopoints loaded. Check file or format.")

    yield # Application runs here (handles incoming requests)

    # Shutdown: (Optional) Add cleanup code here if needed
    # For example, closing database connections, releasing resources, etc.
    print("Application shutting down.")

# Initialize FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)


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
    # Check if geopoints were loaded successfully during startup
    if not geopoints:
        raise HTTPException(status_code=500, detail="Geopoints data not loaded. Check geopoints.json and server logs.")

    try:
        # Load the user's location from the file for each request
        user_location_data = load_user_location(USER_LOCATION_FILE)
        user_latitude = user_location_data["latitude"]
        user_longitude = user_location_data["longitude"]
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        # Raise an HTTP exception if there's an issue loading the user location file
        raise HTTPException(status_code=500, detail=f"Error loading user location from {USER_LOCATION_FILE}: {e}")

    distances = []
    # Calculate distance for each loaded geopoint
    for geopoint in geopoints:
        distance = haversine_distance(
            user_latitude, user_longitude,
            geopoint["latitude"], geopoint["longitude"]
        )
        distances.append({"geopoint": geopoint, "distance_km": round(distance, 2)})

    # Sort the list of distances by the distance value
    distances.sort(key=lambda x: x["distance_km"])

    # Return the top 10 nearest locations
    return distances[:10]

# Instructions to run:
# 1. Save this code as a Python file (e.g., main.py).
# 2. Create 'geopoints.json' and 'user_location.json' files in the same directory.
# 3. Install dependencies: pip install fastapi uvicorn pydantic
# 4. Run: uvicorn main:app --reload
# 5. Access the API at http://127.0.0.1:8000/nearest_geopoints_from_file/
