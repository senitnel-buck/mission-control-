# Mission Control Settings
# Edit these to match your local environment

import os
from pathlib import Path

# Base directory (auto-detected)
BASE_DIR = Path(__file__).parent.parent

# User info
USER_NAME = "Jason Buck"
USER_EMAIL = "jason@buckstone.io"
USER_TIMEZONE = "America/New_York"

# Data paths
DATA_DIR = BASE_DIR / "data"
CONTENT_PIPELINE_FILE = DATA_DIR / "content-pipeline.json"
EXPERT_REQUESTS_FILE = DATA_DIR / "expert-network-requests.md"

# API Keys (load from environment or set here)
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Calendar integration (optional)
CALENDAR_ENABLED = False
CALENDAR_TYPE = "google"  # or "outlook"

# LinkedIn profile
LINKEDIN_PROFILE = "https://www.linkedin.com/in/jbux/"

# X (Twitter) handle
X_HANDLE = "@nolimitgains"

# Colors for terminal output
COLORS_ENABLED = True
