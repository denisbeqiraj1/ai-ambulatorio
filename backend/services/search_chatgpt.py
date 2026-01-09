from openai import OpenAI
from pydantic import BaseModel

# ==========================
# Structured Output Model
# ==========================

class ClinicContact(BaseModel):
    phone_number: str
    source_url: str

# ==========================
# DeepSearch Engine
# ==========================

def deepsearch_web_structured(client,query: str) -> ClinicContact:
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
                    "Return exactly ONE phone number and the URL where it was found, no description the PRECISE URL, no more information.\n"
                    "If none found, return 'Not Found' for both fields."
                ),
            },
            {"role": "user", "content": query},
        ],
        text_format=ClinicContact,
    )

    return response.output_parsed