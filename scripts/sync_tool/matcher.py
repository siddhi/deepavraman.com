def get_slug_from_url(url):
    """
    Extracts the slug from The Hindu article URL.
    Example: https://www.thehindu.com/entertainment/music/meet-carnatic-musics-gen-z/article67701378.ece
    Slug: article67701378.ece? Or maybe just the part after the last slash?
    """
    # The Hindu URLs typically end with /article<id>.ece
    return url.strip('/').split('/')[-1]

import logging

def find_missing_articles(scraped_urls, existing_articles):
    """
    Compares the scraped URLs against the existing articles
    and identifies missing ones.
    """
    existing_canonical_urls = {a['canonical_url'] for a in existing_articles if a['canonical_url']}
    logging.debug(f"Existing canonical URLs: {existing_canonical_urls}")
    existing_slugs = {a['slug'] for a in existing_articles if a['slug']}
    
    missing_urls = []
    
    for url in scraped_urls:
        logging.debug(f"Checking URL: {url}")
        if url in existing_canonical_urls:
            logging.debug(f"Matched by URL: {url}")
            continue
            
        # Try slug match
        slug = get_slug_from_url(url)
        if slug in existing_slugs:
            logging.debug(f"Matched by slug: {slug}")
            continue
            
        # If we reach here, it's missing
        missing_urls.append(url)
        
    return missing_urls
