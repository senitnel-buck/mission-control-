#!/usr/bin/env python3
"""
🎯 MISSION CONTROL DASHBOARD v2.1
A unified command center for Jason Buck

Integrates:
- Outlook Calendar & Email
- Expert Network Tracking (GLG, GuidePoint, ThirdBridge)
- Nansen Crypto Analytics (Smart Money, Token God Mode)
- Multi-LLM APIs (OpenAI, Anthropic, Grok, Gemini)
- Economic Data (FRED, World Bank)
- Content Pipeline (X + LinkedIn tracking)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# Add scripts to path for content_pipeline import
sys.path.insert(0, "/root/clawd/scripts")

try:
    import requests
except ImportError:
    os.system("pip3 install requests -q")
    import requests

# Configuration
TOKENS_FILE = "/root/clawd/outlook_tokens.json"
EXPERT_REQUESTS_FILE = "/root/clawd/data/expert_requests.json"
CONTENT_PIPELINE_FILE = "/root/clawd/data/content-pipeline.json"
NANSEN_API_KEY = os.environ.get("NANSEN_API_KEY", "")
NANSEN_BASE_URL = "https://api.nansen.ai"

# Email categorization keywords
CATEGORIES = {
    "expert_networks": ["glg", "guidepoint", "guidepointglobal", "thirdbridge", "alphasights"],
    "healthcare": ["fierce", "healthcare", "payer", "cms", "medicaid", "medicare", "hospital"],
    "investment": ["deal", "investment", "portfolio", "fund", "capital", "venture"],
    "procurement": ["procurement", "supply chain", "vendor", "rfp", "sourcing"]
}

# API Registry
APIS = {
    "OpenAI": {"env": "OPENAI_API_KEY", "purpose": "Codex CLI, GPT Models"},
    "Anthropic": {"env": "ANTHROPIC_API_KEY", "purpose": "Claude Models"},
    "Grok": {"env": "GROK_API_KEY", "purpose": "xAI Grok Models"},
    "Gemini": {"env": "GEMINI_API_KEY", "purpose": "Google AI"},
    "Brave": {"env": "BRAVE_API_KEY", "purpose": "Web Search"},
    "Nansen": {"env": "NANSEN_API_KEY", "purpose": "Crypto Analytics"},
    "FRED": {"env": "FRED_API_KEY", "purpose": "Macro Economics", "optional": True},
    "World Bank": {"env": None, "purpose": "Global Indicators", "always_on": True},
}

# Colors for terminal (ANSI)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.ENDC}\n")

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}▸ {title}{Colors.ENDC}")
    print(f"{Colors.YELLOW}{'─' * 50}{Colors.ENDC}")

def load_tokens() -> Optional[dict]:
    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None

def load_expert_requests() -> list:
    try:
        os.makedirs(os.path.dirname(EXPERT_REQUESTS_FILE), exist_ok=True)
        if os.path.exists(EXPERT_REQUESTS_FILE):
            with open(EXPERT_REQUESTS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_expert_requests(requests_list: list):
    os.makedirs(os.path.dirname(EXPERT_REQUESTS_FILE), exist_ok=True)
    with open(EXPERT_REQUESTS_FILE, "w") as f:
        json.dump(requests_list, f, indent=2)

def load_content_pipeline() -> dict:
    """Load content pipeline data."""
    try:
        os.makedirs(os.path.dirname(CONTENT_PIPELINE_FILE), exist_ok=True)
        if os.path.exists(CONTENT_PIPELINE_FILE):
            with open(CONTENT_PIPELINE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"items": [], "lastUpdated": None}

def save_content_pipeline(data: dict):
    """Save content pipeline data."""
    data["lastUpdated"] = datetime.utcnow().isoformat()
    os.makedirs(os.path.dirname(CONTENT_PIPELINE_FILE), exist_ok=True)
    with open(CONTENT_PIPELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_pipeline_stats() -> dict:
    """Get content pipeline statistics."""
    data = load_content_pipeline()
    stats = {
        "total": len(data["items"]),
        "x": {"idea": 0, "drafted": 0, "scheduled": 0, "posted": 0},
        "linkedin": {"idea": 0, "drafted": 0, "scheduled": 0, "posted": 0},
        "scheduled_items": [],
        "recent_ideas": []
    }
    
    for item in data["items"]:
        platform = item.get("platform", "x")
        status = item.get("status", "idea")
        if platform in stats and status in stats[platform]:
            stats[platform][status] += 1
        
        # Collect scheduled items
        if status == "scheduled" and item.get("scheduledFor"):
            stats["scheduled_items"].append(item)
        
        # Collect recent ideas (last 7 days)
        if status == "idea":
            try:
                created = datetime.strptime(item.get("created", ""), "%Y-%m-%d")
                if (datetime.utcnow() - created).days <= 7:
                    stats["recent_ideas"].append(item)
            except:
                stats["recent_ideas"].append(item)
    
    # Sort scheduled by date
    stats["scheduled_items"].sort(key=lambda x: x.get("scheduledFor", ""))
    
    return stats

def check_api_status() -> Dict[str, bool]:
    """Check which APIs are configured."""
    status = {}
    for name, config in APIS.items():
        if config.get("always_on"):
            status[name] = True
        elif config.get("env"):
            status[name] = bool(os.environ.get(config["env"]))
        else:
            status[name] = config.get("optional", False)
    return status

def get_nansen_smart_money() -> Optional[dict]:
    """Fetch Smart Money data from Nansen API."""
    if not NANSEN_API_KEY:
        return None
    try:
        headers = {
            "Authorization": f"Bearer {NANSEN_API_KEY}",
            "Content-Type": "application/json"
        }
        # Get Smart Money token flows
        url = f"{NANSEN_BASE_URL}/smart-money/token-flows"
        response = requests.post(url, headers=headers, json={"chain": "ethereum", "limit": 5}, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def get_nansen_top_tokens() -> Optional[list]:
    """Fetch top tokens from Nansen Token God Mode."""
    if not NANSEN_API_KEY:
        return None
    try:
        headers = {
            "Authorization": f"Bearer {NANSEN_API_KEY}",
            "Content-Type": "application/json"
        }
        url = f"{NANSEN_BASE_URL}/token-god-mode/tokens"
        response = requests.post(url, headers=headers, json={"chain": "all", "limit": 5}, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception:
        pass
    return None

def get_calendar_events(tokens: Optional[dict]) -> list:
    """Fetch today's calendar events from Outlook."""
    if not tokens:
        return []
    try:
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        today = datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
        url = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={today}&endDateTime={tomorrow}&$top=10&$select=subject,start,end,location"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("value", [])
    except Exception:
        pass
    return []

def get_unread_emails(tokens: Optional[dict]) -> list:
    """Fetch unread emails from Outlook."""
    if not tokens:
        return []
    try:
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        url = "https://graph.microsoft.com/v1.0/me/messages?$filter=isRead eq false&$top=20&$select=id,subject,from,receivedDateTime,importance,bodyPreview"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("value", [])
    except Exception:
        pass
    return []

def categorize_email(email: dict) -> str:
    """Categorize an email based on sender and subject."""
    sender = email.get("from", {}).get("emailAddress", {}).get("address", "").lower()
    subject = email.get("subject", "").lower()
    combined = f"{sender} {subject}"
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in combined:
                return category
    return "general"

def display_daily_briefing(tokens: Optional[dict]):
    """Display the daily briefing section."""
    print_header("🎯 MISSION CONTROL DASHBOARD v2.1")
    
    now = datetime.utcnow()
    est_time = now + timedelta(hours=-5)
    
    print(f"  📅 {Colors.BOLD}{est_time.strftime('%A, %B %d, %Y')}{Colors.ENDC}")
    print(f"  🕐 {est_time.strftime('%I:%M %p')} EST")
    print(f"  👤 Jason Buck | jason@buckstone.io")
    
    if not tokens:
        print(f"\n  {Colors.YELLOW}⚠ Outlook not connected - run OAuth setup{Colors.ENDC}")

def display_api_status():
    """Display status of all configured APIs."""
    print_section("🔌 API STATUS")
    
    status = check_api_status()
    
    col1 = []
    col2 = []
    
    for i, (name, is_active) in enumerate(status.items()):
        purpose = APIS[name]["purpose"]
        if is_active:
            entry = f"{Colors.GREEN}✅{Colors.ENDC} {name}: {Colors.DIM}{purpose}{Colors.ENDC}"
        else:
            entry = f"{Colors.RED}❌{Colors.ENDC} {name}: {Colors.DIM}{purpose}{Colors.ENDC}"
        
        if i % 2 == 0:
            col1.append(entry)
        else:
            col2.append(entry)
    
    # Print in two columns
    for i in range(max(len(col1), len(col2))):
        left = col1[i] if i < len(col1) else ""
        right = col2[i] if i < len(col2) else ""
        print(f"  {left:<45} {right}")
    
    active_count = sum(1 for v in status.values() if v)
    print(f"\n  {Colors.BOLD}Total: {active_count}/{len(status)} APIs Active{Colors.ENDC}")

def display_crypto_signals():
    """Display Nansen crypto analytics."""
    print_section("🪙 CRYPTO SIGNALS (Nansen)")
    
    if not NANSEN_API_KEY:
        print(f"  {Colors.YELLOW}⚠ Nansen API key not configured{Colors.ENDC}")
        return
    
    print(f"  {Colors.CYAN}📊 Smart Money Analytics:{Colors.ENDC}")
    
    # Try to fetch data
    smart_money = get_nansen_smart_money()
    if smart_money and smart_money.get("data"):
        for token in smart_money["data"][:3]:
            symbol = token.get("symbol", "???")
            net_flow = token.get("net_flow", 0)
            direction = "🟢" if net_flow > 0 else "🔴"
            print(f"     {direction} {symbol}: ${abs(net_flow):,.0f} {'inflow' if net_flow > 0 else 'outflow'}")
    else:
        print(f"     {Colors.DIM}Fetching live data...{Colors.ENDC}")
        print(f"     {Colors.DIM}• Smart Money Token Flows{Colors.ENDC}")
        print(f"     {Colors.DIM}• Top Wallet Movements{Colors.ENDC}")
        print(f"     {Colors.DIM}• Exchange Inflows/Outflows{Colors.ENDC}")
    
    print(f"\n  {Colors.CYAN}🎯 Available Endpoints:{Colors.ENDC}")
    print(f"     • Smart Money Wallets & Holdings")
    print(f"     • Token God Mode Analytics")
    print(f"     • Wallet Profiler & PnL")
    print(f"     • DEX Trade Tracking")

def display_calendar(tokens: Optional[dict]):
    """Display today's calendar events."""
    print_section("📅 TODAY'S CALENDAR")
    
    if not tokens:
        print(f"  {Colors.YELLOW}⚠ Connect Outlook to see calendar{Colors.ENDC}")
        return
    
    events = get_calendar_events(tokens)
    if not events:
        print(f"  {Colors.GREEN}No events scheduled for today{Colors.ENDC}")
        return
    
    for event in events:
        subject = event.get("subject", "No Title")
        start = event.get("start", {}).get("dateTime", "")[:16]
        if start:
            try:
                dt = datetime.fromisoformat(start.replace("Z", ""))
                time_str = dt.strftime("%I:%M %p")
            except:
                time_str = start
        else:
            time_str = "TBD"
        print(f"  {Colors.CYAN}⏰ {time_str}{Colors.ENDC} - {subject}")

def display_email_triage(tokens: Optional[dict]):
    """Display email triage section."""
    print_section("📧 EMAIL TRIAGE")
    
    if not tokens:
        print(f"  {Colors.YELLOW}⚠ Connect Outlook to see emails{Colors.ENDC}")
        return
    
    emails = get_unread_emails(tokens)
    by_category = {"expert_networks": [], "healthcare": [], "investment": [], "procurement": [], "general": []}
    urgent = []
    
    for email in emails:
        category = categorize_email(email)
        by_category[category].append(email)
        if email.get("importance") == "high":
            urgent.append(email)
    
    print(f"  📊 {Colors.BOLD}Unread Summary:{Colors.ENDC}")
    print(f"     Expert Networks: {Colors.CYAN}{len(by_category['expert_networks'])}{Colors.ENDC}")
    print(f"     Healthcare:      {Colors.GREEN}{len(by_category['healthcare'])}{Colors.ENDC}")
    print(f"     Investment:      {Colors.YELLOW}{len(by_category['investment'])}{Colors.ENDC}")
    print(f"     Procurement:     {Colors.BLUE}{len(by_category['procurement'])}{Colors.ENDC}")
    print(f"     General:         {len(by_category['general'])}")
    
    if urgent:
        print(f"\n  🔴 {Colors.RED}{Colors.BOLD}URGENT ({len(urgent)}):{Colors.ENDC}")
        for email in urgent[:3]:
            sender = email.get("from", {}).get("emailAddress", {}).get("name", "Unknown")
            subject = email.get("subject", "No Subject")[:40]
            print(f"     • {sender}: {subject}")
    
    actionable = by_category["expert_networks"][:3] + by_category["investment"][:2]
    if actionable:
        print(f"\n  ⚡ {Colors.BOLD}Top Actionable:{Colors.ENDC}")
        for email in actionable[:5]:
            sender = email.get("from", {}).get("emailAddress", {}).get("name", "Unknown")
            subject = email.get("subject", "No Subject")[:45]
            print(f"     • {Colors.CYAN}{sender}{Colors.ENDC}: {subject}")

def display_expert_tracker():
    """Display expert network tracker."""
    print_section("🎓 EXPERT NETWORK TRACKER")
    
    requests_list = load_expert_requests()
    pending = [r for r in requests_list if r.get("status") == "pending"]
    scheduled = [r for r in requests_list if r.get("status") == "scheduled"]
    total_revenue = sum(r.get("rate", 0) for r in pending + scheduled)
    
    print(f"  💰 {Colors.BOLD}Potential Revenue:{Colors.ENDC} {Colors.GREEN}${total_revenue:,.0f}{Colors.ENDC}")
    print(f"  📋 Pending Requests: {len(pending)}")
    print(f"  📞 Scheduled Calls:  {len(scheduled)}")
    
    if pending:
        print(f"\n  {Colors.YELLOW}Pending Requests:{Colors.ENDC}")
        for req in pending[:3]:
            network = req.get("network", "Unknown")
            topic = req.get("topic", "N/A")[:35]
            rate = req.get("rate", 0)
            print(f"     • [{network}] {topic} (${rate})")
    
    if scheduled:
        print(f"\n  {Colors.GREEN}Upcoming Calls:{Colors.ENDC}")
        for req in scheduled[:3]:
            network = req.get("network", "Unknown")
            topic = req.get("topic", "N/A")[:30]
            date = req.get("scheduled_date", "TBD")
            print(f"     • [{network}] {topic} - {date}")

def display_content_pipeline():
    """Display content pipeline summary."""
    print_section("📝 CONTENT PIPELINE")
    
    stats = get_pipeline_stats()
    
    # Summary by platform and status
    print(f"  {Colors.BOLD}𝕏 X:{Colors.ENDC}")
    print(f"     💡 Ideas: {stats['x']['idea']}  📝 Drafted: {stats['x']['drafted']}  📅 Scheduled: {stats['x']['scheduled']}  ✅ Posted: {stats['x']['posted']}")
    
    print(f"\n  {Colors.BOLD}💼 LinkedIn:{Colors.ENDC}")
    print(f"     💡 Ideas: {stats['linkedin']['idea']}  📝 Drafted: {stats['linkedin']['drafted']}  📅 Scheduled: {stats['linkedin']['scheduled']}  ✅ Posted: {stats['linkedin']['posted']}")
    
    # Upcoming scheduled posts
    if stats["scheduled_items"]:
        print(f"\n  {Colors.CYAN}📅 Upcoming Scheduled:{Colors.ENDC}")
        for item in stats["scheduled_items"][:3]:
            plat = "𝕏" if item["platform"] == "x" else "💼"
            title = item.get("title", "Untitled")[:35]
            scheduled = item.get("scheduledFor", "TBD")
            print(f"     {plat} {scheduled} - {title}")
    
    # Recent ideas needing attention
    if stats["recent_ideas"]:
        print(f"\n  {Colors.YELLOW}💡 Recent Ideas:{Colors.ENDC}")
        for item in stats["recent_ideas"][:3]:
            plat = "𝕏" if item["platform"] == "x" else "💼"
            title = item.get("title", "Untitled")[:40]
            ctype = item.get("type", "")
            print(f"     {plat} [{ctype}] {title}")

def view_full_pipeline():
    """Display detailed content pipeline view."""
    print_section("📋 FULL CONTENT PIPELINE")
    
    data = load_content_pipeline()
    items = data.get("items", [])
    
    if not items:
        print(f"  {Colors.YELLOW}No content in pipeline{Colors.ENDC}")
        return
    
    # Group by status
    by_status = {"idea": [], "drafted": [], "scheduled": [], "posted": []}
    for item in items:
        status = item.get("status", "idea")
        if status in by_status:
            by_status[status].append(item)
    
    status_emoji = {"idea": "💡", "drafted": "📝", "scheduled": "📅", "posted": "✅"}
    
    for status in ["scheduled", "drafted", "idea", "posted"]:
        status_items = by_status[status]
        if status_items:
            print(f"\n  {Colors.BOLD}{status_emoji[status]} {status.upper()} ({len(status_items)}){Colors.ENDC}")
            for item in status_items[:5]:
                plat = "𝕏" if item["platform"] == "x" else "💼"
                title = item.get("title", "Untitled")[:35]
                item_id = item.get("id", "???")
                extra = ""
                if item.get("scheduledFor"):
                    extra = f" | {item['scheduledFor']}"
                elif item.get("postedAt"):
                    extra = f" | Posted {item['postedAt'][:10]}"
                print(f"     [{item_id}] {plat} {title}{extra}")
            if len(status_items) > 5:
                print(f"     ... and {len(status_items) - 5} more")

def add_content_idea():
    """Interactive prompt to add a new content idea."""
    print_section("➕ ADD CONTENT IDEA")
    
    # Import the helper
    try:
        from content_pipeline import add_item, PLATFORMS, TYPES
    except ImportError:
        print(f"  {Colors.RED}Error: content_pipeline.py not found{Colors.ENDC}")
        return
    
    print("  Platforms: x, linkedin")
    platform = input("  Platform: ").strip().lower()
    if platform not in PLATFORMS:
        print(f"  {Colors.RED}Invalid platform{Colors.ENDC}")
        return
    
    print(f"\n  Types: {', '.join(TYPES)}")
    content_type = input("  Type: ").strip().lower()
    if content_type not in TYPES:
        print(f"  {Colors.RED}Invalid type{Colors.ENDC}")
        return
    
    title = input("  Title (short description): ").strip()
    if not title:
        print(f"  {Colors.RED}Title required{Colors.ENDC}")
        return
    
    print("  Content (multi-line, enter empty line to finish):")
    lines = []
    while True:
        line = input("  > ")
        if line == "":
            break
        lines.append(line)
    content = "\n".join(lines)
    
    if not content:
        print(f"  {Colors.RED}Content required{Colors.ENDC}")
        return
    
    item = add_item(platform, content_type, title, content)
    print(f"\n  {Colors.GREEN}✓ Added: {item['id']}{Colors.ENDC}")
    print(f"    Platform: {item['platform']}")
    print(f"    Type: {item['type']}")
    print(f"    Title: {item['title']}")

def update_content_status():
    """Interactive prompt to update content status."""
    print_section("✏️ UPDATE CONTENT STATUS")
    
    try:
        from content_pipeline import update_status, set_posted, get_pending, STATUSES
    except ImportError:
        print(f"  {Colors.RED}Error: content_pipeline.py not found{Colors.ENDC}")
        return
    
    pending = get_pending()
    
    if not pending:
        print(f"  {Colors.YELLOW}No pending content to update{Colors.ENDC}")
        return
    
    print("  Pending Content:")
    for i, item in enumerate(pending, 1):
        plat = "𝕏" if item["platform"] == "x" else "💼"
        print(f"    [{i}] {plat} [{item['status']}] {item['title'][:35]} ({item['id']})")
    
    choice = input("\n  Enter number to update (or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pending):
            item = pending[idx]
            item_id = item.get("id")
            
            print(f"\n  Current status: {item['status']}")
            print(f"  Available: {', '.join(STATUSES)}")
            new_status = input("  New status: ").strip().lower()
            
            if new_status == "posted":
                post_url = input("  Post URL: ").strip()
                if post_url:
                    set_posted(item_id, post_url)
                    print(f"\n  {Colors.GREEN}✓ Marked as posted!{Colors.ENDC}")
                else:
                    print(f"  {Colors.RED}URL required for posted status{Colors.ENDC}")
            elif new_status in STATUSES:
                scheduled_for = None
                if new_status == "scheduled":
                    scheduled_for = input("  Scheduled for (YYYY-MM-DD HH:MM): ").strip()
                update_status(item_id, new_status, scheduled_for)
                print(f"\n  {Colors.GREEN}✓ Status updated to {new_status}!{Colors.ENDC}")
            else:
                print(f"  {Colors.RED}Invalid status{Colors.ENDC}")
        else:
            print(f"  {Colors.RED}Invalid selection{Colors.ENDC}")
    except ValueError:
        print(f"  {Colors.RED}Invalid input{Colors.ENDC}")

def display_menu():
    """Display the quick actions menu."""
    print(f"\n{Colors.BOLD}{'─' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}  QUICK ACTIONS{Colors.ENDC}")
    print(f"{'─' * 70}")
    print(f"  [1] 🔄 Refresh Dashboard        [5] 📝 Generate Discord Summary")
    print(f"  [2] ➕ Add Expert Request       [6] 📋 View Content Pipeline")
    print(f"  [3] ✅ Mark Request Complete    [7] ➕ Add Content Idea")
    print(f"  [4] 📅 View Full Calendar       [8] ✏️  Update Content Status")
    print(f"  [9] 🪙 Fetch Nansen Data        [q] 🚪 Quit")
    print(f"{'─' * 70}")

def add_expert_request():
    """Interactive prompt to add a new expert network request."""
    print_section("➕ ADD EXPERT NETWORK REQUEST")
    requests_list = load_expert_requests()
    
    network = input("  Network (GLG/GuidePoint/ThirdBridge): ").strip()
    topic = input("  Topic: ").strip()
    rate = input("  Hourly Rate ($): ").strip()
    deadline = input("  Response Deadline (YYYY-MM-DD): ").strip()
    
    try:
        rate = float(rate)
    except:
        rate = 0
    
    new_request = {
        "id": len(requests_list) + 1,
        "network": network,
        "topic": topic,
        "rate": rate,
        "deadline": deadline,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    requests_list.append(new_request)
    save_expert_requests(requests_list)
    print(f"\n  {Colors.GREEN}✓ Request added successfully!{Colors.ENDC}")

def mark_request_complete():
    """Mark an expert network request as complete."""
    print_section("✅ MARK REQUEST COMPLETE")
    requests_list = load_expert_requests()
    pending = [r for r in requests_list if r.get("status") in ["pending", "scheduled"]]
    
    if not pending:
        print(f"  {Colors.YELLOW}No pending requests to complete.{Colors.ENDC}")
        return
    
    print("  Pending/Scheduled Requests:")
    for i, req in enumerate(pending, 1):
        print(f"    [{i}] {req.get('network')} - {req.get('topic')[:30]}")
    
    choice = input("\n  Enter number to complete (or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pending):
            req_id = pending[idx].get("id")
            for req in requests_list:
                if req.get("id") == req_id:
                    req["status"] = "completed"
                    req["completed_at"] = datetime.utcnow().isoformat()
            save_expert_requests(requests_list)
            print(f"\n  {Colors.GREEN}✓ Request marked as complete!{Colors.ENDC}")
    except:
        print(f"  {Colors.RED}Invalid selection.{Colors.ENDC}")

def fetch_nansen_detailed():
    """Fetch and display detailed Nansen data."""
    print_section("🪙 NANSEN DETAILED DATA")
    
    if not NANSEN_API_KEY:
        print(f"  {Colors.RED}Nansen API key not configured{Colors.ENDC}")
        return
    
    print(f"  Fetching Smart Money data...")
    
    try:
        headers = {
            "Authorization": f"Bearer {NANSEN_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Try Smart Money endpoint
        url = f"{NANSEN_BASE_URL}/smart-money/tokens"
        response = requests.post(url, headers=headers, json={"chain": "ethereum", "limit": 10}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n  {Colors.GREEN}✓ Data retrieved successfully!{Colors.ENDC}")
            print(f"\n  {Colors.BOLD}Smart Money Top Tokens:{Colors.ENDC}")
            for token in data.get("data", [])[:5]:
                print(f"     • {token}")
        else:
            print(f"  {Colors.YELLOW}API returned status {response.status_code}{Colors.ENDC}")
            print(f"  {Colors.DIM}Response: {response.text[:200]}{Colors.ENDC}")
    except Exception as e:
        print(f"  {Colors.RED}Error: {e}{Colors.ENDC}")

def generate_discord_summary(tokens: Optional[dict]) -> str:
    """Generate a summary for Discord."""
    print_section("📝 DISCORD SUMMARY")
    
    now = datetime.utcnow()
    est_time = now + timedelta(hours=-5)
    
    email_count = 0
    expert_count = 0
    if tokens:
        emails = get_unread_emails(tokens)
        email_count = len(emails)
        expert_count = len([e for e in emails if categorize_email(e) == "expert_networks"])
    
    requests_list = load_expert_requests()
    pending = [r for r in requests_list if r.get("status") == "pending"]
    revenue = sum(r.get("rate", 0) for r in pending)
    
    events = get_calendar_events(tokens) if tokens else []
    
    api_status = check_api_status()
    active_apis = sum(1 for v in api_status.values() if v)
    
    summary = f"""📊 **Mission Control - {est_time.strftime('%B %d, %Y')}**

📧 **Email**
• {email_count} unread ({expert_count} from expert networks)

🎓 **Expert Networks**
• {len(pending)} pending requests (${revenue:,.0f} potential)

📅 **Today**
• {len(events)} calendar events

🔌 **Systems**
• {active_apis}/{len(api_status)} APIs active

---
_Generated by Mission Control v2.1_"""
    
    print(summary)
    print(f"\n  {Colors.GREEN}✓ Summary generated!{Colors.ENDC}")
    return summary

def main():
    """Main dashboard loop."""
    tokens = load_tokens()
    
    while True:
        clear_screen()
        display_daily_briefing(tokens)
        display_api_status()
        display_content_pipeline()
        display_crypto_signals()
        display_calendar(tokens)
        display_email_triage(tokens)
        display_expert_tracker()
        display_menu()
        
        choice = input(f"\n  {Colors.BOLD}Select action:{Colors.ENDC} ").strip().lower()
        
        if choice == '1':
            tokens = load_tokens()
            continue
        elif choice == '2':
            add_expert_request()
            input("\n  Press Enter to continue...")
        elif choice == '3':
            mark_request_complete()
            input("\n  Press Enter to continue...")
        elif choice == '4':
            print_section("📅 FULL CALENDAR (Next 7 Days)")
            if tokens:
                try:
                    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                    today = datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")
                    week_later = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
                    url = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={today}&endDateTime={week_later}&$top=30&$select=subject,start,end"
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        events = response.json().get("value", [])
                        for event in events:
                            start = event.get("start", {}).get("dateTime", "")[:16]
                            subject = event.get("subject", "No Title")
                            print(f"  {start} - {subject}")
                except Exception as e:
                    print(f"  Error: {e}")
            else:
                print(f"  {Colors.YELLOW}⚠ Connect Outlook to view calendar{Colors.ENDC}")
            input("\n  Press Enter to continue...")
        elif choice == '5':
            generate_discord_summary(tokens)
            input("\n  Press Enter to continue...")
        elif choice == '6':
            view_full_pipeline()
            input("\n  Press Enter to continue...")
        elif choice == '7':
            add_content_idea()
            input("\n  Press Enter to continue...")
        elif choice == '8':
            update_content_status()
            input("\n  Press Enter to continue...")
        elif choice == '9':
            fetch_nansen_detailed()
            input("\n  Press Enter to continue...")
        elif choice == 'q':
            print(f"\n  {Colors.CYAN}👋 Goodbye!{Colors.ENDC}\n")
            break
        else:
            continue

if __name__ == "__main__":
    main()
