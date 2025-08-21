from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import sqlite3
import threading
import time
from datetime import datetime
import logging
from job_monitor import JobMonitor
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database and job monitor
db = Database()
job_monitor = JobMonitor(db, socketio)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/monitors', methods=['GET'])
def get_monitors():
    """Get all job monitors"""
    try:
        monitors = db.get_all_monitors()
        return jsonify({'success': True, 'data': monitors})
    except Exception as e:
        logger.error(f"Error getting monitors: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors', methods=['POST'])
def create_monitor():
    """Create a new job monitor"""
    try:
        data = request.json
        required_fields = ['name', 'url', 'keywords', 'check_interval']
        
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        monitor_id = db.create_monitor(
            name=data['name'],
            url=data['url'],
            keywords=data['keywords'],
            check_interval=data['check_interval'],
            selector=data.get('selector', ''),
            is_active=data.get('is_active', True)
        )
        
        # Start monitoring if active
        if data.get('is_active', True):
            job_monitor.start_monitor(monitor_id)
        
        return jsonify({'success': True, 'monitor_id': monitor_id})
    except Exception as e:
        logger.error(f"Error creating monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors/<int:monitor_id>', methods=['PUT'])
def update_monitor(monitor_id):
    """Update an existing job monitor"""
    try:
        data = request.json
        db.update_monitor(monitor_id, **data)
        
        # Restart monitor if it's active
        if data.get('is_active'):
            job_monitor.restart_monitor(monitor_id)
        else:
            job_monitor.stop_monitor(monitor_id)
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors/<int:monitor_id>', methods=['DELETE'])
def delete_monitor(monitor_id):
    """Delete a job monitor"""
    try:
        job_monitor.stop_monitor(monitor_id)
        db.delete_monitor(monitor_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors/<int:monitor_id>/toggle', methods=['POST'])
def toggle_monitor(monitor_id):
    """Toggle monitor active status"""
    try:
        current_status = db.get_monitor(monitor_id)['is_active']
        new_status = not current_status
        
        db.update_monitor(monitor_id, is_active=new_status)
        
        if new_status:
            job_monitor.start_monitor(monitor_id)
        else:
            job_monitor.stop_monitor(monitor_id)
        
        return jsonify({'success': True, 'is_active': new_status})
    except Exception as e:
        logger.error(f"Error toggling monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors/<int:monitor_id>/test', methods=['POST'])
def test_monitor(monitor_id):
    """Test a monitor configuration"""
    try:
        result = job_monitor.test_monitor(monitor_id)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"Error testing monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all detected jobs"""
    try:
        monitor_id = request.args.get('monitor_id')
        jobs = db.get_jobs(monitor_id)
        return jsonify({'success': True, 'data': jobs})
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get monitoring statistics"""
    try:
        stats = db.get_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to job monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

if __name__ == '__main__':
    # Initialize database tables
    db.init_tables()
    
    # Start active monitors
    job_monitor.start_all_active_monitors()
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
