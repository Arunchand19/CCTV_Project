"""
Startup verification script for CCTV Analytics System
"""

import sys
import os

print("=" * 60)
print("CCTV Analytics System - Startup Check")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check required modules
required_modules = {
    'flask': 'Flask',
    'cv2': 'OpenCV',
    'numpy': 'NumPy',
    'werkzeug': 'Werkzeug'
}

print("\nChecking required modules:")
for module, name in required_modules.items():
    try:
        __import__(module)
        print(f"  ✓ {name} installed")
    except ImportError:
        print(f"  ✗ {name} NOT installed - run: pip install {module if module != 'cv2' else 'opencv-python'}")

# Check directories
print("\nChecking directories:")
dirs = ['uploads', 'output', 'templates']
for d in dirs:
    if os.path.exists(d):
        print(f"  ✓ {d}/ exists")
    else:
        print(f"  ✗ {d}/ missing")

# Check files
print("\nChecking required files:")
files = {
    'app.py': 'Flask application',
    'event_detector.py': 'Detection engine',
    'templates/index.html': 'Web interface',
    'coco.names': 'YOLO class names'
}

for file, desc in files.items():
    if os.path.exists(file):
        print(f"  ✓ {file} ({desc})")
    else:
        print(f"  ✗ {file} ({desc}) missing")

# YOLO files (optional)
print("\nOptional YOLO files (for better accuracy):")
yolo_files = ['yolov3.weights', 'yolov3.cfg']
for file in yolo_files:
    if os.path.exists(file):
        print(f"  ✓ {file} available")
    else:
        print(f"  ⚠ {file} not found (will use background subtraction)")

print("\n" + "=" * 60)
print("STARTUP INSTRUCTIONS:")
print("=" * 60)
print("\n1. Run the application:")
print("   python app.py")
print("\n2. Open browser:")
print("   http://localhost:5000")
print("\n3. Upload CCTV video and start detection")
print("\n4. Click 'Stop & Generate Analytics' to view results")
print("\n" + "=" * 60)
