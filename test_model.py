import joblib
import pandas as pd

# 1. Load the model using joblib instead of pickle
# This fixes the STACK_GLOBAL error
model = joblib.load('C:\\Users\\SHEBIN\\OneDrive\\Desktop\\vscode\\trafic\\house_price_random_forest.pkl') 

# 2. Hardcode your new features
new_house_data = {
    'bedrooms': None,
    'bathrooms': 4,
    'sqft_living': 3900,
    'sqft_lot': 3000,
    'floors': 3,
    'waterfront': 0,
    'view': 0,
    'condition': 3,
    'grade': 8,
    'yr_built': 2010,
    'yr_renovated': 22015,
    'lat': 47.5112,
    'long': -122.257,
}

# 3. Convert to DataFrame and predict
test_df = pd.DataFrame([new_house_data])
prediction = model.predict(test_df)

print(f"Predicted Price: ${prediction[0]:,.2f}")