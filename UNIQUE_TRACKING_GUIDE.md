# 🎯 UNIQUE PERSON TRACKING - CCTV Analytics

## Problem Solved
**OLD**: Same person detected in 100 frames = counted as 100 persons ❌  
**NEW**: Same person detected in 100 frames = counted as 1 unique person ✅

---

## 🧠 How Unique Tracking Works

### Multi-Criteria Matching Algorithm

The system uses **3 metrics** to identify if a detection is the same person:

#### 1️⃣ **IoU (Intersection over Union)** - 40% weight
- Measures bounding box overlap
- High IoU = likely same person
- Example: 0.7 IoU means 70% overlap

#### 2️⃣ **Distance Metric** - 40% weight
- Calculates distance between box centers
- Closer distance = likely same person
- Normalized to 300 pixels max

#### 3️⃣ **Size Similarity** - 20% weight
- Compares bounding box sizes
- Similar size = likely same person
- Handles zoom/perspective changes

### Matching Logic
```
Similarity Score = (IoU × 0.4) + (Distance × 0.4) + (Size × 0.2)

If Similarity > 0.3 (30%):
    → SAME PERSON (update existing ID)
Else:
    → NEW PERSON (assign new ID)
```

---

## 📊 Example Scenario

### Video with 3 People Walking

**Frame-by-frame Analysis:**

```
Frame 1:  Person at (100, 200) → Person #1 ✨ NEW
Frame 2:  Person at (105, 205) → Person #1 ✓ SAME
Frame 3:  Person at (110, 210) → Person #1 ✓ SAME
Frame 5:  Person at (500, 100) → Person #2 ✨ NEW
Frame 7:  Person at (115, 215) → Person #1 ✓ SAME
Frame 7:  Person at (505, 105) → Person #2 ✓ SAME
Frame 10: Person at (300, 300) → Person #3 ✨ NEW
Frame 15: Person at (120, 220) → Person #1 ✓ SAME
Frame 15: Person at (510, 110) → Person #2 ✓ SAME
Frame 15: Person at (310, 310) → Person #3 ✓ SAME
```

**Result:**
- Total Detections: 10
- **Unique Persons: 3** ✅

---

## 🛡️ Handling Edge Cases

### 1. **Temporary Occlusion**
Person temporarily hidden behind object:
```
Frame 1: Person #1 visible
Frame 2: Person #1 hidden (not detected)
Frame 3: Person #1 visible again → Still Person #1 ✓
```
**Solution**: Tracks kept alive for 30 frames

### 2. **Similar People**
Two people of similar size near each other:
```
Person A at (100, 200) - Size: 50×150
Person B at (120, 200) - Size: 50×150
```
**Solution**: IoU + Distance prevents confusion

### 3. **Person Exits & Re-enters**
Person leaves frame and returns later:
```
Frame 1-50:   Person #1 visible
Frame 51-100: Person #1 not visible (exited)
Frame 101:    Person returns → Person #2 (new ID)
```
**Solution**: After 30 frames missing, treated as new person

---

## 📱 Object Counting (Non-Persons)

### Objects: Cell Phones, Laptops, etc.

**Strategy**: Count appearances, not tracks
- Phone visible in 10 frames = counted based on distinct appearances
- Focus on quantity present, not tracking individual items

**Example:**
```
Frame 1: 2 cell phones detected
Frame 5: 1 cell phone detected
Frame 10: 3 cell phones detected

Result: Multiple phone detections logged
```

---

## 🎨 Visual Indicators

### Live Detection Display

**Person Labels:**
```
Person #1 → First unique person
Person #2 → Second unique person
Person #3 → Third unique person
```

**Color Coding:**
- 🟢 Green = Person
- 🟣 Magenta = Cell phone
- 🟡 Yellow = Laptop
- 🟠 Orange = Handbag/Backpack

---

## 📊 Dashboard Analytics

### Metrics Shown:

1. **Unique Persons** 
   - Count: Number of different individuals
   - No duplicates, each person counted once

2. **Total Detections**
   - All detection events (persons + objects)

3. **Objects Detected**
   - Person: Unique count
   - Cell Phone: Total appearances
   - Laptop: Total appearances
   - Other objects: Total appearances

---

## 🚀 Usage Example

### Step-by-Step:

1. **Upload** CCTV video clip
2. **Start** live detection
3. **Watch** persons being tracked with IDs
4. **Stop** when desired
5. **View** dashboard showing:
   ```
   Unique Persons: 3
   Objects Detected:
   - Person: 3
   - Cell Phone: 2
   - Laptop: 1
   ```

---

## ✅ Accuracy Improvements

### Previous System:
- Person in 100 frames = 100 persons ❌
- No tracking continuity
- Inflated counts

### Current System:
- Person in 100 frames = 1 person ✅
- Robust multi-metric tracking
- Accurate unique counts
- Handles occlusions
- Size and position validation

---

## 🔧 Technical Details

### Matching Thresholds:
- **Similarity Threshold**: 0.3 (30%)
- **Max Missing Frames**: 30 frames
- **Max Distance**: 300 pixels

### Performance:
- Real-time processing
- Efficient tracking algorithm
- Memory-optimized (stores only last 10 bboxes per person)

---

## 🎯 Key Benefits

✅ **Accurate People Counting** - No duplicates  
✅ **Robust Tracking** - Handles occlusions  
✅ **Multiple Objects** - Detects 80+ object types  
✅ **Live Feedback** - See IDs in real-time  
✅ **Stop Anytime** - Instant analytics  

---

**Ready to use?**
```bash
python app.py
```
Open http://localhost:5000 and see unique person tracking in action! 🚀
