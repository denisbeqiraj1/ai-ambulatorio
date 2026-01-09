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
engine_type = os.getenv("ENGINE", "local")  # "local" or "deepsearch"
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration
MAX_DEEP_SEARCH = int(os.getenv("MAX_DEEP_SEARCH", "3"))

def validate_topic(query: str) -> bool:
    """Validates if the query is related to medical clinics, doctors, or healthcare."""
    if not client:
        print("OpenAI client not initialized, skipping validation.")
        return True

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are a content filter. Check if the user query is related to "
                    "medical clinics, doctors, hospitals, healthcare, or finding medical contacts in Italy. "
                    "Reply ONLY with 'YES' if it is relevant, or 'NO' if it is off-topic (e.g. pizza, gaming, entertainment)."
                )},
                {"role": "user", "content": f"Query: {query}"}
            ],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().upper()
        print(f"Topic Validation for '{query}': {answer}")
        return "YES" in answer
    except Exception as e:
        print(f"Validation Error: {e}")
        return True

def extract_phone_from_text(text: str):
    """Extract phone numbers using regex."""
    phone_pattern = r"(\+?\d{1,3}[\s-]?)?(\(?\d{1,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
    matches = re.findall(phone_pattern, text)
    if matches:
        valid_phones = [m.group() for m in re.finditer(phone_pattern, text)]
        return valid_phones[0] if valid_phones else None
    return None

def scrape_url(url: str):
    """Fetch URL content and return visible text."""
    try:
        print(f"Scraping URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def fetch_search_urls(query: str, max_results: int) -> list[str]:
    """Fetch search URLs depending on engine type."""
    urls = []

    if engine_type == "local":
        # DuckDuckGo search
        print(f"Searching via DuckDuckGo for: {query}")
        try:
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(query, region='it-it', safesearch='off',
                                     max_results=max_results, backend='duckduckgo')
                if ddgs_gen:
                    results = list(ddgs_gen)
                    urls = [r['href'] for r in results if r.get('href')]
        except Exception as e:
            print(f"DuckDuckGo Error: {e}")

    elif engine_type == "deepsearch":
        # OpenAI Web Search
        if not client:
            print("OpenAI client not initialized for DeepSearch.")
            return urls
        print(f"Searching via OpenAI Web Search for: {query}")
        try:
            resp = client.web_search.create(
                query=query,
                num_results=max_results
            )
            for item in resp['results']:
                href = item.get('url') or item.get('link')
                if href:
                    urls.append(href)
        except Exception as e:
            print(f"OpenAI Web Search Error: {e}")

    return urls

def search_clinic(query: str):
    """Main orchestrator for clinic search."""
    if not validate_topic(query):
        print(f"Query '{query}' rejected as off-topic.")
        return {
            "query": query,
            "phone_number": "Off-Topic",
            "source": "Input Validation"
        }

    phone_number = None
    source = "Not Found"
    found_details = []

    start_urls = fetch_search_urls(query, MAX_DEEP_SEARCH)

    if start_urls:
        print(f"Found {len(start_urls)} URLs. Starting Deep Search on top {MAX_DEEP_SEARCH}...")
        for url in start_urls[:MAX_DEEP_SEARCH]:
            page_text = scrape_url(url) if engine_type == "local" else None

            extracted_phone = None
            if engine_type == "local" and page_text:
                extracted_phone = extract_phone_from_text(page_text[:10000])
            
            # If local fails or deepsearch mode, use OpenAI extraction
            if (engine_type == "deepsearch" or not extracted_phone) and client:
                try:
                    prompt_text = page_text[:3000] if page_text else query
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": (
                                "Extract the public phone number for the medical clinic/doctor from the text below. "
                                "If none, say 'Not Found'."
                            )},
                            {"role": "user", "content": f"Page Text or Query:\n{prompt_text}"}
                        ]
                    )
                    content = resp.choices[0].message.content.strip()
                    if "Not Found" not in content:
                        extracted_phone = content
                except Exception as e:
                    print(f"OpenAI extraction error on {url}: {e}")

            if extracted_phone:
                print(f"Phone found on {url}: {extracted_phone}")
                found_details.append({
                    "url": url,
                    "phone": extracted_phone,
                    "method": "OpenAI" if engine_type == "deepsearch" else "Regex/OpenAI"
                })

        # CONSENSUS
        if found_details:
            all_phones = [d['phone'] for d in found_details]
            most_common = Counter(all_phones).most_common(1)[0]
            phone_number = most_common[0]
            count = most_common[1]
            source = f"Deep Search ({count}/{len(found_details)} similar results)"
            print(f"Consensus Phone: {phone_number} ({count} occurrences)")

    else:
        print("No URLs found to search.")

    final_phone = phone_number or "Not Found"
    top_url = next((d['url'] for d in found_details if d['phone'] == final_phone), "Not Found")

    append_result(query, final_phone, top_url)

    return {
        "query": query,
        "phone_number": final_phone,
        "source": source,
        "details": found_details
    }
