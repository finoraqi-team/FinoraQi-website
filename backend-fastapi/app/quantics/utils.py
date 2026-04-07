# utils.py

import numpy as np
from sklearn.metrics import mean_squared_error


# -------------------------
# Avaliação avançada
# -------------------------

def evaluate_model(model, X, y):
    pred = model.predict(X)

    mse = mean_squared_error(y, pred)
    rmse = np.sqrt(mse)
    variance = np.var(pred)

    return {
        "mse": mse,
        "rmse": rmse,
        "variance": variance
    }


# -------------------------
# Score composto (MUITO IMPORTANTE)
# -------------------------

def compute_score(metrics, weights=None):
    """
    Combina múltiplas métricas em um único score
    (quanto menor, melhor)
    """

    if weights is None:
        weights = {
            "mse": 0.6,
            "variance": 0.3,
            "complexity": 0.1
        }

    score = (
        metrics["mse"] * weights["mse"] +
        metrics["variance"] * weights["variance"] +
        metrics.get("complexity", 1) * weights["complexity"]
    )

    return score


# -------------------------
# Seleção dos melhores
# -------------------------

def select_top_models(models, scores, top_k=5):
    indices = np.argsort(scores)[:top_k]
    return [models[i] for i in indices]


# -------------------------
# Ensemble inteligente
# -------------------------

def ensemble_predict(models, X):
    predictions = [m.predict(X) for m in models]
    return np.mean(predictions, axis=0)


# -------------------------
# Mutação de parâmetros
# -------------------------

def mutate_params(params):
    new_params = params.copy()

    for key in new_params:
        if isinstance(new_params[key], (int, float)):
            noise = np.random.uniform(0.8, 1.2)
            new_params[key] = new_params[key] * noise

    return new_params


# -------------------------
# Reamostragem (multi-universe)
# -------------------------

def bootstrap_sample(X, y):
    idx = np.random.choice(len(X), size=len(X), replace=True)
    return X[idx], y[idx]


# -------------------------
# Diversidade de modelos
# -------------------------

def diversity_score(predictions):
    """
    Mede o quão diferentes são os modelos
    """
    return np.mean(np.std(predictions, axis=0))


# -------------------------
# Early stopping simples
# -------------------------

def early_stop(history, patience=3):
    if len(history) < patience:
        return False

    last = history[-patience:]
    return all(last[i] >= last[i-1] for i in range(1, len(last)))
