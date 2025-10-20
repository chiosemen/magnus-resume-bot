# Magnus Resume Bot - Quick Start Guide

Get up and running in 5 minutes!

---

## Prerequisites

- Python 3.9+ installed
- Internet connection

---

## Installation

### 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 2. Install Dependencies (Optional - for full functionality)

```bash
pip install -r requirements.txt
```

**Note:** The application will run without all dependencies. Install them when needed:
- For job scraping: `pip install jobspy pandas`
- For NLP features: `pip install spacy && python -m spacy download en_core_web_sm`
- For resume parsing: `pip install pdfplumber python-docx`

---

## Running the Application

### Option 1: Start Both (Recommended)

**Terminal 1 - API:**
```bash
python run_api.py
```

**Terminal 2 - Dashboard:**
```bash
python run_dashboard.py
```

### Option 2: API Only

```bash
python run_api.py
```

Then visit:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

---

## First Steps

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

### 2. View Statistics

```bash
curl http://localhost:8000/api/stats
```

### 3. Open Interactive Docs

Open in browser: http://localhost:8000/docs

### 4. Open Dashboard (if running)

Open in browser: http://localhost:8501

---

## Common Tasks

### Search for Jobs

```bash
curl -X POST http://localhost:8000/api/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Python Developer",
    "location": "Remote",
    "sites": ["indeed"],
    "results_wanted": 5
  }'
```

### View All Jobs

```bash
curl 'http://localhost:8000/api/jobs?limit=10'
```

### Create Application

```bash
curl -X POST http://localhost:8000/api/applications \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "notes": "Applied via company website"
  }'
```

---

## Troubleshooting

### "Module not found" error
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Ensure you're in the project root
cd /Users/chinyeosemene/magnus-resume-bot
```

### "Connection refused" error
```bash
# Make sure API is running
python run_api.py
```

### "Database locked" error
```bash
# Close all connections or restart
rm data/magnus_resume_bot.db
python run_api.py
```

---

## Configuration

Edit `.env` file to customize:

```bash
nano .env
```

Common settings:
- `API_URL` - API endpoint URL
- `DEFAULT_LOCATION` - Your preferred job location
- `DEFAULT_SEARCH_TERM` - Your preferred job search term

---

## Testing

### Run Database Tests

```bash
python tests/test_database.py
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Statistics
curl http://localhost:8000/api/stats

# Jobs list
curl 'http://localhost:8000/api/jobs?limit=5'
```

---

## Next Steps

1. **Explore the Dashboard**: Visit http://localhost:8501
2. **Read Full Documentation**: See README.md
3. **Check Test Results**: See TESTING_RESULTS.md
4. **Deploy to Production**: Follow deployment guide in README.md

---

## Quick Reference

| Component | URL | Command |
|-----------|-----|---------|
| API | http://localhost:8000 | `python run_api.py` |
| API Docs | http://localhost:8000/docs | - |
| Dashboard | http://localhost:8501 | `python run_dashboard.py` |
| Database | `data/magnus_resume_bot.db` | SQLite |

---

## Getting Help

- **Documentation**: README.md
- **Test Results**: TESTING_RESULTS.md
- **API Docs**: http://localhost:8000/docs
- **Issues**: Create an issue on GitHub

---

**Built with ❤️ - Ready to find your dream job!**
