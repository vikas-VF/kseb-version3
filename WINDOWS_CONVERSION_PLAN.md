# KSEB Energy Analytics - Windows Executable Conversion Plan

## Executive Summary

**Recommendation:** Electron + PyInstaller Hybrid Approach

This plan converts your full-stack webapp (React + FastAPI) into a native Windows desktop application with **ZERO external dependencies** for end users.

---

## Architecture Overview

### Current Development Architecture
```
┌─────────────────────┐
│   Web Browser       │
│ (localhost:3000)    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Vite Dev Server    │
│  (React Frontend)   │
└──────────┬──────────┘
           │ [Axios HTTP]
┌──────────▼──────────┐
│  FastAPI Backend    │
│  (localhost:8000)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  File System        │
│  (Excel + JSON)     │
└─────────────────────┘
```

### Proposed Windows Desktop Architecture
```
┌───────────────────────────────────┐
│   KSEB.exe (Launcher)             │
│   - Starts backend silently       │
│   - Waits for backend ready       │
│   - Launches frontend window      │
└──────────────┬────────────────────┘
               │
        ┌──────┴──────┐
        │             │
┌───────▼─────┐  ┌───▼──────────────┐
│ backend.exe │  │ frontend.exe     │
│ (PyInstaller│  │ (Electron)       │
│  bundle)    │  │                  │
│             │  │                  │
│ • Python    │  │ • Chromium       │
│ • FastAPI   │  │ • Node.js        │
│ • PyPSA     │  │ • React build    │
│ • NumPy     │  │ • No DevTools    │
│ • Pandas    │  │                  │
│ • SciPy     │  │ Connects to:     │
│ • All deps  │  │ http://localhost │
│             │◄─┤ :8000 (auto)     │
│ Port: 8000  │  │                  │
│ (auto-find) │  │ Window: 1400x900 │
└──────┬──────┘  └───────┬──────────┘
       │                 │
       └────────┬────────┘
                │
       ┌────────▼──────────┐
       │  File System      │
       │  %APPDATA%\KSEB   │
       │  %USERPROFILE%\   │
       │  Documents\KSEB   │
       │  Projects         │
       └───────────────────┘
```

---

## Installation Strategy

### ❌ WRONG Approach (Don't do this)
```
User installs .exe
  → Installer checks for Python
  → Prompts user to install Python 3.11
  → Creates virtual environment
  → Runs pip install -r requirements.txt
  → Checks for Node.js
  → Runs npm install
  → Finally starts app
```

**Problems:**
- Requires Python and Node.js installed
- Long installation time (downloading packages)
- Can fail due to network issues
- Package version conflicts
- Poor user experience

### ✅ CORRECT Approach (Recommended)
```
User downloads KSEB-Setup.exe (1.2GB)
  → Runs installer
  → Extracts pre-bundled executables
  → Creates shortcuts
  → Done in 2 minutes!
  → User clicks shortcut → App runs instantly
```

**Advantages:**
- ✅ No Python/Node.js required
- ✅ No internet needed
- ✅ No pip/npm install at runtime
- ✅ All dependencies pre-bundled
- ✅ Works on clean Windows machines
- ✅ Professional user experience

---

## Build Process Breakdown

### Phase 1: Backend Bundling (PyInstaller)

**Goal:** Create standalone `backend.exe` with embedded Python runtime

**Steps:**
1. Install PyInstaller on development machine
2. Create PyInstaller spec file
3. Configure hidden imports for scientific packages
4. Embed Excel templates as data files
5. Build single-file executable
6. Test on clean Windows VM

**Output:**
- `dist/backend.exe` (~500MB-800MB)
- Contains: Python 3.11, FastAPI, PyPSA, numpy, scipy, pandas, matplotlib, all pip packages

**Key Configuration:**
```python
# pyinstaller.spec
a = Analysis(
    ['backend_fastapi/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend_fastapi/input', 'input'),  # Excel templates
    ],
    hiddenimports=[
        'pypsa',
        'netCDF4',
        'numpy',
        'scipy',
        'pandas',
        'sklearn',
        'statsmodels',
        'matplotlib',
        'seaborn',
        'plotly',
        'openpyxl',
        'xlsxwriter',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    console=False,  # No console window
    icon='icon.ico'
)
```

### Phase 2: Frontend Bundling (Electron + Vite)

**Goal:** Create standalone `frontend.exe` with embedded Chromium + Node.js

**Steps:**
1. Build React app with Vite (`npm run build`)
2. Create Electron main process
3. Configure Electron builder
4. Package with electron-builder
5. Test executable

**Output:**
- `dist/frontend.exe` (~200MB-400MB)
- Contains: Chromium, Node.js, React production build

**Key Files:**

**`frontend/electron-main.js`:**
```javascript
const { app, BrowserWindow } = require('electron');
const path = require('path');
const axios = require('axios');

let mainWindow;

// Wait for backend to start
async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await axios.get('http://localhost:8000/health', { timeout: 1000 });
      return true;
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  return false;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    icon: path.join(__dirname, 'icon.ico')
  });

  // Load production build
  mainWindow.loadFile(path.join(__dirname, 'dist/index.html'));

  // Disable DevTools in production
  mainWindow.webContents.on('devtools-opened', () => {
    mainWindow.webContents.closeDevTools();
  });
}

app.on('ready', async () => {
  console.log('Waiting for backend...');
  const ready = await waitForBackend();

  if (ready) {
    createWindow();
  } else {
    console.error('Backend failed to start');
    app.quit();
  }
});
```

**`frontend/package.json` (build section):**
```json
{
  "name": "kseb-frontend",
  "version": "1.0.0",
  "main": "electron-main.js",
  "scripts": {
    "build": "vite build",
    "electron:build": "npm run build && electron-builder"
  },
  "build": {
    "appId": "com.kseb.analytics",
    "productName": "KSEB Energy Analytics",
    "directories": {
      "output": "dist-electron"
    },
    "files": [
      "dist/**/*",
      "electron-main.js",
      "icon.ico"
    ],
    "win": {
      "target": "nsis",
      "icon": "icon.ico"
    }
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.9.1"
  }
}
```

### Phase 3: Launcher Script

**Goal:** Single entry point that orchestrates both executables

**`KSEB.exe` (compiled from launcher.py):**
```python
import subprocess
import time
import sys
import os
from pathlib import Path
import requests

def get_app_dir():
    """Get application directory (handles both dev and bundled)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def find_free_port(start=8000, end=9000):
    """Find available port for backend."""
    import socket
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available ports")

def start_backend():
    """Start backend.exe in background."""
    app_dir = get_app_dir()
    backend_exe = app_dir / "backend.exe"

    if not backend_exe.exists():
        print(f"Error: backend.exe not found at {backend_exe}")
        sys.exit(1)

    # Start backend as subprocess (no console window)
    process = subprocess.Popen(
        [str(backend_exe)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    return process

def wait_for_backend(timeout=30):
    """Wait for backend to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get('http://localhost:8000/health', timeout=1)
            if response.status_code == 200:
                print("Backend is ready!")
                return True
        except:
            time.sleep(1)
    return False

def start_frontend():
    """Start frontend.exe."""
    app_dir = get_app_dir()
    frontend_exe = app_dir / "frontend.exe"

    if not frontend_exe.exists():
        print(f"Error: frontend.exe not found at {frontend_exe}")
        sys.exit(1)

    # Start frontend (this will show the window)
    subprocess.run([str(frontend_exe)])

def main():
    print("Starting KSEB Energy Analytics...")

    # Start backend
    backend_process = start_backend()

    # Wait for backend to be ready
    if not wait_for_backend():
        print("Error: Backend failed to start")
        backend_process.kill()
        sys.exit(1)

    # Start frontend (blocking - keeps running)
    start_frontend()

    # Cleanup when frontend closes
    backend_process.terminate()
    backend_process.wait()
    print("Application closed")

if __name__ == "__main__":
    main()
```

### Phase 4: Windows Installer (NSIS)

**Goal:** Create professional installer with shortcuts

**`installer.nsi`:**
```nsis
!include "MUI2.nsh"

Name "KSEB Energy Analytics"
OutFile "KSEB-Setup.exe"
InstallDir "$PROGRAMFILES\KSEB Energy Analytics"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"

  ; Copy all executables
  File "dist\KSEB.exe"
  File "dist\backend.exe"
  File "dist\frontend.exe"

  ; Create data directories
  CreateDirectory "$APPDATA\KSEB Energy Analytics"
  CreateDirectory "$DOCUMENTS\KSEB Projects"

  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\KSEB Energy Analytics"
  CreateShortcut "$SMPROGRAMS\KSEB Energy Analytics\KSEB.lnk" "$INSTDIR\KSEB.exe"
  CreateShortcut "$DESKTOP\KSEB Energy Analytics.lnk" "$INSTDIR\KSEB.exe"

  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\KSEB Energy Analytics\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\KSEB.exe"
  Delete "$INSTDIR\backend.exe"
  Delete "$INSTDIR\frontend.exe"
  Delete "$INSTDIR\Uninstall.exe"

  RMDir "$INSTDIR"
  RMDir /r "$SMPROGRAMS\KSEB Energy Analytics"
  Delete "$DESKTOP\KSEB Energy Analytics.lnk"
SectionEnd
```

---

## Dependency Strategy

### ❌ WRONG: Runtime Installation
```
# DON'T DO THIS in your installer
pip install -r requirements.txt
npm install
```

### ✅ CORRECT: Pre-bundled Approach

**Backend (PyInstaller):**
```bash
# On development machine (one-time build)
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile backend_fastapi/main.py
# Result: All pip packages embedded in backend.exe
```

**Frontend (Electron Builder):**
```bash
# On development machine (one-time build)
cd frontend
npm install
npm run build  # Creates dist/ folder
npm run electron:build  # Creates frontend.exe with embedded Node.js
# Result: All npm packages embedded in frontend.exe
```

**End User Experience:**
```
User downloads: KSEB-Setup.exe (1.2GB)
User runs installer
User clicks shortcut
→ App runs immediately (NO pip/npm install)
```

---

## Key Technical Considerations

### 1. Path Handling
**Good News:** Your code already uses `pathlib.Path` (cross-platform!)

**Action Needed:**
- Audit all route files for hardcoded "/" separators
- Use Windows-appropriate directories:
  - `%APPDATA%\KSEB Energy Analytics` for app data
  - `%USERPROFILE%\Documents\KSEB Projects` for user projects

### 2. Port Binding
**Issue:** Ports 8000/3000 might be in use

**Solution:** Auto-detect available ports
```python
def find_free_port(start=8000, end=9000):
    import socket
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
```

### 3. Real-time Streaming (SSE)
**Status:** Already implemented with 15-second keep-alive
**Action:** Test on Windows (socket behavior differs)

### 4. Excel Template Embedding
**Solution:** Use PyInstaller's `datas` to embed templates
```python
datas=[
    ('backend_fastapi/input/input_demand_file.xlsx', 'input'),
    ('backend_fastapi/input/load_curve_template.xlsx', 'input'),
    ('backend_fastapi/input/pypsa_input_template.xlsx', 'input'),
]
```

### 5. Scientific Package Compatibility
**Status:** All packages have Windows pre-built wheels
- numpy, scipy, pandas: Official Windows builds
- PyPSA: Windows compatible
- netCDF4: Pre-built Windows wheels available

**Action:** Test on Windows VM before bundling

---

## File Size Estimates

| Component | Uncompressed | Compressed (UPX) |
|-----------|-------------|------------------|
| Backend (PyInstaller) | ~800MB | ~500MB |
| Frontend (Electron) | ~400MB | ~200MB |
| Launcher | ~15MB | ~10MB |
| Templates | ~8MB | ~8MB |
| **Total Installer** | **~1.2GB** | **~720MB** |

---

## Build Timeline Estimate

| Phase | Duration | Effort |
|-------|----------|--------|
| 1. Backend PyInstaller setup | 1 week | Fix paths, test dependencies |
| 2. Frontend Electron wrapper | 1 week | Create electron-main.js, test |
| 3. Integration & launcher | 1 week | Auto-start, port detection |
| 4. Windows installer (NSIS) | 1 week | Create installer, test |
| 5. Testing & debugging | 2-3 weeks | Test on clean Windows VMs |
| 6. Optimization | 1 week | Reduce size, improve startup |
| **Total** | **7-9 weeks** | **Single developer** |

---

## Testing Checklist

### Pre-Build Testing
- [ ] All 105 API endpoints work on Windows
- [ ] PyPSA solver runs on Windows
- [ ] Excel file operations work
- [ ] File paths use backslashes correctly
- [ ] SSE streaming works on Windows sockets

### Post-Build Testing
- [ ] backend.exe runs standalone (no Python needed)
- [ ] frontend.exe runs standalone (no Node.js needed)
- [ ] Launcher starts both correctly
- [ ] Port auto-detection works
- [ ] Backend auto-starts when frontend launches
- [ ] All features functional (forecasting, PyPSA, etc.)
- [ ] Large file handling (>100MB)
- [ ] Installer creates shortcuts
- [ ] Uninstaller removes all files
- [ ] Works on clean Windows 10/11 (no Python/Node.js)

### Edge Case Testing
- [ ] Ports 8000/3000 already in use
- [ ] Long file path names (Windows 260 char limit)
- [ ] Network drive project storage
- [ ] OneDrive/cloud storage projects
- [ ] Multiple instances running
- [ ] Admin vs non-admin privileges

---

## Final Deliverables

1. **KSEB-Setup.exe** (~720MB compressed)
   - Single installer for end users
   - Creates Start Menu shortcuts
   - Creates desktop shortcut
   - Works on clean Windows machines

2. **No External Requirements**
   - ✅ No Python installation needed
   - ✅ No Node.js installation needed
   - ✅ No pip/npm commands
   - ✅ No virtual environment
   - ✅ No internet connection for installation
   - ✅ All dependencies pre-bundled

3. **User Experience**
   - Download installer
   - Run installer (2 minutes)
   - Click desktop shortcut
   - App launches in 10-15 seconds
   - Works offline

---

## Comparison: Bundled vs Runtime Installation

| Aspect | ❌ Runtime Installation | ✅ Pre-bundled (Recommended) |
|--------|------------------------|------------------------------|
| User needs Python? | YES | NO |
| User needs Node.js? | YES | NO |
| Installation time | 15-30 minutes | 2-3 minutes |
| Internet required? | YES (pip/npm) | NO |
| Can fail? | YES (network, conflicts) | NO |
| File size | Small installer (~50MB) | Large installer (~720MB) |
| Professional? | NO | YES |
| User experience | Poor | Excellent |

---

## Recommendation Summary

✅ **Use Electron + PyInstaller approach**
✅ **Bundle ALL dependencies** (no runtime installation)
✅ **No Python/Node.js required** on user machines
✅ **No virtual environment** creation
✅ **Single installer** with professional UX
✅ **Works on clean Windows** machines out of the box

This approach ensures:
- Professional Windows application
- No dependency hell for users
- Fast, reliable installation
- Offline capability
- Enterprise-ready deployment

---

## Next Steps

1. Set up Windows development environment
2. Test all dependencies on Windows
3. Create PyInstaller spec file
4. Build and test backend.exe
5. Create Electron wrapper
6. Build and test frontend.exe
7. Create launcher script
8. Build NSIS installer
9. Test on clean Windows VMs
10. Deploy to users

**Estimated Timeline:** 7-9 weeks with single developer

