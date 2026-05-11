import psycopg2
from config import DB_CONFIG

def create_represent_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("Creating 'Represent' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Represent (
                term VARCHAR(255) NOT NULL,
                synonym VARCHAR(255) NOT NULL,
                PRIMARY KEY (term, synonym)
            );
        """)
        
        # Add some initial common synonyms for testing
        synonyms = [
            ('water', 'h2o'),
            ('climate', 'weather'),
            ('energy', 'power'),
            ('solar', 'photovoltaic'),
            ('renewable', 'sustainable'),
            ('urban', 'city'),
            ('co2', 'carbon'),
            ('forest', 'wood')
        ]
        
        print("Inserting initial synonyms...")
        for term, syn in synonyms:
            cursor.execute(
                "INSERT INTO Represent (term, synonym) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (term, syn)
            )
            # Also insert reverse for bidirectional mapping
            cursor.execute(
                "INSERT INTO Represent (term, synonym) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (syn, term)
            )
            
        conn.commit()
        print("✅ 'Represent' table ready with initial data.")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_represent_table()
