# supervised_model.py
import glob, os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import warnings

warnings.filterwarnings("ignore")

warnings.filterwarnings("ignore")

# --- START: PATH DEFINITION ---
# This section dynamically finds the correct paths for your data and model files.
# It makes your script runnable from anywhere without breaking.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# This is the line you asked for: it points to your 'train_route' folder.
CSV_FOLDER = os.path.join(BASE_DIR, 'train_route')

# Define a folder for saving the trained model.
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True) # Create the 'models' folder if it doesn't exist

MODEL_FILE = os.path.join(MODELS_DIR, "delay_model.pkl")
DATA_FILE = os.path.join(BASE_DIR, "train_dataset.csv") # Save the combined dataset in the main directory
# --- END: PATH DEFINITION ---


def _load_dataset():
    files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))
    if len(files) == 0:
        raise SystemExit("❌ No CSV files found in folder: " + CSV_FOLDER)

    df_list = []
    for f in files:
        tmp = pd.read_csv(f, engine="python", skip_blank_lines=True)
        train_no = os.path.splitext(os.path.basename(f))[0]
        tmp["TrainNo"] = str(train_no).strip().upper()
        df_list.append(tmp)

    df = pd.concat(df_list, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]

    # Standardize columns
    df = df.rename(
        columns={
            "Average_Delay(min)": "avg_delay",
            "Right Time (0-15 min's)": "p_on_time",
            "Slight Delay (15-60 min's)": "p_slight",
            "Significant Delay (>1 Hour)": "p_significant",
            "Cancelled/Unknown": "p_cancelled",
        },
        errors="ignore",
    )

    for col in ["TrainNo", "Station", "Station_Name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    return df

# Load dataset (always load so we can query rows)
if os.path.isfile(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    # ensure uppercase keys present
    for col in ["TrainNo", "Station", "Station_Name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
else:
    df = _load_dataset()
    df.to_csv(DATA_FILE, index=False)

# Feature columns used for the model
feature_cols = ["p_on_time", "p_slight", "p_significant", "p_cancelled"]

# Try load model; if missing, train from CSV and save
if os.path.isfile(MODEL_FILE):
    model = joblib.load(MODEL_FILE)
else:
    print("[supervised_model] No saved model found — training now (this may take a moment)...")
    X = df[feature_cols].fillna(0).astype(float)
    y = df["avg_delay"].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, MODEL_FILE)
    print("[supervised_model] Model trained and saved to", MODEL_FILE)
    print("Test R2:", model.score(X_test, y_test))

def predict_delay(train_no: str, station_code: str, station_name: str = None) -> float:
    """
    Returns predicted average delay in minutes (float).
    - train_no: train number string
    - station_code: station code string
    - station_name: optional station name
    """
    train_no = str(train_no).strip().upper()
    station_code = str(station_code).strip().upper() if station_code else ""

    # try exact train+station match
    match = df[(df["TrainNo"] == train_no) & (df["Station"] == station_code)]
    if not match.empty:
        X_row = match[feature_cols].iloc[0].fillna(0).values.reshape(1, -1)
        return float(model.predict(X_row)[0])

    # try station name match if provided
    if station_name:
        station_name = str(station_name).strip().upper()
        match2 = df[(df["TrainNo"] == train_no) & (df["Station_Name"] == station_name)]
        if not match2.empty:
            X_row = match2[feature_cols].iloc[0].fillna(0).values.reshape(1, -1)
            return float(model.predict(X_row)[0])

    # try average across the train
    train_rows = df[df["TrainNo"] == train_no]
    if not train_rows.empty:
        X_avg = train_rows[feature_cols].fillna(0).mean().values.reshape(1, -1)
        return float(model.predict(X_avg)[0])

    # try average across the station
    if station_code:
        station_rows = df[df["Station"] == station_code]
        if not station_rows.empty:
            X_avg = station_rows[feature_cols].fillna(0).mean().values.reshape(1, -1)
            return float(model.predict(X_avg)[0])

    # global fallback: mean features
    X_mean = df[feature_cols].fillna(0).mean().values.reshape(1, -1)
    return float(model.predict(X_mean)[0])

def get_train_station_row(train_no: str, station_code: str):
    """Return the raw dataset row for train+station if available, else None."""
    train_no = str(train_no).strip().upper()
    station_code = str(station_code).strip().upper() if station_code else ""
    match = df[(df["TrainNo"] == train_no) & (df["Station"] == station_code)]
    if not match.empty:
        return match.iloc[0].to_dict()
    return None

if __name__ == "__main__":
    # quick test
    print("Test predict:", predict_delay("12951", "NDLS"))
