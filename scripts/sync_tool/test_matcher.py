from scripts.sync_tool.matcher import find_missing_articles

def test_find_missing_articles():
    scraped_urls = ["https://www.thehindu.com/a/article1.ece", "https://www.thehindu.com/b/article2.ece"]
    existing_articles = [
        {'canonical_url': 'https://www.thehindu.com/a/article1.ece', 'slug': 'article1', 'title': 'Article 1', 'date': '2024-01-01'}
    ]
    
    missing = find_missing_articles(scraped_urls, existing_articles)
    assert missing == ["https://www.thehindu.com/b/article2.ece"]
    print("Test passed!")

if __name__ == "__main__":
    test_find_missing_articles()
