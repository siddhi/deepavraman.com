"""Fetch remote article HTML."""

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResponse:
    """Container for an HTTP fetch result."""

    body: bytes
    url: str  # Final URL after redirects
    status_code: int


class Fetcher:
    """Simple HTTP fetcher with a browser-like User-Agent."""

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def fetch(self, url: str) -> FetchResponse:
        """Download the page at ``url`` and return its bytes plus final URL."""
        logger.info("Fetching %s", url)
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error for %s: %s", url, exc)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("Network error fetching %s: %s", url, exc)
            raise

        logger.info("Fetched %s (status=%d, final=%s)", url, response.status_code, response.url)
        return FetchResponse(
            body=response.content,
            url=response.url,
            status_code=response.status_code,
        )
