# GitHub Secrets Setup Guide

This guide explains how to set up GitHub Secrets for your repository so you can use them in GitHub Actions or when deploying.

## 🔐 Required Secrets

You need to set up these secrets in your GitHub repository:

1. **OPENAI_API_KEY** - Your OpenAI API key
2. **NEO4J_URI** - Neo4j Aurora connection URI (optional, for when you connect to real Neo4j)
3. **NEO4J_USER** - Neo4j username (optional)
4. **NEO4J_PASSWORD** - Neo4j password (optional)

## 📝 How to Add GitHub Secrets

### Step 1: Go to Your Repository Settings

1. Navigate to your GitHub repository: `https://github.com/dilshankm/echo-home`
2. Click on **Settings** (top menu)
3. In the left sidebar, click on **Secrets and variables** → **Actions**

### Step 2: Add Each Secret

Click **New repository secret** and add each one:

#### Secret 1: OPENAI_API_KEY
- **Name:** `OPENAI_API_KEY`
- **Value:** Your OpenAI API key (starts with `sk-...`)
- Click **Add secret**

#### Secret 2: NEO4J_URI (Optional - for when you have Neo4j Aurora)
- **Name:** `NEO4J_URI`
- **Value:** Your Neo4j URI (e.g., `neo4j+s://xxxxx.databases.neo4j.io`)
- Click **Add secret**

#### Secret 3: NEO4J_USER (Optional)
- **Name:** `NEO4J_USER`
- **Value:** Your Neo4j username (usually `neo4j`)
- Click **Add secret**

#### Secret 4: NEO4J_PASSWORD (Optional)
- **Name:** `NEO4J_PASSWORD`
- **Value:** Your Neo4j password
- Click **Add secret**

## 🚀 Using Secrets in GitHub Actions

If you want to use these secrets in GitHub Actions workflows, create `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        USE_MOCK_NEO4J: "true"
      run: |
        python -m pytest tests/
```

## 🐳 Using Secrets in Docker/Deployment

For Docker deployments (like Railway, Render, Heroku), set environment variables:

### Railway / Render / Heroku

In your deployment platform's environment variables settings, add:

```bash
OPENAI_API_KEY=sk-your-key-here
USE_MOCK_NEO4J=true

# Optional - when you have Neo4j Aurora:
# NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your-password
```

## 🔒 Security Notes

✅ **DO:**
- Store secrets in GitHub Secrets (never commit them)
- Use secrets in CI/CD workflows via `${{ secrets.NAME }}`
- Keep your `.env` file in `.gitignore` (already done!)

❌ **DON'T:**
- Commit `.env` file to git
- Hardcode API keys in your code
- Share secrets publicly

## ✅ Verification

After setting up secrets, verify they're working:

1. Check your `.gitignore` includes `.env` (already configured ✅)
2. Verify `.env` is not tracked by git:
   ```bash
   git ls-files | grep .env
   ```
   (Should return nothing)

3. Your secrets are now safely stored in GitHub and ready to use!

## 📚 Next Steps

- Set up GitHub Actions for automated testing
- Deploy to Railway/Render/Heroku using these secrets
- When you get Neo4j Aurora credentials, add them as secrets

