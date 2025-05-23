from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel, model_validator, ValidationError # Added ValidationError
import math
from typing import List, Dict, Any, Optional
import csv
import io
import json

app = FastAPI()

# Pydantic model for coordinates
class Coordinates(BaseModel):
    latitude: float
    longitude: float

    @model_validator(mode='after')
    def check_valid_coordinates(cls, values):
        # Ensure latitude and longitude are present and are numbers before accessing them
        lat = values.latitude
        lon = values.longitude
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude values")
        return values

# Pydantic model for response
class NearestStationsResponse(BaseModel):
    stations: List[Dict[str, Any]]

# Haversine formula (remains the same)
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
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

# parse_coordinates function (remains the same)
def parse_coordinates(coord_string: str) -> Optional[tuple]:
    if not coord_string or coord_string.strip() == "" or coord_string.strip() == "*":
        return None
    try:
        coord_string = coord_string.strip().strip('"')
        parts = coord_string.split(',')
        if len(parts) != 2:
            return None
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return (lat, lon)
    except (ValueError, IndexError):
        return None

# filter_stations_by_bbox function (remains the same)
def filter_stations_by_bbox(stations: List[Dict[str, Any]], user_lat: float, user_lon: float, max_distance_km: float = 10) -> List[Dict[str, Any]]:
    R = 6371
    lat_range = max_distance_km / 111
    lon_range = max_distance_km / (111 * math.cos(math.radians(user_lat)))
    return [
        station for station in stations
        if (
            abs(station["latitude"] - user_lat) <= lat_range
            and abs(station["longitude"] - user_lon) <= lon_range
        )
    ]

# parse_csv_data_to_stations function (remains the same, assuming it works as intended)
def parse_csv_data_to_stations(csv_content: str) -> List[Dict[str, Any]]:
    stations = {}
    station_id = 1
    current_line = None
    csv_file = io.StringIO(csv_content)
    reader = csv.reader(csv_file, delimiter=',', quotechar='"')
    for parts in reader:
        if not parts or not any(parts):
            continue
        if len(parts) < 4: # Assuming at least stop_name, coord1, coord2, line_number potentially
            continue
            
        stop_name = parts[0].strip()
        coord1 = parts[1].strip() if len(parts) > 1 else ""
        coord2 = parts[2].strip() if len(parts) > 2 else ""
        line_info_or_stop_name_part = parts[3].strip() if len(parts) > 3 else ""

        # Heuristic to differentiate line numbers from continuation of stop names or other data
        if line_info_or_stop_name_part.lower().startswith('ligne') or \
           (not coord1 and not coord2 and line_info_or_stop_name_part): # If coord fields are empty, this might be a line def
            current_line = line_info_or_stop_name_part # Assuming it's a line number/name
            # if it's just a line definition, skip adding a station from this row
            if not stop_name and not coord1 and not coord2:
                 continue
        
        if not stop_name: # Skip if no stop name after potential line processing
            continue
            
        def add_station(coords_tuple, direction_val):
            nonlocal station_id
            if coords_tuple:
                key = (stop_name, coords_tuple[0], coords_tuple[1])
                if key not in stations:
                    stations[key] = {
                        'id': station_id,
                        'name': f"{stop_name} ({direction_val})",
                        'latitude': coords_tuple[0],
                        'longitude': coords_tuple[1],
                        'line_numbers': [current_line] if current_line else ['Unknown'],
                        'original_name': stop_name,
                        'direction': direction_val,
                    }
                    station_id += 1
                else:
                    if current_line and current_line not in stations[key]['line_numbers']:
                        stations[key]['line_numbers'].append(current_line)
        
        parsed_coord1 = parse_coordinates(coord1)
        parsed_coord2 = parse_coordinates(coord2)

        add_station(parsed_coord1, 1)
        add_station(parsed_coord2, 2)
    
    return list(stations.values())


@app.post("/find_nearest_stations/", response_model=NearestStationsResponse)
async def find_nearest_stations(
    coordinates: str = Form(...),  # MODIFICATION: Expect coordinates as a string from the form
    stations_file: UploadFile = File(...)
):
    """
    Find nearest stations based on uploaded CSV file and user coordinates.
    
    Args:
        coordinates: GPS coordinates as a JSON string (e.g., '{"latitude": 40.7, "longitude": -74.0}')
        stations_file: Uploaded CSV file containing stations data
        
    Returns:
        JSON with nearest stations that can be saved to a file
    """
    try:
        # MODIFICATION: Parse the JSON string into a dictionary
        coordinates_data = json.loads(coordinates)
        # MODIFICATION: Validate and create the Coordinates Pydantic model
        user_coordinates = Coordinates(**coordinates_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON format for 'coordinates' field.")
    except ValidationError as e:
        # Pydantic's ValidationError includes detailed error messages
        raise HTTPException(status_code=422, detail=e.errors())

    # Validate file extension and content type
    if not stations_file.filename.endswith('.csv') or stations_file.content_type not in ['text/csv', 'application/csv', 'application/vnd.ms-excel']:
        raise HTTPException(status_code=400, detail="Only CSV files are supported (text/csv, application/csv, or application/vnd.ms-excel)")
    
    # Read and parse the uploaded CSV file
    try:
        content = await stations_file.read()
        csv_content = content.decode('utf-8') # Ensure your CSV is UTF-8 or handle other encodings
        stations = parse_csv_data_to_stations(csv_content)
            
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid CSV file encoding. Please use UTF-8.")
    except Exception as e:
        # Log the exception for debugging: import logging; logging.exception("CSV parsing error")
        raise HTTPException(status_code=400, detail=f"Error reading or parsing CSV file: {str(e)}")
    
    if not stations:
        raise HTTPException(status_code=400, detail="No valid stations found in the uploaded file.")
    
    # Filter stations by bounding box
    user_latitude, user_longitude = user_coordinates.latitude, user_coordinates.longitude
    
    # Ensure stations from CSV have latitude and longitude before filtering or distance calculation
    valid_stations_for_filter = [s for s in stations if "latitude" in s and "longitude" in s]
    if not valid_stations_for_filter:
         raise HTTPException(status_code=400, detail="Stations in CSV are missing coordinate data.")

    filtered_stations = filter_stations_by_bbox(valid_stations_for_filter, user_latitude, user_longitude)
    
    if not filtered_stations:
        raise HTTPException(status_code=404, detail="No stations found within 10km of the provided coordinates.") # Changed to 404
    
    # Calculate distances and sort
    distances = []
    for station in filtered_stations: # Iterate over already filtered (and validated) stations
        distance = haversine_distance(
            user_latitude, user_longitude,
            station["latitude"], station["longitude"]
        )
        
        station_with_distance = station.copy()
        station_with_distance["distance_km"] = round(distance, 2)
        distances.append(station_with_distance)
    
    # Sort by distance and return top 10
    distances.sort(key=lambda x: x["distance_km"])
    nearest_stations = distances[:10]
    
    if not nearest_stations: # Should not happen if filtered_stations was not empty, but as a safeguard
        return NearestStationsResponse(stations=[])

    return NearestStationsResponse(stations=nearest_stations)