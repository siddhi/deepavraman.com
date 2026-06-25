"""Convert a parsed article into a Pelican-compatible reST document."""

import re
from dataclasses import dataclass
from datetime import date

from parser import ParsedArticle


@dataclass(frozen=True)
class RstDocument:
    """Pelican article rendered as reStructuredText."""

    title: str
    slug: str
    date: date
    category: str
    tags: str
    summary: str
    body: str
    source_url: str

    def render(self) -> str:
        """Render the document to reST."""
        underline = "=" * max(len(self.title), 3)
        lines = [
            self.title,
            underline,
            "",
            f":date: {self.date:%Y-%m-%d}",
            f":category: {self.category}",
            f":tags: {self.tags}",
            f":slug: {self.slug}",
            f":summary: {self.summary}",
            "",
            self.body,
            "",
        ]
        return "\n".join(lines)


class Converter:
    """Build a Pelican article from a :class:`ParsedArticle`."""

    DEFAULT_CATEGORY = "Articles"

    def convert(self, article: ParsedArticle) -> RstDocument:
        slug = self._slugify(article.title)
        summary = self._make_summary(article)
        body = self._make_body(article)

        return RstDocument(
            title=article.title,
            slug=slug,
            date=article.published_date,
            category=self.DEFAULT_CATEGORY,
            tags=article.publication,
            summary=summary,
            body=body,
            source_url=article.url,
        )

    @staticmethod
    def _slugify(title: str) -> str:
        """Create a URL-safe slug from the article title."""
        base = title.lower()
        base = re.sub(r"[^\w\s-]", "", base)
        base = re.sub(r"[-\s]+", "-", base).strip("-")
        # Limit length to keep filenames manageable.
        if len(base) > 80:
            base = base[:80].rsplit("-", 1)[0]
        return base or "article"

    def _content_paragraphs(self, article: ParsedArticle) -> list[str]:
        """Return body paragraphs that are real content, not bylines."""
        paragraphs: list[str] = []
        for paragraph in article.body_paragraphs:
            stripped = paragraph.strip()
            if not stripped:
                continue
            if article.author and stripped.lower().startswith(f"by {article.author.lower()}"):
                continue
            if stripped.lower().startswith("by ") and len(stripped) < 80:
                continue
            paragraphs.append(stripped)
        return paragraphs

    def _make_summary(self, article: ParsedArticle) -> str:
        """Generate a short summary from the first meaningful paragraph."""
        for paragraph in self._content_paragraphs(article):
            if len(paragraph) <= 160:
                return paragraph
            truncated = paragraph[:157].rsplit(" ", 1)[0]
            return f"{truncated}..."
        return f"Article from {article.publication}"

    def _make_body(self, article: ParsedArticle) -> str:
        lines: list[str] = [f"{article.publication}: {article.url}"]

        if article.author:
            lines.append("")
            lines.append(f"By {article.author}.")

        if article.images:
            lines.append("")
            for src, alt in article.images:
                lines.append(f".. image:: {src}")
                if alt:
                    lines.append(f"    :alt: {alt}")
                lines.append("")

        lines.append("")
        for paragraph in self._content_paragraphs(article):
            lines.append(paragraph)
            lines.append("")

        return "\n".join(lines).strip()
