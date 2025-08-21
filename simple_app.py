#!/usr/bin/env python3
"""
Simplified Job Monitor Application
This version runs without selenium dependencies for initial testing.
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import sqlite3
import threading
import time
from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup
from database import Database
import hashlib
import random
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

# Simple HTML template for testing
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Monitor - Simple Mode</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #cce7ff; color: #004085; border: 1px solid #b3d7ff; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        input[type="text"], input[type="url"], input[type="number"] { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        label { font-weight: bold; }
        .monitor { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .job { background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 5px; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
</head>
<body>
    <div class="container">
        <h1>🔍 Job Monitor - Simple Mode</h1>
        <div class="status info">
            <strong>Status:</strong> <span id="status">Connecting...</span>
        </div>
        
        <h2>Add Monitor</h2>
        <form id="monitorForm">
            <label>Name:</label>
            <input type="text" id="name" required placeholder="e.g., Google Careers Monitor">
            
            <label>URL:</label>
            <input type="url" id="url" required placeholder="https://...">
            
            <label>Keywords (comma-separated):</label>
            <input type="text" id="keywords" required placeholder="intern, software engineer, new grad">
            
            <label>Check Interval (seconds):</label>
            <input type="number" id="interval" value="30" min="10">
            
            <button type="submit">Add Monitor</button>
            <button type="button" onclick="loadGooglePreset()">Load Google Careers Preset</button>
        </form>
        
        <h2>Active Monitors</h2>
        <div id="monitors"></div>
        
        <h2>Recent Jobs</h2>
        <div id="jobs"></div>
        
        <h2>Notifications</h2>
        <div id="notifications"></div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            document.getElementById('status').innerHTML = '✅ Connected';
            loadMonitors();
            loadJobs();
        });
        
        socket.on('disconnect', function() {
            document.getElementById('status').innerHTML = '❌ Disconnected';
        });
        
        socket.on('new_job', function(data) {
            addNotification('🎉 New Job Found!', data.job.title + ' at ' + data.job.company);
            loadJobs();
            
            // Play notification sound
            try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+Dux2QcBz2P1+fNeysFJXfH8N+QQgkTXrTp7arWFAlFnt7tx2IdBz2P1+fNeysFJHfH8N2QQQkUXrTo7KJWFQpFn+Dux2IcBz+P1/LNeSsFJHfH8N2QQAoUXrPp7KlXFQpFn+Dux2QcBj+Q1/LNeioFJXbH8N2QQAkTXrTp7KlWFQtGnt/tx2IcBz2P1+fNeysFJXbH8N2QQAoTXrTo7KlXFQtFnt7tx2IdBz2P1+fNeysFJXbH8N2QQgkTXbPq7KlXFQpFnt7tyl2dyq')
                audio.play().catch(() => {})
            } catch(e) {}
        });
        
        socket.on('monitor_update', function(data) {
            if (data.new_jobs > 0) {
                addNotification('📊 Monitor Update', data.new_jobs + ' new jobs found');
            }
        });
        
        socket.on('monitor_error', function(data) {
            addNotification('❌ Monitor Error', data.error);
        });
        
        function loadGooglePreset() {
            document.getElementById('name').value = 'Google Careers - Software Engineering Internships';
            document.getElementById('url').value = 'https://www.google.com/about/careers/applications/jobs/results/?jlo=en_US&q=Software+Engineer&target_level=INTERN_AND_APPRENTICE';
            document.getElementById('keywords').value = 'intern, internship, software engineer, new grad';
        }
        
        document.getElementById('monitorForm').onsubmit = function(e) {
            e.preventDefault();
            
            const data = {
                name: document.getElementById('name').value,
                url: document.getElementById('url').value,
                keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()),
                check_interval: parseInt(document.getElementById('interval').value),
                is_active: true
            };
            
            fetch('/api/monitors', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(response => response.json())
            .then(result => {
                if (result.success) {
                    addNotification('✅ Success', 'Monitor created successfully');
                    document.getElementById('monitorForm').reset();
                    loadMonitors();
                } else {
                    addNotification('❌ Error', result.error);
                }
            });
        };
        
        function loadMonitors() {
            fetch('/api/monitors')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('monitors');
                container.innerHTML = '';
                
                data.data.forEach(monitor => {
                    const div = document.createElement('div');
                    div.className = 'monitor';
                    div.innerHTML = `
                        <strong>${monitor.name}</strong> ${monitor.is_active ? '🟢' : '🔴'}
                        <br><small>${monitor.url}</small>
                        <br>Keywords: ${monitor.keywords.join(', ')}
                        <br>Interval: ${monitor.check_interval}s
                        <br><button onclick="toggleMonitor(${monitor.id})">${monitor.is_active ? 'Stop' : 'Start'}</button>
                        <button onclick="testMonitor(${monitor.id})">Test</button>
                        <button onclick="deleteMonitor(${monitor.id})">Delete</button>
                    `;
                    container.appendChild(div);
                });
            });
        }
        
        function loadJobs() {
            fetch('/api/jobs')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('jobs');
                container.innerHTML = '';
                
                data.data.slice(0, 10).forEach(job => {
                    const div = document.createElement('div');
                    div.className = 'job';
                    div.innerHTML = `
                        <strong>${job.title}</strong>
                        <br>Company: ${job.company || 'Unknown'}
                        <br>Location: ${job.location || 'Unknown'}
                        <br>Found: ${new Date(job.detected_at).toLocaleString()}
                        ${job.url ? `<br><a href="${job.url}" target="_blank">View Job</a>` : ''}
                    `;
                    container.appendChild(div);
                });
            });
        }
        
        function toggleMonitor(id) {
            fetch(`/api/monitors/${id}/toggle`, {method: 'POST'})
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    loadMonitors();
                    addNotification('✅ Success', 'Monitor toggled');
                }
            });
        }
        
        function testMonitor(id) {
            addNotification('🧪 Testing', 'Running test scrape...');
            fetch(`/api/monitors/${id}/test`, {method: 'POST'})
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    addNotification('✅ Test Complete', `Found ${result.data.jobs_found} jobs`);
                } else {
                    addNotification('❌ Test Failed', result.error);
                }
            });
        }
        
        function deleteMonitor(id) {
            if (confirm('Delete this monitor?')) {
                fetch(`/api/monitors/${id}`, {method: 'DELETE'})
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        loadMonitors();
                        addNotification('✅ Success', 'Monitor deleted');
                    }
                });
            }
        }
        
        function addNotification(title, message) {
            const container = document.getElementById('notifications');
            const div = document.createElement('div');
            div.className = 'status info';
            div.innerHTML = `<strong>${title}:</strong> ${message}`;
            container.insertBefore(div, container.firstChild);
            
            // Remove after 5 seconds
            setTimeout(() => {
                if (div.parentNode) div.parentNode.removeChild(div);
            }, 5000);
        }
    </script>
</body>
</html>
"""

# Initialize database
db = Database()

class SimpleJobMonitor:
    def __init__(self, database, socketio):
        self.db = database
        self.socketio = socketio
        self.active_monitors = {}
    
    def start_monitor(self, monitor_id: int):
        """Start monitoring a specific job monitor"""
        monitor = self.db.get_monitor(monitor_id)
        if not monitor:
            logger.error(f"Monitor {monitor_id} not found")
            return
        
        if monitor_id in self.active_monitors:
            logger.info(f"Monitor {monitor_id} is already running")
            return
        
        # Create and start monitor thread
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(monitor, stop_event),
            daemon=True
        )
        
        self.active_monitors[monitor_id] = {
            'thread': monitor_thread,
            'stop_event': stop_event,
            'monitor': monitor
        }
        
        monitor_thread.start()
        logger.info(f"Started monitor {monitor_id}: {monitor['name']}")
        
        # Emit status update
        self.socketio.emit('monitor_status', {
            'monitor_id': monitor_id,
            'status': 'started',
            'message': f"Monitor '{monitor['name']}' started"
        })
    
    def stop_monitor(self, monitor_id: int):
        """Stop monitoring a specific job monitor"""
        if monitor_id not in self.active_monitors:
            logger.info(f"Monitor {monitor_id} is not running")
            return
        
        # Signal stop and wait for thread to finish
        self.active_monitors[monitor_id]['stop_event'].set()
        self.active_monitors[monitor_id]['thread'].join(timeout=5)
        
        # Remove from active monitors
        del self.active_monitors[monitor_id]
        
        logger.info(f"Stopped monitor {monitor_id}")
        
        # Emit status update
        self.socketio.emit('monitor_status', {
            'monitor_id': monitor_id,
            'status': 'stopped',
            'message': f"Monitor stopped"
        })
    
    def test_monitor(self, monitor_id: int):
        """Test a monitor configuration"""
        monitor = self.db.get_monitor(monitor_id)
        if not monitor:
            raise Exception(f"Monitor {monitor_id} not found")
        
        try:
            # Run a single scrape
            results = self._scrape_jobs(monitor)
            
            return {
                'success': True,
                'jobs_found': len(results['jobs']),
                'jobs': results['jobs'][:5],  # Return first 5 for preview
                'method': 'requests'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _monitor_loop(self, monitor, stop_event):
        """Main monitoring loop for a single monitor"""
        monitor_id = monitor['id']
        check_interval = monitor['check_interval']
        
        logger.info(f"Starting monitor loop for {monitor['name']} (ID: {monitor_id})")
        
        while not stop_event.is_set():
            try:
                # Scrape jobs
                start_time = time.time()
                results = self._scrape_jobs(monitor)
                scrape_time = time.time() - start_time
                
                jobs_found = len(results['jobs'])
                new_jobs = 0
                
                # Process and save new jobs
                for job in results['jobs']:
                    # Create content hash for deduplication
                    content_hash = self._create_content_hash(job)
                    
                    # Check if job already exists
                    if not self.db.job_exists(content_hash):
                        job_id = self.db.save_job(
                            monitor_id=monitor_id,
                            title=job.get('title', ''),
                            url=job.get('url', ''),
                            company=job.get('company', ''),
                            location=job.get('location', ''),
                            description=job.get('description', ''),
                            content_hash=content_hash
                        )
                        
                        if job_id:
                            new_jobs += 1
                            # Emit new job notification
                            self.socketio.emit('new_job', {
                                'monitor_id': monitor_id,
                                'monitor_name': monitor['name'],
                                'job': job,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"New job found for monitor {monitor_id}: {job.get('title', 'Unknown')}")
                
                # Record monitor run
                self.db.record_monitor_run(
                    monitor_id=monitor_id,
                    jobs_found=jobs_found,
                    new_jobs=new_jobs,
                    success=True
                )
                
                # Emit status update
                self.socketio.emit('monitor_update', {
                    'monitor_id': monitor_id,
                    'jobs_found': jobs_found,
                    'new_jobs': new_jobs,
                    'scrape_time': round(scrape_time, 2),
                    'timestamp': datetime.now().isoformat(),
                    'method': 'requests'
                })
                
                logger.info(f"Monitor {monitor_id} completed: {jobs_found} jobs found, {new_jobs} new")
                
            except Exception as e:
                logger.error(f"Error in monitor {monitor_id}: {e}")
                
                # Record failed run
                self.db.record_monitor_run(
                    monitor_id=monitor_id,
                    jobs_found=0,
                    new_jobs=0,
                    success=False,
                    error_message=str(e)
                )
                
                # Emit error
                self.socketio.emit('monitor_error', {
                    'monitor_id': monitor_id,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            
            # Wait for next check (or until stopped)
            stop_event.wait(check_interval)
        
        logger.info(f"Monitor loop stopped for {monitor['name']} (ID: {monitor_id})")
    
    def _scrape_jobs(self, monitor):
        """Simple web scraping using requests"""
        url = monitor['url']
        keywords = monitor['keywords']
        
        # Use generic scraping
        jobs = self._generic_scrape(url, keywords)
        
        return {
            'jobs': jobs,
            'method': 'requests'
        }
    
    def _generic_scrape(self, url, keywords):
        """Generic web scraping with requests and BeautifulSoup"""
        jobs = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Add cache-busting parameter
            separator = '&' if '?' in url else '?'
            cache_bust = f"_cb={int(time.time())}{random.randint(1000, 9999)}"
            url_with_cache_bust = f"{url}{separator}{cache_bust}"
            
            response = requests.get(url_with_cache_bust, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different selectors to find job listings
            selectors = [
                '[data-job-id]',
                '.job-listing',
                '.job-item',
                '.job-result',
                '.position',
                '.opening',
                'li[class*="job"]',
                'div[class*="job"]',
                '[class*="position"]',
                '[class*="opening"]'
            ]
            
            for selector in selectors:
                try:
                    job_elements = soup.select(selector)
                    if job_elements:
                        logger.info(f"Found {len(job_elements)} elements with selector: {selector}")
                        for element in job_elements[:20]:  # Limit to first 20
                            job = self._extract_job_data(element, url, keywords)
                            if job and self._matches_keywords(job, keywords):
                                jobs.append(job)
                        if jobs:
                            break
                except Exception as e:
                    logger.warning(f"Error with selector '{selector}': {e}")
                    continue
            
            if not jobs:
                # Fallback: look for any text that might be job-related
                all_text = soup.get_text()
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                
                for line in lines:
                    if any(keyword.lower() in line.lower() for keyword in keywords):
                        if len(line) > 10 and len(line) < 200:  # Reasonable job title length
                            jobs.append({
                                'title': line,
                                'url': url,
                                'company': 'Unknown',
                                'location': 'Unknown',
                                'description': line
                            })
                            if len(jobs) >= 5:  # Limit fallback results
                                break
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        return jobs
    
    def _extract_job_data(self, element, base_url, keywords):
        """Extract job data from a single job element"""
        try:
            # Extract title
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.job-title', '[class*="title"]']
            title = None
            for sel in title_selectors:
                title_elem = element.select_one(sel)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:
                        break
            
            if not title:
                title = element.get_text(strip=True)[:100]  # Fallback
            
            # Extract URL
            url = None
            link_elem = element.find('a', href=True)
            if link_elem:
                url = urljoin(base_url, link_elem['href'])
            
            # Extract company
            company_selectors = ['.company', '.employer', '[class*="company"]', '[class*="employer"]']
            company = None
            for sel in company_selectors:
                company_elem = element.select_one(sel)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            # Extract location
            location_selectors = ['.location', '.city', '[class*="location"]', '[class*="city"]']
            location = None
            for sel in location_selectors:
                location_elem = element.select_one(sel)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    break
            
            # Extract description
            description = element.get_text(strip=True)[:500]  # Limit description length
            
            return {
                'title': title,
                'url': url,
                'company': company,
                'location': location,
                'description': description
            }
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {e}")
            return None
    
    def _matches_keywords(self, job, keywords):
        """Check if job matches any of the keywords"""
        if not keywords:
            return True
        
        # Combine all job text for searching
        text_to_search = ' '.join([
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            job.get('description', '')
        ]).lower()
        
        # Check if any keyword matches
        return any(keyword.lower() in text_to_search for keyword in keywords)
    
    def _create_content_hash(self, job):
        """Create a hash for job deduplication"""
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()

# Initialize job monitor
job_monitor = SimpleJobMonitor(db, socketio)

@app.route('/')
def index():
    return render_template_string(SIMPLE_HTML)

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
    
    print("🚀 Starting Simple Job Monitor")
    print("📡 Open your browser to: http://localhost:5000")
    print("🎯 Use the Google Careers preset to get started quickly!")
    print("⏱️  Jobs will be checked every 30 seconds by default")
    print("🔔 You'll get notifications for new jobs")
    print("\nPress Ctrl+C to stop")
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
