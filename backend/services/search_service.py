import os
import re
import requests
from collections import Counter
from bs4 import BeautifulSoup
from ddgs import DDGS
from openai import OpenAI
from pydantic import BaseModel
from .excel_service import append_result

# ==========================
# Configuration
# ==========================

ENGINE = os.getenv("ENGINE", "local")  # local | deepsearch
MAX_DEEP_SEARCH = int(os.getenv("MAX_DEEP_SEARCH", "3"))

client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================
# Structured Output Model
# ==========================

class ClinicContact(BaseModel):
    phone_number: str
    source_url: str

# ==========================
# Validation
# ==========================

def validate_topic(query: str) -> bool:
    if not client:
        return True

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Check if the query is related to medical clinics, doctors, "
                        "hospitals, or healthcare. Reply ONLY with YES or NO."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0,
        )
        return "YES" in response.choices[0].message.content.upper()
    except Exception:
        return True

# ==========================
# Local Engine Helpers
# ==========================

def extract_phone_from_text(text: str):
    phone_pattern = r"(\+?\d[\d\s\-]{6,}\d)"
    matches = [m.group() for m in re.finditer(phone_pattern, text)]
    return matches[0] if matches else None

def scrape_url(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        return ""

def fetch_search_urls(query: str, max_results: int) -> list[str]:
    urls = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                query,
                region="it-it",
                safesearch="off",
                max_results=max_results,
            )
            for r in results:
                if r.get("href"):
                    urls.append(r["href"])
    except Exception:
        pass
    return urls

# ==========================
# DeepSearch Engine
# ==========================

def deepsearch_web_structured(query: str) -> ClinicContact:
    """
    OpenAI Web Search + Structured Output (Pydantic)
    """

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        tools=[{"type": "web_search"}],
        input=[
            {
                "role": "system",
                "content": (
                    "You are a web research agent.\n"
                    "Find the OFFICIAL public phone number of the medical clinic or doctor.\n"
                    "Return exactly ONE phone number and the URL where it was found, no description the correct URL of the phone number.\n"
                    "If none found, return 'Not Found' for both fields."
                ),
            },
            {"role": "user", "content": query},
        ],
        text_format=ClinicContact,
    )

    return response.output_parsed

# ==========================
# Main Search Function
# ==========================

def search_clinic(query: str):
    if not validate_topic(query):
        return {
            "query": query,
            "phone_number": "Off-Topic",
            "source": "Validation",
        }

    # ======================
    # DEEPSEARCH MODE
    # ======================
    if ENGINE == "deepsearch":
        result = deepsearch_web_structured(query)

        append_result(
            query,
            result.phone_number,
            result.source_url,
        )

        return {
            "query": query,
            "phone_number": result.phone_number,
            "source": "OpenAI WebSearch",
            "details": [
                {
                    "phone": result.phone_number,
                    "url": result.source_url,
                    "method": "OpenAI WebSearch"
                }
            ],
        }

    # ======================
    # LOCAL MODE
    # ======================
    phone_number = None
    found_details = []

    urls = fetch_search_urls(query, MAX_DEEP_SEARCH)

    for url in urls[:MAX_DEEP_SEARCH]:
        text = scrape_url(url)
        if not text:
            continue

        phone = extract_phone_from_text(text[:10000])

        # OpenAI fallback per-page
        if not phone and client:
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Extract the public phone number from the text. "
                                "If none exists, reply 'Not Found'."
                            ),
                        },
                        {"role": "user", "content": text[:3000]},
                    ],
                )
                content = resp.choices[0].message.content.strip()
                if "Not Found" not in content:
                    phone = content
            except Exception:
                pass

        if phone:
            found_details.append(
                {"url": url, "phone": phone, "method": "Local"}
            )

    if found_details:
        phones = [d["phone"] for d in found_details]
        phone_number = Counter(phones).most_common(1)[0][0]

    final_phone = phone_number or "Not Found"
    top_url = next(
        (d["url"] for d in found_details if d["phone"] == final_phone),
        "Not Found",
    )

    append_result(query, final_phone, top_url)

    return {
        "query": query,
        "phone_number": final_phone,
        "source": "Local Search",
        "details": found_details,
    }
