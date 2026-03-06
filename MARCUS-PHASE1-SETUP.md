# Marcus Phase 1 MVP Setup Guide

**Goal:** Implement FRED data pipeline + basic analysis

**Duration:** ~2-3 hours for setup + testing

---

## STEP 1: Get FRED API Key

1. **Go to:** https://fred.stlouisfed.org/
2. **Register** for free account (if you don't have one)
3. **Navigate:** User → My Account → API Keys
4. **Copy API key**

---

## STEP 2: Configure FRED API Key

Edit `config/fred-config.json`:

```json
{
  "fred": {
    "api_key": "YOUR_ACTUAL_FRED_API_KEY_HERE",  // ← REPLACE THIS
    ...
  }
}
```

**Important:** Keep this key private. Don't commit to git (it's already in .gitignore).

---

## STEP 3: Install Python Dependencies

```bash
cd /root/clawd-main
pip install -r scripts/requirements.txt
```

Verify installation:
```bash
python3 -c "import requests; print('requests OK')"
```

---

## STEP 4: Test Data Fetch

```bash
# Manually run fetch_fred.py
python3 scripts/fetch_fred.py
```

**Expected output:**
```
INFO - Saving raw data...
INFO - FRED fetch complete: 5/5 successful
```

**Check results:**
```bash
ls -la data/fred/raw/
# Should show files like: 2026-01-22_FEDFUNDS.json
```

---

## STEP 5: Inspect Fetched Data

```bash
# View raw FRED data
cat data/fred/raw/$(date +%Y-%m-%d)_FEDFUNDS.json | jq .

# Should show:
{
  "series_id": "FEDFUNDS",
  "fetched_at": "2026-01-22T02:15:00Z",
  "observations": [
    {
      "date": "2026-01-20",
      "value": "4.50"
    },
    ...
  ]
}
```

---

## STEP 6: Test Data Validation

```bash
python3 scripts/validate_data.py
```

**Expected output:**
```
INFO - Validation report written: telemetry/daily/2026-01-22/data-validation.json
INFO - Data quality: GREEN
```

**Check validation:**
```bash
cat telemetry/daily/$(date +%Y-%m-%d)/data-validation.json | jq .
```

---

## STEP 7: Test Daily Analysis

```bash
python3 scripts/marcus_daily_analysis.py
```

**Expected output:**
```
INFO - Loaded 5 FRED series
INFO - Analysis complete: N signals, M anomalies, K alerts
```

**Check analysis output:**
```bash
# Markdown report
cat memory/daily-analysis/$(date +%Y-%m-%d)-marcus-analysis.md

# JSON output
cat memory/daily-analysis/$(date +%Y-%m-%d)-marcus-analysis.json | jq .
```

---

## STEP 8: Set Up Cron Jobs (Taylor's Responsibility)

**These are managed by Taylor (via cron).** 

Add to crontab (or have Taylor manage via TAYLOR-SOUL.md):

```bash
# FRED Data Fetch - Daily at 01:00 UTC
0 1 * * * cd /root/clawd-main && /usr/bin/python3 scripts/fetch_fred.py >> logs/fetch_fred.log 2>&1

# Data Validation - Daily at 02:00 UTC (after fetch, after backup)
0 2 * * * cd /root/clawd-main && /usr/bin/python3 scripts/validate_data.py >> logs/validate_data.log 2>&1

# Marcus Daily Analysis - Daily at 02:30 UTC
30 2 * * * cd /root/clawd-main && /usr/bin/python3 scripts/marcus_daily_analysis.py >> logs/marcus_analysis.log 2>&1
```

---

## STEP 9: Test End-to-End Flow

Simulate the daily workflow:

```bash
# Clean up today's data (for testing)
rm -f data/fred/raw/$(date +%Y-%m-%d)_*.json
rm -f telemetry/daily/$(date +%Y-%m-%d)/*.json
rm -f memory/daily-analysis/$(date +%Y-%m-%d)-*.json

# Run pipeline
python3 scripts/fetch_fred.py
python3 scripts/validate_data.py
python3 scripts/marcus_daily_analysis.py

# Verify all outputs exist
ls -la data/fred/raw/$(date +%Y-%m-%d)_*.json
ls -la telemetry/daily/$(date +%Y-%m-%d)/
ls -la memory/daily-analysis/$(date +%Y-%m-%d)-*

# Check for alerts
ls -la alerts/active/
```

---

## STEP 10: Verify Logs

Check that everything ran successfully:

```bash
# Fetch logs
tail -20 logs/fetch_fred.log

# Validation logs
tail -20 logs/validate_data.log

# Analysis logs
tail -20 logs/marcus_analysis.log

# All should show SUCCESS or INFO messages
```

---

## Troubleshooting

### Problem: "FRED API key not configured"

**Solution:** Update `config/fred-config.json` with your real API key

```bash
# Check current config
cat config/fred-config.json | grep api_key

# Should show your key, not "YOUR_FRED_API_KEY_HERE"
```

### Problem: "Data directory not found"

**Solution:** Directories are created automatically, but verify:

```bash
mkdir -p data/fred/{raw,processed}
mkdir -p telemetry/daily
mkdir -p memory/daily-analysis
```

### Problem: "No module named requests"

**Solution:** Install dependencies

```bash
pip install requests
```

### Problem: No data in observations

**Solution:** FRED API might be rate-limited or unreachable. Check:

```bash
# Test FRED API directly
curl "https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key=YOUR_KEY"

# If that works, the issue is elsewhere
```

---

## What's Working (Phase 1 MVP)

✅ **Daily FRED data fetch** (5 economic indicators)  
✅ **Data quality validation** (schema, freshness, outliers)  
✅ **Anomaly detection** (z-score based)  
✅ **Market signal detection** (percentage changes >0.5%)  
✅ **Alert generation** (for Sentinel)  
✅ **Daily analysis report** (markdown + JSON)  
✅ **Audit trail** (all outputs logged, timestamped)

---

## What's Next (Phase 2)

After Phase 1 stabilizes (3-7 days of clean data):

- [ ] NASEN energy pipeline (same pattern as FRED)
- [ ] FMOC meeting data pipeline (calendar-based)
- [ ] Cross-agent data sharing (Sterling signals, Taylor diagnostics)
- [ ] Weekly/monthly strategic analysis
- [ ] Forecasting models (time series, MA, etc.)

---

## Important Notes

1. **API Rate Limits:** FRED allows 120 calls/minute. We're well within limits (5 calls/day).

2. **Data Retention:** Raw data kept for 90 days locally, older data archived.

3. **Alerts:** Currently file-based. Later phases can add message-based delivery.

4. **Scheduling:** Taylor (cron) owns all scheduling. Marcus owns analysis.

5. **Git:** All analysis outputs go to `/memory/` and `/alerts/` which are git-tracked for audit trail.

---

## Testing Checklist

- [ ] FRED API key configured
- [ ] `fetch_fred.py` runs successfully
- [ ] Data files created in `data/fred/raw/`
- [ ] `validate_data.py` runs successfully
- [ ] Validation results in `telemetry/daily/`
- [ ] `marcus_daily_analysis.py` runs successfully
- [ ] Analysis report in `memory/daily-analysis/`
- [ ] Logs show no errors
- [ ] All 3 cron jobs scheduled (or queued for Taylor)

---

**Status:** Ready for Phase 1 deployment  
**Next:** Have Taylor schedule cron jobs, run for 3-7 days, then assess for Phase 2
