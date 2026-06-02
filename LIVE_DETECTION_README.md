# CCTV LIVE Object Detection System

## Features
✅ **Live Video Processing** - Watch object detection in real-time
✅ **Colored Bounding Boxes** - Each detected object highlighted with different colors
✅ **Real-time Frame Counter** - Shows current frame and object count
✅ **Interactive Dashboard** - Analytics generated after processing
✅ **Heatmap Visualization** - See high-activity zones

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_webapp.txt
```

### 2. Run Application
```bash
python app.py
```

### 3. Open Browser
```
http://localhost:5000
```

### 4. Use the System

**Step 1:** Click "Select Video File" to choose your CCTV clip

**Step 2:** Click "Start Live Detection" to upload and begin processing

**Step 3:** Watch LIVE as the system:
- Processes each frame
- Detects moving objects
- Draws colored bounding boxes around detected objects
- Shows "LIVE" indicator and frame information

**Step 4:** Click "Generate Dashboard" to see:
- Total detections
- Average objects per frame
- Detection timeline chart
- Heat map of activity zones

## How It Works

### Object Detection
- Uses background subtraction (MOG2 algorithm)
- Identifies moving objects in real-time
- Draws colored bounding boxes (Green, Blue, Yellow, Magenta, Orange)
- Labels each object with "Object 1", "Object 2", etc.

### Live Streaming
- Frame-by-frame processing via HTTP streaming
- Real-time visualization in browser
- No background processing - you see everything live

### Analytics
- Counts all detections throughout video
- Tracks timestamp and position of each object
- Generates heatmap showing high-traffic areas
- Creates timeline chart of detections per second

## Output Files

All results saved in `output/` folder:
- `detections.json` - All detection data with coordinates
- `heatmap.png` - Visual heatmap of activity zones

## Tech Stack
- **Backend:** Flask (Python web framework)
- **Computer Vision:** OpenCV (object detection)
- **Frontend:** HTML5, JavaScript, Chart.js
- **Streaming:** HTTP multipart streaming (MJPEG)
