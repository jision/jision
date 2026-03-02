#!/usr/bin/env python3
"""
Main entry point. Fetches all data sources, renders the README template,
and writes the output.

Usage:
    python scripts/update_readme.py

Environment variables:
    GITHUB_TOKEN    (optional) - GitHub PAT for higher rate limits
    GITHUB_USERNAME (optional) - defaults to 'jision'
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_github import fetch_user_profile, fetch_recent_events
from fetch_medium import fetch_medium_posts
from fetch_linkedin import fetch_linkedin_posts
from render import render_readme, write_readme


def load_config():
    """Load personal config from config.json."""
    config_path = Path(__file__).resolve().parent.parent / "config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "tagline": "",
        "current_focus": "",
        "thoughts": [],
        "fun_facts": [],
        "skills": {},
        "social": {},
    }


def main():
    username = os.environ.get("GITHUB_USERNAME", "jision")
    token = os.environ.get("GITHUB_TOKEN")
    config = load_config()

    # Fetch all data sources
    profile = fetch_user_profile(username, token=token)
    events = fetch_recent_events(username, token=token, max_events=10)
    medium_posts = fetch_medium_posts(config.get("social", {}).get("medium"))
    linkedin_posts = fetch_linkedin_posts()

    # Build template context
    context = {
        "username": username,
        "profile": profile,
        "config": config,
        "events": events,
        "medium_posts": medium_posts,
        "linkedin_posts": linkedin_posts,
        "updated_at": datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC"),
    }

    # Render and write
    readme_content = render_readme(context)
    write_readme(readme_content)

    print(f"README.md updated at {context['updated_at']}")
    print(f"  Profile:  {profile.get('name', 'N/A')}")
    print(f"  Events:   {len(events)}")
    print(f"  Medium:   {len(medium_posts)}")
    print(f"  LinkedIn: {len(linkedin_posts)}")


if __name__ == "__main__":
    main()
