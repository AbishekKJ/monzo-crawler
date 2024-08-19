import pytest
from unittest.mock import patch, MagicMock, call, ANY
from requests.adapters import HTTPAdapter
from crawler.crawler import Crawler
from crawler.url_manager import URLManager
from crawler.parser import parse_links
from crawler.url_manager import URLManager
import requests
import logging
from collections import deque
from urllib.parse import urlparse


@pytest.fixture
def mock_url_manager():
    """Fixture to mock URLManager."""
    with patch('crawler.url_manager.URLManager') as mock:
        yield mock


@pytest.fixture
def mock_parser():
    """Fixture to mock parse_links."""
    with patch('crawler.parser.parse_links') as mock:
        yield mock


@pytest.fixture
def mock_requests_session():
    """Fixture to mock requests.Session."""
    with patch('crawler.crawler.requests.Session') as mock_session:
        yield mock_session.return_value


@pytest.fixture
def crawler_instance(mock_parser, mock_url_manager):
    """Fixture to create a Crawler instance with mocked dependencies."""
    return Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2)


def test_initialization(crawler_instance):
    """Test initialization of the Crawler class."""
    crawler = crawler_instance
    assert crawler.start_url == "https://monzo.com"
    assert crawler.allowed_domain == "monzo.com"
    assert crawler.max_depth == 2
    assert crawler.max_workers == 2
    assert isinstance(crawler.url_manager, URLManager)
    assert isinstance(crawler.logger, logging.Logger)
    assert isinstance(crawler.session, requests.Session)
    assert isinstance(crawler.queue, deque)
    assert isinstance(crawler.visited, set)
    assert crawler.output_file.startswith("urls_")


def test_create_session_with_retries(mock_requests_session):
    """Test the creation of a requests session with retries."""
    crawler = Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2)
    session = crawler._create_session_with_retries()

    assert session is mock_requests_session

    # Check `mount` calls for HTTP and HTTPS adapters
    assert mock_requests_session.mount.call_count == 4
    assert mock_requests_session.mount.call_args_list[0] == call('http://', ANY)
    assert mock_requests_session.mount.call_args_list[1] == call('https://', ANY)

    # Verify the HTTPAdapter configuration
    http_adapter = mock_requests_session.mount.call_args_list[0][0][1]
    assert isinstance(http_adapter, HTTPAdapter)
    assert http_adapter.max_retries.total == 5
    assert http_adapter.max_retries.backoff_factor == 0.3


def test_fetch_success(mock_requests_session):
    """Test the fetch method for successful requests."""

    # Create a mock response object
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.raise_for_status.return_value = None  # Simulate successful request

    # Set the mock session's get method to return the mock response
    mock_requests_session.return_value.get.return_value = mock_response

    # Create the crawler instance, injecting the mock session
    crawler = Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2,
                      session=mock_requests_session.return_value)

    # Call the _fetch method
    html_content = crawler._fetch("https://monzo.com")

    print("HTML Content fetched:", html_content)  # Debugging line

    # Assertions
    assert html_content == "<html></html>"
    mock_requests_session.return_value.get.assert_called_once_with("https://monzo.com", timeout=5)
    mock_response.raise_for_status.assert_called_once()


def test_fetch_failure(mock_requests_session):
    """Test the fetch method for failed requests."""

    # Make the session's get method raise a RequestException
    mock_requests_session.return_value.get.side_effect = requests.RequestException("Failed to fetch")

    # Create the crawler instance, injecting the mock session
    crawler = Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2,
                      session=mock_requests_session.return_value)

    # Call the _fetch method
    html_content = crawler._fetch("https://monzo.com")

    print("HTML Content fetched on failure:", html_content)  # Debugging line

    # Assertions
    assert html_content is None  # Should return None on failure
    mock_requests_session.return_value.get.assert_called_once_with("https://monzo.com", timeout=5)


def test_crawl(crawler_instance):
    """Test the crawl method with basic mocks."""
    # Mock the _fetch method to return fixed HTML content
    with patch.object(crawler_instance, '_fetch', return_value="""<html>
            <head><title>Test</title></head>
            <body>
                <a href="https://monzo.com/page1">Page 1</a>
                <a href="https://monzo.com/page2">Page 2</a>
            </body>
        </html>"""):
        links = crawler_instance.crawl("https://monzo.com", 0)
    # Verify the result of the crawl method
    assert links == {"https://monzo.com/page1", "https://monzo.com/page2"}


def test_run(crawler_instance, mock_parser, mock_url_manager):
    """Test the run method."""
    mock_parser.return_value = {"https://monzo.com/page1"}
    mock_url_manager.should_visit.return_value = True

    with patch.object(crawler_instance, 'write_urls_to_file') as mock_write:
        crawler_instance.run()
        mock_write.assert_called_once()


@pytest.mark.parametrize("url, expected_result", [
    ("https://monzo.com", "monzo.com"),
    ("http://sub.monzo.com", "sub.monzo.com"),
])
def test_allowed_domain(url, expected_result, crawler_instance):
    """Test extraction of allowed domain from URL."""
    crawler_instance.start_url = url
    crawler_instance.allowed_domain = urlparse(url).netloc
    assert crawler_instance.allowed_domain == expected_result
