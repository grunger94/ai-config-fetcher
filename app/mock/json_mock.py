import random

def get_json_mock(app_name: str, env_name: str) -> dict:
    """
    Simulates a mock configuration JSON response for a given app and environment.
    The values are randomized to simulate variability across app-env combinations.
    """
    log_levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    feature_toggle_options = [True, False]
    max_conn_options = [25, 50, 100, 200]

    return {
        "database_url": f"jdbc:postgresql://mock-db.{env_name.lower()}.local:5432/{app_name.lower().replace(' ', '_')}",
        "feature_toggle_x": random.choice(feature_toggle_options),
        "log_level": random.choice(log_levels),
        "max_connections": random.choice(max_conn_options)
    }