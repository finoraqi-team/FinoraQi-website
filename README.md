
<div align="center">

<img width="700" height="390" alt="image" src="https://github.com/user-attachments/assets/8be4de0d-07c8-420d-b076-19c96d76f66e" />

# FinoraQi®

![Status](https://img.shields.io/badge/status-MVP%20Ready-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

**Plataforma de Educação Financeira e Construção de Score de Crédito**  

CRM de gastos com alertas em tempo real, API de crédito instantâneo focada em jovens e API de spread bancário em tempo real para parceiros bancários.

[Demo](https://finora-qi-brlcore.vercel.app) • [API Docs](core.html)

![HTML | CSS | JAVA | Preview](languages.png)

</div>

---

## Visão Geral

FinoraQi é uma solução financeira acessível e inclusiva que ajuda jovens brasileiros a:

- Controlar gastos com alertas inteligentes (SMS + Push)
- Construir histórico de crédito de forma rápida e segura
- Acessar ferramentas de educação financeira gamificada
- Obter atualização instantânea de score nos bureaus (Serasa/SPC)

FinoraQi também atua em processamento de dados visando maior escalabilidade e atomicidade:

- processamento de planilhas em tempo real (Iot | Streamming | Artificial Intelligence | Machine Learning)
- Api em desenvolvimento multimodal
- Gerenciamento de carteira para grandes empresas
- Alteração de valores no dashboard para gerir métricas
- save em xlsx

---

## Fluxo de Processamento de Pagamento

<img width="2000" height="2000" alt="mermaid-1774568097561" src="https://github.com/user-attachments/assets/3d6bf77d-f76c-4924-a5bc-3e9a8fce66a1" />

---

## 🎯 O que é?

O **FinoraQi** ajuda jovens a:
- 📊 Controlar gastos com alertas inteligentes
- 💳 Construir histórico de crédito rapidamente
- 🤖 Processar planilhas com IA em tempo real
- 🎮 Aprender educação financeira de forma gamificada

---

## 🚀 Começar em 2 minutos

### Com Docker (Recomendado)
```bash
# 1. Clone o projeto
git clone https://github.com/finoraqi-team/FinoraQi-website.git
cd FinoraQi-website

# 2. Configure as variáveis
cp .env.example .env

# 3. Suba tudo
docker-compose up -d

# 4. Acesse:
# 🌐 Frontend: http://localhost:8080
# 📚 API: http://localhost:8000/docs
```

### Manual (Desenvolvimento)
```bash
# Backend
cd backend-fastapi
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (outro terminal)
cd frontend
python -m http.server 8080
```

---

## 📁 Estrutura

```
FinoraQi-website/
├── frontend/           # HTML/CSS/JS vanilla
│   ├── index.html      # Landing page
│   ├── dashboard.html  # Dashboard do usuário
│   └── transactions.html # Controle com ML
│
├── backend-fastapi/    # API Python
│   ├── app/
│   │   ├── main.py     # Entry point
│   │   ├── api/        # Endpoints
│   │   ├── ml/         # Modelos ML <1ms
│   │   └── db/         # Banco de dados
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml  # Orquestração local
├── .env.example        # Template de config
└── README.md           # Você está aqui
```

---

## ✨ Funcionalidades Principais

### Para Usuários
- ✅ Dashboard com gráficos de gastos
- ✅ Upload de planilhas (.xlsx, .csv) com categorização automática
- ✅ Alertas em tempo real via WebSocket
- ✅ Exportação de relatórios
- ✅ Tela de simulação de pagamentos

### Para Desenvolvedores
- ✅ API REST com FastAPI (<1ms por request)
- ✅ WebSockets para atualizações em tempo real
- ✅ Modelos ML otimizados com Numba JIT
- ✅ PostgreSQL + Redis para performance
- ✅ Docker ready para deploy

---

## 🔌 API Rápida

```bash
# Health check
curl http://localhost:8000/health

# Processar pagamento
curl -X POST http://localhost:8000/api/v1/payment/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "amount": 150.00,
    "description": "Compra teste",
    "category": "expense",
    "payment_method": "pix"
  }'

# Ver docs completas
# Acesse: http://localhost:8000/docs
```

---

## ⚙️ Configuração (.env)

```bash
# App
ENV=development
SECRET_KEY=mude-esta-chave-na-producao

# Banco de Dados
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/finoraqi

# Redis (cache)
REDIS_URL=redis://localhost:6379/0

# Auth
JWT_SECRET_KEY=mude-tambem-esta-chave

# Google OAuth (opcional)
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-secret
```

---

## 🧪 Testes

```bash
cd backend-fastapi

# Instalar deps de teste
pip install -r requirements-dev.txt

# Rodar testes
pytest

# Com coverage
pytest --cov=app
```

---

<div align="center">

Feito para democratizar o crédito no Brasil 🇧🇷

</div>

---

## Backend Integrado | (opensource)

[API-REAL-TIME](https://github.com/kauecodify/SpreadLiquidityAPI)

---

## Opensource em utilização 

[Preview Nepal](https://www.finoraq.org/)

---

## 📄 Licença

MIT - Veja [LICENSE](./LICENSE) para detalhes.

---

## 📞 Contato

- 📧 finoraqi.finance@gmail.com
- 🌐 https://finora-qi-brlcore.vercel.app
- 🐛 [Issues](https://github.com/finoraqi-team/FinoraQi-website/issues)
