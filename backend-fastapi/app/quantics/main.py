from fastapi import FastAPI
import numpy as np
from app.quantics_engine import run_pipeline

app = FastAPI()


@app.post("/quantum/train")
async def train():
    # mock de dados (substituir depois)
    X = np.random.rand(100, 3)
    y = np.random.rand(100)

    model, results = run_pipeline(X, y)

    return {
        "message": "modelo treinado",
        "results": results,
        "model_type": str(type(model))
    }
