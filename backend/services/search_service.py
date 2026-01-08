import os
import re
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from openai import OpenAI
from .excel_service import append_result

# Initialize OpenAI client
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def search_clinic(query: str):
    """
    Orchestrates the search process:
    1. Try DuckDuckGo (duckduckgo-search lib).
    2. Deep Search: Visit top 3 links and scrape text.
    3. If fails/no phone, try OpenAI.
    4. Save result.
    """
    phone_number = None
    source = "Not Found"
    
    print(f"Searching via DuckDuckGo for: {query}")
    try:
        start_urls = []
        
        # Use DDGS context manager
        with DDGS() as ddgs:
            # text() returns an iterator of dicts: {'title':..., 'href':..., 'body':...}
            ddgs_gen = ddgs.text(query, region='it-it', safesearch='off', max_results=5)
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

        # DEEP SEARCH: Scrape the top URLs
        if start_urls:
            print(f"Found {len(start_urls)} URLs. Starting Deep Search on top 3...")
            
            for url in start_urls[:3]:
                page_text = scrape_url(url)
                if page_text:
                    # Attempt 1: Regex on page text
                    extracted_phone = extract_phone_from_text(page_text[:10000]) # Limit text size
                    if extracted_phone:
                        phone_number = extracted_phone
                        source = f"Deep Search ({url}) + Regex"
                        print(f"Phone found on {url}: {phone_number}")
                        break # Stop if found
                    
                    # Attempt 2: OpenAI Extraction on page snippets
                    # Only do this if regex failed, to save tokens, or if we want high accuracy
                    # For now, let's stick to regex for speed, or maybe use OpenAI if regex fails?
                    # Let's try OpenAI only if we are desperate or valid pattern check is weak.
                    # Given the user wants "parse the research", regex is a good first step.
                    
                    # If regex failed, let's give OpenAI a shot at the page content (truncated)
                    # This increases cost/time but fulfills "Deep Search"
                    if client and not phone_number:
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
                                phone_number = content.strip()
                                source = f"Deep Search ({url}) + OpenAI"
                                print(f"OpenAI found phone on {url}: {phone_number}")
                                break
                        except Exception as e:
                            print(f"OpenAI Error on {url}: {e}")
            
        else:
            print("No URLs found to scrape.")

    except Exception as e:
        print(f"DuckDuckGo Error: {e}")

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
        except Exception as e:
            print(f"OpenAI Error: {e}")

    # Save logic
    final_phone = phone_number if phone_number else "Not Found"
    append_result(query, final_phone, source)
    
    return {
        "query": query,
        "phone_number": final_phone,
        "source": source
    }
