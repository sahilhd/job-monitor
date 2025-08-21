# 🚀 Quick Start Guide

## Instant Setup (3 steps)

### Step 1: Start the Application
```bash
python3 simple_app.py
```

### Step 2: Open Your Browser
Go to: **http://localhost:5000**

### Step 3: Add Google Careers Monitor
1. Click **"Load Google Careers Preset"** 
2. Click **"Add Monitor"**
3. Watch for job notifications! 🎉

## What You'll See

- ✅ **Real-time connection status**
- 📊 **Monitor management interface**
- 🔔 **Instant notifications for new jobs**
- 📱 **Sound alerts when jobs are found**
- 📋 **List of detected jobs**

## Example: Google Internships

The preset monitors this URL:
```
https://www.google.com/about/careers/applications/jobs/results/?jlo=en_US&q=Software+Engineer&target_level=INTERN_AND_APPRENTICE
```

Keywords: `intern, internship, software engineer, new grad`

## Default Settings

- **Check Interval**: 30 seconds (can be changed to 10+ seconds)
- **Keywords**: Match ANY keyword (not all)
- **Deduplication**: Prevents duplicate job alerts
- **Cache Busting**: Always gets fresh results

## Advanced Setup

For the full-featured version with Selenium support:

1. **Install all dependencies:**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

2. **Run the full app:**
   ```bash
   python3 app.py
   ```

3. **Access the advanced UI:**
   ```
   http://localhost:5000
   ```

## Troubleshooting

**Port already in use?**
- Kill the process: `lsof -ti:5000 | xargs kill -9`
- Or change the port in `simple_app.py`

**No notifications?**
- Check browser console for errors
- Ensure keywords match job content
- Try the "Test" button to debug

**Need help?**
- Check the full README.md
- Look at the browser's developer console
- Check terminal output for error messages

---
**Happy job hunting! 🎯**
