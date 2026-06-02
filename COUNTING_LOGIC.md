# 📊 Counting Logic - Clarification

## Updated Metrics Definition

### ✅ **Unique Visitors**
- **What it shows**: Total number of DIFFERENT people detected
- **How counted**: `len(unique_visitors set)`
- **Example**: 5 different people = 5

### ✅ **Entry Count** 
- **What it shows**: SAME as Unique Visitors (unique count)
- **How counted**: `unique_visitors count`
- **Example**: 5 different people = 5
- **Note**: No longer counts re-entry events separately

### ✅ **Exit Count**
- **What it shows**: Number of exit events detected
- **How counted**: Exit events from all zones
- **Example**: 3 people left = 3

### ✅ **Total Events**
- **What it shows**: All events generated (ENTRY, ZONE_ENTER, etc.)
- **How counted**: `len(all_events)`
- **Example**: 156 total event records

---

## Dashboard Display

```
👥 Unique Visitors: 5    ← 5 different people
🚪 Entry Count: 5        ← Same 5 people (no duplicates)
🚶 Exit Count: 3         ← 3 people left
🔔 Total Events: 156     ← All event records
```

### Interpretation:
- **5 unique people** entered the store
- **5 entry count** (same as unique - no duplicate counting)
- **3 people** were detected leaving
- **156 events** were generated total (including zone movements)

---

## Key Changes

### BEFORE:
```
Unique Visitors: 5
Entry Count: 7         ← Could be higher (re-entries counted)
```

### NOW:
```
Unique Visitors: 5
Entry Count: 5         ← Always same as unique visitors
```

---

## Why This Makes Sense

### Scenario: One person enters, leaves, returns
**Before logic:**
- Unique Visitors: 1
- Entry Count: 2 (two ENTRY events)

**New logic:**
- Unique Visitors: 1
- Entry Count: 1 (same person, counted once)

This ensures both metrics show the **TRUE unique count**!

---

## Verification

Check `output/visitors.json`:
```json
{
  "total_unique_visitors": 5,
  "visitors": [
    {"id": "VIS_0001", "frames_seen": 342},
    {"id": "VIS_0002", "frames_seen": 156},
    {"id": "VIS_0003", "frames_seen": 89},
    {"id": "VIS_0004", "frames_seen": 234},
    {"id": "VIS_0005", "frames_seen": 178}
  ]
}
```
- **5 unique visitor IDs** = **5 unique visitors** = **5 entry count** ✅

---

## Summary

✅ **Unique Visitors** = Number of different people
✅ **Entry Count** = Same as unique visitors (guaranteed match)
✅ **Exit Count** = Exit events detected
✅ **Total Events** = All event records

**Both Unique Visitors and Entry Count will always show the same number!**
