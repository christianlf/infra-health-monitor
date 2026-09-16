#!/usr/bin/env python3
"""
Infrastructure Health Monitor - Main CLI Application
Monitors health of IT infrastructure and generates reports.
"""

import sys
import time
import logging
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Import project modules
from src.config import config
from src.checkers.ping_checker import PingChecker
from src.checkers.port_checker import PortChecker
from src.checkers.http_checker import HTTPChecker
from src.storage.database import Database
from src.alerts.alert_manager import AlertManager
from src.reports.report_generator import ReportGenerator


def setup_logging(log_level: str = 'INFO') -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('health_monitor.log'),
            logging.StreamHandler()
        ]
    )


def load_targets(targets_file: str = 'targets.yaml') -> List[Dict[str, Any]]:
    """
    Load monitoring targets from YAML file.
    
    Args:
        targets_file: Path to targets configuration file
        
    Returns:
        List of target configurations
    """
    try:
        with open(targets_file, 'r') as f:
            data = yaml.safe_load(f)
            targets = [t for t in data.get('targets', []) if t.get('enabled', True)]
            logging.info(f"Loaded {len(targets)} enabled targets from {targets_file}")
            return targets
    except FileNotFoundError:
        logging.error(f"Targets file not found: {targets_file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing targets file: {e}")
        sys.exit(1)


def perform_check(target: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """
    Perform health check on a single target.
    
    Args:
        target: Target configuration dictionary
        timeout: Timeout for check in seconds
        
    Returns:
        Check result dictionary
    """
    target_type = target.get('type', '').lower()
    target_name = target.get('name', 'Unknown')
    
    result = {
        'target_name': target_name,
        'target_type': target_type,
        'status': 'fail',
        'response_time_ms': None,
        'error': 'Unknown error'
    }
    
    try:
        if target_type == 'ping':
            checker = PingChecker(timeout=timeout)
            check_result = checker.check(target.get('host', ''))
            result.update(check_result)
            
        elif target_type == 'port':
            checker = PortChecker(timeout=timeout)
            check_result = checker.check(
                target.get('host', ''),
                target.get('port', 0)
            )
            result.update(check_result)
            
        elif target_type == 'http':
            checker = HTTPChecker(timeout=timeout)
            check_result = checker.check(
                target.get('url', ''),
                target.get('expected_status', 200)
            )
            result.update(check_result)
            if 'http_status' in check_result:
                result['http_status'] = check_result['http_status']
            
        else:
            result['error'] = f"Unknown target type: {target_type}"
            
    except Exception as e:
        logging.error(f"Error checking {target_name}: {e}")
        result['error'] = str(e)
    
    return result


def run_checks(targets: List[Dict[str, Any]], db: Database, alert_manager: AlertManager) -> List[Dict[str, Any]]:
    """
    Run health checks on all targets.
    
    Args:
        targets: List of target configurations
        db: Database instance
        alert_manager: AlertManager instance
        
    Returns:
        List of check results
    """
    results = []
    timeout = config.default_timeout
    
    for target in targets:
        target_name = target.get('name', 'Unknown')
        logging.info(f"Checking: {target_name}")
        
        result = perform_check(target, timeout)
        results.append(result)
        
        # Save to database
        db.save_check(
            target_name=result['target_name'],
            target_type=result['target_type'],
            status=result['status'],
            response_time_ms=result.get('response_time_ms'),
            error=result.get('error')
        )
        
        # Check for alerts
        if result['status'] == 'fail':
            consecutive_failures = db.get_consecutive_failures(target_name)
            
            metadata = {}
            if 'host' in target:
                metadata['host'] = target['host']
            if 'port' in target:
                metadata['port'] = target['port']
            if 'url' in target:
                metadata['url'] = target['url']
            
            alert_triggered = alert_manager.check_and_alert(
                target_name=target_name,
                target_type=result['target_type'],
                consecutive_failures=consecutive_failures,
                last_error=result.get('error'),
                metadata=metadata
            )
            
            if alert_triggered:
                logging.warning(f"Alert triggered for {target_name}")
        else:
            # Check if this is a recovery (previous check was failure)
            recent_checks = db.get_recent_checks(target_name=target_name, hours=1, limit=2)
            if len(recent_checks) >= 2 and recent_checks[1]['status'] == 'fail':
                alert_manager.log_recovery(target_name, result['target_type'])
    
    return results


def display_results(results: List[Dict[str, Any]]) -> None:
    """
    Display check results in formatted table.
    
    Args:
        results: List of check results
    """
    table_data = []
    
    for result in results:
        status = result.get('status', 'unknown')
        
        if status == 'ok':
            status_display = f"{Fore.GREEN}✓ OK{Style.RESET_ALL}"
            response_time = result.get('response_time_ms', 0)
            
            if response_time and response_time > 1000:
                response_display = f"{Fore.YELLOW}{response_time:.2f}ms{Style.RESET_ALL}"
            else:
                response_display = f"{response_time:.2f}ms" if response_time else "N/A"
        else:
            status_display = f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
            response_display = "N/A"
        
        table_data.append([
            result.get('target_name', 'Unknown'),
            result.get('target_type', 'unknown'),
            status_display,
            response_display,
            result.get('error', '') or ''
        ])
    
    headers = ['Target', 'Type', 'Status', 'Response Time', 'Error']
    print("\n" + tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Summary
    total = len(results)
    successful = sum(1 for r in results if r.get('status') == 'ok')
    failed = total - successful
    
    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"  Total: {total}")
    print(f"  {Fore.GREEN}Successful: {successful}{Style.RESET_ALL}")
    print(f"  {Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    print(f"  Success Rate: {(successful/total*100):.1f}%" if total > 0 else "  Success Rate: N/A")
    print()


def command_check(args) -> None:
    """Execute single check command."""
    logging.info("Starting health check")
    
    targets = load_targets(args.targets)
    db = Database(config.database_path)
    alert_manager = AlertManager(config.alert_log_path, config.alert_threshold)
    
    results = run_checks(targets, db, alert_manager)
    display_results(results)
    
    logging.info("Health check completed")


def command_monitor(args) -> None:
    """Execute continuous monitoring command."""
    interval = args.interval
    logging.info(f"Starting continuous monitoring (interval: {interval}s)")
    
    targets = load_targets(args.targets)
    db = Database(config.database_path)
    alert_manager = AlertManager(config.alert_log_path, config.alert_threshold)
    
    print(f"{Fore.CYAN}Continuous monitoring started. Press Ctrl+C to stop.{Style.RESET_ALL}\n")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{Fore.YELLOW}=== Check Iteration {iteration} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==={Style.RESET_ALL}")
            
            results = run_checks(targets, db, alert_manager)
            display_results(results)
            
            print(f"{Fore.CYAN}Next check in {interval} seconds...{Style.RESET_ALL}")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Monitoring stopped by user.{Style.RESET_ALL}")
        logging.info("Monitoring stopped by user")


def command_report(args) -> None:
    """Execute report generation command."""
    logging.info(f"Generating report (format: {args.format}, period: {args.last})")
    
    db = Database(config.database_path)
    
    # Parse time period
    hours = 24
    if args.last:
        last = args.last.lower()
        if last.endswith('h'):
            hours = int(last[:-1])
        elif last.endswith('d'):
            hours = int(last[:-1]) * 24
        else:
            logging.error(f"Invalid time period format: {args.last}")
            print(f"{Fore.RED}Error: Invalid time period. Use format like '24h' or '7d'{Style.RESET_ALL}")
            return
    
    # Retrieve data
    data = db.get_recent_checks(hours=hours)
    
    if not data:
        print(f"{Fore.YELLOW}No data found for the specified period.{Style.RESET_ALL}")
        return
    
    print(f"{Fore.CYAN}Generating report with {len(data)} records...{Style.RESET_ALL}")
    
    # Generate report
    report_gen = ReportGenerator()
    
    try:
        if args.format == 'csv':
            filepath = report_gen.generate_csv(data)
            print(f"{Fore.GREEN}CSV report generated: {filepath}{Style.RESET_ALL}")
            
        elif args.format == 'json':
            filepath = report_gen.generate_json(data)
            print(f"{Fore.GREEN}JSON report generated: {filepath}{Style.RESET_ALL}")
            
        elif args.format == 'summary':
            filepath = report_gen.generate_summary(data)
            print(f"{Fore.GREEN}Summary report generated: {filepath}{Style.RESET_ALL}")
            
        elif args.format == 'all':
            results = report_gen.generate_all_formats(data)
            print(f"{Fore.GREEN}All report formats generated:{Style.RESET_ALL}")
            for fmt, path in results.items():
                print(f"  {fmt}: {path}")
        
        # Display statistics
        stats = db.get_statistics(hours=hours)
        print(f"\n{Fore.CYAN}Statistics for last {hours}h:{Style.RESET_ALL}")
        print(f"  Total Checks: {stats['total']}")
        print(f"  Successful: {stats['success']}")
        print(f"  Failed: {stats['failure']}")
        print(f"  Success Rate: {stats['success_rate']:.2f}%")
        if stats['avg_response_time_ms']:
            print(f"  Avg Response Time: {stats['avg_response_time_ms']:.2f}ms")
        print()
        
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        print(f"{Fore.RED}Error generating report: {e}{Style.RESET_ALL}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Infrastructure Health Monitor - Monitor and report on infrastructure health',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py check                          # Run single health check
  python main.py monitor --interval 60          # Monitor every 60 seconds
  python main.py report --format csv --last 24h # Generate CSV report for last 24 hours
  python main.py report --format all --last 7d  # Generate all reports for last 7 days
        """
    )
    
    parser.add_argument(
        '--targets',
        default='targets.yaml',
        help='Path to targets configuration file (default: targets.yaml)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check command
    parser_check = subparsers.add_parser('check', help='Run single health check on all targets')
    parser_check.set_defaults(func=command_check)
    
    # Monitor command
    parser_monitor = subparsers.add_parser('monitor', help='Run continuous monitoring')
    parser_monitor.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser_monitor.set_defaults(func=command_monitor)
    
    # Report command
    parser_report = subparsers.add_parser('report', help='Generate health report')
    parser_report.add_argument(
        '--format',
        choices=['csv', 'json', 'summary', 'all'],
        default='summary',
        help='Report format (default: summary)'
    )
    parser_report.add_argument(
        '--last',
        default='24h',
        help='Time period (e.g., 24h, 7d) (default: 24h)'
    )
    parser_report.set_defaults(func=command_report)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(config.log_level)
    
    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
