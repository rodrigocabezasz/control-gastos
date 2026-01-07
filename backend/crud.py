"""
Operaciones CRUD (Create, Read, Update, Delete) para todos los modelos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract, func
from typing import List, Optional
from datetime import date, datetime, timedelta
from . import models, schemas
from .auth import get_password_hash
import calendar


# ========== USER CRUD ==========
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Obtener usuario por email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Obtener usuario por username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Obtener usuario por ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Crear nuevo usuario"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Crear categorías por defecto
    default_categories = [
        {"name": "Vivienda", "icon": "🏠", "color": "#e74c3c"},
        {"name": "Servicios", "icon": "⚡", "color": "#3498db"},
        {"name": "Transporte", "icon": "🚗", "color": "#9b59b6"},
        {"name": "Alimentación", "icon": "🍔", "color": "#e67e22"},
        {"name": "Salud", "icon": "🏥", "color": "#1abc9c"},
        {"name": "Entretenimiento", "icon": "🎮", "color": "#f39c12"},
        {"name": "Educación", "icon": "📚", "color": "#2ecc71"},
        {"name": "Otros", "icon": "📦", "color": "#95a5a6"},
    ]
    
    for cat_data in default_categories:
        db_category = models.Category(
            user_id=db_user.id,
            **cat_data
        )
        db.add(db_category)
    
    db.commit()
    return db_user


def update_user(db: Session, user_id: int, user: schemas.UserUpdate) -> Optional[models.User]:
    """Actualizar usuario"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


# ========== CATEGORY CRUD ==========
def get_categories(db: Session, user_id: int, include_inactive: bool = False) -> List[models.Category]:
    """Obtener categorías del usuario"""
    query = db.query(models.Category).filter(models.Category.user_id == user_id)
    if not include_inactive:
        query = query.filter(models.Category.is_active == True)
    return query.all()


def get_category(db: Session, category_id: int, user_id: int) -> Optional[models.Category]:
    """Obtener categoría por ID (verificando que pertenece al usuario)"""
    return db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == user_id
    ).first()


def create_category(db: Session, category: schemas.CategoryCreate, user_id: int) -> models.Category:
    """Crear nueva categoría"""
    db_category = models.Category(
        **category.model_dump(),
        user_id=user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: schemas.CategoryUpdate, user_id: int) -> Optional[models.Category]:
    """Actualizar categoría"""
    db_category = get_category(db, category_id, user_id)
    if not db_category:
        return None
    
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int, user_id: int) -> bool:
    """Eliminar categoría (soft delete)"""
    db_category = get_category(db, category_id, user_id)
    if not db_category:
        return False
    
    # Verificar si tiene transacciones o presupuestos asociados
    has_transactions = db.query(models.Transaction).filter(
        models.Transaction.category_id == category_id
    ).first() is not None
    
    if has_transactions:
        # Soft delete: marcar como inactiva
        db_category.is_active = False
        db.commit()
    else:
        # Hard delete si no tiene datos asociados
        db.delete(db_category)
        db.commit()
    
    return True


# ========== TRANSACTION CRUD ==========
def get_transactions(
    db: Session,
    user_id: int,
    category_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Transaction]:
    """Obtener transacciones con filtros"""
    query = db.query(models.Transaction).filter(models.Transaction.user_id == user_id)
    
    if category_id:
        query = query.filter(models.Transaction.category_id == category_id)
    
    if type:
        query = query.filter(models.Transaction.type == type)
    
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    return query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()


def get_transaction(db: Session, transaction_id: int, user_id: int) -> Optional[models.Transaction]:
    """Obtener transacción por ID"""
    return db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.user_id == user_id
    ).first()


def create_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int) -> models.Transaction:
    """Crear nueva transacción"""
    db_transaction = models.Transaction(
        **transaction.model_dump(),
        user_id=user_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def update_transaction(db: Session, transaction_id: int, transaction: schemas.TransactionUpdate, user_id: int) -> Optional[models.Transaction]:
    """Actualizar transacción"""
    db_transaction = get_transaction(db, transaction_id, user_id)
    if not db_transaction:
        return None
    
    update_data = transaction.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def delete_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    """Eliminar transacción"""
    db_transaction = get_transaction(db, transaction_id, user_id)
    if not db_transaction:
        return False
    
    db.delete(db_transaction)
    db.commit()
    return True


# ========== BUDGET CRUD ==========
def get_budgets(db: Session, user_id: int, month: Optional[int] = None, year: Optional[int] = None) -> List[models.Budget]:
    """Obtener presupuestos del usuario"""
    query = db.query(models.Budget).filter(models.Budget.user_id == user_id)
    
    if month:
        query = query.filter(models.Budget.month == month)
    if year:
        query = query.filter(models.Budget.year == year)
    
    return query.all()


def get_budget(db: Session, budget_id: int, user_id: int) -> Optional[models.Budget]:
    """Obtener presupuesto por ID"""
    return db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == user_id
    ).first()


def get_budget_by_category_month(db: Session, user_id: int, category_id: int, month: int, year: int) -> Optional[models.Budget]:
    """Obtener presupuesto por categoría y mes"""
    return db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.category_id == category_id,
        models.Budget.month == month,
        models.Budget.year == year
    ).first()


def create_budget(db: Session, budget: schemas.BudgetCreate, user_id: int) -> models.Budget:
    """Crear nuevo presupuesto"""
    # Verificar si ya existe para esta categoría y mes
    existing = get_budget_by_category_month(db, user_id, budget.category_id, budget.month, budget.year)
    if existing:
        raise ValueError("Ya existe un presupuesto para esta categoría y mes")
    
    db_budget = models.Budget(
        **budget.model_dump(),
        user_id=user_id
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


def update_budget(db: Session, budget_id: int, budget: schemas.BudgetUpdate, user_id: int) -> Optional[models.Budget]:
    """Actualizar presupuesto"""
    db_budget = get_budget(db, budget_id, user_id)
    if not db_budget:
        return None
    
    update_data = budget.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_budget, key, value)
    
    db.commit()
    db.refresh(db_budget)
    return db_budget


def delete_budget(db: Session, budget_id: int, user_id: int) -> bool:
    """Eliminar presupuesto"""
    db_budget = get_budget(db, budget_id, user_id)
    if not db_budget:
        return False
    
    db.delete(db_budget)
    db.commit()
    return True


def get_budget_status(db: Session, budget_id: int, user_id: int) -> Optional[dict]:
    """Obtener estado del presupuesto con gasto actual"""
    db_budget = get_budget(db, budget_id, user_id)
    if not db_budget:
        return None
    
    # Calcular gasto total en la categoría para el mes
    start_date = date(db_budget.year, db_budget.month, 1)
    last_day = calendar.monthrange(db_budget.year, db_budget.month)[1]
    end_date = date(db_budget.year, db_budget.month, last_day)
    
    spent = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.category_id == db_budget.category_id,
        models.Transaction.type == 2,  # 2 = gasto
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).scalar() or 0.0
    
    remaining = db_budget.amount - spent
    percentage_used = (spent / db_budget.amount * 100) if db_budget.amount > 0 else 0
    is_exceeded = spent > db_budget.amount
    
    return {
        "budget": db_budget,
        "spent": round(spent, 2),
        "remaining": round(remaining, 2),
        "percentage_used": round(percentage_used, 2),
        "is_exceeded": is_exceeded
    }


# ========== REMINDER CRUD ==========
def get_reminders(db: Session, user_id: int, active_only: bool = True) -> List[models.Reminder]:
    """Obtener recordatorios del usuario"""
    query = db.query(models.Reminder).filter(models.Reminder.user_id == user_id)
    if active_only:
        query = query.filter(models.Reminder.is_active == True)
    return query.all()


def get_reminder(db: Session, reminder_id: int, user_id: int) -> Optional[models.Reminder]:
    """Obtener recordatorio por ID"""
    return db.query(models.Reminder).filter(
        models.Reminder.id == reminder_id,
        models.Reminder.user_id == user_id
    ).first()


def create_reminder(db: Session, reminder: schemas.ReminderCreate, user_id: int) -> models.Reminder:
    """Crear nuevo recordatorio"""
    db_reminder = models.Reminder(
        **reminder.model_dump(),
        user_id=user_id
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


def update_reminder(db: Session, reminder_id: int, reminder: schemas.ReminderUpdate, user_id: int) -> Optional[models.Reminder]:
    """Actualizar recordatorio"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    if not db_reminder:
        return None
    
    update_data = reminder.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reminder, key, value)
    
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


def delete_reminder(db: Session, reminder_id: int, user_id: int) -> bool:
    """Eliminar recordatorio"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    if not db_reminder:
        return False
    
    db.delete(db_reminder)
    db.commit()
    return True


def mark_reminder_as_paid(db: Session, reminder_id: int, user_id: int, paid_date: date) -> Optional[models.Reminder]:
    """Marcar recordatorio como pagado"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    if not db_reminder:
        return None
    
    db_reminder.last_paid_date = paid_date
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


def get_due_reminders(db: Session, user_id: int, reference_date: date = None) -> List[dict]:
    """Obtener recordatorios próximos a vencer o vencidos"""
    if reference_date is None:
        reference_date = date.today()
    
    reminders = get_reminders(db, user_id, active_only=True)
    due_reminders = []
    
    for reminder in reminders:
        # Calcular próximo vencimiento
        try:
            due_date = date(reference_date.year, reference_date.month, reminder.due_day)
        except ValueError:
            # Día inválido para el mes actual
            last_day = calendar.monthrange(reference_date.year, reference_date.month)[1]
            due_date = date(reference_date.year, reference_date.month, min(reminder.due_day, last_day))
        
        # Si ya pasó este mes, calcular para el próximo mes
        if due_date < reference_date:
            next_month = reference_date.month + 1 if reference_date.month < 12 else 1
            next_year = reference_date.year if reference_date.month < 12 else reference_date.year + 1
            try:
                due_date = date(next_year, next_month, reminder.due_day)
            except ValueError:
                last_day = calendar.monthrange(next_year, next_month)[1]
                due_date = date(next_year, next_month, min(reminder.due_day, last_day))
        
        # Verificar si ya se pagó este mes
        already_paid = False
        if reminder.last_paid_date:
            already_paid = (
                reminder.last_paid_date.year == reference_date.year and
                reminder.last_paid_date.month == reference_date.month
            )
        
        days_until_due = (due_date - reference_date).days
        is_due = days_until_due <= 5 and not already_paid  # Alertar 5 días antes
        
        due_reminders.append({
            "reminder": reminder,
            "due_date": due_date,
            "days_until_due": days_until_due,
            "is_due": is_due,
            "already_paid": already_paid
        })
    
    # Ordenar por días hasta vencimiento
    due_reminders.sort(key=lambda x: x["days_until_due"])
    
    return due_reminders


# ========== STATISTICS ==========
def get_monthly_summary(db: Session, user_id: int, month: int, year: int) -> dict:
    """Obtener resumen mensual de ingresos y gastos"""
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # Total ingresos
    total_income = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == 1,  # 1 = ingreso
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).scalar() or 0.0
    
    # Total gastos
    total_expenses = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == 2,  # 2 = gasto
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).scalar() or 0.0
    
    # Gastos por categoría
    categories_expenses = db.query(
        models.Category.name,
        models.Category.icon,
        models.Category.color,
        func.sum(models.Transaction.amount).label('total')
    ).join(
        models.Transaction,
        models.Transaction.category_id == models.Category.id
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.type == 2,  # 2 = gasto
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).group_by(
        models.Category.id,
        models.Category.name,
        models.Category.icon,
        models.Category.color
    ).all()
    
    # Convertir lista a diccionario
    categories_dict = {}
    for cat in categories_expenses:
        categories_dict[cat.name] = {
            "icon": cat.icon,
            "color": cat.color,
            "total": round(cat.total, 2)
        }
    
    return {
        "month": month,
        "year": year,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "balance": round(total_income - total_expenses, 2),
        "categories_expenses": categories_dict
    }


# ========== LEGACY CRUD (mantener compatibilidad) ==========
def create_bill(db: Session, bill: schemas.BillCreate) -> models.Bill:
    """Crear una nueva bill/factura"""
    db_bill = models.Bill(**bill.model_dump())
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


def get_bills(db: Session, skip: int = 0, limit: int = 100, activo: Optional[bool] = None) -> List[models.Bill]:
    """Obtener lista de bills"""
    query = db.query(models.Bill)
    if activo is not None:
        query = query.filter(models.Bill.activo == activo)
    return query.offset(skip).limit(limit).all()


def get_bill(db: Session, bill_id: int) -> Optional[models.Bill]:
    """Obtener una bill por ID"""
    return db.query(models.Bill).filter(models.Bill.id == bill_id).first()


def update_bill(db: Session, bill_id: int, bill: schemas.BillUpdate) -> Optional[models.Bill]:
    """Actualizar una bill"""
    db_bill = get_bill(db, bill_id)
    if not db_bill:
        return None
    
    update_data = bill.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_bill, key, value)
    
    db.commit()
    db.refresh(db_bill)
    return db_bill


def delete_bill(db: Session, bill_id: int) -> bool:
    """Eliminar una bill"""
    db_bill = get_bill(db, bill_id)
    if not db_bill:
        return False
    db.delete(db_bill)
    db.commit()
    return True


def create_pago(db: Session, pago: schemas.PagoCreate) -> models.Pago:
    """Registrar un pago"""
    db_pago = models.Pago(**pago.model_dump())
    db.add(db_pago)
    db.commit()
    db.refresh(db_pago)
    return db_pago


def get_pagos(db: Session, bill_id: Optional[int] = None, mes: Optional[int] = None, anio: Optional[int] = None) -> List[models.Pago]:
    """Obtener pagos con filtros opcionales"""
    query = db.query(models.Pago)
    
    if bill_id:
        query = query.filter(models.Pago.bill_id == bill_id)
    
    if mes and anio:
        query = query.filter(
            and_(
                extract('month', models.Pago.fecha_pago) == mes,
                extract('year', models.Pago.fecha_pago) == anio
            )
        )
    elif anio:
        query = query.filter(extract('year', models.Pago.fecha_pago) == anio)
    
    return query.all()


def get_pago(db: Session, pago_id: int) -> Optional[models.Pago]:
    """Obtener un pago por ID"""
    return db.query(models.Pago).filter(models.Pago.id == pago_id).first()


def create_presupuesto(db: Session, presupuesto: schemas.PresupuestoCreate) -> models.Presupuesto:
    """Crear un presupuesto mensual"""
    db_presupuesto = models.Presupuesto(**presupuesto.model_dump())
    db.add(db_presupuesto)
    db.commit()
    db.refresh(db_presupuesto)
    return db_presupuesto


def get_presupuestos(db: Session, mes: Optional[int] = None, anio: Optional[int] = None) -> List[models.Presupuesto]:
    """Obtener presupuestos con filtros"""
    query = db.query(models.Presupuesto)
    
    if mes:
        query = query.filter(models.Presupuesto.mes == mes)
    if anio:
        query = query.filter(models.Presupuesto.anio == anio)
    
    return query.all()
