import psycopg2
from config import DB_CONFIG

def rebuild():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("Dropping old tables...")
    cursor.execute("""
        DROP TABLE IF EXISTS query_results CASCADE;
        DROP TABLE IF EXISTS term_document_matrix CASCADE;
        DROP TABLE IF EXISTS lsi_vectors CASCADE;
        DROP TABLE IF EXISTS svd_model CASCADE;
        DROP TABLE IF EXISTS terms CASCADE;
        DROP TABLE IF EXISTS document CASCADE;
        DROP TABLE IF EXISTS documents CASCADE;
        DROP TABLE IF EXISTS Represent CASCADE;
        
        -- Drop new ones if they exist
        DROP TABLE IF EXISTS has CASCADE;
        DROP TABLE IF EXISTS word CASCADE;
        DROP TABLE IF EXISTS term CASCADE;
        DROP TABLE IF EXISTS query CASCADE;
        DROP TABLE IF EXISTS text CASCADE;
    """)

    print("Creating new schema...")
    
    # 1. document (Superclass)
    cursor.execute("""
        CREATE TABLE document (
            id SERIAL PRIMARY KEY
        )
    """)

    # 2. text (Subclass)
    cursor.execute("""
        CREATE TABLE text (
            id INTEGER PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
            url VARCHAR(255),
            title VARCHAR(255),
            author VARCHAR(255),
            date DATE,
            content TEXT
        )
    """)

    # 3. query (Subclass)
    cursor.execute("""
        CREATE TABLE query (
            id INTEGER PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
            label TEXT NOT NULL
        )
    """)

    # 4. term
    cursor.execute("""
        CREATE TABLE term (
            name VARCHAR(255) PRIMARY KEY
        )
    """)

    # 5. has (Frequency matrix)
    cursor.execute("""
        CREATE TABLE has (
            document_id INTEGER REFERENCES document(id) ON DELETE CASCADE,
            term_name VARCHAR(255) REFERENCES term(name) ON DELETE CASCADE,
            frequency REAL NOT NULL,
            PRIMARY KEY (document_id, term_name)
        )
    """)

    # 6. word
    cursor.execute("""
        CREATE TABLE word (
            word VARCHAR(255) PRIMARY KEY
        )
    """)

    # 7. represent (Synonyms)
    cursor.execute("""
        CREATE TABLE represent (
            term_name VARCHAR(255) REFERENCES term(name) ON DELETE CASCADE,
            word VARCHAR(255) REFERENCES word(word) ON DELETE CASCADE,
            PRIMARY KEY (term_name, word)
        )
    """)

    # Legacy required tables for LSI and Tracing
    cursor.execute("""
        CREATE TABLE svd_model (
            name VARCHAR(50) PRIMARY KEY,
            data JSON
        )
    """)
    cursor.execute("""
        CREATE TABLE lsi_vectors (
            doc_id INTEGER PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
            vector JSONB NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE query_results (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            metric VARCHAR(50) NOT NULL,
            top_n INTEGER NOT NULL,
            results JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Schema rebuilt successfully!")

if __name__ == "__main__":
    rebuild()
