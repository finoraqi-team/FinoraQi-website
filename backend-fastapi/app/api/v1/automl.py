from fastapi import APIRouter, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import joblib
import io
import time
import uuid
from datetime import datetime

from app.ml.automl_engine import AutoMLEngine
from app.ml.incremental import IncrementalTrainer
from app.core.websocket_manager import ConnectionManager

router = APIRouter(prefix="/automl", tags=["AutoML"])
manager = ConnectionManager()

# estado compartilhado (em produção: usar Redis)
active_sessions: Dict[str, Dict] = {}

class TrainingConfig(BaseModel):
    target: str
    features: List[str]
    problem_type: str  # "classification" or "regression"
    train_mode: str    # "incremental" or "batch"
    model_type: Optional[str] = "auto"  # "auto", "xgboost", "randomforest", "lightgbm"

@router.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    """Analisa arquivo e retorna metadados das colunas"""
    try:
        # ler arquivo
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(await file.read()))
        else:
            df = pd.read_excel(io.BytesIO(await file.read()))
        
        # analisar colunas
        columns_info = []
        for col in df.columns:
            col_type = str(df[col].dtype)
            non_null = df[col].notna().sum()
            unique_vals = df[col].nunique()
            
            # detectar tipo semântico
            semantic_type = "feature"
            if any(kw in col.lower() for kw in ['rating', 'score', 'class', 'target', 'label']):
                semantic_type = "likely_target"
            elif unique_vals < 10 and col_type in ['object', 'category']:
                semantic_type = "categorical"
            elif col_type in ['int64', 'float64']:
                semantic_type = "numeric"
            
            columns_info.append({
                "name": col,
                "dtype": col_type,
                "non_null": int(non_null),
                "unique": int(unique_vals),
                "type": semantic_type
            })
        
        return {
            "success": True,
            "rows": len(df),
            "columns": [c["name"] for c in columns_info],
            "columns_info": columns_info,
            "preview": df.head(3).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo: {str(e)}")

@router.post("/train")
async def train_model(
    file: UploadFile = File(...),
    target: str = Form(...),
    features: str = Form(...),  # JSON string
    problem_type: str = Form(...),
    train_mode: str = Form("incremental"),
    model_type: str = Form("auto")
):
    """Treina modelo AutoML com suporte a treinamento incremental"""
    import json
    features_list = json.loads(features)
    
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {"start_time": time.time()}
    
    try:
        # carregar dados
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(await file.read()))
        else:
            df = pd.read_excel(io.BytesIO(await file.read()))
        
        # validar colunas
        if target not in df.columns:
            raise ValueError(f"Target '{target}' não encontrada")
        missing = [f for f in features_list if f not in df.columns]
        if missing:
            raise ValueError(f"Features não encontradas: {missing}")
        
        # preparar dados
        X = df[features_list].copy()
        y = df[target].copy()
        
        # limpar dados
        mask = X.notna().all(axis=1) & y.notna()
        X, y = X[mask], y[mask]
        
        # inicializar engine
        if train_mode == "incremental":
            trainer = IncrementalTrainer(
                problem_type=problem_type,
                model_type=model_type if model_type != "auto" else None
            )
            
            # treinar incrementalmente (um por um)
            metrics_log = []
            for idx, (xi, yi) in enumerate(zip(X.itertuples(index=False), y)):
                # converter tuple para dict
                xi_dict = dict(zip(features_list, xi))
                
                # treinar com single sample
                metrics = trainer.partial_fit(xi_dict, yi)
                
                # enviar atualização em tempo real via WebSocket
                if idx % 10 == 0 or idx == len(X) - 1:  # batch updates para performance
                    prediction = trainer.predict(xi_dict)
                    await manager.send_personal_message({
                        "type": "prediction",
                        "row_id": idx + 1,
                        "prediction": str(prediction),
                        "confidence": float(metrics.get('confidence', 0.0)),
                        "processed": idx + 1
                    }, session_id)
                    
                    await manager.send_personal_message({
                        "type": "progress",
                        "percent": (idx + 1) / len(X) * 100,
                        "current": idx + 1,
                        "total": len(X)
                    }, session_id)
                
                if idx % 50 == 0:
                    await manager.send_personal_message({
                        "type": "metrics",
                        "metrics": metrics
                    }, session_id)
                    metrics_log.append(metrics)
                
                # simular "tempo real" com pequeno delay configurável
                # (remover em produção para máxima performance)
                # await asyncio.sleep(0.001)
            
            # métricas finais
            final_metrics = trainer.get_metrics()
            
        else:  # batch mode
            engine = AutoMLEngine(problem_type=problem_type, model_type=model_type)
            report = engine.fit(X, y)
            final_metrics = report["metrics"]
            
            # enviar previsões de preview
            predictions = engine.predict(X.head(10))
            for idx, (pred, conf) in enumerate(zip(predictions["prediction"], predictions["confidence"])):
                await manager.send_personal_message({
                    "type": "prediction",
                    "row_id": idx + 1,
                    "prediction": str(pred),
                    "confidence": float(conf),
                    "processed": idx + 1
                }, session_id)
        
        # salvar modelo
        model_path = f"app/models/automl_{session_id}.pkl"
        trainer.save(model_path) if train_mode == "incremental" else engine.save(model_path)
        
        return {
            "success": True,
            "session_id": session_id,
            "metrics": final_metrics,
            "model_path": model_path,
            "processed_rows": len(X)
        }
        
    except Exception as e:
        if session_id in active_sessions:
            del active_sessions[session_id]
        raise HTTPException(status_code=500, detail=f"Erro no treinamento: {str(e)}")

@router.post("/predict")
async def predict_single(data: Dict[str, Any], session_id: Optional[str] = None):
    """Predição em tempo real para um único registro"""
    if not session_id or session_id not in active_sessions:
        # usar modelo default ou retornar erro
        raise HTTPException(status_code=404, detail="Sessão de modelo não encontrada")
    
    try:
        model_path = f"app/models/automl_{session_id}.pkl"
        model = joblib.load(model_path)
        
        prediction = model.predict([data])
        confidence = model.predict_proba([data]).max() if hasattr(model, 'predict_proba') else None
        
        return {
            "prediction": prediction[0],
            "confidence": float(confidence) if confidence else None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na predição: {str(e)}")

@router.post("/export")
async def export_model(session_id: Optional[str] = None):
    """Exporta modelo treinado para download"""
    model_path = f"app/models/automl_{session_id}.pkl" if session_id else "app/models/automl_latest.pkl"
    
    import os
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    return FileResponse(
        path=model_path,
        filename=f"finoraqi_automl_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl",
        media_type="application/octet-stream"
    )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """WebSocket para atualizações em tempo real"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # manter conexão ativa; mensagens são enviadas pelo backend
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
