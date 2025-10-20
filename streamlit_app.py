"""
Streamlit Dashboard for Magnus Resume Bot.

This dashboard provides:
- API integration to FastAPI backend
- Job search interface with filters
- Results visualization with charts
- Application tracking and management
- Responsive design with modern UI
"""

import os
from urllib.parse import urlparse
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

# Page configuration
st.set_page_config(
    page_title="Magnus Resume Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .job-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #ffffff;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
NAVIGATION_PAGES = [
    "Dashboard",
    "Job Search",
    "Resume Upload",
    "Applications"
]

DEFAULT_LOCAL_API_BASE_URL = "http://localhost:8000"
DEFAULT_PROD_API_BASE_URL = "https://magnus-resume-bot.vercel.app"
CLOUD_HOME_DIRECTORY = "/home/adminuser"


def is_streamlit_cloud() -> bool:
    """Best-effort detection for Streamlit Community Cloud environment."""
    return os.path.expanduser("~") == CLOUD_HOME_DIRECTORY


def normalize_url(value: str) -> str:
    """Strip whitespace and trailing slash from URLs."""
    return value.strip().rstrip("/") if value else value


def resolve_initial_api_base_url() -> str:
    """Resolve the initial API base URL using secrets, env vars, and environment heuristics."""
    # Try to get from secrets, but handle if secrets file doesn't exist
    try:
        if hasattr(st, 'secrets') and st.secrets:
            api_url = st.secrets.get("API_BASE_URL")
            if api_url:
                return normalize_url(api_url)
    except (FileNotFoundError, Exception):
        # Secrets file doesn't exist or can't be read - continue to fallbacks
        pass

    # Try environment variable
    env_value = os.getenv("API_BASE_URL")
    if env_value:
        return normalize_url(env_value)

    # Default to the production API on Streamlit Cloud; otherwise use localhost for local dev.
    if is_streamlit_cloud():
        return DEFAULT_PROD_API_BASE_URL

    return DEFAULT_LOCAL_API_BASE_URL

# Initialize session state
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "selected_jobs" not in st.session_state:
    st.session_state.selected_jobs = []
if "applications" not in st.session_state:
    st.session_state.applications = None
if "nav_page" not in st.session_state:
    st.session_state.nav_page = NAVIGATION_PAGES[0]
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = resolve_initial_api_base_url()
if "api_update_message" not in st.session_state:
    st.session_state.api_update_message = None


def navigate_to(page_name: str):
    """Update the navigation page and rerun the app."""
    if page_name in NAVIGATION_PAGES:
        st.session_state.nav_page = page_name
        st.rerun()


def get_api_base_url() -> str:
    """Return the API base URL from session state."""
    return st.session_state.api_base_url


def update_api_base_url(new_url: str) -> None:
    """Update API base URL if valid."""
    normalized = normalize_url(new_url)

    if not normalized:
        st.warning("Please provide a valid API URL.")
        return

    parsed = urlparse(normalized)
    if not parsed.scheme or not parsed.netloc:
        st.warning("Please provide a full URL including scheme (e.g., https://example.com).")
        return

    st.session_state.api_base_url = normalized
    st.session_state.api_update_message = f"API URL updated to {normalized}"
    st.rerun()


# API Helper Functions
def make_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    files: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Make API request to FastAPI backend.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        data: Request data
        files: Files to upload

    Returns:
        Response data or None on error
    """
    base_url = get_api_base_url()
    url = f"{base_url}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, params=data, timeout=30)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=30)
        elif method == "PATCH":
            response = requests.patch(url, json=data, timeout=30)
        else:
            st.error(f"Unsupported method: {method}")
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        message = f"Could not connect to API at {base_url}"
        if base_url.startswith("http://localhost") and is_streamlit_cloud():
            message += ". Update the API URL in Settings for Streamlit Cloud deployments."
        st.error(message)
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None


def check_api_health() -> bool:
    """Check if API is available."""
    result = make_api_request("/health")
    return result is not None and result.get("status") == "healthy"


# UI Components
def render_header():
    """Render dashboard header."""
    st.markdown('<h1 class="main-header">🤖 Magnus Resume Bot</h1>', unsafe_allow_html=True)
    st.markdown("### Automated Job Search & Application Tracking")

    # API health check
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if check_api_health():
            st.success("✓ API Connected")
        else:
            st.error("✗ API Offline")


def render_statistics():
    """Render statistics cards."""
    stats = make_api_request("/api/stats")

    if stats and stats.get("success"):
        data = stats.get("stats", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Jobs", data.get("total_jobs", 0))

        with col2:
            st.metric("Total Applications", data.get("total_applications", 0))

        with col3:
            st.metric("Resumes Uploaded", data.get("total_resumes", 0))

        with col4:
            # Calculate application rate
            total_jobs = data.get("total_jobs", 0)
            total_apps = data.get("total_applications", 0)
            rate = (total_apps / total_jobs * 100) if total_jobs > 0 else 0
            st.metric("Application Rate", f"{rate:.1f}%")

        # Status breakdown
        if data.get("applications_by_status"):
            st.subheader("Applications by Status")
            status_df = pd.DataFrame(
                list(data["applications_by_status"].items()),
                columns=["Status", "Count"]
            )

            fig = px.pie(
                status_df,
                values="Count",
                names="Status",
                title="Application Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_job_search():
    """Render job search interface."""
    st.header("🔍 Job Search")

    with st.form("job_search_form"):
        col1, col2 = st.columns(2)

        with col1:
            search_term = st.text_input(
                "Search Term",
                placeholder="e.g., Python Developer, Data Scientist",
                help="Keywords to search for in job titles and descriptions"
            )

        with col2:
            location = st.text_input(
                "Location",
                placeholder="e.g., New York, Remote",
                help="Job location (leave empty for all locations)"
            )

        col3, col4, col5 = st.columns(3)

        with col3:
            sites = st.multiselect(
                "Job Sites",
                options=["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"],
                default=["indeed", "linkedin"],
                help="Select job sites to search"
            )

        with col4:
            results_wanted = st.number_input(
                "Results per Site",
                min_value=1,
                max_value=100,
                value=10,
                help="Number of results to fetch from each site"
            )

        with col5:
            hours_old = st.number_input(
                "Max Age (hours)",
                min_value=1,
                max_value=720,
                value=72,
                help="Maximum age of job listings"
            )

        submit = st.form_submit_button("Search Jobs", use_container_width=True)

    if submit:
        if not search_term:
            st.error("Please enter a search term")
            return

        if not sites:
            st.error("Please select at least one job site")
            return

        with st.spinner(f"Searching for '{search_term}' on {len(sites)} sites..."):
            result = make_api_request(
                "/api/jobs/search",
                method="POST",
                data={
                    "search_term": search_term,
                    "location": location,
                    "sites": sites,
                    "results_wanted": results_wanted,
                    "hours_old": hours_old
                }
            )

            if result and result.get("success"):
                st.session_state.search_results = result
                st.success(f"Found {result.get('total_jobs', 0)} jobs!")
            else:
                st.error("Search failed. Please try again.")


def render_search_results():
    """Render search results."""
    if not st.session_state.search_results:
        st.info("No search results yet. Use the search form above to find jobs.")
        return

    results = st.session_state.search_results
    total_jobs = results.get("total_jobs", 0)

    if total_jobs == 0:
        st.warning("No jobs found. Try different search criteria.")
        return

    st.header(f"📋 Search Results ({total_jobs} jobs)")

    # Results summary
    site_results = results.get("results", {})

    # Create tabs for each site
    tabs = st.tabs([f"{site.title()} ({data['count']})" for site, data in site_results.items()])

    for tab, (site, data) in zip(tabs, site_results.items()):
        with tab:
            jobs = data.get("jobs", [])

            if not jobs:
                st.info(f"No jobs found on {site.title()}")
                continue

            # Display jobs
            for idx, job in enumerate(jobs):
                with st.expander(
                    f"**{job.get('title', 'N/A')}** at {job.get('company', 'N/A')}",
                    expanded=(idx < 3)
                ):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                        st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                        st.markdown(f"**Type:** {job.get('job_type', 'N/A')}")

                        if job.get('date_posted'):
                            st.markdown(f"**Posted:** {job.get('date_posted')}")

                        if job.get('salary_min') or job.get('salary_max'):
                            salary = f"${job.get('salary_min', 0):,.0f} - ${job.get('salary_max', 0):,.0f}"
                            st.markdown(f"**Salary:** {salary}")

                        if job.get('description'):
                            st.markdown("**Description:**")
                            st.text_area(
                                "Description",
                                job.get('description', ''),
                                height=150,
                                key=f"desc_{site}_{idx}",
                                label_visibility="collapsed"
                            )

                    with col2:
                        if job.get('job_url'):
                            st.link_button(
                                "View Job",
                                job.get('job_url'),
                                use_container_width=True
                            )

                        if st.button("Track Application", key=f"track_{site}_{idx}"):
                            st.session_state.selected_jobs.append(job)
                            st.success("Added to tracking!")

            # Download option
            if jobs:
                df = pd.DataFrame(jobs)
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"Download {site.title()} Results (CSV)",
                    data=csv,
                    file_name=f"{site}_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )


def render_resume_upload():
    """Render resume upload interface."""
    st.header("📄 Resume Management")

    # Upload section
    st.subheader("Upload Resume")

    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx", "doc", "txt"],
        help="Supported formats: PDF, DOCX, DOC, TXT (max 10MB)"
    )

    if uploaded_file:
        col1, col2 = st.columns([3, 1])

        with col1:
            st.info(f"Selected: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

        with col2:
            if st.button("Upload", use_container_width=True):
                with st.spinner("Uploading resume..."):
                    result = make_api_request(
                        "/api/resumes/upload",
                        method="POST",
                        files={"file": uploaded_file},
                        data={"parse": "true"}
                    )

                    if result and result.get("success"):
                        st.success("Resume uploaded successfully!")
                        st.json(result)
                    else:
                        st.error("Upload failed")

    # List existing resumes
    st.subheader("Uploaded Resumes")

    resumes_result = make_api_request("/api/resumes")

    if resumes_result and resumes_result.get("success"):
        resumes = resumes_result.get("resumes", [])

        if resumes:
            df = pd.DataFrame(resumes)
            df = df[["id", "filename", "file_type", "uploaded_at"]]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No resumes uploaded yet")


def render_applications():
    """Render applications tracking interface."""
    st.header("📊 Application Tracking")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "pending", "applied", "interviewing", "rejected", "accepted"],
            index=0
        )

    with col2:
        limit = st.number_input("Number of Results", min_value=10, max_value=500, value=50)

    with col3:
        if st.button("Refresh", use_container_width=True):
            st.session_state.applications = None

    # Fetch applications
    params = {"limit": limit}
    if status_filter != "All":
        params["status"] = status_filter

    apps_result = make_api_request("/api/applications", data=params)

    if apps_result and apps_result.get("success"):
        applications = apps_result.get("applications", [])

        if not applications:
            st.info("No applications found")
            return

        st.success(f"Found {len(applications)} applications")

        # Display applications
        for idx, app in enumerate(applications):
            with st.expander(
                f"**{app.get('job_title', 'N/A')}** at {app.get('company', 'N/A')} - {app.get('status', 'pending').upper()}",
                expanded=(idx < 5)
            ):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Company:** {app.get('company', 'N/A')}")
                    st.markdown(f"**Location:** {app.get('location', 'N/A')}")
                    st.markdown(f"**Applied:** {app.get('applied_at', 'N/A')}")

                    if app.get('match_score'):
                        st.markdown(f"**Match Score:** {app.get('match_score'):.1f}%")

                    if app.get('notes'):
                        st.markdown(f"**Notes:** {app.get('notes')}")

                with col2:
                    # Update status
                    new_status = st.selectbox(
                        "Status",
                        options=["pending", "applied", "interviewing", "rejected", "accepted"],
                        index=["pending", "applied", "interviewing", "rejected", "accepted"].index(
                            app.get('status', 'pending')
                        ),
                        key=f"status_{app['id']}"
                    )

                    if st.button("Update", key=f"update_{app['id']}"):
                        update_result = make_api_request(
                            f"/api/applications/{app['id']}",
                            method="PATCH",
                            data={"status": new_status}
                        )

                        if update_result and update_result.get("success"):
                            st.success("Updated!")
                            st.rerun()
                        else:
                            st.error("Update failed")

        # Visualization
        if applications:
            df = pd.DataFrame(applications)

            # Timeline chart
            if 'applied_at' in df.columns:
                st.subheader("Application Timeline")
                df['applied_date'] = pd.to_datetime(df['applied_at']).dt.date
                timeline = df.groupby('applied_date').size().reset_index(name='count')

                fig = px.line(
                    timeline,
                    x='applied_date',
                    y='count',
                    title="Applications Over Time",
                    labels={'applied_date': 'Date', 'count': 'Number of Applications'}
                )
                st.plotly_chart(fig, use_container_width=True)


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.header("Navigation")

        # Get the current page index
        current_index = NAVIGATION_PAGES.index(st.session_state.nav_page) if st.session_state.nav_page in NAVIGATION_PAGES else 0

        page = st.radio(
            "Go to",
            options=NAVIGATION_PAGES,
            index=current_index,
            label_visibility="collapsed"
        )

        # Update nav_page if radio selection changed
        if page != st.session_state.nav_page:
            st.session_state.nav_page = page
            st.rerun()

        st.divider()

        st.subheader("Settings")

        with st.form("api_settings_form"):
            api_input = st.text_input(
                "API URL",
                value=get_api_base_url(),
                help="Configure the FastAPI backend endpoint used by the dashboard."
            )
            if st.form_submit_button("Save API URL", use_container_width=True):
                update_api_base_url(api_input)

        if st.session_state.api_update_message:
            st.success(st.session_state.api_update_message)
            st.session_state.api_update_message = None

        st.divider()

        st.caption(f"Magnus Resume Bot v1.0.0")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        return page


# Main Application
def main():
    """Main application entry point."""

    # Render header
    render_header()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "Dashboard":
        render_statistics()

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Quick Actions")
            st.info("Use the sidebar to navigate to different pages")
            st.markdown("- **Job Search**: Find new opportunities")
            st.markdown("- **Resume Upload**: Upload your resume")
            st.markdown("- **Applications**: Track your applications")

            if st.button("Open Job Search Page", use_container_width=True, key="quick_action_job_search"):
                navigate_to("Job Search")
            if st.button("Open Resume Upload Page", use_container_width=True, key="quick_action_resume_upload"):
                navigate_to("Resume Upload")

        with col2:
            st.subheader("Recent Activity")
            st.info("No recent activity")

    elif page == "Job Search":
        render_job_search()
        st.divider()
        render_search_results()

    elif page == "Resume Upload":
        render_resume_upload()

    elif page == "Applications":
        render_applications()


if __name__ == "__main__":
    main()
