import json
import logging

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.utils.db import get_pg_connection, PG_TABLE

logger = logging.getLogger(__name__)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def store_embedding(application_name, environment_name, content, file_hash):
    """Store embeddings in PostgreSQL"""
    logger.debug(f"Storing embeddings for {application_name}-{environment_name}: {content}")

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

def retrieve_similar_configs(query_text, top_k=5):
    """
    Perform similarity search in PostgreSQL using pgvector to retrieve relevant configuration data.
    """
    logger.info(f"Retrieve similar configs for query: {query_text} (top_k={top_k})")

    embedding = embeddings.embed_query(query_text)
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT app_name, env_name, content, embedding <-> %s::vector AS distance
        FROM {PG_TABLE} ORDER BY distance ASC LIMIT %s;
        """,
        (embedding, top_k)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()

    retrieved_configs = [
        {
            "app_name": row[0],
            "env_name": row[1],
            "content": json.loads(row[2]),
            "similarity_score": row[3],
        }
        for row in results
    ]

    return retrieved_configs