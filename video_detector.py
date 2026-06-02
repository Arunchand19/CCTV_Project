import cv2
import numpy as np
from pathlib import Path
import json
import base64

def generate_frames(video_path):
    """Generate frames with object detection for live streaming"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Cannot open video file")
    
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
    
    frame_count = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Color palette for bounding boxes
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 165, 255),  # Orange
    ]
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Apply background subtraction
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_count = 0
        for idx, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Draw bounding box with color
                color = colors[idx % len(colors)]
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Add label
                label = f"Object {detected_count + 1}"
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                detected_count += 1
        
        # Add info overlay
        info_text = f"Frame: {frame_count} | Objects: {detected_count}"
        cv2.rectangle(frame, (10, 10), (400, 50), (0, 0, 0), -1)
        cv2.putText(frame, info_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    cap.release()

def process_video_final(video_path, output_dir="output"):
    """Final processing to generate analytics and heatmap"""
    Path(output_dir).mkdir(exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Cannot open video file")
    
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
    
    detections = []
    frame_count = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    heatmap = np.zeros((height, width), dtype=np.float32)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:
                x, y, w, h = cv2.boundingRect(contour)
                heatmap[y:y+h, x:x+w] += 1
                
                detections.append({
                    'frame': frame_count,
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'timestamp': frame_count / fps
                })
    
    cap.release()
    
    if heatmap.max() > 0:
        heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        cv2.imwrite(f"{output_dir}/heatmap.png", heatmap_color)
    
    analytics = {
        'total_frames': frame_count,
        'total_detections': len(detections),
        'average_objects_per_frame': len(detections) / max(frame_count, 1),
        'video_duration': frame_count / fps,
        'fps': fps,
        'resolution': f"{width}x{height}"
    }
    
    with open(f"{output_dir}/detections.json", 'w') as f:
        json.dump({'detections': detections, 'analytics': analytics}, f, indent=2)
    
    return analytics, detections
