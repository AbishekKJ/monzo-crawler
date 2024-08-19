import re
from urllib.parse import urljoin


def parse_links(html_content, base_url):
    """
    Extracts all the anchor tag links from the HTML content and resolves relative URLs to absolute URLs.

    :param html_content: The HTML content of the page as a string.
    :param base_url: The base URL to resolve relative links.
    :return: A set of fully qualified URLs found in the HTML content.
    """
    # Regular expression to match href links in anchor tags
    href_regex = r'href=[\'"]?([^\'" >]+)'

    # Find all matches of the regex in the HTML content
    links = re.findall(href_regex, html_content)

    # Resolve relative links using the base URL
    absolute_links = {urljoin(base_url, link) for link in links}

    return absolute_links
