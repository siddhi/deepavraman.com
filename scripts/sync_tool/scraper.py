import requests
from bs4 import BeautifulSoup
import logging
import time

def extract_links_from_page(html):
    """
    Parses HTML to extract article URLs based on common The Hindu patterns.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Better strategy: Find all links that look like article links
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        # The Hindu article URLs contain '/article' and end with '.ece'
        if '/article' in href and href.endswith('.ece'):
            # Convert relative to absolute if necessary
            if href.startswith('/'):
                href = f"https://www.thehindu.com{href}"
            links.append(href)
    
    # Remove duplicates
    links = list(set(links))
            
    # Try finding the "Next" link via common patterns
    next_link = soup.select_one('a.next-page') or soup.select_one('a[rel="next"]')
    next_url = next_link.get('href') if next_link else None
    
    return links, next_url

def get_all_article_urls(author_url):
    """
    Manages pagination and crawls the author index page.
    """
    all_urls = set()
    current_url = author_url
    
    while current_url:
        logging.info(f"Crawling: {current_url}")
        try:
            response = requests.get(current_url)
            response.raise_for_status()
            
            links, next_url = extract_links_from_page(response.text)
            
            new_urls_found = len(set(links) - all_urls)
            all_urls.update(links)
            
            logging.info(f"Found {len(links)} links on this page. {new_urls_found} new.")
            
            # For testing pagination, stop after a few pages if needed, 
            # or continue if next_url is found.
            if next_url:
                # Handle relative URLs if necessary
                if next_url.startswith('/'):
                    # Assuming The Hindu root is www.thehindu.com
                    # This might need adjustment.
                    next_url = f"https://www.thehindu.com{next_url}"
                current_url = next_url
                time.sleep(1) # Be polite
            else:
                current_url = None
                
        except Exception as e:
            logging.error(f"Error crawling {current_url}: {e}")
            break
            
    return all_urls
