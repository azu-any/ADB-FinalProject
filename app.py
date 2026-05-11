import os
from flask import Flask, render_template, request, jsonify
from query_engine import QueryEngine
from config import DB_CONFIG
from dotenv import load_dotenv
from scraper import WebScraper
import threading
from indexer import FrequencyAnalyzer
from lsi_engine import LSIEngine

load_dotenv()

app = Flask(__name__)

# Initialize the query engine with the Supabase connection config
try:
    qe = QueryEngine(DB_CONFIG)
except Exception as e:
    print(f"Failed to initialize QueryEngine: {e}")
    qe = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/query", methods=["POST"])
def perform_query():
    if not qe:
        return jsonify({"error": "Database connection not initialized"}), 500
        
    data = request.get_json()
    query_text = data.get("query", "")
    metric = data.get("metric", "cosine")
    top_n = data.get("top_n", 5)
    mode = data.get("mode", "lsi")
    
    if not query_text:
        return jsonify({"error": "Query cannot be empty"}), 400
        
    try:
        if mode == "raw":
            results = qe.query_raw_frequency(query_text, n=top_n, metric=metric)
        else:
            results = qe.query_relevance(query_text, n=top_n, metric=metric)
        
        # Check if results is a string (error message) instead of list
        if isinstance(results, str):
            return jsonify({"error": results}), 400
            
        formatted_results = [
            {"doc_id": doc_id, "title": title, "author": author, "score": float(score)}
            for doc_id, title, author, score in results
        ]
        
        return jsonify({"results": formatted_results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_indexing_pipeline():
    """Runs the full indexing and LSI pipeline in background."""
    global qe
    try:
        print("Starting background indexing pipeline...")
        indexer = FrequencyAnalyzer(DB_CONFIG)
        indexer.run(docs_dir="data/documents", metadata_path="data/metadata.json")
        
        lsi = LSIEngine(DB_CONFIG)
        matrix = lsi.load_frequency_matrix()
        U, S, Vt = lsi.perform_svd(matrix)
        doc_vectors, Uk, Sk = lsi.compute_reduced_representation(U, S, Vt, k=3)
        lsi.save_lsi_vectors(matrix.columns, doc_vectors, Uk, Sk)
        
        # Reload query engine
        qe = QueryEngine(DB_CONFIG)
        print("Background indexing complete.")
    except Exception as e:
        print(f"Indexing pipeline failed: {e}")

@app.route("/api/index_url", methods=["POST"])
def index_url():
    data = request.get_json()
    url = data.get("url", "")
    if not url:
        return jsonify({"error": "URL cannot be empty"}), 400
        
    try:
        scraper = WebScraper(docs_dir="data/documents", metadata_path="data/metadata.json")
        filename, title = scraper.scrape_and_save(url)
        
        # Trigger background indexing
        thread = threading.Thread(target=run_indexing_pipeline)
        thread.start()
        
        return jsonify({"message": f"Successfully scraped '{title}'. System is re-indexing in the background (takes ~30-60s)."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        conn = qe.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        docs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM terms")
        terms = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            "documents": docs,
            "terms": terms,
            "dimensions": 3 # k=3 is currently hardcoded in run_indexing_pipeline
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
