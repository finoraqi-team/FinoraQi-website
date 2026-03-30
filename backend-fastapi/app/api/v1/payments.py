"""
Propósito: Lógica de processamento de pagamentos (HTTP + WebSocket)

Endpoints:
POST /payment/process - Processa pagamento e retorna resultado
GET /benchmark - Executa teste de performance com N iterações

Funcionalidades:
Validação de schema com Pydantic
Chamada ao modelo ML de scoring
Regras de anti-fraude heurísticas
Geração de transaction_id único
Logging de métricas de performance
Envio de updates via WebSocket em tempo real
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import time, uuid, asyncio

from app.ml.scoring import calculate_risk_score
from app.db.models import PaymentRequest, PaymentResponse, RiskLevel
from app.core.websocket import ConnectionManager

# @app.websocket("/ws/payment/{user_id}")
# async def websocket_endpoint(
#     websocket: WebSocket, 
#     user_id: str,
#     token: str = Query(...)  # Token na query string
# ):
#     # Valida token antes de conectar
#     payload = decode_jwt(token)
#     if payload.get("sub") != user_id:
#         await websocket.close(code=4001)  # Unauthorized
#         return
    
#     await manager.connect(websocket, user_id)

router = APIRouter()
manager = ConnectionManager()

class ProcessResult(BaseModel):
    transaction_id: str
    status: str  # "approved", "rejected", "anomaly_detected"
    amount: float
    processing_time_ms: float
    risk_level: RiskLevel
    ml_score: float
    metadata: dict

@router.post("/payment/process", response_model=ProcessResult)
async def process_payment(payload: PaymentRequest):
    """
    Processa um pagamento com ML scoring em <1ms
    
    Flow:
    1. Valida payload com Pydantic
    2. Extrai features para o modelo ML
    3. Executa scoring com Numba JIT
    4. Aplica regras de anti-fraude
    5. Determina status (approved/rejected/anomaly)
    6. Retorna resultado com métricas
    """
    start_time = time.perf_counter()
    
    # 1. Validação já feita pelo Pydantic no payload
    
    # 2. Extrai features (exemplo simplificado)
    features = {
        "amount": payload.amount,
        "user_trust": 0.94,  # Viria do banco de dados
        "transaction_freq": 1.2,
        "time_of_day": datetime.now().hour / 24.0,
        # ... +10 features
    }
    
    # 3. ML Scoring com Numba JIT (<0.5ms)
    ml_start = time.perf_counter()
    risk_score = calculate_risk_score(**features)
    ml_latency = (time.perf_counter() - ml_start) * 1000
    
    # 4. Regras de anti-fraude
    is_anomaly = detect_anomalies(payload, risk_score)
    
    # 5. Determina status
    if risk_score >= 0.70:
        status = "approved"
        risk_level = "low"
    elif risk_score >= 0.40 or is_anomaly:
        status = "anomaly_detected"
        risk_level = "medium"
    else:
        status = "rejected"
        risk_level = "high"
    
    # 6. Monta resposta
    total_time = (time.perf_counter() - start_time) * 1000
    
    return ProcessResult(
        transaction_id=f"tx_{uuid.uuid4().hex[:8]}",
        status=status,
        amount=payload.amount,
        processing_time_ms=round(total_time, 3),
        risk_level=risk_level,
        ml_score=round(risk_score, 3),
        metadata={
            "ml_latency_ms": round(ml_latency, 3),
            "features_used": len(features),
            "is_anomaly": is_anomaly,
            "user_trust": features["user_trust"],
            "model_version": "v2.1.0-numba"
        }
    )

@router.get("/benchmark")
async def run_benchmark(iterations: int = Query(100, ge=1, le=1000)):
    """
    Executa teste de performance com N iterações
    
    Retorna estatísticas: min, max, mean, p50, p95, p99, std
    """
    import numpy as np
    from app.ml.scoring import calculate_risk_score
    
    latencies = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        
        # Simula features aleatórias
        features = {
            "amount": np.random.exponential(100),
            "user_trust": np.random.beta(2, 1),
            "transaction_freq": np.random.gamma(2, 0.5),
            "time_of_day": np.random.random(),
        }
        
        # Executa scoring
        _ = calculate_risk_score(**features)
        
        latency = (time.perf_counter() - start) * 1000
        latencies.append(latency)
    
    # Calcula estatísticas
    return {
        "iterations": iterations,
        "min_ms": round(np.min(latencies), 4),
        "max_ms": round(np.max(latencies), 4),
        "mean_ms": round(np.mean(latencies), 4),
        "p50_ms": round(np.percentile(latencies, 50), 4),
        "p95_ms": round(np.percentile(latencies, 95), 4),
        "p99_ms": round(np.percentile(latencies, 99), 4),
        "std_ms": round(np.std(latencies), 4),
        "target_achieved": np.mean(np.array(latencies) < 1.0) >= 0.90
    }

def detect_anomalies(payload: PaymentRequest, risk_score: float) -> bool:
    """
    Regras heurísticas de detecção de anomalias
    
    Exemplos:
    - Valor muito acima da média do usuário
    - Transação em horário incomum
    - Método de pagamento novo para o usuário
    """
    # Implementação simplificada
    if payload.amount > 10000:  # Valor suspeito alto
        return True
    if payload.payment_method == "crypto" and risk_score < 0.5:
        return True  # Crypto com baixo trust = revisão
    return False