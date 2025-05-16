import streamlit as st
import pandas as pd
import pickle
import numpy as np
import os
import requests
import logging
import json
from datetime import datetime
import time

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'frontend_{datetime.now().strftime("%Y-%m-%d")}.log')

# Custom JSON formatter for ELK compatibility
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "function": record.funcName,
            "line_number": record.lineno,
            "service": "weather_ops_frontend"
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Set up the logger
logger = logging.getLogger("weather_ops_frontend")
logger.setLevel(logging.INFO)

# File handler for JSON logs
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(JsonFormatter())
logger.addHandler(file_handler)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

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

logger.info("Frontend application started")

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

# Function to load model directly from backend API
def load_model_from_backend():
    try:
        logger.info(f"Fetching latest model from backend: {BACKEND_URL}/model")
        response = requests.get(f"{BACKEND_URL}/model")
        
        if response.status_code == 200:
            try:
                # Get the raw binary content
                model_data = response.content
                
                # Deserialize the model
                loaded_model = pickle.loads(model_data)
                
                # Check if model is a tuple (old format) or direct model object (new format)
                if isinstance(loaded_model, tuple) and len(loaded_model) == 2:
                    logger.info("Detected model in old format (tuple with version info)")
                    actual_model = loaded_model[0]  # Extract just the model from the tuple
                    return actual_model
                else:
                    logger.info("Loaded latest model successfully from backend API")
                    return loaded_model
                    
            except Exception as e:
                logger.error(f"Error deserializing model: {str(e)}", exc_info=True)
                raise Exception(f"Failed to deserialize model: {str(e)}")
        else:
            logger.error(f"Failed to fetch model from API: Status code {response.status_code}")
            raise Exception(f"Could not load model from API: {response.status_code}")
    except Exception as e:
        logger.error(f"Error loading model from API: {str(e)}", exc_info=True)
        raise Exception(f"Failed to fetch model from backend: {str(e)}")

# Load data and model with error handling
try:
    # Always try to get data from backend API first
    try:
        response = requests.get(f"{BACKEND_URL}/data/cleaned")
        if response.status_code == 200:
            df = pd.read_json(response.content)
            logger.info("Successfully loaded data from backend API")
        else:
            # Fallback to local files if API fails
            raise Exception(f"Could not load data from API: {response.status_code}")
    except Exception as e:
        logger.warning(f"Falling back to local data file: {str(e)}")
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
        else:
            alt_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/cleaned_weather.csv")
            if os.path.exists(alt_data_path):
                df = pd.read_csv(alt_data_path)
            else:
                logger.error("Could not find cleaned_weather.csv in any location")
                raise Exception("Could not find cleaned_weather.csv in any location")
    
    df = df[["tavg", "tmin", "tmax", "prcp", "wspd"]].copy()
    
    # Always try to get model from backend API first for most up-to-date model
    try:
        model = load_model_from_backend()
        st.success("✅ Using latest model from backend API")
    except Exception as e:
        logger.warning(f"Could not load model from API, falling back to local model: {str(e)}")
        # Fallback to local model
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
                st.warning("⚠️ Using local model (may not be the most recent)")
        else:
            alt_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend/model.pkl")
            if os.path.exists(alt_model_path):
                with open(alt_model_path, "rb") as f:
                    model = pickle.load(f)
                    st.warning("⚠️ Using local model (may not be the most recent)")
            else:
                logger.error("Could not load model from any source")
                raise Exception("Could not find model.pkl in any location")
    
    logger.info("Data and model loaded successfully")
except Exception as e:
    logger.error(f"Error loading data or model: {str(e)}", exc_info=True)
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
    logger.info("Predictions generated successfully")
except Exception as e:
    logger.error(f"Error generating predictions: {str(e)}", exc_info=True)
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
        # Always try to get the latest model for custom predictions
        try:
            latest_model = load_model_from_backend()
            st.sidebar.success("✅ Using latest model from backend API")
        except:
            latest_model = model
            st.sidebar.warning("⚠️ Using cached model for prediction")
            
        input_dict = {}

        # Add tavg lags
        for i in range(1, 4):
            input_dict[f"tavg_t-{i}"] = [custom_input[-i]]

        # Calculate reasonable values for other parameters based on the temperature
        # This ensures predictions change when temperature inputs change
        for i in range(1, 4):
            temp = custom_input[-i]
            # Generate sensible tmin/tmax based on the average temperature
            input_dict[f"tmin_t-{i}"] = [temp - 5.0]  # Min temp typically 5 degrees below avg
            input_dict[f"tmax_t-{i}"] = [temp + 5.0]  # Max temp typically 5 degrees above avg
            
            # Precipitation more likely with lower temps (simplified relationship)
            if temp < 20:
                input_dict[f"prcp_t-{i}"] = [5.0]  # Some precipitation for cooler temps
            else:
                input_dict[f"prcp_t-{i}"] = [0.0]  # Less precipitation for warmer temps
                
            # Wind speed - just a simple value for now
            input_dict[f"wspd_t-{i}"] = [10.0]

        # Fill any remaining missing features required by the model
        for col in latest_model.feature_names_in_:
            if col not in input_dict:
                input_dict[col] = [0.0]

        X_manual = pd.DataFrame(input_dict)
        X_manual = X_manual[latest_model.feature_names_in_]

        pred = latest_model.predict(X_manual)[0]
        desc = describe_weather(pred)

        st.subheader("📍 Prediction from Manual Input")
        st.markdown(f"<div class='emoji'>{desc}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>Predicted tavg: {pred:.2f} °C</div>", unsafe_allow_html=True)
        
        # Add debugging information if needed
        with st.expander("Debug Information"):
            st.write("Input features for prediction:")
            st.dataframe(X_manual)
            
        logger.info("Manual prediction generated successfully")
    except Exception as e:
        logger.error(f"Error generating manual prediction: {str(e)}", exc_info=True)
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
            logger.info("Data uploaded and retraining started successfully")
            
            # Add a slight delay to ensure the model is fully retrained
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()
            for i in range(101):
                progress_bar.progress(i)
                status_text.text(f"Retraining in progress: {i}%")
                time.sleep(0.1)
            
            # Fetch the newly trained model from the backend
            try:
                status_text.text("Fetching new model...")
                # Clear Streamlit's cache to ensure we get fresh data
                st.cache_data.clear()
                st.cache_resource.clear()
                
                # Force reload of data as well
                try:
                    response_data = requests.get(f"{BACKEND_URL}/data/cleaned")
                    if response_data.status_code == 200:
                        df = pd.read_json(response_data.content)
                        df = df[["tavg", "tmin", "tmax", "prcp", "wspd"]].copy()
                        logger.info("Reloaded fresh data from backend")
                except Exception as e:
                    logger.warning(f"Could not reload data: {e}")
                
                # Get the updated model
                model = load_model_from_backend()
                
                # Save the new model locally if we have write access
                try:
                    with open(MODEL_PATH, 'wb') as f:
                        pickle.dump(model, f)
                    logger.info("New model saved locally")
                except:
                    logger.warning("Could not save model locally, but still using it for predictions")
                
                status_text.text("Model updated successfully!")
                st.sidebar.success("✅ New model is now being used for predictions!")
                
                # Force complete page reload to use the new model for all predictions
                st.rerun()
                
            except Exception as e:
                logger.error(f"Error fetching retrained model: {str(e)}")
                st.sidebar.warning("Model was retrained but couldn't be loaded automatically. Please refresh the page.")
        else:
            logger.warning(f"Failed to upload data: {response.json().get('detail', 'Unknown error')}")
            st.sidebar.error(f"❌ Failed: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error contacting API: {str(e)}", exc_info=True)
        st.sidebar.error(f"❌ Error contacting API: {str(e)}")