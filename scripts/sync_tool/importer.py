import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import date

def fetch_and_format_article(url):
    """
    Fetches article content and formats it as a basic .rst file.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Very basic extraction - might need adjustment per site structure
    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "Untitled"
    
    # Extract main content - heuristic approach
    article_body = soup.find('div', class_='article-body') or soup.find('article')
    if not article_body:
        raise ValueError("Could not find article content.")
        
    content = article_body.get_text(separator='\n', strip=True)
    
    # Format as .rst
    rst_content = f"{title}\n" + "=" * len(title) + "\n\n"
    rst_content += f":date: {date.today().isoformat()}\n"
    rst_content += ":category: Articles\n"
    rst_content += f":canonical: {url}\n\n"
    rst_content += content
    
    # Create filename
    slug = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())[:50]
    filename = f"{slug}.rst"
    
    return filename, rst_content

def process_imports(missing_file):
    with open(missing_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
        
    imported = []
    failed = []
    
    for url in urls:
        try:
            filename, content = fetch_and_format_article(url)
            filepath = os.path.join('content', filename)
            
            # Avoid overwrite
            if os.path.exists(filepath):
                filename = f"{os.path.splitext(filename)[0]}-2.rst"
                filepath = os.path.join('content', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            imported.append(url)
        except Exception as e:
            failed.append((url, str(e)))
            
    return imported, failed
