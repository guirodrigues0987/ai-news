"""
Step 2: Relevance filtering + script generation via LLM
Reads news_raw.json (output of fetch_news.py), filters items by relevance,
removes semantic duplicates and writes a presenter-style podcast script
using the Anthropic API, falling back to Gemini if the primary call fails.
"""

import json
import os
import sys

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-8"

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "selected_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["title", "url", "source"],
                "additionalProperties": False,
            },
        },
        "script": {"type": "string"},
    },
    "required": ["selected_items", "script"],
    "additionalProperties": False,
}

# The podcast itself is narrated in Brazilian Portuguese; the prompt is in English.
SYSTEM_PROMPT = """You are the host of a daily podcast about Artificial Intelligence \
news. You receive a list of items (Hacker News + RSS from official blogs) and must:

1. Select only the items that are truly relevant to people who follow AI closely \
(researchers, engineers, enthusiasts) - discard weak items, clickbait, or items \
without technical/strategic substance.
2. Remove semantic duplicates (different items covering the same story), keeping \
the most reliable or most complete source.
3. Write a podcast script in Brazilian Portuguese, in a host's voice explaining \
the news with context and light opinion - not a dry summary, but an engaging \
conversation with a short opening and closing.

Respond only with the requested structured data."""


def load_news(path: str = "news_raw.json") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_user_content(items: list[dict]) -> str:
    return f"Collected items:\n{json.dumps(items, ensure_ascii=False, indent=2)}"


def generate_script_anthropic(items: list[dict]) -> dict:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": SCRIPT_SCHEMA},
        },
        messages=[{"role": "user", "content": build_user_content(items)}],
    )
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


GEMINI_MODEL = "gemini-3.8-flash"


def generate_script_gemini(items: list[dict]) -> dict:
    """Non-Anthropic fallback: Gemini, used only if the call above fails."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        input=build_user_content(items),
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": SCRIPT_SCHEMA,
        },
    )
    return json.loads(interaction.output_text)


def main():
    items = load_news()
    try:
        result = generate_script_anthropic(items)
    except Exception as e:
        # Any Anthropic failure (API, network, missing/invalid credential)
        # falls back to Gemini - not just API errors.
        print(f"Anthropic call failed ({e}); falling back to Gemini.", file=sys.stderr)
        result = generate_script_gemini(items)

    output_path = "script.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Script generated with {len(result['selected_items'])} selected items.")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
