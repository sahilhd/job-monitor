#!/usr/bin/env python3
"""
Railway-optimized Job Monitor Application
This version is optimized for Railway deployment with simplified dependencies.
"""

import os
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

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'railway-job-monitor-secret-key')
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False, async_mode='threading')

# Railway-optimized HTML template
RAILWAY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Job Monitor - Railway Deployment</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .content { padding: 30px; }
        .status { 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 10px; 
            border-left: 5px solid #007bff;
            background: #f8f9fa;
        }
        .success { border-left-color: #28a745; background: #d4edda; color: #155724; }
        .error { border-left-color: #dc3545; background: #f8d7da; color: #721c24; }
        .warning { border-left-color: #ffc107; background: #fff3cd; color: #856404; }
        .form-group { margin-bottom: 20px; }
        label { 
            display: block; 
            font-weight: 600; 
            margin-bottom: 8px; 
            color: #333;
        }
        input[type="text"], input[type="url"], input[type="number"], select {
            width: 100%; 
            padding: 12px; 
            border: 2px solid #e9ecef; 
            border-radius: 8px; 
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
            margin: 5px;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-secondary { background: #6c757d; }
        .btn-danger { background: #dc3545; }
        .btn-success { background: #28a745; }
        .monitor-card {
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 5px solid #667eea;
            transition: transform 0.2s;
        }
        .monitor-card:hover { transform: translateY(-2px); }
        .monitor-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 15px;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        .status-active { background: #28a745; }
        .status-inactive { background: #6c757d; animation: none; }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .job-item {
            background: #e8f5e8;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        .job-title { font-weight: 600; color: #155724; margin-bottom: 5px; }
        .job-details { font-size: 14px; color: #666; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: white;
        }
        .stat-number { font-size: 2em; font-weight: bold; }
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            border-left: 5px solid #28a745;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
        }
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border-radius: 10px;
            transition: background 0.3s;
        }
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        @media (max-width: 768px) {
            .content { padding: 20px; }
            .stats-grid { grid-template-columns: 1fr; }
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Job Monitor</h1>
            <p>Real-time job tracking platform deployed on Railway</p>
            <div style="margin-top: 15px;">
                <span id="status" class="status">Connecting...</span>
            </div>
        </div>
        
        <div class="content">
            <div class="tabs">
                <div class="tab active" onclick="showTab('dashboard')">📊 Dashboard</div>
                <div class="tab" onclick="showTab('monitors')">👁️ Monitors</div>
                <div class="tab" onclick="showTab('jobs')">💼 Jobs</div>
                <div class="tab" onclick="showTab('add')">➕ Add Monitor</div>
            </div>

            <!-- Dashboard Tab -->
            <div id="dashboard" class="tab-content active">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="stat-active">0</div>
                        <div>Active Monitors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="stat-total">0</div>
                        <div>Total Jobs</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="stat-today">0</div>
                        <div>Jobs Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="stat-monitors">0</div>
                        <div>Total Monitors</div>
                    </div>
                </div>
                
                <div class="status success">
                    <strong>🚀 Railway Deployment Active!</strong><br>
                    Your job monitor is running in the cloud and will continuously check for new opportunities.
                </div>
            </div>

            <!-- Monitors Tab -->
            <div id="monitors" class="tab-content">
                <div id="monitors-list"></div>
            </div>

            <!-- Jobs Tab -->
            <div id="jobs" class="tab-content">
                <div id="jobs-list"></div>
            </div>

            <!-- Add Monitor Tab -->
            <div id="add" class="tab-content">
                <h3>Add New Monitor</h3>
                
                <div style="margin-bottom: 20px;">
                    <button type="button" class="btn" onclick="loadGooglePreset()">
                        🎯 Google Careers Preset
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="clearForm()">
                        🗑️ Clear Form
                    </button>
                </div>
                
                <form id="monitorForm">
                    <div class="form-group">
                        <label>Monitor Name</label>
                        <input type="text" id="name" required placeholder="e.g., Google Software Engineering Internships">
                    </div>
                    
                    <div class="form-group">
                        <label>URL to Monitor</label>
                        <input type="url" id="url" required placeholder="https://...">
                    </div>
                    
                    <div class="form-group">
                        <label>Keywords (comma-separated)</label>
                        <input type="text" id="keywords" required placeholder="intern, software engineer, new grad">
                        <small style="color: #666;">Jobs matching ANY of these keywords will be detected</small>
                    </div>
                    
                    <div class="form-group">
                        <label>Check Interval (seconds)</label>
                        <select id="interval">
                            <option value="10">10 seconds (fastest)</option>
                            <option value="30" selected>30 seconds (recommended)</option>
                            <option value="60">1 minute</option>
                            <option value="300">5 minutes</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">🚀 Create Monitor</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let currentTab = 'dashboard';
        
        socket.on('connect', function() {
            document.getElementById('status').innerHTML = '✅ Connected to Railway';
            document.getElementById('status').className = 'status success';
            loadData();
        });
        
        socket.on('disconnect', function() {
            document.getElementById('status').innerHTML = '❌ Disconnected';
            document.getElementById('status').className = 'status error';
        });
        
        socket.on('new_job', function(data) {
            showNotification('🎉 New Job Found!', data.job.title + ' at ' + (data.job.company || 'Unknown Company'));
            playNotificationSound();
            loadData();
        });
        
        socket.on('monitor_update', function(data) {
            if (data.new_jobs > 0) {
                showNotification('📊 Monitor Update', `${data.new_jobs} new jobs found`);
            }
            loadData();
        });
        
        socket.on('monitor_error', function(data) {
            showNotification('❌ Monitor Error', data.error);
        });
        
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            currentTab = tabName;
            
            if (tabName !== 'add') loadData();
        }
        
        function loadData() {
            Promise.all([
                fetch('/api/monitors').then(r => r.json()),
                fetch('/api/jobs').then(r => r.json()),
                fetch('/api/stats').then(r => r.json())
            ]).then(([monitors, jobs, stats]) => {
                updateStats(stats.data);
                updateMonitors(monitors.data);
                updateJobs(jobs.data);
            });
        }
        
        function updateStats(stats) {
            document.getElementById('stat-active').textContent = stats.active_monitors || 0;
            document.getElementById('stat-total').textContent = stats.total_jobs || 0;
            document.getElementById('stat-today').textContent = stats.jobs_today || 0;
            document.getElementById('stat-monitors').textContent = stats.total_monitors || 0;
        }
        
        function updateMonitors(monitors) {
            const container = document.getElementById('monitors-list');
            container.innerHTML = '';
            
            if (monitors.length === 0) {
                container.innerHTML = '<div class="status">No monitors yet. Create your first monitor!</div>';
                return;
            }
            
            monitors.forEach(monitor => {
                const div = document.createElement('div');
                div.className = 'monitor-card';
                div.innerHTML = `
                    <div class="monitor-header">
                        <div style="display: flex; align-items: center;">
                            <div class="status-indicator ${monitor.is_active ? 'status-active' : 'status-inactive'}"></div>
                            <strong>${monitor.name}</strong>
                        </div>
                        <div>
                            <button class="btn btn-secondary" onclick="testMonitor(${monitor.id})">🧪 Test</button>
                            <button class="btn ${monitor.is_active ? 'btn-danger' : 'btn-success'}" onclick="toggleMonitor(${monitor.id})">
                                ${monitor.is_active ? '⏹️ Stop' : '▶️ Start'}
                            </button>
                            <button class="btn btn-danger" onclick="deleteMonitor(${monitor.id})">🗑️ Delete</button>
                        </div>
                    </div>
                    <div><strong>URL:</strong> ${monitor.url}</div>
                    <div><strong>Keywords:</strong> ${monitor.keywords.join(', ')}</div>
                    <div><strong>Interval:</strong> ${monitor.check_interval} seconds</div>
                `;
                container.appendChild(div);
            });
        }
        
        function updateJobs(jobs) {
            const container = document.getElementById('jobs-list');
            container.innerHTML = '';
            
            if (jobs.length === 0) {
                container.innerHTML = '<div class="status">No jobs found yet. Start monitoring to see results!</div>';
                return;
            }
            
            jobs.slice(0, 20).forEach(job => {
                const div = document.createElement('div');
                div.className = 'job-item';
                div.innerHTML = `
                    <div class="job-title">${job.title}</div>
                    <div class="job-details">
                        ${job.company ? `🏢 ${job.company}` : ''} 
                        ${job.location ? `📍 ${job.location}` : ''}
                        📅 ${new Date(job.detected_at).toLocaleString()}
                        ${job.url ? `<br><a href="${job.url}" target="_blank">🔗 View Job</a>` : ''}
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function loadGooglePreset() {
            document.getElementById('name').value = 'Google Careers - Software Engineering Internships';
            document.getElementById('url').value = 'https://www.google.com/about/careers/applications/jobs/results/?jlo=en_US&q=Software+Engineer&target_level=INTERN_AND_APPRENTICE';
            document.getElementById('keywords').value = 'intern, internship, software engineer, new grad';
        }
        
        function clearForm() {
            document.getElementById('monitorForm').reset();
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
                    showNotification('✅ Success', 'Monitor created successfully');
                    clearForm();
                    showTab('monitors');
                    loadData();
                } else {
                    showNotification('❌ Error', result.error);
                }
            });
        };
        
        function toggleMonitor(id) {
            fetch(`/api/monitors/${id}/toggle`, {method: 'POST'})
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showNotification('✅ Success', 'Monitor toggled');
                    loadData();
                }
            });
        }
        
        function testMonitor(id) {
            showNotification('🧪 Testing', 'Running test scrape...');
            fetch(`/api/monitors/${id}/test`, {method: 'POST'})
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showNotification('✅ Test Complete', `Found ${result.data.jobs_found} jobs`);
                } else {
                    showNotification('❌ Test Failed', result.error);
                }
            });
        }
        
        function deleteMonitor(id) {
            if (confirm('Delete this monitor?')) {
                fetch(`/api/monitors/${id}`, {method: 'DELETE'})
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        showNotification('✅ Success', 'Monitor deleted');
                        loadData();
                    }
                });
            }
        }
        
        function showNotification(title, message) {
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.innerHTML = `<strong>${title}</strong><br>${message}`;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 5000);
        }
        
        function playNotificationSound() {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            } catch (error) {
                console.log('Audio notification failed:', error);
            }
        }
        
        // Load initial data
        loadData();
    </script>
</body>
</html>
"""

# Initialize database
db = Database()

class RailwayJobMonitor:
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
            return
        
        # Signal stop and wait for thread to finish
        self.active_monitors[monitor_id]['stop_event'].set()
        self.active_monitors[monitor_id]['thread'].join(timeout=5)
        
        # Remove from active monitors
        del self.active_monitors[monitor_id]
        logger.info(f"Stopped monitor {monitor_id}")
    
    def test_monitor(self, monitor_id: int):
        """Test a monitor configuration"""
        monitor = self.db.get_monitor(monitor_id)
        if not monitor:
            raise Exception(f"Monitor {monitor_id} not found")
        
        try:
            results = self._scrape_jobs(monitor)
            return {
                'success': True,
                'jobs_found': len(results['jobs']),
                'jobs': results['jobs'][:5]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _monitor_loop(self, monitor, stop_event):
        """Main monitoring loop"""
        monitor_id = monitor['id']
        check_interval = max(monitor['check_interval'], 30)  # Minimum 30 seconds for Railway
        
        logger.info(f"Starting monitor loop for {monitor['name']} (ID: {monitor_id})")
        
        while not stop_event.is_set():
            try:
                start_time = time.time()
                results = self._scrape_jobs(monitor)
                scrape_time = time.time() - start_time
                
                jobs_found = len(results['jobs'])
                new_jobs = 0
                
                for job in results['jobs']:
                    content_hash = self._create_content_hash(job)
                    
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
                            self.socketio.emit('new_job', {
                                'monitor_id': monitor_id,
                                'monitor_name': monitor['name'],
                                'job': job,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            logger.info(f"New job found: {job.get('title', 'Unknown')}")
                
                self.db.record_monitor_run(
                    monitor_id=monitor_id,
                    jobs_found=jobs_found,
                    new_jobs=new_jobs,
                    success=True
                )
                
                self.socketio.emit('monitor_update', {
                    'monitor_id': monitor_id,
                    'jobs_found': jobs_found,
                    'new_jobs': new_jobs,
                    'scrape_time': round(scrape_time, 2),
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"Monitor {monitor_id}: {jobs_found} jobs, {new_jobs} new")
                
            except Exception as e:
                logger.error(f"Error in monitor {monitor_id}: {e}")
                
                self.db.record_monitor_run(
                    monitor_id=monitor_id,
                    jobs_found=0,
                    new_jobs=0,
                    success=False,
                    error_message=str(e)
                )
            
            stop_event.wait(check_interval)
    
    def _scrape_jobs(self, monitor):
        """Railway-optimized web scraping"""
        url = monitor['url']
        keywords = monitor['keywords']
        jobs = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            # Cache busting
            separator = '&' if '?' in url else '?'
            cache_bust = f"_railway_cb={int(time.time())}{random.randint(1000, 9999)}"
            url_with_cache_bust = f"{url}{separator}{cache_bust}"
            
            response = requests.get(url_with_cache_bust, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Enhanced job detection
            selectors = [
                '[data-job-id]', '.job-listing', '.job-item', '.job-result',
                '.position', '.opening', 'li[class*="job"]', 'div[class*="job"]',
                '[class*="position"]', '[class*="opening"]', '[role="listitem"]'
            ]
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with '{selector}'")
                        for element in elements[:15]:
                            job = self._extract_job_data(element, url)
                            if job and self._matches_keywords(job, keywords):
                                jobs.append(job)
                        if jobs:
                            break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
            
            # Fallback text search
            if not jobs:
                text_content = soup.get_text()
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                for line in lines:
                    if any(kw.lower() in line.lower() for kw in keywords):
                        if 20 <= len(line) <= 150:
                            jobs.append({
                                'title': line,
                                'url': url,
                                'company': 'Unknown',
                                'location': 'Unknown',
                                'description': line
                            })
                            if len(jobs) >= 3:
                                break
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
        
        return {'jobs': jobs}
    
    def _extract_job_data(self, element, base_url):
        """Extract job information from HTML element"""
        try:
            # Title extraction
            title_selectors = ['h1', 'h2', 'h3', '.title', '.job-title', '[class*="title"]']
            title = None
            for sel in title_selectors:
                elem = element.select_one(sel)
                if elem and elem.get_text(strip=True):
                    title = elem.get_text(strip=True)
                    break
            
            if not title:
                title = element.get_text(strip=True)[:100]
            
            # URL extraction
            url = None
            link = element.find('a', href=True)
            if link:
                url = urljoin(base_url, link['href'])
            
            # Company extraction
            company_selectors = ['.company', '.employer', '[class*="company"]']
            company = None
            for sel in company_selectors:
                elem = element.select_one(sel)
                if elem:
                    company = elem.get_text(strip=True)
                    break
            
            # Location extraction
            location_selectors = ['.location', '.city', '[class*="location"]']
            location = None
            for sel in location_selectors:
                elem = element.select_one(sel)
                if elem:
                    location = elem.get_text(strip=True)
                    break
            
            return {
                'title': title,
                'url': url,
                'company': company,
                'location': location,
                'description': element.get_text(strip=True)[:300]
            }
            
        except Exception as e:
            logger.debug(f"Job extraction error: {e}")
            return None
    
    def _matches_keywords(self, job, keywords):
        """Check keyword matching"""
        if not keywords:
            return True
        
        search_text = ' '.join([
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            job.get('description', '')
        ]).lower()
        
        return any(kw.lower() in search_text for kw in keywords)
    
    def _create_content_hash(self, job):
        """Create hash for deduplication"""
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()

# Initialize job monitor
job_monitor = RailwayJobMonitor(db, socketio)

# Routes
@app.route('/')
def index():
    return render_template_string(RAILWAY_HTML)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/monitors', methods=['GET'])
def get_monitors():
    try:
        monitors = db.get_all_monitors()
        return jsonify({'success': True, 'data': monitors})
    except Exception as e:
        logger.error(f"Error getting monitors: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors', methods=['POST'])
def create_monitor():
    try:
        data = request.json
        required_fields = ['name', 'url', 'keywords', 'check_interval']
        
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Ensure minimum interval for Railway
        check_interval = max(data['check_interval'], 30)
        
        monitor_id = db.create_monitor(
            name=data['name'],
            url=data['url'],
            keywords=data['keywords'],
            check_interval=check_interval,
            selector=data.get('selector', ''),
            is_active=data.get('is_active', True)
        )
        
        if data.get('is_active', True):
            job_monitor.start_monitor(monitor_id)
        
        return jsonify({'success': True, 'monitor_id': monitor_id})
    except Exception as e:
        logger.error(f"Error creating monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors/<int:monitor_id>/toggle', methods=['POST'])
def toggle_monitor(monitor_id):
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
    try:
        result = job_monitor.test_monitor(monitor_id)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"Error testing monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitors/<int:monitor_id>', methods=['DELETE'])
def delete_monitor(monitor_id):
    try:
        job_monitor.stop_monitor(monitor_id)
        db.delete_monitor(monitor_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        monitor_id = request.args.get('monitor_id')
        jobs = db.get_jobs(monitor_id)
        return jsonify({'success': True, 'data': jobs})
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = db.get_stats()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected to Railway deployment')
    emit('status', {'message': 'Connected to Railway Job Monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

if __name__ == '__main__':
    # Initialize database
    db.init_tables()
    
    # Get port from environment (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    logger.info("🚀 Starting Railway Job Monitor")
    logger.info(f"📡 Server will be available on port {port}")
    
    # Start active monitors
    try:
        active_monitors = db.get_active_monitors()
        for monitor in active_monitors:
            job_monitor.start_monitor(monitor['id'])
        logger.info(f"Started {len(active_monitors)} active monitors")
    except Exception as e:
        logger.error(f"Error starting monitors: {e}")
    
    # Run on Railway with production-safe settings
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
