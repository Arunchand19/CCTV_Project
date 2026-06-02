# 🚀 QUICK START GUIDE

## ✅ Step-by-Step Instructions

### 1️⃣ **Verify System**
```bash
python check_system.py
```
This checks all dependencies and files.

### 2️⃣ **Install Dependencies** (if needed)
```bash
pip install flask opencv-python numpy werkzeug
```

### 3️⃣ **Start Application**
```bash
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

### 4️⃣ **Open Browser**
Navigate to: **http://localhost:5000**

### 5️⃣ **Upload & Process**
1. Click "Select Video File" button
2. Choose your CCTV video (MP4, AVI, MOV, MKV)
3. Click "Start AI Detection"
4. Watch LIVE processing with:
   - Visitor IDs (VIS_0001, VIS_0002, etc.)
   - Zone labels (ENTRANCE, ZONE_A, ZONE_B, EXIT)
   - Real-time counters

### 6️⃣ **Stop & Analyze**
1. Click "Stop & Generate Analytics" button anytime
2. System stops and generates dashboard
3. View comprehensive analytics:
   - 👥 Unique Visitors (no duplicates!)
   - 🚪 Entry Count
   - 🚶 Exit Count
   - 🔔 Total Events
   - 📊 Zone Analytics
   - 📈 Timeline Chart
   - 🔥 Heatmap

---

## 📊 Dashboard Metrics Explained

### **Unique Visitors**
- Number of DIFFERENT people
- Same person in 100 frames = counted as 1
- Guaranteed accurate with Python set()

### **Entry Count**
- Total entry events
- May be higher than unique visitors (re-entries)

### **Exit Count**
- Total exit events detected

### **Total Events**
- All events: ENTRY, ZONE_ENTER, ZONE_EXIT, etc.

### **Zone Analytics**
- Total visits per zone
- Unique visitors per zone

### **Event Types**
- Breakdown of all event types
- Visual icons for each type

---

## 🐛 Troubleshooting

### Issue: Import errors
**Solution:**
```bash
pip install flask opencv-python numpy werkzeug
```

### Issue: Video won't upload
**Solution:**
- Check file size (max 500MB)
- Ensure format is MP4, AVI, MOV, or MKV
- Check browser console for errors

### Issue: No detections shown
**Solution:**
- Video may have low motion
- Background subtraction works best with static camera
- Try different video with moving people

### Issue: Unique visitors count seems wrong
**Solution:**
- Check `output/visitors.json` for details
- Each visitor shows frames_seen count
- System guarantees unique counting via set()

---

## 📁 Output Files

After processing, check `output/` folder:

1. **analytics.json** - All metrics
2. **events.json** - All detection events
3. **visitors.json** - Unique visitor details
4. **heatmap.png** - Movement visualization

---

## 🎯 Key Features

✅ **Unique Person Tracking** - No duplicates
✅ **Live Video Stream** - See processing in real-time
✅ **Stop Anytime** - Accurate analytics up to stop point
✅ **Zone-Based Analytics** - Spatial insights
✅ **Event Schema** - Professional retail format
✅ **Multi-Color UI** - Beautiful visualizations
✅ **Responsive Design** - Works on all devices

---

## 💡 Tips

1. **Best Results**: Use videos with clear people movement
2. **Performance**: Process every few frames for speed
3. **Accuracy**: Lower detection threshold catches more
4. **Zones**: Adjust zone regions in `event_detector.py` for your layout
5. **Colors**: Each zone has unique color during live view

---

## 🆘 Need Help?

Check these files:
- `UNIQUE_COUNTING_GUARANTEE.md` - How unique counting works
- `EVENT_SYSTEM_GUIDE.md` - Event schema details
- `UI_DESIGN_GUIDE.md` - UI features explained

---

## ✨ Enjoy Your CCTV Analytics System!

The system provides professional-grade retail analytics with guaranteed unique visitor counting! 🎯
