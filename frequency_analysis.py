import os
from collections import Counter
import matplotlib.pyplot as plt
import pandas as pd
from preprocessing import TextPreprocessor


class FrequencyAnalyzer:
    def __init__(self):
        self.preprocessor = TextPreprocessor()

    def analyze_all_documents(self, docs_dir="data/documents", output_dir="results"):
        os.makedirs(output_dir, exist_ok=True)

        print("🔄 Procesando documentos...\n")
        all_freqs = {}

        doc_files = [f for f in os.listdir(docs_dir) if f.endswith('.txt')]

        for filename in sorted(doc_files):
            doc_path = os.path.join(docs_dir, filename)
            with open(doc_path, 'r', encoding='utf-8') as f:
                text = f.read()

            tokens = self.preprocessor.preprocess(text)
            all_freqs[filename] = Counter(tokens)
            print(f"✅ {filename}: {len(tokens)} tokens")

        # Generar archivos
        self.create_term_document_matrix(all_freqs, output_dir)
        self.generate_luhn_graphs(all_freqs, output_dir)

        print(f"\n🎉 ¡Listo! Revisa la carpeta: **{output_dir}**")

    def create_term_document_matrix(self, all_freqs, output_dir):
        all_terms = set()
        for freq in all_freqs.values():
            all_terms.update(freq.keys())

        terms = sorted(list(all_terms))
        docs = sorted(all_freqs.keys())
        doc_names = [d.replace('.txt', '')[:15] for d in docs]

        data = []
        for term in terms:
            row = [term]
            for doc in docs:
                row.append(all_freqs[doc].get(term, 0))
            data.append(row)

        df = pd.DataFrame(data, columns=['Term'] + doc_names)

        # Guardar archivos
        df.to_csv(f"{output_dir}/term_document_matrix.csv", index=False)

        try:
            df.to_excel(f"{output_dir}/term_document_matrix.xlsx", index=False)
            print("📊 Archivo EXCEL creado: term_document_matrix.xlsx")
        except Exception as e:
            print("⚠️ No se pudo crear Excel (pero sí el CSV)")

        print(f"📋 Tabla completa creada con {len(terms)} términos y {len(docs)} documentos")

    def generate_luhn_graphs(self, all_freqs, output_dir):
        for filename, freq in all_freqs.items():
            if len(freq) < 5:
                continue
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

            safe_name = filename.replace('.txt', '')
            plt.savefig(f"{output_dir}/{safe_name}_luhn.png", dpi=300, bbox_inches='tight')
            plt.close()
            print(f"   📈 Gráfica: {safe_name}_luhn.png")


if __name__ == "__main__":
    analyzer = FrequencyAnalyzer()
    analyzer.analyze_all_documents()
