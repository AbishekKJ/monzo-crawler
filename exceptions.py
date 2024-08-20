class CrawlerException(Exception):
    """Base exception class for crawler errors."""
    pass


class FetchError(CrawlerException):
    """Exception raised when fetching a URL fails."""
    def __init__(self, url: str, message: str):
        super().__init__(f"Failed to fetch {url}: {message}")
        self.url = url
        self.message = message


class RobotsDisallowedError(CrawlerException):
    """Exception raised when a URL is disallowed by robots.txt."""
    def __init__(self, url: str):
        super().__init__(f"URL blocked by robots.txt: {url}")
        self.url = url


class ParseLinksException(Exception):
    """Base class for exceptions raised by parse_links."""
    pass


class InvalidHTMLContentError(ParseLinksException):
    """Exception raised for invalid HTML content."""
    pass


class InvalidBaseURLError(ParseLinksException):
    """Exception raised for invalid base URL."""
    pass
