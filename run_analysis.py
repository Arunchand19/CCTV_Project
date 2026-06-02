"""
Store Intelligence Challenge - Quick Start Script
Runs the complete CCTV analysis pipeline
"""

import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    try:
        import cv2
        import numpy
        import pandas
        import matplotlib
        import seaborn
        print("✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nInstalling dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def run_main_analysis():
    """Run main CCTV analysis"""
    print("\n" + "="*60)
    print("STEP 1: Running Main CCTV Analysis")
    print("="*60)
    subprocess.run([sys.executable, "main.py"])

def run_advanced_analytics():
    """Run advanced analytics"""
    print("\n" + "="*60)
    print("STEP 2: Running Advanced Analytics")
    print("="*60)
    
    # Check if positions file exists
    if not Path("output/customer_positions.csv").exists():
        print("Warning: customer_positions.csv not found. Skipping advanced analytics.")
        return
    
    subprocess.run([sys.executable, "advanced_analytics.py"])

def generate_report():
    """Generate final report"""
    print("\n" + "="*60)
    print("STEP 3: Generating Report")
    print("="*60)
    subprocess.run([sys.executable, "report_generator.py"])

def main():
    """Main execution flow"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Store Intelligence Challenge - CCTV Analytics         ║
    ║              Purplle Tech Challenge 2026                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_dependencies():
        print("Failed to install dependencies. Please install manually.")
        return
    
    # Run analysis pipeline
    try:
        run_main_analysis()
        run_advanced_analytics()
        generate_report()
        
        print("\n" + "="*60)
        print("✓ ANALYSIS COMPLETE!")
        print("="*60)
        print("\nGenerated Files:")
        print("  - output/customer_positions.csv")
        print("  - output/footfall.csv")
        print("  - output/dwell_times.csv")
        print("  - output/insights.json")
        print("  - output/*.png (visualizations)")
        print("  - output/store_intelligence_report.html")
        print("\nOpen 'output/store_intelligence_report.html' in a browser to view results.")
        
    except Exception as e:
        print(f"\n✗ Error during execution: {e}")
        print("Please check the error messages above for details.")

if __name__ == "__main__":
    main()
