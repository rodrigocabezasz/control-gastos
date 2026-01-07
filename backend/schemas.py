"""
Schemas Pydantic para validación de datos
"""
from pydantic import BaseModel, EmailStr, Field, validator, field_serializer
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Mapeos de tipos (constantes locales para evitar imports circulares)
TRANSACTION_TYPE_MAP = {1: "ingreso", 2: "gasto"}
TRANSACTION_TYPE_REVERSE_MAP = {"ingreso": 1, "gasto": 2}

FREQUENCY_MAP = {
    1: "mensual",
    2: "bimensual",
    3: "trimestral",
    4: "semestral",
    5: "anual"
}
FREQUENCY_REVERSE_MAP = {
    "mensual": 1,
    "bimensual": 2,
    "trimestral": 3,
    "semestral": 4,
    "anual": 5
}


# ========== ENUMS ==========
class TransactionTypeEnum(str, Enum):
    INGRESO = "ingreso"
    GASTO = "gasto"


class FrequencyType(str, Enum):
    MENSUAL = "mensual"
    BIMENSUAL = "bimensual"
    TRIMESTRAL = "trimestral"
    SEMESTRAL = "semestral"
    ANUAL = "anual"


class CategoryType(str, Enum):
    VIVIENDA = "vivienda"
    SERVICIOS = "servicios"
    TRANSPORTE = "transporte"
    ALIMENTACION = "alimentacion"
    SALUD = "salud"
    ENTRETENIMIENTO = "entretenimiento"
    EDUCACION = "educacion"
    OTROS = "otros"


# ========== USER SCHEMAS ==========
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ========== CATEGORY SCHEMAS ==========
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#3498db", pattern="^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="📦", max_length=10)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class Category(CategoryBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== TRANSACTION SCHEMAS ==========
class TransactionBase(BaseModel):
    category_id: int
    amount: float = Field(..., gt=0)
    type: TransactionTypeEnum
    description: str = Field(..., min_length=1, max_length=500)
    date: date
    attachment_url: Optional[str] = None


class TransactionCreate(TransactionBase):
    @validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return round(v, 2)
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Convertir type de string a integer para la BD
        if 'type' in data and isinstance(data['type'], str):
            data['type'] = TRANSACTION_TYPE_REVERSE_MAP.get(data['type'], 1)
        return data


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionTypeEnum] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[date] = None
    attachment_url: Optional[str] = None


class Transaction(BaseModel):
    id: int
    user_id: int
    category_id: int
    amount: float
    type: TransactionTypeEnum
    description: str
    date: date
    attachment_url: Optional[str] = None
    created_at: datetime
    
    @validator('type', pre=True)
    def convert_type_from_int(cls, v):
        """Convertir type de integer (BD) a string (API)"""
        if isinstance(v, int):
            return TRANSACTION_TYPE_MAP.get(v, 'gasto')
        return v
    
    class Config:
        from_attributes = True


class TransactionWithCategory(Transaction):
    category: Category
    
    class Config:
        from_attributes = True


# ========== BUDGET SCHEMAS ==========
class BudgetBase(BaseModel):
    category_id: int
    amount: float = Field(..., gt=0)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)
    alert_threshold: float = Field(default=0.8, ge=0.1, le=1.0)


class BudgetCreate(BudgetBase):
    @validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('El monto del presupuesto debe ser positivo')
        return round(v, 2)


class BudgetUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    alert_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)


class Budget(BudgetBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BudgetWithCategory(Budget):
    category: Category
    spent: float = 0.0
    remaining: float = 0.0
    percentage_used: float = 0.0
    is_exceeded: bool = False
    
    class Config:
        from_attributes = True


# ========== REMINDER SCHEMAS ==========
class ReminderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    frequency: FrequencyType
    due_day: int = Field(..., ge=1, le=31)


class ReminderCreate(ReminderBase):
    @validator('amount')
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return round(v, 2)
    
    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Convertir frequency de string a integer para la BD
        if 'frequency' in data and isinstance(data['frequency'], str):
            data['frequency'] = FREQUENCY_REVERSE_MAP.get(data['frequency'], 1)
        return data


class ReminderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    frequency: Optional[FrequencyType] = None
    due_day: Optional[int] = Field(None, ge=1, le=31)
    is_active: Optional[bool] = None
    last_paid_date: Optional[date] = None


class Reminder(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    amount: float
    frequency: FrequencyType
    due_day: int
    is_active: bool
    last_paid_date: Optional[date] = None
    created_at: datetime
    
    @validator('frequency', pre=True)
    def convert_frequency_from_int(cls, v):
        """Convertir frequency de integer (BD) a string (API)"""
        if isinstance(v, int):
            return FREQUENCY_MAP.get(v, 'mensual')
        return v
    
    class Config:
        from_attributes = True


class ReminderWithStatus(Reminder):
    is_due: bool = False
    days_until_due: int = 0
    
    class Config:
        from_attributes = True


# ========== STATISTICS SCHEMAS ==========
class MonthlyStats(BaseModel):
    month: int
    year: int
    total_income: float
    total_expenses: float
    balance: float
    categories_expenses: dict


class YearlyStats(BaseModel):
    year: int
    total_income: float
    total_expenses: float
    balance: float
    monthly_data: List[MonthlyStats]


# ========== LEGACY SCHEMAS ==========
class BillBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    monto: float = Field(gt=0)
    categoria: CategoryType
    frecuencia: FrequencyType
    dia_vencimiento: int = Field(ge=1, le=31)
    activo: bool = True


class BillCreate(BillBase):
    pass


class BillUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    monto: Optional[float] = Field(None, gt=0)
    categoria: Optional[CategoryType] = None
    frecuencia: Optional[FrequencyType] = None
    dia_vencimiento: Optional[int] = Field(None, ge=1, le=31)
    activo: Optional[bool] = None


class Bill(BillBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Pago Schemas
class PagoBase(BaseModel):
    bill_id: int
    fecha_pago: date
    monto_pagado: float = Field(gt=0)
    notas: Optional[str] = None


class PagoCreate(PagoBase):
    pass


class Pago(PagoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Presupuesto Schemas
class PresupuestoBase(BaseModel):
    mes: int = Field(ge=1, le=12)
    anio: int = Field(ge=2020)
    categoria: CategoryType
    monto_limite: float = Field(gt=0)


class PresupuestoCreate(PresupuestoBase):
    pass


class Presupuesto(PresupuestoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Response Models
class BillWithPagos(Bill):
    pagos: List[Pago] = []

    class Config:
        from_attributes = True
