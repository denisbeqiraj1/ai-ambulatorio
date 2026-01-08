import os
import re
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

def search_clinic(query: str):
    """
    Orchestrates the search process:
    1. Try DuckDuckGo (duckduckgo-search lib).
    2. If fails/no phone, try OpenAI.
    3. Save result.
    """
    phone_number = None
    source = "Not Found"
    
    print(f"Searching via DuckDuckGo for: {query}")
    try:
        results_text = ""
        # Use DDGS context manager
        with DDGS() as ddgs:
            # text() returns an iterator of dicts: {'title':..., 'href':..., 'body':...}
            ddgs_gen = ddgs.text(query, region='it-it', safesearch='off', max_results=5)
            if ddgs_gen:
                results = list(ddgs_gen)
                if results:
                    for r in results:
                        title = r.get('title', '')
                        body = r.get('body', '')
                        results_text += f"{title}: {body}\n"
                else:
                    print("DuckDuckGo returned no results.")
            else:
                print("DuckDuckGo generator empty.")

        if results_text:
            print(f"DuckDuckGo found content. Length: {len(results_text)}")
            
            # Attempt 1: Regex
            extracted_phone = extract_phone_from_text(results_text)
            if extracted_phone:
                phone_number = extracted_phone
                source = "DuckDuckGo + Regex"
            
            # Attempt 2: OpenAI Extraction
            if not phone_number and client:
                print("Extracting phone from DuckDuckGo snippets via OpenAI...")
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Extract the phone number from these search results. If multiple, choose the most relevant. If none, say 'Not Found'."},
                            {"role": "user", "content": f"Query: {query}\n\nSearch Results:\n{results_text}"}
                        ]
                    )
                    content = resp.choices[0].message.content
                    if "Not Found" not in content:
                        phone_number = content.strip()
                        source = "DuckDuckGo + OpenAI Extraction"
                except Exception as e:
                    print(f"OpenAI Extraction Error: {e}")
        else:
            print("No text content gathered from DuckDuckGo.")

    except Exception as e:
        print(f"DuckDuckGo Error: {e}")

    # Solution 2: ChatGPT Fallback
    if not phone_number and client:
        print("DuckDuckGo failed or yielded no result. Switching to OpenAI.")
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
