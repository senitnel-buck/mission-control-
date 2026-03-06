#!/usr/bin/env python3
"""
Data Quality Validation - Validate FRED and other data sources

Checks data freshness, schema, outliers, completeness.
Part of Marcus's Phase 1 MVP.

Usage:
  python3 scripts/validate_data.py

Called by: marcus_daily_analysis.py
"""

import json
import os
from datetime import datetime, timedelta
import statistics
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates data quality across pipelines."""
    
    def __init__(self):
        self.config_path = "config/fred-config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def validate_fred_data(self, data_dir="data/fred/raw"):
        """Validate FRED data quality."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "fred",
            "validations": {},
            "quality_tier": "GREEN"
        }
        
        # Find today's FRED files
        try:
            files = [f for f in os.listdir(data_dir) if f.startswith(today)]
        except FileNotFoundError:
            logger.warning(f"Data directory not found: {data_dir}")
            results["quality_tier"] = "RED"
            results["notes"] = "Data directory not found"
            return results
        
        if not files:
            logger.warning(f"No data files for today ({today})")
            results["quality_tier"] = "YELLOW"
            results["notes"] = "No data files found for today"
            return results
        
        # Validate each file
        for filename in files:
            filepath = os.path.join(data_dir, filename)
            validation = self._validate_fred_file(filepath)
            series_id = validation.get("series_id", filename)
            results["validations"][series_id] = validation
            
            # Downgrade quality tier if any validation fails
            if validation.get("status") == "RED":
                results["quality_tier"] = "RED"
            elif validation.get("status") == "YELLOW" and results["quality_tier"] != "RED":
                results["quality_tier"] = "YELLOW"
        
        return results
    
    def _validate_fred_file(self, filepath):
        """Validate a single FRED data file."""
        result = {
            "file": os.path.basename(filepath),
            "status": "GREEN",
            "checks": {}
        }
        
        # Load file
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return {**result, "status": "RED", "error": str(e)}
        
        result["series_id"] = data.get("series_id", "unknown")
        observations = data.get("observations", [])
        
        # Check 1: Data exists
        if not observations:
            result["checks"]["data_exists"] = False
            result["status"] = "RED"
        else:
            result["checks"]["data_exists"] = True
            result["checks"]["observation_count"] = len(observations)
        
        # Check 2: Schema validation
        if observations:
            required_fields = ["date", "value"]
            first_obs = observations[0]
            schema_valid = all(field in first_obs for field in required_fields)
            result["checks"]["schema_valid"] = schema_valid
            if not schema_valid:
                result["status"] = "RED" if result["status"] == "GREEN" else result["status"]
        
        # Check 3: Recency (data should be recent)
        if observations:
            latest_date = observations[-1].get("date", "")
            result["checks"]["latest_date"] = latest_date
            
            try:
                latest = datetime.strptime(latest_date, "%Y-%m-%d")
                now = datetime.utcnow()
                days_old = (now - latest).days
                
                if days_old > 7:
                    result["checks"]["freshness"] = f"STALE ({days_old} days old)"
                    if result["status"] == "GREEN":
                        result["status"] = "YELLOW"
                elif days_old > 30:
                    result["checks"]["freshness"] = f"VERY_STALE ({days_old} days old)"
                    result["status"] = "RED"
                else:
                    result["checks"]["freshness"] = "CURRENT"
            except Exception as e:
                logger.warning(f"Could not parse date {latest_date}: {e}")
        
        # Check 4: Outlier detection (z-score)
        if observations and len(observations) > 5:
            try:
                # Extract numeric values
                values = []
                for obs in observations[-30:]:  # Last 30 observations
                    try:
                        val = float(obs.get("value"))
                        if val is not None:
                            values.append(val)
                    except (ValueError, TypeError):
                        pass
                
                if len(values) > 5:
                    mean = statistics.mean(values)
                    stdev = statistics.stdev(values)
                    
                    latest_value = values[-1]
                    zscore = (latest_value - mean) / stdev if stdev > 0 else 0
                    
                    result["checks"]["latest_value"] = latest_value
                    result["checks"]["zscore"] = round(zscore, 2)
                    
                    if abs(zscore) > 3.0:
                        result["checks"]["anomaly"] = "CRITICAL"
                        if result["status"] == "GREEN":
                            result["status"] = "YELLOW"  # Flag for review but not a data quality issue
                    elif abs(zscore) > 2.0:
                        result["checks"]["anomaly"] = "WARNING"
            except Exception as e:
                logger.warning(f"Could not compute z-score: {e}")
        
        return result
    
    def write_validation_report(self, validation_results, output_dir="telemetry/daily"):
        """Write validation results to file."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        report_dir = os.path.join(output_dir, today)
        os.makedirs(report_dir, exist_ok=True)
        
        filename = os.path.join(report_dir, "data-validation.json")
        try:
            with open(filename, 'w') as f:
                json.dump(validation_results, f, indent=2)
            logger.info(f"Validation report written: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error writing validation report: {e}")
            return False

def main():
    """Run validation."""
    validator = DataValidator()
    results = validator.validate_fred_data()
    validator.write_validation_report(results)
    
    # Log summary
    overall = results.get("quality_tier", "UNKNOWN")
    logger.info(f"Data quality: {overall}")
    
    if overall == "RED":
        logger.warning("Data quality RED - anomalies detected")
    elif overall == "YELLOW":
        logger.warning("Data quality YELLOW - minor issues detected")
    else:
        logger.info("Data quality GREEN - all checks passed")
    
    return overall != "RED"

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
