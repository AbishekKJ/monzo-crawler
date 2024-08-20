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
import threading
from exceptions import CrawlerException, RobotsDisallowedError, FetchError


class Crawler:
    def __init__(self, start_url: str, max_depth: int, max_workers: int, session: Optional[requests.Session] = None):
        """
        Initializes the Crawler with the starting URL, maximum depth, and number of workers.

        :param start_url: The URL to start crawling from.
        :param max_depth: The maximum depth to crawl.
        :param max_workers: The maximum number of concurrent workers.
        :param session: Optional requests.Session to use for HTTP requests.
        """
        self.start_url: str = start_url
        self.allowed_domain: str = urlparse(start_url).netloc
        self.max_depth: int = max_depth
        self.max_workers: int = max_workers
        self.url_manager: URLManager = URLManager(self.allowed_domain)
        self.logger: logging.Logger = logging.getLogger("crawler")
        self.session: requests.Session = session or self._create_session_with_retries()
        self.queue: deque = deque()
        self.visited: Set[str] = set()
        self.output_file: str = self.get_output_file_name()
        self.robots_parser: Optional[RobotsParser] = None

        self.queue_lock = threading.Lock()
        self.visited_lock = threading.Lock()

        self._load_robots_txt()

    def _create_session_with_retries(self) -> requests.Session:
        """
        Creates a requests.Session with retry configuration.

        :return: A configured requests.Session instance.
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
        Loads and parses the robots.txt file from the allowed domain to respect crawl restrictions.

        :raises: Requests exceptions if loading robots.txt fails.
        """
        robots_url = f"https://{self.allowed_domain}/robots.txt"
        try:
            response = self.session.get(robots_url)
            response.raise_for_status()
            if response.status_code == 200:
                self.robots_parser = RobotsParser(response.text)
                self.logger.info("Successfully loaded and parsed robots.txt")
            else:
                self.logger.warning(f"Failed to fetch robots.txt from {robots_url}: Status code {response.status_code}")
        except requests.RequestException as e:
            self.logger.error(f"An error occurred while fetching robots.txt: {e}")
            self.robots_parser = None

    def get_output_file_name(self) -> str:
        """
        Generates the output file name based on the current timestamp.

        :return: The generated output file name.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"out_file_{timestamp}.json"

    def _fetch(self, url: str) -> Optional[str]:
        """
        Fetches the content of the given URL. Raises an exception if the request fails or the URL is blocked.

        :param url: The URL to fetch content from.
        :return: The HTML content of the URL if successful, otherwise raises FetchError.
        :raises: FetchError if the request fails.
        :raises: RobotsDisallowedError if the URL is blocked by robots.txt.
        """
        if self.robots_parser and not self.robots_parser.is_allowed(url):
            self.logger.info(f"URL blocked by robots.txt: {url}")
            raise RobotsDisallowedError(url)

        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            raise FetchError(url, str(e))

    def crawl(self, url: str, depth: int) -> Optional[Set[str]]:
        """
        Crawls a given URL and extracts links from the page. Handles errors and updates visited URLs.

        :param url: The URL to crawl.
        :param depth: The current depth of crawling.
        :return: A set of links found on the page or an empty set if an error occurs.
        """
        self.logger.info(f"Crawling URL: {url} at depth: {depth}")

        try:
            html_content = self._fetch(url)
        except (FetchError, RobotsDisallowedError) as e:
            self.logger.error(str(e))
            return set()

        with self.visited_lock:
            self.url_manager.mark_visited(url)
            self.visited.add(url)

        links = parse_links(html_content, url)

        return links

    def run(self) -> None:
        """
        Starts the crawling process. Manages the queue of URLs to visit and handles concurrency.

        This method initializes the queue with the start URL, creates a ThreadPoolExecutor to handle concurrent crawling,
        and processes each URL until the queue is empty. It updates the queue with new links and writes the visited URLs
        to a file upon completion.
        """
        self.queue.append((self.start_url, 0))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.queue:
                with self.queue_lock:
                    futures = {}

                    for _ in range(len(self.queue)):
                        url, depth = self.queue.popleft()

                        if depth <= self.max_depth and self.url_manager.should_visit(url):
                            futures[executor.submit(self.crawl, url, depth)] = (url, depth)

                for future in as_completed(futures):
                    url, depth = futures[future]
                    try:
                        links = future.result()
                        if links:
                            with self.queue_lock:
                                for link in links:
                                    with self.visited_lock:
                                        if link not in self.visited and self.url_manager.should_visit(link):
                                            self.queue.append((link, depth + 1))
                    except CrawlerException as e:
                        self.logger.error(f"CrawlerException during crawling {url}: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error during crawling {url}: {e}")
                    finally:
                        futures.pop(future)

        self.write_urls_to_file()

    def write_urls_to_file(self) -> None:
        """
        Writes the visited URLs to the output file.

        The file is named based on the timestamp of when the crawling was completed. Each URL is written on a new line.
        """
        with open(self.output_file, 'w') as file:
            for url in sorted(self.visited):
                file.write(f"{url}\n")
        self.logger.info(f"Unique URLs written to {self.output_file}")
