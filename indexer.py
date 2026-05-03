import os
import json
import mysql.connector
from preprocessing import TextPreprocessor

class Indexer:
    def __init__(self, db_config):
        self.db_config = db_config
        self.preprocessor = TextPreprocessor()

    def get_connection(self):
        return mysql.connector.connect(**self.db_config)

    def initialize_db(self, schema_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        with open(schema_path, 'r') as f:
            schema = f.read()
            # Split schema into individual commands
            for command in schema.split(';'):
                if command.strip():
                    cursor.execute(command)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized.")

    def index_documents(self, docs_dir, metadata_file=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Load metadata if provided
        metadata = {}
        if metadata_file and os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        # 1. Clear existing data
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE term_document_matrix")
        cursor.execute("TRUNCATE TABLE terms")
        cursor.execute("TRUNCATE TABLE documents")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')]
        
        all_terms = set()
        doc_data = []

        for filename in doc_files:
            file_path = os.path.join(docs_dir, filename)
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Get metadata from JSON or fallback
                meta = metadata.get(filename, {})
                title = meta.get('title', filename.replace('.txt', '').replace('_', ' ').capitalize())
                author = meta.get('author', 'Unknown')
                publish_date = meta.get('date', None)
                
                # Insert document with metadata
                cursor.execute(
                    "INSERT INTO documents (title, author, publish_date, file_path, content) VALUES (%s, %s, %s, %s, %s)", 
                    (title, author, publish_date, filename, content)
                )
                doc_id = cursor.lastrowid
                
                tokens = self.preprocessor.preprocess(content)
                
                # Count frequencies
                freq_map = {}
                for token in tokens:
                    freq_map[token] = freq_map.get(token, 0) + 1
                    all_terms.add(token)
                
                doc_data.append((doc_id, freq_map))

        # 2. Insert terms and get IDs
        term_to_id = {}
        for term in all_terms:
            cursor.execute("INSERT INTO terms (term) VALUES (%s)", (term,))
            term_to_id[term] = cursor.lastrowid

        # 3. Insert frequencies (Frequency Matrix FrecT)
        for doc_id, freq_map in doc_data:
            for term, freq in freq_map.items():
                term_id = term_to_id[term]
                cursor.execute(
                    "INSERT INTO term_document_matrix (term_id, doc_id, frequency) VALUES (%s, %s, %s)",
                    (term_id, doc_id, freq)
                )

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Indexed {len(doc_files)} documents and {len(all_terms)} terms.")

if __name__ == "__main__":
    # Example usage (adjust credentials)
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "", # Add password if needed
        "database": "lsi_project"
    }
    
    indexer = Indexer(db_config)
    # indexer.initialize_db('schema.sql')
    # indexer.index_documents('data/documents')
