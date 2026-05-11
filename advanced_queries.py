import psycopg2
from config import DB_CONFIG
import math

def advanced_queries():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("🔍 CONSULTAS AVANZADAS - LSI Document Base\n")

    # 1. Euclidean Distance (como en el PDF del profesor)
    print("📐 1. Euclidean Distance entre documentos (versión simplificada):")
    cursor.execute("""
        SELECT 
            d1.title as doc1,
            d2.title as doc2,
            sqrt(sum(pow(td1.frequency - td2.frequency, 2))) as euclidean_distance
        FROM term_document_matrix td1
        JOIN term_document_matrix td2 ON td1.term_id = td2.term_id
        JOIN documents d1 ON td1.doc_id = d1.id
        JOIN documents d2 ON td2.doc_id = d2.id
        WHERE d1.id < d2.id
        GROUP BY d1.title, d2.title
        ORDER BY euclidean_distance ASC
        LIMIT 8;
    """)
    for row in cursor.fetchall():
        print(f"   {row[0][:35]:35} ↔ {row[1][:35]:35} = {row[2]:.2f}")

    # 2. Documentos más similares (por términos en común)
    print("\n🔗 2. Documentos más similares (más términos en común):")
    cursor.execute("""
        SELECT 
            d1.title as doc1,
            d2.title as doc2,
            COUNT(*) as common_terms
        FROM term_document_matrix td1
        JOIN term_document_matrix td2 ON td1.term_id = td2.term_id
        JOIN documents d1 ON td1.doc_id = d1.id
        JOIN documents d2 ON td2.doc_id = d2.id
        WHERE d1.id < d2.id
        GROUP BY d1.title, d2.title
        ORDER BY common_terms DESC
        LIMIT 8;
    """)
    for row in cursor.fetchall():
        print(f"   {row[0][:40]:40} ↔ {row[1][:40]:40} → {row[2]} términos en común")

    # 3. Top términos más frecuentes globales
    print("\n🔥 3. Top 15 términos más frecuentes en toda la colección:")
    cursor.execute("""
        SELECT t.term, SUM(td.frequency) as total_freq
        FROM term_document_matrix td
        JOIN terms t ON td.term_id = t.id
        GROUP BY t.term
        ORDER BY total_freq DESC
        LIMIT 15;
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:20} → {row[1]} veces")

    # 4. Documento más relevante para una consulta (ejemplo)
    print("\n🔎 4. Documentos más relevantes para 'water scarcity climate change':")
    cursor.execute("""
        SELECT d.title, SUM(td.frequency) as relevance
        FROM term_document_matrix td
        JOIN terms t ON td.term_id = t.id
        JOIN documents d ON td.doc_id = d.id
        WHERE t.term IN ('water', 'scarcity', 'climat', 'chang', 'crisi')
        GROUP BY d.title
        ORDER BY relevance DESC
        LIMIT 5;
    """)
    for row in cursor.fetchall():
        print(f"   • {row[1]:3} → {row[0]}")

    cursor.close()
    conn.close()
    print("\n✅ Consultas avanzadas completadas!")

if __name__ == "__main__":
    advanced_queries()
