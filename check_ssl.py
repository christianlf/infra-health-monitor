#!/usr/bin/env python3
"""
SSL Certificate Checker
Monitors SSL/TLS certificates and alerts on expiration
"""

import sys
import os
import argparse
from tabulate import tabulate
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.checkers.ssl_checker import SSLChecker


def main():
    parser = argparse.ArgumentParser(description='Check SSL certificates')
    parser.add_argument('hosts', nargs='+', help='Hosts to check (e.g., google.com github.com)')
    parser.add_argument('--warning-days', type=int, default=30, help='Warning threshold in days (default: 30)')
    parser.add_argument('--critical-days', type=int, default=7, help='Critical threshold in days (default: 7)')
    
    args = parser.parse_args()
    
    print("🔒 SSL Certificate Monitor")
    print("=" * 80)
    print(f"Checking {len(args.hosts)} host(s)...\n")
    
    # Initialize checker
    checker = SSLChecker(
        warning_days=args.warning_days,
        critical_days=args.critical_days
    )
    
    # Check all hosts
    results = checker.check_multiple(args.hosts)
    
    # Format results
    table_data = []
    for host, result in results.items():
        if result['status'] == 'failed':
            status_icon = '❌'
            severity = result.get('severity', 'error').upper()
            days_remaining = 'N/A'
            expiry = 'N/A'
            issuer = 'N/A'
            message = result.get('error', 'Unknown error')
        else:
            cert = result.get('certificate', {})
            days = cert.get('days_remaining', 0)
            
            if days < 0:
                status_icon = '❌'
            elif days <= args.critical_days:
                status_icon = '🚨'
            elif days <= args.warning_days:
                status_icon = '⚠️'
            else:
                status_icon = '✅'
            
            severity = result.get('severity', 'ok').upper()
            days_remaining = f"{days} days"
            expiry = cert.get('expiry_date', 'N/A')
            issuer = cert.get('issuer', 'N/A')
            message = result.get('message', '')
        
        table_data.append([
            status_icon,
            host,
            severity,
            days_remaining,
            expiry,
            issuer,
            message
        ])
    
    # Print table
    headers = ['', 'Host', 'Status', 'Days Left', 'Expires', 'Issuer', 'Message']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Show expiring certificates
    expiring = checker.get_expiring_certificates(args.hosts, args.warning_days)
    
    if expiring:
        print("\n" + "=" * 80)
        print("⚠️  CERTIFICATES REQUIRING ATTENTION")
        print("=" * 80)
        
        for item in expiring:
            print(f"\n🔔 {item['host']}")
            if 'certificate' in item:
                cert = item['certificate']
                print(f"   Subject: {cert['subject']}")
                print(f"   Issuer: {cert['issuer']}")
                print(f"   Expires: {cert['expiry_date']} ({cert['days_remaining']} days)")
                if cert.get('san'):
                    print(f"   Alt Names: {', '.join(cert['san'][:3])}" + 
                          (f" (+{len(cert['san'])-3} more)" if len(cert['san']) > 3 else ""))
            else:
                print(f"   Error: {item.get('error', 'Unknown error')}")
    else:
        print("\n✅ All certificates are valid and not expiring soon.")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
