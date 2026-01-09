import re
import requests
from collections import Counter
from bs4 import BeautifulSoup
from ddgs import DDGS
from .excel_service import append_result
import os

MAX_DEEP_SEARCH = int(os.getenv("MAX_DEEP_SEARCH", "3"))

def extract_phone_from_text(text: str):
    """
    Simple regex to extract phone numbers from a text block.
    """
    phone_pattern = r"(\+?\d{1,3}[\s-]?)?(\(?\d{1,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
    matches = re.findall(phone_pattern, text)
    if matches:
        valid_phones = []
        for match in re.finditer(phone_pattern, text):
            valid_phones.append(match.group())
        return valid_phones[0] if valid_phones else None
    return None

def scrape_url(url: str):
    """
    Fetches the content of a URL and returns the visible text.
    """
    try:
        print(f"Scraping URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def fetch_search_urls(query: str, max_results: int, engine: str = "duckduckgo") -> list[str]:
    """
    Fetches search result URLs from a specified search engine.
    """
    start_urls = []
    print(f"Searching via {engine} for: {query}")
    
    try:
        # Use DDGS context manager
        with DDGS() as ddgs:
            # text() returns an iterator of dicts: {'title':..., 'href':..., 'body':...}
            ddgs_gen = ddgs.text(query, region='it-it', safesearch='off', max_results=max_results, backend='duckduckgo')
            if ddgs_gen:
                results = list(ddgs_gen)
                if results:
                    for r in results:
                        href = r.get('href')
                        if href:
                            start_urls.append(href)
                else:
                    print("DuckDuckGo returned no results.")
            else:
                print("DuckDuckGo generator empty.")
    except Exception as e:
        print(f"DuckDuckGo Error: {e}")
            
    return start_urls


def search_clinic_local(query: str):
    """
    Orchestrates the search process:
    1. Validation: Check if query is in-topic (ambulatori/medical).
    2. Try DuckDuckGo (duckduckgo-search lib).
    3. Deep Search: Visit top N links and scrape text.
    4. Consensus: Check found phone numbers and pick the most frequent.
    5. If fails/no phone, try OpenAI.
    6. Save result.
    """

    phone_number = None
    source = "Not Found"
    found_details = [] # List of {url, phone, method}
    
    # 2. Results via Search Engine
    start_urls = fetch_search_urls(query, MAX_DEEP_SEARCH, engine="duckduckgo")

    # DEEP SEARCH: Scrape the top URLs
    if start_urls:
        print(f"Found {len(start_urls)} URLs. Starting Deep Search on top {MAX_DEEP_SEARCH}...")
        
        for url in start_urls[:MAX_DEEP_SEARCH]:
            page_text = scrape_url(url)
            if page_text:
                # Attempt 1: Regex on page text
                extracted_phone = extract_phone_from_text(page_text[:10000]) # Limit text size
                if extracted_phone:
                    print(f"Phone found on {url} (Regex): {extracted_phone}")
                    found_details.append({
                        "url": url,
                        "phone": extracted_phone,
                        "method": "Regex"
                    })
        
        # CONSENSUS LOGIC
        if found_details:
            # Extract just phone numbers for frequency count
            all_phones = [d['phone'] for d in found_details]
            print(f"Collected phones: {all_phones}")
            most_common = Counter(all_phones).most_common(1)
            phone_number = most_common[0][0]
            count = most_common[0][1]
            source = f"Deep Search ({count}/{len(found_details)} ricerche simili)"
            print(f"Consensus Phone: {phone_number} ({count} occurrences)")
        
    else:
        print("No URLs found to scrape.")

    # Save logic
    final_phone = phone_number if phone_number else "Not Found"
    # Find the first URL where the consensus phone was found
    top_url = "Not Found"
    for detail in found_details:
        if detail['phone'] == final_phone:
            top_url = detail['url']
            break

    # Append result to Google Sheet using the URL of the most common phone
    append_result(query, final_phone, top_url)
    
    return {
        "query": query,
        "phone_number": final_phone,
        "source": source,
        "details": found_details
    }