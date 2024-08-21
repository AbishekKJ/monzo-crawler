# monzo-crawler
Problem
We'd like you to write a simple web crawler in a programming language you're familiar with. Given a starting URL, the crawler should visit each URL it finds on the same domain. It should print each URL visited, and a list of links found on that page. The crawler should be limited to one subdomain - so when you start with *https://monzo.com/*, it would crawl all pages on the monzo.com website, but not follow external links, for example to facebook.com or community.monzo.com.

How to run

```python
poetry run python main.py https://monzo.com --max_depth=1 --workers=5
```

Configuration
The following attributes are configurable via config/<environment>.yaml

workers:

controls the maximum number of threads that can run concurrently

max_depth:
number of levels to go down while fetching urls. Each time we follow the links present on a url, we increase a level.

total:
number of retries to make if fetching of url fails

backoff_factor:
The base value for introducing a delay between retries, preventing server overload.

status_forcelist:
A list of HTTP status codes that should trigger a retry for Python requests
