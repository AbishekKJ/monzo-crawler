import pytest
from unittest.mock import patch, MagicMock, call, ANY
from requests.adapters import HTTPAdapter
from crawler.crawler import Crawler
from crawler.url_manager import URLManager
from crawler.parser import parse_links
import requests
import logging
from collections import deque
from urllib.parse import urlparse


@pytest.fixture
def mock_url_manager() -> URLManager:
    """Fixture to mock URLManager."""
    with patch('crawler.url_manager.URLManager') as mock:
        yield mock


@pytest.fixture
def mock_parser() -> MagicMock:
    """Fixture to mock parse_links."""
    with patch('crawler.parser.parse_links') as mock:
        yield mock


@pytest.fixture
def mock_requests_session() -> MagicMock:
    """Fixture to mock requests.Session."""
    with patch('crawler.crawler.requests.Session') as mock_session:
        yield mock_session.return_value


@pytest.fixture
def crawler_instance(mock_parser: MagicMock, mock_url_manager: URLManager) -> Crawler:
    """Fixture to create a Crawler instance with mocked dependencies."""
    return Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2)


def test_initialization(crawler_instance: Crawler) -> None:
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


def test_create_session_with_retries(mock_requests_session: MagicMock) -> None:
    """Test the creation of a requests session with retries."""
    crawler = Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2)
    session = crawler._create_session_with_retries()

    assert session is mock_requests_session
    assert mock_requests_session.mount.call_count == 4
    assert mock_requests_session.mount.call_args_list[0] == call('http://', ANY)
    assert mock_requests_session.mount.call_args_list[1] == call('https://', ANY)

    http_adapter = mock_requests_session.mount.call_args_list[0][0][1]
    assert isinstance(http_adapter, HTTPAdapter)
    assert http_adapter.max_retries.total == 3
    assert http_adapter.max_retries.backoff_factor == 0.3


def test_fetch_success(mock_requests_session: MagicMock) -> None:
    """Test the fetch method for successful requests."""
    mock_response = MagicMock()
    mock_response.text = "<html></html>"
    mock_response.raise_for_status.return_value = None

    mock_requests_session.return_value.get.return_value = mock_response

    crawler = Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2,
                      session=mock_requests_session.return_value)

    html_content = crawler._fetch("https://monzo.com")

    assert html_content == "<html></html>"


def test_fetch_failure(mock_requests_session: MagicMock) -> None:
    """Test the fetch method for failed requests."""
    mock_requests_session.return_value.get.side_effect = requests.RequestException("Failed to fetch")

    crawler = Crawler(start_url="https://monzo.com", max_depth=2, max_workers=2,
                      session=mock_requests_session.return_value)

    html_content = crawler._fetch("https://monzo.com")

    assert html_content is None


def test_crawl(crawler_instance: Crawler) -> None:
    """Test the crawl method with basic mocks."""
    with patch.object(crawler_instance, '_fetch', return_value="""<html>
            <head><title>Test</title></head>
            <body>
                <a href="https://monzo.com/page1">Page 1</a>
                <a href="https://monzo.com/page2">Page 2</a>
            </body>
        </html>"""):
        links = crawler_instance.crawl("https://monzo.com", 0)

    assert links == {"https://monzo.com/page1", "https://monzo.com/page2"}


def test_run(crawler_instance: Crawler, mock_parser: MagicMock, mock_url_manager: URLManager) -> None:
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
def test_allowed_domain(url: str, expected_result: str, crawler_instance: Crawler) -> None:
    """Test extraction of allowed domain from URL."""
    crawler_instance.start_url = url
    crawler_instance.allowed_domain = urlparse(url).netloc
    assert crawler_instance.allowed_domain == expected_result
