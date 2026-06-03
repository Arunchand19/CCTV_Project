from flask import Flask, render_template, request, jsonify, send_file, Response
import os
from werkzeug.utils import secure_filename
from event_detector import get_detector
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
current_video_path = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    global current_video_path
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        current_video_path = filepath
        
        # Reset detector
        detector = get_detector()
        detector.stop_flag = False
        detector.events = []
        detector.visitors = {}
        detector.frame_count = 0
        detector.entry_count = 0
        detector.exit_count = 0
        detector.unique_visitors = set()
        detector.next_visitor_id = 1
        
        return jsonify({'success': True, 'message': 'Video uploaded successfully'})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/video_feed')
def video_feed():
    global current_video_path
    if current_video_path and os.path.exists(current_video_path):
        detector = get_detector()
        return Response(detector.generate_frames(current_video_path),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return "No video available", 404

@app.route('/stop_processing', methods=['POST'])
def stop_processing():
    detector = get_detector()
    detector.stop_processing()
    return jsonify({'success': True, 'message': 'Processing stopped'})

@app.route('/generate_analytics', methods=['POST'])
def generate_analytics():
    global current_video_path
    
    if not current_video_path:
        return jsonify({'error': 'No video to process'}), 400
    
    try:
        detector = get_detector()
        
        # Check if we have any data to generate analytics from
        if detector.frame_count == 0:
            return jsonify({'error': 'No frames processed yet. Please process video first.'}), 400
        
        analytics = detector.generate_analytics(current_video_path, app.config['OUTPUT_FOLDER'])
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating analytics: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

@app.route('/results')
def get_results():
    analytics_path = os.path.join(app.config['OUTPUT_FOLDER'], 'analytics.json')
    events_path = os.path.join(app.config['OUTPUT_FOLDER'], 'events.json')
    
    if os.path.exists(analytics_path) and os.path.exists(events_path):
        with open(analytics_path, 'r') as f:
            analytics = json.load(f)
        with open(events_path, 'r') as f:
            events = json.load(f)
        return jsonify({
            'analytics': analytics,
            'events': events
        })
    return jsonify({'error': 'No results found'}), 404

@app.route('/heatmap')
def get_heatmap():
    heatmap_path = os.path.join(app.config['OUTPUT_FOLDER'], 'heatmap.png')
    if os.path.exists(heatmap_path):
        return send_file(heatmap_path, mimetype='image/png')
    return "No heatmap available", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
