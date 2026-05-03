# Advanced Databases Final Project: LSI Document Base System

This project implements a **Latent Semantic Indexing (LSI)** system to represent and query a document base using Singular Value Decomposition (SVD). It is designed to evaluate both semantic similarity and document relevance within a relational database context (MySQL).

## 🚀 Features

- **Document Base**: 10+ documents focused on global sustainability (Water, Renewable Energy, Climate Change).
- **Text Preprocessing**: 
  - Stopword removal.
  - Stemming via custom suffix list.
  - Vocabulary extraction and mapping.
- **Relational Storage**:
  - Full persistence of documents, terms, and frequency matrices in MySQL.
  - Storage of reduced SVD vectors and model matrices for semantic querying.
- **Advanced Querying**:
  - **Similarity Metrics**: Inner Product, Cosine, Dice, and Jaccard.
  - **Dissimilarity Metrics**: Euclidean and Manhattan distances.
  - **Semantic Search**: Find the most relevant documents for any free-text query.

## 📂 Project Structure

- `data/`: Document repository.
- `schema.sql`: SQL scripts for database initialization.
- `preprocessing.py`: Text cleaning and normalization pipeline.
- `indexer.py`: Database ingestion and frequency matrix construction.
- `lsi_engine.py`: Dimensionality reduction using SVD.
- `query_engine.py`: Multi-metric query execution and projection.
- `main.py`: Orchestrator for the full workflow.

## 🛠 Setup

1. **MySQL Configuration**:
   Update `config.py` with your database credentials:
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "user": "your_user",
       "password": "your_password",
       "database": "lsi_project"
   }
   ```

2. **Installation**:
   ```bash
   pip install mysql-connector-python numpy scipy pandas
   ```

3. **Run**:
   ```bash
   python main.py
   ```

## 🧠 Technical Details

The system transforms the raw **Term-Document Frequency Matrix ($FrecT$)** into a lower-dimensional latent space using SVD ($A \approx U_k \Sigma_k V_k^T$). This allows the system to identify relationships between documents that share semantic themes even if they don't share exact keywords (handling synonyms and polysemies).
