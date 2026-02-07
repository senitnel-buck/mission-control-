#!/usr/bin/env python3
"""
📝 Content Pipeline Helper
Manage LinkedIn and X content from idea → posted

Usage:
    python content_pipeline.py add x macro-take "Title" "Content here"
    python content_pipeline.py status <id> drafted
    python content_pipeline.py posted <id> "https://x.com/..."
    python content_pipeline.py list [platform] [status]
    python content_pipeline.py pending [platform]
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict

PIPELINE_FILE = "/root/clawd/data/content-pipeline.json"

# Valid values
PLATFORMS = ["x", "linkedin"]
TYPES = ["macro-take", "crypto-insight", "meme", "one-liner", "carousel", "pov", "tactical", "thread"]
STATUSES = ["idea", "drafted", "scheduled", "posted"]


def load_pipeline() -> dict:
    """Load the pipeline JSON file."""
    try:
        os.makedirs(os.path.dirname(PIPELINE_FILE), exist_ok=True)
        if os.path.exists(PIPELINE_FILE):
            with open(PIPELINE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading pipeline: {e}")
    return {"items": [], "lastUpdated": datetime.utcnow().isoformat()}


def save_pipeline(data: dict):
    """Save the pipeline JSON file."""
    data["lastUpdated"] = datetime.utcnow().isoformat()
    os.makedirs(os.path.dirname(PIPELINE_FILE), exist_ok=True)
    with open(PIPELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_id(platform: str) -> str:
    """Generate a new ID for a content item."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    prefix = "x" if platform == "x" else "li"
    
    data = load_pipeline()
    existing = [item["id"] for item in data["items"] if item["id"].startswith(f"{prefix}-{today}")]
    
    counter = 1
    while f"{prefix}-{today}-{counter:03d}" in existing:
        counter += 1
    
    return f"{prefix}-{today}-{counter:03d}"


def add_item(platform: str, content_type: str, title: str, content: str, scheduled_for: Optional[str] = None) -> dict:
    """
    Add a new content item to the pipeline.
    
    Args:
        platform: 'x' or 'linkedin'
        content_type: macro-take, crypto-insight, meme, one-liner, carousel, pov, tactical, thread
        title: Short description
        content: Full post content
        scheduled_for: Optional datetime string (e.g., "2026-02-08 09:00")
    
    Returns:
        The created item dict
    """
    if platform not in PLATFORMS:
        raise ValueError(f"Platform must be one of: {PLATFORMS}")
    if content_type not in TYPES:
        raise ValueError(f"Type must be one of: {TYPES}")
    
    data = load_pipeline()
    
    item = {
        "id": generate_id(platform),
        "platform": platform,
        "type": content_type,
        "status": "idea",
        "title": title,
        "content": content,
        "created": datetime.utcnow().strftime("%Y-%m-%d"),
        "scheduledFor": scheduled_for,
        "postedAt": None,
        "postUrl": None,
        "metrics": {"impressions": None, "engagement": None, "followers": None}
    }
    
    data["items"].append(item)
    save_pipeline(data)
    
    return item


def update_status(item_id: str, new_status: str, scheduled_for: Optional[str] = None) -> Optional[dict]:
    """
    Update the status of a content item.
    
    Args:
        item_id: The ID of the item to update
        new_status: idea, drafted, scheduled, or posted
        scheduled_for: Optional scheduled datetime (required if status is 'scheduled')
    
    Returns:
        The updated item, or None if not found
    """
    if new_status not in STATUSES:
        raise ValueError(f"Status must be one of: {STATUSES}")
    
    data = load_pipeline()
    
    for item in data["items"]:
        if item["id"] == item_id:
            item["status"] = new_status
            if scheduled_for:
                item["scheduledFor"] = scheduled_for
            save_pipeline(data)
            return item
    
    return None


def set_posted(item_id: str, post_url: str) -> Optional[dict]:
    """
    Mark an item as posted with its URL.
    
    Args:
        item_id: The ID of the item
        post_url: The URL of the published post
    
    Returns:
        The updated item, or None if not found
    """
    data = load_pipeline()
    
    for item in data["items"]:
        if item["id"] == item_id:
            item["status"] = "posted"
            item["postUrl"] = post_url
            item["postedAt"] = datetime.utcnow().isoformat()
            save_pipeline(data)
            return item
    
    return None


def update_metrics(item_id: str, impressions: Optional[int] = None, 
                   engagement: Optional[float] = None, followers: Optional[int] = None) -> Optional[dict]:
    """
    Update metrics for a posted item.
    
    Args:
        item_id: The ID of the item
        impressions: View count
        engagement: Engagement rate (percentage)
        followers: Net followers gained
    
    Returns:
        The updated item, or None if not found
    """
    data = load_pipeline()
    
    for item in data["items"]:
        if item["id"] == item_id:
            if impressions is not None:
                item["metrics"]["impressions"] = impressions
            if engagement is not None:
                item["metrics"]["engagement"] = engagement
            if followers is not None:
                item["metrics"]["followers"] = followers
            save_pipeline(data)
            return item
    
    return None


def get_pending(platform: Optional[str] = None) -> List[dict]:
    """
    Get all items not yet posted.
    
    Args:
        platform: Optional filter by platform ('x' or 'linkedin')
    
    Returns:
        List of pending items
    """
    data = load_pipeline()
    items = [item for item in data["items"] if item["status"] != "posted"]
    
    if platform:
        items = [item for item in items if item["platform"] == platform]
    
    return items


def get_by_status(status: str, platform: Optional[str] = None) -> List[dict]:
    """
    Get all items with a specific status.
    
    Args:
        status: idea, drafted, scheduled, or posted
        platform: Optional filter by platform
    
    Returns:
        List of matching items
    """
    if status not in STATUSES:
        raise ValueError(f"Status must be one of: {STATUSES}")
    
    data = load_pipeline()
    items = [item for item in data["items"] if item["status"] == status]
    
    if platform:
        items = [item for item in items if item["platform"] == platform]
    
    return items


def get_by_id(item_id: str) -> Optional[dict]:
    """Get a single item by ID."""
    data = load_pipeline()
    for item in data["items"]:
        if item["id"] == item_id:
            return item
    return None


def delete_item(item_id: str) -> bool:
    """Delete an item by ID. Returns True if found and deleted."""
    data = load_pipeline()
    original_len = len(data["items"])
    data["items"] = [item for item in data["items"] if item["id"] != item_id]
    
    if len(data["items"]) < original_len:
        save_pipeline(data)
        return True
    return False


def get_stats() -> dict:
    """Get summary statistics for the pipeline."""
    data = load_pipeline()
    
    stats = {
        "total": len(data["items"]),
        "by_platform": {"x": 0, "linkedin": 0},
        "by_status": {"idea": 0, "drafted": 0, "scheduled": 0, "posted": 0},
        "by_platform_status": {
            "x": {"idea": 0, "drafted": 0, "scheduled": 0, "posted": 0},
            "linkedin": {"idea": 0, "drafted": 0, "scheduled": 0, "posted": 0}
        },
        "lastUpdated": data.get("lastUpdated")
    }
    
    for item in data["items"]:
        platform = item["platform"]
        status = item["status"]
        stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        stats["by_platform_status"][platform][status] += 1
    
    return stats


def list_items(platform: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    """List all items, optionally filtered by platform and/or status."""
    data = load_pipeline()
    items = data["items"]
    
    if platform:
        items = [item for item in items if item["platform"] == platform]
    if status:
        items = [item for item in items if item["status"] == status]
    
    return items


def print_item(item: dict, verbose: bool = False):
    """Pretty print a content item."""
    status_emoji = {"idea": "💡", "drafted": "📝", "scheduled": "📅", "posted": "✅"}
    platform_emoji = {"x": "𝕏", "linkedin": "💼"}
    
    emoji = status_emoji.get(item["status"], "❓")
    plat = platform_emoji.get(item["platform"], "?")
    
    print(f"  {emoji} [{item['id']}] {plat} {item['title'][:40]}")
    print(f"     Type: {item['type']} | Status: {item['status']}")
    
    if item.get("scheduledFor"):
        print(f"     Scheduled: {item['scheduledFor']}")
    if item.get("postUrl"):
        print(f"     URL: {item['postUrl']}")
    
    if verbose and item.get("content"):
        content_preview = item["content"][:100].replace("\n", " ")
        print(f"     Content: {content_preview}...")


def cli_main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "add":
        if len(sys.argv) < 6:
            print("Usage: python content_pipeline.py add <platform> <type> <title> <content>")
            return
        platform, ctype, title, content = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        scheduled = sys.argv[6] if len(sys.argv) > 6 else None
        item = add_item(platform, ctype, title, content, scheduled)
        print(f"✅ Added: {item['id']}")
        print_item(item)
    
    elif command == "status":
        if len(sys.argv) < 4:
            print("Usage: python content_pipeline.py status <id> <new_status> [scheduled_for]")
            return
        item_id, new_status = sys.argv[2], sys.argv[3]
        scheduled = sys.argv[4] if len(sys.argv) > 4 else None
        item = update_status(item_id, new_status, scheduled)
        if item:
            print(f"✅ Updated: {item['id']} → {new_status}")
            print_item(item)
        else:
            print(f"❌ Item not found: {item_id}")
    
    elif command == "posted":
        if len(sys.argv) < 4:
            print("Usage: python content_pipeline.py posted <id> <post_url>")
            return
        item_id, post_url = sys.argv[2], sys.argv[3]
        item = set_posted(item_id, post_url)
        if item:
            print(f"✅ Marked as posted: {item['id']}")
            print_item(item)
        else:
            print(f"❌ Item not found: {item_id}")
    
    elif command == "list":
        platform = sys.argv[2] if len(sys.argv) > 2 else None
        status = sys.argv[3] if len(sys.argv) > 3 else None
        items = list_items(platform, status)
        print(f"\n📋 Content Pipeline ({len(items)} items)\n")
        for item in items:
            print_item(item)
            print()
    
    elif command == "pending":
        platform = sys.argv[2] if len(sys.argv) > 2 else None
        items = get_pending(platform)
        print(f"\n⏳ Pending Content ({len(items)} items)\n")
        for item in items:
            print_item(item)
            print()
    
    elif command == "stats":
        stats = get_stats()
        print("\n📊 Content Pipeline Stats\n")
        print(f"  Total items: {stats['total']}")
        print(f"\n  By Platform:")
        print(f"    𝕏  X:        {stats['by_platform']['x']}")
        print(f"    💼 LinkedIn: {stats['by_platform']['linkedin']}")
        print(f"\n  By Status:")
        for status, count in stats['by_status'].items():
            emoji = {"idea": "💡", "drafted": "📝", "scheduled": "📅", "posted": "✅"}[status]
            print(f"    {emoji} {status.capitalize()}: {count}")
        print(f"\n  Last Updated: {stats['lastUpdated']}")
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: python content_pipeline.py delete <id>")
            return
        item_id = sys.argv[2]
        if delete_item(item_id):
            print(f"✅ Deleted: {item_id}")
        else:
            print(f"❌ Item not found: {item_id}")
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: python content_pipeline.py get <id>")
            return
        item_id = sys.argv[2]
        item = get_by_id(item_id)
        if item:
            print_item(item, verbose=True)
            print(f"\n  Full content:\n{item.get('content', 'N/A')}")
        else:
            print(f"❌ Item not found: {item_id}")
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    cli_main()
