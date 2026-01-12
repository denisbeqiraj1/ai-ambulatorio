import os
from openai import OpenAI
from .excel_service import append_result
from .search_local import search_clinic_local
from .search_chatgpt import deepsearch_web_structured

# ==========================
# Configuration
# ==========================

ENGINE = os.getenv("ENGINE", "local")  # local | deepsearch

client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
# Main Search Function
# ==========================
def search_clinic(query: str, engine: str | None = None):
    engine = (engine or ENGINE).lower()
    if not validate_topic(query):
        return {
            "query": query,
            "phone_number": "Off-Topic",
            "source": "Validation",
        }

    # ======================
    # DEEPSEARCH MODE
    # ======================
    if engine == "deepsearch":
        if not client:
            return {
                "query": query,
                "phone_number": "Not Found",
                "source": "OpenAI WebSearch (missing API key)",
            }
        result = deepsearch_web_structured(client,query)

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

    return search_clinic_local(query)
