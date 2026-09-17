#!/usr/bin/env python3
"""
Failure Prediction Tool
Uses Machine Learning to predict potential infrastructure failures
"""

import sys
import os
from tabulate import tabulate

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.storage.database import Database
from src.ml.failure_predictor import FailurePredictor
from src.config import Config


def main():
    print("🤖 AI-Powered Failure Prediction")
    print("=" * 60)
    
    # Load config and initialize
    config = Config()
    database = Database(config.database_path)
    predictor = FailurePredictor(database)
    
    # Run predictions
    print("\n📊 Analyzing all targets...\n")
    predictions = predictor.predict_all_targets()
    
    # Format results
    table_data = []
    for target, pred in predictions.items():
        risk_emoji = {
            'low': '✅',
            'medium': '⚡',
            'high': '⚠️',
            'unknown': '❓'
        }.get(pred['risk_level'], '❓')
        
        confidence_percent = f"{pred['confidence']*100:.0f}%"
        
        table_data.append([
            risk_emoji,
            target,
            pred['risk_level'].upper(),
            confidence_percent,
            pred['prediction']
        ])
    
    # Print table
    headers = ['', 'Target', 'Risk Level', 'Confidence', 'Prediction']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Show high-risk targets
    high_risk = predictor.get_high_risk_targets()
    if high_risk:
        print("\n" + "=" * 60)
        print("⚠️  HIGH RISK TARGETS - IMMEDIATE ATTENTION REQUIRED")
        print("=" * 60)
        
        for item in high_risk:
            print(f"\n🚨 {item['target']}")
            print(f"   Risk: {item['risk_level'].upper()} (confidence: {item['confidence']*100:.0f}%)")
            print(f"   Prediction: {item['prediction']}")
            if item['indicators']:
                print(f"   Indicators:")
                for indicator in item['indicators']:
                    print(f"     • {indicator}")
    else:
        print("\n✅ No high-risk targets detected. All systems stable.")
    
    print("\n" + "=" * 60)
    print("💡 Tip: Run 'python main.py monitor' to continue real-time monitoring")


if __name__ == '__main__':
    main()
