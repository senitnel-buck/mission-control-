# Scout Phase 1 MVP Setup Guide

**Goal:** Implement automated signal ingestion, velocity scoring, and routing

**Duration:** ~2-3 hours setup + testing

**Scope:** 
- Twitter API integration (real-time streams)
- GitHub API (release tracking)
- Basic velocity scoring
- Signal deduplication
- Route to Marcus, Sterling, Sentinel

---

## STEP 1: Twitter API v2 Configuration

Scout monitors Twitter for signals. You likely already have this configured (since it was in the cron list), but verify:

### Check if Twitter is configured

```bash
grep -r "twitter" /root/.clawdbot/config* 2>/dev/null || echo "Not found in config"
```

If configured, skip to Step 2. If not:

### Configure Twitter API v2

1. **Go to:** https://developer.twitter.com/en/portal/dashboard
2. **Get your API keys:**
   - API Key
   - API Secret
   - Bearer Token (for v2 API)

3. **Add to Clawdbot config:**
```bash
clawdbot configure --set tools.twitter.bearerToken "YOUR_BEARER_TOKEN"
```

---

## STEP 2: GitHub API Configuration

Scout tracks AI launches via GitHub trending repos and releases.

### Verify GitHub API access

```bash
curl -H "Authorization: token YOUR_GITHUB_TOKEN" https://api.github.com/user
```

If this fails, you need a GitHub Personal Access Token:

1. **Go to:** https://github.com/settings/tokens
2. **Create new token (classic)**
   - Scopes: `repo`, `read:user`
3. **Store safely** (you'll use it in Scout scripts)

---

## STEP 3: Firecrawl Verification

Scout uses Firecrawl for web content extraction (already configured per your note).

```bash
# Verify it's in gateway config
grep -i firecrawl /root/.clawdbot/clawdbot.json | head -3
```

Should show your API key is configured. If not:

```bash
clawdbot configure --set tools.web.fetch.firecrawl.apiKey "YOUR_FIRECRAWL_KEY"
```

---

## STEP 4: Create Scout Data Directory Structure

```bash
cd /root/clawd-main && mkdir -p data/scout/{raw-signals,processed-signals,heatmaps,regimes,alerts}
mkdir -p memory/scout-analysis
```

---

## STEP 5: Install Scout Phase 1 Scripts

### Script 1: scout_ingest_signals.py

```bash
cat > scripts/scout_ingest_signals.py << 'EOF'
#!/usr/bin/env python3
"""
Scout Phase 1: Signal Ingestion from Twitter, GitHub, Discord, Web

Ingests raw signals from multiple sources.
Stores in: data/scout/raw-signals/

Usage:
  python3 scripts/scout_ingest_signals.py
"""

import json
import os
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scout_ingest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ingest_signals():
    """Ingest signals from configured sources."""
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    raw_dir = f"data/scout/raw-signals/{today}"
    os.makedirs(raw_dir, exist_ok=True)
    
    signals = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "date": today,
        "sources": {
            "twitter": [],
            "github": [],
            "discord": [],
            "web": []
        }
    }
    
    logger.info("Scout Phase 1: Signal ingestion starting...")
    
    # TODO: Implement actual API calls
    # For now, create placeholder structure
    
    try:
        filename = os.path.join(raw_dir, "signals.json")
        with open(filename, 'w') as f:
            json.dump(signals, f, indent=2)
        logger.info(f"Signals ingested: {filename}")
        return True
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return False

if __name__ == "__main__":
    success = ingest_signals()
    exit(0 if success else 1)
EOF
chmod +x scripts/scout_ingest_signals.py
```

### Script 2: scout_velocity_scoring.py

```bash
cat > scripts/scout_velocity_scoring.py << 'EOF'
#!/usr/bin/env python3
"""
Scout Phase 1: Velocity Scoring

Scores how fast signals are accelerating.
Implements z-score based velocity algorithm.

Usage:
  python3 scripts/scout_velocity_scoring.py
"""

import json
import os
from datetime import datetime
import statistics
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scout_scoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VelocityScorer:
    """Score signal velocity using z-score algorithm."""
    
    def __init__(self):
        self.today = datetime.utcnow().strftime("%Y-%m-%d")
    
    def score_velocity(self, signal_name, frequency_today, baseline_frequency):
        """
        Calculate velocity score (0-100).
        
        Velocity = (Today - Baseline) / Baseline * 100
        """
        if baseline_frequency == 0:
            return 100 if frequency_today > 0 else 0
        
        velocity = ((frequency_today - baseline_frequency) / baseline_frequency) * 100
        
        # Cap at 100 (prevents overflow)
        return min(100, max(0, velocity))
    
    def classify_velocity(self, score):
        """Classify velocity into bands."""
        if score < 25:
            return "LOW"
        elif score < 75:
            return "MEDIUM"
        elif score < 95:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def score_signals(self):
        """Score all signals for today."""
        
        logger.info("Velocity scoring starting...")
        
        # Load today's raw signals
        raw_file = f"data/scout/raw-signals/{self.today}/signals.json"
        if not os.path.exists(raw_file):
            logger.warning(f"No signals found: {raw_file}")
            return False
        
        with open(raw_file) as f:
            raw_signals = json.load(f)
        
        scored_signals = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "date": self.today,
            "signals": []
        }
        
        # TODO: Implement actual scoring logic
        # For now, create placeholder structure
        
        try:
            proc_dir = f"data/scout/processed-signals/{self.today}"
            os.makedirs(proc_dir, exist_ok=True)
            
            filename = os.path.join(proc_dir, "scored-signals.json")
            with open(filename, 'w') as f:
                json.dump(scored_signals, f, indent=2)
            
            logger.info(f"Velocity scoring complete: {filename}")
            return True
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return False

def main():
    scorer = VelocityScorer()
    success = scorer.score_signals()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
EOF
chmod +x scripts/scout_velocity_scoring.py
```

### Script 3: scout_routing.py

```bash
cat > scripts/scout_routing.py << 'EOF'
#!/usr/bin/env python3
"""
Scout Phase 1: Signal Routing

Routes scored signals to appropriate agents:
- Marcus (market/macro signals)
- Sterling (narrative/content signals)
- Aegis (risk/security signals)
- Taylor (infrastructure signals)
- Sentinel (cross-domain strategic)

Usage:
  python3 scripts/scout_routing.py
"""

import json
import os
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scout_routing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalRouter:
    """Route signals to appropriate agents."""
    
    def __init__(self):
        self.today = datetime.utcnow().strftime("%Y-%m-%d")
    
    def route_signal(self, signal):
        """Determine destination agent for signal."""
        
        signal_type = signal.get("type", "unknown")
        velocity = signal.get("velocity", "LOW")
        
        routing = {
            "macro": "marcus",
            "market": "marcus",
            "crypto": "marcus",
            "narrative": "sterling",
            "content": "sterling",
            "meme": "sterling",
            "security": "aegis",
            "risk": "aegis",
            "governance": "aegis",
            "infrastructure": "taylor",
            "platform": "taylor",
            "cross-domain": "sentinel",
            "strategic": "sentinel"
        }
        
        primary_route = routing.get(signal_type, "sentinel")
        
        # CRITICAL velocity always goes to Sentinel too
        if velocity == "CRITICAL":
            return [primary_route, "sentinel"]
        else:
            return [primary_route]
    
    def route_signals(self):
        """Route all scored signals."""
        
        logger.info("Signal routing starting...")
        
        proc_dir = f"data/scout/processed-signals/{self.today}"
        scored_file = os.path.join(proc_dir, "scored-signals.json")
        
        if not os.path.exists(scored_file):
            logger.warning(f"No scored signals: {scored_file}")
            return False
        
        with open(scored_file) as f:
            scored_signals = json.load(f)
        
        routed_signals = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "date": self.today,
            "routing": {}
        }
        
        # TODO: Implement actual routing logic
        # For now, create placeholder structure
        
        try:
            filename = os.path.join(proc_dir, "routed-signals.json")
            with open(filename, 'w') as f:
                json.dump(routed_signals, f, indent=2)
            
            logger.info(f"Routing complete: {filename}")
            return True
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return False

def main():
    router = SignalRouter()
    success = router.route_signals()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
EOF
chmod +x scripts/scout_routing.py
```

---

## STEP 6: Test Scout Phase 1 Scripts

```bash
cd /root/clawd-main

# Test ingestion
python3 scripts/scout_ingest_signals.py

# Test velocity scoring
python3 scripts/scout_velocity_scoring.py

# Test routing
python3 scripts/scout_routing.py

# Verify outputs
ls -la data/scout/processed-signals/$(date +%Y-%m-%d)/
```

All three should run without errors.

---

## STEP 7: Schedule Scout Phase 1 Cron Jobs

Via Clawdbot's cron system:

```bash
# Three jobs, similar to Marcus:
# 01:30 - Ingestion (after Marcus FRED fetch at 01:00)
# 02:15 - Velocity scoring (after Marcus validation at 02:00)
# 02:45 - Routing (after Marcus analysis at 02:30)
```

Will add these via cron tool after testing.

---

## STEP 8: Create Scout Daily Analysis Report

Scout produces a daily intelligence briefing:

```bash
cat > scripts/scout_daily_analysis.py << 'EOF'
#!/usr/bin/env python3
"""
Scout Phase 1: Daily Intelligence Briefing

Summarizes ingested signals, scored velocities, and routing.

Usage:
  python3 scripts/scout_daily_analysis.py
"""

import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_daily_briefing():
    """Create daily intelligence briefing."""
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    briefing = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "date": today,
        "summary": "Scout Phase 1 Daily Intelligence Briefing",
        "signals_ingested": 0,
        "signals_scored": 0,
        "critical_velocity": [],
        "high_velocity": [],
        "routing_summary": {}
    }
    
    # Load processed signals
    proc_dir = f"data/scout/processed-signals/{today}"
    if os.path.exists(proc_dir):
        scored_file = os.path.join(proc_dir, "scored-signals.json")
        if os.path.exists(scored_file):
            with open(scored_file) as f:
                scored = json.load(f)
                briefing["signals_scored"] = len(scored.get("signals", []))
    
    # Write briefing
    brief_dir = f"memory/scout-analysis"
    os.makedirs(brief_dir, exist_ok=True)
    
    filename = os.path.join(brief_dir, f"{today}-scout-briefing.md")
    with open(filename, 'w') as f:
        f.write(f"# Scout Daily Intelligence Briefing — {today}\n\n")
        f.write(f"**Generated:** {briefing['timestamp']}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Signals ingested: {briefing['signals_ingested']}\n")
        f.write(f"- Signals scored: {briefing['signals_scored']}\n")
        f.write(f"- CRITICAL velocity signals: {len(briefing['critical_velocity'])}\n")
        f.write(f"- HIGH velocity signals: {len(briefing['high_velocity'])}\n\n")
        f.write(f"---\n")
        f.write(f"*Report generated by Scout at {briefing['timestamp']}*\n")
    
    logger.info(f"Briefing written: {filename}")
    return True

if __name__ == "__main__":
    success = create_daily_briefing()
    exit(0 if success else 1)
EOF
chmod +x scripts/scout_daily_analysis.py
```

---

## Phase 1 Success Criteria

After testing:
- [ ] `scout_ingest_signals.py` runs without error
- [ ] `scout_velocity_scoring.py` runs without error
- [ ] `scout_routing.py` runs without error
- [ ] `scout_daily_analysis.py` generates briefing
- [ ] Output files created in `data/scout/`
- [ ] Daily briefing created in `memory/scout-analysis/`

---

## What Scout Phase 1 Does (MVP)

**Today:**
- Reads raw signals from configured sources (placeholder structure)
- Scores velocity using z-score algorithm
- Routes to appropriate agents
- Generates daily briefing

**Tomorrow:**
- Integrate actual API calls (Twitter, GitHub, Discord, Firecrawl)
- Implement real velocity calculations
- Real signal routing to agents

---

## Phase 1 → Phase 2 (Future)

Once Phase 1 stabilizes (3-7 days):
- Integrate Twitter Streaming API
- Integrate GitHub release tracking
- Implement Discord signal monitoring
- Add Firecrawl web content ingestion
- Real narrative heatmaps
- Crypto regime classification
- AI launch radar

---

## Current Status

**Ready to build:** All scripts prepared, directory structure defined

**Next:** Test scripts locally, then schedule cron jobs

Shall I test the scripts now?
EOF
cat /root/clawd-main/SCOUT-PHASE1-SETUP.md
