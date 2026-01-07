from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


# ========== CONSTANTES ==========
# Tipos de transacción (mapeo numérico)
TRANSACTION_TYPE_INGRESO = 1
TRANSACTION_TYPE_GASTO = 2

TRANSACTION_TYPE_MAP = {
    TRANSACTION_TYPE_INGRESO: "ingreso",
    TRANSACTION_TYPE_GASTO: "gasto"
}

TRANSACTION_TYPE_REVERSE_MAP = {
    "ingreso": TRANSACTION_TYPE_INGRESO,
    "gasto": TRANSACTION_TYPE_GASTO
}

# Frecuencias de pago (mapeo numérico)
FREQUENCY_MENSUAL = 1
FREQUENCY_BIMENSUAL = 2
FREQUENCY_TRIMESTRAL = 3
FREQUENCY_SEMESTRAL = 4
FREQUENCY_ANUAL = 5

FREQUENCY_MAP = {
    FREQUENCY_MENSUAL: "mensual",
    FREQUENCY_BIMENSUAL: "bimensual",
    FREQUENCY_TRIMESTRAL: "trimestral",
    FREQUENCY_SEMESTRAL: "semestral",
    FREQUENCY_ANUAL: "anual"
}

FREQUENCY_REVERSE_MAP = {
    "mensual": FREQUENCY_MENSUAL,
    "bimensual": FREQUENCY_BIMENSUAL,
    "trimestral": FREQUENCY_TRIMESTRAL,
    "semestral": FREQUENCY_SEMESTRAL,
    "anual": FREQUENCY_ANUAL
}


# ========== MODELOS ==========
class User(Base):
    """Modelo de usuario"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    """Categorías personalizables por usuario"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    color = Column(String, default="#3498db")  # Color hex para UI
    icon = Column(String, default="📦")  # Emoji o icono
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")


class Transaction(Base):
    """Transacciones (ingresos y gastos)"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Integer, nullable=False)  # 1=ingreso, 2=gasto
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    attachment_url = Column(String)  # URL del comprobante (opcional)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    """Presupuestos mensuales por categoría"""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    alert_threshold = Column(Float, default=0.8)  # Alertar al 80% del presupuesto
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")


class Reminder(Base):
    """Recordatorios de pagos recurrentes"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    amount = Column(Float, nullable=False)
    frequency = Column(Integer, nullable=False)  # 1=mensual, 2=bimensual, 3=trimestral, 4=semestral, 5=anual
    due_day = Column(Integer, nullable=False)  # Día del mes (1-31)
    is_active = Column(Boolean, default=True)
    last_paid_date = Column(Date)  # Última vez que se marcó como pagado
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="reminders")
