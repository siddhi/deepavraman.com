#!/usr/bin/env python3
"""Convert the cleaned The Hindu article into a Pelican .rst article."""
import shutil
from pathlib import Path
from bs4 import BeautifulSoup


def clean_text(t):
    if not t:
        return ""
    import re
    return re.sub(r"[\s\u00a0]+", " ", t).strip()


def main():
    src_html = Path("C:/Users/aksha/OneDrive/Desktop/The_Hindu_Clean/index.html")
    dst_dir = Path("C:/Users/aksha/OneDrive/Desktop/deepavraman.com/content")
    img_dir = dst_dir / "images"
    img_dir.mkdir(exist_ok=True)

    html = src_html.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    title = soup.h1.get_text(strip=True) if soup.h1 else "Untitled"

    # Copy images with descriptive names
    old_new = {
        "IMG_3315.jpg": "raghavasimhan.jpg",
        "hathaani_v2.jpg": "hathaani.jpg",
    }
    for old, new in old_new.items():
        shutil.copy(
            Path("C:/Users/aksha/OneDrive/Desktop/The_Hindu_Clean/images") / old,
            img_dir / new,
        )

    # Lead figure metadata
    lead_fig = soup.find("figure", class_="picture")
    lead_alt = lead_fig.img.get("alt", "") if lead_fig and lead_fig.img else ""

    body = soup.find("div", class_="article-body")
    if not body:
        raise SystemExit("Article body not found in cleaned HTML")

    # Remove related topics
    for el in list(body.find_all("div", class_="related-topics")):
        el.decompose()

    blocks = []

    # Lead image
    blocks.append(f".. image:: images/{old_new['IMG_3315.jpg']}\n   :alt: {lead_alt}\n")

    for elem in body.children:
        if elem.name == "p":
            if "caption" in (elem.get("class") or []):
                continue
            text = clean_text(elem.get_text())
            if text:
                blocks.append(text)
        elif elem.name == "div" and "article-picture" in (elem.get("class") or []):
            img = elem.find("img")
            caption_p = elem.find("p", class_="caption")
            if img:
                alt = clean_text(img.get("alt", ""))
                src = Path(img.get("src", "")).name
                newname = old_new.get(src, src)
                caption = clean_text(caption_p.get_text()) if caption_p else ""
                fig = (
                    f".. figure:: images/{newname}\n"
                    f"   :alt: {alt}\n\n"
                    f"   {caption}\n"
                )
                blocks.append(fig)

    # Compose body with blank lines between blocks (required by RST paragraphs)
    body_rst = "\n\n".join(blocks)

    # Summary from first paragraph, trimmed to a complete sentence
    first_paras = [b for b in blocks if not b.startswith("..") and len(b) > 20]
    raw_summary = first_paras[0] if first_paras else ""
    end = raw_summary.rfind(".", 0, 220)
    summary = raw_summary[: end + 1] if end > 0 else raw_summary[:220]
    summary = summary.replace("\n", " ")

    url = "https://www.thehindu.com/entertainment/meet-raghavasimhan-sankaranarayanans-robotic-violinist-hathaani/article70316642.ece"

    meta_title_line = "=" * len(title)
    rst_content = f"""{meta_title_line}
{title}
{meta_title_line}

:date: 2025-12-06 22:33
:category: Articles
:tags: The Hindu Friday Review
:summary: {summary}

The Hindu: {url}

{body_rst}
"""

    filename = "20251206-meet-raghavasimhan-sankaranarayanans-robotic-violinist.rst"
    out_path = dst_dir / filename
    out_path.write_text(rst_content, encoding="utf-8")
    print(f"Article saved to: {out_path}")
    print(f"Images copied to: {img_dir}")


if __name__ == "__main__":
    main()
