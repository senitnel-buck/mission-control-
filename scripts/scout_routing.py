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

Schedule:
  Daily via cron: 02:45 UTC (after Marcus analysis at 02:30)
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
    
    ROUTING_MAP = {
        "macro": "marcus",
        "market": "marcus",
        "crypto": "marcus",
        "economic": "marcus",
        "narrative": "sterling",
        "content": "sterling",
        "meme": "sterling",
        "social": "sterling",
        "security": "aegis",
        "risk": "aegis",
        "governance": "aegis",
        "policy": "aegis",
        "infrastructure": "taylor",
        "platform": "taylor",
        "reliability": "taylor",
        "cross-domain": "sentinel",
        "strategic": "sentinel",
        "regime-shift": "sentinel"
    }
    
    def __init__(self):
        self.today = datetime.utcnow().strftime("%Y-%m-%d")
    
    def route_signal(self, signal):
        """Determine destination agent(s) for signal."""
        
        signal_type = signal.get("type", "strategic")
        velocity = signal.get("velocity_band", "LOW")
        
        primary_route = self.ROUTING_MAP.get(signal_type, "sentinel")
        
        destinations = [primary_route]
        
        # CRITICAL velocity always routes to Sentinel too
        if velocity == "CRITICAL":
            if primary_route != "sentinel":
                destinations.append("sentinel")
        
        return destinations
    
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
            "routing_summary": {
                "total_signals": len(scored_signals.get("signals", [])),
                "routed_to_marcus": 0,
                "routed_to_sterling": 0,
                "routed_to_aegis": 0,
                "routed_to_taylor": 0,
                "routed_to_sentinel": 0
            },
            "routing": []
        }
        
        # Route each signal
        for signal in scored_signals.get("signals", []):
            destinations = self.route_signal(signal)
            
            routed_entry = {
                "signal_id": signal.get("signal_name", "unknown"),
                "velocity_band": signal.get("velocity_band", "LOW"),
                "destinations": destinations
            }
            
            routed_signals["routing"].append(routed_entry)
            
            # Update routing summary
            for dest in destinations:
                key = f"routed_to_{dest}"
                if key in routed_signals["routing_summary"]:
                    routed_signals["routing_summary"][key] += 1
        
        try:
            filename = os.path.join(proc_dir, "routed-signals.json")
            with open(filename, 'w') as f:
                json.dump(routed_signals, f, indent=2)
            
            logger.info(f"Routing complete: {filename}")
            logger.info(f"Summary: {routed_signals['routing_summary']}")
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
