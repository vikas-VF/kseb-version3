# Dash Webapp - Issues Found & Fixes Applied

**Date:** 2025-11-12
**Status:** 1 Critical Issue Fixed, Several Methods Need Implementation

---

## ✅ Issue #1: FIXED - dash.register_page() Error

### Problem
```
dash.exceptions.PageError: `dash.register_page()` must be called after app instantiation
```

**Root Cause:**
- `model_config.py` and `view_results.py` had `dash.register_page()` calls
- Our app uses **manual routing** (via callbacks in app.py), not Dash Pages framework
- These calls fail because they execute at import time before app instantiation

### Solution Applied
**Files Modified:**
- `dash/pages/model_config.py` (line 24)
- `dash/pages/view_results.py` (line 30)

**Change:**
```python
# Before:
dash.register_page(__name__, path='/pypsa/model-config', title='PyPSA Model Configuration')

# After (removed):
# Note: This page uses manual routing in app.py, not dash.register_page()
```

**Status:** ✅ **FIXED** (Committed: 94a019b)

---

## ⚠️ Issue #2: INCOMPLETE - Missing Methods in local_service.py

### Problem
When we converted from `api_client.py` (HTTP-based) to `local_service.py` (direct execution), we only implemented **26 out of 51 methods**.

**Missing:** 25 methods (49% incomplete)

### Critical Missing Methods (Actually Used in Pages)

#### **PyPSA Analysis Methods** (Used in view_results.py)
```python
❌ get_pypsa_networks(project_path, scenario_name)
❌ get_network_info(project_path, scenario_name, network_file)
❌ get_pypsa_buses(project_path, scenario_name, network_file)
❌ get_pypsa_generators(project_path, scenario_name, network_file)
❌ get_pypsa_storage_units(project_path, scenario_name, network_file)
❌ get_pypsa_lines(project_path, scenario_name, network_file)
❌ get_pypsa_loads(project_path, scenario_name, network_file)
❌ get_component_details(project_path, scenario_name, network_file, component_type)
❌ get_comprehensive_analysis(project_path, scenario_name, network_file)
❌ generate_pypsa_plot(config)
❌ get_available_years(project_path, scenario_name, network_file)
❌ get_plot_availability(project_path, scenario_name, network_file)
```

**Impact:** PyPSA Results Viewer (7 tabs) will **FAIL** when trying to load network data.

#### **Load Profile Analysis Methods** (Used in analyze_profiles.py)
```python
❌ get_analysis_data(project_path, profile_name)
❌ get_profile_years(project_path, profile_name)
❌ get_load_duration_curve(project_path, profile_name, fiscal_year)
❌ get_full_load_profile(project_path, profile_name, fiscal_year, month, season)
```

**Impact:** Load Profile Analysis (6 tabs) will **FAIL** when loading profile data.

#### **Other Missing Methods**
```python
❌ get_available_base_years(project_path)
❌ get_available_scenarios_for_profiles(project_path)
❌ check_profile_exists(project_path, profile_name)
❌ check_consolidated_exists(project_path, scenario_name)
❌ generate_consolidated(project_path, scenario_name)
❌ save_consolidated(project_path, scenario_name, data)
❌ get_correlation(project_path, sector)
❌ get_correlation_matrix(project_path, sector)
❌ get_scenario_meta(project_path, scenario_name)
❌ get_scenario_models(project_path, scenario_name)
❌ get_sector_forecast(project_path, scenario_name, sector_name)
❌ save_model_config(project_path, config)
❌ stop_pypsa_model()
❌ start_forecast(config)  # Different from start_demand_forecast
```

### Methods That Can Be Skipped
```python
✓ _handle_response()  # HTTP-specific, not needed
✓ get_forecast_progress_url()  # SSE URL, not needed (synchronous now)
✓ get_generation_status_url()  # SSE URL, not needed
✓ get_pypsa_progress_url()  # SSE URL, not needed
```

---

## 🔍 Analysis: What Will Break

### ✅ **Working Pages** (Basic functionality implemented)
1. **Home** - Works ✓
2. **Create Project** - Works ✓ (minor TODO for template copying)
3. **Load Project** - Works ✓
4. **Demand Projection** - Works ✓ (uses implemented methods)
5. **Demand Visualization** - Partially works ⚠️ (some features missing)
6. **Settings** - Works ✓

### ⚠️ **Partially Working Pages** (Some methods missing)
1. **Demand Visualization**
   - Missing: `get_available_models()`, `get_sector_forecast()`
   - Impact: Can't show model-specific forecasts, only consolidated

2. **Generate Profiles**
   - Missing: `check_profile_exists()`, `get_available_scenarios_for_profiles()`
   - Impact: Can't validate profile names, can't list scenarios

### ❌ **Broken Pages** (Critical methods missing)
1. **Analyze Profiles**
   - Missing: `get_analysis_data()`, `get_profile_years()`, `get_load_duration_curve()`, `get_full_load_profile()`
   - Impact: **ALL 6 TABS WILL FAIL** - Can't load any profile data

2. **Model Config (PyPSA)**
   - Missing: `save_model_config()`, `get_pypsa_networks()`
   - Impact: Can't save config, can't list available networks

3. **View Results (PyPSA)**
   - Missing: All PyPSA analysis methods listed above
   - Impact: **ALL 7 TABS WILL FAIL** - Can't load network data or generate plots

---

## 🛠️ Solutions

### Option 1: Implement Missing Methods (Comprehensive)
**Effort:** Medium-High (3-5 hours)
**Result:** Full feature parity with original app

Implement all 25 missing methods in `local_service.py` by:
1. Reading data from file system (Excel, CSV, NetCDF)
2. Processing with pandas/pypsa
3. Returning structured data

**Pros:**
- ✅ All features work
- ✅ Complete functionality
- ✅ No regression from original app

**Cons:**
- ⏱️ Time-consuming
- 🔧 More code to maintain

### Option 2: Simplify Pages (Quick Fix)
**Effort:** Low (1-2 hours)
**Result:** Working app with reduced features

Modify pages to work with available methods:
1. **Analyze Profiles:** Directly read CSV files instead of using API methods
2. **View Results:** Directly load NetCDF using pypsa.Network.import_from_netcdf()
3. **Demand Visualization:** Remove model-specific views, keep consolidated only

**Pros:**
- ⚡ Fast to implement
- 🎯 Still functional
- 📉 Less code

**Cons:**
- ❌ Some features lost
- ⚠️ Potential UX issues

### Option 3: Hybrid Approach (Recommended)
**Effort:** Medium (2-3 hours)
**Result:** Core features work, advanced features simplified

Implement only **critical** methods (10-12 methods):
- ✅ `get_pypsa_networks()` - List available networks
- ✅ `get_network_info()` - Get network metadata
- ✅ `get_analysis_data()` - Load profile analysis data
- ✅ `get_profile_years()` - List years in profile
- ✅ `get_load_duration_curve()` - Load duration curve
- ✅ `get_full_load_profile()` - Full profile data
- ✅ `get_pypsa_buses/generators/lines/loads()` - Component data
- ✅ `get_comprehensive_analysis()` - Network analysis

Skip optional methods:
- ⏭️ `generate_pypsa_plot()` - Generate plots in callbacks instead
- ⏭️ `get_component_details()` - Use comprehensive_analysis
- ⏭️ `save_model_config()` - Save directly in callback

**Pros:**
- ✅ Core features work
- ⚡ Reasonable effort
- 📊 Good balance

**Cons:**
- 🎨 Some polish features missing
- 🔄 May need refinement

---

## 📝 Recommended Action Plan

### Phase 1: Implement Critical PyPSA Methods (1-2 hours)
**Priority:** HIGH
**Impact:** Enables PyPSA Results Viewer

```python
# In local_service.py

def get_pypsa_networks(self, project_path: str, scenario_name: str) -> Dict:
    """List .nc network files in scenario folder"""
    pypsa_dir = os.path.join(project_path, 'results', 'pypsa_optimization', scenario_name)
    if not os.path.exists(pypsa_dir):
        return {'networks': []}
    networks = [f for f in os.listdir(pypsa_dir) if f.endswith('.nc')]
    return {'networks': networks}

def get_network_info(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
    """Load network and extract metadata"""
    import pypsa
    network_path = os.path.join(project_path, 'results', 'pypsa_optimization', scenario_name, network_file)
    network = pypsa.Network()
    network.import_from_netcdf(network_path)

    return {
        'buses': len(network.buses),
        'generators': len(network.generators),
        'lines': len(network.lines),
        'loads': len(network.loads),
        'snapshots': len(network.snapshots),
        'multi_period': len(network.investment_periods) > 0 if hasattr(network, 'investment_periods') else False
    }

def get_pypsa_generators(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
    """Get all generators from network"""
    import pypsa
    network_path = os.path.join(project_path, 'results', 'pypsa_optimization', scenario_name, network_file)
    network = pypsa.Network()
    network.import_from_netcdf(network_path)

    return {
        'generators': network.generators.to_dict('records')
    }

# Similar for: get_pypsa_buses, get_pypsa_lines, get_pypsa_loads, get_pypsa_storage_units
```

### Phase 2: Implement Load Profile Analysis Methods (1 hour)
**Priority:** HIGH
**Impact:** Enables Load Profile Analyzer

```python
def get_analysis_data(self, project_path: str, profile_name: str) -> Dict:
    """Get monthly/seasonal analysis data"""
    profile_dir = os.path.join(project_path, 'results', 'load_profiles', profile_name)
    stats_file = os.path.join(profile_dir, 'statistics.json')

    if os.path.exists(stats_file):
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        return stats

    # If stats don't exist, calculate from CSV
    csv_file = os.path.join(profile_dir, 'hourly_profile.csv')
    df = pd.read_csv(csv_file, parse_dates=['Timestamp'])

    # Calculate monthly stats
    monthly = df.groupby(df['Timestamp'].dt.month).agg({
        'Load_MW': ['mean', 'max', 'min', 'sum']
    })

    return {
        'monthly': monthly.to_dict(),
        # Add seasonal, day-type analysis
    }

def get_load_duration_curve(self, project_path: str, profile_name: str, fiscal_year: str) -> Dict:
    """Get load duration curve data"""
    csv_file = os.path.join(project_path, 'results', 'load_profiles', profile_name, 'hourly_profile.csv')
    df = pd.read_csv(csv_file)

    # Filter by fiscal year if specified
    if fiscal_year:
        df = df[df['FiscalYear'] == fiscal_year]

    # Sort loads descending
    loads_sorted = df['Load_MW'].sort_values(ascending=False).values
    hours = np.arange(len(loads_sorted))

    return {
        'hours': hours.tolist(),
        'loads': loads_sorted.tolist()
    }
```

### Phase 3: Test & Refine (30 mins)
1. Test PyPSA Results Viewer with real network files
2. Test Load Profile Analyzer with real profiles
3. Fix any edge cases

---

## 🎯 Current Status Summary

### What's Working ✅
- App starts without errors
- Basic navigation
- Project creation/loading
- Demand forecasting (execution)
- Settings

### What's Broken ❌
- Analyze Profiles (6 tabs) - **CRITICAL**
- View Results PyPSA (7 tabs) - **CRITICAL**
- Some demand visualization features

### What's Missing ⚠️
- 25 methods in local_service.py (49% incomplete)
- Template file copying (minor)
- Correlation top pairs extraction (minor)

---

## 📊 Effort Estimate

| Task | Effort | Priority | Impact |
|------|--------|----------|--------|
| Implement PyPSA methods | 1-2 hrs | HIGH | Enables 7-tab results viewer |
| Implement profile methods | 1 hr | HIGH | Enables 6-tab analyzer |
| Implement optional methods | 1 hr | MEDIUM | Polish features |
| Testing & refinement | 30 min | HIGH | Quality assurance |
| **TOTAL** | **3.5-4.5 hrs** | - | **Full functionality** |

---

## 🚀 Next Steps

**Immediate:**
1. ✅ Fixed `dash.register_page()` error (DONE)
2. ⚠️ Implement critical missing methods (TODO)

**Recommended Priority:**
1. **HIGH:** Implement PyPSA network methods (1-2 hrs)
2. **HIGH:** Implement profile analysis methods (1 hr)
3. **MEDIUM:** Test with real data (30 min)
4. **LOW:** Implement optional methods (1 hr)

**Alternative (Quick Path):**
- Modify pages to read files directly
- Skip API layer entirely
- Trade features for speed

---

## 📋 Decision Point

**User Choice Needed:**

**A)** Implement all missing methods (3.5-4.5 hrs) → Full functionality ✨

**B)** Simplify pages to work without methods (1-2 hrs) → Reduced features ⚡

**C)** Hybrid: Implement only critical methods (2-3 hrs) → Best balance ⚖️

**My Recommendation:** **Option C (Hybrid)** - Implement the 10-12 critical methods that enable the major features (PyPSA Results, Profile Analysis), skip the polish methods. This gives you a fully functional app in reasonable time.

---

**Current Branch:** `claude/dash-webapp-migration-analysis-011CV3YyhxwheFCCMnA5wZp3`
**Last Commit:** `94a019b` - Fixed dash.register_page error
**Status:** App starts successfully, core features work, advanced features need method implementation
