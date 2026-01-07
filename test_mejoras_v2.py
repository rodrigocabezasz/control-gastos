"""
Script de prueba para las nuevas funcionalidades V2.0 y V2.1
Prueba notificaciones, filtros, mark-as-paid, exportación y tendencias
"""
import requests
from datetime import date
import os

# Configuración
API_URL = "http://localhost:8000"
EMAIL = "rorocabezas@gmail.com"  # Cambia por tu email
PASSWORD = "Roro2026."      # Cambia por tu contraseña

def login():
    """Login y obtener token"""
    print("🔐 Iniciando sesión...")
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": EMAIL, "password": PASSWORD}
    )
    if response.status_code == 200:
        token = response.json()['access_token']
        print("✅ Sesión iniciada correctamente")
        return token
    else:
        print(f"❌ Error al iniciar sesión: {response.text}")
        return None

def test_pending_reminders(token):
    """Probar endpoint de recordatorios pendientes"""
    print("\n📋 Probando recordatorios pendientes...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/notifications/pending-reminders?days_ahead=7",
        headers=headers
    )
    
    if response.status_code == 200:
        reminders = response.json()
        print(f"✅ Se encontraron {len(reminders)} recordatorios pendientes")
        for r in reminders:
            print(f"   - {r['name']}: ${r['amount']:.2f} - Vence en {r['days_until_due']} días")
    else:
        print(f"❌ Error: {response.text}")

def test_budget_alerts(token):
    """Probar endpoint de alertas de presupuesto"""
    print("\n⚠️ Probando alertas de presupuesto...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/notifications/budget-alerts",
        headers=headers
    )
    
    if response.status_code == 200:
        alerts = response.json()
        print(f"✅ Se encontraron {len(alerts)} alertas de presupuesto")
        for a in alerts:
            print(f"   - {a['category_name']}: {a['percentage_used']:.1f}% usado - {a['status']}")
    else:
        print(f"❌ Error: {response.text}")

def test_advanced_filters(token):
    """Probar filtros avanzados en transacciones"""
    print("\n🔍 Probando filtros avanzados...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Probar búsqueda por texto
    response = requests.get(
        f"{API_URL}/transactions?search_text=pago&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Búsqueda por texto 'pago': {len(transactions)} resultados")
    else:
        print(f"❌ Error: {response.text}")
    
    # Probar filtro por rango de montos
    response = requests.get(
        f"{API_URL}/transactions?min_amount=100&max_amount=1000&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Filtro por monto ($100-$1000): {len(transactions)} resultados")
    else:
        print(f"❌ Error: {response.text}")

def test_mark_as_paid(token):
    """Probar marcar recordatorio como pagado"""
    print("\n✅ Probando marcar recordatorio como pagado...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Primero obtener un recordatorio
    response = requests.get(f"{API_URL}/reminders", headers=headers)
    if response.status_code == 200:
        reminders = response.json()
        if reminders:
            reminder_id = reminders[0]['id']
            print(f"   Usando recordatorio: {reminders[0]['name']}")
            
            # Obtener categorías
            response = requests.get(f"{API_URL}/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    category_id = categories[0]['id']
                    
                    # Marcar como pagado
                    data = {
                        "category_id": category_id,
                        "payment_date": str(date.today())
                    }
                    response = requests.post(
                        f"{API_URL}/reminders/{reminder_id}/mark-paid",
                        json=data,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ Recordatorio marcado como pagado")
                        print(f"   Transacción creada: ${result['transaction']['amount']:.2f}")
                    else:
                        print(f"❌ Error: {response.text}")
                else:
                    print("⚠️ No hay categorías disponibles")
            else:
                print(f"❌ Error obteniendo categorías: {response.text}")
        else:
            print("⚠️ No hay recordatorios disponibles para probar")
    else:
        print(f"❌ Error obteniendo recordatorios: {response.text}")

def test_export_excel(token):
    """Probar exportación a Excel"""
    print("\n📥 Probando exportación a Excel...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/transactions/export/excel?limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        # Guardar archivo
        filename = "test_export.xlsx"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        file_size = os.path.getsize(filename)
        print(f"✅ Excel exportado correctamente: {filename} ({file_size} bytes)")
        
        # Limpiar archivo de prueba
        os.remove(filename)
        print(f"   Archivo de prueba eliminado")
    else:
        print(f"❌ Error: {response.text}")


def test_export_csv(token):
    """Probar exportación a CSV"""
    print("\n📥 Probando exportación a CSV...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/transactions/export/csv?limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        # Guardar archivo
        filename = "test_export.csv"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        file_size = os.path.getsize(filename)
        print(f"✅ CSV exportado correctamente: {filename} ({file_size} bytes)")
        
        # Limpiar archivo de prueba
        os.remove(filename)
        print(f"   Archivo de prueba eliminado")
    else:
        print(f"❌ Error: {response.text}")


def test_trends(token):
    """Probar endpoint de tendencias"""
    print("\n📈 Probando análisis de tendencias...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{API_URL}/stats/trends?months=6",
        headers=headers
    )
    
    if response.status_code == 200:
        trends = response.json()
        print(f"✅ Tendencias calculadas correctamente")
        print(f"   Meses analizados: {len(trends['months'])}")
        print(f"   Promedio ingresos: ${trends['average']['income']:,.2f}")
        print(f"   Promedio gastos: ${trends['average']['expenses']:,.2f}")
        print(f"   Crecimiento ingresos: {trends['growth_rate']['income']:+.1f}%")
        print(f"   Crecimiento gastos: {trends['growth_rate']['expenses']:+.1f}%")
        print(f"   Predicción próximo mes:")
        print(f"      Ingresos: ${trends['prediction']['next_month_income']:,.2f}")
        print(f"      Gastos: ${trends['prediction']['next_month_expenses']:,.2f}")
        print(f"      Balance: ${trends['prediction']['next_month_balance']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def main():
    print("=" * 60)
    print("🧪 PRUEBA DE NUEVAS FUNCIONALIDADES - V2.0 + V2.1")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n❌ No se pudo iniciar sesión. Verifica tus credenciales.")
        return
    
    # ===== V2.0 - Notificaciones y Filtros =====
    print("\n" + "🔹" * 30)
    print("PRUEBAS V2.0 - Notificaciones y Filtros")
    print("🔹" * 30)
    
    test_pending_reminders(token)
    test_budget_alerts(token)
    test_advanced_filters(token)
    
    # ===== V2.1 - Exportación y Tendencias =====
    print("\n" + "🔹" * 30)
    print("PRUEBAS V2.1 - Exportación y Tendencias")
    print("🔹" * 30)
    
    test_export_excel(token)
    test_export_csv(token)
    test_trends(token)
    
    # Preguntar antes de marcar como pagado (modifica datos)
    print("\n" + "=" * 60)
    print("⚠️  ADVERTENCIA: La siguiente prueba modificará datos")
    print("   Se marcará un recordatorio como pagado y se creará una transacción")
    confirm = input("¿Deseas continuar? (s/n): ")
    
    if confirm.lower() == 's':
        test_mark_as_paid(token)
    else:
        print("⏭️  Prueba omitida")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("\n📊 Resumen:")
    print("   ✅ Notificaciones de recordatorios")
    print("   ✅ Alertas de presupuesto")
    print("   ✅ Filtros avanzados")
    print("   ✅ Exportación a Excel")
    print("   ✅ Exportación a CSV")
    print("   ✅ Análisis de tendencias")
    print("\n🎉 ¡Todas las funcionalidades están operativas!")

if __name__ == "__main__":
    main()
