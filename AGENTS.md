# AGENTS.md

## High-Level Overview

This repository is the source for <https://www.deepavraman.com>, a personal blog / portfolio site built with the [Pelican](https://getpelican.com/) static site generator.

Key facts:

- **Author:** Deepa Venkatraman
- **Generator:** Pelican 4.9.x
- **Primary config:** `pelicanconf.py`
- **Production config:** `publishconf.py`
- **Content format:** reStructuredText (`.rst`) files in `content/`
- **Theme:** Custom theme located at `theme/spotlight/`
- **Styling:** Tailwind CSS with the Typography plugin
- **SEO:** Enhanced with `pelican-seo`
- **Python packaging:** `pyproject.toml` defines the project and its dependencies
- **Deployment:** `publishconf.py` enables production feeds

The site is configured with relative URLs locally (`RELATIVE_URLS = True`) and absolute URLs plus Atom feeds in production.

## How to Manage the Project

### Initial setup

This project is managed with `uv` and not with `pip`

```bash
# Install Python dependencies
uv sync

# Install Node dependencies (used for Tailwind CSS)
npm install
```

### How to run the server

`uv run pelican -r -l`

### How to add and remove dependencies

Python dependencies are declared in `pyproject.toml` under `[project].dependencies`.

```toml
[project]
dependencies = [
    "pelican ~= 4.9.1",
    "pelican-seo ~= 1.2.2",
]
```

Python dependencies are added with `uv`:

```bash
uv add <package>
```

JavaScript dependencies are declared in `package.json` and installed with:

```bash
npm install <package> --save-dev
npm install
```

## Directory Structure

```
.
├── content/                  # Source articles in reStructuredText (.rst)
├── theme/spotlight/          # Custom Pelican theme
│   ├── static/               # Static assets (CSS, images, etc.)
│   └── templates/            # Jinja2 HTML templates
├── scripts/                  # Miscellaneous project scripts (currently empty)
├── output/                   # Generated site (gitignored)
├── node_modules/             # JavaScript dependencies (gitignored)
├── pelicanconf.py            # Local Pelican configuration
├── publishconf.py            # Production Pelican configuration
├── pyproject.toml            # Python project and dependency metadata
├── requirements.txt          # Pinned Python dependencies (from pip-compile)
├── package.json              # Node dependencies (Tailwind Typography)
├── package-lock.json         # Locked Node dependency tree
├── tailwind.config.js        # Tailwind configuration
├── tailwind.css              # Tailwind entry file with @directives
├── tasks.py                  # Invoke tasks for build/serve/publish
├── Makefile                  # Make targets wrapping Pelican commands
├── .gitignore                # VCS ignore rules
└── AGENTS.md                 # This file
```

### What’s in each directory

- **`content/`** — All blog posts written in reStructuredText. Each file typically contains Pelican metadata (title, date, category, tags, etc.) followed by the article body.
- **`theme/spotlight/static/`** — Static assets served as-is by Pelican:
  - `css/main.css` — Main stylesheet
  - `images/` — Banner and profile images
- **`theme/spotlight/templates/`** — Jinja2 templates used by Pelican to render pages such as the home page, articles, archives, categories, tags, authors, and the base layout.
- **`scripts/`** — Reserved for utility scripts. Currently empty.
- **`output/`** — Generated HTML site produced by Pelican. This directory is regenerated on build and is ignored by Git.
- **`node_modules/`** — Installed Node packages used for Tailwind CSS. Ignored by Git.
