# 💰 Control de Gastos Personales

Sistema completo de gestión de gastos personales con autenticación JWT, categorías personalizables, presupuestos mensuales, recordatorios de pagos y visualización de estadísticas.

## 🚀 Características

### Autenticación y Seguridad
- ✅ Registro y login con JWT (JSON Web Tokens)
- ✅ Encriptación de contraseñas con bcrypt
- ✅ Sesiones seguras y protección de rutas
- ✅ Cada usuario tiene sus propios datos aislados

### Gestión de Transacciones
- 💸 Registro de gastos e ingresos
- 📁 Categorías personalizables por usuario
- 📅 Filtrado por fecha, categoría y tipo
- 📎 Opción para adjuntar comprobantes
- 📊 Visualización con gráficos interactivos

### Presupuestos Mensuales
- 💼 Creación de presupuestos por categoría y mes
- 📈 Seguimiento en tiempo real del gasto vs presupuesto
- ⚠️ Alertas cuando se alcanza el umbral configurado
- 🎯 Porcentaje de uso y balance restante

### Recordatorios de Pagos
- 🔔 Alertas de facturas recurrentes (luz, agua, internet, etc.)
- ⏰ Notificaciones 5 días antes del vencimiento
- ✅ Marcar pagos como realizados
- 📆 Soporte para diferentes frecuencias (mensual, bimensual, etc.)

### Análisis y Reportes
- 📊 Dashboard con métricas clave
- 📈 Gráficos de gastos por categoría
- 💹 Comparación ingresos vs gastos
- 💎 Tasa de ahorro mensual
- 📥 Exportación de datos a Excel

## 🏗️ Arquitectura

```
/control_gastos
├── backend/                 # FastAPI Backend
│   ├── __init__.py
│   ├── main.py             # Endpoints de la API
│   ├── models.py           # Modelos SQLAlchemy
│   ├── schemas.py          # Esquemas Pydantic
│   ├── crud.py             # Operaciones CRUD
│   ├── auth.py             # Autenticación JWT
│   └── database.py         # Configuración DB
├── frontend/               # Streamlit Frontend
│   ├── __init__.py
│   └── app.py              # Interfaz de usuario
├── .env                    # Variables de entorno
├── .env.example            # Template de configuración
├── requirements.txt        # Dependencias Python
├── run_backend.py          # Script para iniciar backend
├── run_frontend.py         # Script para iniciar frontend
└── README.md
```

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🛠️ Instalación

### 1. Clonar o descargar el proyecto

```bash
cd control_gastos
```

### 2. Crear entorno virtual

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y ajusta los valores:

```powershell
Copy-Item .env.example .env
```

**Importante:** Genera una SECRET_KEY segura para producción:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copia la clave generada y reemplázala en el archivo `.env`:

```env
SECRET_KEY=tu-clave-generada-aqui
```

## 🚀 Ejecución

### Opción 1: Ejecutar Backend y Frontend por separado

**Terminal 1 - Backend (FastAPI):**
```powershell
python run_backend.py
```
El backend estará disponible en: `http://localhost:8000`
Documentación API: `http://localhost:8000/docs`

**Terminal 2 - Frontend (Streamlit):**
```powershell
python run_frontend.py
```
El frontend estará disponible en: `http://localhost:8501`

### Opción 2: Usar el script de inicio rápido (Windows)

```powershell
.\start.bat
```

Este script iniciará automáticamente el backend y frontend en terminales separadas.

## 📖 Uso

### 1. Registro de Usuario

1. Abre el frontend en `http://localhost:8501`
2. Ve a la pestaña "Registrarse"
3. Completa el formulario con:
   - Nombre de usuario (mínimo 3 caracteres)
   - Email válido
   - Contraseña (mínimo 6 caracteres)
4. Haz clic en "Registrarse"

### 2. Inicio de Sesión

1. Ve a la pestaña "Iniciar Sesión"
2. Ingresa tu email y contraseña
3. Haz clic en "Iniciar Sesión"

### 3. Gestión de Categorías

Las categorías por defecto se crean automáticamente al registrarte:
- 🏠 Vivienda
- ⚡ Servicios
- 🚗 Transporte
- 🍔 Alimentación
- 🏥 Salud
- 🎮 Entretenimiento
- 📚 Educación
- 📦 Otros

Puedes crear categorías personalizadas:
1. Ve a "Categorías" → "Nueva Categoría"
2. Completa el formulario
3. Personaliza el emoji/icono y color

### 4. Registrar Transacciones

1. Ve a "Transacciones" → "Nueva Transacción"
2. Selecciona:
   - Tipo (Ingreso o Gasto)
   - Categoría
   - Monto
   - Fecha
   - Descripción
3. Haz clic en "Guardar Transacción"

### 5. Crear Presupuestos

1. Ve a "Presupuestos" → "Nuevo Presupuesto"
2. Selecciona:
   - Categoría
   - Monto límite
   - Mes y año
   - Umbral de alerta (%) - Por defecto 80%
3. El sistema te alertará cuando alcances el umbral

### 6. Configurar Recordatorios

1. Ve a "Recordatorios" → "Nuevo Recordatorio"
2. Completa:
   - Nombre (ej: "Pago de luz")
   - Monto
   - Frecuencia (mensual, bimensual, etc.)
   - Día de vencimiento (1-31)
3. Recibirás alertas 5 días antes del vencimiento

### 7. Ver Dashboard

El dashboard muestra:
- 💰 Total de ingresos del mes
- 💸 Total de gastos del mes
- 📈 Balance (ingresos - gastos)
- 💎 Tasa de ahorro
- 📊 Gráficos de gastos por categoría
- 🔔 Recordatorios próximos a vencer

## 🔌 API Endpoints

### Autenticación

- `POST /auth/register` - Registrar nuevo usuario
- `POST /auth/login` - Iniciar sesión (obtener token JWT)
- `GET /auth/me` - Obtener información del usuario actual

### Usuarios

- `GET /users/me` - Obtener perfil
- `PUT /users/me` - Actualizar perfil

### Categorías

- `GET /categories` - Listar categorías
- `POST /categories` - Crear categoría
- `GET /categories/{id}` - Obtener categoría
- `PUT /categories/{id}` - Actualizar categoría
- `DELETE /categories/{id}` - Eliminar categoría

### Transacciones

- `GET /transactions` - Listar transacciones (con filtros)
- `POST /transactions` - Crear transacción
- `GET /transactions/{id}` - Obtener transacción
- `PUT /transactions/{id}` - Actualizar transacción
- `DELETE /transactions/{id}` - Eliminar transacción

### Presupuestos

- `GET /budgets` - Listar presupuestos
- `POST /budgets` - Crear presupuesto
- `GET /budgets/{id}` - Obtener presupuesto con estado
- `PUT /budgets/{id}` - Actualizar presupuesto
- `DELETE /budgets/{id}` - Eliminar presupuesto

### Recordatorios

- `GET /reminders` - Listar recordatorios
- `GET /reminders/due` - Obtener recordatorios próximos
- `POST /reminders` - Crear recordatorio
- `GET /reminders/{id}` - Obtener recordatorio
- `PUT /reminders/{id}` - Actualizar recordatorio
- `POST /reminders/{id}/mark-paid` - Marcar como pagado
- `DELETE /reminders/{id}` - Eliminar recordatorio

### Estadísticas

- `GET /stats/monthly?month={m}&year={y}` - Estadísticas mensuales
- `GET /stats/current-month` - Estadísticas del mes actual

**Documentación completa:** `http://localhost:8000/docs`

## 🔐 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ Tokens JWT con expiración (7 días por defecto)
- ✅ Protección de rutas con autenticación
- ✅ Validación de datos con Pydantic
- ✅ Aislamiento de datos por usuario
- ✅ Variables sensibles en `.env` (no en código)

## 🗃️ Base de Datos

### SQLite (Desarrollo)

Por defecto, el proyecto usa SQLite:
- Fácil de configurar
- No requiere instalación adicional
- Archivo: `control_gastos.db`

### PostgreSQL (Producción)

Para cambiar a PostgreSQL:

1. Instala PostgreSQL
2. Crea la base de datos:
```sql
CREATE DATABASE control_gastos;
```

3. Actualiza `.env`:
```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/control_gastos
```

## 📦 Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **Pydantic** - Validación de datos
- **JWT** - Autenticación con tokens
- **Bcrypt** - Hash de contraseñas
- **Uvicorn** - Servidor ASGI

### Frontend
- **Streamlit** - Framework para interfaces web
- **Plotly** - Gráficos interactivos
- **Pandas** - Manipulación de datos
- **Requests** - Cliente HTTP

### Base de Datos
- **SQLite** (desarrollo)
- **PostgreSQL** (producción)

## 🧪 Testing

Ejecutar tests (próximamente):

```powershell
pytest
```

## 📝 Próximas Mejoras

- [ ] Notificaciones por email
- [ ] Exportar reportes en PDF
- [ ] Gráficos de tendencias anuales
- [ ] Modo oscuro en el frontend
- [ ] API para importar datos desde CSV
- [ ] Soporte multi-moneda
- [ ] Categorías compartidas entre usuarios
- [ ] App móvil

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👤 Autor

Desarrollado con ❤️ para facilitar el control de gastos personales.

## 📞 Soporte

Si encuentras algún problema o tienes preguntas:

1. Revisa la documentación
2. Consulta los logs del backend y frontend
3. Abre un issue en el repositorio

## 🎯 Casos de Uso

### Ejemplo 1: Control Mensual Básico

```
1. Registra tus ingresos mensuales (salario)
2. Registra todos tus gastos diarios
3. Crea presupuestos por categoría
4. Revisa el dashboard al final del mes
5. Ajusta tus presupuestos según el análisis
```

### Ejemplo 2: Gestión de Facturas Recurrentes

```
1. Crea recordatorios para todas tus facturas
2. Configura la frecuencia y día de vencimiento
3. Recibe alertas 5 días antes
4. Marca como pagado cuando completes el pago
5. Nunca más olvides un pago
```

### Ejemplo 3: Análisis de Ahorro

```
1. Registra todos los ingresos y gastos
2. Revisa tu tasa de ahorro en el dashboard
3. Identifica categorías con mayor gasto
4. Ajusta presupuestos para aumentar ahorro
5. Exporta datos para análisis externo
```

## ⚙️ Configuración Avanzada

### Cambiar Puerto del Backend

En `run_backend.py`:
```python
uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
```

### Cambiar Puerto del Frontend

En `run_frontend.py`:
```python
os.system("streamlit run frontend/app.py --server.port 8501")
```

### Configurar Tiempo de Expiración del Token

En `backend/auth.py`:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días
```

## 🐛 Troubleshooting

### Error: "Module not found"
```powershell
pip install -r requirements.txt
```

### Error: "Database locked"
Cierra todas las conexiones a la base de datos y reinicia.

### Error: "Token expired"
Inicia sesión nuevamente para obtener un nuevo token.

### Puerto en uso
Cambia el puerto en los archivos de configuración o cierra la aplicación que lo está usando.

---

**¡Gracias por usar Control de Gastos!** 🎉
