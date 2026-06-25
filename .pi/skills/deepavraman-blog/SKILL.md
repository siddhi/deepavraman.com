---
name: deepavraman-blog
description: |
  Manage the deepavraman.com Pelican static blog: setup, serve, build, publish,
  add content, manage Python/Node dependencies, and update the custom theme.
  Use whenever working on <https://www.deepavraman.com> source files.
compatibility: |
  Requires uv and npm. Windows primary. Python deps managed in pyproject.toml;
  Node deps managed in package.json. Tailwind CSS rebuild relies on npm scripts.
---

# deepavraman.com Pelican Blog

This skill describes how to work with Deepa Venkatraman’s personal blog, a
[Pelican](https://getpelican.com/) 4.9.x static site using a custom theme,
Tailwind CSS, and the `pelican-seo` plugin.

## Project Layout

```text
.
├── content/                # reStructuredText (.rst) articles
├── theme/spotlight/        # Custom Pelican theme
│   ├── static/             # CSS, images
│   └── templates/          # Jinja2 HTML templates
├── pelicanconf.py          # Local config (RELATIVE_URLS = True)
├── publishconf.py          # Production config + feeds
├── pyproject.toml          # Python deps
├── requirements.txt        # Pinned deps (uv pip compile output)
├── package.json            # Node deps (Tailwind Typography)
├── tailwind.config.js      # Tailwind theme config
├── tailwind.css            # Tailwind @directives entry
├── tasks.py                # Invoke tasks
└── Makefile                # Make targets wrapping Pelican
```

## Setup

Run once per fresh clone:

```bash
uv sync
npm install
```

## Common Workflows

### Serve locally with auto-reload

```bash
uv run pelican -r -l
```

Equivalent Make target:

```bash
make devserver
```

### Build the site locally

```bash
uv run pelican
```

Output is written to `output/`.

### Build the production site

```bash
uv run pelican -s publishconf.py
```

### Publish / deploy

Use `publishconf.py` for production builds. Deployment itself is handled outside
this repo; verify the generated `output/` matches the expected production output.

## Dependency Management

### Add a Python dependency

Edit `[project].dependencies` in `pyproject.toml`, then run:

```bash
uv add <package>
```

For dev-only packages use `uv add --dev <package>`.

### Regenerate pinned requirements

If you need to refresh `requirements.txt` from `pyproject.toml`:

```bash
uv pip compile pyproject.toml -o requirements.txt
```

### Add a Node dependency

```bash
npm install <package> --save-dev
```

Tailwind plugins become available by extending `tailwind.config.js`.

## Adding Content

1. Create a new `.rst` file in `content/`.
2. Include Pelican metadata at the top:

```rst
My Article Title
################

:date: 2026-06-25 10:00
:category: Musings
:tags: tag-one, tag-two
:summary: Short summary for listings and SEO.

Article body starts here.
```

3. Run `uv run pelican -r -l` to preview, or `uv run pelican` to build.

## Theme / Styling

- Styles live in `theme/spotlight/static/css/main.css`.
- Tailwind entry is `tailwind.css`.
- Tailwind config is `tailwind.config.js`.
- Typography plugin comes from `@tailwindcss/typography` (Node dev dependency).

When changing styles, rebuild Tailwind output as defined by the project’s npm
scripts or build pipeline:

```bash
npx tailwindcss -i ./tailwind.css -o ./theme/spotlight/static/css/main.css --minify
```

Confirm the exact build command by reading `package.json` scripts, since it may
vary.

## SEO

The site uses `pelican-seo` (enabled in config). After building locally you can
inspect `seo_report.html` for SEO recommendations.

## Conventions

- Content is written in **reStructuredText**, not Markdown.
- Prefer `uv` for Python tasks; do not use `pip` directly.
- Prefer `npm` for Node/Tailwind tasks.
- Keep `output/` and `node_modules/` untracked.
- Production feeds are generated only via `publishconf.py`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `uv: command not found` | Install [uv](https://docs.astral.sh/uv/) |
| Missing Node modules | Run `npm install` |
| Tailwind changes not reflected | Rebuild CSS and clear `output/` |
| Wrong URLs locally | Confirm `RELATIVE_URLS = True` in `pelicanconf.py` |
