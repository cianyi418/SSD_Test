import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """
    Load configuration from a JSON file.

    Returns:
        dict: Configuration data as a dictionary.

    Raises:
        FileNotFoundError: If the configuration file is not found.
        json.JSONDecodeError: If the configuration file is not a valid JSON.
    """
    try:
        with open(CONFIG_PATH, "r") as config_file:
            config = json.load(config_file)
            print(f"Configuration loaded successfully from {CONFIG_PATH}")
            return config
    except FileNotFoundError:
        print(f"Configuration file not found: {CONFIG_PATH}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON configuration file: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error while loading configuration: {str(e)}")
        raise