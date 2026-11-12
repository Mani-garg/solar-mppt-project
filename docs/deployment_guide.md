# Deployment Guide & Local Execution Instructions

## 1. System Requirements
- **Operating System:** Windows 10/11, Linux (Ubuntu/Debian), or macOS
- **Python Version:** Python 3.9, 3.10, 3.11, 3.12, or 3.13
- **Git:** Git 2.30+

---

## 2. Local Setup via Windows PowerShell

### Step 1: Open PowerShell and Navigate to Project
```powershell
cd C:\Users\DELL\.gemini\antigravity\scratch\solar_mppt_project
```

### Step 2: Create a Dedicated Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an ExecutionPolicy restriction, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Automated Pytest Verification Suite
```powershell
python -m pytest tests -v
```
All 21 unit and integration tests must pass before running the interactive web application.

### Step 5: Launch the Interactive Streamlit Platform
```powershell
streamlit run app.py
```
Streamlit will automatically open your default browser at `http://localhost:8501`.

---

## 3. GitHub Repository Preparation
To push the project to your GitHub account:

### Initialize Git Repository:
```powershell
git init
git add .
git commit -m "Initial commit: Production-quality Fuzzy Logic MPPT Simulation Platform"
```

### Link Remote Repository and Push:
```powershell
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/solar-mppt-project.git
git push -u origin main
```

---

## 4. Streamlit Community Cloud Deployment
1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/) with your GitHub account.
2. Click **"New App"**.
3. Select your repository: `<YOUR_GITHUB_USERNAME>/solar-mppt-project`.
4. Set **Branch:** `main`.
5. Set **Main file path:** `app.py`.
6. Click **"Deploy!"**.
7. The platform will build and host your application with a public `*.streamlit.app` URL.

---

## 5. Deployment Verification Checklist
- [x] Relative module imports (`src.*`) without absolute host paths
- [x] Zero hardcoded API keys or external secrets
- [x] Standard `requirements.txt` with verified compatible versions
- [x] Headless Streamlit configuration in `.streamlit/config.toml`
- [x] Fully self-contained mathematical models without MATLAB or paid dependencies
