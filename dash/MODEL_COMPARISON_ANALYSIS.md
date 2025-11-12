# Models Directory Comparison Report

## Summary
The Dash and Backend FastAPI have **significantly different model implementations**. The backend models are mostly **commented out/stubbed**, while the Dash models have active code.

---

## 1. FILE INVENTORY COMPARISON

### Dash Models (`/dash/models/`)
```
8 Python files (1 empty __init__.py):
- __init__.py (empty)
- forecasting.py (589 lines - ACTIVE)
- load_profile_generation.py (2,324 lines - ACTIVE)
- network_cache.py (294 lines - ACTIVE)
- network_cache_optimized.py (330 lines - ACTIVE, UNIQUE TO DASH)
- pypsa_analyzer.py (2,850 lines - ACTIVE)
- pypsa_model_executor.py (1,375 lines - ACTIVE)
- pypsa_visualizer.py (1,257 lines - ACTIVE)
- validation_models.py (115 lines - ACTIVE)
```

### Backend FastAPI Models (`/backend_fastapi/models/`)
```
7 Python files:
- forecasting.py (589 lines - COMMENTED OUT/STUBBED)
- load_profile_generation.py (3,556 lines - COMMENTED OUT/STUBBED)
- network_cache.py (294 lines - ACTIVE)
- pypsa_analyzer.py (2,850 lines - ACTIVE)
- pypsa_model_executor.py (3,257 lines - COMMENTED OUT/STUBBED)
- pypsa_visualizer.py (1,257 lines - ACTIVE)
- validation_models.py (115 lines - ACTIVE)
```

---

## 2. CRITICAL DIFFERENCE: COMMENTED OUT CODE

### Backend Files Status
Both `/backend_fastapi/models/forecasting.py` and `/backend_fastapi/models/load_profile_generation.py` are **100% commented out**:
```python
# """
# Complete Advanced Load Profile Generation System
# Updated for New Unified JSON Configuration Format
# """
# import pandas as pd
# import numpy as np
# ... (entire file commented)
```

### Implications
- The backend API endpoints try to spawn these as Python subprocesses
- Since the code is commented out, those subprocesses will fail or do nothing
- This is a **critical issue** blocking production use

---

## 3. FILE SIZE & CONTENT ANALYSIS

| File | Dash | Backend | Status | Notes |
|------|------|---------|--------|-------|
| forecasting.py | 589 | 589 | SAME SIZE | Both have same structure, but backend is commented |
| load_profile_generation.py | 2,324 | 3,556 | DIFFERENT | Backend is 1,232 lines longer (but ALL commented) |
| network_cache.py | 294 | 294 | SAME | Both active and identical |
| network_cache_optimized.py | 330 | N/A | DASH ONLY | Optimized caching with LZ4 compression (100x faster) |
| pypsa_analyzer.py | 2,850 | 2,850 | SAME | Both active and identical |
| pypsa_model_executor.py | 1,375 | 3,257 | DIFFERENT | Backend is 1,882 lines longer (mostly commented) |
| pypsa_visualizer.py | 1,257 | 1,257 | SAME | Both active and identical |
| validation_models.py | 115 | 115 | SAME | Both active and identical |

---

## 4. MODELS BY FUNCTIONALITY

### Demand Forecasting
**Files**: `forecasting.py`
- **Dash**: ACTIVE (589 lines)
  - Functions: ProgressTracker, prepare_ml_data, weighted_average_forecast, load_config
  - Supports: MLR (Multiple Linear Regression), WAM (Weighted Average Method)
- **Backend**: COMMENTED OUT (cannot execute)
- **API Client Method**: `api.start_forecast(config)` → `/project/forecast`

### Load Profile Generation  
**Files**: `load_profile_generation.py`
- **Dash**: ACTIVE (2,324 lines)
  - Functions: monthly_analysis, seasonal_analysis, daily_profile, PatternExtractor
  - Generates hourly load profiles from demand forecasts
- **Backend**: COMMENTED OUT (3,556 lines but disabled)
- **API Client Method**: `api.generate_profile(config)` → `/project/generate-profile`
- **Cache Support**: network_cache.py & network_cache_optimized.py (DASH ONLY)

### PyPSA Optimization
**Files**: `pypsa_model_executor.py`, `pypsa_analyzer.py`, `pypsa_visualizer.py`
- **Dash**: ACTIVE
  - pypsa_model_executor.py (1,375 lines) - Model execution
  - pypsa_analyzer.py (2,850 lines) - Analysis & results
  - pypsa_visualizer.py (1,257 lines) - Plotting & visualization
- **Backend**: PARTIALLY
  - pypsa_model_executor.py (3,257 lines - MOSTLY COMMENTED)
  - pypsa_analyzer.py (2,850 lines - ACTIVE)
  - pypsa_visualizer.py (1,257 lines - ACTIVE)
- **API Client Methods**: 
  - `api.run_pypsa_model(config)` → `/project/run-pypsa-model`
  - `api.get_pypsa_model_progress()` → `/project/pypsa-model-progress`

---

## 5. API CLIENT USAGE IN DASH APP

The Dash app (`/dash/services/api_client.py`) makes HTTP calls to backend endpoints:

### Pages Using API Client
1. **create_project.py** - Project management
2. **demand_projection.py** - Calls `api.start_demand_forecast()`
3. **generate_profiles.py** - Calls `api.generate_profile()`
4. **model_config.py** - Calls `api.run_pypsa_model()`
5. **analyze_profiles.py** - Calls `api.get_load_profiles()`
6. **load_project.py** - Project loading
7. **view_results.py** - Results visualization
8. **demand_visualization.py** - Demand charts

### API Endpoints in APIClient
```python
# Forecasting
- start_forecast(config) → POST /project/forecast
- get_forecast_progress_url() → GET /project/forecast-progress

# Load Profiles
- generate_profile(config) → POST /project/generate-profile
- get_generation_status_url() → GET /project/generation-status
- get_load_profiles(project_path) → GET /project/load-profiles

# PyPSA
- run_pypsa_model(config) → POST /project/run-pypsa-model
- get_pypsa_model_progress() → GET /project/pypsa-model-progress
- stop_pypsa_model() → POST /project/stop-pypsa-model
```

---

## 6. EXCLUSIVE DASH FEATURE

### network_cache_optimized.py (330 lines)
**Purpose**: Multi-level PyPSA network caching with LZ4 compression

**Performance Claims**:
- Memory cache: 0.001s (1000x faster than source)
- Disk cache: 0.1s (100x faster than source)
- Source load: 10s (baseline)

**Features**:
- LRU (Least Recently Used) memory cache
- Compressed disk cache with lz4
- Automatic cache invalidation when files change
- Cache statistics & cleanup

**Status**: Active in Dash, MISSING in Backend

---

## 7. ARCHITECTURE ANALYSIS

### Current Architecture (Problematic)

```
Dash Frontend
    ↓
APIClient (HTTP calls)
    ↓
Backend FastAPI Routers
    ↓
Subprocess Execution
    ↓
/backend_fastapi/models/*.py (COMMENTED OUT - BROKEN)
```

**Problem**: Backend tries to spawn Python subprocesses for:
- `forecasting.py` ← COMMENTED OUT
- `load_profile_generation.py` ← COMMENTED OUT
- `pypsa_model_executor.py` ← MOSTLY COMMENTED OUT

### Recommended Architecture

```
Option A: Direct Imports (Cleaner)
Dash Frontend
    ↓
Dash Models (Local imports)
    ↓
[forecasting, load_profile, pypsa_executor]

Option B: API-First (Better Separation)
Dash Frontend
    ↓
API Client
    ↓
Backend FastAPI Routes
    ↓
Direct Python Imports (NOT subprocess)
    ↓
/backend_fastapi/models/*.py (UNCOMMENT & FIX)
```

---

## 8. KEY FINDINGS & RECOMMENDATIONS

### Critical Issues
1. **Backend models are commented out** - Forecasting and profile generation cannot execute
2. **Inconsistent implementations** - Different line counts for pypsa_model_executor.py (1,375 vs 3,257)
3. **Subprocess approach fragile** - Spawning commented-out Python files will fail
4. **Missing cache optimization** - Backend lacks LZ4 compression cache

### Recommendations

#### For Short-term Fix (Get Working)
1. **Uncomment backend models** or restore from git history
2. **Update subprocess calls** to handle commented-out files
3. **Add error handling** for subprocess failures
4. **Test forecasting pipeline** end-to-end

#### For Long-term Solution
1. **Consolidate models** - Keep one authoritative copy
   - Option 1: Move dash/models → shared location, import in both
   - Option 2: Keep in backend_fastapi, Dash imports via API
   - Option 3: Split into separate `models` package

2. **Implement direct imports** instead of subprocess
   ```python
   # Instead of:
   subprocess.run(['python', 'models/forecasting.py', ...])
   
   # Use:
   from models.forecasting import run_demand_forecast
   result = run_demand_forecast(config)
   ```

3. **Add cache optimization** to backend
   - Migrate `network_cache_optimized.py` to backend
   - Use for PyPSA network loading

4. **Sync implementations** between dash and backend
   - Compare and resolve version differences
   - Establish single source of truth

#### For Testing
- Test forecasting → profile generation → pypsa pipeline
- Verify subprocess spawning works correctly
- Add unit tests for each model
- Monitor subprocess stderr/stdout for errors

---

## Files to Review
- `/home/user/kseb-version3/dash/models/` - Active implementations
- `/home/user/kseb-version3/backend_fastapi/models/` - Commented implementations
- `/home/user/kseb-version3/dash/services/api_client.py` - HTTP client
- `/home/user/kseb-version3/backend_fastapi/routers/` - API endpoints
