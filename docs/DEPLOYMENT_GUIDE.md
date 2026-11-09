# Enterprise Employee Analytics - Cloud Deployment Guide

This guide details the step-by-step procedure to deploy the **Enterprise Employee Analytics & Data Warehouse System** to **Streamlit Community Cloud** (free, public cloud hosting).

---

## 1. Prerequisites

1. Your repository is pushed to GitHub:
   ```
   https://github.com/<your-username>/Enterprise-Employee-Analytics-Data-Warehouse-System
   ```
2. A free [Streamlit Community Cloud account](https://share.streamlit.io) connected to your GitHub account.

---

## 2. Cloud Architecture Readiness

The application has been engineered to be **100% cloud-ready out of the box**:
- **Automatic Fallback Engine**: If an external MySQL server is not detected, `DatabaseConnection` automatically falls back to an embedded SQLite dimensional warehouse located at `data/enterprise_analytics.db`.
- **Auto-Provisioning on Cold Start**: If running on a fresh container where the database does not exist, `_ensure_sqlite_ready()` automatically provisions the star schema and seeds data on first boot.
- **Theme Configuration**: Pre-configured in `.streamlit/config.toml`.
- **Dependency Isolation**: All libraries (`streamlit`, `plotly`, `altair`, `pandas`, `sqlalchemy`, `pymysql`, `mysql-connector-python`, `faker`) are declared in `requirements.txt`.

---

## 3. Deployment Steps on Streamlit Community Cloud

### Step 1: Create New App
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New app"** (or **"Create app"**).
3. Select your repository: `Enterprise-Employee-Analytics-Data-Warehouse-System`.
4. Set the **Branch** to `main`.
5. Set the **Main file path** to:
   ```
   app.py
   ```
   *(Do NOT use `app/streamlit_app.py`; the canonical entry point is `app.py`)*

### Step 2: Configure Cloud Secrets (Optional for MySQL, Not Required for SQLite)
If you wish to connect your cloud app to a hosted cloud MySQL database (e.g., AWS RDS, PlanetScale, Aiven, or Clever Cloud):
1. Expand **Advanced settings...** at the bottom of the deployment form.
2. Under **Secrets**, paste the following block adapted from `.streamlit/secrets.toml.example`:
   ```toml
   [mysql]
   host = "your-cloud-mysql-host.com"
   port = 3306
   user = "your_user"
   password = "your_strong_password"
   oltp_database = "enterprise_hr_oltp"
   olap_database = "enterprise_hr_dw"

   [app]
   backend = "mysql"
   ```
3. If you want the app to run completely serverless using the built-in dimensional warehouse, leave secrets empty or set:
   ```toml
   [app]
   backend = "auto"
   ```

### Step 3: Deploy!
1. Click **"Deploy!"**.
2. Streamlit Cloud will pull the repository, install dependencies from `requirements.txt`, and start `app.py`.
3. Within 1–2 minutes, your live URL will be active at:
   ```
   https://<your-custom-subdomain>.streamlit.app
   ```

---

## 4. Verification Checklist on Cloud

Once launched:
- [ ] **Executive Landing Page (`app.py`)**: Top KPI cards (Active Workforce, Avg Compensation, Flight Risk, SCD2 Transitions) load and display valid integers.
- [ ] **HR Operations Portal (`pages/1_HR_Operations.py`)**: Test onboarding a new employee and triggering an SCD Type 2 reassignment.
- [ ] **Executive Analytics Dashboard (`pages/2_Executive_Analytics.py`)**: Verify the DENSE_RANK leaderboard, YoY trends, and Altair Project Allocation & Bottleneck chart render interactively.
