# CCTV Video Object Detection Dashboard

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements_webapp.txt
```

2. Run the application:
```bash
python app.py
```

3. Open browser and navigate to:
```
http://localhost:5000
```

4. Upload CCTV video clip and view analytics dashboard

## Features
- Video upload interface
- Real-time object detection
- Detection heatmap visualization
- Analytics dashboard with:
  - Total detections count
  - Average objects per frame
  - Detection timeline chart
  - Video metadata

## Output
- Heatmap showing high-activity areas
- Detection count over time
- JSON file with all detection coordinates
