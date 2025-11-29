# Docker Hub Push Setup

## Current Status

✅ **GitHub Actions workflow is ready** - `.github/workflows/docker.yml` will automatically build and push to Docker Hub when you push to the `main` branch.

## Setup Instructions

### Step 1: Add Docker Hub Secrets to GitHub

1. Go to: https://github.com/dilshankm/echo-home/settings/secrets/actions

2. Click **"New repository secret"** and add:

   **Secret 1:**
   - Name: `DOCKER_USERNAME`
   - Value: Your Docker Hub username

   **Secret 2:**
   - Name: `DOCKER_PASSWORD`
   - Value: Your Docker Hub password (or access token)

### Step 2: Verify Image Name

The workflow pushes to: `YOUR_DOCKER_USERNAME/echo-home`

You can change this in `.github/workflows/docker.yml` if needed.

### Step 3: Push to GitHub

Once secrets are added, push to main branch:

```bash
git add .
git commit -m "Add Docker Hub push workflow"
git push origin main
```

The GitHub Actions will automatically:
1. Build the Docker image
2. Test it (run API tests)
3. Push to Docker Hub

## Manual Push to Docker Hub

You can also push manually:

```bash
# Login to Docker Hub
docker login

# Tag the image
docker tag echo-home:latest YOUR_DOCKER_USERNAME/echo-home:latest

# Push to Docker Hub
docker push YOUR_DOCKER_USERNAME/echo-home:latest
```

## Verify Push

After pushing, check your Docker Hub:
- https://hub.docker.com/r/YOUR_DOCKER_USERNAME/echo-home

## Pull and Run

Others can now pull and run:

```bash
docker pull YOUR_DOCKER_USERNAME/echo-home:latest
docker run -d --name echo-home-api \
  -e OPENAI_API_KEY=your-key \
  -e USE_MOCK_NEO4J=true \
  -p 8000:8000 \
  YOUR_DOCKER_USERNAME/echo-home:latest
```

