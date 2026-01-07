"""
Script para iniciar el backend de FastAPI
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Iniciando backend FastAPI...")
    print("📡 API disponible en: http://localhost:8000")
    print("📚 Documentación en: http://localhost:8000/docs")
    print("---")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
