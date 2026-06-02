"""
Utility functions for CCTV analysis
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import json

def load_config(config_path='config.json'):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def validate_video_files(video_dir):
    """Check if all required video files exist"""
    video_path = Path(video_dir)
    required_cameras = ['CAM 1', 'CAM 2', 'CAM 3', 'CAM 4', 'CAM 5']
    found_videos = []
    
    for camera in required_cameras:
        video_file = video_path / f"{camera}.mp4"
        if video_file.exists():
            found_videos.append(camera)
        else:
            print(f"Warning: {camera}.mp4 not found")
    
    return found_videos

def extract_video_metadata(video_path):
    """Extract metadata from video file"""
    cap = cv2.VideoCapture(str(video_path))
    
    metadata = {
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'duration_sec': 0
    }
    
    if metadata['fps'] > 0:
        metadata['duration_sec'] = metadata['frame_count'] / metadata['fps']
    
    cap.release()
    return metadata

def create_sample_data(num_samples=200):
    """Create sample data for testing"""
    cameras = ['CAM 1', 'CAM 2', 'CAM 3', 'CAM 4', 'CAM 5']
    zones = ['Entrance', 'Cosmetics_Section', 'Skincare_Section', 
             'Fragrance_Section', 'Checkout_Counter']
    
    data = []
    for i, (camera, zone) in enumerate(zip(cameras * (num_samples // 5), zones * (num_samples // 5))):
        data.append({
            'camera': camera,
            'timestamp': np.random.uniform(0, 100),
            'x': np.random.randint(50, 590),
            'y': np.random.randint(50, 430),
            'zone': zone
        })
    
    return pd.DataFrame(data)

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def merge_nearby_detections(detections, threshold=50):
    """Merge detections that are close together"""
    if len(detections) == 0:
        return []
    
    merged = []
    used = set()
    
    for i, det1 in enumerate(detections):
        if i in used:
            continue
        
        cluster = [det1]
        for j, det2 in enumerate(detections[i+1:], i+1):
            if j in used:
                continue
            
            center1 = (det1[0] + det1[2]//2, det1[1] + det1[3]//2)
            center2 = (det2[0] + det2[2]//2, det2[1] + det2[3]//2)
            
            if calculate_distance(center1, center2) < threshold:
                cluster.append(det2)
                used.add(j)
        
        # Average the cluster
        avg_x = int(np.mean([d[0] for d in cluster]))
        avg_y = int(np.mean([d[1] for d in cluster]))
        avg_w = int(np.mean([d[2] for d in cluster]))
        avg_h = int(np.mean([d[3] for d in cluster]))
        
        merged.append((avg_x, avg_y, avg_w, avg_h))
        used.add(i)
    
    return merged

def format_time(seconds):
    """Format seconds into readable time string"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def calculate_zone_coverage(positions_df):
    """Calculate percentage coverage per zone"""
    total = len(positions_df)
    if total == 0:
        return {}
    
    zone_counts = positions_df['zone'].value_counts()
    coverage = {zone: (count / total * 100) for zone, count in zone_counts.items()}
    return coverage

def export_to_excel(data_dict, output_path):
    """Export multiple dataframes to Excel with sheets"""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

def get_video_first_frame(video_path):
    """Extract first frame from video"""
    cap = cv2.VideoCapture(str(video_path))
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def draw_detections(frame, detections, color=(0, 255, 0)):
    """Draw bounding boxes on frame"""
    output = frame.copy()
    for det in detections:
        x, y, w, h = det
        cv2.rectangle(output, (x, y), (x+w, y+h), color, 2)
    return output

def calculate_occupancy_rate(positions_df, zone_name, time_window=10):
    """Calculate occupancy rate for a zone"""
    zone_data = positions_df[positions_df['zone'] == zone_name]
    
    if len(zone_data) == 0:
        return 0
    
    timestamps = zone_data['timestamp'].values
    time_bins = np.arange(timestamps.min(), timestamps.max(), time_window)
    
    occupancy = []
    for i in range(len(time_bins) - 1):
        mask = (timestamps >= time_bins[i]) & (timestamps < time_bins[i+1])
        occupancy.append(mask.sum())
    
    return np.mean(occupancy) if occupancy else 0

def generate_comparison_report(before_df, after_df):
    """Compare two datasets (e.g., before/after intervention)"""
    comparison = {
        'before_total': len(before_df),
        'after_total': len(after_df),
        'change_pct': ((len(after_df) - len(before_df)) / len(before_df) * 100) if len(before_df) > 0 else 0
    }
    
    # Zone-wise comparison
    before_zones = before_df['zone'].value_counts()
    after_zones = after_df['zone'].value_counts()
    
    comparison['zone_changes'] = {}
    for zone in before_zones.index:
        before_count = before_zones.get(zone, 0)
        after_count = after_zones.get(zone, 0)
        change = ((after_count - before_count) / before_count * 100) if before_count > 0 else 0
        comparison['zone_changes'][zone] = {
            'before': before_count,
            'after': after_count,
            'change_pct': change
        }
    
    return comparison

class VideoProcessor:
    """Helper class for video processing operations"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = None
        
    def __enter__(self):
        self.cap = cv2.VideoCapture(str(self.video_path))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cap:
            self.cap.release()
    
    def get_frame_at_time(self, time_sec):
        """Get frame at specific timestamp"""
        if not self.cap:
            return None
        
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(time_sec * fps)
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        return frame if ret else None
    
    def extract_frames(self, interval_sec=1):
        """Extract frames at regular intervals"""
        if not self.cap:
            return []
        
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_sec)
        
        frames = []
        frame_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frames.append((frame_count / fps, frame))
            
            frame_count += 1
        
        return frames

if __name__ == "__main__":
    # Test utilities
    print("Testing utilities...")
    
    # Create sample data
    sample_df = create_sample_data(100)
    print(f"Created sample data: {len(sample_df)} rows")
    
    # Calculate coverage
    coverage = calculate_zone_coverage(sample_df)
    print("Zone coverage:")
    for zone, pct in coverage.items():
        print(f"  {zone}: {pct:.1f}%")
    
    print("\nUtilities test complete!")
