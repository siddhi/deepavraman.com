---
name: hindu-article-import
description: Import an article from The Hindu website (https://www.thehindu.com) into the deepavraman.com Pelican site as a new ad-free .rst article with images. Use whenever the user pastes or provides a link to a Hindu article and asks to add it to the website.
---

# Hindu Article Import

This skill adds a The Hindu article to the `deepavraman.com` Pelican site as a clean, ad-free `.rst` article with its images.

## Quick usage

```bash
uv run .pi/skills/hindu-article-import/scripts/import_hindu_article.py "<THE-HINDU-URL>"
```

Example:

```bash
uv run .pi/skills/hindu-article-import/scripts/import_hindu_article.py "https://www.thehindu.com/entertainment/music/example-article/article123.ece"
```

## What it does

1. Fetches the article HTML with a browser User-Agent.
2. Extracts title, author byline, and published/updated date.
3. Removes ads, trackers, YouTube/vimeo/video embeds, Taboola widgets, social share buttons, and the comments section.
4. Downloads article images to `content/images/` under a per-article folder.
5. Writes a new reStructuredText article in `content/` with this metadata:
   - `:date:` — article publish date
   - `:category: Articles`
   - `:tags: The Hindu Friday Review`
   - `:summary:` — first paragraph
   - A link line `The Hindu: <url>`
6. Pelican auto-rebuilds when the dev server (`uv run pelican -r -l`) is running.

## Requirements

- Run from the project root (`C:\Users\aksha\OneDrive\Desktop\deepavraman.com`).
- `beautifulsoup4` is already available through the Pelican dependencies.
- The script uses only Python stdlib plus `bs4`.

## After importing

Verify the new article on the local site:

- Homepage: http://localhost:8000
- Article page: linked from the homepage
