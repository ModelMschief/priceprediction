from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import requests

# 1. Initialize Flask App
app = Flask(__name__)

# 2. Configure CORS (Allows your frontend to communicate with this backend)
CORS(app, resources={r"/*": {"origins": "*"}})

# 3. Load the Trained Model
# Make sure "house_price_random_forest.pkl" is in the same folder as this script
try:
    model = joblib.load("house_price_random_forest.pkl")
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    model = None

# Helper function to get Lat/Long from IP Address using a Free Public API
def get_location_from_ip(ip_address):
    # If running locally, default to Seattle's coordinates
    if ip_address == "127.0.0.1" or ip_address == "::1":
        return 47.6062, -122.3321 
    
    try:
        # Using ip-api.com (Free, no API key required for HTTP)
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        data = response.json()
        print(f"ip geolocation response: {data['lat']} and {data['lon']}")  # Debugging line
        if data["status"] == "success":
            return data["lat"], data["lon"]
    except Exception as e:
        print(f"IP Geolocation failed: {e}")
    
    # Fallback to average King County coordinates if API fails
    return 47.5600, -122.2138 

# Helper function to safely extract values with defaults
def get_val(data, key, default):
    val = data.get(key)
    return val if val is not None else default

# 4. The Prediction Endpoint
@app.route("/predict", methods=["POST"])
def predict_price():
    if model is None:
        return jsonify({"error": "Model not loaded on the server."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    # Extract user IP
    # We check 'X-Forwarded-For' first in case the app is behind a proxy in production
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Impute Missing Location Data
    lat = data.get("lat")
    long = data.get("long")
    if lat is None or long is None:
        lat, long = get_location_from_ip(client_ip)

    # Core required fields
    bedrooms = data.get("bedrooms")
    bathrooms = data.get("bathrooms")
    sqft_living = data.get("sqft_living")
    yr_built = data.get("yr_built")

    # Impute missing optional data
    sqft_lot = data.get("sqft_lot")
    if sqft_lot is None and sqft_living is not None:
        sqft_lot = sqft_living * 3

    # Prepare data precisely as the model expects it (13 features)
    input_data = {
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "sqft_living": sqft_living,
        "sqft_lot": sqft_lot,
        "floors": get_val(data, "floors", 1.0),
        "waterfront": get_val(data, "waterfront", 0),
        "view": get_val(data, "view", 0),
        "condition": get_val(data, "condition", 3),
        "grade": get_val(data, "grade", 7),
        "yr_built": yr_built,
        "yr_renovated": get_val(data, "yr_renovated", 0),
        "lat": lat,
        "long": long
    }

    # Convert to pandas DataFrame
    df = pd.DataFrame([input_data])

    # Predict
    try:
        prediction = model.predict(df)[0]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "status": "success",
        "predicted_price": float(prediction),
        "used_location": {"lat": lat, "long": long}
    })

# Run the server automatically when executing this file
if __name__ == "__main__":
    # Running on port 8000 so the frontend code doesn't need to change its BASE_URL
    app.run(host="0.0.0.0", port=8000, debug=True)