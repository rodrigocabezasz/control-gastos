@echo off
echo ========================================
echo   Control de Gastos - Inicio
echo ========================================
echo.
echo [1/2] Iniciando Backend (FastAPI)...
start "Backend - FastAPI" cmd /k ".\venv\Scripts\python.exe run_backend.py"
timeout /t 3 /nobreak >nul

echo [2/2] Iniciando Frontend (Streamlit)...
start "Frontend - Streamlit" cmd /k ".\venv\Scripts\python.exe run_frontend.py"

echo.
echo ========================================
echo   Aplicacion iniciada!
echo ========================================
echo   Backend:  http://localhost:8000/docs
echo   Frontend: http://localhost:8501
echo ========================================
pause
