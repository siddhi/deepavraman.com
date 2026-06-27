#!/usr/bin/env python3
"""Clean a cloned The Hindu article HTML and prepare an ad-free local version."""
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup, Tag


def clean_text(t):
    if not t:
        return ""
    return re.sub(r"[\s\u00a0]+", " ", t).strip()


def fetch_image(url, dest_dir):
    """Download a remote image with a browser user-agent and return filename."""
    path = urlparse(url).path
    filename = Path(unquote(path)).name
    if not filename:
        filename = "image.jpg"
    filename = re.sub(r"[^\w\-.]", "_", filename)
    local_path = dest_dir / filename
    counter = 1
    stem = local_path.stem
    suffix = local_path.suffix or ".jpg"
    while local_path.exists():
        local_path = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://www.thehindu.com/",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            local_path.write_bytes(response.read())
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return None
    return local_path.name


def normalise_src(img):
    """Return the best available image URL from a lazy-loaded <img> tag."""
    for attr in ("data-original", "data-src", "data-lazy-src"):
        v = img.get(attr)
        if v and not v.endswith("1x1_spacer.png"):
            return v
    src = img.get("src")
    if src and not src.endswith("1x1_spacer.png"):
        return src
    return ""


def is_ad_url(url):
    if not url:
        return True
    patterns = [
        "doubleclick", "googlesyndication", "googleads", "googletagmanager",
        "google-analytics", "facebook.com/tr", "adsystem", "taboola",
        "outbrain", "adsrvr", "omtrdc", "scorecardresearch", "pubmatic",
        "casalemedia", "openx", "rubiconproject", "adsystem.amazon", "adform",
        "liveramp", "crwdcntrl", "3lift", "sharethrough", "adsymptotic",
        "bidswitch", "contextweb", "yieldmo", "districtm", "indexww", "semasio",
        "socdm", "tiqcdn", "teads", "adsafeprotected", "moatads", "iasds",
        "1x1_spacer", "/adsct", "/ad_status",
    ]
    low = url.lower()
    return any(p in low for p in patterns)


def decompose_selectors(soup, selectors):
    for selector in selectors:
        for tag in list(soup.select(selector)):
            tag.decompose()


def remove_ad_elements(soup):
    """Remove known ad/tracking/social/chrome-junk elements."""
    # CSS selectors first
    decompose_selectors(
        soup,
        [
            "script", "style", "noscript", "iframe", "video", "audio", "embed",
            "[id^='google_ads_']",
            "[id^='taboola-']",
            "[id^='taboola_']",
            "[id^='trc_']",
            "[id^='offer_']",
            "[id^='ps-main-container-']",
            "[id^='ps-video-player-']",
            "[id^='ps-ad-player-']",
            "[id^='ps-display-main-container-']",
            "[id*='Inarticle']",
            "[id*='_ads_']",
            "[id*='Desktop_AT']",
            "[id*='Mweb_AT']",
            ".article-ad",
            ".dfp-ad",
            ".inlinead",
            ".middleonead",
            ".inline_embed",
            ".comments-shares",
            ".comment-btn",
            ".read-later",
            ".update-publish-time",
            ".coral-count",
            ".trc_",
            ".videoCube",
            ".taboola-below",
            ".advertisement",
        ],
    )

    ad_id_patterns = [
        re.compile(r"google_ads|taboola|^trc_|offer_|ps-(video|ad)-|uspapi|tcfapi"),
        re.compile(r"Inarticle|midarticle|advertisement|adunit|ad-slot|adslot|article-ad|inlinead|inline_embed"),
        re.compile(r"articledivtrend|articleicymi|articletopnews|subscribe|share|comment|read-later"),
        re.compile(r"artmeterpv|coral-"),
    ]
    ad_class_keywords = [
        "trc_", "videoCube", "taboola", "advertisement", "ad-container",
        "adunit", "ads", "google-ad", "taboola-below", "trc_related",
        "article-ad", "dfp-ad", "inlinead", "middleonead", "inline_embed",
        "comments-shares", "comment-btn", "read-later", "share-page",
    ]

    for tag in list(soup.find_all(True)):
        if not isinstance(tag, Tag) or tag.attrs is None:
            continue
        remove = False
        if tag.get("id"):
            for pat in ad_id_patterns:
                if pat.search(str(tag["id"])):
                    remove = True
                    break
        if not remove and tag.get("class"):
            cls = " ".join(tag["class"])
            if any(kw in cls for kw in ad_class_keywords):
                remove = True
        if remove:
            tag.decompose()


def extract_lead_image(soup, images_dir, downloaded):
    """Find hero/lead images outside the main article body and localise them."""
    parts = []
    for picture in soup.find_all("picture"):
        sources = []
        img_tag = picture.find("img")
        alt = img_tag.get("alt", "") if img_tag else ""
        for source in picture.find_all("source"):
            srcset = source.get("srcset", "")
            for token in re.split(r",\s*", srcset):
                url = token.strip().split()[0]
                if url and url not in sources:
                    sources.append(url)
        if img_tag:
            src = normalise_src(img_tag)
            if src and src not in sources:
                sources.append(src)
        if not sources:
            continue

        def score(u):
            m = re.search(r"(\d+)", Path(u).stem)
            m2 = re.search(r"_(\d+)\.", u)
            v = int(m2.group(1)) if m2 else (int(m.group(1)) if m else 0)
            return v

        chosen = max(sources, key=score)
        if is_ad_url(chosen):
            continue
        local_name = downloaded.get(chosen) or fetch_image(chosen, images_dir)
        if local_name:
            downloaded[chosen] = local_name
            parts.append(
                f'<figure class="picture"><img src="./images/{local_name}" alt="{alt}"></figure>'
            )
    return "".join(parts)


def clean_article_picture(tag, images_dir, downloaded):
    """Convert an <div class="article-picture"> to <figure> and localise its image."""
    img_tag = tag.find("img")
    caption = ""
    cap_tag = tag.find("p", class_="caption")
    if cap_tag:
        caption = clean_text(cap_tag.get_text())
    if not img_tag:
        if caption:
            tag.replace_with(BeautifulSoup(f"<p><em>{caption}</em></p>", "html.parser").p)
        else:
            tag.decompose()
        return

    url = normalise_src(img_tag)
    if not url or is_ad_url(url):
        meta = tag.find("meta", itemprop="url")
        if meta:
            url = meta.get("content", "")
    if not url or is_ad_url(url):
        if caption:
            tag.replace_with(BeautifulSoup(f"<p><em>{caption}</em></p>", "html.parser").p)
        else:
            tag.decompose()
        return

    local_name = downloaded.get(url) or fetch_image(url, images_dir)
    if not local_name:
        if caption:
            tag.replace_with(BeautifulSoup(f"<p><em>{caption}</em></p>", "html.parser").p)
        else:
            tag.decompose()
        return

    downloaded[url] = local_name
    fig_html = f'<figure><img src="./images/{local_name}" alt="">'
    if caption:
        fig_html += f"<figcaption>{caption}</figcaption>"
    fig_html += "</figure>"
    tag.replace_with(BeautifulSoup(fig_html, "html.parser"))


def localise_inline_images(soup, images_dir, downloaded):
    """Download real article images referenced inside the body, drop junk."""
    # Skip images already linked to the new local images folder; they were already processed.
    def already_local(img):
        src = img.get("src", "")
        return src.startswith("./images/") or src.startswith("images/")

    for img in list(soup.find_all("img")):
        if already_local(img):
            continue
        url = normalise_src(img)
        if not url:
            img.decompose()
            continue
        if is_ad_url(url):
            img.decompose()
            continue

        local_name = downloaded.get(url) or fetch_image(url, images_dir)
        if local_name:
            downloaded[url] = local_name
            img["src"] = f"./images/{local_name}"
        else:
            img.decompose()
            continue
        # Clean attributes
        img.attrs = {
            "src": img["src"],
            "alt": img.get("alt", ""),
        }

    # Drop source tags
    for source in list(soup.find_all("source")):
        source.decompose()


def extract_date_from_body(body):
    updated = None
    published = None
    # Date extraction from explicit tags
    for el in body.find_all(["p", "span", "div", "time"]):
        txt = clean_text(el.get_text())
        if len(txt) > 200:
            continue
        if not updated:
            m = re.search(r"Updated-\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}[^\n]*?IST)", txt)
            if m:
                updated = m.group(1).strip()
        if not published:
            m = re.search(r"Published-\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}[^\n]*?IST)", txt)
            if m:
                published = m.group(1).strip()
    return updated, published


def main():
    desktop = Path.home() / "OneDrive" / "Desktop"
    original_html = desktop / "The Hindu.html"
    clean_dir = desktop / "The_Hindu_Clean"

    if not original_html.exists():
        print(f"Original file not found: {original_html}")
        return

    print(f"Reading {original_html}")
    with open(original_html, encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    h1_tag = soup.find("h1")
    title = clean_text(h1_tag.get_text()) if h1_tag else "Untitled"

    # Date fallback on whole document
    updated, published = extract_date_from_body(soup)

    article_body = soup.find("div", id=re.compile(r"content-body-\d+"))
    if not article_body:
        print("Could not find article body. Aborted.")
        return

    # Refresh dates from body specifically
    u2, p2 = extract_date_from_body(article_body)
    updated = u2 or updated
    published = p2 or published

    # Deep copy for mutation
    body = BeautifulSoup(str(article_body), "html.parser").find("div")

    # Clean
    remove_ad_elements(body)

    # Remove event attributes and any remaining small ad/spam containers
    for tag in list(body.find_all(True)):
        if not isinstance(tag, Tag):
            continue
        # Remove any onclick/onerror etc. handlers
        for attr in list(tag.attrs.keys()):
            if attr.startswith("on"):
                del tag[attr]
        if tag.name == "button" or tag.name == "a" and not tag.get("href"):
            # buttons without image children are UI chrome
            if not tag.find("img"):
                tag.decompose()
                continue

    # Prepare clean directory before downloading any images
    if clean_dir.exists():
        shutil.rmtree(clean_dir)
    clean_dir.mkdir(parents=True, exist_ok=True)

    images_dir = clean_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    downloaded = {}

    # Lead/hero image outside the body
    lead_image_html = extract_lead_image(soup, images_dir, downloaded)

    # Localise inline images inside body
    localise_inline_images(body, images_dir, downloaded)

    # Remove empty containers
    changed = True
    while changed:
        changed = False
        for tag in list(body.find_all(["div", "p", "span", "section", "aside", "figure", "button", "ul", "ol"])):
            txt = clean_text(tag.get_text())
            if len(txt) == 0 and not tag.find_all("img"):
                tag.decompose()
                changed = True

    # Remove schemaDiv wrapper id but keep its children
    schema = body.find("div", id="schemaDiv")
    if schema:
        schema.unwrap()

    # Re-remove scripts that might have appeared from unwrapping
    for tag in body.find_all(["script", "style", "noscript", "iframe", "video", "audio", "embed"]):
        tag.decompose()

    article_html = str(body)
    # Strip the remaining outer content-body/articlebodycontent wrappers
    article_html = re.sub(
        r"<div[^>]*class=[\"']articlebodycontent[^\"']*[\"'][^>]*>\s*",
        "",
        article_html,
        count=1,
        flags=re.I,
    )
    article_html = re.sub(r"<div[^>]*id=[\"']content-body-\d+[\"'][^>]*>\s*", "", article_html, count=1, flags=re.I)
    article_html = re.sub(r"</div>\s*$", "", article_html, flags=re.S, count=1)
    article_html = re.sub(r"<div>\s*</div>", "", article_html)

    clean_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light dark; }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: Georgia, "Times New Roman", Times, serif;
      line-height: 1.7;
      max-width: 760px;
      margin: 0 auto;
      padding: 2rem 1.25rem;
      color: #222;
      background: #fff;
    }}
    @media (prefers-color-scheme: dark) {{
      body {{ color: #ddd; background: #111; }}
      a {{ color: #6cf; }}
      figcaption {{ color: #aaa; }}
      .byline {{ color: #aaa; }}
    }}
    h1 {{
      font-size: 1.9rem;
      line-height: 1.25;
      margin-bottom: 0.5rem;
    }}
    .byline {{
      color: #666;
      font-size: 0.9rem;
      margin-bottom: 1.5rem;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .article-body p {{
      margin: 1rem 0;
      font-size: 1.05rem;
    }}
    .article-body img, figure img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 1.5rem auto;
      border-radius: 4px;
    }}
    figure {{ margin: 1.5rem 0; }}
    figcaption {{
      font-size: 0.85rem;
      color: #555;
      margin-top: 0.4rem;
      font-family: system-ui, sans-serif;
      text-align: center;
    }}
    a {{ color: #0066cc; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    strong {{ font-weight: 700; }}
    ::selection {{ background: #b3d4fc; }}
  </style>
</head>
<body>
  <article>
    <h1>{title}</h1>
    <div class="byline">
      {f'<div>Updated: {updated}</div>' if updated else ''}
      {f'<div>Published: {published}</div>' if published else ''}
    </div>
    {lead_image_html}
    <div class="article-body">
      {article_html}
    </div>
  </article>
</body>
</html>"""

    (clean_dir / "index.html").write_text(clean_html, encoding="utf-8")

    print(f"\nClean folder created: {clean_dir}")
    print(f"Images downloaded: {len(downloaded)}")
    for url, name in downloaded.items():
        print(f"  -> {name}")
    print(f"\nTo view locally run:")
    print(f"  cd \"{clean_dir}\" && python -m http.server 8000")


if __name__ == "__main__":
    main()
