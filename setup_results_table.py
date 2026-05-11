import psycopg2
from config import DB_CONFIG

def create_query_results_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("Creating 'query_results' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_results (
                id SERIAL PRIMARY KEY,
                query_text TEXT NOT NULL,
                metric VARCHAR(50) NOT NULL,
                top_n INTEGER NOT NULL,
                results JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("✅ 'query_results' table created successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_query_results_table()
