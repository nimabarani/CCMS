import os
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()

# --- Database Configuration ---
# Uses the same environment variables as your main application
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "database": os.environ.get("DB_NAME", "your_db"),
    "user": os.environ.get("DB_USER", "your_user"),
    "password": os.environ.get("DB_PASSWORD", "your_password"),
    "port": os.environ.get("DB_PORT", "5432"),
}


def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise
