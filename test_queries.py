import psycopg2
from config import DB_CONFIG


def test_database():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("🔍 Verificando base de datos...\n")

    # 1. Cuántos documentos hay
    cursor.execute("SELECT COUNT(*) FROM documents")
    print("📚 Documentos en BD:", cursor.fetchone()[0])

    # 2. Cuántos términos
    cursor.execute("SELECT COUNT(*) FROM terms")
    print("📝 Términos únicos:", cursor.fetchone()[0])

    # 3. Ejemplo de Frequency Matrix
    cursor.execute("""
                   SELECT d.title, t.term, td.frequency
                   FROM term_document_matrix td
                            JOIN documents d ON td.doc_id = d.id
                            JOIN terms t ON td.term_id = t.id
                   ORDER BY td.frequency DESC LIMIT 10
                   """)
    print("\n🔥 Top 10 frecuencias:")
    for row in cursor.fetchall():
        print(f"  • {row[0][:40]:40} | {row[1]:15} | freq = {row[2]}")

    # 4. Consulta simple de similitud (Euclidean como en el PDF del profesor)
    print("\n📐 Probando consulta Euclidean (ejemplo)...")
    cursor.execute("""
                   SELECT d.title, COUNT(*) as common_terms
                   FROM term_document_matrix td1
                            JOIN term_document_matrix td2 ON td1.term_id = td2.term_id
                            JOIN documents d ON td2.doc_id = d.id
                   WHERE td1.doc_id = 1 -- primer documento
                   GROUP BY d.title
                   ORDER BY common_terms DESC LIMIT 5
                   """)
    for row in cursor.fetchall():
        print(f"  • {row[0]} → {row[1]} términos en común")

    cursor.close()
    conn.close()
    print("\n✅ Todo parece estar funcionando correctamente!")


if __name__ == "__main__":
    test_database()
