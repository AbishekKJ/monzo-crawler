from urllib.parse import urlparse


class URLManager:
    def __init__(self, allowed_domain):
        self.allowed_domain = allowed_domain
        self.visited_urls = set()

    def should_visit(self, url, depth):
        parsed_url = urlparse(url)
        # Ensure the domain matches the allowed domain and the URL has not been visited yet
        if parsed_url.netloc != self.allowed_domain or url in self.visited_urls:
            return False
        return True

    def mark_visited(self, url):
        self.visited_urls.add(url)

    def add_links(self, links):
        return {link for link in links if self.should_visit(link, 0)}