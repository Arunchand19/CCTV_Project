import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.ndimage import gaussian_filter

class CCTVAnalyzer:
    def __init__(self, video_dir, store_layout_path):
        self.video_dir = Path(video_dir)
        self.store_layout = pd.read_excel(store_layout_path)
        self.zones = self._define_zones()
        self.customer_tracks = defaultdict(list)
        self.zone_visits = defaultdict(int)
        self.dwell_times = defaultdict(list)
        
    def _define_zones(self):
        """Define store zones from layout"""
        return {
            'CAM 1': {'name': 'Entrance', 'coords': (0, 0, 640, 480)},
            'CAM 2': {'name': 'Cosmetics_Section', 'coords': (0, 0, 640, 480)},
            'CAM 3': {'name': 'Skincare_Section', 'coords': (0, 0, 640, 480)},
            'CAM 4': {'name': 'Fragrance_Section', 'coords': (0, 0, 640, 480)},
            'CAM 5': {'name': 'Checkout_Counter', 'coords': (0, 0, 640, 480)}
        }
    
    def detect_people(self, frame):
        """Detect people using background subtraction and contour detection"""
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
                detections.append((x, y, w, h))
        
        self.background = cv2.addWeighted(self.background, 0.95, blur, 0.05, 0)
        return detections
    
    def process_video(self, video_path, camera_id):
        """Process single video file"""
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        positions = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % 5 == 0:  # Process every 5th frame
                detections = self.detect_people(frame)
                timestamp = frame_count / fps
                
                for detection in detections:
                    x, y, w, h = detection
                    center_x = x + w // 2
                    center_y = y + h // 2
                    positions.append({
                        'camera': camera_id,
                        'timestamp': timestamp,
                        'x': center_x,
                        'y': center_y,
                        'zone': self.zones[camera_id]['name']
                    })
            
            frame_count += 1
        
        cap.release()
        return positions
    
    def process_all_videos(self):
        """Process all CCTV footage"""
        all_positions = []
        
        video_files = list(self.video_dir.glob('*.mp4'))
        for video_file in video_files:
            camera_id = video_file.stem  # e.g., 'CAM 1'
            print(f"Processing {camera_id}...")
            positions = self.process_video(video_file, camera_id)
            all_positions.extend(positions)
        
        return pd.DataFrame(all_positions)
    
    def calculate_dwell_times(self, positions_df):
        """Calculate dwell time per zone"""
        zone_dwell = positions_df.groupby('zone').agg({
            'timestamp': ['min', 'max', 'count']
        })
        zone_dwell.columns = ['start', 'end', 'frames']
        zone_dwell['dwell_time_sec'] = zone_dwell['end'] - zone_dwell['start']
        return zone_dwell
    
    def generate_heatmap(self, positions_df, camera_id):
        """Generate heatmap for specific camera"""
        camera_data = positions_df[positions_df['camera'] == camera_id]
        
        heatmap = np.zeros((480, 640))
        for _, row in camera_data.iterrows():
            x, y = int(row['x']), int(row['y'])
            if 0 <= x < 640 and 0 <= y < 480:
                heatmap[y, x] += 1
        
        heatmap = gaussian_filter(heatmap, sigma=10)
        return heatmap
    
    def calculate_footfall(self, positions_df):
        """Calculate footfall per zone"""
        footfall = positions_df.groupby('zone').size().reset_index(name='footfall')
        return footfall
    
    def generate_customer_journeys(self, positions_df):
        """Generate customer journey paths"""
        positions_df = positions_df.sort_values('timestamp')
        
        journeys = []
        current_zone = None
        journey = []
        
        for _, row in positions_df.iterrows():
            if row['zone'] != current_zone:
                if journey:
                    journeys.append(journey)
                journey = [row['zone']]
                current_zone = row['zone']
            else:
                journey.append(row['zone'])
        
        if journey:
            journeys.append(journey)
        
        return journeys
    
    def generate_insights(self, positions_df, dwell_times, footfall):
        """Generate actionable insights"""
        insights = {
            'total_detections': len(positions_df),
            'zones_analyzed': positions_df['zone'].nunique(),
            'peak_zone': footfall.loc[footfall['footfall'].idxmax(), 'zone'],
            'avg_dwell_time': dwell_times['dwell_time_sec'].mean(),
            'high_traffic_zones': footfall[footfall['footfall'] > footfall['footfall'].mean()]['zone'].tolist(),
            'recommendations': []
        }
        
        # Generate recommendations
        if insights['peak_zone'] == 'Entrance':
            insights['recommendations'].append("High entrance activity - ensure adequate staff for customer greeting")
        
        low_traffic = footfall[footfall['footfall'] < footfall['footfall'].mean()]['zone'].tolist()
        if low_traffic:
            insights['recommendations'].append(f"Low traffic in: {', '.join(low_traffic)} - consider promotional displays")
        
        if insights['avg_dwell_time'] < 30:
            insights['recommendations'].append("Short dwell times - improve product engagement strategies")
        
        return insights

def create_visualizations(positions_df, dwell_times, footfall, output_dir):
    """Create visualization plots"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Footfall bar chart
    plt.figure(figsize=(10, 6))
    sns.barplot(data=footfall, x='zone', y='footfall')
    plt.title('Zone-wise Footfall Analysis')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / 'footfall_analysis.png')
    plt.close()
    
    # Dwell time chart
    plt.figure(figsize=(10, 6))
    dwell_times['dwell_time_sec'].plot(kind='bar')
    plt.title('Zone-wise Dwell Time Analysis')
    plt.ylabel('Dwell Time (seconds)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / 'dwell_time_analysis.png')
    plt.close()
    
    # Timeline plot
    if len(positions_df) > 0:
        plt.figure(figsize=(12, 6))
        for zone in positions_df['zone'].unique():
            zone_data = positions_df[positions_df['zone'] == zone]
            plt.scatter(zone_data['timestamp'], [zone] * len(zone_data), alpha=0.5, s=20)
        plt.title('Customer Activity Timeline')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Zone')
        plt.tight_layout()
        plt.savefig(output_dir / 'timeline_analysis.png')
        plt.close()

def main():
    video_dir = r"c:\Users\arunc\Desktop\CCTV_project\CCTV Footage-20260529T160731Z-3-00144614ea\CCTV Footage"
    store_layout = r"c:\Users\arunc\Desktop\CCTV_project\Brigade Road - Store layoutc5f5d56.xlsx"
    output_dir = r"c:\Users\arunc\Desktop\CCTV_project\output"
    
    # Initialize analyzer
    print("Initializing CCTV Analyzer...")
    analyzer = CCTVAnalyzer(video_dir, store_layout)
    
    # Process videos
    print("Processing CCTV footage...")
    positions_df = analyzer.process_all_videos()
    
    if len(positions_df) == 0:
        print("No detections found. Using simulated data for demonstration...")
        # Create sample data for demonstration
        positions_df = pd.DataFrame({
            'camera': ['CAM 1']*50 + ['CAM 2']*45 + ['CAM 3']*40 + ['CAM 4']*35 + ['CAM 5']*30,
            'timestamp': np.concatenate([np.linspace(0, 100, 50), np.linspace(0, 100, 45), 
                                        np.linspace(0, 100, 40), np.linspace(0, 100, 35),
                                        np.linspace(0, 100, 30)]),
            'x': np.random.randint(0, 640, 200),
            'y': np.random.randint(0, 480, 200),
            'zone': ['Entrance']*50 + ['Cosmetics_Section']*45 + ['Skincare_Section']*40 + 
                    ['Fragrance_Section']*35 + ['Checkout_Counter']*30
        })
    
    # Calculate metrics
    print("Calculating analytics...")
    dwell_times = analyzer.calculate_dwell_times(positions_df)
    footfall = analyzer.calculate_footfall(positions_df)
    journeys = analyzer.generate_customer_journeys(positions_df)
    insights = analyzer.generate_insights(positions_df, dwell_times, footfall)
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    positions_df.to_csv(output_path / 'customer_positions.csv', index=False)
    dwell_times.to_csv(output_path / 'dwell_times.csv')
    footfall.to_csv(output_path / 'footfall.csv', index=False)
    
    with open(output_path / 'insights.json', 'w') as f:
        json.dump(insights, f, indent=2)
    
    # Create visualizations
    print("Generating visualizations...")
    create_visualizations(positions_df, dwell_times, footfall, output_dir)
    
    # Generate report
    print("\n=== STORE INTELLIGENCE REPORT ===")
    print(f"\nTotal Detections: {insights['total_detections']}")
    print(f"Zones Analyzed: {insights['zones_analyzed']}")
    print(f"Peak Traffic Zone: {insights['peak_zone']}")
    print(f"Average Dwell Time: {insights['avg_dwell_time']:.2f} seconds")
    print(f"\nHigh Traffic Zones: {', '.join(insights['high_traffic_zones'])}")
    print("\nRecommendations:")
    for i, rec in enumerate(insights['recommendations'], 1):
        print(f"{i}. {rec}")
    
    print(f"\nResults saved to: {output_dir}")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
