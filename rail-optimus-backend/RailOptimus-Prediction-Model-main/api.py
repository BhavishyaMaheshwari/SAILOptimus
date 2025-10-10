from flask import Flask, request, jsonify
from flask_cors import CORS

# Import your custom modules
# This assumes api.py is in the same directory as your other scripts
from supervised_model import predict_delay, get_train_station_row
from weather_api import get_weather
from rl_agent import SimpleRLAgent

# Initialize Flask app and the RL Agent
app = Flask(__name__)
CORS(app)  # This enables Cross-Origin Resource Sharing to allow your frontend to connect
agent = SimpleRLAgent()

# ------------------------
# Helper functions to parse frontend inputs
# ------------------------
def parse_inputs(train_field: str):
    """Parses the 'trains' string (e.g., "12951:NDLS,12952") into a list of tuples."""
    train_field = train_field.strip()
    pairs = []
    if not train_field:
        return pairs

    tokens = [t.strip() for t in train_field.split(",") if t.strip()]
    for tok in tokens:
        if ":" in tok:
            tr, st = tok.split(":", 1)
            pairs.append((tr.strip(), st.strip().upper()))
        else:
            pairs.append((tok.strip(), "")) # Handle cases with no station code
    return pairs

def parse_cities(city_field: str, num_trains: int):
    """Parses the 'cities' string, ensuring there's a city for each train."""
    city_field = city_field.strip()
    if not city_field:
        return ["Delhi"] * num_trains # Default city
    city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
    if len(city_tokens) < num_trains:
        # If not enough cities are provided, repeat the last one
        city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
    return city_tokens[:num_trains]

def parse_speeds(speed_field: str, num_trains: int):
    """Parses the 'speeds' string, ensuring there's a speed for each train."""
    speed_field = speed_field.strip()
    if not speed_field:
        return [80.0] * num_trains # Default speed
    tokens = []
    for s in speed_field.split(","):
        try:
            tokens.append(float(s.strip()))
        except ValueError:
            tokens.append(80.0) # Default if a value is invalid
    if len(tokens) < num_trains:
        # If not enough speeds are provided, repeat the last one
        tokens += [tokens[-1]] * (num_trains - len(tokens))
    return tokens[:num_trains]

# ------------------------
# The Main API Endpoint
# ------------------------
@app.route("/api/predict", methods=["POST"])
def handle_prediction():
    """
    This function is called when the frontend sends a POST request.
    It processes the input and returns the prediction results.
    """
    try:
        data = request.json
        trains_raw = data.get("trains", "")
        cities_raw = data.get("cities", "")
        speeds_raw = data.get("speeds", "")

        train_station_pairs = parse_inputs(trains_raw)
        if not train_station_pairs:
            return jsonify({"status": "error", "message": "Please enter at least one train."}), 400

        num_trains = len(train_station_pairs)
        cities = parse_cities(cities_raw, num_trains)
        speeds = parse_speeds(speeds_raw, num_trains)

        results = []
        for i, (train_no, station_code) in enumerate(train_station_pairs):
            city = cities[i]
            speed = speeds[i]
            
            try:
                weather_desc, visibility_km, ok = get_weather(city)
                predicted_delay = predict_delay(train_no, station_code, "") # Station name isn't used in this flow
                action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

                row = get_train_station_row(train_no, station_code)
                prob_info = ""
                if row:
                    info_parts = [f"{key.split('_')[-1].title()}: {row.get(key):.0%}" for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"] if key in row]
                    prob_info = ", ".join(info_parts)

                results.append({
                    "train": f"{train_no}:{station_code}" if station_code else train_no,
                    "city": city,
                    "weather": f"{weather_desc}{' (fallback)' if not ok else ''}",
                    "visibility": f"{visibility_km:.2f} km",
                    "predictedDelay": f"{predicted_delay:.2f} mins",
                    "probabilities": prob_info or "N/A",
                    "currentSpeed": f"{speed:.1f} km/h",
                    "action": action
                })
            except Exception as e:
                # Handle errors for individual trains
                results.append({"train": f"{train_no}:{station_code}", "error": str(e)})

        return jsonify({"status": "success", "predictions": results})

    except Exception as e:
        # Handle unexpected server errors
        print(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

if __name__ == "__main__":
    # To run the server, you will execute `python api.py` in your terminal
    app.run(debug=True, port=5000)

