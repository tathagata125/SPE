import streamlit as st
import pandas as pd
import pickle

st.set_page_config(page_title="Weather Predictor", layout="wide")

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

st.title("🌦️ 3-Day Weather Forecast - Bangalore")
st.write("Using past 14 days of weather data to predict upcoming average temperatures.")

# Load cleaned dataset
df = pd.read_csv("../data/cleaned_weather.csv")
df = df[["tavg", "tmin", "tmax", "prcp", "wspd"]].copy()

# Load trained model
with open("../model.pkl", "rb") as f:
    model = pickle.load(f)

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
predictions = []
future_df = df.copy()

for day in range(1, 4):
    for feature in ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']:
        for lag in range(1, 15):
            future_df[f"{feature}_t-{lag}"] = future_df[feature].shift(lag)
    future_df.dropna(inplace=True)
    X_latest = future_df.drop(columns=['tavg']).iloc[-1:]
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

# Layout: 3 columns for 3 days
cols = st.columns(3)
for i, col in enumerate(cols):
    with col:
        st.markdown(f"<div class='emoji'>{predictions[i]['desc']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>{predictions[i]['day']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-font'>{predictions[i]['temp']} °C</div>", unsafe_allow_html=True)

# --- Sidebar Manual Input ---
st.sidebar.markdown("## 🔧 Manual Forecast")
st.sidebar.write("Enter 14 days of average temperatures to predict tomorrow's.")

custom_input = []
for i in range(14, 0, -1):
    val = st.sidebar.number_input(f"Day -{i} tavg (°C)", min_value=-10.0, max_value=50.0, value=25.0, step=0.1, key=f"tavg_{i}")
    custom_input.append(val)

if st.sidebar.button("Predict from custom data"):
    input_dict = {}

    # Add tavg lags
    for i in range(1, 15):
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

