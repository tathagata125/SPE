import pandas as pd
import pickle
import numpy as np
import os
import sys

# Ensure consistent paths
DATA_PATH = "data/cleaned_weather.csv"
MODEL_PATH = "model.pkl"

def predict_next_day():
    # Load cleaned data with error handling
    try:
        df = pd.read_csv(DATA_PATH)
        print(f"✅ Successfully loaded data from {DATA_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: Could not find {DATA_PATH}")
        return None
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return None

    # Create lag features for 3 days - same as in train.py
    features_to_lag = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']
    for feature in features_to_lag:
        for lag in range(1, 4):
            df[f"{feature}_t-{lag}"] = df[feature].shift(lag)

    df.dropna(inplace=True)

    # Prepare latest row (prediction input)
    try:
        X = df.drop(columns=['time', 'tavg'])  # Match training input
        X_new = X.tail(1)
        
        # Debug info
        print(f"Prediction input has {len(X_new.columns)} features")
    except KeyError as e:
        print(f"❌ Error: Missing column in data: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error preparing prediction data: {str(e)}")
        return None

    # Load model with error handling
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        print(f"✅ Successfully loaded model from {MODEL_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: Could not find model at {MODEL_PATH}")
        return None
    except Exception as e:
        print(f"❌ Error loading model: {str(e)}")
        return None

    # Verify feature names match
    model_features = set(model.feature_names_in_)
    input_features = set(X_new.columns)
    
    if not model_features.issubset(input_features):
        missing = model_features - input_features
        print(f"❌ Error: Missing features in prediction data: {missing}")
        return None
    
    # Ensure columns match model's expected features and order
    X_new = X_new[model.feature_names_in_]

    # Predict with error handling
    try:
        prediction = model.predict(X_new)[0]
        print(f"🌡️ Predicted average temperature for tomorrow: {prediction:.2f}°C")
        return prediction
    except Exception as e:
        print(f"❌ Error making prediction: {str(e)}")
        return None

if __name__ == "__main__":
    prediction = predict_next_day()
    if prediction is None:
        sys.exit(1)  # Exit with error code

