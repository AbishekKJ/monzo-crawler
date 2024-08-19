import re
from urllib.parse import urlparse
from typing import Dict, Set


class RobotsParser:
    def __init__(self, robots_txt: str):
        self.rules = self._parse_robots_txt(robots_txt)

    def _parse_robots_txt(self, robots_txt: str) -> Dict[str, Set[str]]:
        """
        Parse the robots.txt content to extract rules.

        Args:
            robots_txt (str): The content of robots.txt.

        Returns:
            Dict[str, Set[str]]: A dictionary where keys are user-agents and values are sets of disallowed paths.
        """
        rules = {}
        current_user_agent = "*"
        disallowed_paths = set()

        for line in robots_txt.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.lower().startswith("user-agent:"):
                current_user_agent = line.split(":", 1)[1].strip()
                rules[current_user_agent] = disallowed_paths
                disallowed_paths = set()
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                disallowed_paths.add(path)

        if current_user_agent not in rules:
            rules[current_user_agent] = disallowed_paths

        return rules

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """
        Check if the URL is allowed by the robots.txt rules for a given user-agent.

        Args:
            url (str): The URL to check.
            user_agent (str): The user-agent to check the rules for.

        Returns:
            bool: True if allowed, False otherwise.
        """
        parsed_url = urlparse(url)
        path = parsed_url.path
        rules = self.rules.get(user_agent, set())
        return all(not re.match(rf"^{rule}", path) for rule in rules)
