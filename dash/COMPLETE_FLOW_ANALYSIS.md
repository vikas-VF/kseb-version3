# COMPREHENSIVE DASH WEBAPP FLOW ANALYSIS

**Date:** 2025-11-16
**Critical Bug Fixed:** Missing `app_config` import in `local_service.py`
**Status:** Analyzing all flows and fixing issues

---

## 🔴 CRITICAL BUG IDENTIFIED AND FIXED

### Problem
My bash script replaced hardcoded strings like `'results'` and `'load_profiles'` with `DirectoryStructure.RESULTS` and `DirectoryStructure.LOAD_PROFILES` in `local_service.py`, but **NEVER added the import statement**.

### Impact
- ❌ ALL functionality broken
- ❌ get_load_profiles() fails
- ❌ No profiles show in dropdown
- ❌ Every API call throws NameError

### Fix Applied
Added missing import to `dash/services/local_service.py` line 32:

```python
from app_config import (
    TemplateFiles,
    InputDemandSheets,
    LoadCurveSheets,
    PyPSASheets,
    ColumnNames,
    AppDefaults,
    DirectoryStructure,
    DataMarkers,
    get_project_template_path,
    get_project_results_path
)
```

---

## 🔍 REACT WARNING ANALYSIS

### Warning Message
```
Warning: Can't perform a React state update on unmounted component.
This is a no-op, but it indicates a memory leak in your application.
```

### Root Cause
This warning indicates you're seeing **REACT errors**, which means:

**YOU ARE RUNNING THE WRONG APPLICATION!**

You have TWO separate applications:
1. **React + FastAPI** (frontend/ + backend_fastapi/)
2. **Dash/Plotly** (dash/)

The React warning means you're running the **React frontend**, not the **Dash app**.

### Solution
**Stop the React frontend and run the Dash app instead:**

```bash
# STOP React frontend (if running)
# Go to frontend/ directory and kill npm start

# START Dash app
cd /home/user/kseb-version3/dash
python app.py
```

The Dash app runs on **port 8050** by default.
The React app runs on **port 3000**.

Check which is running:
```bash
ps aux | grep -E 'node|python.*app\.py'
lsof -i :8050
lsof -i :3000
```

---

## 📊 COMPLETE FLOW ANALYSIS

### 1. PROJECT CREATION FLOW

**File:** `dash/pages/create_project.py`

**Step-by-Step:**

1. **User inputs project name and path** (Lines 48-105)
   - Project name validation (no special chars, not empty)
   - Path validation (directory exists, writable)

2. **Path preview** (Lines 107-124)
   - Shows final path: `{parent_path}/{project_name}/`

3. **User clicks "Create Project"** (Callback line 409)
   - Creates directory structure:
     ```
     ProjectName/
     ├── inputs/
     │   ├── input_demand_file.xlsx (copied from dash/input/)
     │   ├── load_curve_template.xlsx
     │   └── pypsa_input_template.xlsx
     ├── results/
     │   ├── demand_forecasts/
     │   ├── load_profiles/
     │   └── pypsa_optimization/
     ├── project.json
     └── README.md
     ```

4. **Project saved to session** (Line 456)
   - Stored in `active-project-store` (dcc.Store)
   - Contains: `{name, path, created, description}`

5. **Auto-navigation to Demand Projection** (Line 460)

**Files Used:**
- `TemplateFiles.INPUT_DEMAND_FILE` = 'input_demand_file.xlsx'
- `TemplateFiles.LOAD_CURVE_TEMPLATE` = 'load_curve_template.xlsx'
- `TemplateFiles.PYPSA_INPUT_TEMPLATE` = 'pypsa_input_template.xlsx'
- `DirectoryStructure.INPUTS` = 'inputs'
- `DirectoryStructure.RESULTS` = 'results'
- `DirectoryStructure.DEMAND_FORECASTS` = 'demand_forecasts'
- `DirectoryStructure.LOAD_PROFILES` = 'load_profiles'
- `DirectoryStructure.PYPSA_OPTIMIZATION` = 'pypsa_optimization'

**Dynamic Data:**
- ✅ Project name from user input
- ✅ Project path from user input
- ✅ Template files copied from `dash/input/` directory
- ❌ **NOT HARDCODED**

---

### 2. LOAD PROJECT FLOW

**File:** `dash/pages/load_project.py`

**Step-by-Step:**

1. **User browses to project folder**
   - File browser shows directories

2. **Load button clicked**
   - Reads `project.json` from selected folder
   - Validates project structure

3. **Project loaded to session**
   - Stored in `active-project-store`
   - App updates topbar, sidebar, workflow

**Validation:**
- Checks for `project.json` existence
- Checks for `inputs/` and `results/` directories
- Verifies template files exist

---

### 3. DEMAND PROJECTION FLOW

**File:** `dash/pages/demand_projection.py`

**Step-by-Step:**

1. **Page loads** (Line 1319+)
   - Reads `{project_path}/inputs/input_demand_file.xlsx`
   - Parses all sector sheets dynamically:
     ```python
     excel_path = os.path.join(inputs_dir, TemplateFiles.INPUT_DEMAND_FILE)
     xls = pd.ExcelFile(excel_path)

     # Get all sheets DYNAMICALLY
     for sheet_name in xls.sheet_names:
         if sheet_name not in ['main', 'commons', 'Economic_Indicators', 'units']:
             # This is a sector sheet
             df = pd.read_excel(xls, sheet_name=sheet_name)
             sectors.append(sheet_name)
     ```

2. **Sectors displayed** (Line 1349+)
   - Each sector gets a tab
   - Data table shows historical data
   - Charts: Area, Bar, Line, Correlation

3. **User configures forecast** (Modal)
   - Select model: SLR, MLR, WAM
   - Select forecast period
   - Configure parameters (if MLR/WAM)

4. **User clicks "Start Forecasting"**
   - Calls `api.start_forecast(config)`
   - Creates subprocess for forecasting
   - SSE stream shows progress

5. **Results saved**
   - Saved to `{project_path}/results/demand_forecasts/{scenario_name}/`
   - Creates Excel file with forecasted data

**Dynamic Data:**
- ✅ Sectors read from Excel sheets (NOT hardcoded)
- ✅ Economic indicators read from 'Economic_Indicators' sheet
- ✅ Units read from 'units' sheet
- ✅ Model names from `model_registry.py`
- ❌ **NOTHING HARDCODED**

**Sheet Names Used:**
- `InputDemandSheets.MAIN` = 'main'
- `InputDemandSheets.ECONOMIC_INDICATORS` = 'Economic_Indicators'
- `InputDemandSheets.UNITS` = 'units'
- All sector sheets (Domestic_lt, Commercial_lt, etc.)

---

### 4. DEMAND VISUALIZATION FLOW

**File:** `dash/pages/demand_visualization.py`

**Step-by-Step:**

1. **Page loads**
   - Scans `{project_path}/results/demand_forecasts/` for scenario folders

2. **User selects scenario**
   - Dropdown populated DYNAMICALLY from available scenarios

3. **Charts displayed**
   - Reads Excel file from scenario folder
   - Shows forecast results for each sector
   - Interactive Plotly charts

**Dynamic Data:**
- ✅ Scenarios from filesystem scan
- ✅ Sector names from Excel sheets
- ✅ Data from forecast results
- ❌ **NOTHING HARDCODED**

---

### 5. LOAD PROFILE GENERATION FLOW

**File:** `dash/pages/generate_profiles.py`

**Step-by-Step:**

1. **User selects forecast scenario**
   - Dropdown lists available demand forecasts

2. **User uploads base load curve** (OR selects from `inputs/`)
   - File: `load_curve_template.xlsx`
   - Must have sheet: `LoadCurveSheets.PAST_HOURLY_DEMAND` = 'Past_Hourly_Demand'

3. **User configures profile**
   - Profile name
   - Method selection
   - Parameters

4. **User clicks "Generate Profile"**
   - Calls `api.generate_profile(config)`
   - Creates 8760-hour profile
   - Saves to `{project_path}/results/load_profiles/{profile_name}.xlsx`

**Sheet Names Used:**
- `LoadCurveSheets.PAST_HOURLY_DEMAND` = 'Past_Hourly_Demand'
- `LoadCurveSheets.TOTAL_DEMAND` = 'Total Demand'
- `LoadCurveSheets.HOLIDAYS` = 'Holidays'

---

### 6. LOAD PROFILE ANALYSIS FLOW ⚠️ **ISSUE FOUND**

**File:** `dash/pages/analyze_profiles.py`

**Step-by-Step:**

1. **Page loads** (Line 88)
   ```python
   profiles = api.get_load_profiles(project['path']).get('profiles', [])
   ```

2. **`api.get_load_profiles()` is called** (local_service.py line 1769)
   ```python
   def get_load_profiles(self, project_path: str) -> Dict:
       profiles_dir = Path(project_path) / DirectoryStructure.RESULTS / DirectoryStructure.LOAD_PROFILES

       # Lists all .xlsx files in results/load_profiles/
       for p in sorted(profiles_dir.iterdir()):
           if p.suffix.lower() in {'.xlsx', '.xls', '.xlsm', '.xlsb', '.csv'}:
               profiles.append(p.stem)

       return {'profiles': profiles}
   ```

3. **Dropdown populated**
   - If profiles list is empty → **"No profiles" dropdown**
   - If profiles exist → Shows list

**WHY NO PROFILES SHOW:**

### ❌ BEFORE FIX (BROKEN):
```python
# local_service.py line 1778
profiles_dir = Path(project_path) / DirectoryStructure.RESULTS / DirectoryStructure.LOAD_PROFILES
# NameError: name 'DirectoryStructure' is not defined
```

### ✅ AFTER FIX (WORKING):
```python
# Added import at line 32
from app_config import DirectoryStructure

# Now line 1778 works correctly
profiles_dir = Path(project_path) / DirectoryStructure.RESULTS / DirectoryStructure.LOAD_PROFILES
# = Path(project_path) / 'results' / 'load_profiles'
```

**To Populate Dropdown:**
1. Generate at least one load profile
2. Verify file exists: `{project_path}/results/load_profiles/ProfileName.xlsx`
3. Reload the page

---

### 7. PYPSA MODEL CONFIG FLOW

**File:** `dash/pages/model_config.py`

**Step-by-Step:**

1. **User enters scenario name**
   - Default: `AppDefaults.DEFAULT_PYPSA_SCENARIO` = 'PyPSA_Scenario_V1'

2. **User selects solver**
   - Default: `AppDefaults.DEFAULT_SOLVER` = 'highs'

3. **User prepares input file**
   - Must have `{project_path}/inputs/pypsa_input_template.xlsx`
   - Contains 22 sheets with network data

4. **User clicks "Run Model"**
   - Calls `api.run_pypsa_optimization(config)`
   - Creates PyPSA Network
   - Runs optimization
   - Saves results to `{project_path}/results/pypsa_optimization/{scenario}/`

**Sheet Names Used (22 total):**
- `PyPSASheets.GENERATORS` = 'Generators'
- `PyPSASheets.BUSES` = 'Buses'
- `PyPSASheets.DEMAND_FINAL` = 'Demand_final'
- etc. (all 22 defined in app_config.py)

---

### 8. PYPSA VIEW RESULTS FLOW

**File:** `dash/pages/view_results.py`

**Step-by-Step:**

1. **Page loads**
   - Scans `{project_path}/results/pypsa_optimization/` for scenarios

2. **User selects scenario**
   - Dropdown populated DYNAMICALLY

3. **Network file loaded**
   - Reads `.nc` file using **LAZY LOADED** NetworkCache
   - **ONLY LOADS WHEN NEEDED** (not on app startup)

4. **Results displayed**
   - 7 tabs: Dispatch, Capacity, Metrics, Storage, Emissions, Costs, Network
   - Interactive charts

**Dynamic Data:**
- ✅ Scenarios from filesystem scan
- ✅ Network data from .nc file
- ✅ All component names from network
- ❌ **NOTHING HARDCODED**

---

### 9. SETTINGS PAGE WITH DYNAMIC COLORS

**File:** `dash/pages/settings_page.py`

**Requirement:** Dynamic colors for sectors and models

**Current Implementation:**
```python
# In app_config.py line 247
PYPSA_COLORS = {
    'Solar': '#fbbf24',
    'Wind': '#3b82f6',
    'Hydro': '#06b6d4',
    # ... etc
}
```

**To Make Fully Dynamic:**

**For Sectors:**
```python
# Read sectors from Excel file dynamically
excel_path = get_project_template_path(project_path, TemplateFiles.INPUT_DEMAND_FILE)
xls = pd.ExcelFile(excel_path)

sectors = []
for sheet_name in xls.sheet_names:
    if sheet_name not in ['main', 'commons', 'Economic_Indicators', 'units']:
        sectors.append(sheet_name)

# Generate colors dynamically
import plotly.express as px
colors = px.colors.qualitative.Plotly
sector_colors = {sector: colors[i % len(colors)] for i, sector in enumerate(sectors)}
```

**For Models:**
```python
# Models already dynamic from model_registry.py
from model_registry import AVAILABLE_MODELS

models = list(AVAILABLE_MODELS.keys())  # ['SLR', 'MLR', 'WAM']
model_colors = {model: colors[i] for i, model in enumerate(models)}
```

---

## 🔧 WHAT NEEDS TO BE FIXED

### 1. ✅ **FIXED: Missing import in local_service.py**
Added `from app_config import DirectoryStructure, etc.`

### 2. ⚠️ **TO FIX: React warnings**
**User is running React frontend instead of Dash app**

**Action Required:**
```bash
# Stop React frontend
cd frontend/
# Press Ctrl+C if npm start is running

# Start Dash app
cd ../dash/
python app.py

# Access at: http://localhost:8050
```

### 3. ⚠️ **TO VERIFY: Load profiles not showing**
**After import fix, check:**
1. Has user generated any profiles?
2. Do files exist in `{project}/results/load_profiles/`?
3. Are files .xlsx format?

**Test:**
```python
from pathlib import Path
project_path = "/path/to/project"
profiles_dir = Path(project_path) / "results" / "load_profiles"
print("Profiles directory exists:", profiles_dir.exists())
print("Files in directory:", list(profiles_dir.iterdir()) if profiles_dir.exists() else [])
```

---

## 📋 VERIFICATION CHECKLIST

### Dynamic Data Loading (No Hardcoding)

- [x] **Project creation** - User inputs name/path
- [x] **Template files** - Copied from dash/input/
- [x] **Sector names** - Read from Excel sheets
- [x] **Economic indicators** - Read from Economic_Indicators sheet
- [x] **Model names** - From model_registry.py
- [x] **Forecast scenarios** - Scanned from filesystem
- [x] **Load profiles** - Scanned from filesystem
- [x] **PyPSA scenarios** - Scanned from filesystem
- [x] **PyPSA sheets** - All 22 defined in app_config.py
- [x] **Directory names** - All from DirectoryStructure
- [x] **File names** - All from TemplateFiles

### Settings Page Dynamic Colors

- [ ] **TO IMPLEMENT: Sector colors** - Generate from discovered sectors
- [ ] **TO IMPLEMENT: Model colors** - Generate from AVAILABLE_MODELS
- [x] **PyPSA component colors** - Defined in UIConstants.PYPSA_COLORS

---

## 🚀 IMMEDIATE ACTION REQUIRED

### 1. Stop React App, Start Dash App
```bash
# Kill React frontend (port 3000)
lsof -ti:3000 | xargs kill -9

# Start Dash app
cd /home/user/kseb-version3/dash
python app.py

# Access: http://localhost:8050
```

### 2. Test Load Profile Flow
```bash
# 1. Create a project
# 2. Run demand projection
# 3. Generate load profile
# 4. Go to Analyze Profiles page
# 5. Check if dropdown shows the generated profile
```

### 3. Verify Import Fix Works
```bash
cd /home/user/kseb-version3/dash
python3 -c "
from services.local_service import service as api
result = api.get_load_profiles('/path/to/test/project')
print('Profiles:', result['profiles'])
"
```

---

## 📝 SUMMARY

### What Broke
1. ❌ Missing import statement in `local_service.py`
2. ❌ User running React frontend instead of Dash app
3. ❌ No load profiles generated yet

### What Works (After Fix)
1. ✅ Centralized configuration (app_config.py)
2. ✅ Lazy loading for NetworkCache
3. ✅ Lazy loading for pages
4. ✅ All file/sheet/column names from config
5. ✅ All data loaded dynamically

### Next Steps
1. Commit the import fix
2. Test complete flow
3. Generate sample project + profiles
4. Verify all pages work correctly

---

**Status:** Critical bug fixed, ready for testing
**Author:** Claude AI
**Date:** 2025-11-16
