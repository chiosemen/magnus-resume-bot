# Magnus Resume Bot - Vercel Deployment Guide

## Deployment Summary

**Status:** Ready for Deployment ✅
**Platform:** Vercel
**Runtime:** Python 3.9
**Entry Point:** `api/main.py`

---

## Pre-Deployment Checklist

- ✅ `vercel.json` configured
- ✅ `requirements.txt` present
- ✅ `.vercelignore` created
- ✅ Vercel CLI installed (v48.2.9)
- ✅ Logged in as: `chiosemen`
- ✅ API tested locally

---

## Deployment Commands

### Option 1: Preview Deployment (Recommended First)
```bash
vercel
```
This creates a preview deployment for testing.

### Option 2: Production Deployment
```bash
vercel --prod
```
This deploys to production.

---

## Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.9"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "api/main.py"
    }
  ],
  "env": {
    "PYTHONPATH": "/var/task:/var/task/src",
    "DATABASE_PATH": "/tmp/jobs.db",
    "APP_NAME": "Magnus Resume Bot API",
    "APP_VERSION": "1.0.0"
  }
}
```

---

## Environment Variables (Set via Vercel Dashboard)

After deployment, configure these in Vercel Dashboard → Settings → Environment Variables:

**Required:**
- `PYTHONPATH=/var/task:/var/task/src`
- `DATABASE_PATH=/tmp/jobs.db`

**Optional:**
- `CORS_ORIGINS=https://your-domain.com`
- `DEBUG=false`
- `EMAIL_USER=your.email@gmail.com`
- `EMAIL_PASSWORD=your_app_password`

---

## Post-Deployment Steps

### 1. Verify Deployment
```bash
# Get deployment URL from Vercel output
DEPLOYMENT_URL="https://your-app.vercel.app"

# Test health endpoint
curl $DEPLOYMENT_URL/health

# Test stats endpoint
curl $DEPLOYMENT_URL/api/stats
```

### 2. Test API Endpoints

**Health Check:**
```bash
curl https://your-app.vercel.app/health
```

Expected Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T...",
  "version": "1.0.0"
}
```

**Statistics:**
```bash
curl https://your-app.vercel.app/api/stats
```

**Interactive Docs:**
Visit: `https://your-app.vercel.app/docs`

---

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Check that `PYTHONPATH` is set correctly in environment variables.

### Issue: "Database locked" errors
**Solution:** Vercel uses ephemeral storage at `/tmp/`. Database resets on each deployment. For persistence, use:
- Vercel Postgres
- Supabase
- PlanetScale
- External database

### Issue: Deployment size too large
**Solution:** Using `requirements-vercel.txt` with minimal dependencies:
```bash
# In vercel.json, ensure only essential packages
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
python-dotenv==1.0.0
requests==2.31.0
```

### Issue: Cold start timeout
**Solution:**
- Reduce dependencies
- Implement lazy loading
- Consider upgrading to Vercel Pro for faster cold starts

---

## Database Considerations

⚠️ **Important:** SQLite on Vercel is ephemeral (resets on deployment)

### Options for Persistent Storage:

1. **Vercel Postgres** (Recommended)
   ```bash
   vercel postgres create
   ```

2. **Supabase**
   - Free tier available
   - PostgreSQL compatible
   - Real-time features

3. **PlanetScale**
   - MySQL compatible
   - Free tier: 5GB storage
   - Great for serverless

4. **MongoDB Atlas**
   - Free tier: 512MB
   - Good for document storage

---

## Monitoring & Logs

### View Logs
```bash
vercel logs [deployment-url]
```

### Real-time Logs
```bash
vercel logs [deployment-url] --follow
```

### Vercel Dashboard
Visit: https://vercel.com/dashboard
- View deployments
- Monitor usage
- Check analytics
- Configure domains

---

## Custom Domain Setup

### Add Custom Domain
1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Configure DNS records as shown
4. Wait for SSL certificate provisioning (~5 minutes)

### Update CORS
After adding domain, update `CORS_ORIGINS` in environment variables:
```
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

---

## Scaling Considerations

### Vercel Free Tier Limits:
- 100 GB-Hours per month
- 12 serverless functions
- 100 deployments per day

### Optimization Tips:
1. **Reduce Dependencies:** Use `requirements-vercel.txt`
2. **Lazy Loading:** Import heavy modules only when needed
3. **Caching:** Implement response caching
4. **Connection Pooling:** Already implemented in database module
5. **Rate Limiting:** Already implemented in job scraper

---

## CI/CD with GitHub

### Auto-Deploy from GitHub:
1. Push code to GitHub
2. Connect repository in Vercel Dashboard
3. Configure deployment settings:
   - Production Branch: `main`
   - Build Command: (auto-detected)
   - Output Directory: (auto-detected)

### GitHub Integration Benefits:
- ✅ Auto-deploy on push
- ✅ Preview deployments for PRs
- ✅ Comments on PRs with deployment URLs
- ✅ Automatic rollbacks

---

## Security Best Practices

1. **Environment Variables:** Never commit `.env` to git
2. **CORS:** Configure specific origins, not `*`
3. **Rate Limiting:** Already implemented
4. **API Keys:** Store in Vercel environment variables
5. **HTTPS:** Automatically provided by Vercel

---

## Cost Estimation

### Vercel Pricing:
- **Hobby (Free):** $0/month
  - 100 GB-Hours
  - 100 deployments/day
  - Community support

- **Pro:** $20/month per user
  - 1000 GB-Hours
  - Unlimited deployments
  - Advanced analytics
  - Email support

### Expected Usage (Magnus Resume Bot):
- **Free tier sufficient** for:
  - Testing and development
  - Low-traffic applications (<1000 requests/day)
  - Personal projects

---

## Rollback Instructions

### Rollback to Previous Deployment:
```bash
# List deployments
vercel ls

# Promote specific deployment to production
vercel promote [deployment-url]
```

Or via Dashboard:
1. Go to Deployments tab
2. Find previous working deployment
3. Click "Promote to Production"

---

## Support & Resources

- **Vercel Documentation:** https://vercel.com/docs
- **Python on Vercel:** https://vercel.com/docs/frameworks/python
- **Project GitHub:** (your repository)
- **API Documentation:** `https://your-app.vercel.app/docs`

---

**Deployment Prepared By:** Magnus Resume Bot DevOps Assistant
**Date:** October 19, 2025
**Version:** 1.0.0
