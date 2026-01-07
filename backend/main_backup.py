from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from . import models, schemas, crud
from .database import engine, get_db

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Control de Gastos API",
    description="API para gestión de gastos personales, bills y presupuestos",
    version="1.0.0"
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
    """Endpoint raíz"""
    return {
        "message": "API de Control de Gastos",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "bills": "/bills",
            "pagos": "/pagos",
            "presupuestos": "/presupuestos"
        }
    }


# ========== BILLS ENDPOINTS ==========
@app.post("/bills", response_model=schemas.Bill, status_code=201)
def crear_bill(bill: schemas.BillCreate, db: Session = Depends(get_db)):
    """Crear una nueva bill/factura recurrente"""
    return crud.create_bill(db, bill)


@app.get("/bills", response_model=List[schemas.Bill])
def listar_bills(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Listar todas las bills"""
    return crud.get_bills(db, skip=skip, limit=limit, activo=activo)


@app.get("/bills/{bill_id}", response_model=schemas.BillWithPagos)
def obtener_bill(bill_id: int, db: Session = Depends(get_db)):
    """Obtener una bill específica con sus pagos"""
    bill = crud.get_bill(db, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill no encontrada")
    return bill


@app.put("/bills/{bill_id}", response_model=schemas.Bill)
def actualizar_bill(bill_id: int, bill: schemas.BillUpdate, db: Session = Depends(get_db)):
    """Actualizar una bill"""
    updated_bill = crud.update_bill(db, bill_id, bill)
    if not updated_bill:
        raise HTTPException(status_code=404, detail="Bill no encontrada")
    return updated_bill


@app.delete("/bills/{bill_id}", status_code=204)
def eliminar_bill(bill_id: int, db: Session = Depends(get_db)):
    """Eliminar una bill"""
    if not crud.delete_bill(db, bill_id):
        raise HTTPException(status_code=404, detail="Bill no encontrada")
    return None


# ========== PAGOS ENDPOINTS ==========
@app.post("/pagos", response_model=schemas.Pago, status_code=201)
def registrar_pago(pago: schemas.PagoCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo pago"""
    # Verificar que la bill existe
    bill = crud.get_bill(db, pago.bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill no encontrada")
    return crud.create_pago(db, pago)


@app.get("/pagos", response_model=List[schemas.Pago])
def listar_pagos(
    bill_id: Optional[int] = None,
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2020),
    db: Session = Depends(get_db)
):
    """Listar pagos con filtros opcionales"""
    return crud.get_pagos(db, bill_id=bill_id, mes=mes, anio=anio)


@app.get("/pagos/{pago_id}", response_model=schemas.Pago)
def obtener_pago(pago_id: int, db: Session = Depends(get_db)):
    """Obtener un pago específico"""
    pago = crud.get_pago(db, pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago


# ========== PRESUPUESTOS ENDPOINTS ==========
@app.post("/presupuestos", response_model=schemas.Presupuesto, status_code=201)
def crear_presupuesto(presupuesto: schemas.PresupuestoCreate, db: Session = Depends(get_db)):
    """Crear un presupuesto mensual"""
    return crud.create_presupuesto(db, presupuesto)


@app.get("/presupuestos", response_model=List[schemas.Presupuesto])
def listar_presupuestos(
    mes: Optional[int] = Query(None, ge=1, le=12),
    anio: Optional[int] = Query(None, ge=2020),
    db: Session = Depends(get_db)
):
    """Listar presupuestos con filtros"""
    return crud.get_presupuestos(db, mes=mes, anio=anio)


# ========== REPORTES Y UTILIDADES ==========
@app.get("/reportes/pendientes")
def obtener_bills_pendientes(db: Session = Depends(get_db)):
    """Obtener bills pendientes de pago del mes actual"""
    hoy = date.today()
    pendientes = crud.get_bills_pendientes(db, hoy)
    
    return {
        "fecha_consulta": hoy,
        "total_pendientes": len(pendientes),
        "pendientes": [
            {
                "id": p["bill"].id,
                "nombre": p["bill"].nombre,
                "monto": p["bill"].monto,
                "categoria": p["bill"].categoria.value,
                "fecha_vencimiento": p["fecha_vencimiento"],
                "dias_hasta_vencimiento": p["dias_hasta_vencimiento"],
                "vencido": p["vencido"]
            }
            for p in pendientes
        ]
    }


@app.get("/reportes/gastos-categoria")
def obtener_gastos_por_categoria(
    mes: int = Query(..., ge=1, le=12),
    anio: int = Query(..., ge=2020),
    db: Session = Depends(get_db)
):
    """Obtener total de gastos por categoría en un mes"""
    gastos = crud.get_gastos_por_categoria(db, mes, anio)
    total = sum(gastos.values())
    
    return {
        "mes": mes,
        "anio": anio,
        "total_gastado": total,
        "por_categoria": gastos
    }


@app.get("/reportes/resumen-mensual")
def obtener_resumen_mensual(
    mes: int = Query(..., ge=1, le=12),
    anio: int = Query(..., ge=2020),
    db: Session = Depends(get_db)
):
    """Obtener resumen completo del mes: gastos, presupuestos y estado"""
    gastos = crud.get_gastos_por_categoria(db, mes, anio)
    presupuestos = crud.get_presupuestos(db, mes=mes, anio=anio)
    
    # Crear diccionario de presupuestos por categoría
    presupuestos_dict = {p.categoria.value: p.monto_limite for p in presupuestos}
    
    # Calcular estado por categoría
    estado_categorias = []
    for categoria, gasto in gastos.items():
        presupuesto = presupuestos_dict.get(categoria, 0)
        porcentaje = (gasto / presupuesto * 100) if presupuesto > 0 else 0
        
        estado_categorias.append({
            "categoria": categoria,
            "gastado": gasto,
            "presupuesto": presupuesto,
            "disponible": max(0, presupuesto - gasto),
            "porcentaje_usado": round(porcentaje, 2),
            "excedido": gasto > presupuesto
        })
    
    total_gastado = sum(gastos.values())
    total_presupuesto = sum(presupuestos_dict.values())
    
    return {
        "mes": mes,
        "anio": anio,
        "total_gastado": total_gastado,
        "total_presupuesto": total_presupuesto,
        "total_disponible": max(0, total_presupuesto - total_gastado),
        "categorias": estado_categorias
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
