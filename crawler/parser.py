import re
from urllib.parse import urljoin
from typing import Set

def parse_links(html_content: str, base_url: str) -> Set[str]:
    """
    Extracts all the anchor tag links from the HTML content and resolves relative URLs to absolute URLs.

    Args:
        html_content (str): The HTML content of the page as a string.
        base_url (str): The base URL to resolve relative links.

    Returns:
        Set[str]: A set of fully qualified URLs found in the HTML content.
    """
    # Regular expression to match href links in anchor tags
    href_regex = r'href=[\'"]([^\'" >]+(?: [^\'" >]+)*)[\'"]'

    # Find all matches of the regex in the HTML content
    links = re.findall(href_regex, html_content)

    # Resolve relative links using the base URL and handle multiple URLs in a single href
    absolute_links = set()
    for link_group in links:
        for link in link_group.split():
            absolute_links.add(urljoin(base_url, link))

    return absolute_links
