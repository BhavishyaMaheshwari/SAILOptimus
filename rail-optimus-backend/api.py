# from flask import Flask, request, jsonify
# from flask_cors import CORS

# # Import your custom modules
# # This assumes api.py is in the same directory as your other scripts
# from supervised_model import predict_delay, get_train_station_row
# from weather_api import get_weather
# from rl_agent import SimpleRLAgent

# # Initialize Flask app and the RL Agent
# app = Flask(__name__)
# CORS(app)  # This enables Cross-Origin Resource Sharing to allow your frontend to connect
# agent = SimpleRLAgent()

# # ------------------------
# # Helper functions to parse frontend inputs
# # ------------------------
# def parse_inputs(train_field: str):
#     """Parses the 'trains' string (e.g., "12951:NDLS,12952") into a list of tuples."""
#     train_field = train_field.strip()
#     pairs = []
#     if not train_field:
#         return pairs

#     tokens = [t.strip() for t in train_field.split(",") if t.strip()]
#     for tok in tokens:
#         if ":" in tok:
#             tr, st = tok.split(":", 1)
#             pairs.append((tr.strip(), st.strip().upper()))
#         else:
#             pairs.append((tok.strip(), "")) # Handle cases with no station code
#     return pairs

# def parse_cities(city_field: str, num_trains: int):
#     """Parses the 'cities' string, ensuring there's a city for each train."""
#     city_field = city_field.strip()
#     if not city_field:
#         return ["Delhi"] * num_trains # Default city
#     city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
#     if len(city_tokens) < num_trains:
#         # If not enough cities are provided, repeat the last one
#         city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
#     return city_tokens[:num_trains]

# def parse_speeds(speed_field: str, num_trains: int):
#     """Parses the 'speeds' string, ensuring there's a speed for each train."""
#     speed_field = speed_field.strip()
#     if not speed_field:
#         return [80.0] * num_trains # Default speed
#     tokens = []
#     for s in speed_field.split(","):
#         try:
#             tokens.append(float(s.strip()))
#         except ValueError:
#             tokens.append(80.0) # Default if a value is invalid
#     if len(tokens) < num_trains:
#         # If not enough speeds are provided, repeat the last one
#         tokens += [tokens[-1]] * (num_trains - len(tokens))
#     return tokens[:num_trains]

# # ------------------------
# # The Main API Endpoint
# # ------------------------
# @app.route("/api/predict", methods=["POST"])
# def handle_prediction():
#     """
#     This function is called when the frontend sends a POST request.
#     It processes the input and returns the prediction results.
#     """
#     try:
#         data = request.json
#         # --- FIX: ADDED THIS SAFETY CHECK ---
#         # This prevents the "'NoneType' object has no attribute 'get'" error
#         # by ensuring the request body is not empty.
#         if not data:
#             return jsonify({"status": "error", "message": "Request body must be JSON."}), 400
#         trains_raw = data.get("trains", "")
#         cities_raw = data.get("cities", "")
#         speeds_raw = data.get("speeds", "")

#         train_station_pairs = parse_inputs(trains_raw)
#         if not train_station_pairs:
#             return jsonify({"status": "error", "message": "Please enter at least one train."}), 400

#         num_trains = len(train_station_pairs)
#         cities = parse_cities(cities_raw, num_trains)
#         speeds = parse_speeds(speeds_raw, num_trains)

#         results = []
#         for i, (train_no, station_code) in enumerate(train_station_pairs):
#             city = cities[i]
#             speed = speeds[i]
            
#             try:
#                 weather_desc, visibility_km, ok = get_weather(city)
#                 predicted_delay = predict_delay(train_no, station_code, "") # Station name isn't used in this flow
#                 action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

#                 row = get_train_station_row(train_no, station_code)
#                 prob_info = ""
#                 if row:
#                     info_parts = [f"{key.split('_')[-1].title()}: {row.get(key):.0%}" for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"] if key in row]
#                     prob_info = ", ".join(info_parts)

#                 results.append({
#                     "train": f"{train_no}:{station_code}" if station_code else train_no,
#                     "city": city,
#                     "weather": f"{weather_desc}{' (fallback)' if not ok else ''}",
#                     "visibility": f"{visibility_km:.2f} km",
#                     "predictedDelay": f"{predicted_delay:.2f} mins",
#                     "probabilities": prob_info or "N/A",
#                     "currentSpeed": f"{speed:.1f} km/h",
#                     "action": action
#                 })
#             except Exception as e:
#                 # Handle errors for individual trains
#                 results.append({"train": f"{train_no}:{station_code}", "error": str(e)})

#         return jsonify({"status": "success", "predictions": results})

#     except Exception as e:
#         # Handle unexpected server errors
#         print(f"An unexpected error occurred: {e}")
#         return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

# if __name__ == "__main__":
#     # To run the server, you will execute `python api.py` in your terminal
#     app.run(debug=True, port=5000)

# print("--- [1] Starting api.py execution ---")

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# print("--- [2] Imported Flask and CORS successfully ---")

# # Import your custom modules with error handling to see which one fails
# try:
#     from supervised_model import predict_delay, get_train_station_row
#     print("--- [3] Imported 'supervised_model' successfully ---")
# except Exception as e:
#     print(f"\n\n!!! FATAL ERROR: Could not import 'supervised_model'. Please check that file. Error: {e}\n\n")

# try:
#     from weather_api import get_weather
#     print("--- [4] Imported 'weather_api' successfully ---")
# except Exception as e:
#     print(f"\n\n!!! FATAL ERROR: Could not import 'weather_api'. Please check that file. Error: {e}\n\n")

# try:
#     from rl_agent import SimpleRLAgent
#     print("--- [5] Imported 'rl_agent' successfully ---")
# except Exception as e:
#     print(f"\n\n!!! FATAL ERROR: Could not import 'rl_agent'. Please check that file. Error: {e}\n\n")


# # Initialize Flask app and the RL Agent
# app = Flask(__name__)
# print("--- [6] Flask app initialized ---")
# CORS(app)
# agent = SimpleRLAgent()
# print("--- [7] CORS enabled and RL Agent initialized ---")

# # ------------------------
# # Helper functions (unchanged)
# # ------------------------
# def parse_inputs(train_field: str):
#     """Parses the 'trains' string (e.g., "12951:NDLS,12952") into a list of tuples."""
#     train_field = train_field.strip()
#     pairs = []
#     if not train_field:
#         return pairs

#     tokens = [t.strip() for t in train_field.split(",") if t.strip()]
#     for tok in tokens:
#         if ":" in tok:
#             tr, st = tok.split(":", 1)
#             pairs.append((tr.strip(), st.strip().upper()))
#         else:
#             pairs.append((tok.strip(), ""))
#     return pairs

# def parse_cities(city_field: str, num_trains: int):
#     """Parses the 'cities' string, ensuring there's a city for each train."""
#     city_field = city_field.strip()
#     if not city_field:
#         return ["Delhi"] * num_trains
#     city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
#     if len(city_tokens) < num_trains:
#         city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
#     return city_tokens[:num_trains]

# def parse_speeds(speed_field: str, num_trains: int):
#     """Parses the 'speeds' string, ensuring there's a speed for each train."""
#     speed_field = speed_field.strip()
#     if not speed_field:
#         return [80.0] * num_trains
#     tokens = []
#     for s in speed_field.split(","):
#         try:
#             tokens.append(float(s.strip()))
#         except ValueError:
#             tokens.append(80.0)
#     if len(tokens) < num_trains:
#         tokens += [tokens[-1]] * (num_trains - len(tokens))
#     return tokens[:num_trains]


# # ------------------------
# # The Main API Endpoint
# # ------------------------
# @app.route("/api/predict", methods=["POST"])
# def handle_prediction():
#     """Processes input from the frontend and returns prediction results."""
#     print("\n--- [8] Request received inside handle_prediction() ---")
#     try:
#         data = request.json
#         if not data:
#             print("--- [!] Request had no JSON data. Returning 400. ---")
#             return jsonify({"status": "error", "message": "Request body must be JSON."}), 400

#         print("--- [9] Parsing input data... ---")
#         trains_raw = data.get("trains", "")
#         cities_raw = data.get("cities", "")
#         speeds_raw = data.get("speeds", "")

#         train_station_pairs = parse_inputs(trains_raw)
#         if not train_station_pairs:
#             print("--- [!] No trains found in input. Returning 400. ---")
#             return jsonify({"status": "error", "message": "Please enter at least one train."}), 400

#         num_trains = len(train_station_pairs)
#         cities = parse_cities(cities_raw, num_trains)
#         speeds = parse_speeds(speeds_raw, num_trains)

#         results = []
#         print(f"--- [10] Processing {num_trains} train(s)... ---")
#         for i, (train_no, station_code) in enumerate(train_station_pairs):
#             # ... (rest of the logic is unchanged) ...
#             city = cities[i]
#             speed = speeds[i]
#             try:
#                 weather_desc, visibility_km, ok = get_weather(city)
#                 predicted_delay = predict_delay(train_no, station_code, "")
#                 action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

#                 row = get_train_station_row(train_no, station_code)
#                 prob_info = ""
#                 if row:
#                     info_parts = [f"{key.split('_')[-1].title()}: {row.get(key):.0%}" for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"] if key in row]
#                     prob_info = ", ".join(info_parts)
#                 results.append({ "train": f"{train_no}:{station_code}" if station_code else train_no, "city": city, "weather": f"{weather_desc}{' (fallback)' if not ok else ''}", "visibility": f"{visibility_km:.2f} km", "predictedDelay": f"{predicted_delay:.2f} mins", "probabilities": prob_info or "N/A", "currentSpeed": f"{speed:.1f} km/h", "action": action })
#             except Exception as e:
#                 results.append({"train": f"{train_no}:{station_code}", "error": str(e)})
        
#         print("--- [11] Successfully processed all trains. Sending response. ---")
#         return jsonify({"status": "success", "predictions": results})

#     except Exception as e:
#         print(f"\n\n!!! FATAL CRASH inside handle_prediction: {e}\n\n")
#         return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

# if __name__ == "__main__":
#     print("--- [!] Starting Flask Development Server ---")
#     app.run(debug=True, port=5000)


#&new
# print("--- [1] Starting api.py execution ---")

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# print("--- [2] Imported Flask and CORS successfully ---")

# # We will import the slow modules later, inside the request handler.

# # Initialize Flask app
# app = Flask(__name__)
# print("--- [6] Flask app initialized ---")
# CORS(app)
# print("--- [7] CORS enabled ---")

# # ------------------------
# # Helper functions (unchanged)
# # ------------------------
# def parse_inputs(train_field: str):
#     """Parses the 'trains' string (e.g., "12951:NDLS,12952") into a list of tuples."""
#     train_field = train_field.strip()
#     pairs = []
#     if not train_field:
#         return pairs

#     tokens = [t.strip() for t in train_field.split(",") if t.strip()]
#     for tok in tokens:
#         if ":" in tok:
#             tr, st = tok.split(":", 1)
#             pairs.append((tr.strip(), st.strip().upper()))
#         else:
#             pairs.append((tok.strip(), ""))
#     return pairs

# def parse_cities(city_field: str, num_trains: int):
#     """Parses the 'cities' string, ensuring there's a city for each train."""
#     city_field = city_field.strip()
#     if not city_field:
#         return ["Delhi"] * num_trains
#     city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
#     if len(city_tokens) < num_trains:
#         city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
#     return city_tokens[:num_trains]

# def parse_speeds(speed_field: str, num_trains: int):
#     """Parses the 'speeds' string, ensuring there's a speed for each train."""
#     speed_field = speed_field.strip()
#     if not speed_field:
#         return [80.0] * num_trains
#     tokens = []
#     for s in speed_field.split(","):
#         try:
#             tokens.append(float(s.strip()))
#         except ValueError:
#             tokens.append(80.0)
#     if len(tokens) < num_trains:
#         tokens += [tokens[-1]] * (num_trains - len(tokens))
#     return tokens[:num_trains]


# # ------------------------
# # The Main API Endpoint
# # ------------------------
# @app.route("/api/predict", methods=["POST"])
# def handle_prediction():
#     """Processes input from the frontend and returns prediction results."""
#     print("\n--- [8] Request received. Importing models now (this might be slow on first request)... ---")
    
#     # --- FIX: Moved slow imports inside the function to allow the server to start instantly ---
#     from supervised_model import predict_delay, get_train_station_row
#     from weather_api import get_weather
#     from rl_agent import SimpleRLAgent
#     agent = SimpleRLAgent()
#     print("--- [+] Models imported successfully for this request. ---")

#     try:
#         data = request.json
#         if not data:
#             print("--- [!] Request had no JSON data. Returning 400. ---")
#             return jsonify({"status": "error", "message": "Request body must be JSON."}), 400

#         print("--- [9] Parsing input data... ---")
#         trains_raw = data.get("trains", "")
#         cities_raw = data.get("cities", "")
#         speeds_raw = data.get("speeds", "")

#         train_station_pairs = parse_inputs(trains_raw)
#         if not train_station_pairs:
#             print("--- [!] No trains found in input. Returning 400. ---")
#             return jsonify({"status": "error", "message": "Please enter at least one train."}), 400

#         num_trains = len(train_station_pairs)
#         cities = parse_cities(cities_raw, num_trains)
#         speeds = parse_speeds(speeds_raw, num_trains)

#         results = []
#         print(f"--- [10] Processing {num_trains} train(s)... ---")
#         for i, (train_no, station_code) in enumerate(train_station_pairs):
#             # ... (rest of the logic is unchanged) ...
#             city = cities[i]
#             speed = speeds[i]
#             try:
#                 weather_desc, visibility_km, ok = get_weather(city)
#                 predicted_delay = predict_delay(train_no, station_code, "")
#                 action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

#                 row = get_train_station_row(train_no, station_code)
#                 prob_info = ""
#                 if row:
#                     info_parts = [f"{key.split('_')[-1].title()}: {row.get(key):.0%}" for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"] if key in row]
#                     prob_info = ", ".join(info_parts)
#                 results.append({ "train": f"{train_no}:{station_code}" if station_code else train_no, "city": city, "weather": f"{weather_desc}{' (fallback)' if not ok else ''}", "visibility": f"{visibility_km:.2f} km", "predictedDelay": f"{predicted_delay:.2f} mins", "probabilities": prob_info or "N/A", "currentSpeed": f"{speed:.1f} km/h", "action": action })
#             except Exception as e:
#                 results.append({"train": f"{train_no}:{station_code}", "error": str(e)})
        
#         print("--- [11] Successfully processed all trains. Sending response. ---")
#         return jsonify({"status": "success", "predictions": results})

#     except Exception as e:
#         print(f"\n\n!!! FATAL CRASH inside handle_prediction: {e}\n\n")
#         return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

# if __name__ == "__main__":
#     print("--- [!] Starting Flask Development Server ---")
#     # --- FIX: Added use_reloader=False to prevent the infinite restart loop ---
#     app.run(debug=True, port=5000, use_reloader=False)


# print("--- [1] Starting api.py execution ---")

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import traceback # Import traceback for detailed error logging

# print("--- [2] Imported Flask and CORS successfully ---")

# # We will import the slow modules later, inside the request handler.

# # Initialize Flask app
# app = Flask(__name__)
# print("--- [6] Flask app initialized ---")
# CORS(app)
# print("--- [7] CORS enabled ---")


# # ------------------------
# # NEW: Server Status Check Endpoint
# # ------------------------
# @app.route("/status", methods=["GET"])
# def get_status():
#     """A simple endpoint to confirm the server is running."""
#     print("--- [+] Status check successful. Server is running. ---")
#     return jsonify({"status": "ok", "message": "Server is running correctly."})


# # ------------------------
# # Helper functions (unchanged)
# # ------------------------
# def parse_inputs(train_field: str):
#     """Parses the 'trains' string (e.g., "12951:NDLS,12952") into a list of tuples."""
#     train_field = train_field.strip()
#     pairs = []
#     if not train_field:
#         return pairs

#     tokens = [t.strip() for t in train_field.split(",") if t.strip()]
#     for tok in tokens:
#         if ":" in tok:
#             tr, st = tok.split(":", 1)
#             pairs.append((tr.strip(), st.strip().upper()))
#         else:
#             pairs.append((tok.strip(), ""))
#     return pairs

# def parse_cities(city_field: str, num_trains: int):
#     """Parses the 'cities' string, ensuring there's a city for each train."""
#     city_field = city_field.strip()
#     if not city_field:
#         return ["Delhi"] * num_trains
#     city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
#     if len(city_tokens) < num_trains:
#         city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
#     return city_tokens[:num_trains]

# def parse_speeds(speed_field: str, num_trains: int):
#     """Parses the 'speeds' string, ensuring there's a speed for each train."""
#     speed_field = speed_field.strip()
#     if not speed_field:
#         return [80.0] * num_trains
#     tokens = []
#     for s in speed_field.split(","):
#         try:
#             tokens.append(float(s.strip()))
#         except ValueError:
#             tokens.append(80.0)
#     if len(tokens) < num_trains:
#         tokens += [tokens[-1]] * (num_trains - len(tokens))
#     return tokens[:num_trains]


# # ------------------------
# # The Main API Endpoint
# # ------------------------
# @app.route("/api/predict", methods=["POST"])
# def handle_prediction():
#     """Processes input from the frontend and returns prediction results."""
#     print("\n--- [8] Request received on /api/predict. Importing models... ---")
    
#     from supervised_model import predict_delay, get_train_station_row
#     from weather_api import get_weather
#     from rl_agent import SimpleRLAgent
#     agent = SimpleRLAgent()
#     print("--- [+] Models imported successfully for this request. ---")

#     try:
#         data = request.json
#         if not data:
#             print("--- [!] Request had no JSON data. Returning 400. ---")
#             return jsonify({"status": "error", "message": "Request body must be JSON."}), 400

#         print("--- [9] Parsing input data... ---")
#         trains_raw = data.get("trains", "")
#         cities_raw = data.get("cities", "")
#         speeds_raw = data.get("speeds", "")

#         train_station_pairs = parse_inputs(trains_raw)
#         if not train_station_pairs:
#             return jsonify({"status": "error", "message": "Please enter at least one train."}), 400

#         num_trains = len(train_station_pairs)
#         cities = parse_cities(cities_raw, num_trains)
#         speeds = parse_speeds(speeds_raw, num_trains)

#         results = []
#         print(f"--- [10] Processing {num_trains} train(s)... ---")
#         for i, (train_no, station_code) in enumerate(train_station_pairs):
#             city, speed = cities[i], speeds[i]
#             try:
#                 weather_desc, visibility_km, ok = get_weather(city)
#                 predicted_delay = predict_delay(train_no, station_code, "")
#                 action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

#                 row = get_train_station_row(train_no, station_code)
#                 prob_info = ""
#                 if row:
#                     info_parts = [f"{key.split('_')[-1].title()}: {row.get(key):.0%}" for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"] if key in row]
#                     prob_info = ", ".join(info_parts)
#                 results.append({ "train": f"{train_no}:{station_code}" if station_code else train_no, "city": city, "weather": f"{weather_desc}{' (fallback)' if not ok else ''}", "visibility": f"{visibility_km:.2f} km", "predictedDelay": f"{predicted_delay:.2f} mins", "probabilities": prob_info or "N/A", "currentSpeed": f"{speed:.1f} km/h", "action": action })
#             except Exception as e:
#                 print(f"--- [!] Error processing train {train_no}: {e}")
#                 results.append({"train": f"{train_no}:{station_code}", "error": str(e)})
        
#         print("--- [11] Successfully processed all trains. Sending response. ---")
#         return jsonify({"status": "success", "predictions": results})

#     except Exception as e:
#         print("\n\n!!! FATAL CRASH inside handle_prediction !!!")
#         traceback.print_exc() # Print the full error traceback
#         return jsonify({"status": "error", "message": "An internal server error occurred. Check backend logs."}), 500

# if __name__ == "__main__":
#     print("--- [!] Starting Flask Development Server ---")
#     app.run(debug=True, port=5000, use_reloader=False)

print("--- [1] Starting api.py execution ---")

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback # Import traceback for detailed error logging

print("--- [2] Imported Flask and CORS successfully ---")

# We will import the slow modules later, inside the request handler.

# Initialize Flask app
app = Flask(__name__)
print("--- [6] Flask app initialized ---")
CORS(app)
print("--- [7] CORS enabled ---")


# ------------------------
# NEW: Server Status Check Endpoint
# ------------------------
print("--- [1] Starting api.py execution ---")

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback # Import traceback for detailed error logging

print("--- [2] Imported Flask and CORS successfully ---")

# We will import the slow modules later, inside the request handler.

# Initialize Flask app
app = Flask(__name__)
print("--- [6] Flask app initialized ---")
CORS(app)
CORS(app, origins=["http://localhost:8080"])

print("--- [7] CORS enabled ---")


# ------------------------
# NEW: Server Status Check Endpoint
# ------------------------
@app.route("/status", methods=["GET"])
def get_status():
    """A simple endpoint to confirm the server is running."""
    print("--- [+] Status check successful. Server is running. ---")
    return jsonify({"status": "ok", "message": "Server is running correctly."})

# ------------------------
# NEW: Root Endpoint for Diagnostics
# ------------------------
@app.route("/", methods=["GET"])
def index():
    """A root endpoint to provide a clear landing page for the API."""
    print("--- [+] Root endpoint '/' was accessed. ---")
    return "<h1>API is running</h1><p>The prediction server is active. Use the /status or /api/predict endpoints.</p>"


# ------------------------
# Helper functions (unchanged)
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
            pairs.append((tok.strip(), ""))
    return pairs

def parse_cities(city_field: str, num_trains: int):
    """Parses the 'cities' string, ensuring there's a city for each train."""
    city_field = city_field.strip()
    if not city_field:
        return ["Delhi"] * num_trains
    city_tokens = [c.strip() for c in city_field.split(",") if c.strip()]
    if len(city_tokens) < num_trains:
        city_tokens += [city_tokens[-1]] * (num_trains - len(city_tokens))
    return city_tokens[:num_trains]

def parse_speeds(speed_field: str, num_trains: int):
    """Parses the 'speeds' string, ensuring there's a speed for each train."""
    speed_field = speed_field.strip()
    if not speed_field:
        return [80.0] * num_trains
    tokens = []
    for s in speed_field.split(","):
        try:
            tokens.append(float(s.strip()))
        except ValueError:
            tokens.append(80.0)
    if len(tokens) < num_trains:
        tokens += [tokens[-1]] * (num_trains - len(tokens))
    return tokens[:num_trains]


# ------------------------
# The Main API Endpoint
# ------------------------
@app.route("/api/predict", methods=["POST"])
def handle_prediction():
    """Processes input from the frontend and returns prediction results."""
    print("\n--- [8] Request received on /api/predict. Importing models... ---")
    
    from supervised_model import predict_delay, get_train_station_row
    from weather_api import get_weather
    from rl_agent import SimpleRLAgent
    agent = SimpleRLAgent()
    print("--- [+] Models imported successfully for this request. ---")

    try:
        data = request.json
        if not data:
            print("--- [!] Request had no JSON data. Returning 400. ---")
            return jsonify({"status": "error", "message": "Request body must be JSON."}), 400

        print("--- [9] Parsing input data... ---")
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
        print(f"--- [10] Processing {num_trains} train(s)... ---")
        for i, (train_no, station_code) in enumerate(train_station_pairs):
            city, speed = cities[i], speeds[i]
            try:
                weather_desc, visibility_km, ok = get_weather(city)
                predicted_delay = predict_delay(train_no, station_code, "")
                action = agent.get_action(predicted_delay, visibility_km, speed, weather_desc)

                row = get_train_station_row(train_no, station_code)
                prob_info = ""
                if row:
                    info_parts = [f"{key.split('_')[-1].title()}: {row.get(key):.0%}" for key in ["p_on_time", "p_slight", "p_significant", "p_cancelled"] if key in row]
                    prob_info = ", ".join(info_parts)
                results.append({ "train": f"{train_no}:{station_code}" if station_code else train_no, "city": city, "weather": f"{weather_desc}{' (fallback)' if not ok else ''}", "visibility": f"{visibility_km:.2f} km", "predictedDelay": f"{predicted_delay:.2f} mins", "probabilities": prob_info or "N/A", "currentSpeed": f"{speed:.1f} km/h", "action": action })
            except Exception as e:
                print(f"--- [!] Error processing train {train_no}: {e}")
                results.append({"train": f"{train_no}:{station_code}", "error": str(e)})
        
        print("--- [11] Successfully processed all trains. Sending response. ---")
        return jsonify({"status": "success", "predictions": results})

    except Exception as e:
        print("\n\n!!! FATAL CRASH inside handle_prediction !!!")
        traceback.print_exc() # Print the full error traceback
        return jsonify({"status": "error", "message": "An internal server error occurred. Check backend logs."}), 500

if __name__ == "__main__":
    # Add a clear, final message before starting the server
    print("\n--- [!] Starting Flask Development Server ---")
    print("--- [!] Server will be ready when you see '* Running on http://127.0.0.1:5001' ---")
    print("--- [!] Once ready, test the server by visiting: http://127.0.0.1:5001/status in your browser.")
    app.run(debug=True, port=5001, use_reloader=False)

