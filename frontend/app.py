import streamlit as st
import pandas as pd
import pickle
import numpy as np
import os
import requests

# Set page configuration
st.set_page_config(page_title="Weather Predictor", layout="wide")

# Apply styling
st.markdown(
    """
    <style>
    body {
        background-color: #0e1117;
        color: #ffffff;
    }
    .big-font {
        font-size: 28px !important;
        text-align: center;
    }
    .emoji {
        font-size: 40px !important;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:5001")

# Update the paths to work in both containerized and local environments
DATA_PATH = "/app/data/cleaned_weather.csv"  # Direct path to mounted volume in container
MODEL_PATH = "/app/data/model.pkl"           # Direct path to mounted volume in container

# Fallback paths for local development
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/cleaned_weather.csv")
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/model.pkl")

st.title("🌦️ 3-Day Weather Forecast - Bangalore")
st.write("Using past 3 days of weather data to predict upcoming average temperatures.")

# Load data and model with error handling
try:
    # Try loading from local path first
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
    else:
        # Try alternative paths
        alt_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/cleaned_weather.csv")
        if os.path.exists(alt_data_path):
            df = pd.read_csv(alt_data_path)
        else:
            # Try loading from backend API
            try:
                response = requests.get(f"{BACKEND_URL}/data/cleaned")
                if response.status_code == 200:
                    df = pd.read_json(response.content)
                else:
                    raise Exception(f"Could not load data from API: {response.status_code}")
            except:
                raise Exception("Could not find cleaned_weather.csv in any location")
    
    df = df[["tavg", "tmin", "tmax", "prcp", "wspd"]].copy()
    
    # Load trained model - try multiple locations
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    else:
        # Try alternative model path
        alt_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend/model.pkl")
        if os.path.exists(alt_model_path):
            with open(alt_model_path, "rb") as f:
                model = pickle.load(f)
        else:
            # Try to get model from backend API
            try:
                response = requests.get(f"{BACKEND_URL}/model")
                if response.status_code == 200:
                    model = pickle.loads(response.content)
                else:
                    raise Exception(f"Could not load model from API: {response.status_code}")
            except:
                raise Exception("Could not find model.pkl in any location")
    
    st.success("✅ Data and model loaded successfully")
except Exception as e:
    st.error(f"❌ Error loading data or model: {str(e)}")
    st.stop()

# Weather description helper
def describe_weather(temp, prcp=0, wspd=0):
    if prcp > 10:
        return "🌧️ Heavy Rain"
    elif prcp > 2:
        return "🌦️ Light Rain"
    elif wspd > 25:
        return "💨 Windy"
    elif temp >= 35:
        return "🔥 Very Hot"
    elif temp >= 30:
        return "☀️ Hot"
    elif temp >= 24:
        return "🌤️ Pleasant"
    elif temp >= 18:
        return "🌫️ Cool"
    elif temp >= 10:
        return "❄️ Cold"
    else:
        return "🧊 Freezing"

# Forecast next 3 days
try:
    predictions = []
    future_df = df.copy()

    for day in range(1, 4):
        # Create lag features - same as in train.py and predict.py
        for feature in ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']:
            for lag in range(1, 4):
                future_df[f"{feature}_t-{lag}"] = future_df[feature].shift(lag)
        future_df.dropna(inplace=True)
        
        # Prepare prediction features
        X_latest = future_df.drop(columns=['tavg']).iloc[-1:]
        
        # Ensure we only use features the model was trained with
        missing_cols = set(model.feature_names_in_) - set(X_latest.columns)
        for col in missing_cols:
            X_latest[col] = 0  # Add missing columns with default values
        
        # Only select the features the model was trained with, in the correct order
        X_latest = X_latest[model.feature_names_in_]
        
        next_tavg = model.predict(X_latest)[0]
        predictions.append({
            "day": f"Day {day}",
            "temp": round(next_tavg, 2),
            "desc": describe_weather(next_tavg)
        })
        future_df = pd.concat([future_df, pd.DataFrame([{
            'tavg': next_tavg,
            'tmin': future_df['tmin'].iloc[-1],
            'tmax': future_df['tmax'].iloc[-1],
            'prcp': future_df['prcp'].iloc[-1],
            'wspd': future_df['wspd'].iloc[-1],
        }])], ignore_index=True)
except Exception as e:
    st.error(f"❌ Error generating predictions: {str(e)}")
    st.stop()

# Layout: 3 columns for 3 days
cols = st.columns(3)
for i, col in enumerate(cols):
    with col:
        st.markdown(f"<div class='emoji'>{predictions[i]['desc']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>{predictions[i]['day']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>{predictions[i]['temp']} °C</div>", unsafe_allow_html=True)

# --- Sidebar Manual Input ---
st.sidebar.markdown("## 🔧 Manual Forecast")
st.sidebar.write("Enter 3 days of average temperatures to predict tomorrow's.")

custom_input = []
for i in range(3, 0, -1):
    val = st.sidebar.number_input(f"Day -{i} tavg (°C)", min_value=-10.0, max_value=50.0, value=25.0, step=0.1, key=f"tavg_{i}")
    custom_input.append(val)

if st.sidebar.button("Predict from custom data"):
    try:
        input_dict = {}

        # Add tavg lags
        for i in range(1, 4):
            input_dict[f"tavg_t-{i}"] = [custom_input[-i]]

        # Fill missing features required by the model
        for col in model.feature_names_in_:
            if col not in input_dict:
                if col in df.columns:
                    input_dict[col] = [df[col].median()]
                else:
                    try:
                        base_col = col.split("_t-")[0]
                        if base_col in df.columns:
                            input_dict[col] = [df[base_col].median()]
                        else:
                            input_dict[col] = [0.0]
                    except:
                        input_dict[col] = [0.0]

        X_manual = pd.DataFrame(input_dict)
        X_manual = X_manual[model.feature_names_in_]

        pred = model.predict(X_manual)[0]
        desc = describe_weather(pred)

        st.subheader("📍 Prediction from Manual Input")
        st.markdown(f"<div class='emoji'>{desc}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>Predicted tavg: {pred:.2f} °C</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Error generating manual prediction: {str(e)}")

# Sidebar section for API interaction
st.sidebar.markdown("---")
st.sidebar.markdown("## 📤 Retrain Model with New Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file with new weather data", type="csv")

if uploaded_file is not None and st.sidebar.button("Retrain Model"):
    try:
        api_url = f"{BACKEND_URL}/upload/"
        st.sidebar.info(f"Sending data to {api_url}")
        
        response = requests.post(api_url, files={"file": (uploaded_file.name, uploaded_file.getvalue())})

        if response.status_code == 200:
            st.sidebar.success("✅ Data uploaded and retraining started!")
        else:
            st.sidebar.error(f"❌ Failed: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.sidebar.error(f"❌ Error contacting API: {str(e)}")