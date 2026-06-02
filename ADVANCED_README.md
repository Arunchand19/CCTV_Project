# CCTV Advanced Object Detection System

## 🎯 Key Features

### ✅ Unique Person Tracking
- Tracks and counts **unique persons** (no duplicates)
- Each person assigned a unique ID (Person #1, #2, etc.)
- Smart tracking across frames

### ✅ Object Detection
- Detects multiple object types:
  - 👤 Persons
  - 📱 Cell phones
  - 💻 Laptops
  - 👜 Handbags
  - 🎒 Backpacks
  - 🍾 Bottles
  - 🪑 Chairs
  - And 80+ other objects

### ✅ Live Processing with STOP Control
- Watch real-time detection
- **STOP button** - halt processing anytime
- Instant analytics generation on stop

### ✅ Comprehensive Analytics
- Unique persons count (no duplicates)
- Object-wise breakdown with icons
- Detection timeline chart
- Heatmap visualization

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_webapp.txt
```

### 2. (Optional) Download YOLO for Better Accuracy
For advanced object detection, download YOLO weights:
```bash
# Download YOLOv3 weights (237 MB)
# Place in project root folder
```

If YOLO not available, system uses background subtraction (still works!).

### 3. Run Application
```bash
python app.py
```

### 4. Open Browser
```
http://localhost:5000
```

## 📋 How to Use

### Step 1: Upload Video
- Click "Select Video File"
- Choose your CCTV clip (MP4, AVI, MOV, MKV)

### Step 2: Start Live Detection
- Click "Start Live Detection"
- Video processing begins immediately

### Step 3: Watch Live Processing
- See real-time object detection
- Colored bounding boxes around objects
- Person IDs for unique tracking
- Frame counter and person count

### Step 4: Stop When Ready
- Click "🛑 Stop Detection" button anytime
- System immediately stops and generates analytics

### Step 5: View Dashboard
- **Unique Persons**: Number of different individuals
- **Objects Detected**: Breakdown by type (persons, phones, etc.)
- **Timeline Chart**: Detections over time
- **Heatmap**: High-activity zones

## 📊 Analytics Output

### Dashboard Shows:
1. **Unique Persons** - No duplicates, each person counted once
2. **Total Detections** - All objects detected
3. **Video Duration** - Processed time
4. **FPS** - Frames per second

### Objects Section:
- Visual icons for each object type
- Count for each category
- Example: 5 persons, 2 cell phones, 1 laptop

### Charts:
- Detection timeline (per second)
- Heatmap of person movement

## 🎨 Color Coding

- **Green** = Person
- **Magenta** = Cell phone
- **Yellow** = Laptop
- **Orange** = Handbag/Backpack
- **Cyan** = Bottle
- **Blue** = Other objects

## 🔧 Technical Details

### Object Detection Methods:
1. **YOLO** (if weights available) - 80+ object classes
2. **Background Subtraction** (fallback) - Motion detection

### Person Tracking:
- Distance-based matching algorithm
- Tracks persons across frames
- Unique ID assignment
- No duplicate counting

### Performance:
- Real-time processing
- Stop anytime without data loss
- Generates analytics from processed frames only

## 📁 Output Files

Saved in `output/` folder:
- `detections.json` - All detection data including:
  - Analytics summary
  - Frame-by-frame detections
  - Unique person list with IDs
- `heatmap.png` - Visual heatmap

## 🎯 Use Cases

- **Retail**: Count unique customers
- **Security**: Track persons and objects
- **Analytics**: Understand movement patterns
- **Events**: Monitor attendance

## 🔄 Workflow

```
Upload → Live Detection → Stop Anytime → Instant Analytics
```

No waiting for full video processing - stop and analyze whenever you want!
