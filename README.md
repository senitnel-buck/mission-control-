# 🎯 Mission Control Dashboard

Local standalone version for macOS.

## Quick Start

```bash
# Navigate to the directory
cd mission-control

# Run it
python3 mission_control.py

# Or use the launcher
./run.sh
```

## Setup

1. **Extract/clone** to a location like `~/mission-control`

2. **Edit config** (optional):
   ```bash
   nano config/settings.py
   ```
   - Update USER_NAME, USER_EMAIL
   - Add API keys if needed

3. **Make launcher executable**:
   ```bash
   chmod +x run.sh
   ```

4. **Create alias** (optional) - add to `~/.zshrc`:
   ```bash
   alias mc="python3 ~/mission-control/mission_control.py"
   ```

## Features

- 📅 Calendar view (coming soon: Google/Outlook integration)
- 🎓 Expert Network request tracker
- 📝 Content Pipeline (X + LinkedIn)
- 📈 Investment signals dashboard

## Files

```
mission-control/
├── mission_control.py    # Main app
├── run.sh                # Launcher script
├── config/
│   └── settings.py       # Configuration
├── data/
│   ├── content-pipeline.json    # Content tracker
│   └── expert-network-requests.md
└── scripts/              # Helper scripts
```

## Data Sync

To sync with Clawdbot, you can:
1. Pull updates from the container periodically
2. Or set up a shared volume mount

---

Built with ❤️ by Clawdbot
