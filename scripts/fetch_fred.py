#!/usr/bin/env python3
"""
FRED Data Pipeline - Fetch Federal Reserve Economic Data

Pulls FRED data for key economic indicators.
Part of Marcus's Phase 1 MVP.

Usage:
  python3 scripts/fetch_fred.py

Schedule:
  Daily via cron (Taylor manages): 01:00 UTC
"""

import requests
import json
import os
from datetime import datetime
import logging

# Configuration
CONFIG_PATH = "config/fred-config.json"
DATA_DIR = "data/fred/raw"
TELEMETRY_DIR = "telemetry/daily"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fetch_fred.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load FRED configuration."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_PATH}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {CONFIG_PATH}")
        raise

def fetch_series(api_key, series_id):
    """Fetch a single FRED series."""
    endpoint = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json"
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching {series_id}: {e}")
        return None

def save_raw_data(series_id, data):
    """Save raw FRED data to file."""
    if data is None:
        return False
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = os.path.join(DATA_DIR, f"{today}_{series_id}.json")
    
    payload = {
        "series_id": series_id,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "data_date": today,
        "observations": data.get("observations", []),
        "processing_version": 1
    }
    
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Saved: {filename}")
        return True
    except IOError as e:
        logger.error(f"Error saving {filename}: {e}")
        return False

def write_telemetry(config, fetch_results):
    """Write telemetry for Marcus to consume."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    telemetry_dir = os.path.join(TELEMETRY_DIR, today)
    os.makedirs(telemetry_dir, exist_ok=True)
    
    # Count successful/failed fetches
    successful = sum(1 for v in fetch_results.values() if v)
    failed = len(fetch_results) - successful
    
    telemetry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "fred",
        "status": "healthy" if failed == 0 else ("degraded" if failed < len(fetch_results) else "critical"),
        "metrics": {
            "total_series": len(fetch_results),
            "successful_fetches": successful,
            "failed_fetches": failed,
            "success_rate": successful / len(fetch_results) if fetch_results else 0
        },
        "notes": f"Fetched {successful} of {len(fetch_results)} FRED series"
    }
    
    if failed > 0:
        telemetry["failures"] = [k for k, v in fetch_results.items() if not v]
    
    filename = os.path.join(telemetry_dir, "fred-health.json")
    try:
        with open(filename, 'w') as f:
            json.dump(telemetry, f, indent=2)
        logger.info(f"Telemetry written: {filename}")
    except IOError as e:
        logger.error(f"Error writing telemetry: {e}")

def main():
    """Main fetch routine."""
    logger.info("Starting FRED data fetch...")
    
    # Load config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return False
    
    api_key = config['fred']['api_key']
    if api_key == "YOUR_FRED_API_KEY_HERE":
        logger.error("FRED API key not configured. Set it in config/fred-config.json")
        return False
    
    series_list = config['fred']['series']
    fetch_results = {}
    
    # Fetch each series
    logger.info(f"Fetching {len(series_list)} FRED series...")
    for series_id in series_list.keys():
        logger.info(f"Fetching {series_id}...")
        data = fetch_series(api_key, series_id)
        success = save_raw_data(series_id, data) if data else False
        fetch_results[series_id] = success
    
    # Write telemetry for Marcus
    write_telemetry(config, fetch_results)
    
    # Summary
    successful = sum(1 for v in fetch_results.values() if v)
    logger.info(f"FRED fetch complete: {successful}/{len(fetch_results)} successful")
    
    return successful == len(fetch_results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
