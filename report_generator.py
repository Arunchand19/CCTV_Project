import json
import pandas as pd
from pathlib import Path
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def load_results(self):
        """Load all analysis results"""
        results = {}
        
        # Load CSV files
        if (self.output_dir / 'customer_positions.csv').exists():
            results['positions'] = pd.read_csv(self.output_dir / 'customer_positions.csv')
        
        if (self.output_dir / 'footfall.csv').exists():
            results['footfall'] = pd.read_csv(self.output_dir / 'footfall.csv')
        
        if (self.output_dir / 'dwell_times.csv').exists():
            results['dwell_times'] = pd.read_csv(self.output_dir / 'dwell_times.csv')
        
        # Load JSON
        if (self.output_dir / 'insights.json').exists():
            with open(self.output_dir / 'insights.json', 'r') as f:
                results['insights'] = json.load(f)
        
        return results
    
    def generate_html_report(self, results):
        """Generate HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Store Intelligence Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px;
        }}
        .section {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
            min-width: 200px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
        }}
        .metric-label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        .recommendation {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Store Intelligence Analytics Report</h1>
        <p>Generated on: {self.timestamp}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric">
            <div class="metric-value">{results.get('insights', {}).get('total_detections', 0)}</div>
            <div class="metric-label">Total Detections</div>
        </div>
        <div class="metric">
            <div class="metric-value">{results.get('insights', {}).get('zones_analyzed', 0)}</div>
            <div class="metric-label">Zones Analyzed</div>
        </div>
        <div class="metric">
            <div class="metric-value">{results.get('insights', {}).get('avg_dwell_time', 0):.1f}s</div>
            <div class="metric-label">Avg Dwell Time</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Zone Performance</h2>
        <p><strong>Peak Traffic Zone:</strong> {results.get('insights', {}).get('peak_zone', 'N/A')}</p>
        <img src="footfall_analysis.png" alt="Footfall Analysis">
    </div>
    
    <div class="section">
        <h2>Dwell Time Analysis</h2>
        <img src="dwell_time_analysis.png" alt="Dwell Time Analysis">
    </div>
    
    <div class="section">
        <h2>Customer Activity Timeline</h2>
        <img src="timeline_analysis.png" alt="Timeline Analysis">
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
"""
        
        # Add recommendations
        for i, rec in enumerate(results.get('insights', {}).get('recommendations', []), 1):
            html += f'        <div class="recommendation">{i}. {rec}</div>\n'
        
        html += """
    </div>
    
    <div class="section">
        <h2>Detailed Metrics</h2>
"""
        
        # Add footfall table
        if 'footfall' in results:
            html += """
        <h3>Zone-wise Footfall</h3>
        <table>
            <tr>
                <th>Zone</th>
                <th>Footfall Count</th>
                <th>Percentage</th>
            </tr>
"""
            total = results['footfall']['footfall'].sum()
            for _, row in results['footfall'].iterrows():
                pct = (row['footfall'] / total * 100) if total > 0 else 0
                html += f"""
            <tr>
                <td>{row['zone']}</td>
                <td>{row['footfall']}</td>
                <td>{pct:.1f}%</td>
            </tr>
"""
            html += "        </table>\n"
        
        html += """
    </div>
    
    <div class="section">
        <h2>Comprehensive Dashboard</h2>
        <img src="dashboard_summary.png" alt="Dashboard Summary">
    </div>
    
    <div class="section" style="text-align: center; color: #7f8c8d;">
        <p>Store Intelligence Challenge - Purplle Tech 2026</p>
        <p>End-to-End CCTV Analytics Solution</p>
    </div>
</body>
</html>
"""
        return html
    
    def save_report(self):
        """Save HTML report"""
        results = self.load_results()
        html = self.generate_html_report(results)
        
        report_path = self.output_dir / 'store_intelligence_report.html'
        with open(report_path, 'w') as f:
            f.write(html)
        
        print(f"Report saved to: {report_path}")
        return report_path

def generate_summary_stats(output_dir):
    """Generate quick summary statistics"""
    output_path = Path(output_dir)
    
    stats = {
        'timestamp': datetime.now().isoformat(),
        'files_generated': []
    }
    
    # Count output files
    for file in output_path.glob('*'):
        stats['files_generated'].append(file.name)
    
    # Load insights
    if (output_path / 'insights.json').exists():
        with open(output_path / 'insights.json', 'r') as f:
            insights = json.load(f)
            stats['insights'] = insights
    
    # Save summary
    with open(output_path / 'summary_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\n=== SUMMARY STATISTICS ===")
    print(f"Generated {len(stats['files_generated'])} output files")
    if 'insights' in stats:
        print(f"Total Detections: {stats['insights'].get('total_detections', 0)}")
        print(f"Zones Analyzed: {stats['insights'].get('zones_analyzed', 0)}")
        print(f"Peak Zone: {stats['insights'].get('peak_zone', 'N/A')}")
    
    return stats

if __name__ == "__main__":
    output_dir = "output"
    
    # Generate HTML report
    print("Generating HTML report...")
    generator = ReportGenerator(output_dir)
    report_path = generator.save_report()
    
    # Generate summary stats
    print("\nGenerating summary statistics...")
    stats = generate_summary_stats(output_dir)
    
    print(f"\nComplete! Open {report_path} in a browser to view the report.")
