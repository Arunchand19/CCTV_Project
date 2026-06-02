"""
Project Verification & Testing Script
Checks if all components are properly set up
"""

import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} MISSING: {filepath}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n=== Checking Dependencies ===")
    required = ['cv2', 'numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} MISSING")
            missing.append(package)
    
    return len(missing) == 0

def verify_project_structure():
    """Verify all project files are present"""
    print("\n=== Verifying Project Structure ===")
    
    files = {
        # Core modules
        'main.py': 'Main analysis engine',
        'advanced_analytics.py': 'Advanced analytics module',
        'report_generator.py': 'Report generator',
        'utils.py': 'Utility functions',
        'run_analysis.py': 'Pipeline orchestrator',
        
        # Configuration
        'config.json': 'Configuration file',
        'requirements.txt': 'Dependencies',
        
        # Documentation
        'README.md': 'User guide',
        'TECHNICAL_DOCUMENTATION.md': 'Technical specs',
        'PROJECT_SUMMARY.md': 'Project overview',
        
        # Execution
        'RUN_ANALYSIS.bat': 'Windows launcher'
    }
    
    all_present = True
    for file, desc in files.items():
        if not check_file_exists(file, desc):
            all_present = False
    
    return all_present

def check_input_data():
    """Check if input data exists"""
    print("\n=== Checking Input Data ===")
    
    video_dir = Path("CCTV Footage-20260529T160731Z-3-00144614ea/CCTV Footage")
    layout_file = Path("Brigade Road - Store layoutc5f5d56.xlsx")
    
    video_exists = video_dir.exists()
    layout_exists = layout_file.exists()
    
    if video_exists:
        print(f"✓ Video directory found: {video_dir}")
        video_files = list(video_dir.glob("*.mp4"))
        print(f"  Found {len(video_files)} MP4 files")
        for vf in video_files:
            print(f"    - {vf.name}")
    else:
        print(f"✗ Video directory NOT FOUND: {video_dir}")
    
    if layout_exists:
        print(f"✓ Store layout found: {layout_file}")
    else:
        print(f"✗ Store layout NOT FOUND: {layout_file}")
    
    return video_exists and layout_exists

def create_output_directory():
    """Create output directory if it doesn't exist"""
    print("\n=== Output Directory ===")
    output_dir = Path("output")
    
    if output_dir.exists():
        print(f"✓ Output directory exists: {output_dir}")
    else:
        output_dir.mkdir()
        print(f"✓ Output directory created: {output_dir}")
    
    return True

def run_quick_test():
    """Run a quick functionality test"""
    print("\n=== Running Quick Functionality Test ===")
    
    try:
        # Test imports
        from utils import create_sample_data, calculate_zone_coverage
        print("✓ Utils module imports successful")
        
        # Test sample data generation
        sample_df = create_sample_data(50)
        print(f"✓ Sample data generation: {len(sample_df)} rows created")
        
        # Test coverage calculation
        coverage = calculate_zone_coverage(sample_df)
        print(f"✓ Zone coverage calculation: {len(coverage)} zones")
        
        return True
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False

def main():
    """Main verification routine"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        Project Verification & Testing Script             ║
    ║     Store Intelligence Challenge - CCTV Analytics         ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'dependencies': check_dependencies(),
        'structure': verify_project_structure(),
        'input_data': check_input_data(),
        'output_dir': create_output_directory(),
        'functionality': run_quick_test()
    }
    
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = all(results.values())
    
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {component.replace('_', ' ').title()}")
    
    print("="*60)
    
    if all_passed:
        print("\n✓ ALL CHECKS PASSED!")
        print("  Project is ready to run.")
        print("  Execute: python run_analysis.py")
    else:
        print("\n✗ SOME CHECKS FAILED")
        print("  Please fix the issues above before running.")
        
        if not results['dependencies']:
            print("\n  To install dependencies:")
            print("    pip install -r requirements.txt")
        
        if not results['input_data']:
            print("\n  Note: Input data is optional.")
            print("  The system will use sample data for demonstration.")
    
    print()

if __name__ == "__main__":
    main()
