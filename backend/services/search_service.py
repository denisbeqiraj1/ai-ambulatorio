import os
import re
from collections import Counter
from openai import OpenAI
from ddgs import DDGS
from .excel_service import append_result
from bs4 import BeautifulSoup
import requests

# Initialize OpenAI client
client = None
engine_type = os.getenv("ENGINE", "local")  # "local" or "deepsearch"
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_DEEP_SEARCH = int(os.getenv("MAX_DEEP_SEARCH", "3"))

# =======================
# Utility Functions
# =======================

def validate_topic(query: str) -> bool:
    """Validate if query is about medical clinics, doctors, or healthcare."""
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
                    "Reply ONLY with 'YES' if it is relevant, or 'NO' otherwise."
                )},
                {"role": "user", "content": f"Query: {query}"}
            ],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().upper()
        print(f"Topic Validation: {answer}")
        return "YES" in answer
    except Exception as e:
        print(f"Validation Error: {e}")
        return True

def extract_phone_from_text(text: str):
    """Extract phone numbers using regex."""
    phone_pattern = r"(\+?\d{1,3}[\s-]?)?(\(?\d{1,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}"
    matches = [m.group() for m in re.finditer(phone_pattern, text)]
    return matches[0] if matches else None

def deepsearch_extract_phone(query: str):
    """
    Uses OpenAI agentic web search to find a phone number and its URL.
    Returns structured JSON: {"phone_number": str, "source_url": str}
    """
    if not client:
        return {"phone_number": "OpenAI client not initialized", "source_url": None}

    try:
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=f"""
Search the web for the medical clinic or doctor matching this query:
"{query}"

Return exactly a JSON object with TWO keys:
1) "phone_number" — the public phone number you found
2) "source_url" — the URL where that phone number was found

If no phone or URL is found, return:
{{
  "phone_number": "Not Found",
  "source_url": "Not Found"
}}
""",
            response_format={
                "json_schema": {
                    "name": "clinic_phone_search",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "phone_number": {
                                "description": "The extracted phone number",
                                "type": "string"
                            },
                            "source_url": {
                                "description": "The URL where the number was found",
                                "type": "string"
                            }
                        },
                        "required": ["phone_number", "source_url"]
                    }
                }
            }
        )
        output_json = response.output_parsed
        return output_json

    except Exception as e:
        print(f"DeepSearch Error: {e}")
        return {"phone_number": "Error", "source_url": None}

# =======================
# Main Search Function
# =======================

def search_clinic(query: str):
    """
    Main orchestrator:
    - Local mode: DuckDuckGo + scraping + regex/OpenAI extraction
    - Deepsearch mode: Agentic OpenAI web search, structured JSON output
    """
    if not validate_topic(query):
        return {
            "query": query,
            "phone_number": "Off-Topic",
            "source": "Input Validation"
        }

    if engine_type == "deepsearch":
        # Agentic deep search
        result = deepsearch_extract_phone(query)
        append_result(query, result["phone_number"], result["source_url"])
        return {
            "query": query,
            "phone_number": result["phone_number"],
            "source": "DeepSearch Agentic",
            "details": [
                {"url": result["source_url"], "phone": result["phone_number"]}
            ]
        }

    phone_number = None
    source = "Not Found"
    found_details = []

    # Fetch URLs using DuckDuckGo
    start_urls = []
    try:
        with DDGS() as ddgs:
            ddgs_gen = ddgs.text(query, region="it-it", safesearch="off", max_results=MAX_DEEP_SEARCH)
            start_urls = [r["href"] for r in ddgs_gen if r.get("href")]
    except Exception as e:
        print(f"DuckDuckGo Error: {e}")

    for url in start_urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for s in soup(["script", "style"]):
                s.decompose()
            page_text = soup.get_text(separator=" ", strip=True)

            # Regex extraction
            extracted_phone = extract_phone_from_text(page_text[:10000])

            # OpenAI fallback
            if not extracted_phone and client:
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": (
                                "Extract the public phone number for the clinic/doctor. "
                                "If none, reply 'Not Found'."
                            )},
                            {"role": "user", "content": page_text[:3000]}
                        ]
                    )
                    content = resp.choices[0].message.content.strip()
                    if "Not Found" not in content:
                        extracted_phone = content
                except Exception as e:
                    print(f"OpenAI phone extraction error: {e}")

            if extracted_phone:
                found_details.append({
                    "url": url,
                    "phone": extracted_phone,
                    "method": "Regex/OpenAI"
                })

        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # Consensus logic
    if found_details:
        all_phones = [d["phone"] for d in found_details]
        most_common = Counter(all_phones).most_common(1)[0]
        phone_number = most_common[0]
        count = most_common[1]
        source = f"Deep Search ({count}/{len(found_details)})"

    final_phone = phone_number or "Not Found"
    top_url = next((d["url"] for d in found_details if d["phone"] == final_phone), "Not Found")
    append_result(query, final_phone, top_url)

    return {
        "query": query,
        "phone_number": final_phone,
        "source": source,
        "details": found_details
    }
