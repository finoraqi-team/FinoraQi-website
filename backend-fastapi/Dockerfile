# =============================================================================
# FinoraQi Backend - Dockerfile
# =============================================================================
# Propósito: Build de imagem otimizada para produção com ML <1ms
# Base: Python 3.11 slim para menor superfície de ataque
# Otimizações: Multi-stage build, cache de layers, non-root user
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1: Builder (instala dependências de build)
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Metadados da imagem (aparecem em `docker inspect`)
LABEL org.opencontainers.image.title="FinoraQi API"
LABEL org.opencontainers.image.description="Backend FastAPI com ML matemático"
LABEL org.opencontainers.image.vendor="FinoraQi Team"
LABEL org.opencontainers.image.license="MIT"

# Variáveis de build (podem ser sobrescritas com --build-arg)
ARG BUILD_ENV=production
ARG INSTALL_DEV=false

# Instalar dependências de sistema NECESSÁRIAS para compilar packages Python
# Nota: Usamos --no-install-recommends para imagem menor e removemos cache depois
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Compiladores para packages com extensões C (NumPy, Numba, etc.)
    build-essential \
    g++ \
    gcc \
    # Bibliotecas BLAS/LAPACK para computação matemática acelerada
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    # Utilitários para health checks e debugging
    curl \
    tini \
    # Limpeza para reduzir tamanho da imagem
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Definir diretório de trabalho
WORKDIR /build

# Copiar apenas requirements primeiro (cache de layer do Docker)
# Isso evita reinstalar todas as deps se apenas o código mudar
COPY requirements.txt ./
COPY requirements-dev.txt ./

# Instalar dependências Python em prefixo customizado para copiar depois
# --user: instala em ~/.local para não precisar de root no runtime
# --no-cache-dir: reduz tamanho da imagem final
# --prefix=/install: instala em local fácil de copiar para stage final
RUN pip install --user --no-cache-dir --prefix=/install -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then \
         pip install --user --no-cache-dir --prefix=/install -r requirements-dev.txt; \
       fi

# -----------------------------------------------------------------------------
# STAGE 2: Runtime (imagem final mínima)
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# Metadados repetidos para o stage final
LABEL org.opencontainers.image.title="FinoraQi API"
LABEL org.opencontainers.image.source="https://github.com/finoraqi-team/FinoraQi-website"

# -----------------------------------------------------------------------------
# Variáveis de Ambiente para Otimização ML/NumPy
# -----------------------------------------------------------------------------
# Limita threads para evitar oversubscription em containers com CPU limitada
# Importante para performance consistente em Kubernetes com resource limits
ENV OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2 \
    NUMBA_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=2 \
    VECLIB_MAXIMUM_THREADS=2 \
    # Python optimizations
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Path para packages instalados no stage builder
    PATH="/usr/local/bin:$PATH" \
    PYTHONPATH="/usr/local/lib/python3.11/site-packages"

# -----------------------------------------------------------------------------
# Instalação de Runtime Dependencies (apenas o necessário)
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Runtime libs para NumPy/Numba (sem headers de compilação)
    libgomp1 \
    libopenblas0 \
    liblapack3 \
    # Tini como init system para reaparar zombies e signal forwarding
    tini \
    # Limpeza agressiva
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && useradd -m -u 1000 appuser

# Copiar packages Python do stage builder
# Isso transfere apenas o necessário, sem compiladores
COPY --from=builder --chown=appuser:appuser /install /usr/local

# Copiar código da aplicação com permissões corretas
WORKDIR /app
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser pyproject.toml ./pyproject.toml

# -----------------------------------------------------------------------------
# Health Check Otimizado
# -----------------------------------------------------------------------------
# Verifica se a API está respondendo em <5 segundos
# Parâmetros:
#   --interval: verifica a cada 30s
#   --timeout: falha se health check demorar >10s  
#   --start-period: espera 30s após container start antes de começar checks
#   --retries: após 3 falhas consecutivas, marca container como unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:8000/health', timeout=5); exit(0 if r.status_code == 200 else 1)" || exit 1

# Mudar para usuário não-root (security best practice)
USER appuser

# Expor porta (apenas documentação, não publica automaticamente)
EXPOSE 8000

# -----------------------------------------------------------------------------
# Comando de Inicialização
# -----------------------------------------------------------------------------
# Usamos tini como entrypoint para:
# 1. Reapar processos zombie (evita memory leaks)
# 2. Forward signals corretamente (SIGTERM para graceful shutdown)
# 3. Executar o comando real da aplicação
#
# Uvicorn flags explicadas:
#   --host 0.0.0.0: aceita conexões de qualquer interface
#   --port 8000: porta interna do container
#   --workers 2: número de worker processes (ajustar para CPU do host)
#   --loop uvloop: event loop mais rápido que asyncio padrão (~2-4x)
#   --http httptools: parser HTTP otimizado em C
#   --lifespan on: habilita startup/shutdown events (para carregar modelos ML)
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uvicorn", \
     "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--lifespan", "on"]
