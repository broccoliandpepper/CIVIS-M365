#!/usr/bin/env python
"""Test script for SOC analysis engine"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.soc_service import SOCService
from app.database import get_db_hot

def test_soc_analysis():
    print("Testing SOC Analysis Engine...")

    try:
        db = next(get_db_hot())
        result = SOCService.run_analysis(db, 'today')
        print("✅ SOC Analysis completed successfully!")
        print(f"   Status: {result.get('status')}")
        print(f"   Anomalies detected: {result.get('anomalies_detected', 0)}")
        print(f"   Anomalies saved: {result.get('anomalies_saved', 0)}")

        # Test summary
        summary = SOCService.get_executive_summary(db, 'today')
        print("\n📊 Executive Summary:")
        print(f"   Total anomalies: {summary.get('total_anomalies', 0)}")
        print(f"   Critical: {summary.get('critical_count', 0)}")
        print(f"   High: {summary.get('high_count', 0)}")
        print(f"   Total sign-ins: {summary.get('total_signins', 0)}")
        print(f"   Out-of-list sign-ins: {summary.get('out_of_list_signins', 0)}")

        return True

    except Exception as e:
        print(f"❌ SOC Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_soc_analysis()