# Building KSEB Energy Analytics as Windows Desktop Application

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Build Steps](#detailed-build-steps)
5. [Distribution](#distribution)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## 🎯 Overview

This guide explains how to convert the KSEB Energy Analytics webapp into a standalone Windows desktop application that:

✅ **Requires NO Python or Node.js** on user machines
✅ **Bundles ALL dependencies** into executables
✅ **Works offline** (no internet needed after installation)
✅ **Installs like any Windows app** (Start Menu, Desktop shortcut)
✅ **Runs on clean Windows 10/11** without any setup

### What You're Building

```
KSEB-Setup.exe (Installer - ~700MB-1.2GB)
│
├── Frontend (Electron + React)
│   └── Embedded: Chromium, Node.js, React app, all npm packages
│
└── Backend (PyInstaller + FastAPI)
    └── Embedded: Python runtime, FastAPI, PyPSA, numpy, scipy, all pip packages
```

---

## 🔧 Prerequisites

### Development Machine Requirements

You need **ONE Windows machine** with the following installed (only for building, not for end users):

#### 1. Python 3.11 or higher
```bash
# Check version
python --version  # Should show 3.11.x or higher

# Install if needed
# Download from: https://www.python.org/downloads/
```

#### 2. Node.js 18 or higher
```bash
# Check version
node --version  # Should show v18.x or higher
npm --version   # Should show 9.x or higher

# Install if needed
# Download from: https://nodejs.org/
```

#### 3. PyInstaller
```bash
# Install
pip install pyinstaller

# Verify
pyinstaller --version
```

#### 4. NSIS (Nullsoft Scriptable Install System) - Optional
```bash
# Only needed for creating installer
# Download from: https://nsis.sourceforge.io/
# Or skip and distribute the portable .exe directly
```

#### 5. Git (for version control)
```bash
git --version
```

### Recommended Development Setup

- **OS:** Windows 10/11 (64-bit)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk Space:** 5GB free space for build artifacts
- **CPU:** Multi-core processor (build is CPU-intensive)

---

## 🚀 Quick Start

### Option 1: Automated Build (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/kseb-version2.git
cd kseb-version2

# Run automated build script
python build_windows_exe.py --clean

# Wait 15-30 minutes for build to complete

# Find outputs in:
# - dist/kseb-backend.exe (Backend)
# - dist/KSEB Energy Analytics.exe (Frontend)
# - installer/KSEB-Setup.exe (Installer)
```

### Option 2: Manual Build

See [Detailed Build Steps](#detailed-build-steps) below.

---

## 📖 Detailed Build Steps

### Step 1: Prepare Backend (PyInstaller)

#### 1.1 Install Backend Dependencies
```bash
cd backend_fastapi
pip install -r requirements.txt
```

#### 1.2 Create PyInstaller Spec File

The build script creates this automatically, but you can also create it manually:

**File: `backend.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['backend_fastapi/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend_fastapi/input', 'input'),  # Embed Excel templates
    ],
    hiddenimports=[
        'fastapi', 'uvicorn', 'pydantic',
        'pandas', 'numpy', 'scipy',
        'sklearn', 'statsmodels',
        'pypsa', 'xarray', 'netCDF4',
        'matplotlib', 'seaborn', 'plotly',
        'openpyxl', 'xlsxwriter',
    ],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='kseb-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress
    console=False,  # No console window
)
```

#### 1.3 Build Backend Executable
```bash
# From project root
pyinstaller --clean backend.spec

# Wait 5-10 minutes
# Output: dist/kseb-backend.exe
```

#### 1.4 Test Backend
```bash
# Run backend
.\dist\kseb-backend.exe

# In another terminal, test API
curl http://localhost:8000/health
# Should return: {"status": "ok"}

# Stop backend (Ctrl+C)
```

---

### Step 2: Prepare Frontend (Electron)

#### 2.1 Install Frontend Dependencies
```bash
cd frontend
npm install
```

#### 2.2 Build React App
```bash
npm run build

# Output: frontend/dist/ folder with production build
```

#### 2.3 Add Electron Dependencies
```bash
npm install --save-dev electron electron-builder
npm install axios  # For backend communication
```

#### 2.4 Create Electron Files

The build script creates these automatically, but here's what you need:

**File: `frontend/electron-main.js`**

```javascript
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

let backendProcess = null;

// Start backend
function startBackend() {
  const backendExe = path.join(process.resourcesPath, 'backend', 'kseb-backend.exe');
  backendProcess = spawn(backendExe, [], { windowsHide: true });
}

// Wait for backend
async function waitForBackend() {
  for (let i = 0; i < 30; i++) {
    try {
      await axios.get('http://localhost:8000/health', { timeout: 1000 });
      return true;
    } catch {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  return false;
}

app.on('ready', async () => {
  await startBackend();
  const ready = await waitForBackend();

  if (ready) {
    const win = new BrowserWindow({
      width: 1400,
      height: 900,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    win.loadFile(path.join(__dirname, 'dist', 'index.html'));
  } else {
    app.quit();
  }
});

app.on('quit', () => {
  if (backendProcess) backendProcess.kill();
});
```

**File: `frontend/preload.js`**

```javascript
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  platform: process.platform
});
```

#### 2.5 Update package.json

Add to `frontend/package.json`:

```json
{
  "main": "electron-main.js",
  "scripts": {
    "build": "vite build",
    "electron:build": "electron-builder"
  },
  "build": {
    "appId": "com.kseb.analytics",
    "productName": "KSEB Energy Analytics",
    "files": [
      "dist/**/*",
      "electron-main.js",
      "preload.js"
    ],
    "extraResources": [
      {
        "from": "../dist/kseb-backend.exe",
        "to": "backend/kseb-backend.exe"
      }
    ],
    "win": {
      "target": "portable"
    }
  }
}
```

#### 2.6 Build Electron App
```bash
npm run electron:build

# Wait 5-10 minutes
# Output: dist/KSEB Energy Analytics.exe
```

---

### Step 3: Create Installer (Optional)

If you have NSIS installed, create an installer:

**File: `installer/installer.nsi`**

```nsis
!include "MUI2.nsh"

Name "KSEB Energy Analytics"
OutFile "KSEB-Setup.exe"
InstallDir "$PROGRAMFILES\KSEB Energy Analytics"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File "..\dist\KSEB Energy Analytics.exe"

  CreateDirectory "$SMPROGRAMS\KSEB Energy Analytics"
  CreateShortcut "$SMPROGRAMS\KSEB Energy Analytics\KSEB.lnk" "$INSTDIR\KSEB Energy Analytics.exe"
  CreateShortcut "$DESKTOP\KSEB Energy Analytics.lnk" "$INSTDIR\KSEB Energy Analytics.exe"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\*.*"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\KSEB Energy Analytics\*.*"
  RMDir "$SMPROGRAMS\KSEB Energy Analytics"
  Delete "$DESKTOP\KSEB Energy Analytics.lnk"
SectionEnd
```

Build installer:
```bash
cd installer
makensis installer.nsi

# Output: installer/KSEB-Setup.exe
```

---

## 📦 Distribution

### What to Distribute

Choose one of:

**Option 1: Installer (Recommended)**
- File: `KSEB-Setup.exe` (~700MB-1.2GB)
- Users run installer, creates Start Menu shortcut
- Professional experience

**Option 2: Portable Executable**
- File: `KSEB Energy Analytics.exe` (~600MB-1GB)
- Users can run directly without installation
- Good for USB drives or network shares

### Distribution Checklist

- [ ] Test on clean Windows 10 machine (no Python/Node.js)
- [ ] Test on Windows 11
- [ ] Verify all features work (forecasting, PyPSA, etc.)
- [ ] Check file size (should be under 1.5GB)
- [ ] Create user documentation
- [ ] Create release notes
- [ ] Test uninstaller

---

## 🧪 Testing

### Pre-Release Testing

#### Test on Clean Windows Machine

**CRITICAL:** Test on a Windows machine with:
- ✅ NO Python installed
- ✅ NO Node.js installed
- ✅ NO development tools
- ✅ Fresh Windows 10/11 install

#### Functional Tests

1. **Installation**
   - [ ] Installer runs without errors
   - [ ] Creates Start Menu shortcut
   - [ ] Creates Desktop shortcut
   - [ ] Creates application data folder

2. **Application Launch**
   - [ ] App launches within 10-15 seconds
   - [ ] No console windows appear
   - [ ] Main window displays correctly

3. **Core Features**
   - [ ] Create new project
   - [ ] Upload Excel files
   - [ ] Run demand forecasting
   - [ ] Generate load profiles
   - [ ] Run PyPSA optimization
   - [ ] View results
   - [ ] Export to Excel

4. **Edge Cases**
   - [ ] Multiple projects
   - [ ] Large Excel files (>100MB)
   - [ ] Long file paths
   - [ ] Special characters in project names
   - [ ] Network drives
   - [ ] OneDrive/cloud storage

5. **Uninstallation**
   - [ ] Uninstaller runs without errors
   - [ ] Removes all files
   - [ ] Asks about keeping user data
   - [ ] Removes shortcuts

### Performance Testing

- **Startup time:** Should be <15 seconds
- **Backend ready:** Should be <10 seconds
- **Memory usage:** <2GB RAM for typical operations
- **File operations:** Excel import <30 seconds for 50MB files

---

## 🔧 Troubleshooting

### Build Issues

#### PyInstaller fails with "ModuleNotFoundError"

**Problem:** Missing hidden imports

**Solution:** Add to `hiddenimports` in backend.spec:
```python
hiddenimports=[
    'missing_module_name',
]
```

#### Backend executable crashes on startup

**Problem:** Missing data files or DLLs

**Solution:**
1. Check PyInstaller output for warnings
2. Add missing files to `datas` in spec file
3. Run with console=True to see error messages

#### Electron build fails

**Problem:** Missing dependencies

**Solution:**
```bash
cd frontend
npm install --save-dev electron electron-builder
npm install
```

### Runtime Issues

#### App doesn't start - No window appears

**Diagnosis:**
1. Check if backend is running (Task Manager)
2. Try accessing http://localhost:8000/health in browser
3. Check backend logs

**Solution:**
- Increase wait time in electron-main.js
- Check firewall settings
- Ensure port 8000 is available

#### "Backend failed to start within timeout"

**Problem:** Backend takes too long to start

**Solution:** Increase `MAX_WAIT_TIME` in electron-main.js:
```javascript
const MAX_WAIT_TIME = 60000; // 60 seconds
```

#### Excel files not loading

**Problem:** Templates not embedded

**Solution:** Check `datas` in backend.spec:
```python
datas=[
    ('backend_fastapi/input', 'input'),  # Must be present
]
```

#### PyPSA optimization fails

**Problem:** netCDF4 or solver issues

**Solution:**
1. Test PyPSA on development machine first
2. Ensure all PyPSA dependencies in hiddenimports
3. Check solver (e.g., GLPK) is bundled

### Large File Size Issues

**Problem:** Executable is >2GB

**Solution:**
1. Enable UPX compression: `upx=True`
2. Exclude unnecessary packages: `excludes=['tkinter', 'unittest']`
3. Use `--onefile` flag carefully (increases startup time)

---

## ❓ FAQ

### Q: Do end users need Python or Node.js installed?

**A:** NO! All dependencies are bundled. Users just run the installer.

### Q: Can I reduce the file size?

**A:** Yes:
- Enable UPX compression in PyInstaller
- Exclude unnecessary packages
- Use electron-builder compression
- Split into backend/frontend executables

### Q: Does it work offline?

**A:** YES! No internet connection needed after installation.

### Q: Can I update the app without reinstalling?

**A:** Yes, implement auto-update with electron-updater, or distribute new installer.

### Q: How do I debug issues?

**A:**
1. Build with `console=True` in backend.spec to see errors
2. Enable DevTools in Electron (remove closeDevTools code)
3. Check logs in `%APPDATA%\KSEB Energy Analytics\logs`

### Q: Can I distribute on other platforms (Mac/Linux)?

**A:** Yes, but requires:
- PyInstaller builds on target OS
- Electron builder supports Mac/Linux
- Some code changes for platform-specific paths

### Q: How long does the build take?

**A:**
- Backend: 5-10 minutes
- Frontend: 5-10 minutes
- Installer: 2-3 minutes
- **Total: 15-25 minutes**

### Q: What if users have port 8000 in use?

**A:** Implement port auto-detection (see WINDOWS_CONVERSION_PLAN.md)

### Q: Can I include a database later?

**A:** Yes, but:
- SQLite: Bundle database file
- PostgreSQL/MySQL: Require separate installation or bundle server

---

## 📞 Support

### Getting Help

1. **Check logs:**
   - Backend: `%APPDATA%\KSEB Energy Analytics\logs\backend.log`
   - Frontend: Electron DevTools console

2. **Common issues:** See [Troubleshooting](#troubleshooting)

3. **Report bugs:** Create issue on GitHub with:
   - Windows version
   - Error messages
   - Steps to reproduce

### Additional Resources

- **PyInstaller docs:** https://pyinstaller.org/
- **Electron docs:** https://www.electronjs.org/
- **NSIS docs:** https://nsis.sourceforge.io/Docs/

---

## 📝 Build Script Options

### Using build_windows_exe.py

```bash
# Clean build (recommended)
python build_windows_exe.py --clean

# Skip backend (if already built)
python build_windows_exe.py --skip-backend

# Skip frontend (if already built)
python build_windows_exe.py --skip-frontend

# Skip installer (create portable exe only)
python build_windows_exe.py --skip-installer

# Multiple options
python build_windows_exe.py --clean --skip-installer
```

---

## ✅ Checklist: Ready to Build

Before you start, ensure:

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] PyInstaller installed (`pip install pyinstaller`)
- [ ] All backend dependencies install without errors
- [ ] All frontend dependencies install without errors
- [ ] You have 5GB free disk space
- [ ] You have a clean Windows 10/11 VM for testing
- [ ] You have read this entire guide

---

## 🎉 Success!

After successful build, you should have:

✅ **KSEB-Setup.exe** - Professional Windows installer
✅ **No Python/Node.js required** for end users
✅ **All dependencies bundled**
✅ **Works on clean Windows machines**
✅ **Professional desktop application**

Congratulations! You've successfully converted your webapp to a Windows desktop application!

---

**Last Updated:** 2025-11-05
**Version:** 1.0
**Build Script:** build_windows_exe.py
