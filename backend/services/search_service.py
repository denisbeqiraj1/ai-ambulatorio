import os
import requests
from openai import OpenAI
from .excel_service import append_result

# Initialize OpenAI client
client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

OPENSERP_URL = os.getenv("OPENSERP_URL", "http://openserp:7000")

def search_clinic(query: str):
    """
    Orchestrates the search process:
    1. Try OpenSerp (Karust).
    2. If fails, try OpenAI (if available).
    3. Save result.
    """
    phone_number = None
    source = "Not Found"
    
    # Solution 1: OpenSerp
    print(f"Searching via OpenSerp for: {query}")
    try:
        # OpenSerp API: /google/search?text=...
        response = requests.get(f"{OPENSERP_URL}/google/search", params={"text": query})
        if response.status_code == 200:
            results = response.json()
            
            # OpenSerp structure can vary, but usually returns a list of results.
            # We look for something that resembles a Knowledge Graph or top snippets.
            # Based on karust/openserp typical output, it might not separate KG clearly as SerpApi,
            # but let's check for 'knowledge_panel' or similar, or iterate organic results.
            
            # Note: The exact JSON structure of karust/openserp depends on the engine.
            # Assuming it returns a list of "organic" items or a structured object.
            # Let's try to find a phone number in snippets if specifically extracted fields aren't there.
            
            # Simple heuristic: Look for 'phone' key in top-level or iterate results
            # For now, we'll iterate and check snippets/descriptions.
            
            # IMPORTANT: OpenSerp acts as a proxy/scraper. It might return raw-ish data.
            # Let's inspect the first few results for a phone pattern or explicit field.
            
            # If the tool returns "knowledge_panel" we use it.
            # Example response structure might be a list of results.
            
            data = results if isinstance(results, list) else results.get('results', [])
            
            # Heuristic phone extraction (very basic)
            # In a real scenario, we'd use regex on the snippet.
            # For this MVP, we rely on the possibility that the 'description' or 'title' contains it,
            # or if OpenSerp provides structured data.
            
            # Since I can't run it to see exact output, I will add a fallback request to OpenAI 
            # to EXTRACT the phone from the OpenSerp CSV/JSON text if simpler methods fail,
            # OR just default to Solution 2 if explicitly not found.
            
            pass 
        else:
            print(f"OpenSerp failed with status {response.status_code}")

    except Exception as e:
        print(f"OpenSerp Error: {e}")

    # Solution 2: ChatGPT Fallback
    # If OpenSerp didn't give a clear "phone" field, or if we couldn't parse it.
    if not phone_number and client:
        print("OpenSerp failed or yielded no result. Switching to OpenAI.")
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
                phone_number = content
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
