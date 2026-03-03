import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score,confusion_matrix, classification_report
import joblib

# ------------------------------------------------
# 1. Load CLEANED Excel Dataset
# ------------------------------------------------
df = pd.read_excel("cleaned_kc_house_data.xlsx")

# ------------------------------------------------
# 2. Features & Target
# ------------------------------------------------
X = df.drop(columns=["price","sqft_living15","sqft_lot15"])  # Dropping target and less relevant features
y = df["price"]

# ------------------------------------------------
# 3. Train-Test Split
# ------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# ------------------------------------------------
# 4. Train Random Forest Model
# ------------------------------------------------
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# ------------------------------------------------
# 5. Prediction
# ------------------------------------------------
y_pred = model.predict(X_test)

# ------------------------------------------------
# 6. Evaluation
# ------------------------------------------------
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("Random Forest Results")
print("----------------------")
print(f"RMSE: {rmse}")
print(f"R² Score: {r2}")

# ------------------------------------------------
# 7. Save Model
# ------------------------------------------------
joblib.dump(model, "house_price_random_forest.pkl",compress=3)  # Using joblib for better performance and compatibility

print("✅ Model saved as house_price_random_forest.pkl")