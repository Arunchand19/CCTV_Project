import cv2
import numpy as np
from pathlib import Path
import json
from collections import defaultdict
import threading

class ObjectDetector:
    def __init__(self):
        self.stop_flag = False
        self.detections = []
        self.frame_count = 0
        self.object_counts = defaultdict(int)
        self.tracked_persons = []
        self.next_person_id = 1
        self.person_history = []  # Store person features for better tracking
        
        # YOLO configuration
        self.net = None
        self.classes = []
        self.load_yolo()
        
    def load_yolo(self):
        """Load YOLO model"""
        try:
            # Try to load YOLO weights
            weights_path = "yolov3.weights"
            config_path = "yolov3.cfg"
            names_path = "coco.names"
            
            if Path(weights_path).exists() and Path(config_path).exists():
                self.net = cv2.dnn.readNet(weights_path, config_path)
                with open(names_path, 'r') as f:
                    self.classes = [line.strip() for line in f.readlines()]
            else:
                print("YOLO files not found, using background subtraction")
                self.net = None
        except:
            self.net = None
    
    def stop_processing(self):
        """Stop video processing"""
        self.stop_flag = True
    
    def calculate_iou(self, box1, box2):
        """Calculate Intersection over Union between two bounding boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
    
    def calculate_distance(self, box1, box2):
        """Calculate distance between two bounding boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        center1 = (x1 + w1/2, y1 + h1/2)
        center2 = (x2 + w2/2, y2 + h2/2)
        return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
    
    def calculate_similarity(self, box1, box2):
        """Calculate similarity score between two bounding boxes"""
        # Combine IoU and distance metrics
        iou = self.calculate_iou(box1, box2)
        distance = self.calculate_distance(box1, box2)
        
        # Normalize distance (assume max reasonable distance is 300 pixels)
        normalized_distance = max(0, 1 - (distance / 300.0))
        
        # Size similarity
        size1 = box1[2] * box1[3]
        size2 = box2[2] * box2[3]
        size_similarity = min(size1, size2) / max(size1, size2) if max(size1, size2) > 0 else 0
        
        # Weighted combination
        similarity = (iou * 0.4) + (normalized_distance * 0.4) + (size_similarity * 0.2)
        return similarity
    
    def match_person(self, bbox, frame_roi=None, max_frames_missing=30):
        """Match detected person with tracked persons using multiple criteria"""
        best_match_id = None
        best_similarity = 0.0
        
        # Remove stale tracks (not seen for many frames)
        self.tracked_persons = [p for p in self.tracked_persons 
                               if self.frame_count - p['last_frame'] < max_frames_missing]
        
        # Find best match among existing persons
        for person in self.tracked_persons:
            similarity = self.calculate_similarity(bbox, person['last_bbox'])
            
            if similarity > best_similarity and similarity > 0.3:  # Threshold for matching
                best_similarity = similarity
                best_match_id = person['id']
        
        # If found a match, update that person
        if best_match_id is not None:
            for person in self.tracked_persons:
                if person['id'] == best_match_id:
                    person['last_bbox'] = bbox
                    person['frames_seen'] += 1
                    person['last_frame'] = self.frame_count
                    person['bboxes_history'].append(bbox)
                    # Keep only last 10 bboxes
                    if len(person['bboxes_history']) > 10:
                        person['bboxes_history'].pop(0)
                    return best_match_id
        
        # New person detected
        person_id = self.next_person_id
        self.next_person_id += 1
        self.tracked_persons.append({
            'id': person_id,
            'last_bbox': bbox,
            'frames_seen': 1,
            'last_frame': self.frame_count,
            'bboxes_history': [bbox]
        })
        return person_id
    
    def detect_yolo(self, frame):
        """Detect objects using YOLO"""
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        outputs = self.net.forward(output_layers)
        
        boxes = []
        confidences = []
        class_ids = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                results.append({
                    'bbox': boxes[i],
                    'class': self.classes[class_ids[i]],
                    'confidence': confidences[i]
                })
        
        return results
    
    def detect_background_subtraction(self, frame, bg_subtractor):
        """Fallback detection using background subtraction"""
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        results = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                results.append({
                    'bbox': [x, y, w, h],
                    'class': 'person',
                    'confidence': 0.8
                })
        
        return results
    
    def generate_frames(self, video_path):
        """Generate frames with object detection for live streaming"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        
        self.frame_count = 0
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        colors = {
            'person': (0, 255, 0),
            'cell phone': (255, 0, 255),
            'laptop': (0, 255, 255),
            'handbag': (255, 128, 0),
            'backpack': (128, 0, 255),
            'bottle': (0, 128, 255),
            'chair': (255, 255, 0),
            'default': (0, 165, 255)
        }
        
        while not self.stop_flag:
            ret, frame = cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Detect objects
            if self.net is not None:
                detections = self.detect_yolo(frame)
            else:
                detections = self.detect_background_subtraction(frame, bg_subtractor)
            
            frame_objects = defaultdict(int)
            frame_persons = []  # Track persons in current frame
            
            for det in detections:
                x, y, w, h = det['bbox']
                obj_class = det['class']
                confidence = det['confidence']
                
                # Track unique persons
                person_id = None
                if obj_class == 'person':
                    person_id = self.match_person([x, y, w, h])
                    frame_persons.append(person_id)
                else:
                    # Only count non-person objects once per frame appearance
                    frame_objects[obj_class] += 1
                
                # Draw bounding box
                color = colors.get(obj_class, colors['default'])
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Label
                if person_id:
                    label = f"Person #{person_id}"
                else:
                    label = f"{obj_class.title()}"
                
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Store detection
                self.detections.append({
                    'frame': self.frame_count,
                    'object': obj_class,
                    'person_id': person_id,
                    'bbox': [x, y, w, h],
                    'timestamp': self.frame_count / fps
                })
            
            # Update object counts (only count objects once per detection in frame)
            for obj_type, count in frame_objects.items():
                if obj_type not in ['person']:
                    # For objects, we count total occurrences but show in summary
                    pass
            
            # Info overlay
            info_lines = [
                f"Frame: {self.frame_count}",
                f"Unique Persons: {len(self.tracked_persons)}",
                f"Current Frame Objects: {len(frame_persons)}"
            ]
            
            y_offset = 30
            cv2.rectangle(frame, (10, 10), (350, 30 + len(info_lines) * 25), (0, 0, 0), -1)
            for line in info_lines:
                cv2.putText(frame, line, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 25
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        cap.release()
    
    def generate_analytics(self, video_path, output_dir="output"):
        """Generate final analytics and heatmap"""
        Path(output_dir).mkdir(exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Create heatmap
        heatmap = np.zeros((height, width), dtype=np.float32)
        for det in self.detections:
            if det['object'] == 'person':
                x, y, w, h = det['bbox']
                heatmap[y:y+h, x:x+w] += 1
        
        if heatmap.max() > 0:
            heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            cv2.imwrite(f"{output_dir}/heatmap.png", heatmap_color)
        
        # Calculate object counts properly
        object_summary = defaultdict(int)
        seen_objects_per_frame = defaultdict(set)
        
        for det in self.detections:
            obj_class = det['object']
            frame_num = det['frame']
            
            if obj_class != 'person':
                # Count unique objects per frame, then sum
                seen_objects_per_frame[obj_class].add(frame_num)
        
        # Total unique object detections
        for obj_class, frames in seen_objects_per_frame.items():
            object_summary[obj_class] = len(frames)
        
        # Calculate analytics
        analytics = {
            'total_frames_processed': self.frame_count,
            'unique_persons': len(self.tracked_persons),
            'total_detections': len(self.detections),
            'objects_detected': {
                'person': len(self.tracked_persons),
                **dict(object_summary)
            },
            'video_duration': self.frame_count / fps,
            'fps': fps,
            'resolution': f"{width}x{height}"
        }
        
        # Save results
        with open(f"{output_dir}/detections.json", 'w') as f:
            json.dump({
                'analytics': analytics,
                'detections': self.detections,
                'unique_persons': [{'id': p['id'], 'frames_seen': p['frames_seen']} for p in self.tracked_persons]
            }, f, indent=2)
        
        return analytics

# Global detector instance
detector = None

def get_detector():
    global detector
    if detector is None:
        detector = ObjectDetector()
    return detector
