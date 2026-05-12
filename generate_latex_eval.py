import os
import numpy as np
from config import DB_CONFIG
from query_engine import QueryEngine

def generate_latex_table(query, raw_results, lsi_results):
    print(f"\\subsubsection*{{Test Query: ``{query}''}}")
    print("\\begin{table}[H]")
    print("    \\centering")
    print("    \\begin{tabular}{|p{2cm}|p{8cm}|c|}")
    print("    \\hline")
    print("    \\textbf{Retrieval Mode} & \\textbf{Top Result Title} & \\textbf{Score} \\\\ \\hline")
    
    # Process Top 2 Raw Results
    for i, res in enumerate(raw_results[:2]):
        doc_id, title, author, score = res
        # Format score
        score_str = f"{score:.4f}" if isinstance(score, (float, np.float64)) else str(score)
        mode = "Raw TF" if i == 0 else ""
        print(f"    {mode} & {title} & {score_str} \\\\ \\hline")
        
    # Process Top 2 LSI Results
    for i, res in enumerate(lsi_results[:2]):
        doc_id, title, author, score = res
        score_str = f"{score:.4f}" if isinstance(score, (float, np.float64)) else str(score)
        mode = "LSI (Latent)" if i == 0 else ""
        print(f"    {mode} & {title} & {score_str} \\\\ \\hline")
        
    print("    \\end{tabular}")
    print(f"    \\caption{{Comparison of retrieval effectiveness between Raw TF and LSI modes for the query ``{query}''.}}")
    print("\\end{table}")
    print("\n")

if __name__ == "__main__":
    print("🚀 Initializing Query Engine...\n")
    qe = QueryEngine(DB_CONFIG)
    
    test_queries = [
        "Cape Town",
        "water scarcity",
        "renewable solar power"
    ]
    
    print("==================================================")
    print(" LaTeX Evaluation Results for Technical Report")
    print("==================================================\n")
    
    for q in test_queries:
        try:
            raw_res = qe.query_raw_frequency(q)
            lsi_res = qe.query_relevance(q)
            
            # Ensure we only process if results are lists
            if isinstance(raw_res, list) and isinstance(lsi_res, list):
                generate_latex_table(q, raw_res, lsi_res)
            else:
                print(f"⚠️ Could not generate table for '{q}'. Not enough terms matched.")
        except Exception as e:
            print(f"Error evaluating '{q}': {e}")
