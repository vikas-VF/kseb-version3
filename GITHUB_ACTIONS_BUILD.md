# Building Windows Executable with GitHub Actions

## 🎯 Overview

Since you're on Linux and PyInstaller can only create Windows .exe files on Windows, the **best solution** is to use **GitHub Actions** to automatically build on GitHub's Windows servers.

### ✅ **Advantages of GitHub Actions**

- 🔧 **Automatic builds** on Windows servers
- 🆓 **Free for public repositories** (2000 minutes/month for private)
- ☁️ **No Windows machine needed**
- 🔄 **Builds on every push** or manual trigger
- 📦 **Artifacts stored for 30 days**
- 🏷️ **Automatic releases** on version tags

---

## 🚀 Quick Start

### Step 1: Enable GitHub Actions

The workflow file is already created at `.github/workflows/build-windows-exe.yml`

### Step 2: Push Your Code

```bash
# Commit and push
git add .
git commit -m "Add GitHub Actions workflow for Windows builds"
git push origin your-branch
```

### Step 3: Trigger Build

**Option A: Automatic (on push to main/master)**
```bash
# Push to main branch
git checkout main
git merge your-branch
git push origin main
# → Build starts automatically
```

**Option B: Manual Trigger**
1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "Build Windows Executable"
4. Click "Run workflow"
5. Select "full" (or backend-only/frontend-only)
6. Click "Run workflow"

**Option C: Version Tag**
```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
# → Builds and creates GitHub Release automatically
```

---

## 📋 How It Works

### GitHub Actions Workflow

```yaml
Build Process:
1. GitHub checks out your code on Windows server
2. Installs Python 3.11 and Node.js 18
3. Installs all pip and npm dependencies
4. Builds backend with PyInstaller
5. Builds frontend with Electron
6. Creates artifacts (downloadable .exe files)
7. (On version tags) Creates GitHub Release
```

### What Gets Built

```
Backend Job:
  → Runs on: Windows Server (latest)
  → Installs: Python + all pip packages
  → Creates: kseb-backend.exe (~500MB)
  → Upload: As GitHub artifact

Frontend Job:
  → Runs on: Windows Server (latest)
  → Installs: Node.js + all npm packages
  → Downloads: Backend artifact
  → Creates: KSEB Energy Analytics.exe (~600MB-1GB)
  → Upload: As GitHub artifact

Release Job (on tags):
  → Creates GitHub Release
  → Attaches both .exe files
  → Generates release notes
```

---

## 📥 Downloading Build Artifacts

### From GitHub Actions Tab

1. Go to your GitHub repository
2. Click "Actions" tab
3. Click on a completed workflow run
4. Scroll to "Artifacts" section
5. Download:
   - `kseb-backend-windows.zip`
   - `kseb-frontend-windows.zip`

### From GitHub Releases (for tagged versions)

1. Go to your GitHub repository
2. Click "Releases" (right sidebar)
3. Find your version (e.g., v1.0.0)
4. Download executable files directly

---

## 🏷️ Creating Releases

### Automatic Release Creation

```bash
# Tag your commit
git tag v1.0.0 -m "Release version 1.0.0"

# Push tag to GitHub
git push origin v1.0.0

# GitHub Actions will:
# 1. Build both executables
# 2. Create GitHub Release
# 3. Attach .exe files
# 4. Generate release notes
```

### Release Versioning

Follow semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)

---

## ⏱️ Build Time

| Job | Duration |
|-----|----------|
| Backend build | 10-15 minutes |
| Frontend build | 8-12 minutes |
| Total | **~20-30 minutes** |

---

## 💰 GitHub Actions Costs

### Free Tier (Public Repositories)
- ✅ **Unlimited minutes** for public repos
- ✅ **No cost**

### Private Repositories
- 🆓 **2000 minutes/month** free
- Each build uses ~30 minutes
- **~65 builds per month free**
- After that: $0.008 per minute

**For this project:**
- If building once per day: **FREE** (30 builds/month)
- If building multiple times: Still within free tier

---

## 🔧 Customizing the Workflow

### Change Python Version

Edit `.github/workflows/build-windows-exe.yml`:

```yaml
env:
  PYTHON_VERSION: '3.11'  # Change to '3.12' if needed
```

### Change Node.js Version

```yaml
env:
  NODE_VERSION: '18'  # Change to '20' if needed
```

### Add Build Steps

You can add additional steps like:
- Running tests before build
- Code signing
- Virus scanning
- Uploading to cloud storage

---

## 🧪 Testing Builds Locally on Windows

If you have access to a Windows machine:

```bash
# Clone repository
git clone <your-repo>
cd kseb-version2

# Run local build
python build_windows_exe.py --clean

# This uses the same logic as GitHub Actions
# but runs on your local Windows machine
```

---

## 🐛 Troubleshooting

### Build Fails: "Module not found"

**Problem:** Missing Python package

**Solution:** Add to `backend_fastapi/requirements.txt`:
```txt
missing-package==1.0.0
```

### Build Fails: "npm install failed"

**Problem:** Missing npm package

**Solution:** Add to `frontend/package.json`:
```json
{
  "dependencies": {
    "missing-package": "^1.0.0"
  }
}
```

### Build Takes Too Long (>45 minutes)

**Problem:** Workflow timeout

**Solution:** Add to workflow file:
```yaml
jobs:
  build-backend:
    timeout-minutes: 60  # Increase from default 45
```

### Artifact Too Large

**Problem:** GitHub has 2GB artifact size limit

**Solution:**
1. Enable UPX compression (already enabled)
2. Exclude unnecessary packages
3. Split into separate artifacts

---

## 📊 Monitoring Builds

### GitHub Actions Dashboard

1. Go to repository → Actions tab
2. See all workflow runs
3. Click on a run to see details
4. View logs for each job
5. Download artifacts

### Email Notifications

GitHub sends emails on:
- ✅ Build success
- ❌ Build failure
- ⚠️ Build warnings

### Status Badge

Add to your README.md:

```markdown
![Build Status](https://github.com/your-username/kseb-version2/actions/workflows/build-windows-exe.yml/badge.svg)
```

---

## 🔐 Security Considerations

### Secrets

The workflow uses:
- `GITHUB_TOKEN` (automatically provided)

No additional secrets needed unless you add:
- Code signing certificate
- Cloud storage credentials
- API keys

### Private Repositories

If your repo is private:
- Builds are private
- Artifacts are only visible to repo members
- Releases are only visible to repo members

---

## 📦 Distribution Strategy

### Option 1: GitHub Releases (Recommended)

**For end users:**
```
1. Go to: https://github.com/your-org/kseb-version2/releases
2. Download latest release
3. Run KSEB Energy Analytics.exe
```

**Advantages:**
- Professional presentation
- Version tracking
- Release notes
- Download statistics

### Option 2: Direct Artifact Download

**For testing/internal use:**
```
1. Go to Actions tab
2. Select workflow run
3. Download artifact
```

**Advantages:**
- Available immediately
- Don't need to create release
- Good for testing

### Option 3: External Hosting

After downloading from GitHub:
- Upload to your website
- Upload to cloud storage (S3, Azure)
- Share via download link

---

## 🎯 Best Practices

### 1. Use Version Tags

```bash
# Good: Semantic versioning
git tag v1.0.0
git tag v1.1.0
git tag v2.0.0

# Bad: Non-descriptive tags
git tag release
git tag build
```

### 2. Test Before Tagging

```bash
# Push to branch first
git push origin feature-branch

# Wait for build to succeed

# Then create release tag
git tag v1.0.0
git push origin v1.0.0
```

### 3. Write Release Notes

When creating a tag:

```bash
git tag v1.0.0 -m "Release v1.0.0

New features:
- Added demand forecasting
- Improved PyPSA integration
- Fixed Excel export bug

Requirements:
- Windows 10/11
- 2GB RAM
- 1.5GB disk space
"

git push origin v1.0.0
```

### 4. Keep Workflow Updated

Periodically update:
- Python version
- Node.js version
- Action versions (`actions/checkout@v4`, etc.)

---

## 🆚 Comparison: Local vs GitHub Actions

| Aspect | Local Build | GitHub Actions |
|--------|-------------|----------------|
| Requires Windows | ✅ YES | ❌ NO |
| Setup time | 1-2 hours | 5 minutes |
| Build time | 15-30 min | 20-30 min |
| Cost | $0 (your hardware) | $0 (public repos) |
| Automation | Manual | Automatic |
| Artifacts | Local files | Cloud storage |
| Sharing | Manual upload | GitHub Releases |
| CI/CD | No | Yes |

**Recommendation:** Use GitHub Actions for production builds

---

## 📝 Example Workflow

### Development Cycle

```bash
# 1. Develop features
git checkout -b feature-new-analysis
# ... make changes ...
git add .
git commit -m "Add new analysis feature"

# 2. Push and test build
git push origin feature-new-analysis
# → GitHub Actions builds automatically
# → Check Actions tab for results

# 3. If build succeeds, merge to main
git checkout main
git merge feature-new-analysis
git push origin main

# 4. Create release when ready
git tag v1.1.0 -m "Version 1.1.0 - New analysis feature"
git push origin v1.1.0
# → GitHub creates release with .exe files

# 5. Users download from Releases page
```

---

## 🎉 Success Criteria

After GitHub Actions completes, you should have:

✅ **Backend artifact** - `kseb-backend.exe` (~500MB)
✅ **Frontend artifact** - `KSEB Energy Analytics.exe` (~600MB-1GB)
✅ **GitHub Release** (for tagged versions)
✅ **Professional distribution** - Users can download easily
✅ **No manual Windows build** required

---

## 📞 Next Steps

1. ✅ Push your code to GitHub
2. ✅ Check Actions tab for build status
3. ✅ Download artifacts when complete
4. ✅ Test on a Windows machine
5. ✅ Create release tag when ready
6. ✅ Distribute to users via GitHub Releases

---

## 🔗 Useful Links

- **GitHub Actions Documentation:** https://docs.github.com/en/actions
- **PyInstaller Documentation:** https://pyinstaller.org/
- **Electron Builder Documentation:** https://www.electron.build/
- **Your Actions Tab:** `https://github.com/<username>/<repo>/actions`
- **Your Releases:** `https://github.com/<username>/<repo>/releases`

---

**Ready to build?** Push your code and check the Actions tab!

```bash
git add .
git commit -m "Ready for automated Windows build"
git push origin main
```
