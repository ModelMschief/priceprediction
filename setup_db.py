import pandas as pd
import json
import uuid
import DB_manager
import os
from werkzeug.security import generate_password_hash

def run_setup():
    print("Initialize DB...")
    # This will create tables if they don't exist
    DB_manager.init_db()

    csv_path = 'indian_property_mock_data_v2.csv'
    if not os.path.exists(csv_path):
        print(f"File {csv_path} not found!")
        return
    
    print("Loading CSV...")
    df = pd.read_csv(csv_path)

    # Convert any NaN to None for correct DB insertion
    df = df.where(pd.notnull(df), None)

    inserted_users = {} # track by email
    
    print("Processing properties...")
    for idx, row in df.iterrows():
        # Handle Seller Creation
        seller_email = row.get('seller_email')
        seller_name = row.get('seller_name')
        seller_phone = row.get('seller_phone')
        
        # fallback string to ensure string type for phone
        if seller_phone is not None:
             seller_phone = str(seller_phone)
             
        # create strong random password
        random_pwd = uuid.uuid4().hex
        hashed_pwd = generate_password_hash(random_pwd)

        # check if we already processed this user in this loop or DB
        db_user = DB_manager.get_user_by_email(seller_email)
        
        if db_user:
            seller_id = db_user[0]
        else:
            # Check phone is unique too, if fails, we might get an error but we try
            success, msg = DB_manager.create_user(
                username=seller_name,
                email=seller_email,
                hashed_password=hashed_pwd,
                phone=seller_phone,
                address=f"{row.get('city')}, {row.get('state')}" # Using property loc as their address
            )
            
            if success:
                db_user_new = DB_manager.get_user_by_email(seller_email)
                seller_id = db_user_new[0]
            else:
                # If error (e.g. phone already exists but email didnt), fetch by phone might be needed, but assume mock data has 1to1
                print(f"Error creating seller {seller_email}: {msg}")
                continue # skip this house

        # Parse images string to actual python list
        images_str = row.get('images', '[]')
        images_list = []
        if isinstance(images_str, str):
            try:
                images_list = json.loads(images_str)
            except Exception:
                pass
        else:
             images_list = []
        
        house_data = {
            "title": row.get('title'),
            "description": row.get('description', ''),
            "price": float(row.get('price')) if row.get('price') is not None else 0.0,
            "bedrooms": int(row.get('bedrooms')) if row.get('bedrooms') is not None else 0,
            "bathrooms": float(row.get('bathrooms')) if row.get('bathrooms') is not None else 0.0,
            "sqft_living": int(row.get('sqft_living')) if row.get('sqft_living') is not None else 0,
            "sqft_lot": int(row.get('sqft_lot')) if row.get('sqft_lot') is not None else None,
            "floors": float(row.get('floors')) if row.get('floors') is not None else None,
            "waterfront": int(row.get('waterfront', 0)) if row.get('waterfront') is not None else 0,
            "view": int(row.get('view', 0)) if row.get('view') is not None else 0,
            "condition": int(row.get('condition', 3)) if row.get('condition') is not None else 3,
            "grade": int(row.get('grade', 7)) if row.get('grade') is not None else 7,
            "yr_built": int(row.get('yr_built')) if row.get('yr_built') is not None else None,
            "yr_renovated": int(row.get('yr_renovated', 0)) if row.get('yr_renovated') is not None else 0,
            "address": row.get('address'),
            "city": row.get('city'),
            "state": row.get('state'),
            "zipcode": row.get('zipcode'),
            "lat": float(row.get('lat')) if row.get('lat') is not None else None,
            "long": float(row.get('long')) if row.get('long') is not None else None,
            "parking": int(row.get('parking', 0)) if row.get('parking') is not None else 0,
            "garden": int(row.get('garden', 0)) if row.get('garden') is not None else 0,
            "pool": int(row.get('pool', 0)) if row.get('pool') is not None else 0,
            "furnished": int(row.get('furnished', 0)) if row.get('furnished') is not None else 0,
            "images": images_list
        }

        # Create house
        success, h_msg = DB_manager.create_house(seller_id, house_data)
        if not success:
             print(f"Error inserting property {house_data['title']}: {h_msg}")

    print("DB Setup Complete!")

if __name__ == "__main__":
    run_setup()
