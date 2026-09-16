"""
Report Generator - Export health check data to various formats.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates reports from health check data in multiple formats."""
    
    def __init__(self, output_dir: str = "reports") -> None:
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save report files
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()
        
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Report output directory: {self.output_dir}")
    
    def generate_csv(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate CSV report from check data.
        
        Args:
            data: List of check records
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to generated CSV file
        """
        if not data:
            logger.warning("No data provided for CSV report")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"health_report_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                # Get all unique keys from data
                fieldnames = list(data[0].keys())
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"CSV report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            raise
    
    def generate_json(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """
        Generate JSON report from check data.
        
        Args:
            data: List of check records
            filename: Custom filename (auto-generated if None)
            pretty: Format JSON with indentation
            
        Returns:
            Path to generated JSON file
        """
        if not data:
            logger.warning("No data provided for JSON report")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"health_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as jsonfile:
                if pretty:
                    json.dump(data, jsonfile, indent=2, default=str)
                else:
                    json.dump(data, jsonfile, default=str)
            
            logger.info(f"JSON report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")
            raise
    
    def generate_summary(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Generate human-readable summary report.
        
        Args:
            data: List of check records
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to generated summary file
        """
        if not data:
            logger.warning("No data provided for summary report")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"health_summary_{timestamp}.txt"
        
        filepath = self.output_dir / filename
        
        try:
            # Calculate statistics
            total_checks = len(data)
            successful = sum(1 for d in data if d.get('status') == 'ok')
            failed = total_checks - successful
            
            # Group by target
            targets = {}
            for record in data:
                target = record.get('target_name', 'Unknown')
                if target not in targets:
                    targets[target] = {'ok': 0, 'fail': 0, 'response_times': []}
                
                status = record.get('status', 'fail')
                targets[target][status] += 1
                
                if status == 'ok' and record.get('response_time_ms'):
                    targets[target]['response_times'].append(record['response_time_ms'])
            
            # Write summary
            with open(filepath, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("INFRASTRUCTURE HEALTH MONITORING SUMMARY\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Checks: {total_checks}\n")
                f.write(f"Successful: {successful} ({successful/total_checks*100:.1f}%)\n")
                f.write(f"Failed: {failed} ({failed/total_checks*100:.1f}%)\n\n")
                
                f.write("-" * 70 + "\n")
                f.write("TARGET BREAKDOWN\n")
                f.write("-" * 70 + "\n\n")
                
                for target, stats in sorted(targets.items()):
                    total = stats['ok'] + stats['fail']
                    success_rate = (stats['ok'] / total * 100) if total > 0 else 0
                    
                    f.write(f"Target: {target}\n")
                    f.write(f"  Total Checks: {total}\n")
                    f.write(f"  Success: {stats['ok']} ({success_rate:.1f}%)\n")
                    f.write(f"  Failed: {stats['fail']}\n")
                    
                    if stats['response_times']:
                        avg_response = sum(stats['response_times']) / len(stats['response_times'])
                        min_response = min(stats['response_times'])
                        max_response = max(stats['response_times'])
                        f.write(f"  Avg Response Time: {avg_response:.2f}ms\n")
                        f.write(f"  Min/Max Response: {min_response:.2f}ms / {max_response:.2f}ms\n")
                    
                    f.write("\n")
                
                f.write("=" * 70 + "\n")
            
            logger.info(f"Summary report generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise
    
    def generate_all_formats(
        self,
        data: List[Dict[str, Any]],
        base_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate reports in all formats (CSV, JSON, Summary).
        
        Args:
            data: List of check records
            base_name: Base filename (timestamp added automatically)
            
        Returns:
            Dictionary mapping format to file path
        """
        if not data:
            logger.warning("No data provided for report generation")
            return {}
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base = base_name or "health_report"
        
        results = {}
        
        try:
            results['csv'] = self.generate_csv(data, f"{base}_{timestamp}.csv")
            results['json'] = self.generate_json(data, f"{base}_{timestamp}.json")
            results['summary'] = self.generate_summary(data, f"{base}_summary_{timestamp}.txt")
            
            logger.info(f"All report formats generated successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            return results
