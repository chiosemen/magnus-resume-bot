# Vercel Deployment - Quick Command Reference

## 🚀 Deployment Commands

### Deploy to Production
```bash
vercel --prod
```

### Deploy Preview (Testing)
```bash
vercel
```

### Deploy with Auto-Accept
```bash
vercel --yes
```

---

## 📊 Management Commands

### List All Deployments
```bash
vercel ls
```

### Check Current User
```bash
vercel whoami
```

### List Projects
```bash
vercel project ls
```

---

## 📝 Logs & Monitoring

### View Real-time Logs
```bash
vercel logs https://magnus-resume-bot.vercel.app --follow
```

### View Recent Logs
```bash
vercel logs https://magnus-resume-bot.vercel.app
```

### Inspect Specific Deployment
```bash
vercel inspect [deployment-url]
```

---

## 🔧 Environment Variables

### List Environment Variables
```bash
vercel env ls
```

### Add Environment Variable
```bash
echo "value" | vercel env add VARIABLE_NAME production
```

### Remove Environment Variable
```bash
vercel env rm VARIABLE_NAME production
```

### Pull Environment Variables Locally
```bash
vercel env pull
```

---

## 🔄 Rollback & Redeploy

### Rollback to Previous Deployment
```bash
vercel promote [previous-deployment-url]
```

### Redeploy Specific Deployment
```bash
vercel redeploy [deployment-url]
```

---

## 🧪 Testing Deployed API

### Health Check
```bash
curl https://magnus-resume-bot.vercel.app/health
```

### Get Statistics
```bash
curl https://magnus-resume-bot.vercel.app/api/stats
```

### List Jobs (with parameters)
```bash
curl 'https://magnus-resume-bot.vercel.app/api/jobs?limit=10'
```

### View API Documentation
```bash
open https://magnus-resume-bot.vercel.app/docs
```

---

## 🏗️ Project Configuration

### Link Local Project
```bash
vercel link
```

### Remove Project Link
```bash
vercel unlink
```

---

## 🔐 Domain Management

### List Domains
```bash
vercel domains ls
```

### Add Domain
```bash
vercel domains add your-domain.com
```

### Remove Domain
```bash
vercel domains rm your-domain.com
```

---

## 📦 Build Configuration

### Current vercel.json
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

## ⚠️ About the "builds" Warning

**Warning Message:**
```
Due to `builds` existing in your configuration file, the Build and
Development Settings defined in your Project Settings will not apply.
```

**Explanation:**
- This is **expected behavior** and **not an error**
- Using `builds` in `vercel.json` gives you full control over the build process
- Dashboard build settings are intentionally ignored
- This is the correct approach for Python serverless functions

**Action Required:** ✅ None - this is working as intended

---

## 🔍 Troubleshooting Commands

### Check Deployment Status
```bash
vercel inspect [deployment-url]
```

### View Build Logs
```bash
vercel logs [deployment-url] --since 1h
```

### Test Locally
```bash
vercel dev
```

---

## 📚 Useful Resources

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Project Dashboard:** https://vercel.com/chiosemens-projects/magnus-resume-bot
- **Python on Vercel Docs:** https://vercel.com/docs/frameworks/python
- **CLI Reference:** https://vercel.com/docs/cli

---

## 🎯 Quick Deployment Workflow

```bash
# 1. Make changes to code
git add .
git commit -m "Your changes"

# 2. Deploy to preview (optional - for testing)
vercel

# 3. Test preview deployment
curl [preview-url]/health

# 4. Deploy to production
vercel --prod

# 5. Verify production
curl https://magnus-resume-bot.vercel.app/health
```

---

## 📊 Current Production Deployment

**URL:** https://magnus-resume-bot.vercel.app
**Status:** 🟢 Live
**Last Deployed:** October 19, 2025
**Runtime:** Python 3.9
**Region:** Global (Edge Network)

---

**For more details, see:**
- DEPLOYMENT_SUCCESS.md
- DEPLOYMENT.md
- README.md
