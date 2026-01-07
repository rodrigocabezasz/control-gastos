import sqlite3

conn = sqlite3.connect('control_gastos.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(reminders)')
print('Columnas de la tabla reminders:')
for row in cursor.fetchall():
    print(f'  {row[1]}: {row[2]}')
conn.close()
