# **Geopoint Proximity API**

This project provides a simple FastAPI application that calculates the proximity of predefined geopoints to a user's location, reading both the geopoints data and the user's location from JSON files. It returns the top 10 nearest locations.

## **Features ✨**

* 🗺️ Reads a list of geopoints from a JSON file.  
* 📍 Reads the user's current location from a separate JSON file.  
* 📏 Calculates the distance between the user's location and each geopoint using the Haversine formula.  
* 📊 Sorts the geopoints by distance from the user.  
* ✅ Returns the top 10 nearest geopoints via a GET API endpoint.

## **Prerequisites 📋**

* 🐍 Python 3.7+  
* 📦 pip package installer

## **Installation**

1. Clone or download the project files (the Python script and the two JSON files).  
2. Navigate to the project directory in your terminal.  
3. Install the required Python packages:  
   pip install fastapi uvicorn pydantic

## **Project Structure**

Make sure you have the following files in the same directory:

* main.py: The FastAPI application code.  
* geopoints.json: The JSON file containing the list of locations.  
* user\_location.json: The JSON file containing the user's single location.

## **JSON File Formats**

### **geopoints.json**

This file should contain a JSON array (list) of location objects. Each object must have the following keys:

* id: A unique identifier (integer or string).  
* name: The name of the location (string).  
* latitude: The latitude coordinate (number).  
* longitude: The longitude coordinate (number).

Example:  
\[  
  {"id": 1, "name": "Location A", "latitude": 10.123, "longitude": 20.456},  
  {"id": 2, "name": "Location B", "latitude": 11.789, "longitude": 21.012}  
  // ... more locations  
\]

### **user\_location.json**

This file should contain a single JSON object with the user's location. It must have the following keys:

* latitude: The user's latitude coordinate (number).  
* longitude: The user's longitude coordinate (number).

Example:  
{"latitude": 30.654, "longitude": 40.987}

## **Running the Application**

1. Ensure you have the main.py, geopoints.json, and user\_location.json files in the same directory.  
2. Open your terminal in that directory.  
3. Run the application using uvicorn:  
   uvicorn main:app \--reload

   The \--reload flag is useful during development as it restarts the server whenever you make changes to the code.  
4. The application will start, typically running on http://127.0.0.1:8000. You should see output in the terminal indicating that the server is running and that the geopoints have been loaded.

## **Using the API**

The application exposes a single GET endpoint:

* **GET /nearest\_geopoints\_from\_file/**

This endpoint does not require any parameters in the request body or URL. When accessed, it will:

1. Read the user's location from user\_location.json.  
2. Use the geopoints loaded from geopoints.json during startup.  
3. Calculate distances and find the nearest 10\.  
4. Return a JSON array of the top 10 nearest geopoints, including their calculated distance in kilometers.

Example Response:  
\[  
  {  
    "geopoint": {"id": 1, "name": "Nearest Location", "latitude": ... , "longitude": ...},  
    "distance\_km": 0.5  
  },  
  {  
    "geopoint": {"id": 5, "name": "Second Nearest", "latitude": ... , "longitude": ...},  
    "distance\_km": 1.2  
  }  
  // ... up to 10 results  
\]

You can access this endpoint using a web browser (for a simple GET request) or tools like curl, Postman, or by writing a client script.  
Example using curl:  
curl http://127.0.0.1:8000/nearest\_geopoints\_from\_file/

## **Error Handling 🚨**

The application includes basic error handling for:

* ❌ Files not found (geopoints.json, user\_location.json).  
* ❌ Invalid JSON format in the input files.  
* ❌ Incorrect data structure within the JSON files (e.g., missing keys, wrong data types).  
* ❌ If geopoints fail to load on startup, the endpoint will return a 500 error.

If an error occurs, the API will return an HTTP 500 status code with a detail message indicating the nature of the error.

## **Extending the Project 🚀**

* **Dynamic User Location:** Modify the /nearest\_geopoints/ endpoint (from the first version) to accept user location in the request body if you need to handle different user positions without changing user\_location.json.  
* **Database Integration:** Instead of reading from geopoints.json on startup, load locations from a database (like PostgreSQL, SQLite, MongoDB, etc.) for larger datasets and dynamic updates.  
* **Configuration:** Use environment variables or a configuration file to specify the paths for the JSON files.  
* **More Robust Validation:** Add more comprehensive Pydantic models for the geopoint data structure.  
* **Pagination:** Implement pagination if you need to return more than just the top 10 results in batches.  
* **Caching:** For very large lists of geopoints, consider caching distance calculations or using spatial indexing techniques (like R-trees) for faster lookups.