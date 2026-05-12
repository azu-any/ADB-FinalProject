        CREATE TABLE document (
            id SERIAL PRIMARY KEY
        );

        CREATE TABLE text (
            id INTEGER PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
            url VARCHAR(255),
            title VARCHAR(255),
            author VARCHAR(255),
            date DATE,
            content TEXT
        );

        CREATE TABLE query (
            id INTEGER PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
            label TEXT NOT NULL
        );

        CREATE TABLE term (
            name VARCHAR(255) PRIMARY KEY
        );

        CREATE TABLE has (
            document_id INTEGER REFERENCES document(id) ON DELETE CASCADE,
            term_name VARCHAR(255) REFERENCES term(name) ON DELETE CASCADE,
            frequency REAL NOT NULL,
            PRIMARY KEY (document_id, term_name)
        );

        CREATE TABLE word (
            word VARCHAR(255) PRIMARY KEY
        );

        CREATE TABLE represent (
            term_name VARCHAR(255) REFERENCES term(name) ON DELETE CASCADE,
            word VARCHAR(255) REFERENCES word(word) ON DELETE CASCADE,
            PRIMARY KEY (term_name, word)
        );

        CREATE TABLE svd_model (
            name VARCHAR(50) PRIMARY KEY,
            data JSON
        );

        CREATE TABLE lsi_vectors (
            doc_id INTEGER PRIMARY KEY REFERENCES document(id) ON DELETE CASCADE,
            vector JSONB NOT NULL
        );

        CREATE TABLE query_results (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            metric VARCHAR(50) NOT NULL,
            top_n INTEGER NOT NULL,
            results JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
