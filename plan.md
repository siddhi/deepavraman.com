# Implementation Plan: The Hindu Article Sync Script

## 1. Overview
The goal is to create a Python utility that scrapes The Hindu author index pages to identify articles that have not yet been ported to a local Pelican-based website. It will automate the detection of missing content to aid in site maintenance.

## 2. Overall Architecture
The script will follow a modular, pipeline-based architecture:

1.  **Fetcher/Crawler:** Downloads HTML and navigates pagination.
2.  **Extractor:** Parses HTML to get canonical article URLs.
3.  **Content Parser:** Scans the `content/` directory to build a registry of existing articles.
4.  **Matcher/Engine:** Compares the list of scraped URLs against the registry based on specific rules.
5.  **Reporter:** Generates statistics and the `missing_articles.txt` file.

## 3. Module/Function Breakdown

*   **`main.py`**: Entry point. Parses arguments (`--author-url`, `--content-dir`), orchestrates the pipeline.
*   **`scraper.py`**:
    *   `get_all_article_urls(author_url)`: Manages pagination and calls `extract_links_from_page`.
    *   `extract_links_from_page(html)`: Uses BeautifulSoup to find article `<a>` tags.
*   **`parser.py`**:
    *   `scan_content_directory(content_path)`: Walks the directory recursively.
    *   `extract_metadata(file_path)`: Reads `.rst` file headers to extract metadata (canonical URL, title, date).
*   **`matcher.py`**:
    *   `find_missing_articles(scraped_urls, existing_articles)`: Implements the hierarchical matching strategy.
*   **`utils.py`**: Logger configuration, file writing routines, and regex patterns.

## 4. Data Flow
1.  **Input:** Author URL, Content Directory Path.
2.  **Scraping Phase:** `scraper.py` $\to$ List of URLs from The Hindu.
3.  **Parsing Phase:** `parser.py` $\to$ List/Dict of objects representing local articles (with URL, slug, title, date).
4.  **Matching Phase:** `matcher.py` performs comparisons $\to$ Set of unique URLs.
5.  **Output Phase:** Write `missing_articles.txt`, print summary stats to console.

## 5. Strategies

### URL Extraction & Pagination
*   **Strategy:** Use `requests` to fetch the index page and `BeautifulSoup` to parse HTML.
*   **Pagination:** Look for the "Next" link (e.g., `rel="next"` or specific CSS class). Recursively follow until no more links found.

### Pelican Content Parsing
*   **Strategy:** Perform a recursive scan of `content/` looking for `.rst` files.
*   **Metadata:** Use regex to extract metadata fields from the file headers (e.g., `Title: ...`, `Date: ...`, `Canonical-URL: ...`). Avoid full dependency on the heavy Pelican framework to ensure speed and decoupling.

### URL Matching Strategy (Hierarchical)
For every scraped article URL from The Hindu:
1.  **Strict Match:** Does the `Canonical-URL` metadata match the scraped URL?
2.  **Slug Match:** Extract the slug from the scraped URL (last part of path) and compare against the filename of the `.rst` file (ignoring extension).
3.  **Heuristic Match:** If both fail, compare Title + Publication Date metadata against known article data (if extractable).

## 6. Error Handling & Logging
*   **Logging:** Use Python's built-in `logging` module. Log at `INFO` level for progress, `WARNING` for parsing issues, and `ERROR` for network failures.
*   **Network Errors:** Implement retries using `urllib3` (via `requests`) or a `tenacity` decorator to handle transient HTTP errors.
*   **Parsing Errors:** Gracefully skip malformed `.rst` files and log them as warnings.

## 7. Edge Cases
*   The Hindu changes page structure (requires flexible selectors).
*   Article URLs might contain URL parameters that need cleaning.
*   Pelican files might have inconsistent metadata formats.
*   Multiple articles might have the same slug in different categories (rare, but needs handling).

## 8. Testing Strategy
*   **Unit Tests:** Test the matcher logic with dummy data to ensure hierarchical matching works correctly.
*   **Integration Tests:**
    *   Provide a local HTML snippet to test the scraper/pagination.
    *   Provide a dummy `content/` folder to test the parser.
*   **Validation:** Verify `missing_articles.txt` format.

## 9. External Dependencies
*   `requests`: HTTP requests.
*   `beautifulsoup4`: HTML parsing.
*   `python-frontmatter` (optional): To simplify metadata parsing if regex becomes too complex.

## 10. Order of Implementation
1.  **Phase 1: Setup & Scraper:** Implement crawler and pagination logic. Verify we can get all URLs.
2.  **Phase 2: Parser:** Implement recursive `content/` scanning and metadata extraction.
3.  **Phase 3: Matcher:** Implement the matching logic based on the three strategies.
4.  **Phase 4: Reporting & Main:** Assemble components, create `missing_articles.txt`, and print statistics.
5.  **Phase 5: Refinement:** Add error handling, logging, and comprehensive comments.
