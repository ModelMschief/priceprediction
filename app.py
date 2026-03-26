from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import joblib
import pandas as pd
import requests
import jwt
import datetime
import os
import json
import uuid
from functools import wraps
import DB_manager

# JWT Configuration
SECRET_KEY = "smart_dwellings_jwt_secret_2026"
TOKEN_EXPIRY_HOURS = 24

# Upload Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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

def generate_token(user_id, email):
    """Creates a signed JWT token with user info and expiry."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def token_required(f):
    """Decorator to protect routes with JWT authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401
        
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = {"user_id": decoded["user_id"], "email": decoded["email"]}
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please login again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token. Please login again."}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

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
    phone = data.get("phone")
    address = data.get("address")

    if not username or not email or not password or not phone or not address:
        return jsonify({"error": "Missing required fields"}), 400

    hashed_password = generate_password_hash(password)

    success, message = DB_manager.create_user(username, email, hashed_password, phone, address)
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

    # user = (id, username, password_hash, phone, address)
    if user and check_password_hash(user[2], password):
        token = generate_token(user[0], email)
        return jsonify({
            "status": "success", 
            "message": "Login successful", 
            "user": {
                "id": user[0], 
                "username": user[1], 
                "email": email,
                "phone": user[3],
                "address": user[4]
            },
            "token": token
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
@token_required
def predict_price(current_user):
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

# ==========================================
# HOUSE LISTING API ENDPOINTS
# ==========================================

@app.route("/api/houses", methods=["POST"])
@token_required
def add_house(current_user):
    """Add a new house listing with optional image uploads."""
    # Handle both JSON and multipart/form-data
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    else:
        data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Required fields validation
    required = ["title", "price", "bedrooms", "bathrooms", "sqft_living", "address"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Handle image uploads
    uploaded_images = []
    if request.files:
        files = request.files.getlist("images")
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, unique_name))
                uploaded_images.append(unique_name)

    # Build house data dict
    house_data = {
        "title": data["title"],
        "description": data.get("description", ""),
        "price": float(data["price"]),
        "bedrooms": int(data["bedrooms"]),
        "bathrooms": float(data["bathrooms"]),
        "sqft_living": int(data["sqft_living"]),
        "sqft_lot": int(data["sqft_lot"]) if data.get("sqft_lot") else None,
        "floors": float(data["floors"]) if data.get("floors") else None,
        "waterfront": int(data.get("waterfront", 0)),
        "view": int(data.get("view", 0)),
        "condition": int(data.get("condition", 3)),
        "grade": int(data.get("grade", 7)),
        "yr_built": int(data["yr_built"]) if data.get("yr_built") else None,
        "yr_renovated": int(data.get("yr_renovated", 0)),
        "address": data["address"],
        "city": data.get("city"),
        "state": data.get("state"),
        "zipcode": data.get("zipcode"),
        "lat": float(data["lat"]) if data.get("lat") else None,
        "long": float(data["long"]) if data.get("long") else None,
        "parking": int(data.get("parking", 0)),
        "garden": int(data.get("garden", 0)),
        "pool": int(data.get("pool", 0)),
        "furnished": int(data.get("furnished", 0)),
        "images": uploaded_images
    }

    success, result = DB_manager.create_house(current_user["user_id"], house_data)
    if success:
        return jsonify({"status": "success", "message": "House listed successfully", "house_id": result}), 201
    else:
        return jsonify({"error": result}), 500

@app.route("/api/houses", methods=["GET"])
def get_all_houses():
    """Get all house listings (public)."""
    houses = DB_manager.get_all_houses()
    # Parse images JSON string back to list
    for house in houses:
        if isinstance(house.get("images"), str):
            house["images"] = json.loads(house["images"])
    return jsonify({"status": "success", "houses": houses}), 200

@app.route("/api/my-houses", methods=["GET"])
@token_required
def get_my_houses(current_user):
    """Get houses listed by the logged-in seller."""
    houses = DB_manager.get_houses_by_seller(current_user["user_id"])
    for house in houses:
        if isinstance(house.get("images"), str):
            house["images"] = json.loads(house["images"])
    return jsonify({"status": "success", "houses": houses}), 200

@app.route("/uploads/<filename>")
def serve_upload(filename):
    """Serve uploaded house images."""
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)