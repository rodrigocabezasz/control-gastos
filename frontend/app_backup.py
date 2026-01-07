import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from typing import List, Dict

# Configuración de la página
st.set_page_config(
    page_title="Control de Gastos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del backend
API_URL = "http://localhost:8000"

# Mapeo de categorías en español
CATEGORIAS = {
    "vivienda": "🏠 Vivienda",
    "servicios": "⚡ Servicios",
    "transporte": "🚗 Transporte",
    "alimentacion": "🍔 Alimentación",
    "salud": "🏥 Salud",
    "entretenimiento": "🎮 Entretenimiento",
    "educacion": "📚 Educación",
    "otros": "📦 Otros"
}

FRECUENCIAS = {
    "mensual": "Mensual",
    "bimensual": "Bimensual",
    "trimestral": "Trimestral",
    "semestral": "Semestral",
    "anual": "Anual"
}


def api_get(endpoint: str):
    """Realizar petición GET al API"""
    try:
        response = requests.get(f"{API_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al conectar con el API: {e}")
        return None


def api_post(endpoint: str, data: dict):
    """Realizar petición POST al API"""
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al enviar datos: {e}")
        return None


def api_put(endpoint: str, data: dict):
    """Realizar petición PUT al API"""
    try:
        response = requests.put(f"{API_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return None


def api_delete(endpoint: str):
    """Realizar petición DELETE al API"""
    try:
        response = requests.delete(f"{API_URL}{endpoint}")
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False


# ========== PÁGINA: DASHBOARD ==========
def pagina_dashboard():
    """Dashboard principal con resumen y alertas"""
    st.title("💰 Dashboard - Control de Gastos")
    
    # Obtener mes y año actual
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # Obtener bills pendientes
    pendientes = api_get("/reportes/pendientes")
    
    if pendientes:
        # Mostrar alertas
        st.subheader("🔔 Alertas de Pagos Pendientes")
        
        vencidos = [p for p in pendientes["pendientes"] if p["vencido"]]
        proximos = [p for p in pendientes["pendientes"] if not p["vencido"] and p["dias_hasta_vencimiento"] <= 7]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Pendientes", pendientes["total_pendientes"])
        with col2:
            st.metric("⚠️ Vencidos", len(vencidos))
        with col3:
            st.metric("⏰ Próximos (7 días)", len(proximos))
        
        # Mostrar vencidos
        if vencidos:
            st.error("**Pagos Vencidos:**")
            for p in vencidos:
                st.write(f"- **{p['nombre']}**: ${p['monto']:,.2f} - Vencimiento: {p['fecha_vencimiento']} ({abs(p['dias_hasta_vencimiento'])} días de atraso)")
        
        # Mostrar próximos
        if proximos:
            st.warning("**Pagos Próximos (7 días):**")
            for p in proximos:
                st.write(f"- **{p['nombre']}**: ${p['monto']:,.2f} - Vencimiento: {p['fecha_vencimiento']} (en {p['dias_hasta_vencimiento']} días)")
    
    st.divider()
    
    # Resumen mensual
    st.subheader(f"📊 Resumen de {hoy.strftime('%B %Y')}")
    resumen = api_get(f"/reportes/resumen-mensual?mes={mes_actual}&anio={anio_actual}")
    
    if resumen:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Gastado", f"${resumen['total_gastado']:,.2f}")
        with col2:
            st.metric("Presupuesto Total", f"${resumen['total_presupuesto']:,.2f}")
        with col3:
            disponible = resumen['total_disponible']
            delta_color = "normal" if disponible >= 0 else "inverse"
            st.metric("Disponible", f"${disponible:,.2f}")
        
        # Tabla de categorías
        if resumen['categorias']:
            st.subheader("Por Categoría")
            df_categorias = pd.DataFrame(resumen['categorias'])
            df_categorias['categoria'] = df_categorias['categoria'].map(CATEGORIAS)
            
            st.dataframe(
                df_categorias[['categoria', 'gastado', 'presupuesto', 'disponible', 'porcentaje_usado']],
                hide_index=True,
                column_config={
                    "categoria": "Categoría",
                    "gastado": st.column_config.NumberColumn("Gastado", format="$%.2f"),
                    "presupuesto": st.column_config.NumberColumn("Presupuesto", format="$%.2f"),
                    "disponible": st.column_config.NumberColumn("Disponible", format="$%.2f"),
                    "porcentaje_usado": st.column_config.NumberColumn("% Usado", format="%.1f%%")
                }
            )


# ========== PÁGINA: BILLS ==========
def pagina_bills():
    """Gestión de bills/facturas recurrentes"""
    st.title("📄 Gestión de Bills")
    
    tab1, tab2 = st.tabs(["📋 Lista de Bills", "➕ Nueva Bill"])
    
    with tab1:
        # Listar bills
        bills = api_get("/bills?activo=true")
        
        if bills:
            st.subheader(f"Total de Bills Activas: {len(bills)}")
            
            for bill in bills:
                with st.expander(f"{CATEGORIAS[bill['categoria']]} - {bill['nombre']} - ${bill['monto']:,.2f}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Descripción:** {bill.get('descripcion', 'N/A')}")
                        st.write(f"**Monto:** ${bill['monto']:,.2f}")
                        st.write(f"**Categoría:** {CATEGORIAS[bill['categoria']]}")
                    
                    with col2:
                        st.write(f"**Frecuencia:** {FRECUENCIAS[bill['frecuencia']]}")
                        st.write(f"**Día de vencimiento:** {bill['dia_vencimiento']}")
                        st.write(f"**Estado:** {'✅ Activo' if bill['activo'] else '❌ Inactivo'}")
                    
                    # Botones de acción
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"🗑️ Eliminar", key=f"del_{bill['id']}"):
                            if api_delete(f"/bills/{bill['id']}"):
                                st.success("Bill eliminada")
                                st.rerun()
                    with col_btn2:
                        if st.button(f"⏸️ Desactivar", key=f"deact_{bill['id']}"):
                            if api_put(f"/bills/{bill['id']}", {"activo": False}):
                                st.success("Bill desactivada")
                                st.rerun()
        else:
            st.info("No hay bills registradas aún")
    
    with tab2:
        # Formulario para nueva bill
        st.subheader("Crear Nueva Bill")
        
        with st.form("form_nueva_bill"):
            nombre = st.text_input("Nombre *", placeholder="Ej: Netflix, Renta, Luz")
            descripcion = st.text_area("Descripción", placeholder="Detalles adicionales")
            
            col1, col2 = st.columns(2)
            with col1:
                monto = st.number_input("Monto *", min_value=0.01, step=0.01)
                categoria = st.selectbox("Categoría *", options=list(CATEGORIAS.keys()), format_func=lambda x: CATEGORIAS[x])
            
            with col2:
                frecuencia = st.selectbox("Frecuencia *", options=list(FRECUENCIAS.keys()), format_func=lambda x: FRECUENCIAS[x])
                dia_vencimiento = st.number_input("Día de vencimiento *", min_value=1, max_value=31, value=1)
            
            submitted = st.form_submit_button("💾 Guardar Bill")
            
            if submitted:
                if not nombre:
                    st.error("El nombre es obligatorio")
                else:
                    data = {
                        "nombre": nombre,
                        "descripcion": descripcion if descripcion else None,
                        "monto": monto,
                        "categoria": categoria,
                        "frecuencia": frecuencia,
                        "dia_vencimiento": dia_vencimiento,
                        "activo": True
                    }
                    
                    if api_post("/bills", data):
                        st.success(f"✅ Bill '{nombre}' creada exitosamente")
                        st.rerun()


# ========== PÁGINA: PAGOS ==========
def pagina_pagos():
    """Registro de pagos"""
    st.title("💳 Registro de Pagos")
    
    tab1, tab2 = st.tabs(["📋 Historial de Pagos", "➕ Registrar Pago"])
    
    with tab1:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            mes_filtro = st.selectbox("Mes", range(1, 13), index=date.today().month - 1, format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
        with col2:
            anio_filtro = st.number_input("Año", min_value=2020, max_value=2030, value=date.today().year)
        
        # Obtener pagos
        pagos = api_get(f"/pagos?mes={mes_filtro}&anio={anio_filtro}")
        
        if pagos:
            st.subheader(f"Total de Pagos: {len(pagos)}")
            
            # Crear DataFrame
            df_pagos = []
            for pago in pagos:
                bill = api_get(f"/bills/{pago['bill_id']}")
                if bill:
                    df_pagos.append({
                        "Fecha": pago['fecha_pago'],
                        "Bill": bill['nombre'],
                        "Categoría": CATEGORIAS[bill['categoria']],
                        "Monto": pago['monto_pagado'],
                        "Notas": pago.get('notas', '')
                    })
            
            if df_pagos:
                df = pd.DataFrame(df_pagos)
                st.dataframe(
                    df,
                    hide_index=True,
                    column_config={
                        "Monto": st.column_config.NumberColumn("Monto", format="$%.2f")
                    }
                )
                
                st.metric("Total Pagado", f"${df['Monto'].sum():,.2f}")
        else:
            st.info("No hay pagos registrados para este período")
    
    with tab2:
        # Formulario para registrar pago
        st.subheader("Registrar Nuevo Pago")
        
        # Obtener bills activas
        bills = api_get("/bills?activo=true")
        
        if bills:
            with st.form("form_nuevo_pago"):
                bill_options = {bill['id']: f"{bill['nombre']} - ${bill['monto']:,.2f}" for bill in bills}
                bill_id = st.selectbox("Bill *", options=list(bill_options.keys()), format_func=lambda x: bill_options[x])
                
                col1, col2 = st.columns(2)
                with col1:
                    fecha_pago = st.date_input("Fecha de pago *", value=date.today())
                with col2:
                    # Pre-llenar con el monto de la bill seleccionada
                    bill_seleccionada = next((b for b in bills if b['id'] == bill_id), None)
                    monto_default = bill_seleccionada['monto'] if bill_seleccionada else 0.0
                    monto_pagado = st.number_input("Monto pagado *", min_value=0.01, value=monto_default, step=0.01)
                
                notas = st.text_area("Notas", placeholder="Información adicional sobre el pago")
                
                submitted = st.form_submit_button("💾 Registrar Pago")
                
                if submitted:
                    data = {
                        "bill_id": bill_id,
                        "fecha_pago": fecha_pago.isoformat(),
                        "monto_pagado": monto_pagado,
                        "notas": notas if notas else None
                    }
                    
                    if api_post("/pagos", data):
                        st.success("✅ Pago registrado exitosamente")
                        st.rerun()
        else:
            st.warning("⚠️ No hay bills activas. Crea una bill primero en la sección 'Bills'.")


# ========== PÁGINA: PRESUPUESTOS ==========
def pagina_presupuestos():
    """Gestión de presupuestos mensuales"""
    st.title("💵 Gestión de Presupuestos")
    
    tab1, tab2 = st.tabs(["📋 Presupuestos Actuales", "➕ Nuevo Presupuesto"])
    
    with tab1:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            mes_filtro = st.selectbox("Mes", range(1, 13), index=date.today().month - 1, format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
        with col2:
            anio_filtro = st.number_input("Año", min_value=2020, max_value=2030, value=date.today().year)
        
        # Obtener presupuestos
        presupuestos = api_get(f"/presupuestos?mes={mes_filtro}&anio={anio_filtro}")
        
        if presupuestos:
            st.subheader(f"Presupuestos para {datetime(anio_filtro, mes_filtro, 1).strftime('%B %Y')}")
            
            df_presupuestos = pd.DataFrame(presupuestos)
            df_presupuestos['categoria'] = df_presupuestos['categoria'].map(CATEGORIAS)
            
            st.dataframe(
                df_presupuestos[['categoria', 'monto_limite']],
                hide_index=True,
                column_config={
                    "categoria": "Categoría",
                    "monto_limite": st.column_config.NumberColumn("Límite", format="$%.2f")
                }
            )
            
            st.metric("Presupuesto Total", f"${df_presupuestos['monto_limite'].sum():,.2f}")
        else:
            st.info("No hay presupuestos definidos para este período")
    
    with tab2:
        # Formulario para nuevo presupuesto
        st.subheader("Definir Nuevo Presupuesto")
        
        with st.form("form_nuevo_presupuesto"):
            col1, col2 = st.columns(2)
            with col1:
                mes = st.selectbox("Mes *", range(1, 13), format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
                anio = st.number_input("Año *", min_value=2020, max_value=2030, value=date.today().year)
            
            with col2:
                categoria = st.selectbox("Categoría *", options=list(CATEGORIAS.keys()), format_func=lambda x: CATEGORIAS[x])
                monto_limite = st.number_input("Monto límite *", min_value=0.01, step=0.01)
            
            submitted = st.form_submit_button("💾 Guardar Presupuesto")
            
            if submitted:
                data = {
                    "mes": mes,
                    "anio": anio,
                    "categoria": categoria,
                    "monto_limite": monto_limite
                }
                
                if api_post("/presupuestos", data):
                    st.success("✅ Presupuesto creado exitosamente")
                    st.rerun()


# ========== PÁGINA: GRÁFICAS ==========
def pagina_graficas():
    """Visualizaciones y gráficas"""
    st.title("📊 Gráficas y Análisis")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        mes_filtro = st.selectbox("Mes", range(1, 13), index=date.today().month - 1, format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
    with col2:
        anio_filtro = st.number_input("Año", min_value=2020, max_value=2030, value=date.today().year)
    
    # Obtener datos
    gastos_data = api_get(f"/reportes/gastos-categoria?mes={mes_filtro}&anio={anio_filtro}")
    
    if gastos_data and gastos_data['por_categoria']:
        # Gráfica de pastel
        st.subheader("Distribución de Gastos por Categoría")
        
        df_gastos = pd.DataFrame([
            {"Categoría": CATEGORIAS[cat], "Monto": monto}
            for cat, monto in gastos_data['por_categoria'].items()
        ])
        
        fig_pie = px.pie(
            df_gastos,
            values='Monto',
            names='Categoría',
            title=f"Gastos de {datetime(anio_filtro, mes_filtro, 1).strftime('%B %Y')}"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Gráfica de barras
        st.subheader("Gastos por Categoría")
        fig_bar = px.bar(
            df_gastos,
            x='Categoría',
            y='Monto',
            title="Comparación de Gastos",
            labels={'Monto': 'Monto ($)'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Comparación con presupuesto
        st.subheader("Comparación: Gastos vs Presupuesto")
        presupuestos = api_get(f"/presupuestos?mes={mes_filtro}&anio={anio_filtro}")
        
        if presupuestos:
            df_comparacion = []
            for cat, gasto in gastos_data['por_categoria'].items():
                presupuesto = next((p['monto_limite'] for p in presupuestos if p['categoria'] == cat), 0)
                df_comparacion.append({
                    "Categoría": CATEGORIAS[cat],
                    "Gastado": gasto,
                    "Presupuesto": presupuesto
                })
            
            df_comp = pd.DataFrame(df_comparacion)
            
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(name='Gastado', x=df_comp['Categoría'], y=df_comp['Gastado']))
            fig_comp.add_trace(go.Bar(name='Presupuesto', x=df_comp['Categoría'], y=df_comp['Presupuesto']))
            fig_comp.update_layout(barmode='group', title='Gastos vs Presupuesto')
            
            st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("No hay datos de gastos para este período")


# ========== MENÚ PRINCIPAL ==========
def main():
    """Función principal"""
    st.sidebar.title("📱 Menú")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio(
        "Navegación",
        ["Dashboard", "Bills", "Pagos", "Presupuestos", "Gráficas"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip:** Asegúrate de que el backend esté corriendo en http://localhost:8000")
    
    # Verificar conexión con API
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            st.sidebar.success("✅ Conectado al backend")
        else:
            st.sidebar.error("❌ Error de conexión")
    except:
        st.sidebar.error("❌ Backend no disponible")
    
    # Renderizar página seleccionada
    if menu == "Dashboard":
        pagina_dashboard()
    elif menu == "Bills":
        pagina_bills()
    elif menu == "Pagos":
        pagina_pagos()
    elif menu == "Presupuestos":
        pagina_presupuestos()
    elif menu == "Gráficas":
        pagina_graficas()


if __name__ == "__main__":
    main()
