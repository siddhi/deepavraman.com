---
name: import-html-article
description: Imports a locally saved The Hindu article HTML into the Pelican website. Extracts title, publication date, summary, body paragraphs, downloads article images, creates a properly formatted reStructuredText post, and rebuilds the site.
---

# Import HTML Article Skill

Use this skill when you have a saved The Hindu `news.html` file (or similar article page) and want to add it as an article to the `deepavraman.com` Pelican site.

## What it does

1. Validates the saved HTML file exists.
2. Extracts article metadata:
   - Title
   - Publication date
   - Summary / description
   - Original URL
3. Extracts the article body paragraphs from `<div itemprop="articleBody">`.
4. Discovers and downloads article images to the repository.
5. Creates a new `.rst` article in `content/` using repository conventions.
6. Builds the site and reports the generated URL.

## Conventions followed

Files created follow the existing repository patterns:

- Article location: `content/`
- Filename format: `YYYYMMDD-<slug>.rst`
- Frontmatter fields:
  - `:date:`        → `YYYY-MM-DD`
  - `:category:`    → `Articles`
  - `:tags:`        → `The Hindu Friday Review`
  - `:summary:`     → From HTML `<meta name="description">`
- Images: Stored under `content/images/`
- Author: Uses the global `AUTHOR` setting (`Deepa Venkatraman`).

## Usage

### 1. Verify the saved HTML locally

Open the saved HTML file in a browser and confirm:

- The article title is present.
- The full article text is present.
- All article images load.
- Ignore styling, ads, videos, and tracking scripts.

If images are missing, re-download the page with a browser or save it again.

### 2. Run the import script

From the **repository root**:

```bash
uv run python .pi/skills/import-html-article/scripts/import.py path/to/news.html
```

Example:

```bash
uv run python .pi/skills/import-html-article/scripts/import.py news.html
```

### 3. Build the site

```bash
uv run pelican content -o output -s pelicanconf.py
```

### 4. Run the local server

```bash
uv run pelican -r -l
```

Then open the reported article URL, e.g.:

```text
http://localhost:8000/YYYY/MM/DD/<slug>.html
```

Also verify the category listing:

```text
http://localhost:8000/category/articles.html
```

## Import script options

```text
usage: import.py [-h] [--content-dir CONTENT_DIR] [--images-dir IMAGES_DIR] input

positional arguments:
  input                 Path to saved news.html

options:
  -h, --help            show this help message and exit
  --content-dir CONTENT_DIR
                        content directory (default: content)
  --images-dir IMAGES_DIR
                        images directory (default: content/images)
```

## Important notes

- The script relies on standard-library Python modules only and uses a `User-Agent` header to download images.
- It ignores `<iframe>`, `<script>`, ad blocks, and non-article images such as spacer pixels.
- If the title or publication date cannot be extracted, the script exits with an error.
- Always inspect the generated `.rst` file and images before committing.
