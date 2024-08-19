from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Validate if the provided URL is well-formed.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is well-formed, False otherwise.
    """
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)
