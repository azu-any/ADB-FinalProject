-- Create Database
CREATE DATABASE IF NOT EXISTS lsi_project;
USE lsi_project;

-- Table for Documents
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    publish_date DATE,
    file_path VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for Unique Terms (Vocabulary)
CREATE TABLE IF NOT EXISTS terms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    term VARCHAR(100) UNIQUE NOT NULL
);

-- Table for Term-Document Frequency Matrix (FrecT)
-- Stores the number of times term_id appears in document_id
CREATE TABLE IF NOT EXISTS term_document_matrix (
    term_id INT,
    doc_id INT,
    frequency INT DEFAULT 0,
    PRIMARY KEY (term_id, doc_id),
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Table for LSI Vectors (Reduced k-dimensional representation)
-- We'll store the coordinates as JSON for flexibility, or we could have a wide table.
-- Given the requirement to choose terms/dimensions, JSON is easier for varying k.
CREATE TABLE IF NOT EXISTS lsi_vectors (
    doc_id INT PRIMARY KEY,
    vector JSON NOT NULL,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Helper table for Stopwords
CREATE TABLE IF NOT EXISTS stopwords (
    word VARCHAR(50) PRIMARY KEY
);

-- Helper table for Suffixes (Stemming rules)
CREATE TABLE IF NOT EXISTS suffixes (
    suffix VARCHAR(20) PRIMARY KEY,
    replacement VARCHAR(20)
);
