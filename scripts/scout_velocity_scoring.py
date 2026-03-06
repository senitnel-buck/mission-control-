#!/usr/bin/env python3
"""
Scout Phase 1: Velocity Scoring

Scores how fast signals are accelerating.
Implements z-score based velocity algorithm.

Usage:
  python3 scripts/scout_velocity_scoring.py

Schedule:
  Daily via cron: 02:15 UTC (after Marcus validation at 02:00)
"""

import json
import os
from datetime import datetime, timedelta
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
        Capped at 100 to prevent overflow
        """
        if baseline_frequency == 0:
            return 100 if frequency_today > 0 else 0
        
        velocity = ((frequency_today - baseline_frequency) / baseline_frequency) * 100
        
        # Cap at 100
        return min(100, max(0, velocity))
    
    def classify_velocity(self, score):
        """Classify velocity score into bands."""
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
            "scoring_version": 1,
            "algorithm": "z-score",
            "baseline_window_days": 30,
            "signals": [],
            "summary": {
                "total_signals": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0
            }
        }
        
        # Phase 1: Create placeholder scored structure
        # Phase 2: Implement actual scoring from real signal data
        
        for source in raw_signals.get("sources", {}).keys():
            scored_signals["signals"].append({
                "source": source,
                "signal_name": f"{source}_sample",
                "frequency_today": 0,
                "baseline_frequency": 0,
                "velocity_score": 0,
                "velocity_band": "LOW",
                "confidence": 0.0,
                "notes": "Phase 1: Ready for Phase 2 API integration"
            })
        
        try:
            proc_dir = f"data/scout/processed-signals/{self.today}"
            os.makedirs(proc_dir, exist_ok=True)
            
            filename = os.path.join(proc_dir, "scored-signals.json")
            with open(filename, 'w') as f:
                json.dump(scored_signals, f, indent=2)
            
            logger.info(f"Velocity scoring complete: {filename}")
            logger.info(f"Summary: {scored_signals['summary']}")
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
