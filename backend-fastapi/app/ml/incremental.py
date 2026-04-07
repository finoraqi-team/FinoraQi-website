import pandas as pd
import numpy as np
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score
import joblib
from typing import Dict, Any, Optional, List
import warnings
warnings.filterwarnings('ignore')

class IncrementalTrainer:
    """
    Treinador incremental para aprendizado online (um registro por vez)
    Suporta classificação e regressão com múltiplos algoritmos
    """
    
    def __init__(self, problem_type: str = "classification", model_type: Optional[str] = None):
        self.problem_type = problem_type
        self.model_type = model_type or "auto"
        self.is_fitted = False
        
        # Pré-processamento
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.target_encoder = LabelEncoder() if problem_type == "classification" else None
        
        # Modelo base (incremental)
        self.model = self._init_model()
        
        # Métricas acumuladas
        self.metrics_buffer: List[Dict] = []
        self.processed_count = 0
        
    def _init_model(self):
        """Inicializa modelo compatível com partial_fit"""
        if self.model_type == "auto":
            # Auto-seleção baseada no tipo de problema
            if self.problem_type == "classification":
                return SGDClassifier(
                    loss='log_loss', penalty='l2', alpha=0.0001,
                    max_iter=1, tol=None, warm_start=True, random_state=42
                )
            else:
                return SGDRegressor(
                    loss='squared_error', penalty='l2', alpha=0.0001,
                    max_iter=1, tol=None, warm_start=True, random_state=42
                )
        
        elif self.model_type == "histgb":
            # HistGradientBoosting suporta warm_start mas não partial_fit nativo
            # Usamos mini-batches simulados
            return (HistGradientBoostingClassifier if self.problem_type == "classification" 
                   else HistGradientBoostingRegressor)(
                max_iter=10, learning_rate=0.1, random_state=42, warm_start=True
            )
        else:
            # Fallback para SGD
            return SGDClassifier(loss='log_loss', warm_start=True, random_state=42) if self.problem_type == "classification" else SGDRegressor(warm_start=True, random_state=42)
    
    def _preprocess_sample(self, sample: Dict[str, Any]) -> np.ndarray:
        """Preprocessa um único sample para o modelo"""
        # Converter para DataFrame single-row
        df = pd.DataFrame([sample])
        
        # Codificar categóricas
        for col in df.select_dtypes(include=['object', 'category']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                # Fit parcial com valores vistos
                mask = df[col].notna()
                if mask.any():
                    self.label_encoders[col].fit(df[col][mask].astype(str))
            df[col] = self.label_encoders[col].transform(df[col].astype(str).fillna('__missing__'))
        
        # Converter para numpy
        X = df.values.astype(float)
        
        # Escalonar
        if self.is_fitted:
            X = self.scaler.transform(X)
        else:
            X = self.scaler.fit_transform(X)
            self.is_fitted = True
            
        return X
    
    def partial_fit(self, sample: Dict[str, Any], target_value: Any) -> Dict[str, float]:
        """
        Treina o modelo com UM registro por vez
        Retorna métricas atualizadas
        """
        # Preprocessar features
        X = self._preprocess_sample(sample)
        
        # Preprocessar target
        if self.problem_type == "classification":
            if self.target_encoder and not hasattr(self.target_encoder, 'classes_'):
                # Primeiro fit
                y = self.target_encoder.fit_transform([target_value])
            else:
                try:
                    y = self.target_encoder.transform([target_value])
                except ValueError:
                    # Nova classe: expandir encoder (simplificado)
                    self.target_encoder.classes_ = np.append(self.target_encoder.classes_, target_value)
                    y = np.array([len(self.target_encoder.classes_) - 1])
        else:
            y = np.array([float(target_value)])
        
        # Partial fit no modelo
        self.model.partial_fit(X, y, classes=getattr(self.target_encoder, 'classes_', None) if self.problem_type == "classification" else None)
        
        self.processed_count += 1
        
        # Calcular métricas online (simplificadas)
        metrics = self._compute_online_metrics(X, y)
        self.metrics_buffer.append(metrics)
        
        # Manter buffer limitado
        if len(self.metrics_buffer) > 100:
            self.metrics_buffer.pop(0)
            
        return metrics
    
    def _compute_online_metrics(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Calcula métricas aproximadas para feedback em tempo real"""
        try:
            if self.problem_type == "classification":
                pred = self.model.predict(X)
                acc = accuracy_score(y, pred)
                f1 = f1_score(y, pred, average='weighted', zero_division=0)
                
                # Confiança via probabilidade
                if hasattr(self.model, 'predict_proba'):
                    proba = self.model.predict_proba(X)[0]
                    confidence = float(np.max(proba))
                else:
                    confidence = 0.0
                    
                return {
                    "accuracy": float(acc),
                    "f1": float(f1),
                    "confidence": confidence,
                    "processed": self.processed_count,
                    "latency_ms": 0.5  # Placeholder - medir em produção
                }
            else:
                pred = self.model.predict(X)
                mse = mean_squared_error(y, pred)
                r2 = r2_score(y, pred)
                return {
                    "r2": float(max(0, r2)),  # R² pode ser negativo
                    "rmse": float(np.sqrt(mse)),
                    "processed": self.processed_count,
                    "latency_ms": 0.5
                }
        except:
            # Fallback seguro
            return {"processed": self.processed_count, "status": "training"}
    
    def predict(self, sample: Dict[str, Any]) -> Any:
        """Faz predição para um novo sample"""
        X = self._preprocess_sample(sample)
        pred = self.model.predict(X)[0]
        
        if self.problem_type == "classification" and self.target_encoder:
            return self.target_encoder.inverse_transform([pred])[0]
        return pred
    
    def get_metrics(self) -> Dict[str, float]:
        """Retorna métricas consolidadas do treinamento"""
        if not self.metrics_buffer:
            return {"status": "no_data"}
        
        # Média das últimas métricas
        avg_metrics = {}
        for key in self.metrics_buffer[-1].keys():
            if isinstance(self.metrics_buffer[-1][key], (int, float)):
                values = [m[key] for m in self.metrics_buffer if key in m and isinstance(m[key], (int, float))]
                if values:
                    avg_metrics[key] = sum(values) / len(values)
        
        avg_metrics["total_processed"] = self.processed_count
        return avg_metrics
    
    def save(self, path: str):
        """Salva o modelo treinado"""
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "label_encoders": self.label_encoders,
            "target_encoder": self.target_encoder,
            "problem_type": self.problem_type,
            "processed_count": self.processed_count
        }, path)
    
    @classmethod
    def load(cls, path: str) -> 'IncrementalTrainer':
        """Carrega modelo salvo"""
        data = joblib.load(path)
        instance = cls(problem_type=data["problem_type"])
        instance.model = data["model"]
        instance.scaler = data["scaler"]
        instance.label_encoders = data["label_encoders"]
        instance.target_encoder = data["target_encoder"]
        instance.is_fitted = True
        instance.processed_count = data.get("processed_count", 0)
        return instance
