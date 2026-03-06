# Taylor's Cron Job Definitions

**Purpose:** Define all scheduled jobs that Taylor manages  
**Owner:** Taylor (Infrastructure Autopilot)  
**Managed by:** Cron daemon (system scheduler)

---

## Phase 1: Marcus FRED Pipeline

### Job 1: Daily Backup

**Time:** 02:00 UTC (daily, before other jobs)  
**Trigger:** System cron  
**Owner:** Taylor (TAYLOR-SOUL.md — Backup Protocol)

```bash
0 2 * * * /root/clawd-main/scripts/backup.sh >> /root/clawd-main/logs/backup.log 2>&1
```

**Script:** `scripts/backup.sh` (TBD — creates daily backup, pushes to GitHub)  
**Output:** `/root/clawd-main/logs/backup.log`  
**Success indicator:** Exit code 0, backup files created

---

### Job 2: FRED Data Fetch

**Time:** 01:00 UTC (daily)  
**Script:** `scripts/fetch_fred.py`  
**Owner:** Marcus (analysis), Taylor (scheduling)

```bash
0 1 * * * cd /root/clawd-main && /usr/bin/python3 scripts/fetch_fred.py >> logs/fetch_fred.log 2>&1
```

**Purpose:** Fetch latest FRED economic data  
**Output:** 
- `/root/clawd-main/logs/fetch_fred.log` (execution log)
- `/root/clawd-main/data/fred/raw/YYYY-MM-DD_*.json` (5 series)
- `/root/clawd-main/telemetry/daily/YYYY-MM-DD/fred-health.json` (health check)

**Success indicators:**
- Exit code 0
- 5 JSON files created
- Health telemetry shows "healthy"

**Failure handling:**
- Log errors to file
- Write RED status to telemetry
- Next job (validation) will detect and alert Marcus

---

### Job 3: Data Quality Validation

**Time:** 02:00 UTC (daily, after backup and fetch)  
**Script:** `scripts/validate_data.py`  
**Owner:** Marcus (analysis), Taylor (scheduling)

```bash
0 2 * * * cd /root/clawd-main && /usr/bin/python3 scripts/validate_data.py >> logs/validate_data.log 2>&1
```

**Purpose:** Validate FRED data quality (freshness, schema, outliers)  
**Dependencies:** Job 2 (FRED fetch) must complete  
**Output:**
- `/root/clawd-main/logs/validate_data.log` (execution log)
- `/root/clawd-main/telemetry/daily/YYYY-MM-DD/data-validation.json` (validation results)

**Success indicators:**
- Exit code 0
- Validation JSON created
- Quality tier GREEN or YELLOW (not RED)

---

### Job 4: Marcus Daily Analysis

**Time:** 02:30 UTC (daily, after validation)  
**Script:** `scripts/marcus_daily_analysis.py`  
**Owner:** Marcus (analysis), Taylor (scheduling)

```bash
30 2 * * * cd /root/clawd-main && /usr/bin/python3 scripts/marcus_daily_analysis.py >> logs/marcus_analysis.log 2>&1
```

**Purpose:** Run daily analysis, detect anomalies, generate alerts  
**Dependencies:** Jobs 1–3 must complete  
**Output:**
- `/root/clawd-main/logs/marcus_analysis.log` (execution log)
- `/root/clawd-main/memory/daily-analysis/YYYY-MM-DD-marcus-analysis.md` (human report)
- `/root/clawd-main/memory/daily-analysis/YYYY-MM-DD-marcus-analysis.json` (machine format)
- `/root/clawd-main/alerts/active/[LEVEL]_TIMESTAMP_SERIES.json` (if alerts generated)

**Success indicators:**
- Exit code 0
- Analysis report created
- Alerts (if any) created

---

## Execution Order & Dependencies

```
Daily Timeline (UTC):
├── 01:00 — Job 2: FRED Fetch
│   └── Outputs: /data/fred/raw/
│
├── 02:00 — Job 1: Backup (runs independently)
│   └── Outputs: Local backup + GitHub sync
│
├── 02:00 — Job 3: Validation (waits for Job 2)
│   └── Depends on: /data/fred/raw/ files
│   └── Outputs: /telemetry/daily/YYYY-MM-DD/
│
└── 02:30 — Job 4: Marcus Analysis (waits for Jobs 2–3)
    ├── Depends on: /data/fred/raw/, /telemetry/daily/
    └── Outputs: /memory/daily-analysis/, /alerts/active/
```

**Key:** Job 4 runs last and requires all prior jobs to succeed.

---

## Monitoring & Health Checks

### Taylor's Responsibilities

Daily (automated via Job 5 — TBD):

```bash
# Check if previous day's jobs completed successfully
0 3 * * * /root/clawd-main/scripts/check_job_health.sh >> logs/job_health.log 2>&1
```

**Health check script** should verify:
- [ ] All 3 jobs completed (exit code 0)
- [ ] No errors in logs
- [ ] Output files exist and are recent (<24h old)
- [ ] Telemetry shows GREEN or YELLOW status

**If health check fails:**
- Alert Sentinel (escalate in TAYLOR-SOUL.md)
- Log issue in audit trail
- Disable problematic job until fixed

---

## Maintenance & Updates

### Adding a New Job

1. **Define in this file** (TAYLOR-CRON-DEFINITIONS.md)
2. **Create/test the script** (in `/scripts/`)
3. **Get approval from Sentinel** (if infrastructure-impacting)
4. **Schedule via crontab** or cron management tool
5. **Document in audit log** (git commit)

### Updating Existing Job

1. **Update script** (in `/scripts/`)
2. **Test independently** before changing cron
3. **Update this file** if timing/dependencies change
4. **Verify backward compatibility** (new script works with old data)
5. **Document change** (git commit with reason)

### Disabling a Job

If a job is failing repeatedly:

1. Comment out in crontab (don't delete)
2. Log reason in audit trail
3. Alert Sentinel
4. Investigate root cause
5. Fix and re-enable

---

## Logging & Audit Trail

All job output logged:

```
/root/clawd-main/logs/
├── backup.log               (Job 1)
├── fetch_fred.log          (Job 2)
├── validate_data.log       (Job 3)
├── marcus_analysis.log     (Job 4)
└── job_health.log          (Job 5 — TBD)
```

Logs rotated daily by Taylor (see TAYLOR-SOUL.md — Backup Protocol).

**Audit trail:** All jobs logged in git commits:
```bash
git log --oneline | grep "scheduled"
```

---

## Phase 2 & Beyond

**When adding NASEN and FMOC pipelines:**

```bash
# NASEN Pipeline (daily, similar to FRED)
0 1 * * * cd /root/clawd-main && /usr/bin/python3 scripts/fetch_nasen.py >> logs/fetch_nasen.log 2>&1

# FMOC Pipeline (8x yearly, on FOMC meeting dates)
0 15 28 * * [ $(date +%u) -eq 3 ] && cd /root/clawd-main && /usr/bin/python3 scripts/fetch_fmoc.py >> logs/fetch_fmoc.log 2>&1
```

---

## Current Status

**Phase 1 (FRED) jobs:**
- [ ] Job 1 (Backup) — Script TBD
- [ ] Job 2 (FRED Fetch) — Script ready: `scripts/fetch_fred.py` ✅
- [ ] Job 3 (Validation) — Script ready: `scripts/validate_data.py` ✅
- [ ] Job 4 (Analysis) — Script ready: `scripts/marcus_daily_analysis.py` ✅
- [ ] Job 5 (Health Check) — Script TBD

**Next steps:**
1. Create backup script (Taylor)
2. Create health check script (Taylor)
3. Test all scripts locally
4. Schedule cron jobs
5. Monitor for 3–7 days

---

## Important Notes

1. **Timezone:** All times are UTC. Adjust if needed for your timezone.

2. **Python path:** Use `/usr/bin/python3` (absolute path) in crontab.

3. **Working directory:** Use `cd /root/clawd-main &&` to ensure correct paths.

4. **Output redirection:** `>> logs/job.log 2>&1` captures stdout + stderr.

5. **Exit codes:**
   - 0 = success
   - non-zero = failure (cron will log in syslog)

6. **Cron format:** `MM HH DD MM DOW command`
   - MM = minute (0-59)
   - HH = hour (0-23)
   - DD = day of month (1-31)
   - MM = month (1-12)
   - DOW = day of week (0-6, 0=Sunday)

---

**Status:** Phase 1 jobs defined and ready  
**Owner:** Taylor (scheduling), Marcus (analysis)  
**Last updated:** 2026-01-22
