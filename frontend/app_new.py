"""
Control de Gastos - Frontend Streamlit
Sistema completo con autenticación JWT
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List
import json

# Configuración de la página
st.set_page_config(
    page_title="Control de Gastos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del backend
API_URL = "http://localhost:8000"

# ========== ESTILOS CSS ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ========== GESTIÓN DE SESIÓN ==========
def init_session_state():
    """Inicializar variables de sesión"""
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False


def logout():
    """Cerrar sesión"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.logged_in = False
    st.rerun()


def get_headers() -> Dict[str, str]:
    """Obtener headers con token de autenticación"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


# ========== FUNCIONES API ==========
def api_post(endpoint: str, data: dict, use_auth: bool = True):
    """Realizar petición POST"""
    try:
        headers = get_headers() if use_auth else {}
        response = requests.post(f"{API_URL}{endpoint}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
            logout()
        else:
            st.error(f"Error: {e.response.json().get('detail', str(e))}")
        return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None


def api_get(endpoint: str, params: dict = None):
    """Realizar petición GET"""
    try:
        headers = get_headers()
        response = requests.get(f"{API_URL}{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
            logout()
        else:
            st.error(f"Error: {e.response.json().get('detail', str(e))}")
        return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None


def api_put(endpoint: str, data: dict):
    """Realizar petición PUT"""
    try:
        headers = get_headers()
        response = requests.put(f"{API_URL}{endpoint}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
            logout()
        else:
            st.error(f"Error: {e.response.json().get('detail', str(e))}")
        return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None


def api_delete(endpoint: str):
    """Realizar petición DELETE"""
    try:
        headers = get_headers()
        response = requests.delete(f"{API_URL}{endpoint}", headers=headers)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
            logout()
        else:
            st.error(f"Error: {e.response.json().get('detail', str(e))}")
        return False
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return False


# ========== AUTENTICACIÓN ==========
def login_page():
    """Página de login"""
    st.markdown('<div class="main-header">💰 Control de Gastos</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Iniciar Sesión")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_password")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submit:
                # FastAPI OAuth2 espera username y password en form data
                data = {
                    "username": email,  # OAuth2PasswordRequestForm usa 'username'
                    "password": password
                }
                response = requests.post(f"{API_URL}/auth/login", data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.token = result["access_token"]
                    st.session_state.user = result["user"]
                    st.session_state.logged_in = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Email o contraseña incorrectos")
    
    with tab2:
        st.subheader("Crear Cuenta")
        with st.form("register_form"):
            username = st.text_input("Nombre de usuario", key="register_username")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Contraseña", type="password", key="register_password")
            password2 = st.text_input("Confirmar contraseña", type="password", key="register_password2")
            submit = st.form_submit_button("Registrarse", use_container_width=True)
            
            if submit:
                if password != password2:
                    st.error("Las contraseñas no coinciden")
                elif len(password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    data = {
                        "username": username,
                        "email": email,
                        "password": password
                    }
                    result = api_post("/auth/register", data, use_auth=False)
                    if result:
                        st.success("¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.")


# ========== DASHBOARD ==========
def dashboard_page():
    """Página principal del dashboard"""
    st.title("📊 Dashboard")
    
    # Obtener estadísticas del mes actual
    stats = api_get("/stats/current-month")
    
    if stats:
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Ingresos",
                f"${stats['total_income']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "💸 Gastos",
                f"${stats['total_expenses']:,.2f}",
                delta=None
            )
        
        with col3:
            balance = stats['balance']
            st.metric(
                "📈 Balance",
                f"${balance:,.2f}",
                delta=f"${balance:,.2f}",
                delta_color="normal" if balance >= 0 else "inverse"
            )
        
        with col4:
            savings_rate = (balance / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
            st.metric(
                "💎 Tasa de Ahorro",
                f"{savings_rate:.1f}%",
                delta=None
            )
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Gastos por Categoría")
            if stats['categories_expenses']:
                df_cat = pd.DataFrame(stats['categories_expenses'])
                fig = px.pie(
                    df_cat,
                    values='total',
                    names='name',
                    color='name',
                    color_discrete_map={cat['name']: cat['color'] for cat in stats['categories_expenses']}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay gastos registrados este mes")
        
        with col2:
            st.subheader("Ingresos vs Gastos")
            fig = go.Figure(data=[
                go.Bar(name='Ingresos', x=['Mes Actual'], y=[stats['total_income']], marker_color='#2ecc71'),
                go.Bar(name='Gastos', x=['Mes Actual'], y=[stats['total_expenses']], marker_color='#e74c3c')
            ])
            fig.update_layout(barmode='group')
            st.plotly_chart(fig, use_container_width=True)
    
    # Recordatorios próximos
    st.subheader("🔔 Recordatorios Próximos")
    reminders = api_get("/reminders/due")
    
    if reminders:
        due_reminders = [r for r in reminders if r['is_due'] and r['days_until_due'] >= 0]
        
        if due_reminders:
            for reminder in due_reminders[:5]:  # Mostrar máximo 5
                days = reminder['days_until_due']
                if days == 0:
                    message = "⚠️ **Vence HOY**"
                elif days == 1:
                    message = "⏰ Vence mañana"
                else:
                    message = f"📅 Vence en {days} días"
                
                st.warning(f"{message}: {reminder['name']} - ${reminder['amount']:,.2f}")
        else:
            st.success("✅ No hay pagos pendientes próximos")
    else:
        st.info("No hay recordatorios configurados")


# ========== TRANSACCIONES ==========
def transactions_page():
    """Página de transacciones"""
    st.title("💳 Transacciones")
    
    # Tabs para crear y ver transacciones
    tab1, tab2 = st.tabs(["➕ Nueva Transacción", "📋 Ver Transacciones"])
    
    with tab1:
        create_transaction_form()
    
    with tab2:
        view_transactions()


def create_transaction_form():
    """Formulario para crear transacción"""
    st.subheader("Registrar Nueva Transacción")
    
    # Obtener categorías
    categories = api_get("/categories")
    
    if not categories:
        st.warning("Primero debes crear categorías")
        return
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            type = st.selectbox(
                "Tipo",
                options=["gasto", "ingreso"],
                format_func=lambda x: "💸 Gasto" if x == "gasto" else "💰 Ingreso"
            )
            
            category_dict = {f"{cat['icon']} {cat['name']}": cat['id'] for cat in categories}
            selected_cat = st.selectbox("Categoría", options=list(category_dict.keys()))
            category_id = category_dict[selected_cat]
            
            amount = st.number_input("Monto ($)", min_value=0.01, step=0.01)
        
        with col2:
            transaction_date = st.date_input("Fecha", value=date.today())
            description = st.text_area("Descripción", max_chars=500)
        
        submit = st.form_submit_button("💾 Guardar Transacción", use_container_width=True)
        
        if submit:
            data = {
                "type": type,
                "category_id": category_id,
                "amount": amount,
                "date": str(transaction_date),
                "description": description
            }
            
            result = api_post("/transactions", data)
            if result:
                st.success("✅ Transacción registrada exitosamente")
                st.rerun()


def view_transactions():
    """Ver lista de transacciones"""
    st.subheader("Historial de Transacciones")
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_type = st.selectbox(
            "Tipo",
            options=["Todos", "Ingresos", "Gastos"],
            key="filter_type"
        )
    
    with col2:
        categories = api_get("/categories")
        cat_options = ["Todas"] + [f"{cat['icon']} {cat['name']}" for cat in categories] if categories else ["Todas"]
        filter_cat = st.selectbox("Categoría", options=cat_options, key="filter_cat")
    
    with col3:
        start_date = st.date_input("Desde", value=date.today() - timedelta(days=30), key="start_date")
    
    with col4:
        end_date = st.date_input("Hasta", value=date.today(), key="end_date")
    
    # Construir params
    params = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "limit": 100
    }
    
    if filter_type != "Todos":
        params["type"] = "ingreso" if filter_type == "Ingresos" else "gasto"
    
    # Obtener transacciones
    transactions = api_get("/transactions", params=params)
    
    if transactions:
        # Crear DataFrame
        df = pd.DataFrame(transactions)
        
        # Formatear para mostrar
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 2, 3, 1])
            
            with col1:
                st.write(f"📅 {row['date']}")
            
            with col2:
                tipo_icon = "💰" if row['type'] == "ingreso" else "💸"
                st.write(f"{tipo_icon} {row['type'].capitalize()}")
            
            with col3:
                st.write(f"${row['amount']:,.2f}")
            
            with col4:
                # Obtener categoría
                cat = next((c for c in categories if c['id'] == row['category_id']), None)
                if cat:
                    st.write(f"{cat['icon']} {cat['name']}")
            
            with col5:
                st.write(row['description'][:50] + "..." if len(row['description']) > 50 else row['description'])
            
            with col6:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    if api_delete(f"/transactions/{row['id']}"):
                        st.success("Eliminada")
                        st.rerun()
            
            st.divider()
        
        # Exportar a Excel
        if st.button("📥 Exportar a Excel"):
            df_export = df.copy()
            df_export.to_excel("transacciones.xlsx", index=False)
            st.success("Exportado a transacciones.xlsx")
    else:
        st.info("No hay transacciones para mostrar")


# ========== CATEGORÍAS ==========
def categories_page():
    """Página de categorías"""
    st.title("📁 Categorías")
    
    tab1, tab2 = st.tabs(["➕ Nueva Categoría", "📋 Mis Categorías"])
    
    with tab1:
        create_category_form()
    
    with tab2:
        view_categories()


def create_category_form():
    """Formulario para crear categoría"""
    st.subheader("Crear Nueva Categoría")
    
    with st.form("category_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nombre", max_chars=100)
            icon = st.text_input("Emoji/Icono", value="📦", max_chars=10)
        
        with col2:
            color = st.color_picker("Color", value="#3498db")
            description = st.text_area("Descripción (opcional)")
        
        submit = st.form_submit_button("💾 Crear Categoría", use_container_width=True)
        
        if submit:
            data = {
                "name": name,
                "icon": icon,
                "color": color,
                "description": description
            }
            
            result = api_post("/categories", data)
            if result:
                st.success("✅ Categoría creada exitosamente")
                st.rerun()


def view_categories():
    """Ver lista de categorías"""
    st.subheader("Mis Categorías")
    
    categories = api_get("/categories")
    
    if categories:
        for cat in categories:
            with st.expander(f"{cat['icon']} {cat['name']}", expanded=False):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**Descripción:** {cat['description'] or 'Sin descripción'}")
                    st.write(f"**Color:** {cat['color']}")
                    st.write(f"**Estado:** {'✅ Activa' if cat['is_active'] else '❌ Inactiva'}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_{cat['id']}"):
                        st.info("Funcionalidad en desarrollo")
                
                with col3:
                    if st.button("🗑️ Eliminar", key=f"del_cat_{cat['id']}"):
                        if api_delete(f"/categories/{cat['id']}"):
                            st.success("Eliminada")
                            st.rerun()
    else:
        st.info("No tienes categorías creadas")


# ========== PRESUPUESTOS ==========
def budgets_page():
    """Página de presupuestos"""
    st.title("💼 Presupuestos")
    
    tab1, tab2 = st.tabs(["➕ Nuevo Presupuesto", "📊 Mis Presupuestos"])
    
    with tab1:
        create_budget_form()
    
    with tab2:
        view_budgets()


def create_budget_form():
    """Formulario para crear presupuesto"""
    st.subheader("Crear Nuevo Presupuesto")
    
    categories = api_get("/categories")
    
    if not categories:
        st.warning("Primero debes crear categorías")
        return
    
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category_dict = {f"{cat['icon']} {cat['name']}": cat['id'] for cat in categories}
            selected_cat = st.selectbox("Categoría", options=list(category_dict.keys()))
            category_id = category_dict[selected_cat]
            
            amount = st.number_input("Monto Límite ($)", min_value=0.01, step=0.01)
        
        with col2:
            month = st.selectbox("Mes", options=list(range(1, 13)), format_func=lambda x: datetime(2024, x, 1).strftime('%B'))
            year = st.number_input("Año", min_value=2020, max_value=2100, value=datetime.now().year)
            alert_threshold = st.slider("Alertar al (%)", min_value=10, max_value=100, value=80) / 100
        
        submit = st.form_submit_button("💾 Crear Presupuesto", use_container_width=True)
        
        if submit:
            data = {
                "category_id": category_id,
                "amount": amount,
                "month": month,
                "year": year,
                "alert_threshold": alert_threshold
            }
            
            result = api_post("/budgets", data)
            if result:
                st.success("✅ Presupuesto creado exitosamente")
                st.rerun()


def view_budgets():
    """Ver presupuestos"""
    st.subheader("Mis Presupuestos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Mes", options=list(range(1, 13)), index=datetime.now().month - 1, key="budget_month")
    with col2:
        year = st.number_input("Año", value=datetime.now().year, key="budget_year")
    
    budgets = api_get("/budgets", params={"month": month, "year": year})
    
    if budgets:
        for budget_id in [b['id'] for b in budgets]:
            budget_detail = api_get(f"/budgets/{budget_id}")
            
            if budget_detail:
                cat = budget_detail['category']
                percentage = budget_detail['percentage_used']
                
                # Color según el porcentaje
                if percentage >= 100:
                    color = "🔴"
                elif percentage >= budget_detail['alert_threshold'] * 100:
                    color = "🟡"
                else:
                    color = "🟢"
                
                st.write(f"### {color} {cat['icon']} {cat['name']}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Presupuesto", f"${budget_detail['amount']:,.2f}")
                with col2:
                    st.metric("Gastado", f"${budget_detail['spent']:,.2f}")
                with col3:
                    st.metric("Restante", f"${budget_detail['remaining']:,.2f}")
                with col4:
                    st.metric("Uso", f"{percentage:.1f}%")
                
                # Barra de progreso
                st.progress(min(percentage / 100, 1.0))
                
                if budget_detail['is_exceeded']:
                    st.error(f"⚠️ ¡Has excedido el presupuesto por ${abs(budget_detail['remaining']):,.2f}!")
                
                st.divider()
    else:
        st.info("No hay presupuestos para este mes")


# ========== RECORDATORIOS ==========
def reminders_page():
    """Página de recordatorios"""
    st.title("🔔 Recordatorios")
    
    tab1, tab2 = st.tabs(["➕ Nuevo Recordatorio", "📋 Mis Recordatorios"])
    
    with tab1:
        create_reminder_form()
    
    with tab2:
        view_reminders()


def create_reminder_form():
    """Formulario para crear recordatorio"""
    st.subheader("Crear Nuevo Recordatorio")
    
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nombre", max_chars=100)
            amount = st.number_input("Monto ($)", min_value=0.01, step=0.01)
            frequency = st.selectbox(
                "Frecuencia",
                options=["mensual", "bimensual", "trimestral", "semestral", "anual"],
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            due_day = st.number_input("Día de vencimiento", min_value=1, max_value=31, value=1)
            description = st.text_area("Descripción (opcional)")
        
        submit = st.form_submit_button("💾 Crear Recordatorio", use_container_width=True)
        
        if submit:
            data = {
                "name": name,
                "amount": amount,
                "frequency": frequency,
                "due_day": due_day,
                "description": description
            }
            
            result = api_post("/reminders", data)
            if result:
                st.success("✅ Recordatorio creado exitosamente")
                st.rerun()


def view_reminders():
    """Ver recordatorios"""
    st.subheader("Mis Recordatorios")
    
    reminders = api_get("/reminders/due")
    
    if reminders:
        for reminder in reminders:
            days = reminder['days_until_due']
            
            # Color según días hasta vencimiento
            if days < 0:
                icon = "🔴"
                status = f"Vencido hace {abs(days)} días"
            elif days == 0:
                icon = "⚠️"
                status = "Vence HOY"
            elif days <= 5:
                icon = "🟡"
                status = f"Vence en {days} días"
            else:
                icon = "🟢"
                status = f"Vence en {days} días"
            
            with st.expander(f"{icon} {reminder['name']} - ${reminder['amount']:,.2f}", expanded=reminder['is_due']):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Estado:** {status}")
                    st.write(f"**Frecuencia:** {reminder['frequency'].capitalize()}")
                    st.write(f"**Día de vencimiento:** {reminder['due_day']}")
                    if reminder['description']:
                        st.write(f"**Descripción:** {reminder['description']}")
                    if reminder['last_paid_date']:
                        st.write(f"**Último pago:** {reminder['last_paid_date']}")
                
                with col2:
                    if st.button("✅ Marcar Pagado", key=f"pay_{reminder['id']}"):
                        result = api_post(f"/reminders/{reminder['id']}/mark-paid", {})
                        if result:
                            st.success("Marcado como pagado")
                            st.rerun()
                    
                    if st.button("🗑️ Eliminar", key=f"del_rem_{reminder['id']}"):
                        if api_delete(f"/reminders/{reminder['id']}"):
                            st.success("Eliminado")
                            st.rerun()
    else:
        st.info("No tienes recordatorios configurados")


# ========== MAIN ==========
def main():
    """Función principal"""
    init_session_state()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar con navegación
        with st.sidebar:
            st.title("💰 Control de Gastos")
            st.write(f"👤 {st.session_state.user['username']}")
            st.divider()
            
            page = st.radio(
                "Navegación",
                options=["Dashboard", "Transacciones", "Categorías", "Presupuestos", "Recordatorios"],
                label_visibility="collapsed"
            )
            
            st.divider()
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                logout()
        
        # Mostrar página seleccionada
        if page == "Dashboard":
            dashboard_page()
        elif page == "Transacciones":
            transactions_page()
        elif page == "Categorías":
            categories_page()
        elif page == "Presupuestos":
            budgets_page()
        elif page == "Recordatorios":
            reminders_page()


if __name__ == "__main__":
    main()
