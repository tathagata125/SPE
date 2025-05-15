import pandas as pd
import pickle
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Ensure consistent data path
DATA_PATH = "data/cleaned_weather.csv"
MODEL_PATH = "model.pkl"
METRICS_PATH = "metrics.json"

# Add error handling for file operations
try:
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Successfully loaded data from {DATA_PATH}")
except FileNotFoundError:
    print(f"❌ Error: Could not find {DATA_PATH}")
    exit(1)
except Exception as e:
    print(f"❌ Error loading data: {str(e)}")
    exit(1)

# Create consistent lag features (3 days to match predict.py)
features_to_lag = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']
for feature in features_to_lag:
    for lag in range(1, 4):  # Changed from 15 to 4 to create 3 days of lag
        df[f"{feature}_t-{lag}"] = df[feature].shift(lag)

df.dropna(inplace=True)

X = df.drop(columns=['time', 'tavg'])  # Exclude original target and date
y = df['tavg']                         # Predict today's tavg

# Print feature names for debugging
print(f"Training with {len(X.columns)} features: {', '.join(X.columns[:5])}...")

X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

# Train model with error handling
try:
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("✅ Model trained successfully")
except Exception as e:
    print(f"❌ Error training model: {str(e)}")
    exit(1)

# Evaluate model
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")

# Save model and metrics with error handling
try:
    # Add version information to help with compatibility
    import sklearn
    version_info = {
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "sklearn_version": sklearn.__version__
    }
    print("📊 Training with:")
    print(f"  - pandas: {version_info['pandas_version']}")
    print(f"  - numpy: {version_info['numpy_version']}")
    print(f"  - scikit-learn: {version_info['sklearn_version']}")
    
    # Save model with version info
    with open(MODEL_PATH, "wb") as f:
        pickle.dump((model, version_info), f)
    
    # Update metrics to include version info
    metrics = {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "feature_count": len(X.columns),
        "training_samples": len(X_train),
        "package_versions": version_info
    }
    
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f)
        
    print(f"✅ Model saved to {MODEL_PATH}")
    print(f"✅ Metrics saved to {METRICS_PATH}")
except Exception as e:
    print(f"❌ Error saving model or metrics: {str(e)}")
    exit(1)

