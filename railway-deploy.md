# 🚀 Railway Deployment Guide

## Quick Deploy to Railway

### Option 1: One-Click Deploy (Recommended)

1. **Fork this repository** to your GitHub account

2. **Visit Railway:** https://railway.app

3. **Connect GitHub** and select this repository

4. **Deploy automatically** - Railway will detect the Dockerfile and deploy!

### Option 2: Railway CLI Deploy

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Initialize project:**
   ```bash
   railway init
   ```

4. **Deploy:**
   ```bash
   railway up
   ```

## 🔧 Configuration

Railway will automatically:
- ✅ Build using the Dockerfile
- ✅ Set the PORT environment variable
- ✅ Provide a public URL
- ✅ Enable automatic HTTPS

### Environment Variables (Optional)

In Railway dashboard, you can set:

```
SECRET_KEY=your-secure-random-key
DEFAULT_CHECK_INTERVAL=30
MAX_CONCURRENT_MONITORS=5
```

## 📱 Using Your Deployed App

Once deployed, Railway will give you a URL like:
```
https://your-app-name.railway.app
```

### Getting Started:

1. **Open the URL** in your browser
2. **Click "Google Careers Preset"** 
3. **Click "Create Monitor"**
4. **Watch for real-time job notifications!** 🎉

## 🎯 Features on Railway

- ✅ **Real-time monitoring** with WebSocket support
- ✅ **Sound notifications** for new jobs
- ✅ **Mobile-responsive** interface
- ✅ **Automatic deployments** from GitHub
- ✅ **HTTPS enabled** by default
- ✅ **24/7 uptime** monitoring

## 📊 Monitoring Performance

Your Railway app includes:

- **Health endpoint:** `/health`
- **Real-time stats** in the dashboard
- **Automatic restarts** if needed
- **Built-in logging** via Railway

## 🛠️ Troubleshooting

### Deployment Issues:

1. **Check Railway logs** in the dashboard
2. **Verify Dockerfile** is in the root directory
3. **Ensure requirements.txt** is up to date

### Runtime Issues:

1. **Monitor the Railway logs** for errors
2. **Check `/health` endpoint** for app status
3. **Test monitor creation** via the web interface

### Common Solutions:

**Memory issues:**
- Reduce `MAX_CONCURRENT_MONITORS` to 3-5
- Increase check intervals to 60+ seconds

**Rate limiting:**
- Increase check intervals
- Add delays between requests

## 🎮 Demo URLs to Try

Once deployed, test with these job sites:

1. **Google Careers** (preset available)
2. **Y Combinator Jobs:** https://www.ycombinator.com/jobs
3. **AngelList:** https://angel.co/jobs
4. **Hacker News Jobs:** https://news.ycombinator.com/jobs

## 📈 Scaling on Railway

Railway's free tier includes:
- ✅ 500 hours/month runtime
- ✅ Shared CPU/Memory
- ✅ Perfect for job monitoring

For heavy usage, upgrade to Railway Pro for:
- 🚀 Dedicated resources
- 🚀 Unlimited runtime
- 🚀 Priority support

## 🔒 Security Notes

- ✅ All connections use HTTPS
- ✅ No API keys stored in code
- ✅ Environment variables are encrypted
- ✅ Regular security updates via Docker

---

## 🎉 Success!

Your job monitor is now running 24/7 in the cloud!

**Next steps:**
1. Add multiple monitors for different companies
2. Customize keywords for your target roles
3. Share the URL with friends/colleagues
4. Set up email notifications (coming soon)

Happy job hunting! 🎯
