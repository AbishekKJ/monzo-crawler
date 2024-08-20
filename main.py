import argparse
from crawler.crawler import Crawler
from utils import is_valid_url
from config.config import setup_configuration, load_config


def main() -> None:
    """
    Main entry point for running the crawler from the command line.
    """
    setup_configuration()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Web Crawler")
    parser.add_argument("start_url", help="The base URL to start crawling")
    parser.add_argument("--max_depth", type=int, default=3, help="Maximum crawling depth")
    parser.add_argument("--max_workers", type=int, default=5, help="Number of concurrent workers")
    args = parser.parse_args()

    if not is_valid_url(args.start_url):
        raise ValueError(f"The start URL '{args.start_url}' is not valid.")

    config = load_config()
    max_depth = args.max_depth or config.get("max_depth", 3)
    max_workers = args.max_workers or config.get("max_workers", 5)

    crawler = Crawler(start_url=args.start_url, max_depth=max_depth, max_workers=max_workers)
    crawler.run()


if __name__ == "__main__":
    main()
