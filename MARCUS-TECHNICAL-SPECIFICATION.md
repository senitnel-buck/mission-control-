# MARCUS TECHNICAL SPECIFICATION

**Author:** Sentinel (on behalf of Marcus)  
**Date:** 2026-01-22  
**Purpose:** Define technical architecture for Marcus's data pipelines, telemetry access, and alert systems

---

## EXECUTIVE SUMMARY

Marcus requires:
1. **Telemetry collection interface** for system metrics
2. **Alert/messaging delivery system** to Sentinel
3. **Data storage architecture** for pipelines and analysis
4. **Pipeline automation framework** (managed by Taylor's cron)
5. **Cross-agent data sharing protocol** (Sterling, Taylor)

This spec defines MVP (Minimum Viable Product) and nice-to-have enhancements.

---

## 1. SYSTEM TELEMETRY COLLECTION

### 1.1 Telemetry Sources Required

Marcus needs access to:

| Source | Data | Format | Frequency | Location/API |
|--------|------|--------|-----------|--------------|
| **Gateway logs** | Uptime, websocket stability, latency | JSON lines or plain text | Real-time / daily summary | `~/.clawdbot/logs/gateway.log` (or API) |
| **Cron outputs** | Job success/failure, execution time, output | JSON or structured text | Per job completion | `~/.clawdbot/logs/cron/` directory |
| **Agent metrics** | Bootstrap time, task completion rate, token/task | JSON | Daily summary or per-session | Sentinel/gateway telemetry API or memory files |
| **Session data** | Session count, memory per session, token/session | JSON | Daily/hourly | Session manager API or status files |
| **Token tracking** | Daily burn rate, session token consumption | JSON | Daily | Token usage logs or API |
| **Container health** | Docker restart count, CPU/memory, uptime | JSON | Daily health check | Docker stats API or Taylor's health report |

### 1.2 MVP Implementation: File-Based Telemetry

**Simple, no API required:**

```
/root/clawd-main/telemetry/
├── daily/
│   └── YYYY-MM-DD/
│       ├── gateway-health.json
│       ├── cron-summary.json
│       ├── agent-metrics.json
│       ├── session-metrics.json
│       └── token-burn.json
├── archive/
│   └── YYYY-MM/ (older data)
└── current.json (latest snapshot)
```

**Each JSON file contains:**
```json
{
  "timestamp": "2026-01-22T02:00:00Z",
  "source": "gateway|cron|agent|session|token",
  "status": "healthy|degraded|critical",
  "metrics": {
    "key": "value"
  },
  "notes": "Human-readable context"
}
```

**Marcus's job:** 
- Daily 02:00 UTC: Read all JSON files from `telemetry/daily/YYYY-MM-DD/`
- Validate freshness and schema
- Trigger anomaly detection
- Store processed analysis in `memory/daily-analysis/`

**Taylor's job (cron-managed):**
- Daily 01:00 UTC: Generate telemetry JSON files from various sources
- Write to `telemetry/daily/YYYY-MM-DD/`
- Include timestamp and validation checksums

**Advantage:** No API, file-based, git-trackable, simple to debug

### 1.3 Telemetry JSON Schema Examples

**gateway-health.json**
```json
{
  "timestamp": "2026-01-22T02:00:00Z",
  "source": "gateway",
  "metrics": {
    "uptime_percent": 99.8,
    "websocket_disconnects_24h": 2,
    "avg_latency_ms": 145,
    "reconnect_attempts": 1,
    "errors_last_24h": 0
  },
  "status": "healthy",
  "notes": "Stable, within normal parameters"
}
```

**cron-summary.json**
```json
{
  "timestamp": "2026-01-22T02:00:00Z",
  "source": "cron",
  "metrics": {
    "total_jobs_24h": 24,
    "successful": 23,
    "failed": 1,
    "success_rate": 0.958,
    "avg_execution_time_sec": 14.2,
    "longest_execution_sec": 47
  },
  "failed_jobs": [
    {
      "name": "market-intel-task",
      "error": "API timeout",
      "execution_time_sec": 47
    }
  ],
  "status": "degraded",
  "notes": "One failure due to external API lag, otherwise healthy"
}
```

**token-burn.json**
```json
{
  "timestamp": "2026-01-22T02:00:00Z",
  "source": "token",
  "metrics": {
    "tokens_consumed_24h": 1200000,
    "daily_average_last_7days": 1100000,
    "growth_percent": 9.1,
    "runway_days": 90,
    "forecast_runway_if_growth_continues": 60
  },
  "status": "healthy",
  "notes": "Burn trending up slightly, monitor for acceleration"
}
```

---

## 2. ALERT & NOTIFICATION DELIVERY

### 2.1 Alert System Design

**Alert levels:**
- **CRITICAL:** Immediate action required (pipeline down, system cliff, security issue)
- **WARNING:** Attention needed, may require action (performance degradation, anomaly)
- **INFO:** Informational (routine findings, trends)

**Delivery mechanism:** File-based + message tool

### 2.2 Alert File Structure

```
/root/clawd-main/alerts/
├── active/
│   └── CRITICAL_2026-01-22_data-source-outage.json
├── resolved/
│   └── CRITICAL_2026-01-20_data-source-outage.json
└── archive/
    └── 2026-01/ (older)
```

**Alert JSON format:**
```json
{
  "id": "data-source-outage",
  "timestamp": "2026-01-22T03:15:00Z",
  "level": "CRITICAL",
  "title": "FRED Pipeline Unavailable",
  "description": "FRED API not responding. Last successful pull: 48h ago.",
  "source": "marcus",
  "affected_systems": ["market-intelligence", "content-strategy"],
  "recommended_action": "Investigate FRED API status. Switch to cached data if available.",
  "escalation_target": "sentinel",
  "state": "active",
  "resolved_at": null,
  "resolution_notes": null
}
```

### 2.3 Sentinel Integration

**Sentinel's job:**
- Monitor `alerts/active/` directory
- For CRITICAL alerts: immediately notified (message tool or console)
- For WARNING/INFO: batched in daily summary
- Acknowledge alerts by moving to `alerts/resolved/` with resolution notes

**Marcus's job:**
- Write alerts to `alerts/active/` when triggered
- Monitor alert status (is Sentinel aware?)
- Auto-resolve alerts when condition clears
- Archive resolved alerts to `alerts/archive/`

### 2.4 MVP: File + Message Tool Hybrid

```python
# Marcus's alert flow
def alert_sentinel(level, title, description, action):
    # 1. Write alert file
    alert = {
        "timestamp": now(),
        "level": level,
        "title": title,
        ...
    }
    write_json(f"alerts/active/{level}_{timestamp}_{id}.json", alert)
    
    # 2. Send message if CRITICAL
    if level == "CRITICAL":
        message.send(
            channel="clawdbot",
            to="sentinel",
            message=f"🚨 {title}\n{description}\nAction: {action}"
        )
    
    # 3. Log for audit trail
    commit_alert_to_git()
```

---

## 3. DATA STORAGE ARCHITECTURE

### 3.1 Storage Locations

**Raw pipeline data:**
```
/root/clawd-main/data/
├── fred/
│   ├── raw/
│   │   └── YYYY-MM-DD_fed-funds-rate.json
│   ├── processed/
│   │   └── fred_series_cache.json
│   └── metadata.json
├── nasen/
│   ├── raw/
│   │   └── YYYY-MM-DD_energy-prices.json
│   ├── processed/
│   │   └── nasen_commodities_cache.json
│   └── metadata.json
└── fmoc/
    ├── raw/
    │   └── YYYY-MM-DD_fomc-statement.md
    ├── processed/
    │   └── fmoc_decisions.json
    └── metadata.json
```

**Analysis outputs:**
```
/root/clawd-main/memory/
├── daily-analysis/
│   └── YYYY-MM-DD-marcus-analysis.md
├── weekly-analysis/
│   └── YYYY-W##-marcus-weekly.md
├── monthly-review/
│   └── YYYY-MM-marcus-strategic.md
├── forecasts/
│   └── YYYY-MM-forecast.md
└── rca/ (root cause analyses)
    └── YYYY-MM-DD-incident-name.md
```

**Backup & versioning:**
- All data committed to git (via Taylor's backup)
- Archive old data (>90 days) to `data/archive/YYYY-MM/`
- Keep last 30 days in active directories

### 3.2 Data Versioning

Every raw data file includes:
```json
{
  "source": "fred|nasen|fmoc",
  "fetched_at": "2026-01-22T02:30:00Z",
  "data_date": "2026-01-21",  // Date the data represents
  "series_id": "FEDFUNDS",    // For FRED
  "processing_version": 1,
  "checksum": "sha256:abc123..."
}
```

### 3.3 Data Retention Policy

| Data Type | Retention | Location |
|-----------|-----------|----------|
| Raw pipeline data | 90 days | `/data/` |
| Processed analysis | 1 year | `/memory/` |
| Forecasts | 3 months | `/memory/forecasts/` |
| RCA reports | Permanent | `/memory/rca/` |
| Alerts | 6 months active, then archive | `/alerts/` |

---

## 4. PIPELINE ARCHITECTURE

### 4.1 Pipeline Ownership & Scheduling

**Marcus owns:** Data analysis, validation, interpretation, reporting  
**Taylor owns:** Scheduling (cron jobs), execution, infrastructure  

**Workflow:**
```
Taylor's cron job (daily 01:00 UTC)
  → Executes fetch_fred.py, fetch_nasen.py, fetch_fmoc.py
  → Writes raw data to /root/clawd-main/data/*/raw/
  → Logs execution to telemetry/

Marcus's analysis (daily 02:30 UTC, after Taylor's backup)
  → Reads raw data from /root/clawd-main/data/*/raw/
  → Validates quality (freshness, schema, outliers)
  → Processes into insights
  → Writes to memory/daily-analysis/
  → Generates alerts if needed
```

### 4.2 FRED Pipeline (Federal Reserve Economic Data)

**Source:** API at https://fred.stlouisfed.org/  
**Required:** API key (free from fred.org)

**MVP Script: fetch_fred.py**
```python
import requests
import json
from datetime import datetime

FRED_API_KEY = "YOUR_API_KEY"  # Store in secure config
FRED_ENDPOINT = "https://api.stlouisfed.org/fred"

# Series IDs to fetch
SERIES = {
    "FEDFUNDS": "Federal Funds Rate",
    "UNRATE": "Unemployment Rate",
    "CPIAUCSL": "CPI All Urban Consumers",
    "A191RL1Q225SBEA": "Real GDP"
}

def fetch_series(series_id):
    url = f"{FRED_ENDPOINT}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

def save_data(series_id, data):
    filename = f"/root/clawd-main/data/fred/raw/{datetime.now().strftime('%Y-%m-%d')}_{series_id}.json"
    with open(filename, 'w') as f:
        json.dump({
            "series_id": series_id,
            "fetched_at": datetime.now().isoformat(),
            "data": data
        }, f)
    print(f"Saved {filename}")

if __name__ == "__main__":
    for series_id, name in SERIES.items():
        try:
            data = fetch_series(series_id)
            save_data(series_id, data)
        except Exception as e:
            print(f"ERROR fetching {series_id}: {e}")
            # Log to telemetry for Marcus to detect
```

**Taylor's cron job:**
```
0 1 * * * /usr/bin/python3 /root/clawd-main/scripts/fetch_fred.py >> /root/clawd-main/logs/fetch_fred.log 2>&1
```

**Marcus's validation:**
- Check file exists and is <24h old
- Parse JSON, verify expected fields
- Check for data gaps or NaN values
- Compare latest value to historical range (flag outliers)
- Write quality tier (GREEN/YELLOW/RED) to metadata

### 4.3 NASEN Pipeline (Energy Market Data)

**Source:** [Specify: API? Web scraping? Data feed?]  
**Frequency:** Daily market data, weekly fundamentals

**TBD:** Exact data source and API details (placeholder for Jason to specify)

**Structure:** Similar to FRED
```
/root/clawd-main/data/nasen/raw/YYYY-MM-DD_commodities.json
```

### 4.4 FMOC Pipeline (Federal Open Market Committee)

**Source:** federalreserve.gov, Bloomberg, financial news feeds  
**Frequency:** 8x annually (FOMC meetings ~every 6 weeks)

**Calendar-based approach:**
```python
# fmoc_calendar.json
{
  "meetings": [
    { "date": "2026-01-28", "announcement_time": "14:00 UTC" },
    { "date": "2026-03-18", "announcement_time": "14:00 UTC" },
    ...
  ]
}

# Check calendar, trigger fetch on meeting date
if today == next_fomc_date:
    fetch_statement_and_transcripts()
```

**Data capture:**
1. Post-announcement (immediately): Statement + market reaction
2. Transcript (3 weeks later): Full meeting transcript
3. Follow-up: Member speeches, economic projections

**Storage:**
```
/root/clawd-main/data/fmoc/raw/
├── 2026-01-28_statement.md
├── 2026-01-28_market_reaction.json
├── 2026-02-18_transcript.md (3 weeks later)
└── 2026-02-xx_member_speeches.json
```

---

## 5. ANOMALY DETECTION FRAMEWORK

### 5.1 Statistical Thresholds

**Z-score based (simple MVP):**
```python
def detect_anomaly(value, historical_values):
    mean = statistics.mean(historical_values[-30:])  # 30-day average
    stdev = statistics.stdev(historical_values[-30:])
    z_score = (value - mean) / stdev if stdev > 0 else 0
    
    if abs(z_score) > 3:
        return "CRITICAL_ANOMALY"
    elif abs(z_score) > 2:
        return "ANOMALY"
    else:
        return "NORMAL"
```

**Applied to:**
- Token burn rate (flag if >2 std dev above mean)
- Cron job execution time (flag if >2 std dev)
- Agent reliability (flag if success rate drops >10%)
- Market moves (flag if >3 std dev, e.g., 10%+ daily swing)

### 5.2 Anomaly Configuration

```json
{
  "anomaly_thresholds": {
    "token_burn_zscore": 2.0,
    "cron_execution_time_zscore": 2.5,
    "market_move_percent": 10.0,
    "agent_failure_rate_increase": 0.10,
    "baseline_window_days": 30
  }
}
```

---

## 6. CROSS-AGENT DATA SHARING

### 6.1 Sterling (Content Intelligence)

**Marcus → Sterling:** Signal opportunities, market intelligence, timing

**Data format:** Markdown + JSON
```
/root/clawd-main/signals/sterling/
└── YYYY-MM-DD_signal-opportunities.json
```

**JSON structure:**
```json
{
  "timestamp": "2026-01-22T02:30:00Z",
  "signals": [
    {
      "id": "energy-volatility-1",
      "title": "Natural Gas Prices Elevated",
      "confidence": "HIGH",
      "momentum": "BUILDING",
      "content_angle": "Procurement strategy in volatile markets",
      "target_audience": "Supply chain, procurement, energy network",
      "estimated_engagement": 2.3,
      "timing_window_hours": 48,
      "competitive_saturation": "LOW",
      "priority": "HIGH"
    }
  ]
}
```

**Sterling's job:**
- Daily: Check for new signals in `/signals/sterling/`
- Review, rank by priority
- Incorporate into content strategy
- Report engagement back to Marcus

### 6.2 Taylor (Infrastructure Diagnostics)

**Marcus → Taylor:** Performance baselines, degradation alerts, capacity forecasts

**Data format:** JSON reports
```
/root/clawd-main/diagnostics/taylor/
├── YYYY-MM-DD-performance-baseline.json
├── YYYY-MM-DD-anomalies.json
└── YYYY-MM-DD-capacity-forecast.json
```

**Example anomaly report:**
```json
{
  "timestamp": "2026-01-22T02:30:00Z",
  "anomalies": [
    {
      "type": "cron-execution-time",
      "job": "market-intel-task",
      "baseline_sec": 12,
      "observed_sec": 47,
      "zscore": 3.2,
      "severity": "MEDIUM",
      "likely_cause": "API lag or data volume increase",
      "recommended_action": "Investigate external API performance"
    }
  ]
}
```

**Taylor's job:**
- Daily: Read diagnostics from `/diagnostics/taylor/`
- Act on alerts (investigate, remediate)
- Report back to Marcus on resolution
- Adjust monitoring based on Marcus feedback

---

## 7. DEPENDENCIES & TOOLS

### 7.1 Required Python Libraries

```
# data/requirements.txt
pandas==2.0.0+
numpy==1.24.0+
scipy==1.10.0+
requests==2.31.0+
matplotlib==3.7.0+  # Visualization
statsmodels==0.14.0+  # Time series analysis
scikit-learn==1.3.0+  # ML/anomaly detection
```

### 7.2 External Services & Keys

| Service | API Key | Purpose | Free Tier |
|---------|---------|---------|-----------|
| FRED | fredapi.key | Economic data | YES (free registration) |
| [NASEN/Energy] | [TBD] | Energy market data | [TBD] |

### 7.3 Git Integration

All analysis scripts committed to git:
```
/root/clawd-main/scripts/
├── fetch_fred.py
├── fetch_nasen.py
├── fetch_fmoc.py
├── validate_data.py
├── analyze_signals.py
└── anomaly_detection.py
```

---

## 8. IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-2)

**Goal:** Basic pipelines + file-based telemetry

✅ **Week 1:**
- [ ] Set up telemetry JSON schema
- [ ] Write fetch_fred.py
- [ ] Create data storage directories
- [ ] Test FRED data pull

✅ **Week 2:**
- [ ] Write Marcus's daily analysis script
- [ ] Implement basic anomaly detection
- [ ] Alert file system
- [ ] Test end-to-end flow

**Result:** Marcus can pull FRED data, validate, analyze, and alert Sentinel

### Phase 2: Full Pipelines (Weeks 3-4)

**Goal:** All three pipelines (FRED, NASEN, FMOC) + cross-agent integration

- [ ] Implement NASEN pipeline
- [ ] Implement FMOC pipeline
- [ ] Cross-agent data sharing (Sterling signals, Taylor diagnostics)
- [ ] Weekly/monthly reporting

### Phase 3: Enhancement (Weeks 5+)

**Goal:** Forecasting, dashboards, advanced anomaly detection

- [ ] Forecasting models (time series, ML)
- [ ] Visualization/dashboards
- [ ] Advanced anomaly detection (isolation forest, etc.)
- [ ] Real-time alert streaming (if needed)

---

## 9. SUCCESS CRITERIA

### MVP Success
- ✅ FRED pipeline pulls daily data automatically (Taylor cron)
- ✅ Marcus validates and analyzes data
- ✅ Alerts trigger when data is stale or anomalies detected
- ✅ Sentinel receives alerts via file + message
- ✅ All data versioned in git

### Full Implementation Success
- ✅ All three pipelines (FRED, NASEN, FMOC) operational
- ✅ Sterling receives weekly signal opportunities
- ✅ Taylor receives daily diagnostics
- ✅ Weekly/monthly strategic analysis delivered
- ✅ Forecasting models accurate (80%+ accuracy on historical data)

---

## 10. OPEN QUESTIONS FOR JASON

1. **NASEN data source:** Where do you want energy data from? (API? Bloomberg? Custom feed?)
2. **Forecasting sophistication:** Simple trend extrapolation or advanced ML models?
3. **Visualization needs:** Do you need dashboards, or markdown reports sufficient?
4. **Data retention:** How far back do you want to keep historical data?
5. **Real-time requirements:** Do alerts need to be instant, or batch daily is fine?

---

## APPENDIX: Example Daily Analysis Workflow

```python
# /root/clawd-main/scripts/marcus_daily_analysis.py
# Runs daily at 02:30 UTC (after Taylor's 02:00 UTC backup)

import json, os
from datetime import datetime, timedelta

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Load telemetry
    telemetry = load_telemetry(today)
    
    # 2. Load raw data
    fred_data = load_data("data/fred/raw", today)
    nasen_data = load_data("data/nasen/raw", today)
    
    # 3. Validate quality
    fred_quality = validate_fred(fred_data)  # returns GREEN/YELLOW/RED
    nasen_quality = validate_nasen(nasen_data)
    
    # 4. Detect anomalies
    anomalies = detect_anomalies(telemetry, fred_data, nasen_data)
    
    # 5. Generate insights
    market_signals = analyze_market_trends(fred_data, nasen_data)
    system_diagnostics = analyze_system_health(telemetry)
    
    # 6. Create alerts
    for anomaly in anomalies:
        create_alert(anomaly)
    
    # 7. Write Sterling signals
    write_signals_for_sterling(market_signals)
    
    # 8. Write Taylor diagnostics
    write_diagnostics_for_taylor(system_diagnostics)
    
    # 9. Write daily analysis
    write_analysis(f"memory/daily-analysis/{today}-marcus-analysis.md", 
                   market_signals, system_diagnostics)
    
    # 10. Commit to git
    git_commit(f"analysis: {today} daily analysis and alerts")

if __name__ == "__main__":
    main()
```

---

**Status:** DRAFT - Ready for review and implementation  
**Next:** Jason feedback on open questions, then Phase 1 development
