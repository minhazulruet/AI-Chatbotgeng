# GitHub Deployment Guide

This guide walks you through deploying the AI Chatbot project to GitHub and setting up CI/CD.

## Step 1: Create a GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **+** icon in the top-right corner and select **New repository**
3. Configure your repository:
   - **Repository name**: `AI-Chatbot` (or your preferred name)
   - **Description**: "AI-Powered Chatbot with LLM and RAG"
   - **Visibility**: Choose **Public** (if you want it visible) or **Private**
   - **Do NOT initialize** with README, .gitignore, or license (we already have these)
4. Click **Create repository**

## Step 2: Configure Git User (First Time Only)

Open PowerShell/Terminal and run:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 3: Add Remote and Push Code

Navigate to your project folder and run:

```powershell
cd "D:\RA\AI Chatbot"

# Add the remote repository (replace USERNAME/REPO with your details)
git remote add origin https://github.com/USERNAME/AI-Chatbot.git

# Rename branch to main (GitHub standard)
git branch -M main

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: AI Chatbot with FastAPI, RAG, and LLM integration"

# Push to GitHub
git push -u origin main
```

## Step 4: Set Up GitHub Secrets (For Environment Variables)

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets (copy from your `.env` file):
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - Any other sensitive environment variables

> **Note**: These secrets will be available to GitHub Actions workflows without being exposed in logs

## Step 5: Create `.env.example`

Create `backend/.env.example` with all required variables (without values):

```env
# LLM APIs
OPENAI_API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_api_key_here

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Application Settings
DEBUG=false
ENVIRONMENT=production
```

Push this file so others know what environment variables are needed.

## Step 6: Verify CI/CD Pipeline

1. After pushing code, go to your repository on GitHub
2. Click the **Actions** tab
3. You should see the CI Pipeline workflow running
4. It will:
   - Set up Python environment
   - Install dependencies
   - Run linting checks
   - Execute tests (if any)
   - Upload coverage reports

## Step 7: Add Branch Protection (Optional)

For production safety:

1. Go to **Settings** → **Branches**
2. Click **Add rule** under "Branch protection rules"
3. Set branch name pattern: `main`
4. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Include administrators

## Step 8: Add Collaboration (Optional)

To add team members:

1. Go to **Settings** → **Collaborators**
2. Click **Add people**
3. Enter their GitHub username
4. Choose access level (Pull/Triage/Push/Maintain/Admin)

## Ongoing Development Workflow

### Create a Feature Branch
```powershell
git checkout -b feature/new-feature-name
```

### Make Changes and Commit
```powershell
git add .
git commit -m "Description of changes"
```

### Push to GitHub
```powershell
git push origin feature/new-feature-name
```

### Create Pull Request
1. Go to GitHub repository
2. Click **New pull request**
3. Compare `feature/new-feature-name` with `main`
4. Add description and submit
5. Wait for CI checks to pass
6. Request review from team members
7. Merge when approved

## Useful Git Commands

```powershell
# Check status
git status

# View commit history
git log --oneline

# Undo last commit (keeps changes)
git reset --soft HEAD~1

# Undo last commit (discards changes)
git reset --hard HEAD~1

# Update from remote
git pull origin main

# View differences
git diff
```

## Troubleshooting

### "Repository not found" error
- Verify the remote URL: `git remote -v`
- Update if wrong: `git remote set-url origin https://github.com/USERNAME/REPO.git`

### "Permission denied" error
- Use HTTPS with Personal Access Token instead of SSH
- Or generate SSH key: [GitHub SSH Setup](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

### Can't push large files
- GitHub has a 100MB file size limit
- Use Git LFS for large files: [Git LFS Setup](https://git-lfs.github.com/)
- Or ensure RAG data files are in `.gitignore`

## Additional Resources

- [GitHub Docs](https://docs.github.com)
- [Git Documentation](https://git-scm.com/doc)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)

---

**Next Steps**: After deployment, consider:
- Setting up branch protection rules
- Adding contributors
- Enabling GitHub Pages for documentation
- Creating releases/tags for versions
- Setting up issue templates
