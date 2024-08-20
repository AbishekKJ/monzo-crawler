import pytest
from urllib.parse import urlparse
from crawler.url_manager import URLManager


@pytest.fixture
def url_manager() -> URLManager:
    """Fixture to create a URLManager instance with a specified allowed domain."""
    return URLManager(allowed_domain="monzo.com")


def test_should_visit(url_manager: URLManager) -> None:
    """Test the should_visit method of URLManager."""
    url = "https://monzo.com/page"
    assert url_manager.should_visit(url) is True

    url = "https://otherdomain.com/page"
    assert url_manager.should_visit(url) is False

    url_manager.mark_visited(url)
    assert url_manager.should_visit(url) is False


def test_mark_visited(url_manager: URLManager) -> None:
    """Test the mark_visited method of URLManager."""
    url = "https://monzo.com/page"
    url_manager.mark_visited(url)
    assert url in url_manager.visited_urls


@pytest.mark.parametrize("url, expected_domain", [
    ("https://monzo.com/page", "monzo.com"),
    ("http://sub.monzo.com/page", "sub.monzo.com"),
    ("https://otherdomain.com/page", "otherdomain.com"),
])
def test_urlparse(url: str, expected_domain: str) -> None:
    """Test the extraction of domain using urlparse."""
    parsed_url = urlparse(url)
    assert parsed_url.netloc == expected_domain
