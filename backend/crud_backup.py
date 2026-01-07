from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
from . import models, schemas


# ========== BILLS ==========
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


# ========== PAGOS ==========
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


# ========== PRESUPUESTOS ==========
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


# ========== UTILIDADES ==========
def get_bills_pendientes(db: Session, fecha: date) -> List[dict]:
    """Obtener bills pendientes de pago para una fecha"""
    bills_activas = get_bills(db, activo=True)
    pendientes = []
    
    mes_actual = fecha.month
    anio_actual = fecha.year
    
    for bill in bills_activas:
        # Verificar si ya se pagó este mes
        pagos_mes = db.query(models.Pago).filter(
            and_(
                models.Pago.bill_id == bill.id,
                extract('month', models.Pago.fecha_pago) == mes_actual,
                extract('year', models.Pago.fecha_pago) == anio_actual
            )
        ).first()
        
        if not pagos_mes:
            # Calcular días hasta vencimiento
            try:
                fecha_vencimiento = date(anio_actual, mes_actual, bill.dia_vencimiento)
            except ValueError:
                # Si el día no existe en el mes (ej: 31 en febrero), usar último día del mes
                import calendar
                ultimo_dia = calendar.monthrange(anio_actual, mes_actual)[1]
                fecha_vencimiento = date(anio_actual, mes_actual, min(bill.dia_vencimiento, ultimo_dia))
            
            dias_hasta_vencimiento = (fecha_vencimiento - fecha).days
            
            pendientes.append({
                "bill": bill,
                "fecha_vencimiento": fecha_vencimiento,
                "dias_hasta_vencimiento": dias_hasta_vencimiento,
                "vencido": dias_hasta_vencimiento < 0
            })
    
    return pendientes


def get_gastos_por_categoria(db: Session, mes: int, anio: int) -> dict:
    """Obtener total de gastos por categoría en un mes"""
    pagos = get_pagos(db, mes=mes, anio=anio)
    
    gastos_categoria = {}
    for pago in pagos:
        categoria = pago.bill.categoria.value
        if categoria not in gastos_categoria:
            gastos_categoria[categoria] = 0
        gastos_categoria[categoria] += pago.monto_pagado
    
    return gastos_categoria
