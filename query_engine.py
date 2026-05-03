import mysql.connector
import numpy as np
import json
from preprocessing import TextPreprocessor

class QueryEngine:
    def __init__(self, db_config):
        self.db_config = db_config
        self.preprocessor = TextPreprocessor()

    def get_connection(self):
        return mysql.connector.connect(**self.db_config)

    def get_doc_vector(self, doc_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT vector FROM lsi_vectors WHERE doc_id = %s", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return np.array(json.loads(row[0]))
        return None

    def get_all_vectors(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.doc_id, d.title, v.vector 
            FROM lsi_vectors v 
            JOIN documents d ON v.doc_id = d.id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [(row[0], row[1], np.array(json.loads(row[2]))) for row in rows]

    def get_svd_model(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, data FROM svd_model")
        model = {name: np.array(json.loads(data)) for name, data in cursor.fetchall()}
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
        
        # 3. Create query vector in term space
        q_term_vec = np.zeros(num_terms)
        for token in tokens:
            if token in terms:
                q_term_vec[terms[token]] += 1
        
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
        
        for doc_id, title, v_doc in all_docs:
            score = compare_func(q_latent, v_doc)
            results.append((doc_id, title, score))
            
        # 6. Sort and return
        # For distances (euclidean, manhattan), lower is better. 
        # For similarities, higher is better.
        reverse = metric not in ['euclidean', 'manhattan']
        results.sort(key=lambda x: x[2], reverse=reverse)
        
        return results[:n]

if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "lsi_project"
    }
    qe = QueryEngine(db_config)
    # Example: print(qe.compare_documents(1, 2, 'cosine'))
