"""
Script para iniciar el frontend de Streamlit
"""
import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Iniciando frontend Streamlit...")
    print("🌐 Aplicación disponible en: http://localhost:8501")
    print("---")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port=8501"
    ])
