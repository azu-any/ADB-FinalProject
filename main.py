import os
from config import DB_CONFIG
from indexer import Indexer
from lsi_engine import LSIEngine
from query_engine import QueryEngine

def run_demo():
    print("--- LSI Document Base System Demo ---")
    
    # 1. Initialize Indexer and DB
    indexer = Indexer(DB_CONFIG)
    print("\n[1/4] Initializing Database and Indexing Documents...")
    try:
        indexer.initialize_db('schema.sql')
        indexer.index_documents('data/documents', metadata_file='data/metadata.json')
    except Exception as e:
        print(f"Error during indexing: {e}")
        print("Please ensure MySQL is running and DB_CONFIG is correct.")
        return

    # 2. Perform LSI
    print("\n[2/4] Performing SVD and Dimensionality Reduction...")
    lsi = LSIEngine(DB_CONFIG)
    matrix = lsi.load_frequency_matrix()
    U, S, Vt = lsi.perform_svd(matrix)
    
    print(f"Terms: {matrix.shape[0]}, Documents: {matrix.shape[1]}")
    print(f"Singular Values: {S}")
    
    # Let the user choose k (expert user requirement)
    try:
        user_k = input(f"\nEnter the number of dimensions to keep (1-{len(S)}) [default: 3]: ").strip()
        k = int(user_k) if user_k else 3
        if k < 1 or k > len(S):
            print(f"Invalid k, defaulting to 3.")
            k = 3
    except EOFError:
        print("\nNon-interactive mode detected, using k=3.")
        k = 3
    except ValueError:
        print("Invalid input, defaulting to 3.")
        k = 3

    print(f"Applying dimensionality reduction with k={k}...")
    doc_vectors, Uk, Sk = lsi.compute_reduced_representation(U, S, Vt, k)
    lsi.save_lsi_vectors(matrix.columns, doc_vectors, Uk, Sk)

    # 3. Querying
    print("\n[3/4] Testing Document Similarity (Doc 1 vs Doc 2)...")
    qe = QueryEngine(DB_CONFIG)
    
    # Compare first two docs
    doc_ids = list(matrix.columns)
    if len(doc_ids) >= 2:
        sim = qe.compare_documents(doc_ids[0], doc_ids[1], metric='cosine')
        print(f"Cosine Similarity between Doc {doc_ids[0]} and Doc {doc_ids[1]}: {sim:.4f}")
        
        dist = qe.compare_documents(doc_ids[0], doc_ids[1], metric='euclidean')
        print(f"Euclidean Distance between Doc {doc_ids[0]} and Doc {doc_ids[1]}: {dist:.4f}")

    # 4. Search Relevance
    print("\n[4/4] Testing Search Queries...")
    queries = [
        "solar panels and renewable energy",
        "protecting oceans and marine life",
        "water scarcity and climate change"
    ]
    
    for q_text in queries:
        print(f"\nQuery: '{q_text}'")
        results = qe.query_relevance(q_text, n=3, metric='cosine')
        if isinstance(results, str):
            print(results)
        else:
            for doc_id, title, score in results:
                print(f" - [{score:.4f}] {title} (ID: {doc_id})")

if __name__ == "__main__":
    run_demo()
