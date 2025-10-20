# 🤖 Magnus Resume Bot

**Automated Job Search & Application Tracking System**

Magnus Resume Bot is a comprehensive, production-ready application that automates job searching across multiple platforms (Indeed, LinkedIn, ZipRecruiter, Glassdoor, Google), provides intelligent resume matching, and tracks your job applications—all with a beautiful web interface.

---

## ✨ Features

### 🔍 **Multi-Platform Job Search**
- Search jobs across 5 major platforms simultaneously
- Real-time scraping with rate limiting and exponential backoff
- Customizable search parameters (keywords, location, age, results count)
- Batch processing for efficient large-scale searches

### 📊 **Application Tracking**
- Track application status (pending, applied, interviewing, rejected, accepted)
- Match score calculation
- Notes and timeline management
- Visual analytics and statistics

### 📄 **Resume Management**
- Upload multiple resume versions (PDF, DOCX, DOC, TXT)
- Store and manage resume files
- Ready for future resume parsing integration

### 🎨 **Modern Web Interface**
- **Streamlit Dashboard**: Beautiful, responsive UI for local development
- **FastAPI Backend**: Production-ready REST API
- Interactive charts and visualizations
- Real-time statistics

### 🚀 **Production Ready**
- Thread-safe SQLite database with connection pooling
- Rate limiting per platform to avoid blocks
- Comprehensive error handling and logging
- Vercel deployment configuration included
- Environment-based configuration

---

## 📁 Project Structure

```
magnus-resume-bot/
├── api/                        # FastAPI application
│   ├── __init__.py
│   └── main.py                 # Main API endpoints
├── src/
│   ├── models/
│   │   ├── database.py         # Thread-safe database layer
│   │   └── job_scraper.py      # Rate-limited job scraper
│   └── utils/                  # Utility functions
├── tests/                      # Test suite
│   ├── __init__.py
│   └── test_database.py
├── data/                       # Database and uploaded files
├── docs/                       # Documentation
├── .streamlit/                 # Streamlit configuration
│   ├── config.toml
│   └── secrets.toml
├── streamlit_app.py            # Streamlit dashboard
├── run_api.py                  # API entry point
├── run_dashboard.py            # Dashboard entry point
├── requirements.txt            # Python dependencies
├── vercel.json                 # Vercel deployment config
├── .env.example                # Environment variables template
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git (for version control)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd magnus-resume-bot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

# Install spaCy language model (for NLP features)
python -m spacy download en_core_web_sm
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Environment Variables:**
```bash
# API Configuration
API_URL=http://localhost:8000
ENVIRONMENT=development

# Email Configuration (Optional)
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your_app_password

# Job Search Defaults
DEFAULT_LOCATION=United States
DEFAULT_SEARCH_TERM=SAP EWM Consultant
```

### 5. Initialize Database

The database will be automatically created on first run, but you can test it:

```bash
python tests/test_database.py
```

---

## 💻 Running the Application

### Option 1: Using Entry Point Scripts (Recommended)

**Terminal 1 - Start API Server:**
```bash
python run_api.py
```
- API available at: `http://localhost:8000`
- Interactive docs at: `http://localhost:8000/docs`

**Terminal 2 - Start Dashboard:**
```bash
python run_dashboard.py
```
- Dashboard available at: `http://localhost:8501`

### Option 2: Manual Start

**Start API:**
```bash
cd api
python main.py
# or
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Dashboard:**
```bash
streamlit run streamlit_app.py
```

---

## 📖 Usage Guide

### 1. Search for Jobs

1. Open the dashboard at `http://localhost:8501`
2. Navigate to **"Job Search"** page
3. Enter search criteria:
   - Search term (e.g., "Python Developer")
   - Location (e.g., "New York" or "Remote")
   - Select job sites (Indeed, LinkedIn, etc.)
   - Number of results per site
   - Maximum age of listings
4. Click **"Search Jobs"**
5. View results organized by platform

### 2. Track Applications

1. Navigate to **"Applications"** page
2. Click **"Track Application"** on any job
3. Update status as you progress:
   - Pending
   - Applied
   - Interviewing
   - Rejected
   - Accepted
4. Add notes for each application
5. View statistics and timeline

### 3. Upload Resume

1. Navigate to **"Resume Upload"** page
2. Click **"Browse files"**
3. Select resume (PDF, DOCX, DOC, or TXT)
4. Click **"Upload"**
5. View all uploaded resumes in the list

### 4. View Dashboard

1. Navigate to **"Dashboard"** page
2. View key metrics:
   - Total jobs found
   - Total applications
   - Application rate
   - Status distribution
3. See visual analytics

---

## 🔌 API Endpoints

### Health Check
```bash
GET /health
```

### Job Search
```bash
POST /api/jobs/search
Content-Type: application/json

{
  "search_term": "Python Developer",
  "location": "New York",
  "sites": ["indeed", "linkedin"],
  "results_wanted": 10,
  "hours_old": 72
}
```

### List Jobs
```bash
GET /api/jobs?limit=50&company=Google&location=Remote
```

### Get Job Details
```bash
GET /api/jobs/{job_id}
```

### Upload Resume
```bash
POST /api/resumes/upload
Content-Type: multipart/form-data

file: <resume.pdf>
parse: true
```

### List Resumes
```bash
GET /api/resumes
```

### Create Application
```bash
POST /api/applications
Content-Type: application/json

{
  "job_id": 1,
  "resume_id": 1,
  "notes": "Applied via company website"
}
```

### Update Application
```bash
PATCH /api/applications/{application_id}
Content-Type: application/json

{
  "status": "interviewing",
  "notes": "Phone screen scheduled",
  "match_score": 85.5
}
```

### Get Statistics
```bash
GET /api/stats
```

For interactive API documentation, visit: `http://localhost:8000/docs`

---

## 🌐 Deployment

### Deploy to Vercel

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Login to Vercel:**
```bash
vercel login
```

3. **Deploy:**
```bash
vercel
```

4. **Set Environment Variables:**
Go to your Vercel dashboard → Settings → Environment Variables:
- `PYTHONPATH=/var/task:/var/task/src`
- `DATABASE_PATH=/tmp/jobs.db`
- `CORS_ORIGINS=https://your-domain.com`

5. **Deploy to Production:**
```bash
vercel --prod
```

### Deploy Streamlit Dashboard

1. **Streamlit Community Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set `API_BASE_URL` in secrets
   - Deploy

2. **Update Streamlit Secrets:**
```toml
# .streamlit/secrets.toml
API_BASE_URL = "https://your-vercel-api.vercel.app"
```

---

## 🧪 Testing

### Run Database Tests
```bash
python tests/test_database.py
```

### Test API Manually
```bash
# Start the API
python run_api.py

# In another terminal, test endpoints
curl http://localhost:8000/health

# Test job search
curl -X POST http://localhost:8000/api/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Python Developer",
    "location": "Remote",
    "sites": ["indeed"],
    "results_wanted": 5
  }'
```

### Test Dashboard
```bash
python run_dashboard.py
# Open http://localhost:8501 in browser
```

---

## 🔧 Configuration

### Rate Limiting

Rate limits are configured per platform in `src/models/job_scraper.py`:

```python
RateLimitConfig(
    requests_per_minute=10,
    requests_per_hour=100,
    min_delay_seconds=2.0
)
```

### Database

Database location can be configured:
```python
# Default: data/magnus_resume_bot.db
db = Database(db_path=Path("custom/path/to/db.sqlite"))
```

### Retry Logic

Exponential backoff can be customized:
```python
RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)
```

---

## 📊 Database Schema

### Tables

**jobs**
- id, title, company, location, job_type
- date_posted, job_url, description
- salary_min, salary_max, currency, site
- created_at, updated_at

**resumes**
- id, filename, file_path, file_type
- content, parsed_data, uploaded_at

**applications**
- id, job_id, resume_id, status
- applied_at, match_score, notes

**job_skills**
- id, job_id, skill, importance

---

## 🛠️ Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure you're in the project root and virtual environment is activated
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**2. Database Locked**
```bash
# Close all connections or delete the database
rm data/magnus_resume_bot.db
# Restart the application
```

**3. API Connection Failed**
```bash
# Ensure API is running
curl http://localhost:8000/health

# Check .streamlit/secrets.toml has correct API_BASE_URL
```

**4. Rate Limit Errors**
```bash
# Wait for rate limit window to reset
# Or adjust rate limits in src/models/job_scraper.py
```

**5. Missing Dependencies**
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 Development Roadmap

- [ ] Resume parsing with skill extraction
- [ ] AI-powered job matching (using LLMs)
- [ ] Email notifications for new jobs
- [ ] Cover letter generation
- [ ] Browser automation for auto-apply
- [ ] Chrome extension
- [ ] Mobile app
- [ ] Job alerts and saved searches
- [ ] Analytics dashboard with advanced metrics
- [ ] Integration with more job platforms

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [jobspy](https://github.com/Bunsly/JobSpy) - Job scraping library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Dashboard framework
- [Vercel](https://vercel.com/) - Deployment platform

---

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: support@magnusresumebot.com (configure in .env)

---

## 🌟 Star History

If you find this project helpful, please consider giving it a star! ⭐

---

**Built with ❤️ for job seekers everywhere**

*Last Updated: October 2024*
