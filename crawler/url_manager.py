from urllib.parse import urlparse
from typing import Set, Iterable
import threading


class URLManager:
    def __init__(self, allowed_domain: str):
        """
        Initializes the URLManager with the allowed domain.

        :param allowed_domain: The domain that URLs must match to be visited.
        """
        self.allowed_domain: str = allowed_domain
        self.visited_urls: Set[str] = set()

        self.lock = threading.Lock()

    def should_visit(self, url: str) -> bool:
        """
        Determines if the given URL should be visited.

        :param url: The URL to check.
        :param depth: The depth of the URL in the crawl.
        :return: True if the URL should be visited, False otherwise.
        """
        parsed_url = urlparse(url)
        with self.lock:
            return parsed_url.netloc == self.allowed_domain and url not in self.visited_urls

    def mark_visited(self, url: str) -> None:
        """
        Marks the given URL as visited.

        :param url: The URL to mark as visited.
        """
        with self.lock:
            self.visited_urls.add(url)

