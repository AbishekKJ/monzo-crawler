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

        self._load_robots_txt()

    def _create_session_with_retries(self) -> requests.Session:
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"urls_{timestamp}.json"

    def _fetch(self, url: str) -> Optional[str]:
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
        self.queue.append((self.start_url, 0))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.queue:
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
                            for link in links:
                                if link not in self.visited and self.url_manager.should_visit(link):
                                    self.queue.append((link, depth + 1))
                    except Exception as e:
                        self.logger.error(f"Error during crawling {url}: {e}")
                    finally:
                        futures.pop(future)
        self.write_urls_to_file()

    def write_urls_to_file(self) -> None:
        with open(self.output_file, 'w') as file:
            for url in sorted(self.visited):
                file.write(f"{url}\n")
        self.logger.info(f"Unique URLs written to {self.output_file}")
