# Magnus Resume Bot - Streamlit Cloud Deployment Guide

**Dashboard File:** `streamlit_app.py`
**Backend API:** https://magnus-resume-bot.vercel.app
**Target Platform:** Streamlit Community Cloud

---

## 📋 Pre-Deployment Checklist

✅ **Files Configured:**
- [x] `streamlit_app.py` - Main dashboard application
- [x] `.streamlit/config.toml` - Theme and server configuration
- [x] `.streamlit/secrets.toml` - API URL configuration (local)
- [x] `requirements-streamlit.txt` - Streamlit-specific dependencies
- [x] `requirements-full.txt` - Full dependencies (all features)

✅ **Backend API:**
- [x] Vercel deployment live at https://magnus-resume-bot.vercel.app
- [x] Health endpoint responding
- [x] All API endpoints functional

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Repository

**1.1 Ensure code is committed to Git:**
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

**1.2 Choose requirements file:**
For Streamlit Cloud, you have two options:

**Option A: Full Features (Recommended)**
```bash
# Use requirements-full.txt (includes job scraping, NLP, etc.)
cp requirements-full.txt requirements.txt
```

**Option B: Minimal (Faster deployment)**
```bash
# Use requirements-streamlit.txt (essential dashboard only)
cp requirements-streamlit.txt requirements.txt
```

---

### Step 2: Access Streamlit Community Cloud

**2.1 Go to Streamlit Cloud:**
- Visit: https://share.streamlit.io/
- Click **"Sign up"** or **"Sign in"**

**2.2 Connect GitHub Account:**
- Click **"Continue with GitHub"**
- Authorize Streamlit to access your repositories
- Grant access to the repository containing magnus-resume-bot

---

### Step 3: Create New App

**3.1 Click "New app" button**

**3.2 Fill in deployment settings:**

| Field | Value |
|-------|-------|
| **Repository** | `your-username/magnus-resume-bot` |
| **Branch** | `main` (or your default branch) |
| **Main file path** | `streamlit_app.py` |
| **App URL (optional)** | `magnus-resume-bot` or custom name |

---

### Step 4: Configure Secrets

**4.1 Click "Advanced settings" → "Secrets"**

**4.2 Add the following secrets:**

```toml
# Required: Backend API URL
API_BASE_URL = "https://magnus-resume-bot.vercel.app"

# Optional: Environment identifier
ENVIRONMENT = "production"

# Optional: Debug mode
DEBUG = "false"
```

**Important Notes:**
- Secrets are environment variables accessible via `st.secrets`
- Never commit `.streamlit/secrets.toml` to GitHub
- Secrets are encrypted and secure in Streamlit Cloud

---

### Step 5: Deploy

**5.1 Click "Deploy!" button**

The deployment process will:
1. Clone your repository
2. Install dependencies from `requirements.txt`
3. Run `streamlit run streamlit_app.py`
4. Build the dashboard

**Expected deployment time:** 2-5 minutes

---

### Step 6: Monitor Deployment

**6.1 Watch the deployment logs**

You'll see:
```
Installing dependencies...
✅ streamlit==1.29.0
✅ plotly==5.18.0
✅ pandas==2.0.3
✅ requests==2.31.0

Starting Streamlit app...
✅ App is live!
```

**6.2 Common deployment issues:**

| Issue | Solution |
|-------|----------|
| Module not found | Check `requirements.txt` |
| Secret not found | Verify secrets configuration |
| API connection failed | Check `API_BASE_URL` |
| Build timeout | Use minimal requirements |

---

## ✅ Post-Deployment Verification

### Step 7: Verify Dashboard

**7.1 Access your dashboard:**
```
https://magnus-resume-bot.streamlit.app
```
or
```
https://your-username-magnus-resume-bot.streamlit.app
```

**7.2 Check Health Indicator:**
- Top right corner should show: **✓ API Connected**
- If shows **✗ API Offline**, check secrets configuration

**7.3 Test Core Features:**

| Feature | Test | Expected Result |
|---------|------|-----------------|
| **Dashboard** | Click "Dashboard" in sidebar | Statistics display |
| **Job Search** | Enter search term and click "Search Jobs" | Results appear in tabs |
| **Resume Upload** | Click "Resume Upload" | Upload form displays |
| **Applications** | Click "Applications" | Application list loads |

---

## 🔧 Configuration Details

### Environment Variables (Secrets)

**Required:**
```toml
API_BASE_URL = "https://magnus-resume-bot.vercel.app"
```

**Optional:**
```toml
# Environment identifier
ENVIRONMENT = "production"

# Debug mode
DEBUG = "false"

# Custom settings
DEFAULT_LOCATION = "United States"
DEFAULT_SEARCH_TERM = "Python Developer"
```

---

### Streamlit Configuration

**File:** `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

---

## 🎨 Custom Domain Setup

### Option 1: Streamlit Subdomain (Free)
Default URL: `https://your-app-name.streamlit.app`

### Option 2: Custom Domain (Paid Plan)
1. Upgrade to Streamlit Teams or Enterprise
2. Add custom domain in settings
3. Configure DNS records
4. Enable SSL certificate

---

## 🔄 Continuous Deployment

Streamlit Cloud auto-deploys on push to main branch:

```bash
# Make changes
git add .
git commit -m "Update dashboard"
git push origin main

# Streamlit Cloud will automatically:
# 1. Detect the push
# 2. Rebuild the app
# 3. Deploy new version
```

**Deployment triggers:**
- Push to main branch
- Manual redeploy from dashboard
- Dependency changes in requirements.txt

---

## 📊 Resource Limits

### Streamlit Community Cloud (Free Tier)

| Resource | Limit |
|----------|-------|
| **RAM** | 1 GB |
| **CPU** | 1 core |
| **Apps** | 1 public + 2 private |
| **Uptime** | Sleep after 7 days inactivity |
| **Concurrent users** | Unlimited |
| **Build time** | 10 minutes max |

### Optimization Tips

**1. Reduce Dependencies:**
Use `requirements-streamlit.txt` instead of full requirements

**2. Enable Caching:**
```python
@st.cache_data(ttl=3600)
def fetch_data():
    return requests.get(API_URL)
```

**3. Lazy Loading:**
Import heavy libraries only when needed

**4. Session State:**
Use `st.session_state` to persist data

---

## 🐛 Troubleshooting

### Issue: "App is not responding"
**Solution:**
1. Check deployment logs
2. Verify API_BASE_URL in secrets
3. Test API endpoint manually
4. Restart app from dashboard

### Issue: "Module not found"
**Solution:**
1. Add missing module to `requirements.txt`
2. Push changes to trigger rebuild
3. Check module name and version

### Issue: "Connection refused"
**Solution:**
1. Verify backend API is running
2. Check CORS settings on API
3. Ensure HTTPS (not HTTP) for API URL

### Issue: "Secrets not found"
**Solution:**
1. Go to App Settings → Secrets
2. Verify secrets are correctly formatted
3. Secrets use TOML format, not JSON
4. Restart app after updating secrets

---

## 🔐 Security Best Practices

**1. Never commit secrets:**
```bash
# Add to .gitignore
.streamlit/secrets.toml
*.env
.env.local
```

**2. Use environment-specific configs:**
```python
import streamlit as st

# Production
if st.secrets.get("ENVIRONMENT") == "production":
    API_URL = st.secrets["API_BASE_URL"]
# Local development
else:
    API_URL = "http://localhost:8000"
```

**3. Validate API responses:**
```python
try:
    response = requests.get(API_URL)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    st.error(f"API Error: {e}")
```

---

## 📈 Monitoring & Analytics

### Built-in Metrics

**Access via Streamlit Dashboard:**
1. Go to https://share.streamlit.io/
2. Select your app
3. View metrics:
   - Total views
   - Active users
   - Response times
   - Error rates

### Custom Analytics

Add Google Analytics:
```python
# In streamlit_app.py
import streamlit.components.v1 as components

# Inject GA tracking code
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=YOUR-GA-ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'YOUR-GA-ID');
</script>
""", height=0)
```

---

## 🚀 Advanced Features

### 1. Multi-Page Apps

Already configured with sidebar navigation:
- Dashboard
- Job Search
- Resume Upload
- Applications

### 2. State Persistence

Using `st.session_state`:
```python
if "search_results" not in st.session_state:
    st.session_state.search_results = None
```

### 3. Caching

Optimize API calls:
```python
@st.cache_data(ttl=3600)
def get_jobs(limit=50):
    return requests.get(f"{API_URL}/api/jobs?limit={limit}")
```

### 4. File Uploads

Resume upload feature:
```python
uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
if uploaded_file:
    files = {"file": uploaded_file}
    response = requests.post(f"{API_URL}/api/resumes/upload", files=files)
```

---

## 🔄 Rollback Procedure

**If deployment fails:**

1. **Revert to previous version:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Or deploy specific commit:**
   - Go to Streamlit Dashboard
   - Click "Settings" → "Advanced"
   - Change branch or commit hash
   - Click "Save"

3. **Emergency rollback:**
   - Click "⋮" menu on app
   - Select "Reboot app"
   - Or "Delete app" and redeploy

---

## 📞 Support Resources

**Streamlit Community:**
- Forum: https://discuss.streamlit.io/
- Documentation: https://docs.streamlit.io/
- GitHub: https://github.com/streamlit/streamlit

**Magnus Resume Bot:**
- API Documentation: https://magnus-resume-bot.vercel.app/docs
- Project GitHub: (your repository)
- Deployment Docs: See DEPLOYMENT_SUCCESS.md

---

## ✅ Deployment Checklist

Before going live:

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` updated
- [ ] Secrets configured in Streamlit Cloud
- [ ] API endpoint accessible
- [ ] Health check passing
- [ ] All features tested
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Mobile responsive
- [ ] Analytics setup (optional)

---

**Deployment Guide Version:** 1.0.0
**Last Updated:** October 19, 2025
**Platform:** Streamlit Community Cloud
**Author:** Magnus Resume Bot DevOps Assistant
