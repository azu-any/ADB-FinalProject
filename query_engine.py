import psycopg2
import numpy as np
import json
import re
from preprocessing import TextPreprocessor

class QueryEngine:
    def __init__(self, db_config):
        self.db_config = db_config
        self.preprocessor = TextPreprocessor()

    def get_connection(self):
        return psycopg2.connect(**self.db_config)

    def get_doc_vector(self, doc_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT vector FROM lsi_vectors WHERE doc_id = %s", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            data = row[0]
            return np.array(data if isinstance(data, list) else json.loads(data))
        return None

    def get_all_vectors(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.doc_id, d.title, d.author, v.vector 
            FROM lsi_vectors v 
            JOIN documents d ON v.doc_id = d.id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [(row[0], row[1], row[2], np.array(row[3] if isinstance(row[3], list) else json.loads(row[3]))) for row in rows]

    def get_svd_model(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, data FROM svd_model")
        model = {name: np.array(data if isinstance(data, list) else json.loads(data)) for name, data in cursor.fetchall()}
        conn.close()
        return model

    # --- Similarity Functions ---
    def inner_product(self, v1, v2):
        return np.dot(v1, v2)

    def cosine_similarity(self, v1, v2):
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0
        return np.dot(v1, v2) / (norm_v1 * norm_v2)

    def dice_coefficient(self, v1, v2):
        # Applied to binary vectors or sets in original space
        # For latent space, we can use a normalized dot product variation
        intersection = np.sum(np.minimum(v1, v2))
        return 2 * intersection / (np.sum(v1) + np.sum(v2))

    def jaccard_coefficient(self, v1, v2):
        intersection = np.sum(np.minimum(v1, v2))
        union = np.sum(np.maximum(v1, v2))
        if union == 0: return 0
        return intersection / union

    # --- Dissimilarity Functions ---
    def euclidean_distance(self, v1, v2):
        return np.linalg.norm(v1 - v2)

    def manhattan_distance(self, v1, v2):
        return np.sum(np.abs(v1 - v2))

    # --- Query Execution ---
    def compare_documents(self, doc_id1, doc_id2, metric='cosine'):
        v1 = self.get_doc_vector(doc_id1)
        v2 = self.get_doc_vector(doc_id2)
        
        if v1 is None or v2 is None:
            return "One or both documents not found."
        
        metrics = {
            'cosine': self.cosine_similarity,
            'inner': self.inner_product,
            'dice': self.dice_coefficient,
            'jaccard': self.jaccard_coefficient,
            'euclidean': self.euclidean_distance,
            'manhattan': self.manhattan_distance
        }
        
        if metric not in metrics:
            return "Unknown metric."
            
        return metrics[metric](v1, v2)

    def query_relevance(self, query_text, n=5, metric='cosine'):
        # 1. Preprocess query
        tokens = self.preprocessor.preprocess(query_text)
        
        # 2. Get term mapping from DB
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, term FROM terms ORDER BY id")
        terms = {row[1]: i for i, row in enumerate(cursor.fetchall())}
        num_terms = len(terms)
        
        # 3. Create query vector in term space with synonym expansion
        q_term_vec = np.zeros(num_terms)
        
        # Expand tokens with synonyms using original words from query
        # We split by non-alphanumeric to get potential terms
        raw_words = re.findall(r'[a-z]+', query_text.lower())
        all_search_terms = set(tokens) # Start with original stemmed tokens
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for word in raw_words:
                cursor.execute("SELECT synonym FROM Represent WHERE term = %s", (word,))
                syns = [row[0] for row in cursor.fetchall()]
                for s in syns:
                    # Preprocess the synonym to match the index
                    p_syns = self.preprocessor.preprocess(s)
                    all_search_terms.update(p_syns)
            conn.close()
        except Exception as e:
            print(f"⚠️ Warning fetching synonyms: {e}")

        for p_term in all_search_terms:
            if p_term in terms:
                q_term_vec[terms[p_term]] += 1
        
        if np.all(q_term_vec == 0):
            return "Query contains no terms found in the index."

        # 4. Project query into latent space
        # q_k = q^T * Uk * Sk^-1
        model = self.get_svd_model()
        Uk = model['Uk']
        Sk = model['Sk']
        
        # Invert S (it's diagonal)
        Sk_inv = np.linalg.inv(Sk)
        
        q_latent = q_term_vec.T @ Uk @ Sk_inv
        
        # 5. Compare against all doc vectors
        all_docs = self.get_all_vectors()
        results = []
        
        metrics = {
            'cosine': self.cosine_similarity,
            'inner': self.inner_product,
            'dice': self.dice_coefficient,
            'jaccard': self.jaccard_coefficient,
            'euclidean': self.euclidean_distance,
            'manhattan': self.manhattan_distance
        }
        
        compare_func = metrics.get(metric, self.cosine_similarity)
        
        for doc_id, title, author, v_doc in all_docs:
            score = compare_func(q_latent, v_doc)
            results.append((doc_id, title, author, score))
            
        # 6. Sort and return
        # For distances (euclidean, manhattan), lower is better. 
        # For similarities, higher is better.
        reverse = metric not in ['euclidean', 'manhattan']
        results.sort(key=lambda x: x[3], reverse=reverse)
        results = results[:n]

        # 7. Save results to query_results table
        self.save_query_result(query_text, metric, n, results)
            
        return results

    def query_raw_frequency(self, query_text, n=5, metric='cosine'):
        """Computes relevance using the raw term_document_matrix (no SVD/LSI)."""
        # 1. Preprocess query
        tokens = self.preprocessor.preprocess(query_text)
        if not tokens:
            return "Query contains only stopwords or no valid words."
            
        # 2. Get terms index
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, term FROM terms ORDER BY id")
        terms_db = cursor.fetchall()
        
        terms = {row[1]: i for i, row in enumerate(terms_db)}
        term_id_map = {row[1]: row[0] for row in terms_db}
        num_terms = len(terms)
        
        # 3. Create query vector in term space with synonym expansion
        q_term_vec = np.zeros(num_terms)
        
        raw_words = re.findall(r'[a-z]+', query_text.lower())
        all_search_terms = set(tokens) 
        
        try:
            for word in raw_words:
                cursor.execute("SELECT synonym FROM Represent WHERE term = %s", (word,))
                syns = [row[0] for row in cursor.fetchall()]
                for s in syns:
                    p_syns = self.preprocessor.preprocess(s)
                    all_search_terms.update(p_syns)
        except Exception as e:
            pass

        for p_term in all_search_terms:
            if p_term in terms:
                q_term_vec[terms[p_term]] += 1
        
        if np.all(q_term_vec == 0):
            conn.close()
            return "Query contains no terms found in the index."

        # 4. Fetch the entire raw term_document_matrix
        cursor.execute("SELECT id, title, author FROM documents ORDER BY id")
        docs_info = cursor.fetchall()
        
        results = []
        metrics = {
            'cosine': self.cosine_similarity,
            'euclidean': self.euclidean_distance,
            'inner': self.inner_product,
            'dice': self.dice_coefficient,
            'jaccard': self.jaccard_coefficient,
            'manhattan': self.manhattan_distance
        }
        compare_func = metrics.get(metric, self.cosine_similarity)
        
        for doc_id, title, author in docs_info:
            # Reconstruct document vector
            cursor.execute("SELECT term_id, frequency FROM term_document_matrix WHERE doc_id = %s", (doc_id,))
            doc_terms = cursor.fetchall()
            
            d_vec = np.zeros(num_terms)
            for t_id, freq in doc_terms:
                # Find index in array
                array_idx = next(i for i, row in enumerate(terms_db) if row[0] == t_id)
                d_vec[array_idx] = freq
                
            score = compare_func(q_term_vec, d_vec)
            results.append((doc_id, title, author, score))
            
        conn.close()

        # 5. Sort and return
        reverse = metric not in ['euclidean', 'manhattan']
        results.sort(key=lambda x: x[3], reverse=reverse)
        results = results[:n]

        # Save result
        self.save_query_result(query_text, f"{metric}_raw", n, results)
        
        return results

    def save_query_result(self, query_text, metric, n, results):
        """Saves the search result to the database for history/analysis."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Format results as a list of dictionaries for JSONB
            json_results = [
                {"doc_id": r[0], "title": r[1], "author": r[2], "score": float(r[3])}
                for r in results
            ]
            
            cursor.execute(
                "INSERT INTO query_results (query_text, metric, top_n, results) VALUES (%s, %s, %s, %s)",
                (query_text, metric, n, json.dumps(json_results))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Warning saving query result: {e}")

if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "lsi_project"
    }
    qe = QueryEngine(db_config)
    # Example: print(qe.compare_documents(1, 2, 'cosine'))
