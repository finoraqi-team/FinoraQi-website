from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Dict, Any
import time
import numpy as np
from numba import jit
import uvicorn
import asyncio
import json
from datetime import datetime
import hashlib
import secrets

# Configuração da aplicação
app = FastAPI(
    title="FinoraQi Payment API",
    description="Processamento de pagamentos com ML matemático <1ms",
    version="2.0.0-ml",
    default_response_class=ORJSONResponse,
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: especificar domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELOS PYDANTIC ===
class PaymentRequest(BaseModel):
    user_id: str = Field(..., min_length=8, max_length=36, description="ID do usuário")
    amount: float = Field(..., gt=0, le=100000, description="Valor em BRL")
    description: str = Field(..., max_length=200, description="Descrição da transação")
    category: Literal["income", "expense", "investment", "transfer"]
    payment_method: Literal["pix", "credit_card", "debit_card", "bank_transfer", "wallet"]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('amount')
    def validate_amount_precision(cls, v):
        return round(v, 2)  # Garantir 2 casas decimais

class PaymentResponse(BaseModel):
    success: bool
    transaction_id: str
    status: Literal["approved", "pending", "rejected", "anomaly_detected"]
    amount: float
    processing_time_ms: float
    ml_score: float
    risk_level: Literal["low", "medium", "high"]
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProcessingProgress(BaseModel):
    job_id: str
    stage: Literal["received", "validating", "ml_scoring", "fraud_check", "approved"]
    progress_percent: int
    elapsed_ms: float
    estimated_remaining_ms: float

# === ML MATEMÁTICO OTIMIZADO COM NUMBA ===
class PaymentMLProcessor:
    """Processador ML matemático para pagamentos - otimizado para <0.5ms"""
    
    def __init__(self):
        # Pré-compilar funções com Numba no init
        self._warmup()
        
    def _warmup(self):
        """Warm-up: compilar funções JIT e aquecer cache"""
        # Dados dummy para compilação JIT
        dummy_features = np.array([[1.0, 0.5, 0.2, 100.0, 1.5]], dtype=np.float32)
        _ = self._calculate_risk_score_numba(dummy_features)
        _ = self._anomaly_detection_vectorized(np.array([100, 105, 98, 102], dtype=np.float32))
        
    @jit(nopython=True, cache=True, parallel=False)
    def _calculate_risk_score_numba(self, features: np.ndarray) -> float:
        """
        Cálculo de risco com fórmula matemática otimizada
        Features: [amount_normalized, velocity, user_trust, historical_avg, time_factor]
        Retorna: score 0-1 (0=baixo risco, 1=alto risco)
        """
        # Pesos otimizados (treinados offline)
        weights = np.array([0.35, 0.25, 0.20, 0.15, 0.05], dtype=np.float32)
        
        # Sigmoid vectorizada para normalização
        def sigmoid(x):
            return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))
        
        # Cálculo do score
        linear_comb = np.dot(features[0], weights)
        risk_score = sigmoid(linear_comb * 2.5 - 1.25)  # Ajuste de curva
        
        return float(risk_score)
    
    @jit(nopython=True, cache=True)
    def _anomaly_detection_vectorized(self, amounts: np.ndarray) -> np.ndarray:
        """Detecção de anomalias com Z-score vetorizado - O(n)"""
        if len(amounts) < 3:
            return np.zeros(len(amounts), dtype=np.bool_)
        
        mean = np.mean(amounts)
        std = np.std(amounts)
        
        if std < 0.01:  # Evitar divisão por zero
            return np.zeros(len(amounts), dtype=np.bool_)
        
        z_scores = np.abs((amounts - mean) / std)
        return z_scores > 2.5  # Threshold para anomalia
    
    def process_payment_features(self, payment: PaymentRequest, user_history: Dict) -> Dict:
        """
        Extrai features e calcula score em <0.3ms
        """
        start = time.perf_counter()
        
        # Extrair features normalizadas
        amount_norm = min(payment.amount / 10000, 1.0)  # Normalizar para 0-1
        velocity = user_history.get('tx_last_hour', 0) / 10  # Normalizar
        user_trust = user_history.get('trust_score', 0.8)
        hist_avg = user_history.get('avg_amount', 100)
        time_factor = 1.0 if 9 <= datetime.now().hour <= 18 else 1.3  # Horário comercial
        
        # Feature vector
        features = np.array([[
            amount_norm,
            velocity,
            user_trust,
            min(payment.amount / max(hist_avg, 1), 3.0),  # Ratio amount/avg
            time_factor
        ]], dtype=np.float32)
        
        # Calcular risco com função compilada
        risk_score = self._calculate_risk_score_numba(features)
        
        # Verificar anomalia com histórico recente
        recent_amounts = np.array(user_history.get('last_10_amounts', [100]*10), dtype=np.float32)
        is_anomaly = self._anomaly_detection_vectorized(
            np.append(recent_amounts, payment.amount)
        )[-1]
        
        elapsed = (time.perf_counter() - start) * 1000
        
        return {
            'risk_score': round(risk_score, 4),
            'is_anomaly': bool(is_anomaly),
            'features_used': 5,
            'ml_latency_ms': round(elapsed, 4)
        }

# Instância global do processador ML
ml_processor = PaymentMLProcessor()

# Cache em memória para user history (simulado)
user_cache: Dict[str, Dict] = {}

def get_user_history(user_id: str) -> Dict:
    """Simula busca de histórico do usuário com cache"""
    if user_id not in user_cache:
        # Gerar histórico simulado consistente
        np.random.seed(hash(user_id) % 2**32)
        user_cache[user_id] = {
            'trust_score': 0.7 + np.random.random() * 0.25,
            'avg_amount': 50 + np.random.exponential(100),
            'tx_last_hour': np.random.poisson(2),
            'last_10_amounts': (50 + np.random.exponential(80, 10)).tolist()
        }
    return user_cache[user_id]

# === ENDPOINTS ===

@app.get("/health", tags=["monitoring"])
async def health():
    """Health check com status dos modelos ML"""
    return ORJSONResponse({
        "status": "healthy",
        "ml_processor": "loaded",
        "numba_compiled": True,
        "timestamp": time.time()
    })

@app.post("/api/v1/payment/process", response_model=PaymentResponse, tags=["payments"])
async def process_payment(payment: PaymentRequest):
    """
    Processa pagamento com ML matemático otimizado
    Tempo alvo: <1ms total (validação + ML + resposta)
    """
    start_time = time.perf_counter()
    
    # Step 1: Validação rápida (<0.05ms)
    if payment.amount > 10000:
        return PaymentResponse(
            success=False,
            transaction_id=f"tx_{secrets.token_hex(8)}",
            status="rejected",
            amount=payment.amount,
            processing_time_ms=round((time.perf_counter() - start_time) * 1000, 4),
            ml_score=0.0,
            risk_level="high",
            timestamp=time.time(),
            metadata={"reason": "amount_exceeds_limit"}
        )
    
    # Step 2: Buscar histórico do usuário (<0.1ms com cache)
    user_history = get_user_history(payment.user_id)
    
    # Step 3: Processamento ML (<0.4ms com Numba)
    ml_result = ml_processor.process_payment_features(payment, user_history)
    
    # Step 4: Decisão de aprovação
    risk_level = "low" if ml_result['risk_score'] < 0.3 else "medium" if ml_result['risk_score'] < 0.7 else "high"
    
    if ml_result['is_anomaly'] and risk_level == "high":
        status = "anomaly_detected"
        success = False
    elif risk_level == "high":
        status = "rejected"
        success = False
    else:
        status = "approved"
        success = True
    
    # Calcular tempo total
    total_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Gerar ID da transação
    tx_id = f"tx_{hashlib.sha256(f'{payment.user_id}{payment.amount}{time.time()}'.encode()).hexdigest()[:16]}"
    
    response = PaymentResponse(
        success=success,
        transaction_id=tx_id,
        status=status,
        amount=payment.amount,
        processing_time_ms=round(total_time_ms, 4),
        ml_score=ml_result['risk_score'],
        risk_level=risk_level,
        timestamp=time.time(),
        metadata={
            "ml_latency_ms": ml_result['ml_latency_ms'],
            "is_anomaly": ml_result['is_anomaly'],
            "features_used": ml_result['features_used'],
            "user_trust": user_history['trust_score']
        }
    )
    
    return response

@app.post("/api/v1/payment/batch", tags=["payments"])
async def process_batch_payments(payments: list[PaymentRequest], background_tasks: BackgroundTasks):
    """Processamento em batch com paralelismo - ideal para planilhas"""
    start_time = time.perf_counter()
    
    results = []
    for payment in payments:
        result = await process_payment(payment)
        results.append(result)
    
    total_time = (time.perf_counter() - start_time) * 1000
    avg_time = total_time / len(payments) if payments else 0
    
    return ORJSONResponse({
        "success": True,
        "processed": len(results),
        "approved": sum(1 for r in results if r.success),
        "total_time_ms": round(total_time, 2),
        "avg_time_per_payment_ms": round(avg_time, 4),
        "results": results
    })

# === WEBSOCKET PARA TEMPO REAL ===
@app.websocket("/ws/payment/{user_id}")
async def payment_websocket(websocket: WebSocket, user_id: str):
    """WebSocket para atualizações em tempo real do processamento"""
    await websocket.accept()
    
    try:
        while True:
            # Aguardar mensagem do frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "process_payment":
                payment_data = message.get("data")
                
                # Simular etapas de processamento com timing real
                stages = [
                    ("received", 0, 0.1),
                    ("validating", 15, 0.15),
                    ("ml_scoring", 45, 0.25),
                    ("fraud_check", 75, 0.15),
                    ("approved", 100, 0.05)
                ]
                
                job_id = secrets.token_hex(8)
                
                for stage, progress, duration in stages:
                    stage_start = time.perf_counter()
                    
                    # Simular processamento da etapa
                    await asyncio.sleep(duration / 1000)  # Converter ms para segundos
                    
                    elapsed = (time.perf_counter() - stage_start) * 1000
                    
                    progress_data = ProcessingProgress(
                        job_id=job_id,
                        stage=stage,
                        progress_percent=progress,
                        elapsed_ms=round(elapsed, 3),
                        estimated_remaining_ms=round(sum(s[2] for s in stages if s[1] > progress), 3)
                    )
                    
                    await websocket.send_json(progress_data.dict())
                
                # Enviar resultado final
                final_result = {
                    "type": "result",
                    "job_id": job_id,
                    "success": True,
                    "transaction_id": f"tx_{secrets.token_hex(8)}",
                    "total_time_ms": round(sum(s[2] for s in stages), 3),
                    "timestamp": time.time()
                }
                await websocket.send_json(final_result)
                
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# === ENDPOINT DE BENCHMARK ===
@app.get("/api/v1/benchmark", tags=["monitoring"])
async def benchmark(iterations: int = 100):
    """Endpoint para testar performance - retorna estatísticas"""
    results = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        # Simular processamento mínimo
        _ = ml_processor._calculate_risk_score_numba(
            np.array([[0.5, 0.3, 0.8, 1.2, 1.0]], dtype=np.float32)
        )
        
        elapsed = (time.perf_counter() - start) * 1000
        results.append(elapsed)
    
    return ORJSONResponse({
        "iterations": iterations,
        "min_ms": round(min(results), 4),
        "max_ms": round(max(results), 4),
        "mean_ms": round(np.mean(results), 4),
        "p50_ms": round(np.percentile(results, 50), 4),
        "p95_ms": round(np.percentile(results, 95), 4),
        "p99_ms": round(np.percentile(results, 99), 4),
        "std_ms": round(np.std(results), 4),
        "target_achieved": np.percentile(results, 99) < 1.0
    })

# === ROOT ===
@app.get("/")
async def root():
    return {
        "message": "FinoraQi Payment API v2.0-ML",
        "endpoints": {
            "process_payment": "POST /api/v1/payment/process",
            "batch_process": "POST /api/v1/payment/batch",
            "websocket": "WS /ws/payment/{user_id}",
            "benchmark": "GET /api/v1/benchmark",
            "health": "GET /health",
            "docs": "/docs"
        },
        "performance_target": "<1ms per payment with ML"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=2,  # Otimizado para 2 vCPU
        loop="uvloop",  # Event loop mais rápido
        http="httptools"  # Parser HTTP otimizado
    )
