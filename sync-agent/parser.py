"""Parse remote article HTML into structured data."""

import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedArticle:
    """Structured representation of an extracted article."""

    title: str
    author: str | None
    publication: str
    published_date: date
    url: str
    body_paragraphs: list[str]
    images: list[tuple[str, str]]  # (image_url, alt_text)


class Parser:
    """Extract article metadata and body from arbitrary news HTML."""

    PUBLICATION_MAP: dict[str, str] = {
        "thehindu.com": "The Hindu",
        "thenewsminute.com": "The News Minute",
        "thehindubusinessline.com": "Business Line",
        "indianexpress.com": "The Indian Express",
        "deccanherald.com": "Deccan Herald",
        "newindianexpress.com": "The New Indian Express",
        "hindustantimes.com": "Hindustan Times",
    }

    # HTML selectors used to locate the main article body.
    BODY_SELECTORS = [
        "article",
        "main",
        '[itemprop="articleBody"]',
        '[itemprop="mainEntity"]',
        ".article-body",
        ".story-body",
        ".article_content",
        ".content__article-body",
        ".story_details",
        "#article-body",
        "#content-main",
        "#main-content",
        ".entry-content",
        ".post-content",
    ]

    def parse(self, html: bytes | str, url: str) -> ParsedArticle:
        """Parse ``html`` and return a :class:`ParsedArticle`."""
        soup = BeautifulSoup(html, "lxml")

        canonical_url = self._canonical_url(soup, url)
        title = self._extract_title(soup)
        author = self._extract_author(soup)
        publication = self._publication_from_url(canonical_url, soup)
        published_date = self._extract_date(soup, canonical_url)
        body_node = self._find_body_node(soup)
        paragraphs = self._extract_paragraphs(body_node)
        images = self._extract_images(body_node or soup, canonical_url)

        if not title:
            title = "Untitled Import"
            logger.warning("Could not extract title from %s", canonical_url)

        if not paragraphs:
            logger.warning("Could not extract body paragraphs from %s; using fallback", canonical_url)
            paragraphs = self._fallback_paragraphs(soup)

        logger.info(
            "Parsed article: title=%r publication=%r date=%s paragraphs=%d images=%d",
            title,
            publication,
            published_date.isoformat(),
            len(paragraphs),
            len(images),
        )

        return ParsedArticle(
            title=title,
            author=author,
            publication=publication,
            published_date=published_date,
            url=canonical_url,
            body_paragraphs=paragraphs,
            images=images[:5],  # Keep only the first five images.
        )

    # -----------------------------------------------------------------------
    # URL helpers
    # -----------------------------------------------------------------------
    def _canonical_url(self, soup: BeautifulSoup, request_url: str) -> str:
        canonical = soup.find("link", rel="canonical")
        if isinstance(canonical, Tag) and canonical.get("href"):
            return urljoin(request_url, str(canonical["href"]).strip())
        og_url = soup.find("meta", property="og:url")
        if isinstance(og_url, Tag) and og_url.get("content"):
            return urljoin(request_url, str(og_url["content"]).strip())
        return request_url

    def _normalise_url(self, url: str) -> str:
        """Strip fragments/query noise for duplicate comparison."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    # -----------------------------------------------------------------------
    # Publication detection
    # -----------------------------------------------------------------------
    def _publication_from_url(self, url: str, soup: BeautifulSoup) -> str:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip("www.")
        for suffix, name in self.PUBLICATION_MAP.items():
            if domain.endswith(suffix):
                return name

        # Try schema.org / JSON-LD publisher name.
        jsonld = self._jsonld(soup)
        publisher = self._walk(jsonld, "publisher", "name")
        if publisher:
            return str(publisher)

        # Fallback to a cleaned version of the netloc.
        display = parsed.netloc.replace("www.", "").replace("-", " ")
        return display.title() if display.islower() else display

    # -----------------------------------------------------------------------
    # Title extraction
    # -----------------------------------------------------------------------
    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if isinstance(og_title, Tag) and og_title.get("content"):
            return str(og_title["content"]).strip()

        twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
        if isinstance(twitter_title, Tag) and twitter_title.get("content"):
            return str(twitter_title["content"]).strip()

        h1 = soup.find("h1")
        if isinstance(h1, Tag):
            text = self._clean_text(h1.get_text())
            if text:
                return text

        title_tag = soup.find("title")
        if isinstance(title_tag, Tag):
            text = self._clean_text(title_tag.get_text())
            if text:
                return text

        return ""

    # -----------------------------------------------------------------------
    # Author extraction
    # -----------------------------------------------------------------------
    def _extract_author(self, soup: BeautifulSoup) -> str | None:
        for prop in ("author", "article:author"):
            meta = soup.find("meta", attrs={"name": prop}) or soup.find("meta", property=prop)
            if isinstance(meta, Tag) and meta.get("content"):
                text = self._clean_text(str(meta["content"]))
                if text:
                    return text

        jsonld = self._jsonld(soup)
        for key in ("author", "creator"):
            value = self._walk(jsonld, key)
            if isinstance(value, str):
                return self._clean_text(value)
            if isinstance(value, dict):
                name = value.get("name")
                if isinstance(name, str):
                    return self._clean_text(name)
            if isinstance(value, list) and value:
                first = value[0]
                if isinstance(first, dict):
                    name = first.get("name")
                    if isinstance(name, str):
                        return self._clean_text(name)
                if isinstance(first, str):
                    return self._clean_text(first)

        # HTML byline patterns.
        for selector in (
            "[class*=byline]",
            ".author",
            ".article-author",
            "[rel=author]",
            "[itemprop=author]",
        ):
            node = soup.select_one(selector)
            if node:
                text = self._clean_text(node.get_text())
                if text and len(text) < 200:
                    return text

        return None

    # -----------------------------------------------------------------------
    # Date extraction
    # -----------------------------------------------------------------------
    def _extract_date(self, soup: BeautifulSoup, url: str) -> date:
        raw_date: str | None = None

        for prop in ("article:published_time", "datePublished", "publish-date", "DC.date.issued"):
            meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if isinstance(meta, Tag) and meta.get("content"):
                raw_date = str(meta["content"]).strip()
                break

        if not raw_date:
            time_tag = soup.find("time")
            if isinstance(time_tag, Tag):
                raw_date = str(time_tag.get("datetime", "")).strip() or self._clean_text(time_tag.get_text())

        if not raw_date:
            jsonld = self._jsonld(soup)
            for key in ("datePublished", "dateCreated", "dateModified"):
                value = self._walk(jsonld, key)
                if isinstance(value, str):
                    raw_date = value
                    break

        parsed = self._parse_date(raw_date)
        if parsed:
            return parsed

        logger.warning("Could not extract date from %s; using today as fallback", url)
        return date.today()

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None

        # Drop timezone suffixes like +05:30 / Z and process common formats.
        cleaned = re.sub(r"Z$", "+00:00", value.strip())
        cleaned = re.sub(r"\.[0-9]+(?:[+-][0-9:]+)?$", "", cleaned)

        # Try ISO 8601 first.
        try:
            return datetime.fromisoformat(cleaned).date()
        except ValueError:
            pass

        for fmt in (
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ):
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue

        # Date-only regex fallback.
        match = re.search(r"(20\d{2})[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])", cleaned)
        if match:
            year, month, day = map(int, match.groups())
            return date(year, month, day)

        return None

    # -----------------------------------------------------------------------
    # Body extraction
    # -----------------------------------------------------------------------
    def _find_body_node(self, soup: BeautifulSoup) -> Tag | None:
        for selector in self.BODY_SELECTORS:
            node = soup.select_one(selector)
            if node:
                return node

        # Secondary heuristic: the largest <div> that contains many <p> tags.
        candidates = []
        for div in soup.find_all("div"):
            paragraphs = div.find_all("p")
            if len(paragraphs) >= 4:
                text_len = len(div.get_text(strip=True))
                candidates.append((text_len, div))
        if candidates:
            return max(candidates, key=lambda item: item[0])[1]

        return None

    def _extract_paragraphs(self, node: Tag | None) -> list[str]:
        if not node:
            return []

        # Remove non-content elements.
        for tag in node.find_all(["script", "style", "nav", "aside", "footer"]):
            tag.decompose()
        for tag in node.find_all(class_=re.compile(r"share|social|comment|related|widget|newsletter|ads")):
            tag.decompose()

        paragraphs: list[str] = []
        for child in node.descendants:
            if child.name in ("p", "div", "section") and child.parent is not None:
                text = self._clean_text(child.get_text())
                if text and len(text) > 15:
                    paragraphs.append(text)

        # De-duplicate while preserving order.
        seen: set[str] = set()
        unique: list[str] = []
        for p in paragraphs:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    def _fallback_paragraphs(self, soup: BeautifulSoup) -> list[str]:
        for tag in soup.find_all(["script", "style", "nav", "aside", "footer", "header"]):
            tag.decompose()
        texts: list[str] = []
        for p in soup.find_all("p"):
            text = self._clean_text(p.get_text())
            if len(text) > 40:
                texts.append(text)
        return texts or [""]

    # -----------------------------------------------------------------------
    # Image extraction
    # -----------------------------------------------------------------------
    def _extract_images(self, node: Tag | None, base_url: str) -> list[tuple[str, str]]:
        if not node:
            return []

        images: list[tuple[str, str]] = []
        seen: set[str] = set()

        for img in node.find_all("img"):
            if not isinstance(img, Tag):
                continue
            src = img.get("src") or img.get("data-src") or img.get("data-original")
            if not src:
                continue
            src = urljoin(base_url, str(src).strip())
            if src in seen:
                continue
            seen.add(src)

            # Skip common non-article assets.
            lower = src.lower()
            if any(x in lower for x in ("logo", "icon", "avatar", "social", "share", "tracked", "/ads/")):
                continue
            if lower.startswith("data:"):
                continue

            alt = self._clean_text(str(img.get("alt", "")))
            width = img.get("width")
            try:
                if width and int(width) < 80:
                    continue
            except (ValueError, TypeError):
                pass

            images.append((src, alt))

        return images

    # -----------------------------------------------------------------------
    # JSON-LD helpers
    # -----------------------------------------------------------------------
    def _jsonld(self, soup: BeautifulSoup) -> dict[str, Any] | list[Any] | None:
        data: Any = None
        for script in soup.find_all("script", type="application/ld+json"):
            if not isinstance(script, Tag):
                continue
            try:
                parsed = json.loads(script.string or "")
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, list):
                news = [item for item in parsed if isinstance(item, dict) and item.get("@type") in ("NewsArticle", "Article", "WebPage")]
                if news:
                    return news[0]
                data = parsed[0] if parsed and data is None else data
            elif isinstance(parsed, dict):
                if parsed.get("@type") in ("NewsArticle", "Article", "WebPage"):
                    return parsed
                if "@graph" in parsed:
                    graph = parsed["@graph"]
                    news = [
                        item
                        for item in graph
                        if isinstance(item, dict) and item.get("@type") in ("NewsArticle", "Article")
                    ]
                    if news:
                        return news[0]
                if data is None:
                    data = parsed

        return data

    def _walk(self, data: Any, *keys: str) -> Any:
        if not isinstance(data, dict):
            return None

        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    # -----------------------------------------------------------------------
    # Text cleaning
    # -----------------------------------------------------------------------
    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        # Collapse whitespace and non-breaking spaces.
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\u00a0", " ")
        return text.strip()
