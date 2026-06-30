import os
import re

def extract_metadata(file_path):
    """
    Reads .rst file headers to extract metadata.
    Specifically looks for a "The Hindu: <URL>" line in the content.
    """
    metadata = {
        'canonical_url': None,
        'title': None,
        'date': None
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Extract title (usually the first part underlined with =)
        title_match = re.search(r'^(.+)\n=+\n', content, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
            
        # Extract date
        date_match = re.search(r'^:date: (.+)$', content, re.MULTILINE)
        if date_match:
            metadata['date'] = date_match.group(1).strip()
            
        # Extract canonical URL
        url_match = re.search(r'^The Hindu: (https://www\.thehindu\.com/.+)$', content, re.MULTILINE)
        if url_match:
            metadata['canonical_url'] = url_match.group(1).strip()
            
    return metadata

def scan_content_directory(content_path):
    """
    Walks the directory recursively and builds a registry of existing articles.
    """
    existing_articles = []
    
    for root, dirs, files in os.walk(content_path):
        for file in files:
            if file.endswith('.rst'):
                file_path = os.path.join(root, file)
                metadata = extract_metadata(file_path)
                metadata['filename'] = file
                metadata['slug'] = os.path.splitext(file)[0]
                existing_articles.append(metadata)
                
    return existing_articles
