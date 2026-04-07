# models.py

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.neural_network import MLPRegressor
import numpy as np


class ModelFactory:
    """
    Factory responsável por criar modelos variados com parâmetros aleatórios.
    """

    def __init__(self):
        self.registry = {
            "rf": self._random_forest,
            "ridge": self._ridge,
            "lasso": self._lasso,
            "gboost": self._gboost,
            "mlp": self._mlp,
        }

    def create(self, model_type=None):
        if model_type is None:
            model_type = np.random.choice(list(self.registry.keys()))

        return self.registry[model_type]()

    # -------------------------
    # Modelos
    # -------------------------

    def _random_forest(self):
        return RandomForestRegressor(
            n_estimators=np.random.randint(50, 200),
            max_depth=np.random.randint(3, 15),
            min_samples_split=np.random.randint(2, 10),
        )

    def _ridge(self):
        return Ridge(
            alpha=np.random.uniform(0.01, 10)
        )

    def _lasso(self):
        return Lasso(
            alpha=np.random.uniform(0.001, 1)
        )

    def _gboost(self):
        return GradientBoostingRegressor(
            n_estimators=np.random.randint(50, 200),
            learning_rate=np.random.uniform(0.01, 0.2),
            max_depth=np.random.randint(2, 6),
        )

    def _mlp(self):
        return MLPRegressor(
            hidden_layer_sizes=(
                np.random.randint(50, 150),
                np.random.randint(20, 100),
            ),
            learning_rate_init=np.random.uniform(0.0005, 0.01),
            max_iter=300
        )


# -------------------------
# Wrapper de modelo
# -------------------------

class QuantumModel:
    """
    Wrapper padronizado para qualquer modelo
    """

    def __init__(self, model):
        self.model = model
        self.metrics = {}
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X):
        return self.model.predict(X)

    def set_metrics(self, metrics: dict):
        self.metrics = metrics

    def get_complexity(self):
        return getattr(self.model, "n_estimators", 1)

    def get_params(self):
        return self.model.get_params()
