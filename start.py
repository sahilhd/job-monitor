#!/usr/bin/env python3
"""
Job Monitor Startup Script
This script installs dependencies and starts the job monitoring platform.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{'='*50}")
    print(f"📋 {description}")
    print(f"{'='*50}")
    
    try:
        if isinstance(command, list):
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_chrome():
    """Check if Chrome is installed"""
    chrome_paths = {
        'Darwin': [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium'
        ],
        'Linux': [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium'
        ],
        'Windows': [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
        ]
    }
    
    system = platform.system()
    paths = chrome_paths.get(system, [])
    
    for path in paths:
        if os.path.exists(path):
            print(f"✅ Found Chrome at: {path}")
            return True
    
    print("⚠️  Chrome not found at standard locations")
    print("Please install Google Chrome for full functionality")
    return False

def install_dependencies():
    """Install Python dependencies"""
    return run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "Installing Python dependencies")

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'data']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Created necessary directories")
    return True

def setup_environment():
    """Setup environment variables"""
    env_file = Path('.env')
    if not env_file.exists():
        env_content = """# Job Monitor Environment Variables
# Database
DATABASE_URL=sqlite:///job_monitor.db

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production

# Monitoring Configuration
DEFAULT_CHECK_INTERVAL=10
MAX_CONCURRENT_MONITORS=10

# Scraping Configuration
REQUEST_TIMEOUT=30
MAX_RETRIES=3
SELENIUM_TIMEOUT=20

# Optional: Proxy Configuration (if needed)
# USE_PROXY=false
# PROXY_HOST=
# PROXY_PORT=
# PROXY_USERNAME=
# PROXY_PASSWORD=

# Optional: Notification Configuration
# ENABLE_EMAIL_NOTIFICATIONS=false
# EMAIL_SMTP_SERVER=
# EMAIL_PORT=587
# EMAIL_USERNAME=
# EMAIL_PASSWORD=
# EMAIL_RECIPIENTS=
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
    else:
        print("✅ .env file already exists")
    return True

def start_application():
    """Start the job monitor application"""
    print(f"\n{'='*50}")
    print("🚀 Starting Job Monitor Application")
    print(f"{'='*50}")
    print("📡 The application will be available at: http://localhost:5000")
    print("🎯 Press Ctrl+C to stop the application")
    print(f"{'='*50}\n")
    
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed to start: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🔍 Job Monitor - Setup and Startup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check Chrome installation
    check_chrome()
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        print("Please check your internet connection and try again")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print("✅ Setup completed successfully!")
    print(f"{'='*50}")
    
    # Ask user if they want to start the application
    start_now = input("\nWould you like to start the application now? (y/n): ").lower().strip()
    
    if start_now in ['y', 'yes', '']:
        start_application()
    else:
        print("\n📋 To start the application later, run:")
        print("   python app.py")
        print("\n🌐 Then open your browser to: http://localhost:5000")

if __name__ == "__main__":
    main()
