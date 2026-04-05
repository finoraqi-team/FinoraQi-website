# import time

# class Model:
#     def __init__(self):
#         print("Loading model...")
#         time.sleep(2) # load

#     def predict(self, x):
#         time.sleep(0.5)  # inferência
#         return {"result": x * 2}

# model = Model()

import joblib
import numpy as np

class RiskModel:
    def __init__(self):
        print("Loading risk model...")
        self.model = joblib.load("risk_model.joblib")

    def predict(self, renda, idade, score_credito, dividas):
        X = np.array([[renda, idade, score_credito, dividas]])

        prob = self.model.predict_proba(X)[0][1]  # prob de inadimplência
        prediction = int(prob > 0.5)

        return {
            "inadimplente": prediction,
            "probabilidade": float(prob)
        }

model = RiskModel()
