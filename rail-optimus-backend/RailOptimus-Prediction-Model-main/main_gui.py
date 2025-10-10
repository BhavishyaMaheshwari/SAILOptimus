
import tkinter as tk
from tkinter import messagebox, scrolledtext
from supervised_model import predict_delay, get_train_station_row
from weather_api import get_weather
from rl_agent import SimpleRLAgent

agent = SimpleRLAgent()

# ------------------------
# Helpers
# ------------------------
def parse_inputs(train_field: str, station_field: str):
    train_field = train_field.strip()
    station_field = station_field.strip().upper()
    pairs = []

    if not train_field:
        return pairs

    tokens = [t.strip() for t in train_field.split(",") if t.strip()]
    for tok in tokens:
        if ":" in tok:
            tr, st = tok.split(":", 1)
            pairs.append((tr.strip(), st.strip().upper()))
        else:
            pairs.append((tok.strip(), station_field if station_field else ""))
    return pairs

def parse_cities(city_field: str, num_trains: int):
    city_field = city_field.strip()
    if not city_field:
        return ["Delhi"] * num_trains

    city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
    if len(city_tokens) < num_trains:
        city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
    return city_tokens[:num_trains]

def parse_speeds(speed_field: str, num_trains: int):
    speed_field = speed_field.strip()
    if not speed_field:
        return [80.0] * num_trains

    tokens = []
    for s in speed_field.split(","):
        try:
            tokens.append(float(s.strip()))
        except:
            tokens.append(80.0)
    if len(tokens) < num_trains:
        tokens += [tokens[-1]] * (num_trains - len(tokens))
    return tokens[:num_trains]

# ------------------------
# Predict button
# ------------------------
def on_predict():
    trains_raw = entry_train.get()
    station_raw = entry_station.get()
    station_name = entry_name.get()

    pairs = parse_inputs(trains_raw, station_raw)
    if not pairs:
        messagebox.showwarning("Input Error", "Enter at least one train (format: 12951 or 12951:NDLS).")
        return

    cities = parse_cities(entry_city.get(), len(pairs))
    speeds = parse_speeds(entry_speed.get(), len(pairs))

    # Clear output
    txt_output.delete(1.0, tk.END)

    for i, (train_no, station_code) in enumerate(pairs):
        city = cities[i]
        speed = speeds[i]

        # Validate speed
        if speed < 0:
            txt_output.insert(tk.END, f"⚠️ Invalid speed for {train_no}, using default 80 km/h\n")
            speed = 80.0

        weather_desc, visibility_km, ok = get_weather(city)
        header = f"Train: {train_no}    City: {city}    Weather: {weather_desc}    Visibility: {visibility_km:.2f} km"
        if not ok:
            header += "   (weather fallback)"
        txt_output.insert(tk.END, header + "\n")

        # try:
        #     if not station_code:
        #         predicted_delay = predict_delay(train_no, "", station_name if station_name else None)
        #     else:
        #         predicted_delay = predict_delay(train_no, station_code, station_name if station_name else None)
        try:
            if not station_code:
                    # Pass station_name directly. It will be "" if the box is empty.
                predicted_delay = predict_delay(train_no, "", station_name)
            else:
        # Pass station_name directly here as well.
                predicted_delay = predict_delay(train_no, station_code, station_name)

            row = get_train_station_row(train_no, station_code) if station_code else None

            action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

            txt_output.insert(tk.END, f"  Predicted Delay: {predicted_delay:.2f} mins\n")
            if row:
                info = []
                for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"]:
                    if key in row:
                        info.append(f"{key}={row.get(key)}")
                if info:
                    txt_output.insert(tk.END, "  Probabilities: " + ", ".join(info) + "\n")
            txt_output.insert(tk.END, f"  Current Speed: {speed:.1f} km/h\n")
            txt_output.insert(tk.END, f"  Action (RL): {action}\n")
            txt_output.insert(tk.END, "-"*70 + "\n")
        except Exception as e:
            txt_output.insert(tk.END, f"⚠️ Error for {train_no}:{station_code} -> {e}\n")
            txt_output.insert(tk.END, "-"*70 + "\n")

# ------------------------
# GUI layout
# ------------------------
root = tk.Tk()
root.title("Train Delay Predictor + Decision System")

tk.Label(root, text="Train(s) [comma separated, e.g., 12951:NDLS,12952:MB]:").grid(row=0, column=0, sticky="e", padx=5, pady=4)
entry_train = tk.Entry(root, width=60)
entry_train.grid(row=0, column=1, padx=5, pady=4)
entry_train.insert(0, "12951:NDLS,12952:MB")

tk.Label(root, text="Station Code (optional):").grid(row=1, column=0, sticky="e", padx=5, pady=4)
entry_station = tk.Entry(root, width=25)
entry_station.grid(row=1, column=1, sticky="w", padx=5, pady=4)

tk.Label(root, text="Station Name (optional):").grid(row=2, column=0, sticky="e", padx=5, pady=4)
entry_name = tk.Entry(root, width=50)
entry_name.grid(row=2, column=1, padx=5, pady=4)

tk.Label(root, text="City(s) for weather [comma separated, optional]:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
entry_city = tk.Entry(root, width=50)
entry_city.grid(row=3, column=1, padx=5, pady=4)
entry_city.insert(0, "Delhi,Mumbai")

tk.Label(root, text="Speed(s) [km/h, comma separated, optional]:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
entry_speed = tk.Entry(root, width=25)
entry_speed.grid(row=4, column=1, sticky="w", padx=5, pady=4)
entry_speed.insert(0, "80,60")

btn_predict = tk.Button(root, text="Predict & Decide", command=on_predict)
btn_predict.grid(row=5, column=0, columnspan=2, pady=8)

txt_output = scrolledtext.ScrolledText(root, width=85, height=22)
txt_output.grid(row=6, column=0, columnspan=2, padx=8, pady=8)

root.mainloop()
