# 🧠 ML_V1 – FastAPI + Celery + Redis

Este módulo implementa um pipeline de Machine Learning otimizado para **baixa latência** usando:

* FastAPI (API rápida)
* Celery (processamento assíncrono)
* Redis (cache + broker)

---

# 🚀 Arquitetura

```
Client Request
     ↓
FastAPI (Gateway)
     ↓
Cache (Redis)
     ↓
Celery Worker (ML Model)
     ↓
Response Storage (Redis)
```

---

# ⚡ Objetivo

Reduzir latência e evitar bloqueio do servidor movendo a inferência para processamento assíncrono.

---

# 📂 Estrutura

```
ml/
 ├── main.py        # API endpoints
 ├── model.py       # Modelo ML
 ├── tasks.py       # Tasks Celery
 ├── worker.py      # Worker runner
 ├── cache.py       # Redis cache
 ├── schemas.py     # Validação (Pydantic)
 ├── config.py      # Configurações
 └── README.md      # Documentação
```

---

# ⚙️ Configuração

## Variáveis de ambiente

```
REDIS_URL=redis://localhost:6379/0
```

---

# 🧠 Modelo (model.py)

* Carregado uma única vez no startup
* Evita reload por request

```
model = Model()
```

---

# 📡 Endpoint principal

## POST `/predict`

### Entrada:

```
{
  "value": 10
}
```

### Fluxo:

1. Gera hash do input
2. Verifica cache
3. Se existir → retorna imediato
4. Se não → envia para Celery

### Resposta:

```
{
  "status": "processing",
  "task_id": "abc123"
}
```

---

## GET `/result/{task_id}`

### Retorna:

```
{
  "status": "done",
  "data": {...}
}
```

---

# ⚡ Cache Strategy

* Baseado em hash do input
* TTL padrão: 5 minutos
* Evita recomputação

---

# 📨 Celery

## Task principal

```
run_prediction(data)
```

### Função:

* Executa modelo
* Salva resultado no Redis
* Retorna resultado

---

# 🧪 Como rodar

## 1. Instalar dependências

```
pip install fastapi uvicorn celery redis
```

---

## 2. Subir Redis

```
docker run -p 6379:6379 redis
```

---

## 3. Rodar API

```
uvicorn app.ml.main:app --reload
```

---

## 4. Rodar Worker

```
celery -A app.ml.worker worker --loglevel=info
```

---

# ⚡ Performance

| Etapa              | Tempo médio |
| ------------------ | ----------- |
| API response       | 10–50 ms    |
| Inferência (async) | 300–800 ms  |

---

# 🧠 Boas práticas aplicadas

* Modelo carregado uma vez (warmup)
* Cache Redis para evitar recomputação
* Processamento assíncrono com Celery
* Separação de responsabilidades

---

# 🔥 Melhorias futuras

* ONNX Runtime (redução de latência)
* Batch inference
* GPU support
* Rate limiting
* Monitoramento (Prometheus/Grafana)

---

# ⚠️ Observações

* FastAPI NÃO deve rodar inferência pesada diretamente
* Sempre usar worker para escala
* Redis é obrigatório para performance ideal

---

# 📌 Resumo

Este módulo transforma o ML service em:

* Escalável
* Rápido
* Não bloqueante

---

# 👨‍💻 Autor

FinoraQi Team
