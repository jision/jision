"""
Medium blog post fetcher.

To activate: add `feedparser>=6.0.0,<7.0.0` to requirements.txt,
then implement the function below.
"""


def fetch_medium_posts(username=None, max_posts=5):
    """
    Fetch latest posts from Medium RSS feed.

    When implemented, parses: https://medium.com/feed/@{username}
    Returns list of dicts: [{"title", "url", "date", "summary"}, ...]
    """
    if not username:
        return []

    try:
        import feedparser
    except ImportError:
        return []

    feed = feedparser.parse(f"https://medium.com/feed/@{username}")
    posts = []
    for entry in feed.entries[:max_posts]:
        # Strip HTML tags from summary
        summary = entry.get("summary", "")
        import re
        summary = re.sub(r"<[^>]+>", "", summary)[:150].strip()
        if summary:
            summary += "..."

        posts.append({
            "title": entry.get("title", "Untitled"),
            "url": entry.get("link", ""),
            "date": entry.get("published", ""),
            "summary": summary,
        })
    return posts
