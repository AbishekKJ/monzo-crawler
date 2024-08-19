import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
import logging
from datetime import datetime
from collections import deque
from crawler.parser import parse_links
from crawler.robots_parser import RobotsParser
from crawler.url_manager import URLManager
from typing import Optional, Set
from config.config import load_config


class Crawler:
    def __init__(self, start_url: str, max_depth: int, max_workers: int, session: Optional[requests.Session] = None):
        """
        Initialize the Crawler with the given parameters.

        Args:
            start_url (str): The starting URL for the crawl.
            max_depth (int): The maximum depth to crawl.
            max_workers (int): The maximum number of worker threads.
            session (Optional[requests.Session]): An optional requests.Session object for making HTTP requests.
        """
        self.start_url: str = start_url
        self.allowed_domain: str = urlparse(start_url).netloc
        self.max_depth: int = max_depth
        self.max_workers: int = max_workers
        self.url_manager: URLManager = URLManager(self.allowed_domain)  # Pass allowed domain
        self.logger: logging.Logger = logging.getLogger("crawler")
        self.session: requests.Session = session or self._create_session_with_retries()
        self.queue: deque = deque()  # Custom queue to manage BFS order
        self.visited: Set[str] = set()
        self.output_file: str = self.get_output_file_name()
        self.robots_parser: Optional[RobotsParser] = None

        # Fetch and parse robots.txt
        self._load_robots_txt()

    def _create_session_with_retries(self) -> requests.Session:
        """
        Create and configure a requests.Session with retry strategy.

        Returns:
            requests.Session: The configured session object.
        """
        session = requests.Session()
        config = load_config()
        retry_config = config.get("retry", {})

        total_retries = retry_config.get("total", 5)
        backoff_factor = retry_config.get("backoff_factor", 0.3)
        status_forcelist = retry_config.get("status_forcelist", [500, 502, 503, 504])

        retry_strategy = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _load_robots_txt(self) -> None:
        """
        Fetch and parse robots.txt for the allowed domain.
        """
        robots_url = f"https://{self.allowed_domain}/robots.txt"
        response = self.session.get(robots_url)
        if response.status_code == 200:
            self.robots_parser = RobotsParser(response.text)
            self.logger.info("Successfully loaded and parsed robots.txt")
        else:
            self.logger.warning(f"Failed to fetch robots.txt from {robots_url}")

    def get_output_file_name(self) -> str:
        """
        Generate a timestamped filename for output.

        Returns:
            str: The generated filename.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"urls_{timestamp}.json"

    def _fetch(self, url: str) -> Optional[str]:
        """
        Fetch the content of the URL with retries.

        Args:
            url (str): The URL to fetch.

        Returns:
            Optional[str]: The content of the URL or None if the request failed.
        """
        if self.robots_parser and not self.robots_parser.is_allowed(url):
            self.logger.info(f"URL blocked by robots.txt: {url}")
            return None

        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def crawl(self, url: str, depth: int) -> Optional[Set[str]]:
        """
        Crawl a given URL and return links found on the page.

        Args:
            url (str): The URL to crawl.
            depth (int): The current depth of the crawl.

        Returns:
            Optional[Set[str]]: A set of links found on the page or None if no links are found.
        """
        self.logger.info(f"Crawling URL: {url} at depth: {depth}")
        self.url_manager.mark_visited(url)
        self.visited.add(url)

        html_content = self._fetch(url)
        if not html_content:
            return None

        links = parse_links(html_content, url)
        self.url_manager.add_links(links)

        return links

    def run(self) -> None:
        """
        Main BFS crawling logic with concurrency.
        """
        self.queue.append((self.start_url, 0))  # Start BFS with the root URL and depth 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.queue:
                futures = {}

                # Submit tasks for all items in the queue at the current depth
                for _ in range(len(self.queue)):
                    url, depth = self.queue.popleft()

                    if depth <= self.max_depth and self.url_manager.should_visit(url):
                        futures[executor.submit(self.crawl, url, depth)] = (url, depth)

                # Process the results and add new links to the queue
                for future in as_completed(futures):
                    url, depth = futures[future]
                    try:
                        links = future.result()
                        if links:
                            for link in links:
                                # Ensure the new link is not visited and enqueue for the next depth level
                                if link not in self.visited and self.url_manager.should_visit(link):
                                    self.queue.append((link, depth + 1))
                    except Exception as e:
                        self.logger.error(f"Error during crawling {url}: {e}")
                    finally:
                        futures.pop(future)
        self.write_urls_to_file()

    def write_urls_to_file(self) -> None:
        """
        Write the unique list of URLs to the output file.
        """
        with open(self.output_file, 'w') as file:
            for url in sorted(self.visited):
                file.write(f"{url}\n")
        self.logger.info(f"Unique URLs written to {self.output_file}")
