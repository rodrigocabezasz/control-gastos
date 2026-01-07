"""Script para inicializar la base de datos"""
from backend.database import engine, Base
from backend.models import User, Category, Transaction, Budget, Reminder

print("🔄 Eliminando tablas existentes...")
Base.metadata.drop_all(bind=engine)

print("🔄 Creando tablas...")
Base.metadata.create_all(bind=engine)

print("✅ Base de datos inicializada correctamente")
