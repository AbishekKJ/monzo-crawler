import pytest
import re
from urllib.parse import urljoin
from crawler.parser import parse_links

def test_parse_links_absolute_urls():
    """Test extracting and resolving absolute URLs."""
    html_content = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <a href="https://monzo.com/page1">Page 1</a>
                <a href="https://monzo.com/page2">Page 2</a>
            </body>
        </html>
    '''
    base_url = "https://monzo.com"
    expected_links = {
        "https://monzo.com/page1",
        "https://monzo.com/page2"
    }

    result = parse_links(html_content, base_url)

    assert result == expected_links

def test_parse_links_relative_urls():
    """Test extracting and resolving relative URLs."""
    html_content = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <a href="/page1">Page 1</a>
                <a href="page2">Page 2</a>
            </body>
        </html>
    '''
    base_url = "https://monzo.com"
    expected_links = {
        "https://monzo.com/page1",
        "https://monzo.com/page2"
    }

    result = parse_links(html_content, base_url)

    assert result == expected_links

def test_parse_links_no_links():
    """Test HTML content with no links."""
    html_content = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <p>No links here!</p>
            </body>
        </html>
    '''
    base_url = "https://monzo.com"
    expected_links = set()

    result = parse_links(html_content, base_url)

    assert result == expected_links

def test_parse_links_empty_html():
    """Test empty HTML content."""
    html_content = ''
    base_url = "https://monzo.com"
    expected_links = set()

    result = parse_links(html_content, base_url)

    assert result == expected_links

def test_parse_links_multiple_hrefs():
    """Test HTML content with multiple hrefs in one anchor tag."""
    html_content = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <a href="https://monzo.com/page1 https://monzo.com/page2">Pages</a>
            </body>
        </html>
    '''
    base_url = "https://monzo.com"
    expected_links = {
        "https://monzo.com/page1",
        "https://monzo.com/page2"
    }

    result = parse_links(html_content, base_url)
    assert result == expected_links

def test_parse_links_with_fragment():
    """Test HTML content with fragment in href."""
    html_content = '''
        <html>
            <head><title>Test</title></head>
            <body>
                <a href="/page1#section">Page 1</a>
            </body>
        </html>
    '''
    base_url = "https://monzo.com"
    expected_links = {
        "https://monzo.com/page1#section"
    }

    result = parse_links(html_content, base_url)

    assert result == expected_links
