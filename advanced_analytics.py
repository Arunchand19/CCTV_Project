import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter

class AdvancedAnalytics:
    def __init__(self, positions_df):
        self.positions_df = positions_df
        
    def create_heatmap_overlay(self, camera_id, output_path):
        """Create heatmap overlay on first frame"""
        heatmap = np.zeros((480, 640))
        camera_data = self.positions_df[self.positions_df['camera'] == camera_id]
        
        for _, row in camera_data.iterrows():
            x, y = int(row['x']), int(row['y'])
            if 0 <= x < 640 and 0 <= y < 480:
                heatmap[y, x] += 1
        
        from scipy.ndimage import gaussian_filter
        heatmap = gaussian_filter(heatmap, sigma=15)
        
        # Normalize
        if heatmap.max() > 0:
            heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # Save
        cv2.imwrite(str(output_path / f'{camera_id}_heatmap.png'), heatmap_color)
        return heatmap_color
    
    def analyze_customer_flow(self):
        """Analyze customer flow patterns"""
        self.positions_df = self.positions_df.sort_values(['camera', 'timestamp'])
        
        # Calculate movement between zones
        zone_transitions = []
        prev_zone = None
        
        for zone in self.positions_df['zone'].values:
            if prev_zone and zone != prev_zone:
                zone_transitions.append((prev_zone, zone))
            prev_zone = zone
        
        transition_counts = Counter(zone_transitions)
        
        return {
            'transitions': dict(transition_counts),
            'most_common_path': transition_counts.most_common(1)[0] if transition_counts else None
        }
    
    def calculate_zone_efficiency(self):
        """Calculate zone efficiency metrics"""
        zone_stats = self.positions_df.groupby('zone').agg({
            'timestamp': ['count', 'min', 'max']
        })
        zone_stats.columns = ['visits', 'first_visit', 'last_visit']
        zone_stats['duration'] = zone_stats['last_visit'] - zone_stats['first_visit']
        zone_stats['visit_rate'] = zone_stats['visits'] / zone_stats['duration'].replace(0, 1)
        
        return zone_stats
    
    def identify_hotspots(self, threshold=0.7):
        """Identify high-activity hotspots"""
        hotspots = []
        
        for camera in self.positions_df['camera'].unique():
            camera_data = self.positions_df[self.positions_df['camera'] == camera]
            
            # Create density grid
            grid = np.zeros((48, 64))
            for _, row in camera_data.iterrows():
                x, y = int(row['x'] / 10), int(row['y'] / 10)
                if 0 <= x < 64 and 0 <= y < 48:
                    grid[y, x] += 1
            
            # Find hotspots
            max_density = grid.max()
            hotspot_mask = grid > (max_density * threshold)
            hotspot_coords = np.argwhere(hotspot_mask)
            
            for coord in hotspot_coords:
                hotspots.append({
                    'camera': camera,
                    'zone': camera_data.iloc[0]['zone'],
                    'x': coord[1] * 10,
                    'y': coord[0] * 10,
                    'density': grid[coord[0], coord[1]]
                })
        
        return pd.DataFrame(hotspots)
    
    def generate_peak_hours(self):
        """Identify peak activity hours"""
        self.positions_df['hour'] = (self.positions_df['timestamp'] // 3600).astype(int)
        hourly_activity = self.positions_df.groupby('hour').size()
        
        peak_hour = hourly_activity.idxmax()
        peak_count = hourly_activity.max()
        
        return {
            'peak_hour': peak_hour,
            'peak_count': peak_count,
            'hourly_distribution': hourly_activity.to_dict()
        }

def create_dashboard_report(positions_df, output_dir):
    """Create comprehensive dashboard"""
    analytics = AdvancedAnalytics(positions_df)
    output_path = Path(output_dir)
    
    # Create heatmaps for all cameras
    print("Generating heatmaps...")
    for camera in positions_df['camera'].unique():
        analytics.create_heatmap_overlay(camera, output_path)
    
    # Analyze flow
    print("Analyzing customer flow...")
    flow_analysis = analytics.analyze_customer_flow()
    
    # Zone efficiency
    print("Calculating zone efficiency...")
    zone_efficiency = analytics.calculate_zone_efficiency()
    zone_efficiency.to_csv(output_path / 'zone_efficiency.csv')
    
    # Hotspots
    print("Identifying hotspots...")
    hotspots = analytics.identify_hotspots()
    if len(hotspots) > 0:
        hotspots.to_csv(output_path / 'hotspots.csv', index=False)
    
    # Peak hours
    print("Analyzing peak hours...")
    peak_hours = analytics.generate_peak_hours()
    
    # Create summary visualization
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Zone visits
    zone_counts = positions_df['zone'].value_counts()
    axes[0, 0].bar(range(len(zone_counts)), zone_counts.values)
    axes[0, 0].set_xticks(range(len(zone_counts)))
    axes[0, 0].set_xticklabels(zone_counts.index, rotation=45, ha='right')
    axes[0, 0].set_title('Zone-wise Customer Visits')
    axes[0, 0].set_ylabel('Number of Detections')
    
    # Temporal distribution
    if 'hour' in positions_df.columns:
        hourly = positions_df.groupby('hour').size()
        axes[0, 1].plot(hourly.index, hourly.values, marker='o')
        axes[0, 1].set_title('Hourly Activity Distribution')
        axes[0, 1].set_xlabel('Hour')
        axes[0, 1].set_ylabel('Activity Count')
        axes[0, 1].grid(True, alpha=0.3)
    
    # Zone efficiency
    if len(zone_efficiency) > 0:
        axes[1, 0].bar(range(len(zone_efficiency)), zone_efficiency['visit_rate'].values)
        axes[1, 0].set_xticks(range(len(zone_efficiency)))
        axes[1, 0].set_xticklabels(zone_efficiency.index, rotation=45, ha='right')
        axes[1, 0].set_title('Zone Visit Rate')
        axes[1, 0].set_ylabel('Visits per Second')
    
    # Camera distribution
    camera_counts = positions_df['camera'].value_counts()
    axes[1, 1].pie(camera_counts.values, labels=camera_counts.index, autopct='%1.1f%%')
    axes[1, 1].set_title('Camera Coverage Distribution')
    
    plt.tight_layout()
    plt.savefig(output_path / 'dashboard_summary.png', dpi=150)
    plt.close()
    
    return {
        'flow_analysis': flow_analysis,
        'zone_efficiency': zone_efficiency.to_dict(),
        'peak_hours': peak_hours,
        'hotspots_count': len(hotspots)
    }

if __name__ == "__main__":
    # Load data
    positions_df = pd.read_csv('output/customer_positions.csv')
    
    # Generate dashboard
    dashboard_data = create_dashboard_report(positions_df, 'output')
    
    print("Dashboard generated successfully!")
