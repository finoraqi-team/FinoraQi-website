"""
Propósito: Definição de schemas de dados (validação) e modelos de banco

Recursos:
Pydantic BaseModel para validação automática de requests/responses
Field com constraints (min, max, regex, enum)
Config com from_attributes para ORM integration
Enums tipados para status, risk_level, payment_method
Modelos SQLAlchemy para persistência (opcional)
"""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime
from typing import Optional, List

# === Enums ===
class TransactionType(str, Enum):
    EXPENSE = "expense"
    INCOME = "income"
    INVESTMENT = "investment"
    TRANSFER = "transfer"

class PaymentMethod(str, Enum):
    PIX = "pix"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    CRYPTO = "crypto"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class PaymentStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ANOMALY_DETECTED = "anomaly_detected"
    PENDING_REVIEW = "pending_review"

# === Request/Response Schemas ===
class PaymentRequest(BaseModel):
    """
    Schema para requisição de processamento de pagamento
    
    Validações:
    - amount: > 0, máximo 1M
    - user_id: string não vazia
    - description: 3-200 caracteres
    - category/method: valores do enum
    """
    user_id: str = Field(..., min_length=1, max_length=100, description="ID único do usuário")
    amount: float = Field(..., gt=0, le=1_000_000, description="Valor da transação em BRL")
    description: str = Field(..., min_length=3, max_length=200, description="Descrição da transação")
    
    category: Optional[TransactionType] = Field(default=TransactionType.EXPENSE)
    payment_method: Optional[PaymentMethod] = Field(default=PaymentMethod.PIX)
    
    # Campos opcionais para contexto adicional
    metadata: Optional[dict] = Field(default=None, description="Dados extras para logging/ML")
    
    @field_validator('description')
    @classmethod
    def description_not_suspicious(cls, v: str) -> str:
        # Validação customizada: bloqueia palavras suspeitas
        suspicious = ["teste", "fake", "fraude", "xxx"]
        if any(word in v.lower() for word in suspicious):
            raise ValueError('Descrição contém termos inválidos')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_demo_001",
                "amount": 150.00,
                "description": "Compra marketplace",
                "category": "expense",
                "payment_method": "pix"
            }
        }

class PaymentResponse(BaseModel):
    """
    Schema para resposta de processamento
    """
    transaction_id: str = Field(..., description="ID único da transação processada")
    status: PaymentStatus = Field(..., description="Status final do processamento")
    amount: float = Field(..., description="Valor processado")
    processing_time_ms: float = Field(..., description="Tempo total em milissegundos")
    
    risk_level: RiskLevel = Field(..., description="Nível de risco calculado")
    ml_score: float = Field(..., ge=0, le=1, description="Score do modelo ML (0-1)")
    
    metadata: dict = Field(default_factory=dict, description="Metadados do processamento")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class BenchmarkResult(BaseModel):
    """
    Schema para resultado do teste de performance
    """
    iterations: int
    min_ms: float
    max_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    std_ms: float
    target_achieved: bool  # >=90% das requests <1ms

# === Modelos de Banco de Dados (SQLAlchemy - opcional) ===
# from sqlalchemy.orm import declarative_base, Mapped, mapped_column
# from sqlalchemy import String, Float, DateTime, Enum as SQLEnum

# Base = declarative_base()

# class TransactionDB(Base):
#     __tablename__ = "transactions"
#     
#     id: Mapped[str] = mapped_column(String(32), primary_key=True)
#     user_id: Mapped[str] = mapped_column(String(100), index=True)
#     amount: Mapped[float] = mapped_column(Float)
#     description: Mapped[str] = mapped_column(String(200))
#     category: Mapped[str] = mapped_column(SQLEnum(TransactionType))
#     payment_method: Mapped[str] = mapped_column(SQLEnum(PaymentMethod))
#     
#     risk_score: Mapped[float] = mapped_column(Float)
#     risk_level: Mapped[str] = mapped_column(SQLEnum(RiskLevel))
#     status: Mapped[str] = mapped_column(SQLEnum(PaymentStatus))
#     
#     processing_time_ms: Mapped[float] = mapped_column(Float)
#     ml_metadata: Mapped[dict] = mapped_column(JSON)  # PostgreSQL
#     
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
#     updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow)