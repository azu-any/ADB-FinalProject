import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

class WebScraper:
    def __init__(self, docs_dir="data/documents", metadata_path="data/metadata.json"):
        self.docs_dir = docs_dir
        self.metadata_path = metadata_path
        os.makedirs(self.docs_dir, exist_ok=True)

    def scrape_and_save(self, url):
        """Scrapes a URL, extracts text and title, saves it, and updates metadata."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LSI Search Engine/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = soup.title.string.strip() if soup.title else "Untitled Document"
            
            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()

            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Create a safe filename
            safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())
            filename = f"{safe_title[:30]}_web.txt"
            filepath = os.path.join(self.docs_dir, filename)

            # Save the document
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

            # Update metadata
            self._update_metadata(filename, title, url)
            
            return filename, title

        except Exception as e:
            print(f"Scraping error: {e}")
            raise Exception(f"Failed to scrape URL: {e}")

    def _update_metadata(self, filename, title, url):
        """Appends the new document metadata to metadata.json."""
        metadata = {}
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                try:
                    metadata = json.load(f)
                except json.JSONDecodeError:
                    pass

        # Extract domain for author
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        author = domain.replace('www.', '').capitalize()
        date_str = datetime.now().strftime("%Y-%m-%d")

        metadata[filename] = {
            "title": title,
            "author": author,
            "date": date_str,
            "url": url
        }

        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)
            
        print(f"✅ Saved and metadata updated for {filename}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        scraper = WebScraper()
        scraper.scrape_and_save(url)
        print("Done.")
