import numpy as np
from quantics import Quantics
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error


def generate_models(X, y):
    models = []

    # variação de hiperparâmetros
    for depth in [3, 5, 10]:
        for n in [50, 100]:
            model = RandomForestRegressor(max_depth=depth, n_estimators=n)
            model.fit(X, y)
            models.append(model)

    # outro algoritmo
    for alpha in [0.1, 1.0, 10]:
        model = Ridge(alpha=alpha)
        model.fit(X, y)
        models.append(model)

    return models


def evaluate_models(models, X, y):
    results = []

    for model in models:
        pred = model.predict(X)

        mse = mean_squared_error(y, pred)
        complexity = getattr(model, "n_estimators", 1)

        results.append([mse, complexity])

    return np.array(results)


def quantics_filter(results):
    q = Quantics()
    clusters = q.fit_transform(results)

    return clusters


def select_best(models, results):
    # escolhe menor erro
    best_idx = np.argmin(results[:, 0])
    return models[best_idx]


def run_pipeline(X, y):
    models = generate_models(X, y)

    results = evaluate_models(models, X, y)

    clusters = quantics_filter(results)

    best_model = select_best(models, results)

    return best_model, results.tolist()
