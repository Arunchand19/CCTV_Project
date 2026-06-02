"""
Live CCTV Detection System with YOLO
Real-time object detection and visualization
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict, Counter
import time

class LiveCCTVDetector:
    def __init__(self):
        self.detections = []
        self.frame_count = 0
        self.start_time = None
        self.detection_stats = defaultdict(int)
        self.zone_stats = defaultdict(lambda: defaultdict(int))
        
        # YOLO class names (COCO dataset)
        self.class_names = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
        
        # Color palette for different classes
        np.random.seed(42)
        self.colors = np.random.randint(0, 255, size=(len(self.class_names), 3), dtype=np.uint8)
        
        # Store-specific colors
        self.store_colors = {
            'person': (0, 255, 0),      # Green for customers
            'handbag': (255, 0, 0),     # Blue for bags
            'backpack': (255, 0, 0),    # Blue for backpacks
            'bottle': (0, 255, 255),    # Yellow for products
            'cup': (0, 255, 255),       # Yellow for products
            'cell phone': (255, 0, 255) # Magenta for phones
        }
        
    def initialize_yolo(self):
        """Initialize YOLO model - using OpenCV DNN with fallback"""
        try:
            # Try to load YOLOv4-tiny (faster for real-time)
            config_path = "yolov4-tiny.cfg"
            weights_path = "yolov4-tiny.weights"
            
            if not Path(config_path).exists() or not Path(weights_path).exists():
                print("⚠ YOLO weights not found. Using fallback detection...")
                return None
            
            net = cv2.dnn.readNet(weights_path, config_path)
            net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            layer_names = net.getLayerNames()
            output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
            
            print("✓ YOLO model loaded successfully!")
            return {'net': net, 'output_layers': output_layers}
        except Exception as e:
            print(f"⚠ YOLO initialization failed: {e}")
            print("Using fallback HOG detector...")
            return None
    
    def detect_with_yolo(self, frame, yolo_model, confidence_threshold=0.5, nms_threshold=0.4):
        """Detect objects using YOLO"""
        height, width = frame.shape[:2]
        
        # Create blob from image
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        yolo_model['net'].setInput(blob)
        
        # Forward pass
        outputs = yolo_model['net'].forward(yolo_model['output_layers'])
        
        # Process detections
        boxes = []
        confidences = []
        class_ids = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > confidence_threshold:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    
                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # Apply non-maximum suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)
        
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                class_id = class_ids[i]
                confidence = confidences[i]
                
                detections.append({
                    'bbox': (x, y, w, h),
                    'class_id': class_id,
                    'class_name': self.class_names[class_id] if class_id < len(self.class_names) else 'unknown',
                    'confidence': confidence
                })
        
        return detections
    
    def detect_with_hog(self, frame):
        """Fallback: Detect people using HOG"""
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Detect people
        boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8), padding=(4, 4), scale=1.05)
        
        detections = []
        for i, (x, y, w, h) in enumerate(boxes):
            detections.append({
                'bbox': (x, y, w, h),
                'class_id': 0,
                'class_name': 'person',
                'confidence': weights[i][0] if len(weights) > i else 0.5
            })
        
        return detections
    
    def detect_with_background_subtraction(self, frame):
        """Additional fallback: Background subtraction"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if not hasattr(self, 'background'):
            self.background = blur
            return []
        
        diff = cv2.absdiff(self.background, blur)
        thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                detections.append({
                    'bbox': (x, y, w, h),
                    'class_id': 0,
                    'class_name': 'person',
                    'confidence': 0.7
                })
        
        self.background = cv2.addWeighted(self.background, 0.95, blur, 0.05, 0)
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes with labels on frame"""
        for det in detections:
            x, y, w, h = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Get color for this class
            if class_name in self.store_colors:
                color = self.store_colors[class_name]
            else:
                color = tuple(map(int, self.colors[det['class_id'] % len(self.colors)]))
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label background
            label = f"{class_name}: {confidence:.2f}"
            (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x, y - label_h - 10), (x + label_w, y), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame
    
    def draw_info_panel(self, frame, detections, fps, frame_number):
        """Draw information panel on frame"""
        height, width = frame.shape[:2]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 200), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        # Count objects by class
        class_counts = Counter([det['class_name'] for det in detections])
        
        # Draw statistics
        y_offset = 35
        cv2.putText(frame, f"LIVE CCTV DETECTION", (20, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 30
        
        cv2.putText(frame, f"Frame: {frame_number} | FPS: {fps:.1f}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25
        
        cv2.putText(frame, f"Total Detections: {len(detections)}", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 25
        
        # Show top 3 detected classes
        for class_name, count in class_counts.most_common(3):
            color = self.store_colors.get(class_name, (255, 255, 255))
            cv2.putText(frame, f"  {class_name}: {count}", (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_offset += 20
        
        # Draw legend
        legend_y = height - 100
        cv2.putText(frame, "LEGEND:", (20, legend_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        legend_y += 20
        
        for class_name, color in list(self.store_colors.items())[:4]:
            cv2.rectangle(frame, (20, legend_y - 10), (40, legend_y + 5), color, -1)
            cv2.putText(frame, class_name, (50, legend_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            legend_y += 20
        
        return frame
    
    def process_video_live(self, video_path, output_path=None, display=True, save_video=True):
        """Process video with live detection display"""
        print(f"\n{'='*70}")
        print("LIVE CCTV DETECTION SYSTEM")
        print(f"{'='*70}\n")
        
        # Initialize YOLO
        print("Initializing detection model...")
        yolo_model = self.initialize_yolo()
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"✗ Error: Could not open video {video_path}")
            return None
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"✓ Video loaded: {width}x{height} @ {fps} FPS")
        print(f"  Total frames: {total_frames}")
        print(f"\nProcessing... Press 'q' to quit, 'p' to pause\n")
        
        # Setup video writer
        if save_video and output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        else:
            out = None
        
        # Processing variables
        self.start_time = time.time()
        frame_number = 0
        paused = False
        all_detections = []
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_number += 1
                current_time = time.time() - self.start_time
                current_fps = frame_number / current_time if current_time > 0 else 0
                
                # Detect objects
                if yolo_model:
                    detections = self.detect_with_yolo(frame, yolo_model)
                else:
                    # Try HOG first, then background subtraction
                    detections = self.detect_with_hog(frame)
                    if len(detections) == 0:
                        detections = self.detect_with_background_subtraction(frame)
                
                # Store detections with metadata
                for det in detections:
                    det['frame'] = frame_number
                    det['timestamp'] = current_time
                    all_detections.append(det)
                    self.detection_stats[det['class_name']] += 1
                
                # Draw detections and info
                frame = self.draw_detections(frame, detections)
                frame = self.draw_info_panel(frame, detections, current_fps, frame_number)
                
                # Save frame
                if out:
                    out.write(frame)
                
                # Progress indicator
                if frame_number % 30 == 0:
                    progress = (frame_number / total_frames) * 100
                    print(f"Progress: {progress:.1f}% | Frame: {frame_number}/{total_frames} | "
                          f"FPS: {current_fps:.1f} | Detections: {len(detections)}")
            
            # Display frame
            if display:
                cv2.imshow('Live CCTV Detection', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n⚠ Stopped by user")
                    break
                elif key == ord('p'):
                    paused = not paused
                    print(f"\n{'⏸ Paused' if paused else '▶ Resumed'}")
        
        # Cleanup
        cap.release()
        if out:
            out.release()
        if display:
            cv2.destroyAllWindows()
        
        # Calculate statistics
        processing_time = time.time() - self.start_time
        avg_fps = frame_number / processing_time if processing_time > 0 else 0
        
        print(f"\n{'='*70}")
        print("PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Frames processed: {frame_number}/{total_frames}")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Total detections: {len(all_detections)}")
        print(f"\nDetection breakdown:")
        for class_name, count in sorted(self.detection_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {class_name}: {count}")
        
        return {
            'detections': all_detections,
            'stats': dict(self.detection_stats),
            'total_frames': frame_number,
            'processing_time': processing_time,
            'avg_fps': avg_fps
        }
    
    def save_detection_results(self, results, output_dir):
        """Save detection results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save detections to CSV
        if results['detections']:
            df = pd.DataFrame(results['detections'])
            df.to_csv(output_path / 'live_detections.csv', index=False)
            print(f"✓ Saved: {output_path / 'live_detections.csv'}")
        
        # Save statistics to JSON
        stats_data = {
            'timestamp': datetime.now().isoformat(),
            'total_detections': len(results['detections']),
            'detection_counts': results['stats'],
            'processing_stats': {
                'total_frames': results['total_frames'],
                'processing_time': results['processing_time'],
                'average_fps': results['avg_fps']
            }
        }
        
        with open(output_path / 'detection_stats.json', 'w') as f:
            json.dump(stats_data, f, indent=2)
        print(f"✓ Saved: {output_path / 'detection_stats.json'}")

def main():
    """Main execution for live detection"""
    import sys
    
    # Check if video path provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Default: Use first available camera video
        video_dir = Path("CCTV Footage-20260529T160731Z-3-00144614ea/CCTV Footage")
        if video_dir.exists():
            video_files = list(video_dir.glob("*.mp4"))
            if video_files:
                video_path = video_files[0]
                print(f"Using default video: {video_path.name}")
            else:
                print("✗ No video files found!")
                print("Usage: python live_detection.py <video_path>")
                return
        else:
            print("✗ Video directory not found!")
            print("Usage: python live_detection.py <video_path>")
            return
    
    # Initialize detector
    detector = LiveCCTVDetector()
    
    # Process video
    output_video = Path("output/live_detection_output.mp4")
    output_video.parent.mkdir(exist_ok=True)
    
    results = detector.process_video_live(
        video_path=video_path,
        output_path=output_video,
        display=True,
        save_video=True
    )
    
    if results:
        # Save results
        detector.save_detection_results(results, "output")
        
        print(f"\n{'='*70}")
        print("OUTPUT FILES")
        print(f"{'='*70}")
        print(f"✓ Processed video: {output_video}")
        print(f"✓ Detection data: output/live_detections.csv")
        print(f"✓ Statistics: output/detection_stats.json")

if __name__ == "__main__":
    main()
