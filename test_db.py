import psycopg2
from config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM documents")
print("Documentos:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM terms")
print("Términos únicos:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM term_document_matrix")
print("Registros en Frequency Matrix:", cursor.fetchone()[0])

cursor.close()
conn.close()
print("✅ Conexión a Supabase OK")
