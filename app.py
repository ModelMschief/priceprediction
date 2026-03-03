from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import requests
import DB_manager

# 1. Initialize Flask App (Pure API)
app = Flask(__name__)

# 2. Configure CORS (Crucial so your separate frontend can talk to this API)
CORS(app, resources={r"/*": {"origins": "*"}})

# ==========================================
# DATABASE SETUP (SQLite3)
# ==========================================


DB_manager.init_db()

# ==========================================
# ML MODEL SETUP
# ==========================================
try:
    model = joblib.load("house_price_random_forest.pkl")
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    model = None

def get_location_from_ip(ip_address):
    if ip_address == "127.0.0.1" or ip_address == "::1":
        return 47.6062, -122.3321 
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        data = response.json()
        if data["status"] == "success":
            return data["lat"], data["lon"]
    except Exception as e:
        print(f"IP Geolocation failed: {e}")
    return 47.5600, -122.2138 

def get_val(data, key, default):
    val = data.get(key)
    return val if val is not None else default

# ==========================================
# AUTHENTICATION API ENDPOINTS
# ==========================================

@app.route("/api/register", methods=["POST"])
def register_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    # Hashing password even though security isn't the main focus, it's best practice
    hashed_password = generate_password_hash(password)

    success, message = DB_manager.create_user(username, email, hashed_password)
    if success:
        return jsonify({"status": "success", "message": message}), 201
    else:
        return jsonify({"error": message}), 400

@app.route("/api/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email")
    password = data.get("password")

    user = DB_manager.get_user_by_email(email)

    # user[2] is the hashed password from the DB
    if user and check_password_hash(user[2], password):
        return jsonify({
            "status": "success", 
            "message": "Login successful", 
            "user": {"id": user[0], "username": user[1], "email": email}
        }), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        return jsonify({"error": "Missing required fields"}), 400

    hashed_password = generate_password_hash(new_password)

    success = DB_manager.update_user_password(email, hashed_password)
    if success:
        return jsonify({"status": "success", "message": "Password updated successfully"}), 200
    else:
        return jsonify({"error": "Email not found"}), 404
# ==========================================
# ML PREDICTION API ENDPOINT
# ==========================================

@app.route("/predict", methods=["POST"])
def predict_price():
    if model is None:
        return jsonify({"error": "Model not loaded on the server."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    lat = data.get("lat")
    long = data.get("long")
    if lat is None or long is None:
        lat, long = get_location_from_ip(client_ip)

    bedrooms = data.get("bedrooms")
    bathrooms = data.get("bathrooms")
    sqft_living = data.get("sqft_living")
    yr_built = data.get("yr_built")

    sqft_lot = data.get("sqft_lot")
    if sqft_lot is None and sqft_living is not None:
        sqft_lot = sqft_living * 3

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

    df = pd.DataFrame([input_data])

    try:
        prediction = model.predict(df)[0]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "status": "success",
        "predicted_price": float(prediction),
        "used_location": {"lat": lat, "long": long}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)