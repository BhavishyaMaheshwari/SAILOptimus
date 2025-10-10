import glob, os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import tkinter as tk
from tkinter import messagebox
import warnings

warnings.filterwarnings("ignore")


CSV_FOLDER = r"C:\DATA\Joseph Jisso\SIH\SL_Logistic Regression\Train_Route"  

files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))

print("Found CSV files:", len(files))

if len(files) == 0:

    raise SystemExit("No CSV files found in folder: " + CSV_FOLDER)


# load and concatenate

df_list = []

for f in files:

    tmp = pd.read_csv(f, engine='python', skip_blank_lines=True)

    train_no = os.path.splitext(os.path.basename(f))[0]

    tmp['TrainNo'] = str(train_no).strip().upper()

    df_list.append(tmp)

df = pd.concat(df_list, ignore_index=True)


df.columns = [c.strip() for c in df.columns]

df = df.rename(columns={
    "Average_Delay(min)": "avg_delay",
    "Right Time (0-15 min's)": "p_on_time",
    "Slight Delay (15-60 min's)": "p_slight",
    "Significant Delay (>1 Hour)": "p_significant",
    "Cancelled/Unknown": "p_cancelled",

}, errors='ignore')

for col in ['TrainNo', 'Station', 'Station_Name']:

    if col in df.columns:

        df[col] = df[col].astype(str).str.strip().str.upper()


feature_cols = ['p_on_time', 'p_slight', 'p_significant', 'p_cancelled']

X = df[feature_cols].fillna(0).astype(float)

y = df['avg_delay'].astype(float)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)

model.fit(X_train, y_train)

print("Model trained. Test R2:", model.score(X_test, y_test))



def predict_delay(train_no, station_code, station_name=None):

    train_no = str(train_no).strip().upper()

    station_code = str(station_code).strip().upper()

    if station_name:

        station_name = str(station_name).strip().upper()


    match = df[(df['TrainNo'] == train_no) & (df['Station'] == station_code)]

    if not match.empty:

        X_row = match[feature_cols].iloc[0].values.reshape(1, -1)

        pred = float(model.predict(X_row)[0])

        return f"{train_no} → {station_code}: {pred:.2f} mins"


    if station_name:

        match2 = df[(df['TrainNo'] == train_no) & (df['Station_Name'] == station_name)]

        if not match2.empty:

            X_row = match2[feature_cols].iloc[0].values.reshape(1, -1)

            pred = float(model.predict(X_row)[0])

            return f"{train_no} → ({station_code}, {station_name}): {pred:.2f} mins"


    train_rows = df[df['TrainNo'] == train_no]

    if not train_rows.empty:

        X_avg = train_rows[feature_cols].mean().values.reshape(1, -1)

        pred = float(model.predict(X_avg)[0])

        return f"{train_no} → avg across train: {pred:.2f} mins"


    station_rows = df[df['Station'] == station_code]

    if not station_rows.empty:

        X_avg = station_rows[feature_cols].mean().values.reshape(1, -1)

        pred = float(model.predict(X_avg)[0])

        return f"{station_code} → avg across station: {pred:.2f} mins"


    X_mean = X.mean().values.reshape(1, -1)

    pred = float(model.predict(X_mean)[0])

    return f"Global avg fallback: {pred:.2f} mins"



# GUI

def on_predict():

    train_no = entry_train.get()

    station_code = entry_station.get()

    station_name = entry_name.get()

    if not train_no or not station_code:

        messagebox.showwarning("Input Error", "Train Number and Station Code are required!")

        return

    result = predict_delay(train_no, station_code, station_name if station_name else None)

    messagebox.showinfo("Prediction Result", result)



root = tk.Tk()

root.title("Train Delay Predictor")


tk.Label(root, text="Train Number:").grid(row=0, column=0, padx=5, pady=5, sticky="e")

entry_train = tk.Entry(root, width=30)

entry_train.grid(row=0, column=1, padx=5, pady=5)


tk.Label(root, text="Station Code:").grid(row=1, column=0, padx=5, pady=5, sticky="e")

entry_station = tk.Entry(root, width=30)

entry_station.grid(row=1, column=1, padx=5, pady=5)


tk.Label(root, text="Station Name (optional):").grid(row=2, column=0, padx=5, pady=5, sticky="e")

entry_name = tk.Entry(root, width=30)

entry_name.grid(row=2, column=1, padx=5, pady=5)


btn_predict = tk.Button(root, text="Predict Delay", command=on_predict)

btn_predict.grid(row=3, column=0, columnspan=2, pady=10)


root.mainloop()