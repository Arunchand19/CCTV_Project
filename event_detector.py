import cv2
import numpy as np
from pathlib import Path
import json
from collections import defaultdict
from datetime import datetime, timezone
import uuid

class EventBasedDetector:
    def __init__(self):
        self.stop_flag = False
        self.events = []
        self.visitors = {}  # visitor_id -> visitor data
        self.zones = {
            'ENTRANCE': {'region': (0, 0, 320, 480)},
            'ZONE_A': {'region': (320, 0, 640, 480)},
            'ZONE_B': {'region': (640, 0, 960, 480)},
            'EXIT': {'region': (960, 0, 1280, 480)}
        }
        self.next_visitor_id = 1
        self.frame_count = 0
        self.session_id = str(uuid.uuid4())
        
        # Analytics
        self.zone_visitors = defaultdict(int)
        self.zone_dwell_times = defaultdict(list)
        self.entry_count = 0
        self.exit_count = 0
        self.unique_visitors = set()
        
        # YOLO
        self.net = None
        self.classes = []
        self.load_yolo()
    
    def load_yolo(self):
        """Load YOLO model"""
        try:
            weights_path = "yolov3.weights"
            config_path = "yolov3.cfg"
            names_path = "coco.names"
            
            if Path(weights_path).exists() and Path(config_path).exists():
                self.net = cv2.dnn.readNet(weights_path, config_path)
                with open(names_path, 'r') as f:
                    self.classes = [line.strip() for line in f.readlines()]
        except:
            self.net = None
    
    def get_zone_from_position(self, x, y):
        """Determine which zone a position belongs to"""
        for zone_name, zone_data in self.zones.items():
            zx, zy, zw, zh = zone_data['region']
            if zx <= x <= zx + zw and zy <= y <= zy + zh:
                return zone_name
        return None
    
    def calculate_iou(self, box1, box2):
        """Calculate IoU between boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = w1 * h1 + w2 * h2 - intersection
        return intersection / union if union > 0 else 0.0
    
    def match_visitor(self, bbox, confidence):
        """Match or create visitor - AGGRESSIVE matching to prevent duplicate counting"""
        x, y, w, h = bbox
        center_x = x + w // 2
        center_y = y + h // 2
        current_zone = self.get_zone_from_position(center_x, center_y)
        
        best_match = None
        best_score = 0.0
        
        # Check ALL existing visitors with very lenient matching
        for visitor_id, visitor in self.visitors.items():
            v_x, v_y, v_w, v_h = visitor['last_bbox']
            v_center_x = v_x + v_w // 2
            v_center_y = v_y + v_h // 2
            
            # Calculate multiple similarity metrics
            
            # 1. Distance between centers
            distance = np.sqrt((center_x - v_center_x)**2 + (center_y - v_center_y)**2)
            distance_score = max(0, 1 - (distance / 400))  # Increased threshold to 400 pixels
            
            # 2. Size similarity
            size1 = w * h
            size2 = v_w * v_h
            if max(size1, size2) > 0:
                size_ratio = min(size1, size2) / max(size1, size2)
            else:
                size_ratio = 0
            
            # 3. IoU (less weight)
            iou = self.calculate_iou(bbox, visitor['last_bbox'])
            
            # 4. Frame gap penalty (very lenient - up to 60 frames)
            frames_gap = self.frame_count - visitor['last_frame']
            if frames_gap < 60:
                gap_score = 1.0 - (frames_gap / 60)
            else:
                gap_score = 0.0
            
            # Combined score with emphasis on distance and size
            # If person is reasonably close and similar size, it's probably the same person
            score = (distance_score * 0.4) + (size_ratio * 0.4) + (iou * 0.1) + (gap_score * 0.1)
            
            # Very lenient threshold - if score > 0.3, consider it a match
            if score > best_score:
                best_score = score
                best_match = visitor_id
        
        # CRITICAL: Use very low threshold to aggressively match
        if best_match and best_score > 0.3:  # Lowered from 0.25
            # Update existing visitor
            visitor = self.visitors[best_match]
            visitor['last_bbox'] = bbox
            visitor['last_frame'] = self.frame_count
            visitor['last_zone'] = current_zone
            visitor['frames_seen'] = visitor.get('frames_seen', 1) + 1
            
            # Add to zones visited if new zone
            if current_zone and current_zone not in visitor['zones_visited']:
                visitor['zones_visited'].append(current_zone)
            
            return best_match, False  # Not a new visitor
        else:
            # Only create new visitor if really no match found
            visitor_id = f"VIS_{self.next_visitor_id:04d}"
            self.next_visitor_id += 1
            self.visitors[visitor_id] = {
                'id': visitor_id,
                'last_bbox': bbox,
                'last_frame': self.frame_count,
                'last_zone': current_zone,
                'entry_time': datetime.now(timezone.utc).isoformat(),
                'zones_visited': [current_zone] if current_zone else [],
                'confidence': confidence,
                'frames_seen': 1
            }
            self.unique_visitors.add(visitor_id)
            return visitor_id, True  # New visitor
    
    def emit_event(self, visitor_id, event_type, zone_id=None, dwell_ms=0, confidence=0.9):
        """Emit an event in required schema"""
        event = {
            "event_id": str(uuid.uuid4()),
            "store_id": "STORE_BLR_002",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": visitor_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zone_id": zone_id or "ENTRANCE",
            "dwell_ms": dwell_ms,
            "is_staff": False,
            "confidence": confidence,
            "metadata": {},
            "queue_depth": None,
            "sku_zone": None,
            "session_seq": len(self.events) + 1
        }
        self.events.append(event)
        return event
    
    def detect_yolo(self, frame):
        """Detect using YOLO"""
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        outputs = self.net.forward(output_layers)
        
        boxes, confidences, class_ids = [], [], []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5 and self.classes[class_id] == 'person':
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
                    'confidence': confidences[i]
                })
        return results
    
    def detect_background_subtraction(self, frame, bg_subtractor):
        """Fallback detection"""
        fg_mask = bg_subtractor.apply(frame)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        results = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1500:
                x, y, w, h = cv2.boundingRect(contour)
                results.append({
                    'bbox': [x, y, w, h],
                    'confidence': 0.8
                })
        return results
    
    def stop_processing(self):
        """Stop processing"""
        self.stop_flag = True
    
    def generate_frames(self, video_path):
        """Generate frames with detection"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video")
        
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        colors = {
            'ENTRANCE': (0, 255, 0),
            'ZONE_A': (255, 0, 255),
            'ZONE_B': (0, 255, 255),
            'EXIT': (255, 255, 0)
        }
        
        while not self.stop_flag:
            ret, frame = cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Detect
            if self.net:
                detections = self.detect_yolo(frame)
            else:
                detections = self.detect_background_subtraction(frame, bg_subtractor)
            
            # Process detections
            detected_count = 0
            for det in detections:
                x, y, w, h = det['bbox']
                confidence = det['confidence']
                
                visitor_id, is_new = self.match_visitor([x, y, w, h], confidence)
                detected_count += 1
                
                center_x = x + w // 2
                center_y = y + h // 2
                current_zone = self.get_zone_from_position(center_x, center_y)
                
                # Get visitor data
                visitor = self.visitors.get(visitor_id)
                previous_zone = visitor.get('last_zone') if visitor else None
                
                # Emit ENTRY event for new visitors
                if is_new:
                    self.emit_event(visitor_id, "ENTRY", current_zone, 0, confidence)
                    self.entry_count += 1
                
                # Emit EXIT event when visitor enters EXIT zone for the first time
                if current_zone == 'EXIT' and previous_zone != 'EXIT' and not is_new:
                    self.emit_event(visitor_id, "EXIT", current_zone, 0, confidence)
                    self.exit_count += 1
                
                # Draw
                color = colors.get(current_zone, (0, 165, 255))
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                label = f"{visitor_id}"
                if current_zone:
                    label += f" [{current_zone}]"
                
                cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw zones (light gray borders)
            for zone_name, zone_data in self.zones.items():
                zx, zy, zw, zh = zone_data['region']
                cv2.rectangle(frame, (zx, zy), (zx + zw, zy + zh), (100, 100, 100), 1)
                cv2.putText(frame, zone_name, (zx + 10, zy + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
            
            # Info overlay - TOP RIGHT (moved from top-left to avoid LIVE indicator overlap)
            info = [
                f"Frame: {self.frame_count}",
                f"Unique Visitors: {len(self.unique_visitors)}",
                f"Objects Detected: {detected_count}",
                f"Total Events: {len(self.events)}"
            ]
            
            # Calculate overlay dimensions
            overlay_width = 350
            overlay_height = 30 + len(info) * 25
            overlay_x = frame_width - overlay_width - 10
            overlay_y = 10
            
            # Black semi-transparent background
            overlay = frame.copy()
            cv2.rectangle(overlay, (overlay_x, overlay_y), (overlay_x + overlay_width, overlay_y + overlay_height), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
            
            y_offset = overlay_y + 20
            for line in info:
                cv2.putText(frame, line, (overlay_x + 10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 25
            
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        cap.release()
    
    def generate_analytics(self, video_path, output_dir="output"):
        """Generate analytics with accurate unique visitor count and exit tracking"""
        Path(output_dir).mkdir(exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Generate enhanced heatmap with Gaussian smoothing
        heatmap = np.zeros((height, width), dtype=np.float32)
        for visitor in self.visitors.values():
            x, y, w, h = visitor['last_bbox']
            frames_seen = visitor.get('frames_seen', 1)
            # Add weighted contribution based on dwell time
            for i in range(max(0, y), min(height, y + h)):
                for j in range(max(0, x), min(width, x + w)):
                    heatmap[i, j] += frames_seen
        
        if heatmap.max() > 0:
            # Apply Gaussian blur for smoother heatmap
            from scipy.ndimage import gaussian_filter
            heatmap_smooth = gaussian_filter(heatmap, sigma=20)
            
            # Normalize to 0-255
            heatmap_normalized = (heatmap_smooth / heatmap_smooth.max() * 255).astype(np.uint8)
            
            # Apply custom colormap for more attractive visualization
            heatmap_color = cv2.applyColorMap(heatmap_normalized, cv2.COLORMAP_JET)
            
            # Add transparency overlay effect
            # Create a base frame (black background)
            base = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Blend heatmap with base for better visibility
            alpha = 0.7
            blended = cv2.addWeighted(heatmap_color, alpha, base, 1 - alpha, 0)
            
            cv2.imwrite(f"{output_dir}/heatmap.png", blended)
        
        # Calculate zone metrics
        zone_metrics = {}
        for zone_name in self.zones.keys():
            zone_events = [e for e in self.events if e.get('zone_id') == zone_name]
            zone_visitors = set(e['visitor_id'] for e in zone_events)
            
            zone_metrics[zone_name] = {
                'total_visits': len(zone_events),
                'unique_visitors': len(zone_visitors)
            }
        
        # Calculate EXIT count properly
        # Count visitors who moved to EXIT zone or left the frame
        exit_count = 0
        for visitor in self.visitors.values():
            zones_visited = visitor.get('zones_visited', [])
            # Check if visitor reached EXIT zone
            if 'EXIT' in zones_visited:
                exit_count += 1
        
        # Also count EXIT events directly
        exit_events = [e for e in self.events if e.get('event_type') == 'EXIT']
        exit_count = max(exit_count, len(exit_events))
        
        self.exit_count = exit_count
        
        # Calculate average session duration
        total_duration = 0
        visitor_count = len(self.visitors)
        if visitor_count > 0:
            for visitor in self.visitors.values():
                frames_seen = visitor.get('frames_seen', 1)
                duration_seconds = frames_seen / fps
                total_duration += duration_seconds
            avg_duration = total_duration / visitor_count
        else:
            avg_duration = 0
        
        # Calculate conversion rate (exits / entries * 100)
        unique_visitor_count = len(self.unique_visitors)
        conversion_rate = 0
        if unique_visitor_count > 0:
            conversion_rate = (exit_count / unique_visitor_count) * 100
        
        analytics = {
            'session_id': self.session_id,
            'unique_visitors': unique_visitor_count,
            'entry_count': unique_visitor_count,
            'exit_count': exit_count,
            'total_events': len(self.events),
            'frames_processed': self.frame_count,
            'duration_seconds': self.frame_count / fps,
            'fps': fps,
            'zone_metrics': zone_metrics,
            'conversion_rate': conversion_rate,
            'avg_session_duration': avg_duration
        }
        
        # Save events
        with open(f"{output_dir}/events.json", 'w') as f:
            json.dump(self.events, f, indent=2)
        
        # Save analytics
        with open(f"{output_dir}/analytics.json", 'w') as f:
            json.dump(analytics, f, indent=2)
        
        # Save visitor summary for verification
        visitor_summary = {
            'total_unique_visitors': unique_visitor_count,
            'total_exits': exit_count,
            'visitors': [
                {
                    'id': v['id'],
                    'frames_seen': v.get('frames_seen', 1),
                    'zones_visited': v.get('zones_visited', []),
                    'entry_time': v.get('entry_time', '')
                }
                for v in self.visitors.values()
            ]
        }
        with open(f"{output_dir}/visitors.json", 'w') as f:
            json.dump(visitor_summary, f, indent=2)
        
        return analytics

# Global detector
detector = None

def get_detector():
    global detector
    if detector is None:
        detector = EventBasedDetector()
    return detector
