import yaml
from dotenv import load_dotenv
from config.logger import configure_logger

load_dotenv()


def load_config(config_file):
    """Load environment-specific configuration from YAML files."""
    environment = os.getenv("ENVIRONMENT", "dev")
    config_file = f'config/{environment}.yaml'

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file {config_file} not found.")

    import yaml
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def setup_logging():
    """Set up logging based on the environment or default level."""
    config = load_config()
    configure_logger(config.get('logging', {}))