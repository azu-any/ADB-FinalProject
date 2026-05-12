import os
import pandas as pd
import psycopg2
import json
from preprocessing import TextPreprocessor
from collections import Counter


class FrequencyAnalyzer:
    def __init__(self, db_config=None):
        self.db_config = db_config
        self.preprocessor = TextPreprocessor()

    def get_connection(self):
        if not self.db_config:
            return None
        return psycopg2.connect(**self.db_config)

    def run(self, docs_dir="data/documents", output_dir="results", metadata_path=None):
        os.makedirs(output_dir, exist_ok=True)
        
        # Load metadata if provided
        metadata = {}
        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            print(f"✅ Metadata loaded from {metadata_path}")

        doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')]
        all_freqs = {}
        doc_id_map = {}

        print("🔄 Procesando documentos...\n")
        for i, filename in enumerate(sorted(doc_files), 1):
            with open(os.path.join(docs_dir, filename), 'r', encoding='utf-8') as f:
                text = f.read()
            tokens = self.preprocessor.preprocess(text)
            all_freqs[filename] = Counter(tokens)
            doc_id_map[filename] = i
            print(f"✅ {filename} → {len(tokens)} tokens")

        # 1. Tabla Global Ancha (como la del profesor)
        self.create_global_wide_matrix(all_freqs, output_dir)

        # 2. Tabla Global Larga ordenada por término
        self.create_global_long_table(all_freqs, doc_id_map, output_dir)

        # 3. Tablas individuales por documento con TODOS los términos
        self.create_per_document_full_tables(all_freqs, output_dir)

        # 4. Gráficas Luhn
        self.generate_luhn_graphs(all_freqs, output_dir)

        # 5. Guardar en Base de Datos (para LSI)
        if self.db_config:
            self.save_to_db(all_freqs, doc_id_map, docs_dir, metadata)

        print(f"\n🎉 ¡Todo generado correctamente!")

    def save_to_db(self, all_freqs, doc_id_map, docs_dir, metadata):
        conn = self.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        print("\n🗄️ Indexando en base de datos...")
        try:
            # Limpiar datos previos
            cursor.execute("TRUNCATE TABLE has, lsi_vectors, term, query, text, document CASCADE")
            
            # Insertar documentos
            for filename, doc_id in doc_id_map.items():
                with open(os.path.join(docs_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Default values from filename
                title = filename.replace('.txt', '').replace('_', ' ').capitalize()
                author = filename.split('-')[0].capitalize() if '-' in filename else "Unknown"
                publish_date = None
                
                # Override with metadata if available
                # Check both exact filename and filename without extension
                meta_key = filename
                if meta_key not in metadata and meta_key.endswith('.txt'):
                    meta_key = meta_key[:-4]
                
                if filename in metadata or meta_key in metadata:
                    file_meta = metadata.get(filename, metadata.get(meta_key))
                    title = file_meta.get('title', title)
                    author = file_meta.get('author', author)
                    publish_date = file_meta.get('date', publish_date)
                    
                    # Ensure publish_date is in valid format for PostgreSQL (YYYY-MM-DD)
                    # If it's just a year "2020", convert to "2020-01-01"
                    if publish_date and len(str(publish_date)) == 4 and str(publish_date).isdigit():
                        publish_date = f"{publish_date}-01-01"
                    elif not publish_date:
                        publish_date = None

                # Insertar en document (Superclase)
                cursor.execute("INSERT INTO document (id) VALUES (%s)", (doc_id,))
                
                # Insertar en text (Subclase)
                cursor.execute(
                    "INSERT INTO text (id, url, title, author, date, content) VALUES (%s, %s, %s, %s, %s, %s)",
                    (doc_id, filename, title, author, publish_date, content)
                )
            
            # Insertar términos
            all_terms = sorted(set(term for freq in all_freqs.values() for term in freq.keys()))
            from psycopg2.extras import execute_values
            
            print("   📤 Insertando términos...")
            term_data = [(t,) for t in all_terms]
            execute_values(cursor, "INSERT INTO term (name) VALUES %s ON CONFLICT DO NOTHING", term_data)
                
            print("   📤 Subiendo matriz de frecuencias (HAS)...")
            matrix_data = []
            for filename, freq in all_freqs.items():
                doc_id = doc_id_map[filename]
                for term, count in freq.items():
                    matrix_data.append((doc_id, term, count))
            
            execute_values(cursor, "INSERT INTO has (document_id, term_name, frequency) VALUES %s", matrix_data)
            
            conn.commit()
            print("✅ Base de datos actualizada")
        except Exception as e:
            print(f"❌ Error DB: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def create_global_wide_matrix(self, all_freqs, output_dir):
        all_terms = sorted(set(term for freq in all_freqs.values() for term in freq.keys()))
        docs = sorted(all_freqs.keys())
        doc_names = [d.replace('.txt', '')[:12] for d in docs]

        data = []
        for term in all_terms:
            row = [term]
            for doc in docs:
                row.append(all_freqs[doc].get(term, 0))
            data.append(row)

        df = pd.DataFrame(data, columns=['Term'] + doc_names)
        df.to_csv(f"{output_dir}/global_wide_matrix.csv", index=False)
        print("📊 Tabla Global Ancha creada")

    def create_global_long_table(self, all_freqs, doc_id_map, output_dir):
        """Ordenada por término"""
        data = []
        all_terms = sorted(set(term for freq in all_freqs.values() for term in freq.keys()))

        for term in all_terms:
            for filename in sorted(all_freqs.keys()):
                count = all_freqs[filename].get(term, 0)
                if count > 0:
                    data.append({
                        'term': term,
                        'doc_id': doc_id_map[filename],
                        'frequency': count
                    })

        df = pd.DataFrame(data)
        df.to_csv(f"{output_dir}/global_long_table.csv", index=False)
        print("📊 Tabla Global Larga ordenada por término creada")

    def create_per_document_full_tables(self, all_freqs, output_dir):
        """Cada documento con TODOS los términos"""
        all_terms = sorted(set(term for freq in all_freqs.values() for term in freq.keys()))

        for filename, freq in all_freqs.items():
            data = []
            for term in all_terms:
                count = freq.get(term, 0)
                data.append({
                    'term': term,
                    'frequency': count,
                    'present': 1 if count > 0 else 0
                })

            df = pd.DataFrame(data)
            safe_name = filename.replace('.txt', '')[:30]
            df.to_csv(f"{output_dir}/per_doc_{safe_name}.csv", index=False)
            print(f"   📋 Tabla completa para: {safe_name}")

    def generate_luhn_graphs(self, all_freqs, output_dir):
        import matplotlib.pyplot as plt
        for filename, freq in all_freqs.items():
            if len(freq) < 5: continue
            sorted_freq = sorted(freq.values(), reverse=True)
            plt.figure(figsize=(12, 7))
            plt.plot(range(1, len(sorted_freq) + 1), sorted_freq, 'b-', linewidth=2.5)
            plt.title(f'Luhn Curve - {filename.replace(".txt", "")}')
            plt.xlabel('Ordered terms rank (R)')
            plt.ylabel('Term frequency (F)')
            plt.grid(True, alpha=0.3)
            plt.axvline(x=20, color='green', linestyle='--', label='Upper bound')
            plt.axvline(x=len(sorted_freq) // 2, color='red', linestyle='--', label='Lower bound')
            plt.legend()
            safe = filename.replace('.txt', '')
            plt.savefig(f"{output_dir}/{safe}_luhn.png", dpi=300, bbox_inches='tight')
            plt.close()


if __name__ == "__main__":
    analyzer = FrequencyAnalyzer()
    analyzer.run()
