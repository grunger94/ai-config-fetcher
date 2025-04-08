import random

def get_json_mock(app_name: str, env_name: str) -> dict:
    """
    Simulates a mock configuration JSON response for a given app and environment.
    The values are randomized to simulate variability across app-env combinations.
    """
    return {
        "database_url": f"jdbc:postgresql://mock-db.{env_name.lower()}.local:5432/{app_name.lower().replace(' ', '_')}",
        "feature_toggle_x": random.choice(["DEBUG", "INFO", "WARN", "ERROR"]),
        "log_level": random.choice([True, False]),
        "max_connections": random.choice([25, 50, 100, 200]),
        "service_metadata": {
            "team": random.choice(["core-services", "platform", "data-ingestion"]),
            "owner": random.choice(["alice", "bob", "carla"]),
            "critical": random.choice([True, False]),
            "data_publish": random.choice([True, False, None])  # simulate missing config
        }
    }