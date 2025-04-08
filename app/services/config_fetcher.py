import json
import logging
from typing import List, Dict, Any

from app.mock.json_mock import get_json_mock
from app.services.vector_search import store_embedding
from app.utils.db import get_pg_connection, PG_TABLE
from app.utils.hashing import get_file_hash

logger = logging.getLogger(__name__)

def fetch_and_embed_all_configs(apps: List[str], envs: List[str]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Fetches configuration data for each app-env combination individually and stores their embeddings into a vectorstore.
    """
    all_configs = {}

    for app_name in apps:
        app_configs = {}
        for env_name in envs:
            config = fetch_and_embed_app_env_config(app_name, env_name)
            app_configs[env_name] = config
        all_configs[app_name] = app_configs

    return all_configs

def fetch_and_embed_app_env_config(application_name, environment_name) -> dict:
    """Fetch, check, and persist the configuration in PostgreSQL vectorstore."""
    json_content = get_json_mock(application_name, environment_name)  # Mocking API response
    new_hash = get_file_hash(json.dumps(json_content))
    file_name = f"{application_name}-{environment_name}"

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

    if stored_hash == new_hash:
        logger.debug(f"No changes detected for {file_name}, skipping ingestion")
    else:
        # Store new embedding
        store_embedding(application_name, environment_name, json.dumps(json_content), new_hash)

    return json_content