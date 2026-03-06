#!/usr/bin/env python3
"""
Marcus Daily Analysis - FRED Data Analysis and Signal Detection

Runs daily analysis on FRED data.
Detects anomalies, generates insights.
Part of Marcus's Phase 1 MVP.

Usage:
  python3 scripts/marcus_daily_analysis.py

Schedule:
  Daily via cron (Taylor manages): 02:30 UTC
  (After fetch_fred.py at 01:00 UTC and backup at 02:00 UTC)
"""

import json
import os
from datetime import datetime, timedelta
import statistics
import logging

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/marcus_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarcusAnalysis:
    """Daily analysis engine for Marcus."""
    
    def __init__(self):
        self.config_path = "config/fred-config.json"
        self.config = self._load_config()
        self.today = datetime.utcnow().strftime("%Y-%m-%d")
        self.analysis_results = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "date": self.today,
            "signals": [],
            "anomalies": [],
            "alerts": []
        }
    
    def _load_config(self):
        """Load configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def load_fred_data(self, data_dir="data/fred/raw"):
        """Load today's FRED data."""
        data = {}
        try:
            files = [f for f in os.listdir(data_dir) if f.startswith(self.today)]
            for filename in files:
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r') as f:
                    file_data = json.load(f)
                    series_id = file_data.get("series_id")
                    data[series_id] = file_data
            logger.info(f"Loaded {len(data)} FRED series")
        except Exception as e:
            logger.error(f"Error loading FRED data: {e}")
        
        return data
    
    def load_validation_results(self, validation_dir="telemetry/daily"):
        """Load validation results."""
        validation_file = os.path.join(validation_dir, self.today, "data-validation.json")
        try:
            with open(validation_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Validation file not found: {validation_file}")
            return None
        except Exception as e:
            logger.error(f"Error loading validation: {e}")
            return None
    
    def detect_anomalies(self, fred_data, validation_results):
        """Detect anomalies in FRED data."""
        if validation_results is None:
            return
        
        thresholds = self.config.get('fred', {}).get('anomaly_thresholds', {})
        zscore_critical = thresholds.get('zscore_critical', 3.0)
        zscore_warning = thresholds.get('zscore_warning', 2.0)
        
        for series_id, validation in validation_results.get('validations', {}).items():
            checks = validation.get('checks', {})
            zscore = checks.get('zscore')
            anomaly = checks.get('anomaly')
            
            if zscore is not None and abs(zscore) > zscore_warning:
                latest_value = checks.get('latest_value')
                
                anomaly_record = {
                    "series_id": series_id,
                    "value": latest_value,
                    "zscore": zscore,
                    "severity": "CRITICAL" if abs(zscore) > zscore_critical else "WARNING",
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                }
                
                self.analysis_results["anomalies"].append(anomaly_record)
                logger.warning(f"Anomaly detected: {series_id} zscore={zscore:.2f}")
    
    def generate_market_signals(self, fred_data):
        """Generate market intelligence signals from FRED data."""
        series_names = self.config.get('fred', {}).get('series', {})
        
        for series_id, data in fred_data.items():
            observations = data.get('observations', [])
            if len(observations) < 2:
                continue
            
            try:
                # Get last two values
                latest = float(observations[-1].get('value'))
                previous = float(observations[-2].get('value'))
                
                # Calculate change
                change = latest - previous
                change_pct = (change / previous * 100) if previous != 0 else 0
                
                series_name = series_names.get(series_id, {}).get('name', series_id)
                
                # Generate signal if meaningful change
                if abs(change_pct) > 0.5:  # More than 0.5% change
                    signal = {
                        "series_id": series_id,
                        "name": series_name,
                        "latest_value": latest,
                        "change": round(change, 4),
                        "change_pct": round(change_pct, 2),
                        "detected_at": datetime.utcnow().isoformat() + "Z"
                    }
                    self.analysis_results["signals"].append(signal)
                    logger.info(f"Signal: {series_id} {change_pct:+.2f}%")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse values for {series_id}: {e}")
    
    def generate_alerts(self):
        """Generate alerts from anomalies."""
        for anomaly in self.analysis_results["anomalies"]:
            severity = anomaly.get("severity", "WARNING")
            series_id = anomaly.get("series_id")
            zscore = anomaly.get("zscore")
            
            alert = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": severity,
                "title": f"Data Anomaly: {series_id}",
                "description": f"{series_id} shows unusual value (zscore={zscore:.2f})",
                "series_id": series_id,
                "zscore": zscore,
                "recommended_action": "Review FRED data for unusual economic indicators"
            }
            
            self.analysis_results["alerts"].append(alert)
    
    def write_analysis_report(self, output_dir="memory/daily-analysis"):
        """Write analysis report."""
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{self.today}-marcus-analysis.md")
        
        try:
            with open(filename, 'w') as f:
                f.write(f"# Marcus Daily Analysis — {self.today}\n\n")
                
                # Summary
                f.write("## Summary\n\n")
                f.write(f"- **Timestamp:** {self.analysis_results['timestamp']}\n")
                f.write(f"- **Signals detected:** {len(self.analysis_results['signals'])}\n")
                f.write(f"- **Anomalies detected:** {len(self.analysis_results['anomalies'])}\n")
                f.write(f"- **Alerts generated:** {len(self.analysis_results['alerts'])}\n\n")
                
                # Signals
                if self.analysis_results["signals"]:
                    f.write("## Market Signals\n\n")
                    for signal in self.analysis_results["signals"]:
                        f.write(f"### {signal.get('name', signal.get('series_id'))}\n\n")
                        f.write(f"- **Series ID:** {signal.get('series_id')}\n")
                        f.write(f"- **Latest Value:** {signal.get('latest_value')}\n")
                        f.write(f"- **Change:** {signal.get('change_pct'):+.2f}%\n")
                        f.write(f"- **Detected:** {signal.get('detected_at')}\n\n")
                
                # Anomalies
                if self.analysis_results["anomalies"]:
                    f.write("## Anomalies Detected\n\n")
                    for anomaly in self.analysis_results["anomalies"]:
                        severity = anomaly.get("severity", "UNKNOWN")
                        f.write(f"### [{severity}] {anomaly.get('series_id')}\n\n")
                        f.write(f"- **Value:** {anomaly.get('value')}\n")
                        f.write(f"- **Z-Score:** {anomaly.get('zscore'):.2f}\n")
                        f.write(f"- **Detected:** {anomaly.get('detected_at')}\n\n")
                
                # Alerts
                if self.analysis_results["alerts"]:
                    f.write("## Alerts for Sentinel\n\n")
                    for alert in self.analysis_results["alerts"]:
                        f.write(f"### [{alert.get('level')}] {alert.get('title')}\n\n")
                        f.write(f"- **Description:** {alert.get('description')}\n")
                        f.write(f"- **Action:** {alert.get('recommended_action')}\n")
                        f.write(f"- **Time:** {alert.get('timestamp')}\n\n")
                
                f.write("---\n")
                f.write(f"*Report generated by Marcus at {datetime.utcnow().isoformat()}Z*\n")
            
            logger.info(f"Analysis report written: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error writing report: {e}")
            return False
    
    def write_json_output(self, output_dir="memory/daily-analysis"):
        """Write JSON output for machine consumption."""
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"{self.today}-marcus-analysis.json")
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.analysis_results, f, indent=2)
            logger.info(f"JSON output written: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error writing JSON: {e}")
            return False
    
    def create_alerts_for_sentinel(self):
        """Create alert files for Sentinel to consume."""
        alerts_dir = "alerts/active"
        os.makedirs(alerts_dir, exist_ok=True)
        
        for alert in self.analysis_results["alerts"]:
            severity = alert.get("level", "INFO")
            series_id = alert.get("series_id", "unknown")
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            
            filename = os.path.join(alerts_dir, f"{severity}_{timestamp}_{series_id}.json")
            
            alert_payload = {
                "id": f"{timestamp}_{series_id}",
                "timestamp": alert.get("timestamp"),
                "level": severity,
                "title": alert.get("title"),
                "description": alert.get("description"),
                "source": "marcus",
                "affected_systems": ["market-intelligence"],
                "recommended_action": alert.get("recommended_action"),
                "escalation_target": "sentinel",
                "state": "active",
                "resolved_at": None
            }
            
            try:
                with open(filename, 'w') as f:
                    json.dump(alert_payload, f, indent=2)
                logger.info(f"Alert file created: {filename}")
            except Exception as e:
                logger.error(f"Error creating alert: {e}")

def main():
    """Run daily analysis."""
    logger.info("Starting Marcus daily analysis...")
    
    analysis = MarcusAnalysis()
    
    # Load data
    fred_data = analysis.load_fred_data()
    validation_results = analysis.load_validation_results()
    
    # Analyze
    analysis.detect_anomalies(fred_data, validation_results)
    analysis.generate_market_signals(fred_data)
    analysis.generate_alerts()
    
    # Output
    analysis.write_analysis_report()
    analysis.write_json_output()
    analysis.create_alerts_for_sentinel()
    
    # Summary
    logger.info(f"Analysis complete: {len(analysis.analysis_results['signals'])} signals, "
                f"{len(analysis.analysis_results['anomalies'])} anomalies, "
                f"{len(analysis.analysis_results['alerts'])} alerts")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
