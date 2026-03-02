import requests
from datetime import datetime, timezone

GITHUB_API_BASE = "https://api.github.com"


def fetch_user_profile(username, token=None):
    """Fetch GitHub user profile data."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(f"{GITHUB_API_BASE}/users/{username}", headers=headers)
    resp.raise_for_status()
    data = resp.json()

    return {
        "name": data.get("name"),
        "bio": data.get("bio"),
        "public_repos": data.get("public_repos", 0),
        "followers": data.get("followers", 0),
        "following": data.get("following", 0),
        "blog": data.get("blog"),
        "hireable": data.get("hireable"),
        "created_at": data.get("created_at", ""),
    }


def fetch_recent_events(username, token=None, max_events=10):
    """Fetch and format recent GitHub events."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"{GITHUB_API_BASE}/users/{username}/events",
        headers=headers,
        params={"per_page": 100},
    )
    resp.raise_for_status()

    events = []
    for raw in resp.json():
        formatted = _format_event(raw)
        if formatted:
            events.append(formatted)
            if len(events) >= max_events:
                break
    return events


def _format_event(event):
    """Format a raw GitHub event into a display-friendly dict."""
    etype = event.get("type", "")
    repo = event.get("repo", {}).get("name", "")
    payload = event.get("payload", {})
    created_at = event.get("created_at", "")

    if etype == "PushEvent":
        count = payload.get("size", 0) or len(payload.get("commits", []))
        ref = payload.get("ref", "").split("/")[-1]
        if count > 0:
            desc = f"Pushed {count} commit{'s' if count != 1 else ''} to `{ref}`"
        else:
            desc = f"Pushed to `{ref}`"
        emoji = "\U0001f4cc"
    elif etype == "PullRequestEvent":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        merged = pr.get("merged", False)
        number = pr.get("number", "")
        if action == "closed" and merged:
            desc = f"Merged PR #{number}"
            emoji = "\U0001f50a"
        else:
            desc = f"{action.capitalize()} PR #{number}"
            emoji = "\U0001f500"
    elif etype == "CreateEvent":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref") or ""
        desc = f"Created {ref_type} `{ref}`" if ref else f"Created {ref_type}"
        emoji = "\U0001f331"
    elif etype == "IssuesEvent":
        action = payload.get("action", "")
        number = payload.get("issue", {}).get("number", "")
        desc = f"{action.capitalize()} issue #{number}"
        emoji = "\U0001f41b"
    elif etype == "WatchEvent":
        desc = "Starred"
        emoji = "\u2b50"
    elif etype == "IssueCommentEvent":
        number = payload.get("issue", {}).get("number", "")
        desc = f"Commented on #{number}"
        emoji = "\U0001f4ac"
    elif etype == "ForkEvent":
        desc = "Forked"
        emoji = "\U0001f374"
    else:
        return None

    return {
        "type": etype,
        "repo": repo,
        "description": desc,
        "emoji": emoji,
        "created_at": created_at,
        "time_ago": _time_ago(created_at),
    }


def fetch_user_repos(username, token=None):
    """Fetch all public repos for a user (paginated)."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{GITHUB_API_BASE}/users/{username}/repos",
            headers=headers,
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def compute_top_languages(repos, token=None, max_langs=8):
    """Aggregate language bytes across repos and return sorted list with percentages."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    lang_bytes = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs_url = repo.get("languages_url")
        if not langs_url:
            continue
        try:
            resp = requests.get(langs_url, headers=headers)
            resp.raise_for_status()
            for lang, nbytes in resp.json().items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + nbytes
        except requests.RequestException:
            continue

    total = sum(lang_bytes.values()) or 1
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:max_langs]
    return [
        {"name": name, "percent": round(nbytes / total * 100, 1)}
        for name, nbytes in sorted_langs
    ]


def fetch_repo_details(owner, repo_name, token=None):
    """Fetch single repo metadata for featured project cards."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}", headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return {
        "name": data.get("name", repo_name),
        "full_name": data.get("full_name", f"{owner}/{repo_name}"),
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "url": data.get("html_url", f"https://github.com/{owner}/{repo_name}"),
    }


def _time_ago(iso_timestamp):
    """Convert ISO timestamp to human-readable relative time."""
    if not iso_timestamp:
        return ""
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    months = days // 30
    return f"{months} month{'s' if months != 1 else ''} ago"
