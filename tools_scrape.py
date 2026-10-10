import json
from scrapling.fetchers import StealthyFetcher

def fetch_web_data(url: str) -> str:
    try:
        print(f"[*] Fetching target: {url} via Scrapling...")
        page = StealthyFetcher.fetch(url, headless=True)
        text_content = page.css('body ::text').getall()
        clean_text = " ".join([t.strip() for t in text_content if t.strip()])
        return clean_text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(fetch_web_data(sys.argv[1]))
    else:
        print("Usage: python tools_scrape.py <url>")
