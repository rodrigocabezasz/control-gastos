"""
API FastAPI - Control de Gastos Personales
Sistema completo con autenticación JWT, gestión de transacciones, presupuestos y recordatorios
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from . import models, schemas, crud
from .database import engine, get_db
from .auth import authenticate_user, create_access_token, get_current_user

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Control de Gastos API",
    description="API completa para gestión de gastos personales con autenticación JWT",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "API de Control de Gastos v2.0",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "categories": "/categories",
            "transactions": "/transactions",
            "budgets": "/budgets",
            "reminders": "/reminders",
            "stats": "/stats"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# ========== AUTHENTICATION ==========
@app.post("/auth/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    # Verificar si el email ya existe
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Verificar si el username ya existe
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Crear usuario
    return crud.create_user(db=db, user=user)


@app.post("/auth/login", response_model=schemas.Token, tags=["Authentication"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login y obtener token JWT"""
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=schemas.User.from_orm(user)
    )


@app.get("/auth/me", response_model=schemas.User, tags=["Authentication"])
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user


# ========== USERS ==========
@app.get("/users/me", response_model=schemas.User, tags=["Users"])
def read_user_me(current_user: models.User = Depends(get_current_user)):
    """Obtener perfil del usuario actual"""
    return current_user


@app.put("/users/me", response_model=schemas.User, tags=["Users"])
def update_user_me(
    user: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario actual"""
    updated_user = crud.update_user(db, current_user.id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return updated_user


# ========== CATEGORIES ==========
@app.get("/categories", response_model=List[schemas.Category], tags=["Categories"])
def get_categories(
    include_inactive: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las categorías del usuario"""
    return crud.get_categories(db, current_user.id, include_inactive)


@app.post("/categories", response_model=schemas.Category, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(
    category: schemas.CategoryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva categoría personalizada"""
    return crud.create_category(db, category, current_user.id)


@app.get("/categories/{category_id}", response_model=schemas.Category, tags=["Categories"])
def get_category(
    category_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener categoría por ID"""
    category = crud.get_category(db, category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@app.put("/categories/{category_id}", response_model=schemas.Category, tags=["Categories"])
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar categoría"""
    updated = crud.update_category(db, category_id, category, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return updated


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"])
def delete_category(
    category_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar categoría"""
    success = crud.delete_category(db, category_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


# ========== TRANSACTIONS ==========
@app.get("/transactions", response_model=List[schemas.Transaction], tags=["Transactions"])
def get_transactions(
    category_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener transacciones con filtros opcionales"""
    return crud.get_transactions(
        db,
        current_user.id,
        category_id=category_id,
        type=type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )


@app.post("/transactions", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED, tags=["Transactions"])
def create_transaction(
    transaction: schemas.TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva transacción (ingreso o gasto)"""
    # Verificar que la categoría pertenece al usuario
    category = crud.get_category(db, transaction.category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    return crud.create_transaction(db, transaction, current_user.id)


@app.get("/transactions/{transaction_id}", response_model=schemas.Transaction, tags=["Transactions"])
def get_transaction(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener transacción por ID"""
    transaction = crud.get_transaction(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return transaction


@app.put("/transactions/{transaction_id}", response_model=schemas.Transaction, tags=["Transactions"])
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar transacción"""
    updated = crud.update_transaction(db, transaction_id, transaction, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return updated


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Transactions"])
def delete_transaction(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar transacción"""
    success = crud.delete_transaction(db, transaction_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")


# ========== BUDGETS ==========
@app.get("/budgets", response_model=List[schemas.Budget], tags=["Budgets"])
def get_budgets(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener presupuestos del usuario"""
    return crud.get_budgets(db, current_user.id, month, year)


@app.post("/budgets", response_model=schemas.Budget, status_code=status.HTTP_201_CREATED, tags=["Budgets"])
def create_budget(
    budget: schemas.BudgetCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo presupuesto mensual"""
    # Verificar que la categoría existe
    category = crud.get_category(db, budget.category_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    try:
        return crud.create_budget(db, budget, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/budgets/{budget_id}", response_model=schemas.BudgetWithCategory, tags=["Budgets"])
def get_budget(
    budget_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener presupuesto por ID con estado actual"""
    budget_status = crud.get_budget_status(db, budget_id, current_user.id)
    if not budget_status:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    # Obtener categoría
    category = crud.get_category(db, budget_status["budget"].category_id, current_user.id)
    
    return schemas.BudgetWithCategory(
        **budget_status["budget"].__dict__,
        category=category,
        spent=budget_status["spent"],
        remaining=budget_status["remaining"],
        percentage_used=budget_status["percentage_used"],
        is_exceeded=budget_status["is_exceeded"]
    )


@app.put("/budgets/{budget_id}", response_model=schemas.Budget, tags=["Budgets"])
def update_budget(
    budget_id: int,
    budget: schemas.BudgetUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar presupuesto"""
    updated = crud.update_budget(db, budget_id, budget, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return updated


@app.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Budgets"])
def delete_budget(
    budget_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar presupuesto"""
    success = crud.delete_budget(db, budget_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")


# ========== REMINDERS ==========
@app.get("/reminders", response_model=List[schemas.Reminder], tags=["Reminders"])
def get_reminders(
    active_only: bool = True,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener recordatorios del usuario"""
    return crud.get_reminders(db, current_user.id, active_only)


@app.get("/reminders/due", response_model=List[schemas.ReminderWithStatus], tags=["Reminders"])
def get_due_reminders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener recordatorios próximos a vencer"""
    due_reminders = crud.get_due_reminders(db, current_user.id)
    
    result = []
    for item in due_reminders:
        reminder_data = schemas.ReminderWithStatus(
            **item["reminder"].__dict__,
            is_due=item["is_due"],
            days_until_due=item["days_until_due"]
        )
        result.append(reminder_data)
    
    return result


@app.post("/reminders", response_model=schemas.Reminder, status_code=status.HTTP_201_CREATED, tags=["Reminders"])
def create_reminder(
    reminder: schemas.ReminderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo recordatorio de pago"""
    return crud.create_reminder(db, reminder, current_user.id)


@app.get("/reminders/{reminder_id}", response_model=schemas.Reminder, tags=["Reminders"])
def get_reminder(
    reminder_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener recordatorio por ID"""
    reminder = crud.get_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    return reminder


@app.put("/reminders/{reminder_id}", response_model=schemas.Reminder, tags=["Reminders"])
def update_reminder(
    reminder_id: int,
    reminder: schemas.ReminderUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar recordatorio"""
    updated = crud.update_reminder(db, reminder_id, reminder, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    return updated


@app.post("/reminders/{reminder_id}/mark-paid", response_model=schemas.Reminder, tags=["Reminders"])
def mark_reminder_paid(
    reminder_id: int,
    paid_date: date = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar recordatorio como pagado"""
    if paid_date is None:
        paid_date = date.today()
    
    updated = crud.mark_reminder_as_paid(db, reminder_id, current_user.id, paid_date)
    if not updated:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")
    return updated


@app.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Reminders"])
def delete_reminder(
    reminder_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar recordatorio"""
    success = crud.delete_reminder(db, reminder_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")


# ========== STATISTICS ==========
@app.get("/stats/monthly", response_model=schemas.MonthlyStats, tags=["Statistics"])
def get_monthly_stats(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas mensuales"""
    return crud.get_monthly_summary(db, current_user.id, month, year)


@app.get("/stats/current-month", response_model=schemas.MonthlyStats, tags=["Statistics"])
def get_current_month_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas del mes actual"""
    today = date.today()
    return crud.get_monthly_summary(db, current_user.id, today.month, today.year)


# ========== LEGACY ENDPOINTS (mantener compatibilidad) ==========
@app.post("/bills", response_model=schemas.Bill, status_code=201, tags=["Legacy"])
def crear_bill(bill: schemas.BillCreate, db: Session = Depends(get_db)):
    """Crear una nueva bill/factura recurrente"""
    return crud.create_bill(db, bill)


@app.get("/bills", response_model=List[schemas.Bill], tags=["Legacy"])
def listar_bills(activo: Optional[bool] = None, db: Session = Depends(get_db)):
    """Obtener lista de bills"""
    return crud.get_bills(db, activo=activo)


@app.get("/bills/{bill_id}", response_model=schemas.Bill, tags=["Legacy"])
def obtener_bill(bill_id: int, db: Session = Depends(get_db)):
    """Obtener una bill por ID"""
    bill = crud.get_bill(db, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill no encontrada")
    return bill


@app.put("/bills/{bill_id}", response_model=schemas.Bill, tags=["Legacy"])
def actualizar_bill(bill_id: int, bill: schemas.BillUpdate, db: Session = Depends(get_db)):
    """Actualizar una bill"""
    updated = crud.update_bill(db, bill_id, bill)
    if not updated:
        raise HTTPException(status_code=404, detail="Bill no encontrada")
    return updated


@app.delete("/bills/{bill_id}", status_code=204, tags=["Legacy"])
def eliminar_bill(bill_id: int, db: Session = Depends(get_db)):
    """Eliminar una bill"""
    success = crud.delete_bill(db, bill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bill no encontrada")


@app.post("/pagos", response_model=schemas.Pago, status_code=201, tags=["Legacy"])
def crear_pago(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo pago"""
    return crud.create_pago(db, pago)


@app.get("/pagos", response_model=List[schemas.Pago], tags=["Legacy"])
def listar_pagos(
    bill_id: Optional[int] = None,
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2020),
    db: Session = Depends(get_db)
):
    """Obtener pagos con filtros"""
    return crud.get_pagos(db, bill_id=bill_id, mes=mes, anio=anio)


@app.post("/presupuestos", response_model=schemas.Presupuesto, status_code=201, tags=["Legacy"])
def crear_presupuesto(presupuesto: schemas.PresupuestoCreate, db: Session = Depends(get_db)):
    """Crear presupuesto mensual"""
    return crud.create_presupuesto(db, presupuesto)


@app.get("/presupuestos", response_model=List[schemas.Presupuesto], tags=["Legacy"])
def listar_presupuestos(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2020),
    db: Session = Depends(get_db)
):
    """Obtener presupuestos con filtros"""
    return crud.get_presupuestos(db, mes=mes, anio=anio)
