import logging

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.utils.db import get_pg_connection, PG_TABLE

logger = logging.getLogger(__name__)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def get_stored_hash(application_name: str, environment_name: str):
    conn = get_pg_connection()
    cur = conn.cursor()

    # Check stored hash
    cur.execute(
        f"SELECT file_hash FROM {PG_TABLE} WHERE app_name = %s AND env_name = %s",
        (application_name, environment_name)
    )
    row = cur.fetchone()
    stored_hash = row[0] if row else None
    cur.close()
    conn.close()

    return stored_hash

def store_embedding(application_name: str, environment_name: str, content: str, file_hash: str):
    """Store embeddings in PostgreSQL"""
    logger.debug(f"Storing embeddings for {application_name}-{environment_name}")

    embedding = embeddings.embed_query(content)

    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        f"""
        INSERT INTO {PG_TABLE} (app_name, env_name, content, embedding, file_hash)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (app_name, env_name) DO UPDATE
        SET content = EXCLUDED.content, embedding = EXCLUDED.embedding, file_hash = EXCLUDED.file_hash
        """,
        (application_name, environment_name, content, embedding, file_hash)
    )
    conn.commit()
    cur.close()
    conn.close()

def fetch_configurations(apps: list[str], envs: list[str]):
    conn = get_pg_connection()
    cur = conn.cursor()

    query = f"""
            SELECT app_name, env_name, content
            FROM {PG_TABLE}
            WHERE app_name = ANY(%s) AND env_name = ANY(%s)
        """
    params = (apps, envs)

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


