import psycopg2
from pgvector.psycopg2 import register_vector

PG_HOST = "localhost"
PG_DATABASE = "pg_vector"
PG_USER = "postgres"
PG_PASSWORD = "postgres"
PG_TABLE = "vector_store"

def get_pg_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    register_vector(conn)
    return conn