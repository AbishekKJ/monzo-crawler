import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv
from config.logger import configure_logger

# Load environment variables from a .env file
load_dotenv()


def load_config() -> Dict[str, Any]:
    """
    Load environment-specific configuration from YAML files.

    Returns:
        Dict[str, Any]: The configuration settings as a dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
    """
    environment = os.getenv("ENVIRONMENT", "dev")
    config_file = f'config/{environment}.yaml'

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file {config_file} not found.")

    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    return config


def setup_configuration() -> None:
    """
    Set up configuration including logging.
    """
    # Load configuration
    config = load_config()

    # Set up logging
    logging_config = config.get("logging", {})
    configure_logger(logging_config)
