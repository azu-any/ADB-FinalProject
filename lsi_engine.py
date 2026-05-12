import psycopg2
import numpy as np
import pandas as pd
from scipy.linalg import svd
import json

from config import DB_CONFIG

class LSIEngine:
    def __init__(self, db_config):
        self.db_config = db_config

    def get_connection(self):
        return psycopg2.connect(**self.db_config)

    def load_frequency_matrix(self):
        conn = self.get_connection()
        query = """
            SELECT t.name as term, d.id as doc_id, COALESCE(h.frequency, 0) as frequency
            FROM term t
            CROSS JOIN text d
            LEFT JOIN has h ON t.name = h.term_name AND d.id = h.document_id
            ORDER BY t.name, d.id
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Pivot to create Matrix (Terms as rows, Docs as columns)
        matrix = df.pivot(index='term', columns='doc_id', values='frequency').fillna(0)
        return matrix

    def perform_svd(self, matrix):
        # A = U * S * Vt
        # matrix.values is the ndarray
        A = matrix.values.astype(float)
        U, S, Vt = svd(A, full_matrices=False)
        return U, S, Vt

    def compute_reduced_representation(self, U, S, Vt, k):
        """
        k is the number of singular values to keep.
        Reduced Matrix Ak = Uk * Sk * Vtk
        However, for LSI retrieval, we often represent docs in k-space.
        Document coordinates in k-space are the columns of (Sk * Vtk) or just Vtk?
        Standard LSI uses (Sk * Vtk) or projection: d_k = d^T * Uk * Sk^-1
        We'll store document vectors in the k-dimensional space.
        """
        Uk = U[:, :k]
        Sk = np.diag(S[:k])
        Vtk = Vt[:k, :]
        
        # Doc vectors in latent space: columns of (Sk * Vtk)^T or just Vtk^T
        # Usually docs are represented as rows in the V matrix scaled by S
        doc_vectors = (Sk @ Vtk).T 
        return doc_vectors, Uk, Sk

    def save_lsi_vectors(self, doc_ids, doc_vectors, Uk, Sk, terms):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Save document vectors
        cursor.execute("TRUNCATE TABLE lsi_vectors")
        for i, doc_id in enumerate(doc_ids):
            vector_json = json.dumps(doc_vectors[i].tolist())
            cursor.execute(
                "INSERT INTO lsi_vectors (doc_id, vector) VALUES (%s, %s)",
                (int(doc_id), vector_json)
            )
        
        # Save reduction matrices (U_k and S_k_inv) to a new table or file
        # For simplicity, let's create a table 'svd_model'
        cursor.execute("CREATE TABLE IF NOT EXISTS svd_model (name VARCHAR(50) PRIMARY KEY, data JSON)")
        cursor.execute("INSERT INTO svd_model (name, data) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data", ('Uk', json.dumps(Uk.tolist())))
        cursor.execute("INSERT INTO svd_model (name, data) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data", ('Sk', json.dumps(Sk.tolist())))
        cursor.execute("INSERT INTO svd_model (name, data) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET data = EXCLUDED.data", ('terms', json.dumps(terms)))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Stored LSI vectors and SVD model.")

if __name__ == "__main__":
    db_config = DB_CONFIG
    
    lsi = LSIEngine(db_config)
    matrix = lsi.load_frequency_matrix()
    print("Frequency Matrix Shape:", matrix.shape)
    
    U, S, Vt = lsi.perform_svd(matrix)
    print("Singular Values:", S)
    
    # Simple heuristic: keep 80% of energy or a fixed k
    k = 6 # Increased from 3 to 6 to capture variance of smaller documents vs Wikipedia
    doc_vectors, Uk, Sk = lsi.compute_reduced_representation(U, S, Vt, k)
    
    lsi.save_lsi_vectors(matrix.columns, doc_vectors, Uk, Sk, matrix.index.tolist())
