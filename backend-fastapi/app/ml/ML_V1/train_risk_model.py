import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib

# Dados simulados (substituir por dados reais + chave)
data = pd.DataFrame({
    "renda": [2000, 5000, 3000, 10000, 1500, 7000, 4000],
    "idade": [25, 40, 30, 50, 22, 45, 35],
    "score_credito": [400, 700, 500, 800, 300, 750, 650],
    "dividas": [1500, 1000, 2000, 500, 2500, 800, 1200],
    "inadimplente": [1, 0, 1, 0, 1, 0, 0]
})

X = data[["renda", "idade", "score_credito", "dividas"]]
y = data["inadimplente"]

model = LogisticRegression()
model.fit(X, y)

joblib.dump(model, "risk_model.joblib")

print("Modelo de risco treinado!")
