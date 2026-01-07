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
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search_text: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Transaction]:
    """Obtener transacciones con filtros avanzados"""
    query = db.query(models.Transaction).filter(models.Transaction.user_id == user_id)
    
    if category_id:
        query = query.filter(models.Transaction.category_id == category_id)
    
    if type:
        query = query.filter(models.Transaction.type == type)
    
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    if min_amount is not None:
        query = query.filter(models.Transaction.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(models.Transaction.amount <= max_amount)
    
    if search_text:
        query = query.filter(models.Transaction.description.ilike(f"%{search_text}%"))
    
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


# ========== NOTIFICATION & ALERTS ==========
def get_pending_reminders(db: Session, user_id: int, days_ahead: int = 7) -> List[dict]:
    """Obtener recordatorios próximos a vencer"""
    today = date.today()
    reminders = db.query(models.Reminder).filter(
        models.Reminder.user_id == user_id,
        models.Reminder.is_active == True
    ).all()
    
    pending = []
    for reminder in reminders:
        # Calcular próxima fecha de vencimiento
        current_month = today.month
        current_year = today.year
        
        # Si el día ya pasó este mes, calcular para el próximo periodo
        if today.day > reminder.due_day:
            if reminder.frequency == 1:  # mensual
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
        
        # Crear fecha de vencimiento
        try:
            due_date = date(current_year, current_month, reminder.due_day)
        except ValueError:
            # Si el día no existe en el mes (ej: 31 en febrero), usar último día del mes
            last_day = calendar.monthrange(current_year, current_month)[1]
            due_date = date(current_year, current_month, last_day)
        
        # Verificar si está dentro del rango de días
        days_until_due = (due_date - today).days
        
        if 0 <= days_until_due <= days_ahead:
            # Verificar si ya fue pagado este periodo
            if reminder.last_paid_date:
                # Si ya se pagó después de la fecha de vencimiento, no mostrar
                if reminder.last_paid_date >= due_date:
                    continue
            
            pending.append({
                "reminder_id": reminder.id,
                "name": reminder.name,
                "amount": reminder.amount,
                "due_date": due_date,
                "days_until_due": days_until_due,
                "frequency": models.FREQUENCY_MAP.get(reminder.frequency, "desconocido")
            })
    
    return sorted(pending, key=lambda x: x["days_until_due"])


def get_budget_alerts(db: Session, user_id: int, month: int, year: int) -> List[dict]:
    """Obtener alertas de presupuestos excedidos o cerca del límite"""
    budgets = db.query(models.Budget).filter(
        models.Budget.user_id == user_id,
        models.Budget.month == month,
        models.Budget.year == year
    ).all()
    
    alerts = []
    for budget in budgets:
        # Calcular gasto actual de la categoría en el mes
        total_spent = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.category_id == budget.category_id,
            models.Transaction.type == 2,  # gastos
            extract('month', models.Transaction.date) == month,
            extract('year', models.Transaction.date) == year
        ).scalar() or 0
        
        # Calcular porcentaje usado
        percentage_used = (total_spent / budget.amount * 100) if budget.amount > 0 else 0
        
        # Crear alerta si supera el threshold o el 100%
        if percentage_used >= (budget.alert_threshold * 100):
            category = db.query(models.Category).filter(models.Category.id == budget.category_id).first()
            
            status = "warning" if percentage_used < 100 else "danger"
            
            alerts.append({
                "budget_id": budget.id,
                "category_name": category.name if category else "Desconocido",
                "category_icon": category.icon if category else "📦",
                "budget_amount": budget.amount,
                "spent_amount": total_spent,
                "percentage_used": round(percentage_used, 1),
                "remaining": budget.amount - total_spent,
                "status": status
            })
    
    return sorted(alerts, key=lambda x: x["percentage_used"], reverse=True)


def mark_reminder_as_paid(
    db: Session,
    reminder_id: int,
    user_id: int,
    payment_date: date,
    category_id: int
) -> tuple[models.Reminder, models.Transaction]:
    """Marcar recordatorio como pagado y crear transacción automática"""
    # Obtener recordatorio
    reminder = db.query(models.Reminder).filter(
        models.Reminder.id == reminder_id,
        models.Reminder.user_id == user_id
    ).first()
    
    if not reminder:
        return None, None
    
    # Actualizar fecha de último pago
    reminder.last_paid_date = payment_date
    
    # Crear transacción automática
    transaction = models.Transaction(
        user_id=user_id,
        category_id=category_id,
        amount=reminder.amount,
        type=2,  # gasto
        description=f"Pago de {reminder.name} (automático desde recordatorio)",
        date=payment_date
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(reminder)
    db.refresh(transaction)
    
    return reminder, transaction


# ========== TRENDS & ANALYTICS ==========
def get_spending_trends(db: Session, user_id: int, months: int = 6) -> dict:
    """Obtener tendencias de gastos e ingresos de los últimos N meses"""
    today = date.today()
    trends_data = {
        "months": [],
        "income": [],
        "expenses": [],
        "balance": [],
        "categories_trend": {},
        "growth_rate": {
            "income": 0,
            "expenses": 0
        },
        "average": {
            "income": 0,
            "expenses": 0,
            "balance": 0
        },
        "prediction": {
            "next_month_income": 0,
            "next_month_expenses": 0,
            "next_month_balance": 0
        }
    }
    
    # Calcular datos para cada mes
    for i in range(months - 1, -1, -1):
        # Calcular mes y año
        target_month = today.month - i
        target_year = today.year
        
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        # Obtener transacciones del mes
        total_income = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.type == 1,  # ingreso
            extract('month', models.Transaction.date) == target_month,
            extract('year', models.Transaction.date) == target_year
        ).scalar() or 0
        
        total_expenses = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.type == 2,  # gasto
            extract('month', models.Transaction.date) == target_month,
            extract('year', models.Transaction.date) == target_year
        ).scalar() or 0
        
        balance = total_income - total_expenses
        
        # Agregar a listas
        month_name = calendar.month_name[target_month][:3]  # Ene, Feb, Mar...
        trends_data["months"].append(f"{month_name} {target_year}")
        trends_data["income"].append(float(total_income))
        trends_data["expenses"].append(float(total_expenses))
        trends_data["balance"].append(float(balance))
        
        # Gastos por categoría del mes
        categories = db.query(
            models.Category.name,
            func.sum(models.Transaction.amount).label('total')
        ).join(
            models.Transaction,
            models.Transaction.category_id == models.Category.id
        ).filter(
            models.Transaction.user_id == user_id,
            models.Transaction.type == 2,  # gastos
            extract('month', models.Transaction.date) == target_month,
            extract('year', models.Transaction.date) == target_year
        ).group_by(models.Category.name).all()
        
        for cat_name, cat_total in categories:
            if cat_name not in trends_data["categories_trend"]:
                trends_data["categories_trend"][cat_name] = []
            trends_data["categories_trend"][cat_name].append(float(cat_total))
    
    # Calcular promedios
    if trends_data["income"]:
        trends_data["average"]["income"] = sum(trends_data["income"]) / len(trends_data["income"])
        trends_data["average"]["expenses"] = sum(trends_data["expenses"]) / len(trends_data["expenses"])
        trends_data["average"]["balance"] = sum(trends_data["balance"]) / len(trends_data["balance"])
    
    # Calcular tasa de crecimiento (comparando primer y último mes)
    if len(trends_data["income"]) >= 2:
        if trends_data["income"][0] > 0:
            income_growth = ((trends_data["income"][-1] - trends_data["income"][0]) / trends_data["income"][0]) * 100
            trends_data["growth_rate"]["income"] = round(income_growth, 1)
        
        if trends_data["expenses"][0] > 0:
            expenses_growth = ((trends_data["expenses"][-1] - trends_data["expenses"][0]) / trends_data["expenses"][0]) * 100
            trends_data["growth_rate"]["expenses"] = round(expenses_growth, 1)
    
    # Predicción simple (promedio de últimos 3 meses)
    if len(trends_data["income"]) >= 3:
        recent_income = trends_data["income"][-3:]
        recent_expenses = trends_data["expenses"][-3:]
        
        trends_data["prediction"]["next_month_income"] = sum(recent_income) / len(recent_income)
        trends_data["prediction"]["next_month_expenses"] = sum(recent_expenses) / len(recent_expenses)
        trends_data["prediction"]["next_month_balance"] = (
            trends_data["prediction"]["next_month_income"] - 
            trends_data["prediction"]["next_month_expenses"]
        )
    
    return trends_data


# ========== IMPORT RULES CRUD ==========
def get_import_rules(db: Session, user_id: int) -> List[models.ImportRule]:
    """Obtener todas las reglas de importación del usuario"""
    return db.query(models.ImportRule).filter(
        models.ImportRule.user_id == user_id,
        models.ImportRule.is_active == True
    ).order_by(models.ImportRule.priority.desc()).all()


def create_import_rule(db: Session, rule: schemas.ImportRuleCreate, user_id: int) -> models.ImportRule:
    """Crear nueva regla de importación"""
    db_rule = models.ImportRule(
        **rule.model_dump(),
        user_id=user_id
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def update_import_rule(db: Session, rule_id: int, rule: schemas.ImportRuleUpdate, user_id: int) -> Optional[models.ImportRule]:
    """Actualizar regla de importación"""
    db_rule = db.query(models.ImportRule).filter(
        models.ImportRule.id == rule_id,
        models.ImportRule.user_id == user_id
    ).first()
    
    if not db_rule:
        return None
    
    for key, value in rule.model_dump(exclude_unset=True).items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    return db_rule


def delete_import_rule(db: Session, rule_id: int, user_id: int) -> bool:
    """Eliminar regla de importación"""
    db_rule = db.query(models.ImportRule).filter(
        models.ImportRule.id == rule_id,
        models.ImportRule.user_id == user_id
    ).first()
    
    if not db_rule:
        return False
    
    db.delete(db_rule)
    db.commit()
    return True


def apply_import_rules(db: Session, user_id: int, description: str) -> Optional[int]:
    """Aplicar reglas de importación para auto-categorizar basado en descripción"""
    # Obtener reglas ordenadas por prioridad
    rules = get_import_rules(db, user_id)
    
    # Buscar coincidencia
    description_lower = description.lower()
    for rule in rules:
        if rule.keyword.lower() in description_lower:
            return rule.category_id
    
    return None


# ========== PENDING TRANSACTIONS CRUD ==========
def get_pending_transactions(db: Session, user_id: int, batch_id: Optional[str] = None) -> List[models.PendingTransaction]:
    """Obtener transacciones pendientes de confirmación"""
    query = db.query(models.PendingTransaction).filter(
        models.PendingTransaction.user_id == user_id,
        models.PendingTransaction.is_confirmed == False
    )
    
    if batch_id:
        query = query.filter(models.PendingTransaction.import_batch_id == batch_id)
    
    return query.order_by(models.PendingTransaction.date.desc()).all()


def create_pending_transaction(
    db: Session, 
    transaction: schemas.PendingTransactionCreate, 
    user_id: int
) -> models.PendingTransaction:
    """Crear transacción pendiente"""
    db_transaction = models.PendingTransaction(
        **transaction.model_dump(),
        user_id=user_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def update_pending_transaction_category(
    db: Session, 
    transaction_id: int, 
    category_id: int, 
    user_id: int
) -> Optional[models.PendingTransaction]:
    """Actualizar categoría de transacción pendiente"""
    db_transaction = db.query(models.PendingTransaction).filter(
        models.PendingTransaction.id == transaction_id,
        models.PendingTransaction.user_id == user_id,
        models.PendingTransaction.is_confirmed == False
    ).first()
    
    if not db_transaction:
        return None
    
    db_transaction.category_id = category_id
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def confirm_pending_transactions(
    db: Session, 
    transaction_ids: List[int], 
    user_id: int,
    category_assignments: Optional[dict] = None
) -> int:
    """Confirmar transacciones pendientes y convertirlas en transacciones reales"""
    confirmed_count = 0
    
    for trans_id in transaction_ids:
        # Obtener transacción pendiente
        pending = db.query(models.PendingTransaction).filter(
            models.PendingTransaction.id == trans_id,
            models.PendingTransaction.user_id == user_id,
            models.PendingTransaction.is_confirmed == False
        ).first()
        
        if not pending:
            continue
        
        # Aplicar asignación de categoría si se proporcionó
        if category_assignments and str(trans_id) in category_assignments:
            pending.category_id = category_assignments[str(trans_id)]
        
        # Verificar que tenga categoría
        if not pending.category_id:
            continue
        
        # Crear transacción real
        transaction = models.Transaction(
            user_id=user_id,
            category_id=pending.category_id,
            amount=pending.amount,
            type=pending.type,
            description=pending.description,
            date=pending.date
        )
        
        db.add(transaction)
        
        # Marcar como confirmada
        pending.is_confirmed = True
        
        confirmed_count += 1
    
    db.commit()
    return confirmed_count


def delete_pending_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    """Eliminar transacción pendiente"""
    db_transaction = db.query(models.PendingTransaction).filter(
        models.PendingTransaction.id == transaction_id,
        models.PendingTransaction.user_id == user_id
    ).first()
    
    if not db_transaction:
        return False
    
    db.delete(db_transaction)
    db.commit()
    return True


def parse_bank_excel(file_content: bytes, user_id: int, db: Session) -> dict:
    """
    Parsear archivo Excel o CSV de banco y crear transacciones pendientes
    Formato esperado: Fecha | Descripción | Cargo/Abono
    """
    import pandas as pd
    from io import BytesIO
    import uuid
    
    # Generar ID de lote
    batch_id = str(uuid.uuid4())[:8]
    
    # Intentar leer como Excel primero, luego como CSV
    df = None
    try:
        df = pd.read_excel(BytesIO(file_content))
    except:
        # Intentar leer como CSV con diferentes configuraciones
        for sep in [';', ',', '\t']:  # Probar diferentes separadores
            for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                try:
                    # Reiniciar BytesIO para cada intento
                    content_io = BytesIO(file_content)
                    
                    # Leer todo el archivo para buscar la fila de encabezado
                    df_test = pd.read_csv(content_io, sep=sep, encoding=encoding, header=None)
                    
                    # Buscar fila que contenga "Fecha" (columna de encabezado típica)
                    header_row = None
                    for idx, row in df_test.iterrows():
                        row_str = ' '.join(str(cell).lower() for cell in row if pd.notna(cell))
                        if 'fecha' in row_str and ('descripción' in row_str or 'descripcion' in row_str or 'detalle' in row_str):
                            header_row = idx
                            break
                    
                    if header_row is not None:
                        # Leer nuevamente usando la fila correcta como encabezado
                        content_io = BytesIO(file_content)  # Reiniciar nuevamente
                        df = pd.read_csv(content_io, sep=sep, encoding=encoding, header=header_row)
                        break
                except:
                    continue
            
            if df is not None:
                break
    
    if df is None or df.empty:
        raise ValueError("No se pudo leer el archivo. Verifica el formato.")
    
    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Crear versión lowercase para comparación
    cols_lower = {col: col.lower() for col in df.columns}
    
    # Intentar identificar columnas (flexible para diferentes formatos)
    date_col = None
    desc_col = None
    cargo_col = None
    abono_col = None
    
    for col, col_lower in cols_lower.items():
        if any(word in col_lower for word in ['fecha', 'date']):
            date_col = col
        elif any(word in col_lower for word in ['descripción', 'descripcion', 'description', 'detalle', 'glosa']):
            desc_col = col
        elif any(word in col_lower for word in ['cargo', 'cargos', 'debe', 'egreso', 'gasto']):
            cargo_col = col
        elif any(word in col_lower for word in ['abono', 'abonos', 'haber', 'ingreso', 'deposito', 'depósito']):
            abono_col = col
    
    if not date_col:
        raise ValueError(f"No se encontró columna de fecha. Columnas disponibles: {', '.join(df.columns)}")
    
    if not desc_col:
        raise ValueError(f"No se encontró columna de descripción. Columnas disponibles: {', '.join(df.columns)}")
    
    if not cargo_col and not abono_col:
        raise ValueError(f"No se encontraron columnas de Cargo/Abono. Columnas disponibles: {', '.join(df.columns)}")
    
    total_imported = 0
    duplicates_skipped = 0
    auto_categorized = 0
    pending_transactions = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Extraer fecha
            fecha_raw = row[date_col]
            if pd.isna(fecha_raw):
                continue
            
            # Intentar parsear fecha con diferentes formatos
            fecha = None
            fecha_str = str(fecha_raw).strip()
            
            # Mapeo de meses en español
            meses_es = {
                'ene': '01', 'enero': '01',
                'feb': '02', 'febrero': '02',
                'mar': '03', 'marzo': '03',
                'abr': '04', 'abril': '04',
                'may': '05', 'mayo': '05',
                'jun': '06', 'junio': '06',
                'jul': '07', 'julio': '07',
                'ago': '08', 'agosto': '08',
                'sep': '09', 'septiembre': '09',
                'oct': '10', 'octubre': '10',
                'nov': '11', 'noviembre': '11',
                'dic': '12', 'diciembre': '12'
            }
            
            # Si tiene formato "02/Ene" o similar
            if '/' in fecha_str and any(mes in fecha_str.lower() for mes in meses_es.keys()):
                from datetime import datetime
                parts = fecha_str.split('/')
                if len(parts) == 2:
                    dia = parts[0].zfill(2)
                    mes_str = parts[1].lower()
                    mes = meses_es.get(mes_str, '01')
                    
                    # Determinar año basado en el mes
                    # Si es diciembre y estamos en enero, es año anterior
                    # Si es enero y estamos en diciembre, es año siguiente
                    now = datetime.now()
                    anio = now.year
                    
                    if mes == '12' and now.month == 1:
                        anio = now.year - 1
                    elif mes == '01' and now.month == 12:
                        anio = now.year + 1
                    
                    fecha_str_formatted = f"{anio}-{mes}-{dia}"
                    try:
                        fecha = datetime.strptime(fecha_str_formatted, "%Y-%m-%d").date()
                    except:
                        pass
            
            # Si no se pudo parsear con el formato especial, intentar pandas
            if not fecha:
                try:
                    fecha = pd.to_datetime(fecha_raw, errors='coerce').date()
                except:
                    pass
            
            if not fecha or pd.isna(fecha):
                errors.append(f"Fila {idx+2}: Fecha inválida '{fecha_raw}'")
                continue
            
            # Extraer descripción
            descripcion = str(row[desc_col]).strip()
            if descripcion == 'nan' or not descripcion or descripcion == '':
                continue
            
            # Ignorar filas que contienen totales o notas
            if any(word in descripcion.lower() for word in ['subtotal', 'notas:', 'información referencial']):
                continue
            
            # Determinar monto y tipo - manejar valores vacíos, NaN, y strings vacíos
            cargo = 0
            abono = 0
            
            if cargo_col:
                cargo_val = row[cargo_col]
                if pd.notna(cargo_val) and str(cargo_val).strip() != '':
                    try:
                        # Eliminar separadores de miles (punto) y convertir
                        cargo_str = str(cargo_val).replace('.', '').replace(',', '.').strip()
                        if cargo_str:
                            cargo = float(cargo_str)
                    except:
                        pass
            
            if abono_col:
                abono_val = row[abono_col]
                if pd.notna(abono_val) and str(abono_val).strip() != '':
                    try:
                        # Eliminar separadores de miles (punto) y convertir
                        abono_str = str(abono_val).replace('.', '').replace(',', '.').strip()
                        if abono_str:
                            abono = float(abono_str)
                    except:
                        pass
            
            # Determinar tipo de transacción
            if cargo > 0:
                amount = cargo
                trans_type = 2  # gasto
            elif abono > 0:
                amount = abono
                trans_type = 1  # ingreso
            else:
                # Ambos están vacíos o en cero, saltar
                continue
            
            # Verificar si ya existe una transacción con los mismos datos (evitar duplicados)
            descripcion_corta = descripcion[:200]
            
            # Buscar en transacciones confirmadas
            existe_confirmada = db.query(models.Transaction).filter(
                models.Transaction.user_id == user_id,
                models.Transaction.date == fecha,
                models.Transaction.amount == amount,
                models.Transaction.description == descripcion_corta
            ).first()
            
            # Buscar en transacciones pendientes
            existe_pendiente = db.query(models.PendingTransaction).filter(
                models.PendingTransaction.user_id == user_id,
                models.PendingTransaction.date == fecha,
                models.PendingTransaction.amount == amount,
                models.PendingTransaction.description == descripcion_corta
            ).first()
            
            # Si ya existe, saltar esta transacción
            if existe_confirmada or existe_pendiente:
                duplicates_skipped += 1
                continue
            
            # Intentar auto-categorizar
            category_id = apply_import_rules(db, user_id, descripcion)
            auto_cat = category_id is not None
            
            if auto_cat:
                auto_categorized += 1
            
            # Crear transacción pendiente
            pending = models.PendingTransaction(
                user_id=user_id,
                category_id=category_id,
                amount=amount,
                type=trans_type,
                description=descripcion_corta,
                raw_description=descripcion,
                date=fecha,
                auto_categorized=auto_cat,
                import_batch_id=batch_id
            )
            
            db.add(pending)
            pending_transactions.append(pending)
            total_imported += 1
            
        except Exception as e:
            # Ignorar filas con errores
            continue
    
    db.commit()
    
    # Refrescar para obtener IDs
    for p in pending_transactions:
        db.refresh(p)
    
    # Convertir objetos SQLAlchemy a dicts para serialización
    from . import schemas
    pending_dicts = [schemas.PendingTransaction.model_validate(p) for p in pending_transactions]
    
    return {
        "total_imported": total_imported,
        "auto_categorized": auto_categorized,
        "needs_review": total_imported - auto_categorized,
        "duplicates_skipped": duplicates_skipped,
        "batch_id": batch_id,
        "pending_transactions": pending_dicts
    }
