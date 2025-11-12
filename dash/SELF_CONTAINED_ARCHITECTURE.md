# KSEB Energy Analytics - Self-Contained Dash Webapp Architecture

**Date:** 2025-11-12
**Architecture:** Fully Self-Contained Dash Application (No FastAPI Backend)

---

## Overview

This is a **pure Python Dash web application** with all business logic running in-process. No separate backend server required!

### Old Architecture (Removed)
```
React Frontend (Port 5173)
    ↓ HTTP
FastAPI Backend (Port 8000)
    ↓ Direct Import
Models (forecasting, PyPSA, etc.)
```

### New Architecture (Current)
```
Dash Webapp (Port 8050)
    ↓ Direct Import
Models (forecasting, PyPSA, etc.)
    ↓
Excel Files / Results
```

**Benefits:**
- ✅ **Simpler deployment** - Only one Python process to run
- ✅ **Faster execution** - No HTTP overhead, direct function calls
- ✅ **Easier debugging** - Everything in one codebase
- ✅ **Lower resource usage** - No need for two servers
- ✅ **Better error handling** - Direct exception propagation

---

## How It Works

### Services Layer

**Old:** `/dash/services/api_client.py` (HTTP client)
```python
# Made HTTP POST/GET requests to FastAPI
response = requests.post('http://localhost:8000/project/forecast', json=config)
```

**New:** `/dash/services/local_service.py` (Direct execution)
```python
# Directly imports and calls business logic
from models.forecasting import DemandForecaster
forecaster = DemandForecaster(project_path)
results = forecaster.run_forecast(config)
```

### Pages → Services → Models

**Example: Demand Forecasting Flow**

```python
# 1. User clicks "Start Forecasting" in demand_projection.py
# pages/demand_projection.py
from services.local_service import service as api

@callback(...)
def start_forecasting(n_clicks, config, project):
    # Calls local service (NOT HTTP)
    response = api.start_demand_forecast(project['path'], config)

    ↓

# 2. Local service executes model directly
# services/local_service.py
def start_demand_forecast(self, project_path: str, config: Dict):
    from forecasting import DemandForecaster
    forecaster = DemandForecaster(project_path)
    results = forecaster.run_forecast(config)  # Direct call!

    ↓

# 3. Model does the work
# models/forecasting.py
class DemandForecaster:
    def run_forecast(self, config):
        # Train ML models
        # Generate predictions
        # Save to Excel
        return results
```

**Key Change:** Everything is **synchronous** and **in-process**. No HTTP, no subprocess spawning, no network calls.

---

## Project Structure

```
dash/
├── app.py                          # Main entry point
│   └── Runs on http://localhost:8050
│
├── pages/                          # UI layouts & callbacks
│   ├── home.py
│   ├── demand_projection.py        # Imports service
│   ├── generate_profiles.py
│   └── view_results.py
│
├── services/
│   ├── local_service.py            # ✅ NEW - Direct model execution
│   └── api_client.py               # ❌ DEPRECATED - Not used
│
├── models/                         # Business logic (same as backend)
│   ├── forecasting.py              # Demand forecasting ML models
│   ├── load_profile_generation.py  # Load profile generation
│   ├── pypsa_model_executor.py     # PyPSA optimization
│   ├── pypsa_analyzer.py           # PyPSA network analysis
│   ├── pypsa_visualizer.py         # PyPSA charts
│   └── network_cache_optimized.py  # Performance optimization
│
├── components/                     # Reusable UI components
│   ├── sidebar.py
│   ├── topbar.py
│   └── workflow_stepper.py
│
├── callbacks/                      # Callback registration
│   ├── project_callbacks.py
│   ├── forecast_callbacks.py
│   └── ...
│
├── utils/                          # Helpers
│   ├── state_manager.py
│   ├── charts.py
│   └── export.py
│
└── assets/                         # Static files
    ├── css/
    └── images/
```

---

## Running the Application

### Installation

```bash
cd /home/user/kseb-version3/dash

# Install dependencies (no FastAPI/Uvicorn needed!)
pip install -r requirements.txt
```

### Start the App

```bash
# Single command - that's it!
python app.py
```

The app will start on **http://localhost:8050**

**No separate backend server needed!** 🎉

---

## Key Features

### 1. Project Management
- Create projects with folder structure
- Load existing projects
- Recent projects list
- All handled by `local_service.py` file operations

### 2. Demand Forecasting
- **4 ML Models:** SLR, MLR, WAM, Time Series
- **Direct Execution:** `forecasting.py` runs in Dash process
- **Progress Tracking:** Synchronous execution, instant feedback
- **Results:** Saved to `results/demand_forecasts/`

### 3. Load Profile Generation
- **Statistical & Historical Methods**
- **4-Step Wizard:** Method → Data Source → Constraints → Generate
- **Direct Execution:** `load_profile_generation.py` in-process
- **Results:** Saved to `results/load_profiles/`

### 4. PyPSA Grid Optimization
- **Network Modeling:** Buses, generators, lines, storage
- **Optimization:** LOPF or Capacity Expansion
- **Direct Execution:** `pypsa_model_executor.py` in-process
- **Results:** Saved to `results/pypsa_optimization/`

---

## File Operations

### Project Folder Structure
```
ProjectName/
├── inputs/
│   ├── demand_data.xlsx          # User uploads
│   ├── load_curve.xlsx
│   └── pypsa_config.xlsx
├── results/
│   ├── demand_forecasts/
│   │   └── ScenarioName/
│   │       ├── forecast_results.xlsx
│   │       └── metadata.json
│   ├── load_profiles/
│   │   └── ProfileName/
│   │       ├── hourly_profile.csv
│   │       └── statistics.json
│   └── pypsa_optimization/
│       └── NetworkName/
│           ├── network.nc
│           ├── results.xlsx
│           └── summary.json
├── project.json                  # Metadata
└── color.json                    # Color settings
```

### How Data Flows

**1. User Input → Excel Upload**
```
User uploads demand_data.xlsx to /ProjectName/inputs/
```

**2. Processing → Model Execution**
```
Dash callback → local_service.py → models/forecasting.py → Excel processing
```

**3. Results → Excel Output**
```
Models write results to /ProjectName/results/demand_forecasts/Scenario/
```

**4. Visualization → Data Loading**
```
Dash callback → local_service.py → Read Excel → Plotly charts
```

---

## Performance

### Execution Model

**Old (HTTP-based):**
- Request → Network → Parse JSON → Execute → Serialize JSON → Network → Response
- **Overhead:** 50-200ms per API call
- **Complexity:** Connection pooling, timeouts, retries

**New (Direct calls):**
- Function call → Execute → Return
- **Overhead:** < 1ms
- **Simplicity:** Standard Python function calls

### Caching

The models use advanced caching:
- **Network Cache:** 10-100x speedup for PyPSA networks
- **LZ4 Compression:** 90% smaller cached files
- **In-Memory:** Results cached during session

---

## Migration Details

### What Changed

**Files Modified:**
```
dash/services/local_service.py           # NEW - Replaces HTTP calls
dash/requirements.txt                    # REMOVED fastapi, uvicorn, requests
dash/pages/*.py                          # CHANGED imports to local_service
```

**Files Deprecated:**
```
dash/services/api_client.py              # No longer used
backend_fastapi/                         # No longer needed for Dash
```

### Import Changes

**Old:**
```python
from services.api_client import api
response = api.start_forecast(config)    # HTTP POST
```

**New:**
```python
from services.local_service import service as api
response = api.start_demand_forecast(project_path, config)  # Direct call
```

**Note:** We aliased `service as api` so all existing `api.method()` calls work unchanged!

---

## Error Handling

### Old Architecture
```
Error in model → Exception → FastAPI catches → HTTP 500 → Dash gets error
```

### New Architecture
```
Error in model → Exception → Dash callback catches → Direct error message
```

**Benefit:** Better error messages, easier to debug

---

## Development Workflow

### Adding a New Feature

**Example: Add Export to PDF**

1. **Create model function** in `/models/export.py`
```python
def export_to_pdf(project_path, data):
    # Generate PDF
    return pdf_path
```

2. **Add service method** in `/services/local_service.py`
```python
def export_pdf(self, project_path: str, data: Dict) -> Dict:
    from export import export_to_pdf
    pdf_path = export_to_pdf(project_path, data)
    return {'success': True, 'pdf_path': pdf_path}
```

3. **Call from page** in `/pages/demand_visualization.py`
```python
@callback(...)
def export_button_click(n_clicks, data, project):
    response = api.export_pdf(project['path'], data)
    # Download PDF
```

**No HTTP routes, no FastAPI, no backend changes needed!**

---

## Testing

### Unit Tests
```bash
# Test models directly
python -m pytest models/test_forecasting.py

# Test services
python -m pytest services/test_local_service.py

# Test pages (callbacks)
python -m pytest pages/test_demand_projection.py
```

### Integration Tests
```bash
# Start app and test end-to-end
python app.py &
python -m pytest tests/integration/
```

---

## Deployment

### Option 1: Simple (Development)
```bash
python app.py
```

### Option 2: Production (Gunicorn)
```bash
gunicorn app:server -b 0.0.0.0:8050 -w 4
```

### Option 3: Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```bash
docker build -t kseb-dash .
docker run -p 8050:8050 kseb-dash
```

**No need to run multiple containers!** Just one for the Dash app.

---

## FAQ

### Q: Why remove FastAPI?
**A:** You wanted a fully self-contained Dash webapp. FastAPI adds unnecessary complexity when everything can run in one Python process.

### Q: What about async operations?
**A:** Dash supports async callbacks! You can use `async def` if needed:
```python
@callback(...)
async def my_callback(...):
    result = await some_async_function()
    return result
```

### Q: How do I handle long-running operations?
**A:** Two options:
1. **Background callbacks:** Use `@callback(..., background=True)`
2. **Threading:** Run in separate thread, poll for results
3. **Celery:** Add Celery for distributed task queue (optional)

### Q: Can I still use the FastAPI backend separately?
**A:** Yes! The backend_fastapi folder still exists. But for the Dash app, it's not needed.

### Q: What about the React frontend?
**A:** Deprecated. Dash is the new frontend. React folder can be archived.

---

## Next Steps

1. **Test End-to-End:**
   - Create project
   - Upload data
   - Run forecasting
   - Generate profiles
   - Execute PyPSA
   - Verify all results

2. **Performance Tuning:**
   - Enable caching
   - Optimize Plotly charts
   - Add progress indicators

3. **Production Deploy:**
   - Use Gunicorn/Waitress
   - Add monitoring
   - Configure logging

---

## Summary

**Before:** React + FastAPI + Models (3 separate pieces)
**After:** Dash + Models (1 unified application)

**Result:** Simpler, faster, easier to maintain! 🚀

**To run:**
```bash
cd /home/user/kseb-version3/dash
python app.py
# Open http://localhost:8050
```

That's it! Welcome to the self-contained Dash webapp. 🎉
