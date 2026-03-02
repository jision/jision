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

from fetch_github import (
    fetch_user_profile,
    fetch_recent_events,
    fetch_user_repos,
    compute_top_languages,
    fetch_repo_details,
)
from fetch_medium import fetch_medium_posts
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

    # Fetch repos and compute top languages
    repos = fetch_user_repos(username, token=token)
    top_languages = compute_top_languages(repos, token=token)

    # Enrich featured projects with live API data
    featured_projects = []
    for project in config.get("featured_projects", []):
        owner = project.get("owner", username)
        name = project.get("name", "")
        try:
            details = fetch_repo_details(owner, name, token=token)
            details["tech"] = project.get("tech", details.get("language", ""))
            featured_projects.append(details)
        except Exception:
            # Fallback to config data if API call fails
            featured_projects.append({
                "name": name,
                "full_name": f"{owner}/{name}",
                "description": project.get("description", ""),
                "language": project.get("tech", ""),
                "tech": project.get("tech", ""),
                "stars": 0,
                "forks": 0,
                "url": f"https://github.com/{owner}/{name}",
            })

    # LinkedIn data from config
    linkedin = config.get("linkedin", {})

    # Build template context
    context = {
        "username": username,
        "profile": profile,
        "config": config,
        "events": events,
        "medium_posts": medium_posts,
        "top_languages": top_languages,
        "featured_projects": featured_projects,
        "linkedin": linkedin,
        "updated_at": datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC"),
    }

    # Render and write
    readme_content = render_readme(context)
    write_readme(readme_content)

    print(f"README.md updated at {context['updated_at']}")
    print(f"  Profile:    {profile.get('name', 'N/A')}")
    print(f"  Events:     {len(events)}")
    print(f"  Medium:     {len(medium_posts)}")
    print(f"  Languages:  {len(top_languages)}")
    print(f"  Projects:   {len(featured_projects)}")


if __name__ == "__main__":
    main()
