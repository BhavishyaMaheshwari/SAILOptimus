# rl_agent.py
import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib
import os

class SimpleRLAgent:
    def __init__(self, model_file="rl_agent_model.pkl"):
        self.actions = ["decrease", "maintain", "increase"]
        self.weather_map = {"clear":0, "clouds":1, "rain":2, "fog":3}
        self.model_file = model_file

        if os.path.isfile(model_file):
            self.model = joblib.load(model_file)
        else:
            self.model = LogisticRegression(multi_class="multinomial", max_iter=500)
            X, y = self._generate_training_data()
            self.model.fit(X, y)
            joblib.dump(self.model, model_file)

    # ------------------------
    # Encode features
    # ------------------------
    def _encode_state(self, predicted_delay, visibility, speed, weather_desc):
        w = self.weather_map.get(weather_desc.lower(), 0)
        return [predicted_delay/300.0, visibility/10.0, speed/160.0, w]

    # ------------------------
    # Generate synthetic training data
    # ------------------------
    def _generate_training_data(self):
        X = []
        y = []
        for delay in range(0, 301, 30):
            for vis in [1,2,3,5,7,10]:
                for speed in range(0, 161, 20):
                    for w in ["clear","clouds","rain","fog"]:
                        action = "maintain"
                        # Low speed → increase
                        if speed < 40:
                            action = "increase"
                        # High speed → decrease
                        elif speed > 120:
                            action = "decrease"
                        # Bad visibility or bad weather
                        if vis < 3 or w in ["fog","rain"]:
                            if speed > 60:
                                action = "decrease"
                            elif speed < 50:
                                action = "increase"
                        # Delay influence
                        if delay > 120:
                            action = "increase"
                        elif delay < 20 and action == "maintain":
                            action = "decrease"

                        X.append(self._encode_state(delay, vis, speed, w))
                        y.append(action)
        return np.array(X), np.array(y)

    # ------------------------
    # Predict action
    # ------------------------
    def get_action(self, predicted_delay, visibility, speed, weather_desc="Clear"):
        state = np.array([self._encode_state(predicted_delay, visibility, speed, weather_desc)])
        return self.model.predict(state)[0]

# ------------------------
# Quick test
# ------------------------
if __name__ == "__main__":
    agent = SimpleRLAgent()
    print(agent.get_action(90, 2.0, 20, "Fog"))   # likely "increase"
    print(agent.get_action(120, 10.0, 80, "Clear")) # likely "maintain"
    print(agent.get_action(60, 2.0, 100, "Rain"))   # likely "decrease"
