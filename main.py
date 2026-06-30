import argparse
import sys
from scripts.sync_tool.scraper import get_all_article_urls
from scripts.sync_tool.parser import scan_content_directory
from scripts.sync_tool.matcher import find_missing_articles
from scripts.sync_tool.utils import setup_logging

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Sync The Hindu articles to Pelican content directory.")
    parser.add_argument("--author-url", required=True, help="URL of The Hindu author index page.")
    parser.add_argument("--content-dir", required=True, help="Path to Pelican content directory.")
    args = parser.parse_args()
    
    print("Fetching articles from The Hindu...")
    scraped_urls = get_all_article_urls(args.author_url)
    print(f"Total articles found on The Hindu: {len(scraped_urls)}")
    
    print("Scanning local content directory...")
    existing_articles = scan_content_directory(args.content_dir)
    print(f"Total articles already present: {len(existing_articles)}")
    
    print("Matching articles...")
    missing_urls = find_missing_articles(scraped_urls, existing_articles)
    
    print(f"Total missing articles: {len(missing_urls)}")
    
    if missing_urls:
        with open("missing_articles.txt", "w") as f:
            for url in missing_urls:
                f.write(f"{url}\n")
        print("Missing articles written to missing_articles.txt")
    else:
        print("No missing articles found.")

if __name__ == "__main__":
    main()
