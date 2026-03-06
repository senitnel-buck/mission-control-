# Marcus Phase 1 MVP - Implementation Checklist

**Goal:** Get FRED pipeline running daily  
**Duration:** ~3-4 hours setup, then 3-7 days monitoring  
**Owner:** You + Marcus + Taylor

---

## Pre-Implementation (30 min)

- [ ] Read MARCUS-PHASE1-SETUP.md (fully understand)
- [ ] Read TAYLOR-CRON-DEFINITIONS.md (understand scheduling)
- [ ] Review MARCUS-SOUL.md sections on data validation and analysis
- [ ] Verify you have Python 3.8+ installed: `python3 --version`

---

## FRED API Setup (15 min)

- [ ] Create account on fred.stlouisfed.org (if needed)
- [ ] Generate API key from user account dashboard
- [ ] Copy API key to `config/fred-config.json`
- [ ] Verify file is in .gitignore (so key won't leak to GitHub)

**Verify:**
```bash
grep "api_key" config/fred-config.json | grep -v "YOUR_"
```

---

## Install Dependencies (10 min)

- [ ] Install requirements: `pip install -r scripts/requirements.txt`
- [ ] Verify requests library: `python3 -c "import requests; print('OK')"`

---

## Test Phase 1: Fetch FRED Data (15 min)

```bash
python3 scripts/fetch_fred.py
```

**Verify success:**
- [ ] Exit code 0 (no errors in console)
- [ ] 5 JSON files created in `data/fred/raw/`
- [ ] Files contain observations with dates and values
- [ ] `telemetry/daily/YYYY-MM-DD/fred-health.json` created
- [ ] Health telemetry shows "success_rate": 1.0

**If failed:**
- [ ] Check FRED API key is correct
- [ ] Check internet connection
- [ ] Review error in `logs/fetch_fred.log`

---

## Test Phase 2: Validate Data (10 min)

```bash
python3 scripts/validate_data.py
```

**Verify success:**
- [ ] Exit code 0 (no errors)
- [ ] Validation report created in `telemetry/daily/YYYY-MM-DD/data-validation.json`
- [ ] Quality tier is GREEN or YELLOW (not RED)
- [ ] All series show "freshness": "CURRENT"

**If failed:**
- [ ] Check that FRED fetch completed (files exist)
- [ ] Review validation report for specific failures
- [ ] Check `logs/validate_data.log`

---

## Test Phase 3: Run Daily Analysis (10 min)

```bash
python3 scripts/marcus_daily_analysis.py
```

**Verify success:**
- [ ] Exit code 0 (no errors)
- [ ] Markdown report created: `memory/daily-analysis/YYYY-MM-DD-marcus-analysis.md`
- [ ] JSON output created: `memory/daily-analysis/YYYY-MM-DD-marcus-analysis.json`
- [ ] Report contains "Summary" section with signal/anomaly counts
- [ ] Check `logs/marcus_analysis.log`

**If alerts were triggered:**
- [ ] Alert files created in `alerts/active/`
- [ ] Alert files are valid JSON
- [ ] Alert has timestamp, level (CRITICAL/WARNING), and description

---

## Full Pipeline Test (15 min)

Clean up and run the entire workflow:

```bash
# Clean old test data
rm -f data/fred/raw/$(date +%Y-%m-%d)_*.json
rm -f telemetry/daily/$(date +%Y-%m-%d)/*.json
rm -f memory/daily-analysis/$(date +%Y-%m-%d)-*.json

# Run full pipeline
python3 scripts/fetch_fred.py && echo "Fetch: OK"
python3 scripts/validate_data.py && echo "Validation: OK"
python3 scripts/marcus_daily_analysis.py && echo "Analysis: OK"

# Verify all outputs exist
[ -d "data/fred/raw" ] && echo "Data: OK"
[ -d "telemetry/daily/$(date +%Y-%m-%d)" ] && echo "Telemetry: OK"
[ -f "memory/daily-analysis/$(date +%Y-%m-%d)-marcus-analysis.md" ] && echo "Report: OK"
```

---

## Schedule Cron Jobs (15 min)

**Option A: Manual crontab edit**

```bash
# Edit crontab
crontab -e

# Add these 3 lines:
0 1 * * * cd /root/clawd-main && /usr/bin/python3 scripts/fetch_fred.py >> logs/fetch_fred.log 2>&1
0 2 * * * cd /root/clawd-main && /usr/bin/python3 scripts/validate_data.py >> logs/validate_data.log 2>&1
30 2 * * * cd /root/clawd-main && /usr/bin/python3 scripts/marcus_daily_analysis.py >> logs/marcus_analysis.log 2>&1

# Verify crontab
crontab -l
```

**Option B: Have Taylor manage via cron tool**

- [ ] Share TAYLOR-CRON-DEFINITIONS.md with Taylor
- [ ] Taylor schedules the 3 jobs using cron management system
- [ ] Verify jobs scheduled: `crontab -l | grep -E "fetch_fred|validate_data|marcus"`

---

## Monitor First Run (5 min)

- [ ] At 01:00 UTC tomorrow, check for new data files
- [ ] At 02:00 UTC, check for validation results
- [ ] At 02:30 UTC, check for analysis report

```bash
# Check logs next morning
tail -20 logs/fetch_fred.log
tail -20 logs/validate_data.log
tail -20 logs/marcus_analysis.log

# All should show success/info messages, no errors
```

---

## Monitor Week 1 (3-7 days)

- [ ] Run `tail -f logs/marcus_analysis.log` to watch daily execution
- [ ] Review daily analysis reports in `memory/daily-analysis/`
- [ ] Check for alerts in `alerts/active/`
- [ ] Verify data quality remains GREEN
- [ ] Document any issues

**Success criteria:**
- [ ] All 3 jobs run daily without errors
- [ ] Data is fetched, validated, and analyzed
- [ ] At least 3 consecutive days of clean runs
- [ ] No Python exceptions in logs

---

## Commit Progress (5 min)

```bash
# After successful test run
cd /root/clawd-main
git add -A
git commit -m "docs: Marcus Phase 1 MVP - FRED pipeline tested and operational

- All 3 scripts (fetch, validate, analyze) tested locally
- Configuration set up and verified
- Cron jobs scheduled [if applicable]
- [Date] - [Number] consecutive days of clean daily runs
"
git push origin main
```

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "FRED API key not configured" | Update `config/fred-config.json` with real key |
| "No module named requests" | `pip install requests` |
| No data files created | Check FRED API is reachable, internet connection |
| Data shows "STALE" | FRED data updates daily; if >7 days old, check external API |
| No alerts created | Anomalies may not be present (this is OK, normal behavior) |
| Cron jobs not running | Check crontab: `crontab -l`, verify times in UTC |
| Permission denied on script | Run: `chmod +x scripts/fetch_fred.py` |

---

## Phase 1 Success Metrics

**Minimum viable success:**
- ✅ FRED fetch runs daily at 01:00 UTC
- ✅ Data validation runs daily at 02:00 UTC  
- ✅ Analysis runs daily at 02:30 UTC
- ✅ No critical errors for 3+ consecutive days
- ✅ At least 5 FRED series fetched daily
- ✅ Analysis reports generated daily

---

## Phase 2 Kickoff Conditions

After Phase 1 runs cleanly for 3-7 days:

- [ ] Review MARCUS-TECHNICAL-SPECIFICATION.md Phase 2 section
- [ ] Plan NASEN pipeline implementation
- [ ] Plan FMOC pipeline implementation
- [ ] Expand cross-agent integration (Sterling signals, Taylor diagnostics)

---

## Estimated Timeline

| Step | Duration | Owner |
|------|----------|-------|
| Setup & Config | 30 min | You |
| Install deps | 10 min | You |
| Test FRED fetch | 15 min | You |
| Test validation | 10 min | You |
| Test analysis | 10 min | You |
| Full pipeline test | 15 min | You |
| Schedule cron | 15 min | You / Taylor |
| **TOTAL** | **~2 hours** | |
| Monitor Week 1 | 5 min/day | You + Marcus |
| **Phase 1 Complete** | **7 days** | You + Marcus + Taylor |

---

## Key Contacts

- **Marcus:** Owns analysis, data validation, signal detection
- **Taylor:** Owns cron scheduling, logs, monitoring
- **Sentinel:** Executive oversight, alert review

---

**Next step:** Start with FRED API setup, then run through checklist  
**Status:** Ready for implementation  
**Last updated:** 2026-01-22
