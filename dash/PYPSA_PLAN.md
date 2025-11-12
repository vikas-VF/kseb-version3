# PyPSA Suite - Implementation Plan

## Overview
Complete Plotly Dash implementation matching React PyPSA Suite module (~2,000 lines total)

**Two Main Pages:**
1. **Model Configuration** (ModelConfig.jsx - 533 lines)
2. **View Results** (ViewResults.jsx + UnifiedNetworkView.jsx - ~1,900 lines)

---

## PAGE 1: Model Configuration - Implementation Plan

### Features Breakdown

#### 1. Main Layout (Priority: HIGH)
**Components:**
- Header with title and description
- Configuration form section
- Configuration summary panel
- Footer with Run Model button

**State Required:**
- Scenario name (default: PyPSA_Scenario_V1)
- Selected solver (default: highs)
- Existing scenarios list
- Project path
- Error messages

**Design:**
- Centered card layout with gradient background
- Professional styling with indigo/purple gradient header
- Information boxes with icons

---

#### 2. Basic Configuration Form (Priority: HIGH)
**Features:**
- Scenario Name input
  - Text input with placeholder
  - Duplicate name check (shows warning banner)
  - Real-time validation feedback
- Solver Selection dropdown
  - Highs solver (default and recommended)
  - Solver description display
- Project path display (read-only)

**API Endpoints:**
- `GET /project/pypsa/scenarios?projectPath=X` - List existing scenarios
- `POST /project/pypsa/apply-configuration` - Apply config (create scenario folder)
- `POST /project/run-pypsa-model` - Start model execution

**Validation:**
- Scenario name: Required, shows warning if duplicate
- Solver: Required (pre-filled with highs)
- Project path: Must exist

---

#### 3. Configuration Summary (Priority: HIGH)
**Features:**
- Summary panel with gradient background
- Three information rows:
  - Scenario Name (with file icon)
  - Solver (with wrench icon)
  - Project Path (with folder icon)
- Real-time updates as user edits

---

#### 4. Model Execution & Progress Tracking (Priority: HIGH)
**Features:**
- Apply Configuration & Run Model button
  - Disabled when model is running
  - Shows spinner when running
- Real-time progress tracking via SSE (or polling alternative)
- Progress modal with:
  - Title: "PyPSA Model Execution"
  - Progress indicator
  - Process logs display
  - Solver logs integration
  - Minimize/maximize functionality
  - Stop model button
- Floating indicator when minimized
  - Shows progress percentage
  - Click to restore modal
  - Stop button

**SSE Streams:**
1. `/project/pypsa-model-progress` - Main progress stream
   - Type: 'progress' - Progress updates
   - Type: 'end' - Completion/failure
   - Type: 'error' - Error messages
2. `/project/pypsa-solver-logs?projectPath=X&scenarioName=Y` - Solver logs
   - Type: 'log' - Solver log entries
   - Type: 'end' - Stream end

**Process States:**
- idle → running → completed/failed
- Logs accumulation (unified system)
- Stop functionality via `/project/stop-pypsa-model`

---

### File Structure

```
dash/pages/
├── pypsa_model_config.py   # Model Configuration page (Est. 600-700 lines)
```

---

### Implementation Order (Model Configuration)

**Part 1: Layout & State (150 lines)**
- [ ] Main centered card layout
- [ ] Header with gradient
- [ ] State stores (config, validation, existing scenarios)
- [ ] Project path loading from storage

**Part 2: Configuration Form (150 lines)**
- [ ] Scenario name input with validation
- [ ] Duplicate name check and warning
- [ ] Solver selection dropdown
- [ ] Project path display
- [ ] Info box about PyPSA optimization

**Part 3: Configuration Summary (100 lines)**
- [ ] Summary panel with gradient
- [ ] Three information rows with icons
- [ ] Real-time updates

**Part 4: Model Execution (250 lines)**
- [ ] Apply & Run button handler
- [ ] Configuration application API call
- [ ] Model execution start
- [ ] SSE connection setup (or polling alternative)
- [ ] Process modal integration
- [ ] Floating indicator
- [ ] Stop model functionality
- [ ] Success/failure handling

---

## PAGE 2: View Results - Implementation Plan

### Features Breakdown

#### 1. Main Layout & View Modes (Priority: HIGH)
**Components:**
- Header with project info
- View mode toggle (Excel Results / Network Analysis)
- Content area (switches based on view mode)

**State Required:**
- View mode ('excel' or 'network')
- Selected folder/sheet (Excel mode)
- Selected scenario/network (Network mode)

---

#### 2. Excel Results View (Priority: MEDIUM)
**Features:**
- Folder selector dropdown
  - Loads optimization folders from project
- Sheet selector dropdown
  - Loads sheets from selected folder
- Chart type toggle
  - Area Chart button
  - Stacked Bar Chart button
- Chart display area
  - Plotly area/bar charts
  - Responsive design

**API Endpoints:**
- `GET /project/optimization-folders?projectPath=X` - List folders
- `GET /project/optimization-sheets?projectPath=X&folderName=Y` - List sheets
- `GET /project/optimization-sheet-data?projectPath=X&folderName=Y&sheetName=Z` - Sheet data

**Charts:**
- Area chart (stacked)
- Stacked bar chart
- Dynamic data keys from sheet columns

---

#### 3. Network Analysis View (Priority: HIGH)
**Features:**
- Network Selector component
  - Scenario dropdown
  - Network file(s) selector
  - Multi-select support
- Unified Network View
  - 7 tabs: Dispatch, Capacity, Metrics, Storage, Emissions, Costs, Network
  - Tab-specific visualizations
  - Data loading per tab
  - Info cards with statistics
  - Charts (Area, Bar, Line, Pie)
  - Tables with data

---

#### 4. Network Visualization Tabs (Priority: HIGH)

**Tab 1: Dispatch & Load**
- Resolution selector (1H, 3H, 6H, 12H, 1D, 1W)
- Generation Dispatch area chart (stacked by carrier)
- Load line overlay (dashed black)
- Gradient fills per carrier
- Timestamp X-axis
- Power (MW) Y-axis
- Support for negative values (stackOffset="sign")

**Tab 2: Capacity**
- Info cards: Total Generation, Storage Power, Storage Energy
- Generator Capacities bar chart (colored by carrier)
- Storage Energy Capacity chart (if applicable)
- Multi-period support: Stacked bar by year
- Single-period: Bar chart by carrier

**Tab 3: Metrics**
- Info cards: Renewable Share, Renewable Energy, Total Energy, Total Curtailment
- Renewable vs Non-Renewable pie chart
- Renewable Breakdown by Carrier pie chart
- Capacity Utilization Factors (CUF) table & bar chart
- Curtailment Analysis table & bar chart
- Multi-period: Charts and tables by year

**Tab 4: Storage**
- Info cards: Storage Units count, Stores count
- Storage Units chart (power & energy capacity)
- Stores chart (energy capacity)
- Tables with storage details

**Tab 5: Emissions**
- Info cards: Total Emissions, Emissions Intensity
- Emissions by Carrier bar chart
- Emissions breakdown table
- Multi-period: Emissions by year

**Tab 6: Costs**
- Info cards: Total System Cost
- System Costs by Carrier bar chart
- Cost breakdown table
- Multi-period: Costs by year

**Tab 7: Network**
- Transmission Lines table
- Line capacity visualization
- Network topology (if available)

---

### API Endpoints (View Results)

**Excel View:**
- `GET /project/optimization-folders`
- `GET /project/optimization-sheets`
- `GET /project/optimization-sheet-data`

**Network View:**
- `GET /pypsa/scenarios?projectPath=X` - List scenarios
- `GET /pypsa/networks?projectPath=X&scenario=Y` - List network files
- `GET /pypsa/dispatch?projectPath=X&scenario=Y&network=Z&resolution=R` - Dispatch data
- `GET /pypsa/total-capacities?projectPath=X&scenario=Y&network=Z` - Capacity data
- `GET /pypsa/renewable-share?projectPath=X&scenario=Y&network=Z` - Metrics data
- `GET /pypsa/storage-units?projectPath=X&scenario=Y&network=Z` - Storage data
- `GET /pypsa/emissions?projectPath=X&scenario=Y&network=Z` - Emissions data
- `GET /pypsa/system-costs?projectPath=X&scenario=Y&network=Z` - Costs data
- `GET /pypsa/lines?projectPath=X&scenario=Y&network=Z` - Network lines data

---

### File Structure

```
dash/pages/
├── pypsa_view_results.py   # View Results page (Est. 1,800-2,000 lines)
```

---

### Implementation Order (View Results)

**Phase 1: Main Layout & Excel View (300 lines)**
- [ ] Header with view mode toggle
- [ ] Excel view layout
- [ ] Folder selector with loading
- [ ] Sheet selector with loading
- [ ] Chart type toggle
- [ ] Area chart rendering
- [ ] Stacked bar chart rendering
- [ ] Loading states and error handling

**Phase 2: Network Selector (150 lines)**
- [ ] Scenario dropdown
- [ ] Network files selector
- [ ] Multi-select support
- [ ] Selection state management
- [ ] API integration for scenarios and networks

**Phase 3: Dispatch Tab (250 lines)**
- [ ] Resolution selector
- [ ] Dispatch data loading
- [ ] Area chart with stacked carriers
- [ ] Load line overlay
- [ ] Gradient fills
- [ ] Tooltip formatting
- [ ] Dynamic domain calculation for negative values

**Phase 4: Capacity Tab (250 lines)**
- [ ] Info cards (generation, storage)
- [ ] Generator capacities bar chart
- [ ] Storage charts
- [ ] Multi-period detection
- [ ] Multi-period stacked bar by year
- [ ] Single-period bar by carrier

**Phase 5: Metrics Tab (350 lines)**
- [ ] Info cards (renewable share, energy, curtailment)
- [ ] Renewable vs Non-Renewable pie chart
- [ ] Renewable breakdown pie chart
- [ ] CUF table and bar chart
- [ ] Curtailment table and bar chart
- [ ] Multi-period tables by year

**Phase 6: Storage Tab (200 lines)**
- [ ] Info cards
- [ ] Storage units chart
- [ ] Stores chart
- [ ] Storage details tables

**Phase 7: Emissions Tab (200 lines)**
- [ ] Info cards
- [ ] Emissions by carrier bar chart
- [ ] Emissions table
- [ ] Multi-period support

**Phase 8: Costs Tab (200 lines)**
- [ ] Info cards
- [ ] System costs bar chart
- [ ] Cost breakdown table
- [ ] Multi-period support

**Phase 9: Network Tab (150 lines)**
- [ ] Transmission lines table
- [ ] Line capacity visualization
- [ ] Network topology (if available)

---

## Total Estimated Time

**Model Configuration:** 6-10 hours
**View Results:** 30-40 hours

**Total:** 36-50 hours

**React Code Size:** ~2,000 lines
**Expected Dash Size:** 2,400-2,700 lines

---

## Key Differences from React

- **Charts:** Plotly instead of Recharts
- **SSE:** Dash doesn't support SSE natively - use dcc.Interval polling or implement custom solution
- **State:** dcc.Store instead of unified notification context
- **Icons:** dash-iconify instead of lucide-react
- **Styling:** Dash Bootstrap Components instead of Tailwind CSS

---

## Data Transformers (Utility Functions)

**Helper Functions Needed:**
1. `format_number(value, decimals)` - Format large numbers with K/M/B suffixes
2. `format_percentage(value)` - Format as percentage with 2 decimals
3. `interpolate_color(low_color, high_color, value)` - Color gradient for carriers
4. `detect_multi_period(data)` - Check if data has multiple years
5. `aggregate_by_carrier(data, field)` - Sum values by carrier
6. `aggregate_by_year(data, field)` - Sum values by year

**Color Mapping (PYPSA_COLORS):**
```python
PYPSA_COLORS = {
    'Solar': '#fbbf24',  # Amber
    'Wind': '#3b82f6',   # Blue
    'Hydro': '#06b6d4',  # Cyan
    'Battery': '#8b5cf6', # Purple
    'Gas': '#ef4444',    # Red
    'Coal': '#6b7280',   # Gray
    'Nuclear': '#10b981', # Green
    'Biomass': '#84cc16', # Lime
    # ... more mappings
}
```

---

## Testing Checklist

Model Configuration:
- [ ] Scenario name validation works
- [ ] Duplicate name warning displays
- [ ] Configuration summary updates
- [ ] Model starts execution
- [ ] Progress tracking works
- [ ] Logs display correctly
- [ ] Stop model works
- [ ] Floating indicator shows when minimized
- [ ] Success/failure handling

View Results:
- [ ] Excel view loads folders
- [ ] Excel view loads sheets
- [ ] Excel view displays charts correctly
- [ ] Network view loads scenarios
- [ ] Network view loads network files
- [ ] All 7 tabs render correctly
- [ ] Dispatch chart handles negative values
- [ ] Multi-period detection works
- [ ] Info cards display correct values
- [ ] Tables render with data
- [ ] Charts are responsive
- [ ] Loading states work
- [ ] Error handling works

---

**Ready to implement!** Starting with Model Configuration, then View Results.
