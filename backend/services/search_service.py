import os
import re
import requests
from bs4 import BeautifulSoup
from collections import Counter
from ddgs import DDGS
from openai import OpenAI
from .excel_service import append_result

# Initialize OpenAI client
client = None
# Initialize OpenAI client
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration using simple integer conversion with default fallback
MAX_DEEP_SEARCH = int(os.getenv("MAX_DEEP_SEARCH", "3"))

def validate_topic(query: str) -> bool:
    """
    Validates if the query is related to medical clinics, doctors, or healthcare.
    Returns True if relevant, False otherwise.
    """
    if not client:
        print("OpenAI client not initialized, skipping validation.")
        return True

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a content filter. Check if the user query is related to medical clinics, doctors, hospitals, healthcare, or finding medical contacts in Italy. Reply ONLY with 'YES' if it is relevant, or 'NO' if it is off-topic (e.g. pizza, gaming, entertainment)."},
                {"role": "user", "content": f"Query: {query}"}
            ],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().upper()
        print(f"Topic Validation for '{query}': {answer}")
        return "YES" in answer
    except Exception as e:
        print(f"Validation Error: {e}")
        # Fail open if validation errors out to avoid blocking legitimate requests during outages
        return True

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

def search_clinic(query: str):
    """
    Orchestrates the search process:
    1. Validation: Check if query is in-topic (ambulatori/medical).
    2. Try DuckDuckGo (duckduckgo-search lib).
    3. Deep Search: Visit top N links and scrape text.
    4. Consensus: Check found phone numbers and pick the most frequent.
    5. If fails/no phone, try OpenAI.
    6. Save result.
    """
    
    # 1. Input Validation
    if not validate_topic(query):
        print(f"Query '{query}' rejected as off-topic.")
        return {
            "query": query,
            "phone_number": "Off-Topic",
            "source": "Input Validation"
        }

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
                    # Continue to build consensus
                
                # Attempt 2: OpenAI Extraction on page snippets
                # Only if regex failed for this URL
                elif client:
                    print(f"Regex failed on {url}, asking OpenAI...")
                    try:
                        resp = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "Extract the public phone number for the medical clinic/doctor from the text below. If none, say 'Not Found'."},
                                {"role": "user", "content": f"Page Text:\n{page_text[:3000]}"}
                            ]
                        )
                        content = resp.choices[0].message.content
                        if "Not Found" not in content:
                            p_num = content.strip()
                            print(f"OpenAI found phone on {url}: {p_num}")
                            found_details.append({
                                "url": url,
                                "phone": p_num,
                                "method": "OpenAI"
                            })
                    except Exception as e:
                        print(f"OpenAI Error on {url}: {e}")
        
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

    # Solution 2: ChatGPT Fallback
    if not phone_number and client:
        print("Deep Search failed. Switching to OpenAI direct knowledge.")
        try:
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that finds public phone numbers for medical clinics. If you don't know it, say 'Not Found'."},
                    {"role": "user", "content": f"Find the phone number for: {query}"}
                ]
            )
            content = response.choices[0].message.content
            if "Not Found" not in content:
                phone_number = content.strip()
                source = "OpenAI"
                found_details.append({
                    "url": "OpenAI Direct Knowledge",
                    "phone": phone_number,
                    "method": "LLM Fallback"
                })
        except Exception as e:
            print(f"OpenAI Error: {e}")

    # Save logic
    final_phone = phone_number if phone_number else "Not Found"
    append_result(query, final_phone, source)
    
    return {
        "query": query,
        "phone_number": final_phone,
        "source": source,
        "details": found_details
    }
