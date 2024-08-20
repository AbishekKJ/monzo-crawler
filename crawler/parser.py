import re
from urllib.parse import urljoin, urlparse
from typing import Set
from exceptions import InvalidBaseURLError, InvalidHTMLContentError, ParseLinksException


def parse_links(html_content: str, base_url: str) -> Set[str]:
    """
    Extracts all the anchor tag links from the HTML content and resolves relative URLs to absolute URLs.

    Args:
        html_content (str): The HTML content of the page as a string.
        base_url (str): The base URL to resolve relative links.

    Returns:
        Set[str]: A set of fully qualified URLs found in the HTML content.
    """
    if not isinstance(html_content, str) or not html_content:
        raise InvalidHTMLContentError("Invalid HTML content provided. Content must be a non-empty string.")

    if not isinstance(base_url, str) or not urlparse(base_url).scheme:
        raise InvalidBaseURLError("Invalid base URL provided. URL must be a valid URL with a scheme.")

    href_regex = r'href=[\'"]([^\'" >]+(?: [^\'" >]+)*)[\'"]'

    try:
        links = re.findall(href_regex, html_content)
    except re.error as e:
        raise ParseLinksException(f"Regular expression error: {e}")

    # Resolve relative links using the base URL and handle multiple URLs in a single href
    absolute_links = set()
    for link_group in links:
        for link in link_group.split():
            try:
                absolute_links.add(urljoin(base_url, link))
            except Exception as e:
                raise ParseLinksException(f"URL join error: {e}")

    return absolute_links
