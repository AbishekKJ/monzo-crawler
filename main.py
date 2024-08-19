import argparse
import os
import logging
from crawler.crawler import Crawler
from config.config import load_config, setup_logging


def load_config():
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
    """Set up logging based on environment."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Logging initialized with level {log_level}")


def main():
    """Main entry point for running the crawler from the command line."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Web Crawler")
    parser.add_argument("start_url", help="The base URL to start crawling")
    parser.add_argument("--max_depth", type=int, default=3, help="Maximum crawling depth")
    parser.add_argument("--max_workers", type=int, default=5, help="Number of concurrent workers")
    args = parser.parse_args()

    # Load configuration and set up the environment
    setup_logging()
    config = load_config()

    # Extracting config settings
    max_depth = args.max_depth or config.get("max_depth", 3)
    max_workers = args.max_workers or config.get("max_workers", 5)

    # Start the crawler
    crawler = Crawler(start_url=args.start_url, max_depth=max_depth, max_workers=max_workers)
    crawler.run()


if __name__ == "__main__":
    main()