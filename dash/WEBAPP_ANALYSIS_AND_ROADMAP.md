# KSEB Energy Analytics Platform - Complete Webapp Analysis & Roadmap

**Date:** 2025-11-12
**Status:** Migration from FastAPI+React to Dash (Python-only webapp)
**Current State:** ~70% Complete - Major functionality exists but scattered across duplicate files

---

## Executive Summary

The KSEB Energy Analytics Platform is being converted from a FastAPI+React architecture to a pure Dash/Plotly webapp. The analysis reveals that **most functionality is already implemented but exists in duplicate "complete" vs "basic" page versions**. The app currently imports basic stub versions while feature-complete versions exist unused.

### Critical Issues

1. **❌ App-Breaking:** Missing components in layouts causing callback errors
   - `forecast-execution-status` - Referenced in callbacks but missing from layout
   - `sectors-list-preview` - Referenced in callbacks but missing from layout

2. **❌ Feature-Breaking:** Wrong page versions imported
   - App uses basic/minimal pages instead of feature-complete versions
   - 6 major features have duplicate implementations

3. **⚠️ Incomplete Integration:** Backend API calls not fully wired
   - Progress tracking defined but not polling backend
   - Settings save callbacks incomplete
   - Excel export functionality missing

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DASH APPLICATION (Port 8050)             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app.py - Main Entry Point                          │   │
│  │  - Store components for state management            │   │
│  │  - Interval components for progress polling         │   │
│  │  - Layout routing and page rendering                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌────────────────┐  │
│  │  Components   │  │     Pages     │  │   Callbacks    │  │
│  ├───────────────┤  ├───────────────┤  ├────────────────┤  │
│  │ - Sidebar     │  │ - Home        │  │ - Project      │  │
│  │ - Topbar      │  │ - Projects    │  │ - Forecast     │  │
│  │ - Workflow    │  │ - Demand      │  │ - Profile      │  │
│  │               │  │ - Load        │  │ - PyPSA        │  │
│  │               │  │ - PyPSA       │  │ - Settings     │  │
│  │               │  │ - Settings    │  │                │  │
│  └───────────────┘  └───────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Port 8000)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Routes (16 router modules)                         │   │
│  │  - Project, Sector, Forecast, Profile, PyPSA        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Models (Shared with Dash)                          │   │
│  │  - forecasting.py (ML models)                       │   │
│  │  - load_profile_generation.py                       │   │
│  │  - pypsa_model_executor.py                          │   │
│  │  - pypsa_analyzer.py                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## File Structure Analysis

### Pages Directory - DUPLICATE FILES PROBLEM

| Feature | Basic Version (Imported) | Complete Version (Not Used) | Lines Difference |
|---------|--------------------------|----------------------------|-----------------|
| **Home** | `home.py` (10K) | `home_complete.py` (23K) | +13K (130% more) |
| **Create Project** | `create_project.py` (4K) | `create_project_complete.py` (20K) | +16K (400% more) |
| **Load Project** | `load_project.py` (2.2K) | `load_project_complete.py` (13K) | +10.8K (491% more) |
| **Demand Projection** | `demand_projection.py` (45K) | `demand_projection_part1/2.py` (partial split) | Complex |
| **Generate Profiles** | `generate_profiles.py` (1.9K) | `load_profiles_generate.py` (34K) | +32K (1,689% more!) |
| **Analyze Profiles** | `analyze_profiles.py` (18K) | `load_profiles_analyze.py` (18K) | Duplicate |
| **Model Config** | `model_config.py` (2.9K) | `pypsa_model_config.py` (31K) | +28K (969% more) |
| **View Results** | `view_results.py` (2.1K) | `pypsa_view_results.py` (41K) | +38.9K (1,852% more!) |

**Total Waste:** ~138K lines of duplicate/unused code

---

## Detailed Feature Analysis

### 1. PROJECT MANAGEMENT

#### How Projects Work

**Folder Structure Created:**
```
ProjectName/
├── inputs/                        # User uploads Excel files here
│   ├── demand_data.xlsx          # Historical demand data
│   ├── load_curve.xlsx           # Load profile templates
│   └── pypsa_config.xlsx         # Network configuration
├── results/
│   ├── demand_forecasts/         # Output: Forecast scenarios
│   │   └── scenario_name/
│   │       ├── forecast_results.xlsx
│   │       └── metadata.json
│   ├── load_profiles/            # Output: Generated hourly profiles
│   │   └── profile_name/
│   │       ├── hourly_profile.csv
│   │       └── statistics.json
│   └── pypsa_optimization/       # Output: Grid optimization results
│       └── network_name/
│           ├── network.nc        # PyPSA network file
│           ├── results.xlsx      # Dispatch, capacity, costs
│           └── summary.json
├── project.json                  # Metadata (name, created, path)
└── color.json                    # Color configuration per sector
```

**Implementation Status:**
- ✅ `create_project.py` - Creates folder structure
- ✅ `load_project.py` - Loads existing project
- ✅ Backend routes work correctly
- ⚠️ Complete versions have validation, recent projects, templates
- ❌ Not using complete versions

**What's Missing:**
- Project templates (preconfigured with sample data)
- Recent projects list in UI
- Project validation on load (path exists, write permissions)

---

### 2. DEMAND PROJECTION & FORECASTING

#### How It Works

**Flow:**
```
1. User configures forecast:
   - Scenario name (e.g., "BaseCase_2040")
   - Target year (2030-2050)
   - Models to use: SLR, MLR, WAM, Time Series
   - COVID-19 year exclusion (optional)
   - T&D losses per sector
   - Solar share integration

2. User clicks "Start Forecasting"
   ↓
3. Frontend sends request to FastAPI:
   POST /project/forecast
   {
     "project_path": "/path/to/project",
     "scenario_name": "BaseCase_2040",
     "target_year": 2040,
     "models": ["SLR", "MLR", "WAM"],
     "exclude_covid": true,
     "td_losses": {"Residential": 8.5, "Commercial": 7.2, ...},
     "solar_share": 0.15
   }
   ↓
4. Backend processes (forecasting.py):
   - Loads historical data from inputs/demand_data.xlsx
   - Trains ML models (SLR, MLR, WAM, Time Series)
   - Generates predictions for each sector
   - Applies T&D losses
   - Integrates solar share
   - Saves to results/demand_forecasts/scenario_name/
   ↓
5. Progress updates via SSE (Server-Sent Events):
   GET /project/forecast-progress?scenario=BaseCase_2040

   Stream:
   data: {"progress": 25, "message": "Training SLR model..."}
   data: {"progress": 50, "message": "Training MLR model..."}
   data: {"progress": 75, "message": "Calculating predictions..."}
   data: {"progress": 100, "message": "Complete!"}
   ↓
6. Frontend polls progress (dcc.Interval every 1s)
   Updates progress modal in real-time
   ↓
7. On completion:
   - Loads results from Excel
   - Displays in Demand Visualization page
   - Shows 5 tabs: Data Table, Area Chart, Stacked Bar, Line Chart, Correlation
```

**Forecasting Models:**

1. **Simple Linear Regression (SLR)**
   - Single variable trend: `Demand(t) = a * Year + b`
   - Best for stable growth patterns

2. **Multiple Linear Regression (MLR)**
   - Multiple economic indicators: `Demand(t) = β0 + β1*GDP + β2*Pop + β3*Temp + ...`
   - Requires indicator data in Excel

3. **Weighted Average Method (WAM)**
   - Historical weighting: Recent years weighted higher
   - Smooths out anomalies

4. **Time Series (ARIMA)**
   - Seasonal decomposition
   - Handles cyclical patterns

**Implementation Status:**

✅ **Fully Implemented in demand_projection.py (1,356 lines):**
- Dual view toggle (Consolidated vs Sector-specific)
- Configure Forecast Modal with 3 tabs:
  - Basic Config (scenario, year, models)
  - T&D Losses (per sector sliders)
  - Advanced Options (COVID exclusion, solar share)
- Data loading from backend API
- Color configuration integration
- 5 visualization tabs per view

❌ **Critical Missing:**
- `forecast-execution-status` component (LINE 8 in forecast_callbacks.py)
- `sectors-list-preview` component (LINE 46 in forecast_callbacks.py)

⚠️ **Partially Implemented:**
- Progress tracking modal exists but not fully wired to backend SSE
- T&D losses inputs collected but not sent to API
- Excel file reading from results folder (only via backend, not direct)

**What Needs to Be Fixed:**
1. Add missing components to demand_projection.py layout
2. Wire up T&D losses to API call
3. Connect progress modal to real backend SSE endpoint
4. Add scenario loading from results folder
5. Implement scenario comparison feature

---

### 3. DEMAND VISUALIZATION

#### How It Works

**Purpose:** Display forecast results with interactive charts

**Data Source:**
```
results/demand_forecasts/scenario_name/
├── forecast_results.xlsx
│   Sheets:
│   - Consolidated (all sectors aggregated)
│   - Residential (sector breakdown)
│   - Commercial
│   - Industrial
│   - Agriculture
│   - Public Lighting
│   - Metadata (models used, parameters, accuracy)
└── metadata.json
```

**Features:**
- **Consolidated View:** All sectors combined
  - Tabs: Data Table, Area Chart, Stacked Bar, Line Chart
  - Unit conversion: MWh, kWh, GWh, TWh
  - Export to Excel/CSV

- **Sector View:** Individual sector analysis
  - Tabs: Data Table, Line Chart, Correlation Analysis
  - Compare multiple scenarios
  - Color-coded by sector (from color.json)

**Implementation Status:**
- ✅ demand_visualization.py exists (structure defined)
- ✅ Backend API `/project/scenarios` lists available scenarios
- ✅ Backend API `/project/load-scenario-data` loads Excel
- ⚠️ Frontend not fully loading results from Excel
- ❌ Scenario comparison not implemented

---

### 4. LOAD PROFILE GENERATION

#### How It Works

**Purpose:** Convert annual demand forecast to hourly/15-min load profiles

**Flow:**
```
1. User selects:
   - Forecast scenario (e.g., "BaseCase_2040")
   - Profile generation method:
     a) Statistical Profiling (from historical patterns)
     b) Historical Pattern Matching (use past year as template)
   - Timeframe: Hourly or 15-minute
   - Constraints: Peak limits, load factor targets

2. 4-Step Wizard:

   STEP 1: Method & Timeframe
   ├── Method: [Statistical | Historical]
   ├── Resolution: [Hourly | 15-min]
   └── Profile Name: "Profile_2040_BaseCase"

   STEP 2: Data Source
   ├── If Statistical:
   │   - Historical load curve from inputs/load_curve.xlsx
   │   - Seasonal factors
   │   - Day type patterns (weekday, weekend, holiday)
   ├── If Historical:
   │   - Reference year selector
   │   - Scaling factor

   STEP 3: Constraints (Optional)
   ├── Peak demand limit (MW)
   ├── Minimum load factor
   ├── Holiday adjustments
   └── Seasonal variations

   STEP 4: Review & Generate
   ├── Summary of selections
   ├── Estimated generation time
   └── [Start Generation] button

3. Backend processing (load_profile_generation.py):
   - Loads forecast data
   - Applies profiling method:

     Statistical:
     - Calculates monthly energy (GWh)
     - Distributes to hourly using historical patterns
     - Applies day type variations
     - Normalizes to match annual total

     Historical:
     - Loads reference year profile
     - Scales to match forecast demand
     - Adjusts for peak/load factor constraints

   - Saves to results/load_profiles/profile_name/
     ├── hourly_profile.csv (8760 or 35040 rows)
     ├── monthly_stats.json
     ├── peak_analysis.json
     └── heatmap_data.json

4. Progress tracking:
   - Real-time logs in modal
   - Progress bar (0-100%)
   - Estimated time remaining
   - Can minimize modal and continue working

5. On completion:
   - Auto-navigate to Analyze Profiles page
   - Load generated profile
   - Display heatmaps, time series, statistics
```

**Implementation Status:**

✅ **Complete 4-Step Wizard EXISTS but UNUSED:**
- `load_profiles_generate.py` (894 lines) has full implementation
- Progress modal with real-time logs
- Floating indicator when minimized
- All 4 steps fully functional

❌ **Currently Using Basic Version:**
- `generate_profiles.py` (41 lines) - Just a simple form
- No wizard, no progress tracking, no constraints
- **THIS IS THE PROBLEM** - App imports basic version

**What Needs to Be Fixed:**
1. Switch from `generate_profiles.py` to `load_profiles_generate.py`
2. Wire up backend API call to actually generate profiles
3. Connect progress polling to backend endpoint
4. Implement constraints application in step 3

---

### 5. LOAD PROFILE VISUALIZATION

#### How It Works

**Purpose:** Analyze generated hourly load profiles with interactive visualizations

**Data Loaded:**
```
results/load_profiles/profile_name/
├── hourly_profile.csv
│   Columns: Timestamp, Load_MW, Sector, DayType, Season
│
├── monthly_stats.json
│   {
│     "Jan": {"peak": 1250, "avg": 890, "min": 420, "energy": 658},
│     "Feb": {"peak": 1180, ...},
│     ...
│   }
│
├── peak_analysis.json
│   {
│     "annual_peak": 1450,
│     "peak_timestamp": "2040-07-15 14:00",
│     "top_10_peaks": [...],
│     "load_factor": 0.68
│   }
│
└── heatmap_data.json
    # 365 x 24 matrix for heatmap visualization
```

**Features - 6 Analysis Tabs:**

**Tab 1: Overview**
- Annual heatmap (365 days × 24 hours)
- Color gradient: Low (blue) → High (red)
- Interactive hover: Date, Hour, Load value
- Peak hour highlighting

**Tab 2: Time Series**
- Hourly load curve for selected period
- Date range selector
- Zoom/pan capabilities
- Export chart

**Tab 3: Month-wise Analysis**
- 12 monthly box plots
- Peak, average, min for each month
- Seasonal patterns visible
- Month selector for drill-down

**Tab 4: Season-wise Analysis**
- 4 seasonal comparisons (Summer, Monsoon, Winter, Spring)
- Average daily profiles per season
- Stacked area charts
- Legend with color coding

**Tab 5: Day-type Comparison**
- Weekday vs Weekend vs Holiday
- Average profiles overlaid
- Percentage difference
- Hour-by-hour comparison

**Tab 6: Load Duration Curve**
- Sorted load values (high to low)
- Cumulative percentage
- Base/shoulder/peak load identification
- Capacity factor analysis

**Implementation Status:**
- ✅ **load_profiles_analyze.py (18K lines) - FULLY IMPLEMENTED**
- ✅ All 6 tabs functional
- ✅ Interactive Plotly charts
- ✅ Color controls
- ✅ Period selection
- ✅ Backend integration for loading profiles

**What Works:**
- Everything! This is one of the complete modules.

---

### 6. PyPSA GRID OPTIMIZATION

#### How It Works

**Purpose:** Optimize power grid with renewable energy integration, storage, and transmission

**PyPSA Model Components:**

```
Network:
├── Buses (Nodes)
│   - Location: Lat/Lon
│   - Carrier: AC or DC
│   - Voltage level: 11kV, 33kV, 66kV, 110kV, 220kV, 400kV
│
├── Generators
│   ├── Solar PV (variable)
│   ├── Wind (variable)
│   ├── Hydro (dispatchable)
│   ├── Coal/Gas (dispatchable)
│   ├── Biomass
│   └── Parameters:
│       - Capacity (MW)
│       - Marginal cost (₹/MWh)
│       - Efficiency
│       - Capital cost
│       - Lifetime
│
├── Storage Units
│   ├── Battery storage
│   ├── Pumped hydro
│   ├── Parameters:
│       - Capacity (MWh)
│       - Power (MW)
│       - Efficiency (charge/discharge)
│       - Cyclic state of charge
│
├── Lines (Transmission)
│   - From bus → To bus
│   - Capacity (MW)
│   - Length (km)
│   - Reactance, resistance
│   - Capital cost
│
└── Loads
    - Bus location
    - Hourly profile (from Load Profile Generation)
    - Sector allocation
```

**Workflow:**

```
STEP 1: Configure Model (pypsa_model_config.py)
├── Network Name: "Kerala_Grid_2040"
├── Load Profile: [Dropdown of generated profiles]
├── Optimization Type:
│   ├── LOPF (Linear Optimal Power Flow) - Single snapshot
│   ├── Capacity Expansion - Multi-period planning
├── Solver:
│   ├── GLPK (open-source, slower)
│   ├── CBC (open-source, faster)
│   ├── Gurobi (commercial, fastest) - requires license
│   └── HiGHS (recommended, fast, open-source)
├── Time Resolution:
│   ├── Full year (8760 hours)
│   ├── Representative days (24 hours × N days)
│   ├── Monthly averages
├── Network Components:
│   └── Load from inputs/pypsa_config.xlsx
│       Sheets:
│       - Buses
│       - Generators
│       - Storage
│       - Lines
│       - Transformers
│       - Loads
├── Scenarios:
│   ├── Base Case
│   ├── High RE (80% renewable)
│   ├── Storage Expansion
│   └── Custom

STEP 2: Execute Optimization
├── Backend calls pypsa_model_executor.py:
│
│   1. Load network configuration
│   2. Attach load profiles (hourly)
│   3. Build PyPSA network object
│      network = pypsa.Network()
│      network.import_from_csv_folder(project_path + "/inputs/")
│
│   4. Add components:
│      network.add("Bus", bus_name, **params)
│      network.add("Generator", gen_name, **params)
│      network.add("StorageUnit", storage_name, **params)
│      network.add("Line", line_name, **params)
│      network.add("Load", load_name, p_set=profile)
│
│   5. Run optimization:
│      If LOPF:
│        network.lopf(pyomo=False, solver_name='highs')
│
│      If Capacity Expansion:
│        network.optimize(
│          solver_name='highs',
│          multi_investment_periods=True
│        )
│
│   6. Extract results:
│      - generators_t.p (dispatch over time)
│      - storage_units_t.state_of_charge
│      - lines_t.p0 (line flows)
│      - buses_t.marginal_price (LMP)
│
│   7. Calculate metrics:
│      - Total system cost
│      - LCOE (Levelized Cost of Energy)
│      - Renewable penetration %
│      - Capacity factors
│      - Curtailment (renewable energy wasted)
│      - Storage cycles
│      - Transmission congestion
│
│   8. Save results:
│      results/pypsa_optimization/network_name/
│      ├── network.nc (NetCDF format - full network)
│      ├── results.xlsx
│      │   Sheets:
│      │   - Dispatch (hourly generator output)
│      │   - Storage SOC
│      │   - Line Flows
│      │   - Bus Prices
│      │   - Capacity
│      │   - Costs
│      │   - Emissions
│      │   - Summary
│      └── summary.json
│
├── Progress Tracking:
│   - Real-time solver logs
│   - Iteration count
│   - Objective function value
│   - Estimated time remaining
│   - Can stop/cancel mid-optimization

STEP 3: View Results (pypsa_view_results.py)

TAB 1: Excel Results
├── Sheet selector dropdown
├── Interactive data table
├── Export filtered data
└── Column sorting/filtering

TAB 2: Dispatch & Load
├── Stacked area chart:
│   - X-axis: Time (hours)
│   - Y-axis: Power (MW)
│   - Layers: Each generator type
│   - Line: Total load
├── Drill-down: Click to see hourly details
├── Export chart/data

TAB 3: Capacity
├── Bar chart: Installed capacity by type
├── Pie chart: Capacity mix %
├── Comparison: Optimal vs Input capacity
└── Color-coded by generator type

TAB 4: Metrics
├── KPI Cards:
│   ├── Total Cost: ₹X billion
│   ├── LCOE: ₹Y/kWh
│   ├── Renewable %: Z%
│   ├── Peak Load: W MW
├── Capacity Factor table
└── Curtailment analysis

TAB 5: Storage
├── State of charge over time (line chart)
├── Charge/discharge cycles
├── Efficiency losses
└── Utilization %

TAB 6: Emissions
├── Total CO₂ emissions
├── Emissions by fuel type
├── Emissions intensity (tCO₂/MWh)
└── Comparison with target

TAB 7: Network Visualization
├── Interactive map:
│   - Nodes: Buses (sized by load)
│   - Edges: Lines (thickness = capacity, color = flow)
│   - Generators: Icons at bus locations
├── Plotly network graph
├── Zoom/pan
└── Click for component details
```

**Implementation Status:**

✅ **Complete Implementation EXISTS but UNUSED:**
- `pypsa_model_config.py` (825 lines) - Full config with all options
- `pypsa_view_results.py` (1,212 lines) - 7 tabs, all visualizations

❌ **Currently Using Basic Version:**
- `model_config.py` (58 lines) - Minimal form
- `view_results.py` (46 lines) - Empty placeholder

**What Needs to Be Fixed:**
1. Switch to complete versions
2. Wire up PyPSA execution to backend
3. Implement network visualization (Plotly network graphs)
4. Add color configuration for generator types
5. Test with actual PyPSA models

---

### 7. COLOR CONFIGURATION

#### How It Works

**Purpose:** Consistent color schemes across all visualizations

**Storage:**
```
project_folder/color.json
{
  "sectors": {
    "Residential": "#3b82f6",      // blue-500
    "Commercial": "#10b981",       // green-500
    "Industrial": "#f59e0b",       // amber-500
    "Agriculture": "#8b5cf6",      // violet-500
    "Public Lighting": "#ec4899"   // pink-500
  },
  "models": {
    "SLR": "#06b6d4",              // cyan-500
    "MLR": "#8b5cf6",              // violet-500
    "WAM": "#f59e0b",              // amber-500
    "Time Series": "#ef4444"       // red-500
  },
  "generators": {
    "Solar": "#fbbf24",            // yellow-400
    "Wind": "#06b6d4",             // cyan-500
    "Hydro": "#3b82f6",            // blue-500
    "Coal": "#6b7280",             // gray-500
    "Gas": "#f97316",              // orange-500
    "Biomass": "#10b981"           // green-500
  },
  "chart_theme": "light"
}
```

**Usage:**
- Demand charts: Color by sector
- Forecast charts: Color by model type
- PyPSA dispatch: Color by generator type
- Storage SOC: Color by storage type

**Implementation Status:**
- ✅ Color storage in project folder
- ✅ Backend API `/project/settings/colors` (GET/POST)
- ✅ Settings page UI exists
- ⚠️ Not fully integrated in all charts
- ❌ PyPSA generator colors not implemented

**What Needs to Be Added:**
1. Color picker UI in settings page
2. Apply colors to PyPSA visualizations
3. Save callback wired to backend
4. Default color schemes (light/dark mode)

---

## Roadmap to Completion

### Phase 1: Critical Fixes (URGENT - 2 hours)

**Goal:** Fix app-breaking errors so it runs without crashes

1. **Add Missing Components to demand_projection.py**
   - [ ] Add `forecast-execution-status` div in layout
   - [ ] Add `sectors-list-preview` div in layout
   - [ ] Test callbacks don't crash

2. **Fix Callback Outputs**
   - [ ] Update forecast_callbacks.py to match layout
   - [ ] Verify all Output IDs exist in layouts
   - [ ] Test each callback independently

### Phase 2: Consolidate Duplicate Files (CRITICAL - 4 hours)

**Goal:** Eliminate duplicate code, use complete versions

1. **Merge Page Files**
   - [ ] Keep complete versions, delete basic versions
   - [ ] `home_complete.py` → `home.py`
   - [ ] `create_project_complete.py` → `create_project.py`
   - [ ] `load_project_complete.py` → `load_project.py`
   - [ ] `load_profiles_generate.py` → `generate_profiles.py`
   - [ ] `pypsa_model_config.py` → `model_config.py`
   - [ ] `pypsa_view_results.py` → `view_results.py`

2. **Update Imports**
   - [ ] Update `pages/__init__.py`
   - [ ] Verify app.py routes correctly
   - [ ] Test navigation works

3. **Delete Unused Files**
   - [ ] Remove old basic versions
   - [ ] Remove part1/part2 split files
   - [ ] Clean up duplicates

### Phase 3: Wire Up Backend Integration (HIGH - 6 hours)

**Goal:** Connect all features to FastAPI backend

1. **Demand Forecasting**
   - [ ] Wire `start_forecasting()` to `POST /project/forecast`
   - [ ] Implement SSE progress streaming
   - [ ] Convert SSE to Interval polling in Dash
   - [ ] Test full forecast execution
   - [ ] Verify results saved to Excel

2. **Load Profile Generation**
   - [ ] Wire 4-step wizard to backend
   - [ ] Implement `POST /project/generate-profiles` call
   - [ ] Connect progress polling
   - [ ] Test profile generation end-to-end
   - [ ] Verify CSV output

3. **PyPSA Optimization**
   - [ ] Wire config page to backend
   - [ ] Implement `POST /project/pypsa/run-model` call
   - [ ] Connect solver progress polling
   - [ ] Test optimization execution
   - [ ] Verify network.nc and results.xlsx created

4. **Settings**
   - [ ] Wire color picker to `POST /settings/save-colors`
   - [ ] Test color persistence
   - [ ] Apply colors across all charts

### Phase 4: Complete Missing Features (MEDIUM - 4 hours)

**Goal:** Implement partially complete features

1. **T&D Losses**
   - [ ] Collect T&D loss values from modal
   - [ ] Pass to forecast API call
   - [ ] Verify application in results

2. **Scenario Management**
   - [ ] List available scenarios from results folder
   - [ ] Load scenario data into visualization
   - [ ] Implement scenario comparison (side-by-side)

3. **Excel Export**
   - [ ] Add export buttons to all visualization pages
   - [ ] Implement download functionality
   - [ ] Test CSV/Excel export

4. **Color Configuration for PyPSA**
   - [ ] Add generator color settings
   - [ ] Apply to dispatch charts
   - [ ] Apply to network visualization

### Phase 5: Advanced Features (LOW - 3 hours)

**Goal:** Polish and advanced functionality

1. **Project Templates**
   - [ ] Create sample project templates
   - [ ] Implement template selection in create project
   - [ ] Pre-fill with demo data

2. **Recent Projects**
   - [ ] Store recent projects in localStorage
   - [ ] Display in home page
   - [ ] Quick load functionality

3. **Network Visualization**
   - [ ] Implement Plotly network graph for PyPSA
   - [ ] Show buses, generators, lines
   - [ ] Interactive tooltips
   - [ ] Flow animation

4. **Validation**
   - [ ] Validate project paths
   - [ ] Check Excel file formats
   - [ ] Verify PyPSA config completeness
   - [ ] User-friendly error messages

### Phase 6: Testing & Documentation (2 hours)

**Goal:** Ensure reliability and maintainability

1. **End-to-End Testing**
   - [ ] Create test project
   - [ ] Run full demand forecast
   - [ ] Generate load profiles
   - [ ] Execute PyPSA optimization
   - [ ] Verify all results

2. **Error Handling**
   - [ ] Add try-catch in all callbacks
   - [ ] User-friendly error messages
   - [ ] Logging for debugging

3. **Documentation**
   - [ ] Update README.md
   - [ ] Create user guide
   - [ ] Document API endpoints
   - [ ] Code comments

---

## File Consolidation Plan

### Files to KEEP (Complete Versions)
```
dash/
├── app.py ✅
├── pages/
│   ├── __init__.py (update)
│   ├── home.py (from home_complete.py) ✅
│   ├── create_project.py (from create_project_complete.py) ✅
│   ├── load_project.py (from load_project_complete.py) ✅
│   ├── demand_projection.py (fix missing components) ✅
│   ├── demand_visualization.py ✅
│   ├── generate_profiles.py (from load_profiles_generate.py) ✅
│   ├── analyze_profiles.py (keep, it's complete) ✅
│   ├── model_config.py (from pypsa_model_config.py) ✅
│   ├── view_results.py (from pypsa_view_results.py) ✅
│   └── settings_page.py ✅
├── callbacks/ (all existing) ✅
├── components/ (all existing) ✅
├── models/ (all existing) ✅
├── services/ (all existing) ✅
└── utils/ (all existing) ✅
```

### Files to DELETE
```
dash/pages/
├── home_complete.py ❌
├── create_project_complete.py ❌
├── load_project_complete.py ❌
├── create_project_part1.py ❌
├── create_project_part2.py ❌
├── demand_projection_part1.py ❌
├── demand_projection_part2.py ❌
├── load_profiles_generate.py ❌ (merged into generate_profiles.py)
├── load_profiles_analyze.py ❌ (merged into analyze_profiles.py)
├── pypsa_model_config.py ❌ (merged into model_config.py)
└── pypsa_view_results.py ❌ (merged into view_results.py)
```

### Result
- **Before:** 20 page files, ~190K lines, many duplicates
- **After:** 11 page files, ~100K lines, no duplicates
- **Savings:** ~47% reduction in code size, easier to maintain

---

## Expected Final State

### File Count
- **Before:** 151 files (74 Dash, 23 Backend, 54 React)
- **After:** 140 files (63 Dash consolidated)
- **Deleted:** 11 duplicate files

### Functionality
- ✅ Project creation with templates
- ✅ Project loading with validation
- ✅ Demand forecasting (4 ML models)
- ✅ T&D losses integration
- ✅ Demand visualization (5 chart types)
- ✅ Scenario comparison
- ✅ Load profile generation (4-step wizard)
- ✅ Load profile analysis (6 visualization tabs)
- ✅ PyPSA configuration (all components)
- ✅ PyPSA optimization (LOPF + capacity expansion)
- ✅ PyPSA visualization (7 analysis tabs)
- ✅ Color configuration (sectors, models, generators)
- ✅ Settings persistence
- ✅ Real-time progress tracking

### Performance
- Dash app startup: <3 seconds
- Page navigation: <500ms
- Forecast execution: 30s - 5min (depending on data size)
- Profile generation: 10s - 2min
- PyPSA optimization: 1min - 30min (depending on network size)
- Results loading: <1s (with caching)

---

## Success Metrics

✅ **App runs without errors** - No missing component exceptions
✅ **All pages navigate correctly** - No 404s or blank pages
✅ **Full forecast workflow** - Config → Execute → Visualize
✅ **Full profile workflow** - Select → Generate → Analyze
✅ **Full PyPSA workflow** - Configure → Optimize → View Results
✅ **Settings persist** - Colors saved and applied
✅ **Progress tracking works** - Real-time updates during processing
✅ **Excel I/O works** - Read inputs, write results
✅ **Code maintainability** - Single source of truth, no duplicates

---

## Next Steps

**IMMEDIATE (Next 1 hour):**
1. Fix missing component errors
2. Add `forecast-execution-status` and `sectors-list-preview` to demand_projection.py
3. Test app runs without crashes

**SHORT-TERM (Next 4 hours):**
1. Consolidate duplicate files
2. Update imports
3. Delete unused files
4. Test navigation

**MEDIUM-TERM (Next 8 hours):**
1. Wire up backend APIs
2. Implement missing features
3. Add advanced functionality
4. Full testing

**COMPLETION TARGET:** 13 hours total work

---

## Questions/Decisions Needed

1. **React Frontend:** Keep or delete? (Currently unused)
   - **Recommendation:** Keep for now, mark deprecated, delete later

2. **Page file naming:** Standard naming convention?
   - **Recommendation:** Use descriptive names without _complete suffix

3. **Color themes:** Light + Dark mode support?
   - **Recommendation:** Implement in Phase 5 (low priority)

4. **Deployment:** How to deploy Dash app?
   - **Options:** Docker, Gunicorn, Cloud (AWS/GCP)

---

**This analysis is complete and ready for implementation.**
