"""
Step 1: AI news collection
Sources: Hacker News (public API) + RSS feeds from official blogs
(OpenAI, Anthropic, Google DeepMind)

Goal: gather the most recent/relevant AI items from the last 24-48h,
without duplicates, in a structured format (JSON) to feed the next step
(relevance filtering + podcast script generation).
"""

import json
from datetime import UTC, datetime, timedelta

import feedparser
import requests

# Simple keywords to pre-filter what is relevant to AI
# (the next step refines this with an LLM-based filter)
AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "llm",
    "gpt",
    "claude",
    "gemini",
    "openai",
    "anthropic",
    "deepmind",
    "machine learning",
    "neural network",
    "transformer",
    "chatbot",
    "generative ai",
    "agent",
]

RSS_FEEDS = {
    "OpenAI": "https://openai.com/blog/rss.xml",
    "Anthropic": "https://www.anthropic.com/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
}

HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def is_ai_related(text: str) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in AI_KEYWORDS)


def fetch_hn_ai_stories(max_stories_to_check=150, hours_window=48):
    """Fetch Hacker News top stories and keep the AI-related ones."""
    print("Fetching Hacker News stories...")
    resp = requests.get(HN_TOP_STORIES_URL, timeout=10)
    resp.raise_for_status()
    story_ids = resp.json()[:max_stories_to_check]

    cutoff = datetime.now(UTC) - timedelta(hours=hours_window)
    results = []

    for story_id in story_ids:
        try:
            item_resp = requests.get(HN_ITEM_URL.format(story_id), timeout=10)
            item = item_resp.json()
        except (requests.RequestException, ValueError):
            continue

        if not item or item.get("type") != "story":
            continue

        title = item.get("title", "")
        story_time = datetime.fromtimestamp(item.get("time", 0), tz=UTC)

        if story_time < cutoff:
            continue

        if not is_ai_related(title):
            continue

        results.append(
            {
                "source": "Hacker News",
                "title": title,
                "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "published": story_time.isoformat(),
                "score": item.get("score", 0),
                "raw_id": story_id,
            }
        )

    print(f"  -> {len(results)} relevant stories found.")
    return results


def fetch_rss_ai_posts(hours_window=48):
    """Fetch recent posts from the official blogs via RSS."""
    print("Fetching posts from official blogs (RSS)...")
    cutoff = datetime.now(UTC) - timedelta(hours=hours_window)
    results = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"  Warning: failed to read feed from {source_name}: {e}")
            continue

        for entry in feed.entries:
            published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if not published_struct:
                continue

            published_dt = datetime(*published_struct[:6], tzinfo=UTC)
            if published_dt < cutoff:
                continue

            results.append(
                {
                    "source": source_name,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published": published_dt.isoformat(),
                    "score": None,
                    "raw_id": entry.get("id", entry.get("link", "")),
                }
            )

    print(f"  -> {len(results)} blog posts found.")
    return results


def deduplicate(items):
    """Drop simple duplicates by normalized title."""
    seen_titles = set()
    unique = []
    for item in items:
        normalized = item["title"].strip().lower()
        if normalized in seen_titles:
            continue
        seen_titles.add(normalized)
        unique.append(item)
    return unique


def main():
    hn_items = fetch_hn_ai_stories()
    rss_items = fetch_rss_ai_posts()

    all_items = deduplicate(hn_items + rss_items)
    all_items.sort(key=lambda x: x["published"], reverse=True)

    output_path = "news_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"\nFinal total (deduplicated): {len(all_items)} items.")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
