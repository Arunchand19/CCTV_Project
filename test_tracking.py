"""
Test script to verify unique person tracking
"""

print("""
🎯 UNIQUE PERSON TRACKING - How It Works
==========================================

Enhanced Tracking Algorithm:
---------------------------
1. **IoU (Intersection over Union)**: Measures overlap between bounding boxes
2. **Distance Metric**: Calculates center-point distance between detections
3. **Size Similarity**: Compares box sizes to ensure same person
4. **Weighted Score**: Combines all metrics for robust matching

Tracking Features:
-----------------
✅ Same person tracked across frames (counted as 1)
✅ Handles temporary occlusions (person missing for few frames)
✅ Size and position validation
✅ Automatic stale track removal (after 30 frames)

Matching Criteria:
-----------------
- Similarity Score > 0.3 (30%) required for match
- IoU weight: 40%
- Distance weight: 40%
- Size similarity weight: 20%

Example:
--------
Frame 1: Person detected at (100, 100) → Person #1
Frame 2: Person detected at (105, 102) → SAME Person #1 (not #2!)
Frame 3: Person detected at (110, 105) → SAME Person #1
Frame 10: New person at (500, 300) → Person #2

Result: Only 2 unique persons counted (not 13)

Object Counting:
---------------
✅ Persons: Unique count only
✅ Objects (phones, laptops, etc.): Counted per frame appearance
✅ No duplicate person counting
✅ Accurate final summary

🚀 Run the application to see it in action!
python app.py
""")
