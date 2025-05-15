from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import math
import os
from typing import List, Dict, Any
from contextlib import asynccontextmanager

# Get the directory where the current script is located
# This ensures that the JSON files are found relative to the script's location,
# regardless of the current working directory when the script is executed.
SCRIPT_DIR = os.path.dirname(__file__)

# Define the full paths to the input JSON data files
# os.path.join is used to construct paths in a way that is compatible with
# different operating systems (Windows, macOS, Linux).
GEODATA_FILE = os.path.join(SCRIPT_DIR, "geopoints.json")
USER_LOCATION_FILE = os.path.join(SCRIPT_DIR, "user_location.json")

# Variable to store loaded geopoints.
# This variable is populated during the application startup event.
geopoints: List[Dict[str, Any]] = []

# Haversine formula to calculate distance between two lat/lon points in kilometers
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the distance between two geographic points on Earth's surface
    using the Haversine formula.

    Args:
        lat1: Latitude of the first point (in degrees).
        lon1: Longitude of the first point (in degrees).
        lat2: Latitude of the second point (in degrees).
        lon2: Longitude of the second point (in degrees).

    Returns:
        The distance between the two points in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Difference in coordinates
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    # Haversine formula calculation
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance = R * c
    distance = R * c
    return distance

# Function to load geopoints from the JSON file
def load_geopoints(filename: str):
    """
    Loads geopoints data from a specified JSON file.
    Includes basic validation and error handling.

    Args:
        filename: The full path to the JSON file containing geopoints.

    Returns:
        A list of dictionaries representing the geopoints, or an empty list
        if the file is not found, has invalid JSON, or contains invalid data.
    """
    if not os.path.exists(filename):
        # Print an error if the file is not found
        print(f"Error: Geopoints file not found at {filename}")
        return [] # Return empty list if file not found
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Check if the loaded data is a list
            if not isinstance(data, list):
                print(f"Error: Geopoints file must contain a list of locations. File: {filename}")
                return []
            # Basic validation for each location entry in the list
            validated_data = []
            for item in data:
                # Check for required keys ('id', 'name', 'latitude', 'longitude')
                if not all(k in item for k in ("id", "name", "latitude", "longitude")):
                     print(f"Warning: Skipping invalid item (missing keys) in geopoints file: {item}")
                     continue # Skip invalid items instead of raising error
                # Check if latitude and longitude are numbers
                if not isinstance(item.get('latitude'), (int, float)) or not isinstance(item.get('longitude'), (int, float)):
                     print(f"Warning: Skipping item with invalid lat/lon types: {item}")
                     continue # Skip invalid items
                validated_data.append(item)
            return validated_data
    except json.JSONDecodeError:
        # Handle JSON decoding errors
        print(f"Error decoding JSON from geopoints file: {filename}")
        return []
    except Exception as e:
        # Catch any other unexpected errors during file loading
        print(f"An unexpected error occurred while loading geopoints: {e}")
        return []

# Function to load user location from the JSON file
def load_user_location(filename: str):
    """
    Loads the user's location data from a specified JSON file.
    Includes basic validation and error handling.

    Args:
        filename: The full path to the JSON file containing the user's location.

    Returns:
        A dictionary containing the user's latitude and longitude.
    """
    if not os.path.exists(filename):
        # Raise a FileNotFoundError if the user location file is not found
        raise FileNotFoundError(f"User location file not found at {filename}")
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Check if the loaded data is a dictionary
            if not isinstance(data, dict):
                 raise ValueError("User location file must contain a single object.")
            # Check for required keys ('latitude', 'longitude')
            if not all(k in data for k in ("latitude", "longitude")):
                 raise ValueError("User location file must have 'latitude' and 'longitude'.")
            # Check if latitude and longitude are numbers
            if not isinstance(data.get('latitude'), (int, float)) or not isinstance(data.get('longitude'), (int, float)):
                 raise ValueError("Invalid latitude or longitude type in user location file.")
            return data
    except json.JSONDecodeError:
        # Handle JSON decoding errors
        raise ValueError(f"Error decoding JSON from user location file: {filename}")
    except Exception as e:
        # Catch any other unexpected errors during file loading
        raise RuntimeError(f"An error occurred while loading user location: {e}")

# Lifespan event handler for startup and shutdown
# This function is run when the FastAPI application starts up and shuts down.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    Loads geopoints data when the application starts.
    """
    # Startup logic: Load geopoints data
    global geopoints # Declare geopoints as global to modify the module-level variable
    print(f"Attempting to load geopoints from {GEODATA_FILE}...")
    geopoints = load_geopoints(GEODATA_FILE)
    if geopoints:
        print(f"Successfully loaded {len(geopoints)} geopoints.")
    else:
        print("No geopoints loaded. Check geopoints.json file path and format.")

    yield # The application will now handle incoming requests

    # Shutdown logic: (Optional) Add cleanup code here if needed
    # This block is executed when the application is shutting down.
    # For example, you could close database connections or release other resources.
    print("Application shutting down.")

# Initialize FastAPI app with the lifespan event handler
# The lifespan handler is passed to the 'lifespan' parameter.
app = FastAPI(lifespan=lifespan)


# API endpoint to find the nearest geopoints based on user location from file
@app.get("/nearest_geopoints_from_file/")
async def find_nearest_geopoints_from_file():
    """
    API endpoint to find the 10 nearest geopoints to the user's location.
    It reads the geopoints data loaded during startup and the user's location
    from the predefined JSON file.

    Returns:
        List[Dict[str, Any]]: A list of the top 10 nearest geopoints,
                               sorted by distance, including their distance in kilometers.
        Raises:
            HTTPException: If geopoints data was not loaded or if there's an error
                           loading the user location file.
    """
    # Check if geopoints were loaded successfully during startup
    if not geopoints:
        # Return a 500 Internal Server Error if geopoints data is missing
        raise HTTPException(status_code=500, detail="Geopoints data not loaded. Check geopoints.json and server logs.")

    try:
        # Load the user's location from the file for each request.
        # This assumes the user's location file might change between requests.
        user_location_data = load_user_location(USER_LOCATION_FILE)
        user_latitude = user_location_data["latitude"]
        user_longitude = user_location_data["longitude"]
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        # Raise an HTTP exception if there's an issue loading the user location file
        raise HTTPException(status_code=500, detail=f"Error loading user location from {USER_LOCATION_FILE}: {e}")

    distances = []
    # Calculate distance for each loaded geopoint relative to the user's location
    for geopoint in geopoints:
        distance = haversine_distance(
            user_latitude, user_longitude,
            geopoint["latitude"], geopoint["longitude"]
        )
        # Append the geopoint data and the calculated distance to the distances list
        distances.append({"geopoint": geopoint, "distance_km": round(distance, 2)})

    # Sort the list of distances based on the 'distance_km' key
    distances.sort(key=lambda x: x["distance_km"])

    # Return the top 10 nearest locations from the sorted list
    return distances[:10]

# Instructions to run this application:
# 1. Save this code as a Python file (e.g., main.py).
# 2. Create 'geopoints.json' and 'user_location.json' files in the SAME directory as the Python script.
# 3. Make sure you have FastAPI, Uvicorn, and Pydantic installed in your Python environment (preferably a virtual environment):
#    pip install fastapi uvicorn pydantic
# 4. Open your terminal or command prompt, navigate to the directory where you saved the files.
# 5. Run the application using uvicorn:
#    uvicorn main:app --reload
#    (Replace 'main' with the name of your Python file if different)
# 6. The application will start, and you should see output indicating that geopoints are being loaded.
# 7. Access the API endpoint by making a GET request to:
#    http://127.0.0.1:8000/nearest_geopoints_from_file/
#    You can use a web browser, curl, Postman, or write a simple script to do this.
