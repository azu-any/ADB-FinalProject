import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_config():
    result = urlparse(DATABASE_URL)
    return {
        "host": result.hostname,
        "port": result.port or 5432,
        "user": result.username,
        "password": result.password,
        "database": result.path[1:],
        "sslmode": "require"
    }

DB_CONFIG = get_db_config()
print("✅ Configuración Supabase cargada")
