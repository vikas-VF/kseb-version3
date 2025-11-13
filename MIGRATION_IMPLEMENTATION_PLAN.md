# Dash Webapp Implementation Plan
## Complete Migration from FastAPI+React to Dash

**Status**: 80-85% Complete
**Created**: 2025-11-13
**Critical Gaps**: 3 major items

---

## ✅ COMPLETED ITEMS

### 1. Excel Template Files
- ✅ Created `dash/input/` directory
- ✅ Copied all 3 Excel templates from `backend_fastapi/input/`:
  - `input_demand_file.xlsx` (70KB)
  - `load_curve_template.xlsx` (2.1MB)
  - `pypsa_input_template.xlsx` (5.2MB)

### 2. Core Infrastructure
- ✅ All 11 pages implemented with full UI
- ✅ Project creation/loading workflows
- ✅ State management with dcc.Store
- ✅ Navigation and routing
- ✅ Sidebar with active states

### 3. Load Profile Workflows
- ✅ 4-step generation wizard
- ✅ SSE-based progress tracking (JavaScript EventSource)
- ✅ `LoadProfileGenerator` model (2,324 lines)
- ✅ Background execution
- ✅ 6-tab analysis dashboard
- ✅ **ENHANCED**: Max/Min/Avg 24-hour profiles (not in React)

### 4. PyPSA Workflows
- ✅ Model configuration page
- ✅ `PyPSAModelExecutor` (1,375 lines)
- ✅ 7-tab network analysis
- ✅ Capacity, dispatch, metrics, storage, emissions, costs, network views
- ✅ Multi-period network support

### 5. Demand Visualization
- ✅ Dual view mode (consolidated vs sector-specific)
- ✅ 5-tab analysis (Data, Area, Bar, CAGR, Models)
- ✅ Per-scenario state persistence
- ✅ Interactive Plotly charts with zoom/pan
- ✅ Export functionality (Excel, CSV, PNG)
- ✅ **ENHANCED**: Better state management than React

---

## ⚠️ CRITICAL IMPLEMENTATION TASKS

### Task 1: Implement Demand Forecasting Execution
**Priority**: HIGH
**Effort**: 4-6 hours
**Files**: `dash/services/local_service.py`

**Current State:**
```python
# Line 756-782 in local_service.py
def start_demand_forecast(self, project_path: str, config: Dict) -> Dict:
    """Start demand forecasting process"""
    try:
        # TODO: Implement actual forecasting logic  ⚠️
        # For now, return a stub response indicating forecast initiated
        logger.info(f"Forecast requested with config: {config}")

        # Save config for later implementation
        config_path = os.path.join(project_path, 'config', 'forecast_config.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return {
            'success': True,
            'process_id': f"forecast_{config.get('scenario_name', 'default')}",
            'message': 'Forecast configuration saved. Implementation in progress.'
        }
    except Exception as e:
        logger.error(f"Error starting forecast: {e}")
        return {'success': False, 'error': str(e)}
```

**Required Implementation:**
1. Import `forecasting.py` model
2. Prepare config in FastAPI format
3. Spawn subprocess like FastAPI does:
   ```python
   subprocess.Popen([
       "python", "models/forecasting.py",
       "--config", str(config_path)
   ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
   ```
4. Store process in global dict for tracking
5. Parse stdout for "PROGRESS:" JSON lines

**Reference**: `backend_fastapi/routers/forecast_routes.py:182-290`

---

### Task 2: Implement SSE Endpoint for Demand Projection
**Priority**: HIGH
**Effort**: 4-6 hours
**Files**: `dash/app.py`, `dash/services/local_service.py`

**Current State:**
- Load profiles use clientside EventSource to connect to SSE endpoint
- But there's NO Flask route serving SSE for forecasting

**Required Implementation:**

#### A. Add Flask SSE Route to `dash/app.py`:
```python
from flask import Response, stream_with_context
import queue
import json

# Global queue for forecast SSE events
forecast_sse_queue = queue.Queue()

@server.route('/api/forecast-progress')
def forecast_progress_sse():
    """Server-Sent Events endpoint for forecast progress"""
    def generate():
        try:
            while True:
                # Get event from queue (blocks until available)
                event = forecast_sse_queue.get(timeout=15)

                # Send event
                event_type = event.get('type', 'progress')
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event)}\n\n"

                # Check if this is the end event
                if event_type == 'end':
                    break
        except queue.Empty:
            # Timeout - send keep-alive
            yield ": keep-alive\n\n"
        except Exception as e:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
```

#### B. Update `local_service.py` to Feed SSE Queue:
```python
import threading
import subprocess

# Global dict to track forecast processes
forecast_processes = {}

def start_demand_forecast(self, project_path: str, config: Dict) -> Dict:
    """Start demand forecasting process with SSE support"""
    try:
        # Create scenario folder
        scenario_path = Path(project_path) / "results" / "demand_forecasts" / config['scenario_name']
        scenario_path.mkdir(parents=True, exist_ok=True)

        # Prepare config for Python script
        config_for_python = {
            "scenario_name": config['scenario_name'],
            "target_year": config['target_year'],
            "exclude_covid": config.get('exclude_covid_years', False),
            "forecast_path": str(scenario_path),
            "sectors": {}
        }

        for sector in config['sectors']:
            config_for_python["sectors"][sector['name']] = {
                "enabled": True,
                "models": sector['selected_methods'],
                "parameters": {
                    "MLR": {"independent_vars": sector.get('mlr_parameters', [])},
                    "WAM": {"window_size": sector.get('wam_window', 10)}
                },
                "data": sector['data']
            }

        # Write config
        config_path = scenario_path / "forecast_config.json"
        with open(config_path, 'w') as f:
            json.dump(config_for_python, f, indent=2)

        # Start subprocess in background thread
        process_id = f"forecast_{config['scenario_name']}"
        thread = threading.Thread(
            target=self._run_forecast_subprocess,
            args=(config_path, process_id)
        )
        thread.daemon = True
        thread.start()

        forecast_processes[process_id] = {
            'thread': thread,
            'status': 'running',
            'scenario': config['scenario_name']
        }

        return {
            'success': True,
            'process_id': process_id,
            'message': 'Forecast process started.'
        }
    except Exception as e:
        logger.error(f"Error starting forecast: {e}")
        return {'success': False, 'error': str(e)}

def _run_forecast_subprocess(self, config_path: Path, process_id: str):
    """Run forecasting subprocess and stream output to SSE queue"""
    from dash.app import forecast_sse_queue  # Import the global queue

    script_path = Path(__file__).parent.parent / "models" / "forecasting.py"

    try:
        process = subprocess.Popen(
            ["python", str(script_path), "--config", str(config_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Read stdout line by line
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                logger.info(f"[Forecast STDOUT]: {line}")

                # Parse progress lines
                if line.startswith('PROGRESS:'):
                    try:
                        progress_data = json.loads(line[9:])
                        forecast_sse_queue.put(progress_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse progress JSON: {e}")

        # Wait for completion
        process.wait()

        # Send completion event
        if process.returncode == 0:
            forecast_sse_queue.put({
                'type': 'end',
                'status': 'completed',
                'message': 'Forecast completed successfully'
            })
        else:
            forecast_sse_queue.put({
                'type': 'end',
                'status': 'failed',
                'error': 'Forecast process failed'
            })

        forecast_processes[process_id]['status'] = 'completed'

    except Exception as e:
        logger.error(f"Forecast subprocess error: {e}")
        forecast_sse_queue.put({
            'type': 'end',
            'status': 'failed',
            'error': str(e)
        })
        forecast_processes[process_id]['status'] = 'failed'

def get_forecast_status_url(self) -> str:
    """Get SSE URL for forecast progress"""
    return '/api/forecast-progress'
```

#### C. Update `dash/pages/demand_projection.py`:
Already has SSE handling code! Just needs to call `api.get_forecast_status_url()` which we just added above.

**Verification**: Check lines 826-900 in demand_projection.py - SSE client code exists

---

### Task 3: Update create_project to Copy Excel Templates
**Priority**: MEDIUM
**Effort**: 1-2 hours
**Files**: `dash/services/local_service.py`

**Current State:**
```python
# Line 90-130 in local_service.py
def create_project(self, project_data: Dict) -> Dict:
    """Create new project with folder structure"""
    try:
        project_name = project_data['name']
        project_location = project_data['location']

        # Create project directory
        project_path = os.path.join(project_location, project_name)
        if os.path.exists(project_path):
            return {'success': False, 'error': 'Project already exists'}

        os.makedirs(project_path)

        # Create subfolders
        folders = [
            'inputs',
            'results/demand_forecasts',
            'results/load_profiles',
            'results/pypsa_optimization'
        ]

        for folder in folders:
            os.makedirs(os.path.join(project_path, folder), exist_ok=True)

        # ⚠️ MISSING: Copy template Excel files to inputs folder

        # Save project metadata
        # ... (rest of code)
```

**Required Implementation:**
```python
import shutil

def create_project(self, project_data: Dict) -> Dict:
    """Create new project with folder structure"""
    try:
        project_name = project_data['name']
        project_location = project_data['location']

        # Create project directory
        project_path = os.path.join(project_location, project_name)
        if os.path.exists(project_path):
            return {'success': False, 'error': 'Project already exists'}

        os.makedirs(project_path)

        # Create subfolders
        folders = [
            'inputs',
            'results/demand_forecasts',
            'results/load_profiles',
            'results/pypsa_optimization'
        ]

        for folder in folders:
            os.makedirs(os.path.join(project_path, folder), exist_ok=True)

        # ✅ NEW: Copy Excel template files to inputs folder
        template_dir = Path(__file__).parent.parent / 'input'
        inputs_dir = Path(project_path) / 'inputs'

        template_files = [
            'input_demand_file.xlsx',
            'load_curve_template.xlsx',
            'pypsa_input_template.xlsx'
        ]

        for template_file in template_files:
            src = template_dir / template_file
            dst = inputs_dir / template_file
            if src.exists():
                shutil.copy2(src, dst)
                logger.info(f"Copied template: {template_file}")
            else:
                logger.warning(f"Template not found: {template_file}")

        # Save project metadata
        # ... (rest of code)
```

**Reference**: `backend_fastapi/routers/project_routes.py:25-75`

---

## 🔍 VERIFICATION TASKS

### Task 4: Verify Load Profile Generation
**Status**: Appears complete but needs testing

**Checklist:**
- [ ] Test Base Profile method
- [ ] Test STL Decomposition method
- [ ] Verify SSE progress updates work
- [ ] Check all Excel sheets are created correctly
- [ ] Verify pattern extraction logic matches FastAPI

**Reference Model**: `dash/models/load_profile_generation.py:1-2324`

---

### Task 5: Verify PyPSA Model Execution
**Status**: Appears complete but needs testing

**Checklist:**
- [ ] Test single-year optimization
- [ ] Test multi-year optimization
- [ ] Verify all constraints apply correctly
- [ ] Check .nc network file creation
- [ ] Verify Excel results export

**Reference Model**: `dash/models/pypsa_model_executor.py:1-1375`

---

### Task 6: Wire Export Functionality in Demand Visualization
**Priority**: LOW
**Effort**: 1-2 hours

**Current State:**
- Export utils exist in `utils/export.py`
- Buttons exist in UI
- Callbacks not wired to download

**Required**: Connect export buttons to `dcc.Download` components

---

## 📊 IMPLEMENTATION PRIORITY

### Phase 1: Critical (This Week)
1. ✅ Create input folder with templates
2. ⚠️ Implement demand forecasting execution
3. ⚠️ Add SSE endpoint for forecasting
4. ⚠️ Update create_project to copy templates

### Phase 2: Verification (Next Week)
5. Test demand projection end-to-end
6. Test load profile generation end-to-end
7. Test PyPSA execution end-to-end
8. Verify all Excel operations match FastAPI

### Phase 3: Enhancements (Following Week)
9. Wire export functionality
10. Add unit tests
11. Performance optimization
12. Bug fixes

---

## 🎯 SUCCESS CRITERIA

**Definition of Done:**
- [ ] Demand forecasting executes all models (SLR, MLR, WAM, TimeSeries)
- [ ] Real-time SSE progress updates during forecasting
- [ ] Excel results match FastAPI output format exactly
- [ ] All 3 Excel templates copied to new projects
- [ ] Load profile generation verified working
- [ ] PyPSA optimization verified working
- [ ] No dummy/placeholder code remains
- [ ] No hardcoded data (except design constants)
- [ ] All workflows tested end-to-end

---

## 📝 NOTES

### Key Differences: Dash vs FastAPI+React

**Architecture:**
- **FastAPI+React**: Separate backend API + frontend client
- **Dash**: Unified Python app with callbacks

**Process Execution:**
- **FastAPI**: Spawns subprocess, streams stdout to SSE via asyncio.Queue
- **Dash**: Need Flask SSE route + threading to stream subprocess output

**State Management:**
- **React**: React hooks (useState, useContext)
- **Dash**: dcc.Store + callbacks

**SSE Implementation:**
- **React**: JavaScript EventSource in component
- **Dash**: JavaScript EventSource in clientside callback

### Code Reuse

**Models (100% reusable):**
- ✅ `forecasting.py` - IDENTICAL to FastAPI
- ✅ `load_profile_generation.py` - Functionally equivalent
- ✅ `pypsa_analyzer.py` - IDENTICAL to FastAPI
- ✅ `pypsa_model_executor.py` - Functionally equivalent
- ✅ `pypsa_visualizer.py` - IDENTICAL to FastAPI

**Excel Templates (100% shared):**
- ✅ All 3 templates now in `dash/input/`

---

## 🐛 KNOWN ISSUES

1. **generate_profiles.py Line 880** - Calls `api.get_generation_status_url()` but local_service doesn't have this method
   - **Fix**: Add method returning '/api/generation-status'

2. **demand_projection.py** - Has SSE client code but no server endpoint
   - **Fix**: Add Flask route (Task 2)

3. **Forecasting service** - Returns stub success without executing
   - **Fix**: Implement subprocess execution (Task 1)

---

## 📚 REFERENCE FILES

### FastAPI Backend
- `backend_fastapi/main.py` - API configuration
- `backend_fastapi/routers/forecast_routes.py` - Forecasting SSE implementation
- `backend_fastapi/routers/project_routes.py` - Project creation with templates
- `backend_fastapi/models/forecasting.py` - Forecasting algorithms

### Dash Webapp
- `dash/app.py` - Main application
- `dash/services/local_service.py` - Business logic layer
- `dash/models/forecasting.py` - Forecasting model (SAME as FastAPI)
- `dash/pages/demand_projection.py` - Forecasting UI
- `dash/pages/generate_profiles.py` - Load profile UI with SSE example

---

**Last Updated**: 2025-11-13
**Implementation Status**: 80-85% → Target: 100%
