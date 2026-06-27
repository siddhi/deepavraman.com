#!/usr/bin/env python3
"""Import a The Hindu article into the deepavraman.com Pelican site.

Usage:
    uv run .pi/skills/hindu-article-import/scripts/import_hindu_article.py <URL>
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse, urlsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONTENT_DIR = PROJECT_ROOT / "content"
IMAGES_BASE = CONTENT_DIR / "images"

THE_HINDU_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def clean_text(t: str | None) -> str:
    if not t:
        return ""
    return re.sub(r"[\s\u00a0]+", " ", t).strip()


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": THE_HINDU_UA, "Accept": "text/html,*/*;q=0.9"})
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def is_ad_url(url: str) -> bool:
    if not url:
        return True
    ad_patterns = [
        "doubleclick", "googlesyndication", "googleads", "googletagmanager",
        "google-analytics", "facebook.com/tr", "adsystem", "taboola", "outbrain",
        "adsrvr", "scorecardresearch", "pubmatic", "casalemedia", "openx",
        "rubiconproject", "adform", "liveramp", "crwdcntrl", "3lift",
        "sharethrough", "adsymptotic", "bidswitch", "contextweb", "yieldmo",
        "districtm", "indexww", "semasio", "socdm", "tiqcdn", "teads",
        "adsafeprotected", "moatads", "iasds", "1x1_spacer", "/adsct", "/ad_status",
    ]
    low = url.lower()
    return any(p in low for p in ad_patterns)


def sanitise_filename(name: str) -> str:
    name = unquote(name)
    return re.sub(r"[^\w\-.]", "_", Path(name).name)


def download_image(url: str, dest_dir: Path, used_names: set[str]) -> str:
    """Download an image with a browser UA and return its local filename."""
    filename = sanitise_filename(url.split("?")[0]) or "image.jpg"
    if not Path(filename).suffix:
        filename += ".jpg"
    if filename in used_names:
        stem = Path(filename).stem
        suffix = Path(filename).suffix or ".jpg"
        counter = 1
        while f"{stem}_{counter}{suffix}" in used_names:
            counter += 1
        filename = f"{stem}_{counter}{suffix}"
    used_names.add(filename)
    dest = dest_dir / filename
    req = Request(url, headers={
        "User-Agent": THE_HINDU_UA,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.thehindu.com/",
    })
    with urlopen(req, timeout=20) as resp:
        dest.write_bytes(resp.read())
    return filename


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


@dataclass
class ArticleImage:
    url: str
    alt: str = ""
    caption: str = ""
    local_name: str = ""


@dataclass
class Article:
    title: str = "Untitled"
    url: str = ""
    published: str = ""
    updated: str = ""
    summary: str = ""
    body_blocks: list[str | ArticleImage] = field(default_factory=list)
    lead_image: ArticleImage | None = None


def extract_dates(soup: BeautifulSoup) -> tuple[str, str]:
    updated = ""
    published = ""
    for el in soup.find_all(["p", "span", "div", "time"]):
        if not isinstance(el, Tag):
            continue
        txt = clean_text(el.get_text())
        if len(txt) > 200:
            continue
        if not updated:
            m = re.search(r"Updated[\s:-]*([A-Za-z]+\s+\d{1,2},\s*\d{4}[^\n]*?IST)", txt)
            if m:
                updated = m.group(1).strip()
        if not published:
            m = re.search(r"Published[\s:-]*([A-Za-z]+\s+\d{1,2},\s*\d{4}[^\n]*?IST)", txt)
            if m:
                published = m.group(1).strip()
    return published, updated


def normalise_img_url(img: Tag) -> str:
    for attr in ("data-original", "data-src", "src"):
        v = img.get(attr)
        if v and not isinstance(v, str):
            v = str(v)
        if v and not v.endswith("1x1_spacer.png"):
            return v
    return ""


def select_best_image_url(urls: list[str]) -> str:
    """Prefer the largest image when alternatives are present."""
    def score(u: str) -> int:
        m = re.search(r"LANDSCAPE_(\d+)", u, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"FREE_(\d+)", u, re.I)
        if m:
            return int(m.group(1))
        m = re.search(r"/(\d+)x(\d+)/", u)
        if m:
            return int(m.group(1)) * int(m.group(2))
        return 0
    return max((u for u in urls if not is_ad_url(u)), key=score, default="")


def extract_lead_image(soup: BeautifulSoup) -> ArticleImage | None:
    for picture in soup.find_all("picture"):
        urls: list[str] = []
        img_tag = picture.find("img")
        alt = ""
        if img_tag:
            alt = clean_text(img_tag.get("alt", ""))
            src = normalise_img_url(img_tag)
            if src:
                urls.append(src)
        for source in picture.find_all("source"):
            srcset = source.get("srcset", "")
            for token in re.split(r",\s*", srcset):
                url = token.strip().split()[0]
                if url:
                    urls.append(url)
        chosen = select_best_image_url(urls)
        if chosen:
            return ArticleImage(url=chosen, alt=alt)
    return None


def remove_ad_elements(body: Tag) -> None:
    ad_id_patterns = [
        re.compile(r"google_ads"),
        re.compile(r"taboola[-_]"),
        re.compile(r"^taboola"),
        re.compile(r"^trc_"),
        re.compile(r"offer_"),
        re.compile(r"ps-(video|ad)-"),
        re.compile(r"Inarticle|advertisement|adunit|ad-slot|adslot|inlinead|inline_embed"),
        re.compile(r"articledivtrend|articleicymi|articletopnews|subscribe|share-page"),
        re.compile(r"uspapi|tcfapi|artmeterpv|coral-"),
    ]
    ad_class_keywords = [
        "trc_", "videoCube", "taboola", "advertisement", "ad-container",
        "adunit", "ads", "google-ad", "taboola-below", "trc_related",
        "article-ad", "dfp-ad", "inlinead", "middleonead", "inline_embed",
        "comments-shares", "comment-btn", "read-later", "share-page",
    ]

    for tag in list(body.find_all(True)):
        if not isinstance(tag, Tag) or tag.attrs is None:
            continue
        remove = False
        if tag.get("id"):
            for pat in ad_id_patterns:
                if pat.search(str(tag["id"])):
                    remove = True
                    break
        if not remove and tag.get("class"):
            cls = " ".join(tag["class"]).lower()
            if any(kw in cls for kw in ad_class_keywords):
                remove = True
        if remove:
            tag.decompose()


def _ancestors(tag: Tag) -> list[Tag]:
    ancestors = []
    parent = tag.parent
    while isinstance(parent, Tag):
        ancestors.append(parent)
        parent = parent.parent
    return ancestors


def _is_inside_ad_container(tag: Tag) -> bool:
    ad_class_keywords = [
        "trc_", "videoCube", "taboola", "advertisement", "ad-container",
        "adunit", "ads", "google-ad", "taboola-below", "trc_related",
        "article-ad", "dfp-ad", "inlinead", "middleonead", "inline_embed",
        "comments-shares", "comment-btn", "read-later", "share-page",
        "related-topics",
    ]
    ad_id_patterns = [
        re.compile(r"google_ads|taboola[-_]|^taboola|^trc_|offer_|ps-(video|ad)-"),
        re.compile(r"Inarticle|advertisement|adunit|ad-slot|adslot|inlinead|inline_embed"),
        re.compile(r"articledivtrend|articleicymi|articletopnews|subscribe|share-page"),
        re.compile(r"uspapi|tcfapi|artmeterpv|coral-"),
    ]
    for ancestor in [tag, *_ancestors(tag)]:
        if ancestor.get("id"):
            for pat in ad_id_patterns:
                if pat.search(str(ancestor["id"])):
                    return True
        if ancestor.get("class"):
            cls = " ".join(ancestor["class"]).lower()
            if any(kw in cls for kw in ad_class_keywords):
                return True
    return False


def _collect_blocks(body: Tag) -> list[str | ArticleImage]:
    blocks: list[str | ArticleImage] = []
    processed_p: set[int] = set()

    for tag in body.find_all(["p", "div", "picture"], recursive=True):
        if not isinstance(tag, Tag):
            continue
        if _is_inside_ad_container(tag):
            continue
        if id(tag) in processed_p:
            continue

        if tag.name == "p":
            if "caption" in (tag.get("class") or []):
                continue
            if tag.find_parent("div", class_="article-picture"):
                continue
            text = clean_text(tag.get_text())
            # Drop date/time metadata paragraphs that duplicate frontmatter
            if re.search(r"^(Updated|Published)\s*-\s*[A-Za-z]+\s+\d{1,2},\s*\d{4}", text):
                continue
            if text:
                blocks.append(text)
                processed_p.add(id(tag))
        elif tag.name == "div" and "article-picture" in (tag.get("class") or []):
            img = tag.find("img")
            caption_p = tag.find("p", class_="caption")
            if img:
                url = normalise_img_url(img)
                if url and not is_ad_url(url):
                    caption = clean_text(caption_p.get_text()) if caption_p else ""
                    blocks.append(ArticleImage(url=url, alt=clean_text(img.get("alt", "")), caption=caption))
                    if caption_p:
                        processed_p.add(id(caption_p))
        elif tag.name == "picture":
            # Inline picture with source/srcset
            urls = []
            img_tag = tag.find("img")
            alt = ""
            if img_tag and not img_tag.find_parent("div", class_="article-picture"):
                alt = clean_text(img_tag.get("alt", ""))
                src = normalise_img_url(img_tag)
                if src:
                    urls.append(src)
                for source in tag.find_all("source"):
                    srcset = source.get("srcset", "")
                    for token in re.split(r",\s*", srcset):
                        u = token.strip().split()[0]
                        if u:
                            urls.append(u)
            if urls and not _is_inside_ad_container(tag):
                chosen = select_best_image_url(urls)
                if chosen:
                    blocks.append(ArticleImage(url=chosen, alt=alt))

    return blocks


def parse_article(url: str, html: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")
    article = Article(url=url)

    h1 = soup.find("h1")
    article.title = clean_text(h1.get_text()) if h1 else "Untitled"

    article.published, article.updated = extract_dates(soup)

    # Lead image outside the article body
    article.lead_image = extract_lead_image(soup)

    body = soup.find("div", id=re.compile(r"content-body-\d+"))
    if not body:
        return article

    remove_ad_elements(body)

    # Remove embedded media and scripts
    for t in body.find_all(["script", "noscript", "style", "iframe", "video", "audio", "embed"]):
        t.decompose()

    article.body_blocks = _collect_blocks(body)

    # Summary from first real paragraph
    for block in article.body_blocks:
        if isinstance(block, str):
            article.summary = re.sub(r"\s+", " ", block)[:220]
            end = article.summary.rfind(".", 0, 220)
            if end > 0:
                article.summary = article.summary[: end + 1]
            break

    return article


# --------------------------------------------------------------------------- #
# RST generation
# --------------------------------------------------------------------------- #


def slugify(title: str) -> str:
    s = unquote(title).lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s


def parse_published_date(date_str: str) -> str:
    """Convert a date string like 'December 06, 2025 10:33 pm IST' to '2025-12-06 22:33'."""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    # Extract components
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\s+(\d{1,2}):(\d{2})\s*(am|pm)\s*IST", date_str)
    if not m:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    month_name, day, year, hour, minute, meridiem = m.groups()
    hour = int(hour)
    minute = int(minute)
    if meridiem.lower() == "pm" and hour != 12:
        hour += 12
    elif meridiem.lower() == "am" and hour == 12:
        hour = 0
    try:
        dt = datetime(int(year), datetime.strptime(month_name, "%B").month, int(day), hour, minute)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d %H:%M")


def generate_rst(article: Article, output_dir: Path) -> Path:
    blocks_rst: list[str] = []

    # Prepare per-article image directory
    article_id_match = re.search(r"/article(\d+)\.ece?", article.url)
    article_id = article_id_match.group(1) if article_id_match else "hindu"
    image_dir = IMAGES_BASE / article_id
    image_dir.mkdir(parents=True, exist_ok=True)

    used_names: set[str] = set()

    def ensure_image(img: ArticleImage) -> str:
        if not img.local_name:
            img.local_name = download_image(img.url, image_dir, used_names)
        return img.local_name

    if article.lead_image:
        local = ensure_image(article.lead_image)
        if local:
            blocks_rst.append(f".. image:: images/{article_id}/{local}\n   :alt: {article.lead_image.alt}\n")

    for block in article.body_blocks:
        if isinstance(block, ArticleImage):
            local = ensure_image(block)
            if local:
                fig = f".. figure:: images/{article_id}/{local}\n   :alt: {block.alt}\n"
                if block.caption:
                    fig += f"\n   {block.caption}\n"
                blocks_rst.append(fig)
        else:
            blocks_rst.append(block)

    date_line = parse_published_date(article.published or article.updated)
    title_line = "=" * len(article.title)
    summary = article.summary or ""

    rst = f"""{title_line}
{article.title}
{title_line}

:date: {date_line}
:category: Articles
:tags: The Hindu Friday Review
:summary: {summary}

The Hindu: {article.url}

{"\n\n".join(blocks_rst)}
"""

    slug = slugify(article.title)
    filename = f"{date_line.split()[0].replace('-', '')}-{slug}.rst"
    out = output_dir / filename
    out.write_text(rst, encoding="utf-8")
    print(f"Article written to: {out}")
    return out


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import a The Hindu article into the Pelican project.")
    parser.add_argument("url", help="Full URL of The Hindu article")
    args = parser.parse_args(argv)

    if "thehindu.com" not in args.url:
        print("Error: URL does not look like a The Hindu article.", file=sys.stderr)
        return 1

    print(f"Fetching: {args.url}")
    html = fetch_html(args.url)
    article = parse_article(args.url, html)
    if not article.body_blocks:
        print("Error: Could not extract article content.", file=sys.stderr)
        return 1

    generate_rst(article, CONTENT_DIR)
    print("Done. Pelican should now auto-rebuild the site.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
