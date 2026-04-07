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

from joblib import Parallel, delayed

        results = Parallel(n_jobs=-1)(
            delayed(self.evaluate_single)(m, X, y) for m in models
        )
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

# import numpy as np
# from quantics import Quantics
# from sklearn.metrics import mean_squared_error


# class QuantumEngine:

#     def __init__(self, generations=5, population_size=20):
#         self.generations = generations
#         self.population_size = population_size

#     # -------------------------
#     # Geração inicial
#     # -------------------------
#     def generate_population(self, X, y):
#         from sklearn.ensemble import RandomForestRegressor
#         from sklearn.linear_model import Ridge

#         models = []

#         for _ in range(self.population_size):
#             if np.random.rand() > 0.5:
#                 model = RandomForestRegressor(
#                     max_depth=np.random.randint(2, 10),
#                     n_estimators=np.random.randint(10, 150)
#                 )
#             else:
#                 model = Ridge(
#                     alpha=np.random.uniform(0.01, 10)
#                 )

#             model.fit(X, y)
#             models.append(model)

#         return models

#     # -------------------------
#     # Avaliação multi-métrica
#     # -------------------------
#     def evaluate(self, models, X, y):
#         results = []

#         for model in models:
#             pred = model.predict(X)

#             mse = mean_squared_error(y, pred)
#             variance = np.var(pred)

#             complexity = getattr(model, "n_estimators", 1)

#             results.append([mse, variance, complexity])

#         return np.array(results)

#     # -------------------------
#     # Filtragem com quantics
#     # -------------------------
#     def quantics_selection(self, models, results):
#         q = Quantics()
#         clusters = q.fit_transform(results)

#         # pega melhores pontos (menor erro)
#         scores = results[:, 0]
#         best_indices = np.argsort(scores)[: max(3, len(models)//4)]

#         return [models[i] for i in best_indices]

#     # -------------------------
#     # Mutação (evolução)
#     # -------------------------
#     def mutate(self, models, X, y):
#         new_models = []

#         for model in models:
#             params = model.get_params()

#             if "max_depth" in params:
#                 params["max_depth"] = max(2, params["max_depth"] + np.random.randint(-2, 3))

#             if "alpha" in params:
#                 params["alpha"] *= np.random.uniform(0.5, 1.5)

#             new_model = model.__class__(**params)
#             new_model.fit(X, y)

#             new_models.append(new_model)

#         return new_models

#     # -------------------------
#     # Loop evolutivo principal
#     # -------------------------
#     def run(self, X, y):
#         population = self.generate_population(X, y)

#         for gen in range(self.generations):
#             results = self.evaluate(population, X, y)

#             selected = self.quantics_selection(population, results)

#             mutated = self.mutate(selected, X, y)

#             population = selected + mutated

#         final_results = self.evaluate(population, X, y)

#         best_idx = np.argmin(final_results[:, 0])

#         return population[best_idx], final_results

#         def build_ensemble(models, X):
#         preds = [m.predict(X) for m in models]
#         return np.mean(preds, axis=0)

#         self.history.append(results)
