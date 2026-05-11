import os
import pandas as pd
from preprocessing import TextPreprocessor
from collections import Counter


class FrequencyAnalyzer:
    def __init__(self):
        self.preprocessor = TextPreprocessor()

    def run(self, docs_dir="data/documents", output_dir="results"):
        os.makedirs(output_dir, exist_ok=True)

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

        print(f"\n🎉 ¡Todo generado correctamente en carpeta 'results'!")

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
