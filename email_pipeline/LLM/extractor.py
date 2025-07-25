import os
import re
import json
import openai
from typing import Optional, List, Dict
from dotenv import load_dotenv
from prompts.templates import FALLBACK_MATCH_PROMPT

# Load OpenAI API Key from environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def query_openai(prompt: str) -> Optional[dict]:
    """
    Send a structured extraction prompt to OpenAI and parse the JSON response.

    Args:
        prompt (str): The formatted prompt to send.

    Returns:
        Optional[dict]: Parsed JSON response or None on failure.
    """
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract structured data from emails. "
                        "Return ONLY valid JSON. Enclose all keys and string values in double quotes. "
                        "Return no more than 5 items. No explanation or extra text."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()

        # Strip trailing commas before parsing (optional cleanup)
        content = re.sub(r',\s*([}\]])', r'\1', content)

        return json.loads(content)

    except json.JSONDecodeError as json_err:
        print(f"❌ Failed to decode JSON: {json_err}")
        print("🔎 Raw content from OpenAI:")
        print(content)
        return None
    except Exception as e:
        print(f"❌ OpenAI query error: {e}")
        return None


def match_item_desc_via_gpt(item_description: str, candidate_items: List[Dict]) -> dict:
    """
    Match a short item description to the best candidate from a list using GPT.

    Args:
        item_description (str): Raw item description from email.
        candidate_items (list): List of known items from DB.

    Returns:
        dict: Best-matching candidate row or empty dict if no confident match.
    """
    if not candidate_items:
        return {}

    prompt = FALLBACK_MATCH_PROMPT.format(
        short_desc=item_description,
        candidates=json.dumps(candidate_items, indent=2)
    )

    result = query_openai(prompt)
    return result if isinstance(result, dict) and "entry_id" in result else {}


def match_item_desc_via_gpt_returns(item_description: str, candidate_items: List[Dict]) -> dict:
    """
    Specialized variant for matching return items to known candidates using GPT.

    Ensures GPT does not hallucinate by checking the match is among provided candidates.

    Args:
        item_description (str): Short return item description.
        candidate_items (list): Known return items in DB.

    Returns:
        dict: Matched item row or empty dict if none found.
    """
    if not candidate_items:
        return {}

    prompt = FALLBACK_MATCH_PROMPT.format(
        short_desc=item_description,
        candidates=json.dumps(candidate_items, indent=2)
    )

    result = query_openai(prompt)

    # Only accept result if it matches one of the known candidates
    if isinstance(result, dict) and result in candidate_items:
        print("✅ LLM matched return item successfully.")
        return result

    print("🆕 LLM returned no valid match.")
    return {}
