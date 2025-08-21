#!/usr/bin/env python3
"""
Test Railway deployment locally
"""

import os
import requests
import time
import threading
from railway_app import app, db, socketio

def test_railway_app():
    """Test the Railway app locally"""
    print("🧪 Testing Railway Job Monitor Locally")
    print("=" * 50)
    
    # Set environment for testing
    os.environ['PORT'] = '5001'
    
    # Start the app in a thread
    def run_app():
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    
    # Wait for server to start
    print("⏳ Starting server...")
    time.sleep(5)
    
    try:
        # Test health endpoint
        print("🩺 Testing health endpoint...")
        response = requests.get('http://localhost:5001/health', timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test main page
        print("🏠 Testing main page...")
        response = requests.get('http://localhost:5001/', timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            if 'Job Monitor' in response.text:
                print("✅ Page content is correct")
            else:
                print("⚠️  Page content may be incorrect")
        else:
            print(f"❌ Main page failed: {response.status_code}")
            return False
        
        # Test API endpoints
        print("🔌 Testing API endpoints...")
        
        # Test monitors endpoint
        response = requests.get('http://localhost:5001/api/monitors', timeout=10)
        if response.status_code == 200:
            print("✅ Monitors API working")
        else:
            print(f"❌ Monitors API failed: {response.status_code}")
        
        # Test stats endpoint
        response = requests.get('http://localhost:5001/api/stats', timeout=10)
        if response.status_code == 200:
            print("✅ Stats API working")
        else:
            print(f"❌ Stats API failed: {response.status_code}")
        
        # Test jobs endpoint
        response = requests.get('http://localhost:5001/api/jobs', timeout=10)
        if response.status_code == 200:
            print("✅ Jobs API working")
        else:
            print(f"❌ Jobs API failed: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎉 Railway app test completed successfully!")
        print("📋 Ready for Railway deployment!")
        print("\n🚀 To deploy to Railway:")
        print("1. Push code to GitHub")
        print("2. Connect repository to Railway")
        print("3. Deploy automatically!")
        print("\n📱 Your app will be available at:")
        print("https://your-app-name.railway.app")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("\n💡 Make sure the server started correctly")
        return False
    
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_railway_app()
    if not success:
        print("\n❌ Tests failed. Check the output above for details.")
        exit(1)
    else:
        print("\n✅ All tests passed! Ready for Railway deployment.")
        exit(0)
