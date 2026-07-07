# 🚀 Hirify – Job Portal Backend API (Flask + Supabase)

This repository contains the **Python Flask backend API** for **Hirify** .  
It provides secure APIs for managing users, companies, jobs, and applications.
This project follows a **fork → branch → pull request** workflow to prevent accidental changes to the main branch.

---

## 🎯 Objective

Build a scalable, secure backend for a job portal where:

- Recruiters can post jobs  
- Candidates can apply to jobs  
- Resumes are stored securely in cloud storage  
- Access is role-based 

---

## 🚀 Getting Started — Local Setup

> Follow these steps to create a safe local dev environment using the fork → branch → PR workflow.

### 1. Fork the repository
Click **Fork** on the top-right of the original repo to create a copy under your GitHub account.

### 2. Clone **your fork**
Replace `YOUR_USERNAME` with your GitHub handle:

```bash
git clone https://github.com/YOUR_USERNAME/Hirify.git

cd Hirify

cd hirify-backend
```

### 3. Create & activate virtual environment
``` bash
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (cmd)
venv\Scripts\activate
```

### 4. Install dependencies
``` bash
pip install -r requirements.txt
```
🔐 Environment Variables (.env)
Create a .env file in the repository root (hirify-backend/) with your credentials.
⚠️ DO NOT COMMIT .env — it is included in .gitignore.
Example .env:
# Flask
``` bash
FLASK_APP=run.py
FLASK_ENV=development
PORT=5000

# Supabase
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_KEY=<your-service-role-public-key>

```

▶️ Run the Application
``` bash
python run.py
The API will be available at:
http://127.0.0.1:5000/
```
🔁 Team Contribution Workflow (Very Important)
To protect the main branch and keep the repo stable, follow this Fork → Branch → PR workflow. Never push directly to main.
✅ Rule: Always work on a branch and create a PR from your fork


🪵 Step-by-step workflow
1. Sync & switch to main
``` bash
git checkout main
git pull origin main
```

2. Create a new branch
Name branches clearly:
``` bash
git checkout -b feature/your-descriptive-branch-name
```
Examples:
feature/jwt-middleware
fix/supabase-connection
feature/application-endpoint

3. Make your changes
Work locally, run tests, and ensure quality.

4. Stage & commit
Use semantic commit messages:
``` bash
git add .
git commit -m "feat: add POST /jobs endpoint"
```
Commit prefixes:
feat: new feature
fix: bugfix
chore: maintenance/cleanup
docs: documentation

5. Push branch to your fork
``` bash
git push origin feature/your-descriptive-branch-name
```

6. Create a Pull Request (PR)
Go to your fork on GitHub. 
Click Compare & pull request (or Contribute → Open pull request).
Set: 
Base repo: original team repo
Base branch: main
Head repo: your fork
Compare branch: your feature branch
Fill the PR template / description and request reviewers.
✅ Your code must be reviewed and approved before merging into the team repo main.
