import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
import logging
from datetime import datetime
from collections import deque
from crawler.parser import parse_links
from crawler.url_manager import URLManager


class Crawler:
    def __init__(self, start_url, max_depth, max_workers):
        self.start_url = start_url
        self.allowed_domain = urlparse(start_url).netloc
        self.max_depth = max_depth
        self.max_workers = max_workers
        self.url_manager = URLManager(self.allowed_domain)  # Pass allowed domain
        self.logger = logging.getLogger("crawler")
        self.session = self._create_session_with_retries()
        self.queue = deque()  # Custom queue to manage BFS order
        self.visited = set()
        self.output_file = self.get_output_file_name()

    def _create_session_with_retries(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_output_file_name(self):
        """Generate a timestamped filename for output."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"urls_{timestamp}.json"

    def _fetch(self, url):
        """Fetches the content of the URL with retries."""
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None

    def crawl(self, url, depth):
        """Crawls a given URL and returns links found on the page."""
        if not self.url_manager.should_visit(url, depth):
            return

        self.logger.info(f"Crawling URL: {url} at depth: {depth}")
        self.url_manager.mark_visited(url)
        self.visited.add(url)

        html_content = self._fetch(url)
        if not html_content:
            return

        links = parse_links(html_content, url)
        self.url_manager.add_links(links)

        return links

    def run(self):
        """Main BFS crawling logic with concurrency."""
        self.queue.append((self.start_url, 0))  # Start BFS with the root URL and depth 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.queue:
                futures = {}

                # Submit tasks for all items in the queue at the current depth
                for _ in range(len(self.queue)):
                    url, depth = self.queue.popleft()

                    if depth <= self.max_depth and self.url_manager.should_visit(url, depth):
                        futures[executor.submit(self.crawl, url, depth)] = (url, depth)

                # Process the results and add new links to the queue
                for future in as_completed(futures):
                    url, depth = futures[future]
                    try:
                        links = future.result()
                        if links:
                            for link in links:
                                # Ensure the new link is not visited and enqueue for the next depth level
                                if link not in self.visited and self.url_manager.should_visit(link, depth + 1):
                                    self.queue.append((link, depth + 1))
                    except Exception as e:
                        self.logger.error(f"Error during crawling {url}: {e}")
                    finally:
                        futures.pop(future)
        self.write_urls_to_file()

    def write_urls_to_file(self):
        """Write the unique list of URLs to the output file."""
        with open(self.output_file, 'w') as file:
            for url in sorted(self.visited):
                file.write(f"{url}\n")
        self.logger.info(f"Unique URLs written to {self.output_file}")


if __name__ == "__main__":
    # Basic configuration for logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Example usage
    crawler = Crawler(start_url="https://example.com", max_depth=3, max_workers=5)
    crawler.run()