# Detailed Models Comparison Table

## All Files Side-by-Side

| Filename | Dash Path | Dash Lines | Dash Status | Backend Path | Backend Lines | Backend Status | Notes |
|----------|-----------|-----------|---------|-------------|-------------|---------|--------|
| forecasting.py | `/dash/models/` | 589 | ✓ ACTIVE | `/backend_fastapi/models/` | 589 | ✗ COMMENTED | Functions: ProgressTracker, prepare_ml_data, weighted_average_forecast |
| load_profile_generation.py | `/dash/models/` | 2,324 | ✓ ACTIVE | `/backend_fastapi/models/` | 3,556 | ✗ COMMENTED | Difference: 1,232 lines (backend longer but all commented) |
| network_cache.py | `/dash/models/` | 294 | ✓ ACTIVE | `/backend_fastapi/models/` | 294 | ✓ ACTIVE | IDENTICAL - Simple PyPSA network caching |
| network_cache_optimized.py | `/dash/models/` | 330 | ✓ ACTIVE | N/A | — | — | UNIQUE TO DASH - LZ4 compression, 100x faster |
| pypsa_analyzer.py | `/dash/models/` | 2,850 | ✓ ACTIVE | `/backend_fastapi/models/` | 2,850 | ✓ ACTIVE | IDENTICAL - Analysis & results extraction |
| pypsa_model_executor.py | `/dash/models/` | 1,375 | ✓ ACTIVE | `/backend_fastapi/models/` | 3,257 | ✗ MOSTLY COMMENTED | Difference: 1,882 lines (backend longer but mostly commented) |
| pypsa_visualizer.py | `/dash/models/` | 1,257 | ✓ ACTIVE | `/backend_fastapi/models/` | 1,257 | ✓ ACTIVE | IDENTICAL - Plotting & visualization |
| validation_models.py | `/dash/models/` | 115 | ✓ ACTIVE | `/backend_fastapi/models/` | 115 | ✓ ACTIVE | IDENTICAL - Data validation |

## Summary Statistics

### Dash Models Total
- Files: 8 (including __init__.py)
- Active files: 8
- Total lines: ~11,700
- Python modules: 7 (1 empty init file)
- Commented files: 0

### Backend Models Total  
- Files: 7
- Active files: 4
- Disabled/Commented: 3
- Total lines: ~15,500 (but 5,114 lines are commented out)
- Python modules: 7

### Key Differences
| Metric | Value |
|--------|-------|
| Files identical in both | 4 (network_cache, pypsa_analyzer, pypsa_visualizer, validation_models) |
| Files only in Dash | 1 (network_cache_optimized) |
| Files disabled in Backend | 3 (forecasting, load_profile_generation, pypsa_model_executor) |
| Total line difference | ~3,800 lines (backend has longer versions but many are commented) |

## Functionality by Use Case

### Use Case 1: Demand Forecasting
```
Process: Load historical data → Forecast electricity demand for target year
```
| Component | Dash | Backend | Status |
|-----------|------|---------|--------|
| Code | forecasting.py (589 lines) | forecasting.py (589 lines) | ✗ Backend disabled |
| Forecasting methods | MLR, WAM | MLR, WAM | Same |
| API endpoint | N/A (direct import) | /project/forecast | ✗ Cannot use |
| Execution | Can run | Cannot run (subprocess fails) | BROKEN |

### Use Case 2: Load Profile Generation
```
Process: Convert demand forecast → Hourly load profiles
```
| Component | Dash | Backend | Status |
|-----------|------|---------|--------|
| Code | load_profile_generation.py (2,324) | load_profile_generation.py (3,556) | ✗ Backend disabled |
| Pattern analysis | ✓ PatternExtractor class | ✓ In code but commented | Different implementations |
| Caching | ✓ network_cache_optimized | ✗ Missing | Dash only (100x faster) |
| API endpoint | N/A (direct import) | /project/generate-profile | ✗ Cannot use |
| Execution | Can run | Cannot run (subprocess fails) | BROKEN |

### Use Case 3: PyPSA Energy Optimization
```
Process: Optimize power system → Generate dispatch & expansion plans
```
| Component | Dash | Backend | Status |
|-----------|------|---------|--------|
| Model executor | pypsa_model_executor.py (1,375) | pypsa_model_executor.py (3,257) | ✗ Mostly disabled |
| Analyzer | pypsa_analyzer.py (2,850) | pypsa_analyzer.py (2,850) | ✓ Both active |
| Visualizer | pypsa_visualizer.py (1,257) | pypsa_visualizer.py (1,257) | ✓ Both active |
| API endpoint | N/A (direct import) | /project/run-pypsa-model | ✗ Partially broken |
| Execution | Can run | Cannot run fully (executor disabled) | PARTIALLY BROKEN |

## Subprocess Execution Analysis

### Backend Routing Architecture
The backend FastAPI routes attempt to spawn Python subprocesses:

```python
# In /backend_fastapi/routers/forecast_routes.py
python_script_path = Path(__file__).parent.parent / "models" / "forecasting.py"
subprocess.run(['python', str(python_script_path), ...])
```

### Problem
The subprocess tries to execute these files which are **100% commented out**:
- `/backend_fastapi/models/forecasting.py` → All imports, functions, classes commented
- `/backend_fastapi/models/load_profile_generation.py` → All code commented
- `/backend_fastapi/models/pypsa_model_executor.py` → Most code commented

### Result
When a user triggers forecasting/profile generation via Dash UI:
1. Dash calls `api.start_forecast()` → sends HTTP POST to backend
2. Backend router receives request and tries to spawn subprocess
3. Subprocess executes `python /backend_fastapi/models/forecasting.py`
4. Python interprets file as blank (all comments)
5. Nothing happens or subprocess errors out
6. Frontend never receives completion signal

## Code Quality Observations

### Dash Models
- Well-documented with docstrings
- Clear class/function organization
- Includes progress tracking (ProgressTracker class)
- Error handling present
- Logging implemented

### Backend Models (Where Active)
- pypsa_analyzer.py: Well-structured, complete implementation
- pypsa_visualizer.py: Good visualization code with Plotly integration
- validation_models.py: Simple but effective validation
- network_cache.py: Basic but functional caching

### Backend Models (Disabled)
- forecasting.py: 100% commented - impossible to debug/fix without uncommenting
- load_profile_generation.py: 100% commented - dead code
- pypsa_model_executor.py: ~70% commented - partially salvageable

## Recommendations by Priority

### P0 (Critical - System Broken)
1. Uncomment `/backend_fastapi/models/forecasting.py` or restore from git
2. Uncomment `/backend_fastapi/models/load_profile_generation.py`
3. Fix `/backend_fastapi/models/pypsa_model_executor.py`
4. Test subprocess execution with proper error logging

### P1 (High - Performance & Features)
1. Migrate `network_cache_optimized.py` to backend
2. Update backend subprocess to use direct imports instead
3. Reconcile version differences (1,232 and 1,882 line gaps)
4. Add comprehensive error handling

### P2 (Medium - Architecture)
1. Consolidate to single source of truth
2. Add unit tests for each model
3. Establish CI/CD checks for commented code
4. Document model interfaces

### P3 (Low - Optimization)
1. Performance profiling
2. Memory optimization
3. Parallel processing for multi-sector forecasting
4. Caching improvements

## Files to Investigate Further

1. **Git history check**
   - Why are backend models commented out?
   - When did this happen?
   - What was the last working version?

2. **Version reconciliation**
   - Why is backend pypsa_model_executor.py 1,882 lines longer?
   - Why is backend load_profile_generation.py 1,232 lines longer?
   - Are these intentional improvements or accumulated cruft?

3. **Subprocess implementation**
   - How are errors from subprocess being handled?
   - Are return codes being checked?
   - Where are stdout/stderr being captured?

## Conclusion

The system has two separate model codebases with significant inconsistencies:
- **Dash models**: Fully functional, can execute directly
- **Backend models**: Partially disabled, cannot execute

This creates a **critical architectural problem** where the API layer (which should be the single source of truth) cannot actually execute the core algorithms. 

The recommended solution is to **consolidate models and fix the backend implementations**, then either:
1. Use direct imports in backend (faster, simpler)
2. Fix subprocess approach (more complex, but allows long-running processes)

Current state makes the system unsuitable for production use without immediate fixes.
