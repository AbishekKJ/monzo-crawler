import pytest
from unittest.mock import patch
from urllib.parse import urlparse
from crawler.url_manager import URLManager


@pytest.fixture
def url_manager():
    """Fixture to create a URLManager instance."""
    return URLManager(allowed_domain="monzo.com")


def test_should_visit(url_manager):
    """Test the should_visit method."""
    # Test case: URL is within the allowed domain and not visited
    url = "https://monzo.com/page"
    assert url_manager.should_visit(url, 0) == True

    # Test case: URL is outside the allowed domain
    url = "https://otherdomain.com/page"
    assert url_manager.should_visit(url, 0) == False

    # Test case: URL has been visited
    url_manager.mark_visited(url)
    assert url_manager.should_visit(url, 0) == False


def test_mark_visited(url_manager):
    """Test the mark_visited method."""
    url = "https://monzo.com/page"
    url_manager.mark_visited(url)
    assert url in url_manager.visited_urls


def test_add_links(url_manager):
    """Test the add_links method."""
    links = [
        "https://monzo.com/page1",
        "https://monzo.com/page2",
        "https://otherdomain.com/page"
    ]
    url_manager.mark_visited("https://monzo.com/page1")  # Pre-mark a URL as visited

    result = url_manager.add_links(links)

    # Ensure that only links within the allowed domain and not visited are returned
    expected_result = {"https://monzo.com/page2"}
    assert result == expected_result


@pytest.mark.parametrize("url, expected_domain", [
    ("https://monzo.com/page", "monzo.com"),
    ("http://sub.monzo.com/page", "sub.monzo.com"),
    ("https://otherdomain.com/page", "otherdomain.com"),
])
def test_urlparse(url, expected_domain):
    """Test the extraction of domain using urlparse."""
    parsed_url = urlparse(url)
    assert parsed_url.netloc == expected_domain
