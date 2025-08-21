#!/bin/bash

# Railway startup script for Job Monitor
echo "🚀 Starting Job Monitor on Railway"
echo "📡 Port: $PORT"

# Initialize database and start monitors in background
python3 -c "
from railway_app import db, job_monitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db.init_tables()
logger.info('Database initialized')

# Start active monitors
try:
    active_monitors = db.get_active_monitors()
    for monitor in active_monitors:
        job_monitor.start_monitor(monitor['id'])
    logger.info(f'Started {len(active_monitors)} active monitors')
except Exception as e:
    logger.error(f'Error starting monitors: {e}')
" &

# Start Gunicorn with SocketIO support
exec gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT railway_app:app
