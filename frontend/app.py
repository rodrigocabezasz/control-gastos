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
        response = requests.post(f"{API_URL}{endpoint}", json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Tiempo de espera agotado. Verifica que el backend esté corriendo.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 No se puede conectar al backend. Verifica que esté corriendo en http://localhost:8000")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
            return None
        else:
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = e.response.text if e.response.text else str(e)
            st.error(f"Error del servidor: {error_detail}")
        return None
    except requests.exceptions.JSONDecodeError as e:
        st.error(f"Error: El servidor devolvió una respuesta inválida. Verifica los logs del backend.")
        return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None


def api_get(endpoint: str, params: dict = None):
    """Realizar petición GET"""
    try:
        headers = get_headers()
        response = requests.get(f"{API_URL}{endpoint}", headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Tiempo de espera agotado. Verifica que el backend esté corriendo.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🔌 No se puede conectar al backend. Verifica que esté corriendo en http://localhost:8000")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("Sesión expirada. Por favor, inicia sesión nuevamente.")
            return None
        else:
            try:
                error_detail = e.response.json().get('detail', str(e))
            except:
                error_detail = e.response.text if e.response.text else str(e)
            st.error(f"Error: {error_detail}")
        return None
    except requests.exceptions.JSONDecodeError as e:
        st.error(f"Error: La respuesta del servidor no es válida. Verifica que el backend esté funcionando correctamente.")
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
                if not email or not password:
                    st.error("Por favor, completa todos los campos")
                else:
                    try:
                        # FastAPI OAuth2 espera username y password en form data
                        data = {
                            "username": email,  # OAuth2PasswordRequestForm usa 'username'
                            "password": password
                        }
                        response = requests.post(f"{API_URL}/auth/login", data=data, timeout=10)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.token = result["access_token"]
                            st.session_state.user = result["user"]
                            st.session_state.logged_in = True
                            st.success("¡Bienvenido!")
                            st.rerun()
                        else:
                            st.error("Email o contraseña incorrectos")
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Tiempo de espera agotado. Verifica que el backend esté corriendo.")
                    except requests.exceptions.ConnectionError:
                        st.error("🔌 No se puede conectar al backend en http://localhost:8000")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
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
    
    if stats is None:
        st.warning("⚠️ No se pudieron cargar las estadísticas. Verifica que:")
        st.info("""
        1. El backend esté corriendo en http://localhost:8000
        2. Tu sesión sea válida (intenta cerrar sesión y volver a entrar)
        3. Hayas registrado al menos una transacción este mes
        """)
        
        # Mostrar recordatorios aunque las stats fallen
        st.subheader("🔔 Recordatorios Próximos")
        reminders = api_get("/reminders/due")
        if reminders:
            due_reminders = [r for r in reminders if r.get('is_due') and r.get('days_until_due', 0) >= 0]
            if due_reminders:
                for reminder in due_reminders[:5]:
                    days = reminder.get('days_until_due', 0)
                    if days == 0:
                        message = "⚠️ **Vence HOY**"
                    elif days == 1:
                        message = "⏰ Vence mañana"
                    else:
                        message = f"📅 Vence en {days} días"
                    st.warning(f"{message}: {reminder.get('name', 'N/A')} - ${reminder.get('amount', 0):,.2f}")
            else:
                st.success("✅ No hay pagos pendientes próximos")
        return
    
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
    
    # ========== NOTIFICACIONES Y ALERTAS ==========
    st.divider()
    
    # Recordatorios próximos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔔 Recordatorios Próximos")
        pending_reminders = api_get("/notifications/pending-reminders?days_ahead=7")
        
        if pending_reminders:
            for reminder in pending_reminders[:5]:  # Mostrar máximo 5
                days = reminder['days_until_due']
                
                if days == 0:
                    icon = "🚨"
                    color = "error"
                    message = "Vence HOY"
                elif days <= 2:
                    icon = "⚠️"
                    color = "warning"
                    message = f"Vence en {days} día{'s' if days > 1 else ''}"
                else:
                    icon = "📅"
                    color = "info"
                    message = f"Vence en {days} días"
                
                with st.container():
                    st.markdown(f"**{icon} {reminder['name']}** - ${reminder['amount']:,.2f}")
                    st.caption(f"{message} • {reminder['frequency'].capitalize()}")
        else:
            st.success("✅ No hay pagos pendientes próximos")
    
    with col2:
        st.subheader("⚠️ Alertas de Presupuesto")
        budget_alerts = api_get("/notifications/budget-alerts")
        
        if budget_alerts:
            for alert in budget_alerts[:5]:  # Mostrar máximo 5
                percentage = alert['percentage_used']
                
                if percentage >= 100:
                    icon = "🚨"
                    status_text = f"Excedido por ${abs(alert['remaining']):,.2f}"
                elif percentage >= 80:
                    icon = "⚠️"
                    status_text = f"Quedan ${alert['remaining']:,.2f}"
                else:
                    continue  # No mostrar si está por debajo del threshold
                
                with st.container():
                    st.markdown(f"**{icon} {alert['category_icon']} {alert['category_name']}**")
                    st.progress(min(percentage / 100, 1.0))
                    st.caption(f"{percentage:.1f}% usado • {status_text}")
        else:
            st.info("💚 Todos los presupuestos están bajo control")
    
    # ========== TENDENCIAS Y ANÁLISIS ==========
    st.divider()
    st.subheader("📈 Tendencias y Análisis")
    
    # Obtener datos de tendencias
    trends = api_get("/stats/trends?months=6")
    
    if trends and trends.get('months'):
        # Crear tabs para diferentes vistas
        tab_trend1, tab_trend2, tab_trend3 = st.tabs(["📊 Evolución Mensual", "📉 Por Categoría", "🔮 Predicción"])
        
        with tab_trend1:
            # Gráfico de línea: Ingresos vs Gastos
            fig_trend = go.Figure()
            
            fig_trend.add_trace(go.Scatter(
                x=trends['months'],
                y=trends['income'],
                mode='lines+markers',
                name='Ingresos',
                line=dict(color='#2ecc71', width=3),
                marker=dict(size=8)
            ))
            
            fig_trend.add_trace(go.Scatter(
                x=trends['months'],
                y=trends['expenses'],
                mode='lines+markers',
                name='Gastos',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=8)
            ))
            
            fig_trend.add_trace(go.Scatter(
                x=trends['months'],
                y=trends['balance'],
                mode='lines+markers',
                name='Balance',
                line=dict(color='#3498db', width=3, dash='dash'),
                marker=dict(size=8)
            ))
            
            fig_trend.update_layout(
                title="Evolución de Ingresos, Gastos y Balance",
                xaxis_title="Mes",
                yaxis_title="Monto ($)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Métricas de tendencia
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            
            with col_t1:
                st.metric(
                    "📊 Promedio Ingresos",
                    f"${trends['average']['income']:,.2f}"
                )
            
            with col_t2:
                st.metric(
                    "📊 Promedio Gastos",
                    f"${trends['average']['expenses']:,.2f}"
                )
            
            with col_t3:
                growth_income = trends['growth_rate']['income']
                st.metric(
                    "📈 Crecimiento Ingresos",
                    f"{growth_income:+.1f}%",
                    delta=f"{growth_income:+.1f}%"
                )
            
            with col_t4:
                growth_expenses = trends['growth_rate']['expenses']
                st.metric(
                    "📉 Crecimiento Gastos",
                    f"{growth_expenses:+.1f}%",
                    delta=f"{growth_expenses:+.1f}%",
                    delta_color="inverse"
                )
        
        with tab_trend2:
            # Gráfico de tendencias por categoría
            if trends['categories_trend']:
                st.write("**Evolución de gastos por categoría:**")
                
                fig_cat_trend = go.Figure()
                
                for category, values in trends['categories_trend'].items():
                    fig_cat_trend.add_trace(go.Scatter(
                        x=trends['months'],
                        y=values,
                        mode='lines+markers',
                        name=category,
                        marker=dict(size=6)
                    ))
                
                fig_cat_trend.update_layout(
                    title="Tendencia de Gastos por Categoría",
                    xaxis_title="Mes",
                    yaxis_title="Monto ($)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_cat_trend, use_container_width=True)
            else:
                st.info("No hay suficientes datos para mostrar tendencias por categoría")
        
        with tab_trend3:
            # Predicción para el próximo mes
            st.write("**Predicción para el próximo mes (basada en últimos 3 meses):**")
            
            col_p1, col_p2, col_p3 = st.columns(3)
            
            with col_p1:
                st.metric(
                    "💰 Ingresos Estimados",
                    f"${trends['prediction']['next_month_income']:,.2f}"
                )
            
            with col_p2:
                st.metric(
                    "💸 Gastos Estimados",
                    f"${trends['prediction']['next_month_expenses']:,.2f}"
                )
            
            with col_p3:
                predicted_balance = trends['prediction']['next_month_balance']
                st.metric(
                    "📈 Balance Estimado",
                    f"${predicted_balance:,.2f}",
                    delta=f"${predicted_balance:,.2f}",
                    delta_color="normal" if predicted_balance >= 0 else "inverse"
                )
            
            # Gráfico de predicción
            months_with_pred = trends['months'] + ["Predicción"]
            income_with_pred = trends['income'] + [trends['prediction']['next_month_income']]
            expenses_with_pred = trends['expenses'] + [trends['prediction']['next_month_expenses']]
            
            fig_pred = go.Figure()
            
            fig_pred.add_trace(go.Scatter(
                x=months_with_pred,
                y=income_with_pred,
                mode='lines+markers',
                name='Ingresos',
                line=dict(color='#2ecc71', width=3)
            ))
            
            fig_pred.add_trace(go.Scatter(
                x=months_with_pred,
                y=expenses_with_pred,
                mode='lines+markers',
                name='Gastos',
                line=dict(color='#e74c3c', width=3)
            ))
            
            # Marcar la predicción
            fig_pred.add_vline(
                x=len(trends['months']) - 0.5,
                line_dash="dash",
                line_color="gray",
                annotation_text="Predicción"
            )
            
            fig_pred.update_layout(
                title="Proyección del Próximo Mes",
                xaxis_title="Mes",
                yaxis_title="Monto ($)",
                height=400
            )
            
            st.plotly_chart(fig_pred, use_container_width=True)
            
            st.info("💡 La predicción se basa en el promedio de los últimos 3 meses. Es una estimación simple que te ayuda a planificar.")
    else:
        st.info("📊 No hay suficientes datos históricos para mostrar tendencias. Registra transacciones durante varios meses para ver el análisis.")


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
    
    # ========== FILTROS AVANZADOS ==========
    with st.expander("🔍 Filtros Avanzados", expanded=True):
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
        
        # Segunda fila de filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_amount = st.number_input("Monto mínimo ($)", min_value=0.0, value=0.0, step=10.0, key="min_amount")
        
        with col2:
            max_amount = st.number_input("Monto máximo ($)", min_value=0.0, value=0.0, step=10.0, key="max_amount")
            if max_amount == 0.0:
                max_amount = None
        
        with col3:
            search_text = st.text_input("🔍 Buscar en descripción", placeholder="Escribe para buscar...", key="search_text")
    
    # Construir params
    params = {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "limit": 100
    }
    
    if filter_type != "Todos":
        params["type"] = "ingreso" if filter_type == "Ingresos" else "gasto"
    
    if filter_cat != "Todas" and categories:
        selected_cat_name = filter_cat.split(" ", 1)[1] if " " in filter_cat else filter_cat
        cat = next((c for c in categories if c['name'] == selected_cat_name), None)
        if cat:
            params["category_id"] = cat['id']
    
    if min_amount > 0:
        params["min_amount"] = min_amount
    
    if max_amount:
        params["max_amount"] = max_amount
    
    if search_text:
        params["search_text"] = search_text
    
    # Obtener transacciones
    transactions = api_get("/transactions", params=params)
    
    if transactions:
        st.success(f"📊 Se encontraron {len(transactions)} transacciones")
        
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
        
        # Botones de exportación
        st.divider()
        col_export1, col_export2, col_export3 = st.columns([1, 1, 2])
        
        with col_export1:
            if st.button("📥 Exportar a Excel", use_container_width=True):
                # Construir URL con parámetros
                export_url = f"{API_URL}/transactions/export/excel?"
                
                if filter_type != "Todos":
                    export_url += f"type={'ingreso' if filter_type == 'Ingresos' else 'gasto'}&"
                
                if filter_cat != "Todas" and categories:
                    selected_cat_name = filter_cat.split(" ", 1)[1] if " " in filter_cat else filter_cat
                    cat = next((c for c in categories if c['name'] == selected_cat_name), None)
                    if cat:
                        export_url += f"category_id={cat['id']}&"
                
                export_url += f"start_date={start_date}&end_date={end_date}"
                
                if min_amount > 0:
                    export_url += f"&min_amount={min_amount}"
                
                if max_amount:
                    export_url += f"&max_amount={max_amount}"
                
                if search_text:
                    export_url += f"&search_text={search_text}"
                
                # Hacer request para descargar
                headers = get_headers()
                try:
                    response = requests.get(export_url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        filename = f"transacciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        st.download_button(
                            label="⬇️ Descargar Excel",
                            data=response.content,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    else:
                        st.error("Error al exportar a Excel")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col_export2:
            if st.button("📥 Exportar a CSV", use_container_width=True):
                # Construir URL con parámetros
                export_url = f"{API_URL}/transactions/export/csv?"
                
                if filter_type != "Todos":
                    export_url += f"type={'ingreso' if filter_type == 'Ingresos' else 'gasto'}&"
                
                if filter_cat != "Todas" and categories:
                    selected_cat_name = filter_cat.split(" ", 1)[1] if " " in filter_cat else filter_cat
                    cat = next((c for c in categories if c['name'] == selected_cat_name), None)
                    if cat:
                        export_url += f"category_id={cat['id']}&"
                
                export_url += f"start_date={start_date}&end_date={end_date}"
                
                if min_amount > 0:
                    export_url += f"&min_amount={min_amount}"
                
                if max_amount:
                    export_url += f"&max_amount={max_amount}"
                
                if search_text:
                    export_url += f"&search_text={search_text}"
                
                # Hacer request para descargar
                headers = get_headers()
                try:
                    response = requests.get(export_url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        filename = f"transacciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        st.download_button(
                            label="⬇️ Descargar CSV",
                            data=response.content,
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.error("Error al exportar a CSV")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col_export3:
            st.caption("💡 Los archivos exportados incluyen todas las transacciones que coinciden con los filtros aplicados")
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
            name = st.text_input("Nombre", max_chars=100, placeholder="Ej: Cuenta de Celular")
            amount = st.number_input("Monto ($)", min_value=0.01, max_value=999999999.99, step=0.01, format="%.2f")
            frequency = st.selectbox(
                "Frecuencia",
                options=["mensual", "bimensual", "trimestral", "semestral", "anual"],
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            due_day = st.number_input("Día de vencimiento", min_value=1, max_value=31, value=1)
            description = st.text_area("Descripción (opcional)", placeholder="Ej: Telefónica - Plan móvil")
        
        submit = st.form_submit_button("💾 Crear Recordatorio", use_container_width=True)
        
        if submit:
            if not name or name.strip() == "":
                st.error("⚠️ El nombre es obligatorio")
            elif amount <= 0:
                st.error("⚠️ El monto debe ser mayor a 0")
            else:
                data = {
                    "name": name.strip(),
                    "amount": float(amount),
                    "frequency": frequency,
                    "due_day": int(due_day),
                    "description": description.strip() if description else None
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
                    
                    # Formulario para marcar como pagado
                    with st.form(key=f"pay_form_{reminder['id']}"):
                        st.write("**Marcar como pagado:**")
                        
                        # Obtener categorías
                        categories = api_get("/categories")
                        if categories:
                            cat_options = {f"{cat['icon']} {cat['name']}": cat['id'] for cat in categories}
                            selected_cat = st.selectbox(
                                "Categoría para el gasto", 
                                options=list(cat_options.keys()),
                                key=f"cat_{reminder['id']}"
                            )
                            
                            payment_date = st.date_input(
                                "Fecha de pago",
                                value=date.today(),
                                key=f"date_{reminder['id']}"
                            )
                            
                            pay_submit = st.form_submit_button("✅ Marcar como Pagado")
                            
                            if pay_submit:
                                data = {
                                    "category_id": cat_options[selected_cat],
                                    "payment_date": str(payment_date)
                                }
                                result = api_post(f"/reminders/{reminder['id']}/mark-paid", data)
                                if result:
                                    st.success("✅ Marcado como pagado y transacción creada")
                                    st.rerun()
                        else:
                            st.warning("⚠️ Necesitas crear categorías primero")
                
                with col2:
                    if st.button("🗑️ Eliminar", key=f"del_rem_{reminder['id']}"):
                        if api_delete(f"/reminders/{reminder['id']}"):
                            st.success("Eliminado")
                            st.rerun()
    else:
        st.info("No tienes recordatorios configurados")


# ========== IMPORTAR BANCO ==========
def import_page():
    """Página de importación de cartolas bancarias"""
    st.title("🏦 Importar Cartola Bancaria")
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs(["📤 Importar Excel", "📋 Revisar Pendientes", "⚙️ Reglas de Homologación"])
    
    with tab1:
        import_excel_tab()
    
    with tab2:
        review_pending_tab()
    
    with tab3:
        import_rules_tab()


def import_excel_tab():
    """Tab para importar archivo Excel"""
    st.subheader("Importar Transacciones desde Excel")
    
    # Información sobre el formato
    with st.expander("ℹ️ Formato del archivo Excel", expanded=False):
        st.markdown("""
        **El archivo Excel debe contener las siguientes columnas:**
        
        - **Fecha**: Fecha de la transacción (cualquier formato de fecha)
        - **Descripción**: Descripción o glosa de la transacción
        - **Cargo**: Monto de los gastos/egresos (opcional si hay columna Abono)
        - **Abono**: Monto de los ingresos/depósitos (opcional si hay columna Cargo)
        
        **Nota:** Los nombres de columnas pueden variar (Fecha/Date, Descripción/Description/Glosa, 
        Cargo/Debe/Egreso, Abono/Haber/Ingreso). El sistema intentará identificarlas automáticamente.
        
        **Ejemplo:**
        
        | Fecha | Descripción | Cargo | Abono |
        |-------|-------------|-------|-------|
        | 01/01/2026 | SUPERMERCADO ABC | 45000 | |
        | 02/01/2026 | SUELDO MENSUAL | | 500000 |
        | 03/01/2026 | FARMACIA XYZ | 12500 | |
        """)
    
    # Upload de archivo
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo Excel o CSV de cartola bancaria",
        type=['xlsx', 'xls', 'csv'],
        help="Sube el archivo Excel o CSV descargado desde tu banco"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Archivo cargado: {uploaded_file.name}")
        
        if st.button("🚀 Importar Transacciones", type="primary", use_container_width=True):
            with st.spinner("Procesando archivo..."):
                # Preparar archivo para envío
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                headers = get_headers()
                
                try:
                    response = requests.post(
                        f"{API_URL}/transactions/import/excel",
                        files=files,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("🎉 ¡Importación completada!")
                        
                        # Mostrar resumen
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "📊 Total Importadas",
                                result['total_imported']
                            )
                        
                        with col2:
                            st.metric(
                                "✅ Auto-Categorizadas",
                                result['auto_categorized']
                            )
                        
                        with col3:
                            st.metric(
                                "⚠️ Requieren Revisión",
                                result['needs_review']
                            )
                        
                        with col4:
                            st.metric(
                                "🚫 Duplicadas Omitidas",
                                result.get('duplicates_skipped', 0)
                            )
                        
                        st.info(f"🔖 ID de lote: {result['batch_id']}")
                        
                        if result.get('duplicates_skipped', 0) > 0:
                            st.info(f"ℹ️ Se omitieron {result['duplicates_skipped']} transacciones duplicadas (misma fecha, monto y descripción)")
                        
                        if result['needs_review'] > 0:
                            st.warning("⚠️ Hay transacciones que requieren asignación de categoría. Ve a la pestaña 'Revisar Pendientes'")
                        else:
                            st.success("✅ Todas las transacciones fueron categorizadas automáticamente")
                        
                        # Botón para ir a revisar
                        if st.button("➡️ Ir a Revisar Pendientes"):
                            st.rerun()
                        
                    else:
                        error_detail = response.json().get('detail', 'Error desconocido')
                        st.error(f"❌ Error al importar: {error_detail}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏱️ Tiempo de espera agotado. El archivo puede ser muy grande.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def review_pending_tab():
    """Tab para revisar transacciones pendientes"""
    st.subheader("Revisar Transacciones Pendientes")
    
    # Obtener transacciones pendientes
    pending = api_get("/transactions/pending")
    
    if not pending:
        st.info("✅ No hay transacciones pendientes de revisión")
        return
    
    st.success(f"📊 Hay {len(pending)} transacciones pendientes")
    
    # Obtener categorías para el selector
    categories = api_get("/categories")
    if not categories:
        st.warning("⚠️ Necesitas crear categorías primero")
        return
    
    cat_options = {f"{cat['icon']} {cat['name']}": cat['id'] for cat in categories}
    
    # Formulario para asignar categorías
    with st.form("assign_categories_form"):
        st.write("**Asigna categorías a las transacciones:**")
        
        assignments = {}
        selected_ids = []
        
        for idx, trans in enumerate(pending):
            col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
            
            with col1:
                select = st.checkbox(
                    "Seleccionar",
                    key=f"select_{trans['id']}",
                    value=True,
                    label_visibility="collapsed"
                )
                if select:
                    selected_ids.append(trans['id'])
            
            with col2:
                st.write(f"📅 {trans['date']}")
            
            with col3:
                tipo_icon = "💰" if trans['type'] == "ingreso" else "💸"
                st.write(f"{tipo_icon} ${trans['amount']:,.0f}")
            
            with col4:
                # Mostrar descripción
                desc = trans['description'][:60] + "..." if len(trans['description']) > 60 else trans['description']
                if trans['auto_categorized']:
                    st.write(f"✅ {desc}")
                else:
                    st.write(f"⚠️ {desc}")
            
            with col5:
                # Selector de categoría
                default_cat = None
                if trans['category_id']:
                    # Buscar la categoría actual
                    current_cat = next((c for c in categories if c['id'] == trans['category_id']), None)
                    if current_cat:
                        default_cat = f"{current_cat['icon']} {current_cat['name']}"
                
                if default_cat and default_cat in cat_options:
                    default_index = list(cat_options.keys()).index(default_cat)
                else:
                    default_index = 0
                
                selected_cat = st.selectbox(
                    "Categoría",
                    options=list(cat_options.keys()),
                    key=f"cat_{trans['id']}",
                    index=default_index,
                    label_visibility="collapsed"
                )
                
                assignments[str(trans['id'])] = cat_options[selected_cat]
            
            st.divider()
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            confirm_button = st.form_submit_button(
                f"✅ Confirmar {len(selected_ids)} Seleccionadas",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            delete_button = st.form_submit_button(
                f"🗑️ Eliminar {len(selected_ids)} Seleccionadas",
                use_container_width=True
            )
        
        if confirm_button:
            if selected_ids:
                data = {
                    "transaction_ids": selected_ids,
                    "category_assignments": assignments
                }
                
                result = api_post("/transactions/pending/confirm", data)
                
                if result:
                    st.success(f"✅ {result['confirmed_count']} transacciones confirmadas")
                    st.rerun()
            else:
                st.warning("⚠️ No hay transacciones seleccionadas")
        
        if delete_button:
            if selected_ids:
                deleted_count = 0
                for trans_id in selected_ids:
                    if api_delete(f"/transactions/pending/{trans_id}"):
                        deleted_count += 1
                
                st.success(f"🗑️ {deleted_count} transacciones eliminadas")
                st.rerun()
            else:
                st.warning("⚠️ No hay transacciones seleccionadas")


def import_rules_tab():
    """Tab para gestionar reglas de homologación"""
    st.subheader("Reglas de Homologación Automática")
    
    st.info("""
    💡 **¿Qué son las reglas de homologación?**
    
    Las reglas permiten categorizar automáticamente las transacciones según palabras clave en la descripción.
    Por ejemplo, si creas una regla con la palabra "supermercado" → categoría "Alimentación",
    todas las transacciones que contengan "supermercado" en su descripción se asignarán automáticamente
    a la categoría Alimentación.
    """)
    
    # Tabs para crear y ver reglas
    tab_create, tab_view = st.tabs(["➕ Nueva Regla", "📋 Mis Reglas"])
    
    with tab_create:
        st.write("**Crear Nueva Regla de Homologación**")
        
        categories = api_get("/categories")
        if not categories:
            st.warning("⚠️ Necesitas crear categorías primero")
            return
        
        with st.form("create_rule_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                keyword = st.text_input(
                    "Palabra clave",
                    placeholder="Ej: supermercado, farmacia, uber",
                    help="Palabra o frase que debe aparecer en la descripción"
                )
                
                cat_options = {f"{cat['icon']} {cat['name']}": cat['id'] for cat in categories}
                selected_cat = st.selectbox("Categoría destino", options=list(cat_options.keys()))
            
            with col2:
                priority = st.slider(
                    "Prioridad",
                    min_value=0,
                    max_value=100,
                    value=50,
                    help="Mayor prioridad = se aplica primero (útil si hay múltiples coincidencias)"
                )
            
            submit = st.form_submit_button("💾 Crear Regla", use_container_width=True)
            
            if submit:
                if not keyword or keyword.strip() == "":
                    st.error("⚠️ La palabra clave es obligatoria")
                else:
                    data = {
                        "keyword": keyword.strip().lower(),
                        "category_id": cat_options[selected_cat],
                        "priority": priority
                    }
                    
                    result = api_post("/import-rules", data)
                    if result:
                        st.success(f"✅ Regla creada: '{keyword}' → {selected_cat}")
                        st.rerun()
    
    with tab_view:
        st.write("**Reglas Activas**")
        
        rules = api_get("/import-rules")
        
        if rules:
            # Agrupar por categoría
            categories = api_get("/categories")
            cat_dict = {cat['id']: cat for cat in categories} if categories else {}
            
            for rule in rules:
                cat = cat_dict.get(rule['category_id'])
                cat_name = f"{cat['icon']} {cat['name']}" if cat else "Categoría desconocida"
                
                col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
                
                with col1:
                    st.write(f"🔑 **{rule['keyword']}**")
                
                with col2:
                    st.write(f"→ {cat_name}")
                
                with col3:
                    st.write(f"Prioridad: {rule['priority']}")
                
                with col4:
                    if st.button("🗑️", key=f"del_rule_{rule['id']}"):
                        if api_delete(f"/import-rules/{rule['id']}"):
                            st.success("Eliminada")
                            st.rerun()
                
                st.divider()
        else:
            st.info("📝 No hay reglas creadas. Crea reglas para automatizar la categorización.")


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
                options=["Dashboard", "Transacciones", "Categorías", "Presupuestos", "Recordatorios", "Importar Banco"],
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
        elif page == "Importar Banco":
            import_page()


if __name__ == "__main__":
    main()
