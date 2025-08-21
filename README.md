# 🔍 Job Monitor

A robust, real-time job monitoring platform that tracks job postings across multiple websites and sends instant notifications when new opportunities matching your criteria are found.

## ✨ Features

- **🎯 Real-time Monitoring**: Continuously monitors job sites with configurable intervals (10-second minimum)
- **🔔 Instant Notifications**: Sound alerts and visual notifications for new job postings
- **🌐 Multi-website Support**: Works with any job site, with specialized parsers for major platforms
- **🔍 Smart Keyword Filtering**: Advanced keyword matching to find relevant opportunities
- **🛡️ Anti-detection Technology**: Robust scraping with rotating user agents, headers, and anti-bot measures
- **💾 Persistent Storage**: SQLite database stores all job postings and monitoring history
- **📊 Analytics Dashboard**: Real-time statistics and monitoring insights
- **🎨 Modern UI**: Clean, responsive React-based interface
- **⚡ WebSocket Integration**: Real-time updates without page refresh

## 🚀 Quick Start

### Automated Setup (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd jobmonitor
   ```

2. **Run the automated setup:**
   ```bash
   python start.py
   ```
   
   This will:
   - Check system requirements
   - Install all dependencies
   - Set up the database
   - Create configuration files
   - Start the application

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the application:**
   ```bash
   python app.py
   ```

## 🎯 Google Careers Pre-configured Setup

The platform comes with a pre-configured setup for monitoring Google's Software Engineering internships:

1. Click "Add Monitor" in the web interface
2. Click "Google Careers - Software Engineering Internships" quick setup
3. Customize keywords if needed (default: "intern, internship, software engineer, new grad")
4. Click "Create Monitor"

The monitor will immediately start checking every 10 seconds for new postings!

## 🛠️ Configuration

### Monitor Settings

- **Name**: Descriptive name for your monitor
- **URL**: Target job site URL to monitor
- **Keywords**: Comma-separated keywords (jobs matching ANY keyword will be detected)
- **Check Interval**: How often to check for updates (minimum 5 seconds)
- **CSS Selector**: Optional custom selector for job listings
- **Active Status**: Enable/disable monitoring

### Environment Variables

Create a `.env` file (automatically created by setup):

```env
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
```

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Chrome Browser**: Required for JavaScript-heavy sites
- **Memory**: 2GB RAM minimum (4GB recommended)
- **Storage**: 1GB free space for database and logs

## 🔧 Advanced Features

### Anti-Detection Measures

- **Rotating User Agents**: Random browser identification
- **Dynamic Headers**: Realistic browser headers
- **Cache Busting**: Prevents cached responses
- **Random Delays**: Human-like browsing patterns
- **Proxy Support**: Optional proxy rotation (configurable)

### Supported Websites

- ✅ **Google Careers** (specialized parser)
- ✅ **Any standard job site** (generic parser)
- 🔄 **LinkedIn Jobs** (parser in development)
- 🔄 **Indeed** (parser in development)
- 🔄 **Glassdoor** (parser in development)

### Custom Parsers

Add custom parsers for specific websites:

```python
# parsers/custom_parser.py
class CustomJobSiteParser:
    def __init__(self):
        self.name = "Custom Site"
    
    def parse(self, url, keywords, selector=''):
        # Custom parsing logic
        return jobs_list
```

## 📊 API Endpoints

### Monitors
- `GET /api/monitors` - List all monitors
- `POST /api/monitors` - Create new monitor
- `PUT /api/monitors/{id}` - Update monitor
- `DELETE /api/monitors/{id}` - Delete monitor
- `POST /api/monitors/{id}/toggle` - Start/stop monitor
- `POST /api/monitors/{id}/test` - Test monitor configuration

### Jobs
- `GET /api/jobs` - List detected jobs
- `GET /api/jobs?monitor_id={id}` - Jobs for specific monitor

### Statistics
- `GET /api/stats` - Monitoring statistics

## 🎵 Sound Notifications

The platform plays audio alerts when new jobs are found:
- **Browser-based**: Uses Web Audio API for cross-platform compatibility
- **Automatic**: No additional software required
- **Customizable**: Modify notification sounds in the frontend code

## 🔍 Troubleshooting

### Common Issues

**Chrome/Selenium Issues:**
```bash
# Update Chrome driver
pip install --upgrade undetected-chromedriver
```

**Permission Errors:**
```bash
# Install in user directory
pip install --user -r requirements.txt
```

**Port Already in Use:**
```bash
# Change port in app.py
socketio.run(app, debug=True, host='0.0.0.0', port=5001)
```

**No Jobs Found:**
1. Test your monitor configuration using the "Test" button
2. Check if the website structure has changed
3. Try different CSS selectors
4. Verify keywords are spelled correctly

### Debugging

Enable debug mode in `.env`:
```env
FLASK_ENV=development
DEBUG=True
```

Check logs for detailed error information:
```bash
tail -f logs/job_monitor.log
```

## 🚧 Development

### Project Structure
```
jobmonitor/
├── app.py                 # Main Flask application
├── job_monitor.py         # Core monitoring engine
├── database.py           # Database operations
├── scraper_utils.py      # Anti-detection utilities
├── parsers/              # Website-specific parsers
│   ├── __init__.py
│   └── google_careers_parser.py
├── templates/            # Frontend templates
│   └── index.html        # React-based UI
├── requirements.txt      # Python dependencies
├── start.py             # Setup and startup script
└── README.md            # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Add new parsers in the `parsers/` directory
4. Test thoroughly with different websites
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Undetected ChromeDriver**: For robust browser automation
- **BeautifulSoup**: For HTML parsing
- **Flask-SocketIO**: For real-time communication
- **React**: For the user interface
- **Tailwind CSS**: For styling

## 📞 Support

- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Open an issue with the "enhancement" label
- 📧 **General Questions**: Check existing issues or create a new one

---

**Happy Job Hunting! 🎯**
