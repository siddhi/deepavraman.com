#!/usr/bin/env python3
"""
Import a saved The Hindu article HTML into the Pelican site.

Usage:
    uv run python .pi/skills/import-html-article/scripts/import.py path/to/news.html
"""

import argparse
import datetime
import html
import os
import re
import sys
import urllib.request


def extract_meta(text):
    """Extract title, date, summary, and canonical URL from meta tags."""
    title = None
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', text)
    if m:
        title = html.unescape(m.group(1).strip())
    if not title:
        m = re.search(r'<title>(.*?)</title>', text, re.DOTALL)
        if m:
            title = html.unescape(m.group(1).replace('- The Hindu', '').strip())

    published = None
    m = re.search(r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"', text)
    if m:
        published = m.group(1)
    if not published:
        m = re.search(r'<meta[^>]+name="publish-date"[^>]+content="([^"]+)"', text)
        if m:
            published = m.group(1)

    summary = ''
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', text)
    if m:
        summary = html.unescape(m.group(1).strip())

    url = ''
    m = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', text)
    if m:
        url = html.unescape(m.group(1).strip())

    return title, published, summary, url


def _extract_body_html(text):
    """Return the raw HTML fragment inside <div itemprop="articleBody">."""
    marker = '<div class="schemaDiv" id="schemaDiv" itemprop="articleBody">'
    start = text.find(marker)
    if start == -1:
        return ''

    start += len(marker)
    depth = 1
    i = start
    end = start
    while i < len(text) and depth > 0:
        next_open = text.find('<div', i)
        next_close = text.find('</div>', i)
        if next_open == -1:
            next_open = len(text) + 1
        if next_close == -1:
            next_close = len(text) + 1

        if next_open < next_close:
            depth += 1
            i = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                end = next_close
                break
            i = next_close + 6

    return text[start:end]


def extract_body(text):
    """Extract plain-text paragraphs from <div itemprop="articleBody">."""
    body_html = _extract_body_html(text)
    if not body_html:
        return []
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', body_html, re.DOTALL)
    clean = []
    for p in paragraphs:
        p = re.sub(r'<[^>]+>', '', p)
        p = html.unescape(p)
        p = ' '.join(p.split())
        if p:
            clean.append(p)
    return clean


def extract_images(text):
    """Find article image URLs inside the article body area."""
    body_html = _extract_body_html(text)
    if not body_html:
        return []

    urls = set()
    for src in re.findall(r'data-src-template="([^"]+)"', body_html):
        if '1x1_spacer' not in src and src.startswith('http'):
            urls.add(src)
    for src in re.findall(r'data-original="([^"]+)"', body_html):
        if '1x1_spacer' not in src and 'google-preferred' not in src and src.startswith('http'):
            urls.add(src)
    return sorted(urls)


def slugify(title):
    """Create a URL-safe slug from the article title."""
    s = title.lower()
    s = re.sub(r"['’]", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    s = re.sub(r'-+', '-', s)
    return s


def download_image(url, dest):
    """Download an image with a browser-like User-Agent."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0'
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'wb') as f:
        f.write(data)
    return len(data)


def determine_date(published):
    """Parse the publication date string into a datetime object."""
    if not published:
        return datetime.datetime.now()
    s = published.strip()
    if ':' in s:
        return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
    return datetime.datetime.strptime(s, '%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser(description='Import a saved The Hindu article HTML into Pelican.')
    parser.add_argument('input', help='Path to saved news.html')
    parser.add_argument('--content-dir', default='content', help='content directory (default: content)')
    parser.add_argument('--images-dir', default='content/images', help='images directory (default: content/images)')
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f'Error: file not found: {args.input}', file=sys.stderr)
        sys.exit(1)

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    title, published, summary, url = extract_meta(text)
    if not title:
        print('Error: could not extract article title.', file=sys.stderr)
        sys.exit(1)
    if not published:
        print('Error: could not extract publication date.', file=sys.stderr)
        sys.exit(1)

    date_obj = determine_date(published)
    date_str = date_obj.strftime('%Y-%m-%d')
    slug = slugify(title)
    filename = f"{date_obj.strftime('%Y%m%d')}-{slug}.rst"
    filepath = os.path.join(args.content_dir, filename)

    if os.path.exists(filepath):
        print(f'Warning: article already exists at {filepath}', file=sys.stderr)

    body_html = _extract_body_html(text)
    body_paragraphs = extract_body(text)
    image_urls = extract_images(text)

    os.makedirs(args.content_dir, exist_ok=True)
    os.makedirs(args.images_dir, exist_ok=True)

    # Download images and build relative references
    image_refs = []
    for idx, img_url in enumerate(image_urls):
        base = os.path.basename(img_url.split('?')[0])
        ext = os.path.splitext(base)[1].lower()
        if not ext or ext not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            ext = '.jpg'
        img_name = f'{slug}-{idx + 1}{ext}'
        dest = os.path.join(args.images_dir, img_name)
        try:
            size = download_image(img_url, dest)
            rel = os.path.relpath(dest, args.content_dir).replace('\\', '/')
            image_refs.append(rel)
            print(f'Downloaded image: {dest} ({size} bytes)')
        except Exception as exc:
            print(f'Warning: failed to download {img_url}: {exc}', file=sys.stderr)

    # Build the article
    lines = [
        title,
        '=' * len(title),
        '',
        f':date: {date_str}',
        ':category: Articles',
        ':tags: The Hindu Friday Review',
        f':summary: {summary}',
        '',
        f'The Hindu: {url}',
        '',
    ]

    for rel in image_refs:
        lines.extend([
            f'.. image:: {rel}',
            '',
        ])

    for p in body_paragraphs:
        lines.extend([p, ''])

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'\nCreated article: {filepath}')
    if image_refs:
        print(f'Images stored under: {args.images_dir}')
    print(f'Preview URL: http://localhost:8000/{slug}.html')
    print('\nNext steps:')
    print('  uv run pelican content -o output -s pelicanconf.py')
    print('  uv run pelican -r -l')


if __name__ == '__main__':
    main()
