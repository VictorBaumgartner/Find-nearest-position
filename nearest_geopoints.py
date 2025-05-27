# from fastapi import FastAPI, HTTPException, File, UploadFile, Form
# from pydantic import BaseModel, model_validator, ValidationError # Added ValidationError
# import math
# from typing import List, Dict, Any, Optional
# import csv
# import io
# import json

# app = FastAPI()

# # Pydantic model for coordinates
# class Coordinates(BaseModel):
#     latitude: float
#     longitude: float

#     @model_validator(mode='after')
#     def check_valid_coordinates(cls, values):
#         # Ensure latitude and longitude are present and are numbers before accessing them
#         lat = values.latitude
#         lon = values.longitude
#         if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
#             raise ValueError("Invalid latitude or longitude values")
#         return values

# # Pydantic model for response
# class NearestStationsResponse(BaseModel):
#     stations: List[Dict[str, Any]]

# # Haversine formula (remains the same)
# def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#     R = 6371
#     lat1_rad = math.radians(lat1)
#     lon1_rad = math.radians(lon1)
#     lat2_rad = math.radians(lat2)
#     lon2_rad = math.radians(lon2)
#     dlon = lon2_rad - lon1_rad
#     dlat = lat2_rad - lat1_rad
#     a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     distance = R * c
#     return distance

# # parse_coordinates function (remains the same)
# def parse_coordinates(coord_string: str) -> Optional[tuple]:
#     if not coord_string or coord_string.strip() == "" or coord_string.strip() == "*":
#         return None
#     try:
#         coord_string = coord_string.strip().strip('"')
#         parts = coord_string.split(',')
#         if len(parts) != 2:
#             return None
#         lat = float(parts[0].strip())
#         lon = float(parts[1].strip())
#         return (lat, lon)
#     except (ValueError, IndexError):
#         return None

# # filter_stations_by_bbox function (remains the same)
# def filter_stations_by_bbox(stations: List[Dict[str, Any]], user_lat: float, user_lon: float, max_distance_km: float = 10) -> List[Dict[str, Any]]:
#     R = 6371
#     lat_range = max_distance_km / 111
#     lon_range = max_distance_km / (111 * math.cos(math.radians(user_lat)))
#     return [
#         station for station in stations
#         if (
#             abs(station["latitude"] - user_lat) <= lat_range
#             and abs(station["longitude"] - user_lon) <= lon_range
#         )
#     ]

# # parse_csv_data_to_stations function (remains the same, assuming it works as intended)
# def parse_csv_data_to_stations(csv_content: str) -> List[Dict[str, Any]]:
#     stations = {}
#     station_id = 1
#     current_line = None
#     csv_file = io.StringIO(csv_content)
#     reader = csv.reader(csv_file, delimiter=',', quotechar='"')
#     for parts in reader:
#         if not parts or not any(parts):
#             continue
#         if len(parts) < 4: # Assuming at least stop_name, coord1, coord2, line_number potentially
#             continue
            
#         stop_name = parts[0].strip()
#         coord1 = parts[1].strip() if len(parts) > 1 else ""
#         coord2 = parts[2].strip() if len(parts) > 2 else ""
#         line_info_or_stop_name_part = parts[3].strip() if len(parts) > 3 else ""

#         # Heuristic to differentiate line numbers from continuation of stop names or other data
#         if line_info_or_stop_name_part.lower().startswith('ligne') or \
#            (not coord1 and not coord2 and line_info_or_stop_name_part): # If coord fields are empty, this might be a line def
#             current_line = line_info_or_stop_name_part # Assuming it's a line number/name
#             # if it's just a line definition, skip adding a station from this row
#             if not stop_name and not coord1 and not coord2:
#                  continue
        
#         if not stop_name: # Skip if no stop name after potential line processing
#             continue
            
#         def add_station(coords_tuple, direction_val):
#             nonlocal station_id
#             if coords_tuple:
#                 key = (stop_name, coords_tuple[0], coords_tuple[1])
#                 if key not in stations:
#                     stations[key] = {
#                         'id': station_id,
#                         'name': f"{stop_name} ({direction_val})",
#                         'latitude': coords_tuple[0],
#                         'longitude': coords_tuple[1],
#                         'line_numbers': [current_line] if current_line else ['Unknown'],
#                         'original_name': stop_name,
#                         'direction': direction_val,
#                     }
#                     station_id += 1
#                 else:
#                     if current_line and current_line not in stations[key]['line_numbers']:
#                         stations[key]['line_numbers'].append(current_line)
        
#         parsed_coord1 = parse_coordinates(coord1)
#         parsed_coord2 = parse_coordinates(coord2)

#         add_station(parsed_coord1, 1)
#         add_station(parsed_coord2, 2)
    
#     return list(stations.values())


# @app.post("/find_nearest_stations/", response_model=NearestStationsResponse)
# async def find_nearest_stations(
#     coordinates: str = Form(...),  # MODIFICATION: Expect coordinates as a string from the form
#     stations_file: UploadFile = File(...)
# ):
#     """
#     Find nearest stations based on uploaded CSV file and user coordinates.
    
#     Args:
#         coordinates: GPS coordinates as a JSON string (e.g., '{"latitude": 40.7, "longitude": -74.0}')
#         stations_file: Uploaded CSV file containing stations data
        
#     Returns:
#         JSON with nearest stations that can be saved to a file
#     """
#     try:
#         # MODIFICATION: Parse the JSON string into a dictionary
#         coordinates_data = json.loads(coordinates)
#         # MODIFICATION: Validate and create the Coordinates Pydantic model
#         user_coordinates = Coordinates(**coordinates_data)
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=422, detail="Invalid JSON format for 'coordinates' field.")
#     except ValidationError as e:
#         # Pydantic's ValidationError includes detailed error messages
#         raise HTTPException(status_code=422, detail=e.errors())

#     # Validate file extension and content type
#     if not stations_file.filename.endswith('.csv') or stations_file.content_type not in ['text/csv', 'application/csv', 'application/vnd.ms-excel']:
#         raise HTTPException(status_code=400, detail="Only CSV files are supported (text/csv, application/csv, or application/vnd.ms-excel)")
    
#     # Read and parse the uploaded CSV file
#     try:
#         content = await stations_file.read()
#         csv_content = content.decode('utf-8') # Ensure your CSV is UTF-8 or handle other encodings
#         stations = parse_csv_data_to_stations(csv_content)
            
#     except UnicodeDecodeError:
#         raise HTTPException(status_code=400, detail="Invalid CSV file encoding. Please use UTF-8.")
#     except Exception as e:
#         # Log the exception for debugging: import logging; logging.exception("CSV parsing error")
#         raise HTTPException(status_code=400, detail=f"Error reading or parsing CSV file: {str(e)}")
    
#     if not stations:
#         raise HTTPException(status_code=400, detail="No valid stations found in the uploaded file.")
    
#     # Filter stations by bounding box
#     user_latitude, user_longitude = user_coordinates.latitude, user_coordinates.longitude
    
#     # Ensure stations from CSV have latitude and longitude before filtering or distance calculation
#     valid_stations_for_filter = [s for s in stations if "latitude" in s and "longitude" in s]
#     if not valid_stations_for_filter:
#          raise HTTPException(status_code=400, detail="Stations in CSV are missing coordinate data.")

#     filtered_stations = filter_stations_by_bbox(valid_stations_for_filter, user_latitude, user_longitude)
    
#     if not filtered_stations:
#         raise HTTPException(status_code=404, detail="No stations found within 10km of the provided coordinates.") # Changed to 404
    
#     # Calculate distances and sort
#     distances = []
#     for station in filtered_stations: # Iterate over already filtered (and validated) stations
#         distance = haversine_distance(
#             user_latitude, user_longitude,
#             station["latitude"], station["longitude"]
#         )
        
#         station_with_distance = station.copy()
#         station_with_distance["distance_km"] = round(distance, 2)
#         distances.append(station_with_distance)
    
#     # Sort by distance and return top 10
#     distances.sort(key=lambda x: x["distance_km"])
#     nearest_stations = distances[:1]
    
#     if not nearest_stations: # Should not happen if filtered_stations was not empty, but as a safeguard
#         return NearestStationsResponse(stations=[])

#     return NearestStationsResponse(stations=nearest_stations)







# Add this to your requirements.txt or install manually:
# geopy>=2.0.0
# fastapi
# uvicorn
# pydantic
# python-multipart (for Form and UploadFile)


from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from pydantic import BaseModel, model_validator, ValidationError
import math
from typing import List, Dict, Any, Optional, Callable, Coroutine 
import csv
import io
import json
import asyncio 
from functools import partial 

# Geopy imports
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeopyError 

app = FastAPI()

# --- Pydantic Models ---

class Coordinates(BaseModel):
    latitude: float
    longitude: float

    @model_validator(mode='after')
    def check_valid_coordinates(cls, values):
        lat = values.latitude
        lon = values.longitude
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude values")
        return values

class Station(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    line_numbers: List[str]
    original_name: str
    direction: int
    distance_km: float
    city: Optional[str] = None
    transport_type: str = "BUS"

class NearestStationsResponse(BaseModel):
    stations: List[Station]

# --- Geocoding Setup ---

AsyncGeocodeCallable = Callable[[str, ...], Coroutine[Any, Any, Optional[Any]]]

async def get_geocode_service() -> AsyncGeocodeCallable:
    if not hasattr(get_geocode_service, "geolocator_instance"):
        get_geocode_service.geolocator_instance = Nominatim(
            user_agent="fastapi_station_finder_app/1.0" 
        )
        get_geocode_service.geocode_rate_limited = RateLimiter(
            get_geocode_service.geolocator_instance.reverse, 
            min_delay_seconds=1, 
            error_wait_seconds=5.0,
            swallow_exceptions=False 
        )

    async def async_geocode_wrapper(query_str: str, **kwargs):
        loop = asyncio.get_event_loop()
        fn = partial(get_geocode_service.geocode_rate_limited, query_str, **kwargs)
        try:
            return await loop.run_in_executor(None, fn)
        except GeopyError as e:
            print(f"GeopyError during geocoding for query '{query_str}': {e}")
            return None 
        except Exception as e:
            print(f"Unexpected error during geocoding executor call for query '{query_str}': {e}")
            return None

    return async_geocode_wrapper


async def get_city_from_coords(
    latitude: float, 
    longitude: float,
    geocode_service: AsyncGeocodeCallable 
) -> Optional[str]:
    query = f"{latitude}, {longitude}"
    try:
        location = await geocode_service(query, language='en', addressdetails=True, timeout=10)
        if location and location.raw and 'address' in location.raw:
            address = location.raw['address']
            city = address.get('city', address.get('town', address.get('village', address.get('county'))))
            return city
        return None
    except GeocoderTimedOut:
        print(f"Warning: Geocoding timed out for {query}")
        return None
    except GeocoderUnavailable:
        print(f"Warning: Geocoding service unavailable for {query}")
        return None
    except Exception as e:
        print(f"Warning: An unexpected error occurred during geocoding for {query}: {e}")
        return None

# --- Helper Functions (Math, Parsing) ---

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def parse_coordinates(coord_string: str) -> Optional[tuple[float, float]]:
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

def filter_stations_by_bbox(
    stations: List[Dict[str, Any]], 
    user_lat: float, user_lon: float, 
    max_distance_km: float = 10.0
) -> List[Dict[str, Any]]:
    lat_range = max_distance_km / 111.0
    lon_range = max_distance_km / (111.0 * math.cos(math.radians(user_lat))) if math.cos(math.radians(user_lat)) != 0 else max_distance_km / 111.0
    
    return [
        s for s in stations
        if "latitude" in s and "longitude" in s and
           abs(s["latitude"] - user_lat) <= lat_range and
           abs(s["longitude"] - user_lon) <= lon_range
    ]

def parse_csv_data_to_stations(csv_content: str) -> List[Dict[str, Any]]:
    stations_dict: Dict[tuple, Dict[str, Any]] = {} 
    station_id_counter = 1
    current_line: Optional[str] = None
    csv_file = io.StringIO(csv_content)
    reader = csv.reader(csv_file, delimiter=',', quotechar='"')

    for parts in reader:
        if not parts or not any(part.strip() for part in parts):
            continue
        
        stop_name = parts[0].strip() if len(parts) > 0 else ""
        coord1_str = parts[1].strip() if len(parts) > 1 else ""
        coord2_str = parts[2].strip() if len(parts) > 2 else ""
        line_info_candidate = parts[3].strip() if len(parts) > 3 and parts[3] else ""

        is_line_def_row = line_info_candidate.lower().startswith('ligne') or \
                          (not coord1_str and not coord2_str and line_info_candidate and not stop_name)

        if is_line_def_row:
            current_line = line_info_candidate
            if not stop_name:
                continue
        
        if not stop_name:
            continue

        def add_station_entry(coords_tuple: Optional[tuple[float, float]], direction_val: int):
            nonlocal station_id_counter
            if coords_tuple:
                lat, lon = coords_tuple
                station_key = (stop_name, lat, lon)
                if station_key not in stations_dict:
                    stations_dict[station_key] = {
                        'id': station_id_counter,
                        'name': f"{stop_name} (Dir {direction_val})",
                        'latitude': lat,
                        'longitude': lon,
                        'line_numbers': [current_line] if current_line else ['Unknown Line'],
                        'original_name': stop_name,
                        'direction': direction_val,
                    }
                    station_id_counter += 1
                else:
                    if current_line and current_line not in stations_dict[station_key]['line_numbers']:
                        stations_dict[station_key]['line_numbers'].append(current_line)
        
        parsed_coord1 = parse_coordinates(coord1_str)
        parsed_coord2 = parse_coordinates(coord2_str)

        if parsed_coord1: add_station_entry(parsed_coord1, 1)
        if parsed_coord2: add_station_entry(parsed_coord2, 2)
            
    return list(stations_dict.values())

# --- FastAPI Endpoint ---

@app.post("/find_nearest_stations/", response_model=NearestStationsResponse)
async def find_nearest_stations_endpoint(
    coordinates: str = Form(...),  # pyright: ignore[reportInvalidTypeForm]
    stations_file: UploadFile = File(...),  # pyright: ignore[reportInvalidTypeForm]
    geocode_service: AsyncGeocodeCallable = Depends(get_geocode_service)
):
    """
    Find nearest stations based on uploaded CSV file and user coordinates.
    Adds city (via geocoding), distance, and transport type (BUS) to station data.
    """
    try:
        coordinates_data = json.loads(coordinates)
        user_coordinates = Coordinates(**coordinates_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON format for 'coordinates' field.")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    if not stations_file.filename or not stations_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV files are supported.")
    
    expected_content_types = ['text/csv', 'application/vnd.ms-excel', 'application/csv']
    if stations_file.content_type not in expected_content_types:
         print(f"Warning: Received unexpected Content-Type '{stations_file.content_type}' for CSV file. Processing anyway.")

    content = await stations_file.read()
    try:
        csv_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_content = content.decode('latin-1')
            print("Info: CSV file decoded using latin-1 as UTF-8 failed.")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid CSV file encoding. Please use UTF-8 or latin-1.")

    try:
        all_stations_from_csv = parse_csv_data_to_stations(csv_content)
    except Exception as e:
        print(f"Critical error during CSV parsing: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading or parsing CSV file: {str(e)}")

    if not all_stations_from_csv:
        raise HTTPException(status_code=400, detail="No valid stations found in the uploaded file.")
    
    user_lat, user_lon = user_coordinates.latitude, user_coordinates.longitude
    
    stations_in_bbox = filter_stations_by_bbox(all_stations_from_csv, user_lat, user_lon, max_distance_km=10.0)

    if not stations_in_bbox:
        raise HTTPException(status_code=404, detail="No stations found within the initial ~10km search area.")
    
    stations_with_distances = []
    for station_data in stations_in_bbox:
        distance = haversine_distance(
            user_lat, user_lon,
            station_data["latitude"], station_data["longitude"]
        )
        
        if distance <= 10.0:
            station_data_copy = station_data.copy()
            station_data_copy["distance_km"] = round(distance, 2)
            stations_with_distances.append(station_data_copy)
    
    if not stations_with_distances:
        raise HTTPException(status_code=404, detail="No stations found within 10km (precise distance) of the provided coordinates.")
    
    stations_with_distances.sort(key=lambda x: x["distance_km"])
    
    top_raw_stations = stations_with_distances[:1] 
    
    enriched_stations_list: List[Station] = []
    for station_raw_data in top_raw_stations:
        city_name = await get_city_from_coords(
            station_raw_data["latitude"], 
            station_raw_data["longitude"],
            geocode_service
        )
        
        try:
            station_obj = Station(
                **station_raw_data, 
                city=city_name
            )
            enriched_stations_list.append(station_obj)
        except ValidationError as e:
            print(f"Pydantic validation error for station data (ID: {station_raw_data.get('id', 'Unknown')}): {e.errors()}")

    if not enriched_stations_list:
        raise HTTPException(status_code=404, detail="No stations could be processed and validated after enrichment.")

    return NearestStationsResponse(stations=enriched_stations_list)

# --- How to Run ---
# 1. Save this code as `main.py` (or your preferred filename like `nearest_geopoints.py`).
# 2. Install dependencies: `pip install fastapi uvicorn pydantic geopy python-multipart`
# 3. Run the FastAPI server: `uvicorn main:app --reload`
#
# --- Example cURL to test ---
# curl -X POST "http://127.0.0.1:8000/find_nearest_stations/" \
#      -F "coordinates={\"latitude\": 48.8566, \"longitude\": 2.3522}" \
#      -F "stations_file=@path/to/your/stations.csv"
#
# (Replace `path/to/your/stations.csv` with the actual path to your CSV file,
#  and `main:app` with `your_filename:app` if you used a different name for the Python file)