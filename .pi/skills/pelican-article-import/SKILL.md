---
name: pelican-article-import
description: Import a saved web article (HTML) into this Pelican static site, including images, metadata, and build.
---

# Pelican Article Import

Use this skill when adding a saved/offline HTML article to this Deepa Venkatraman Pelican website.

## Assumptions

- This website uses Pelican with reStructuredText (`.rst`) content.
- Articles live in `content/`.
- The site uses a custom theme at `theme/spotlight/`.
- Python dependencies are installed via `uv` (`.venv`).
- The saved HTML file and its `_files` asset folder exist locally on disk.

## Step 1: Parse the saved HTML

Read the local HTML file. Do not re-download the article from the web.

Extract:

- Title (`<h1 class="title">` or `<title>`)
- Subtitle (`<h2 class="sub-title">`) if present
- Author (`meta[property="article:author"]`)
- Publication date (`meta[name="publish-date"]` → `YYYY-MM-DD`)
- Source URL (`link[rel="canonical"]`)
- Summary/description (`meta[name="description"]`)
- Complete article body (main content container, e.g. `.articlebodycontent .schemaDiv`)
- Images with captions and credits
  - Lead image is usually in `.article-picture.top-pic`
  - In-article images are in `.article-picture`
  - Captions are in `<p class="caption">`

Ignore:

- CSS and font differences
- Embedded videos
- Advertisements (`div.article-ad`)
- Social media widgets
- Related articles / share buttons
- UI icons and logos

## Step 2: Identify and prepare images

1. Extract every image used in the article body, including lead/top images and in-article images.
2. Skip UI icons, ads, logos, social widgets, and tracking pixels.
3. Save images to `content/images/`.
4. Copy in-article images from the saved `_files` folder.
5. Download remote/lead images using a browser-like `User-Agent` header if needed.
6. Give images clean, descriptive filenames (e.g. `hathaani.jpg`, `author-name.jpg`).

## Step 3: Create the `.rst` article

Save to `content/YYYYMMDD-short-descriptive-slug.rst`.

Required metadata block:

```rst
========================================
Article Title
========================================

:date: YYYY-MM-DD
:category: Articles
:tags: Publication Name
:summary: One or two sentence summary.
```

Body guidelines:

- Include the source URL near the top: `The Hindu: <url>`
- Include the subtitle as a lead paragraph if present.
- Preserve paragraph structure.
- Convert inline `<i>`/`<em>` to RST `*italic*`.
- Convert inline `<b>`/`<strong>` to RST `**bold**`.
- Insert images with captions using Pelican `{static}` intrasite link syntax so paths resolve correctly:

```rst
.. image:: {static}/images/filename.jpg
   :alt: Descriptive alt text

*Caption text | Photo Credit: Name*
```

## Step 4: Build the site

Run the Pelican build:

```bash
uv run pelican content
```

Then start the dev server to preview:

```bash
uv run pelican -r -l
```

Open `http://localhost:8000/` and verify the new article appears.

## Verification checklist

- [ ] New article appears on the homepage.
- [ ] Article page is generated in `output/`.
- [ ] Images are copied to `output/images/`.
- [ ] Image `src` attributes in the generated HTML use relative paths (e.g. `./images/filename.jpg`).
- [ ] Every image is visible on the rendered article page.
- [ ] Captions and credits appear correctly.
- [ ] No build warnings about missing images.

## Retry policy for missing images

If any image fails to render:

1. Delete the generated `.rst` file and any incorrectly copied images.
2. Determine the cause: incorrect path, unsupported format, missing copy, wrong Pelican syntax, or blocked remote download.
3. Fix the import logic.
4. Recreate the article.
5. Rebuild and verify again. Repeat until every image renders correctly.
