# Demand Visualization - Implementation Plan

## Overview
Complete Plotly Dash implementation matching React DemandVisualization.jsx (1,223 lines)

## Features Breakdown

### 1. Main Layout & Navigation (Priority: HIGH)
**Components:**
- Header with project name
- Scenario selector dropdown (loads from `/project/scenarios`)
- Year range inputs (start year, end year with validation)
- Unit selector (MWh, kWh, GWh, TWh)
- Model Selection button (opens modal)
- Compare Scenario button (toggles comparison mode)
- Three main tabs: Sector Data | T&D Losses | Consolidated Results

**State Required:**
- Selected scenario
- Start year / End year
- Selected unit
- Active tab
- Comparison mode flag
- Scenarios to compare

---

### 2. Sector Data View (Priority: HIGH)
**Features:**
- Sector selector dropdown
- Demand type selector (Gross/Net/On-Grid)
- Line chart showing:
  - Multiple model series (MLR, SLR, WAM, Historical, User Data, Time Series)
  - Forecast marker line (dashed red vertical line)
  - Historical/Projected labels
  - Zoom controls (x and y sliders)
- Data table with all models in columns
- Unit conversion across all displays

**API Endpoints:**
- `GET /project/scenarios/{scenario}/sectors` - Get sector list
- `GET /project/scenarios/{scenario}/models` - Get available models per sector
- `GET /project/scenarios/{scenario}/sectors/{sector}?startYear=X&endYear=Y` - Fetch sector data

**Plotly Chart:**
```python
go.Figure([
    go.Scatter(x=years, y=model_data, name='MLR', mode='lines+markers'),
    # ... more models
    go.Scatter(x=[forecast_year]*2, y=[min, max],
              mode='lines', line=dict(dash='dash', color='red'),
              showlegend=False)  # Forecast marker
])
```

---

### 3. T&D Losses Tab (Priority: MEDIUM)
**Features:**
- Sector selector
- T&D Loss percentage input (per sector)
- Area chart showing loss values over time
- Gradient fill with markers
- Save button to update backend

**API Endpoints:**
- `GET /project/scenarios/{scenario}/td-losses` - Get current losses
- `POST /project/scenarios/{scenario}/td-losses` - Update losses

**Plotly Chart:**
```python
go.Figure([
    go.Scatter(x=years, y=losses, fill='tonexty',
              mode='lines+markers', fillcolor='rgba(239,68,68,0.2)')
])
```

---

### 4. Consolidated Results View (Priority: HIGH)
**Features:**
- Model selection per sector (via modal)
- Two chart tabs:
  - **Area Chart**: Stacked area by sector with color coding
  - **Stacked Bar Chart**: Stacked bars with total line overlay
- Data table showing all sectors in columns
- Legend controls (show/hide sectors)
- Zoom controls (x and y sliders)
- Save button to persist consolidated data

**API Endpoints:**
- `POST /project/scenarios/{scenario}/consolidated` - Calculate consolidated with model selections
  ```json
  {
    "projectPath": "/path",
    "scenarioName": "Base Case",
    "startYear": 2020,
    "endYear": 2050,
    "modelSelections": {"Residential": "MLR", "Commercial": "SLR", ...}
  }
  ```
- `GET /project/scenarios/{scenario}/consolidated/exists` - Check if saved
- `GET /project/scenarios/{scenario}/sectors/Consolidated_Results` - Fetch saved
- `POST /project/save-consolidated` - Save to backend

**Plotly Charts:**

Area Chart:
```python
fig = go.Figure()
for sector in sectors:
    fig.add_trace(go.Scatter(
        x=years, y=data[sector],
        stackgroup='one', name=sector,
        fillcolor=colors[sector]
    ))
```

Stacked Bar Chart:
```python
fig = go.Figure()
for sector in sectors:
    fig.add_trace(go.Bar(x=years, y=data[sector], name=sector))
# Add total line
fig.add_trace(go.Scatter(x=years, y=total_data, mode='lines', name='Total'))
fig.update_layout(barmode='stack')
```

---

### 5. Model Selection Modal (Priority: HIGH)
**Features:**
- Modal with sector-by-sector model dropdown
- Available models per sector from backend
- Default to first available model
- Apply button to trigger recalculation
- Cancel button to discard changes

**State:**
```python
model_selections = {
    'Residential': 'MLR',
    'Commercial': 'SLR',
    'Industrial': 'WAM',
    # ...
}
```

**Callback Flow:**
1. User clicks "Model Selection" button
2. Modal opens with current selections
3. User changes dropdowns
4. Click "Apply" → POST to `/consolidated` endpoint
5. Update consolidated data and charts

---

### 6. Comparison Mode (Priority: MEDIUM)
**Features:**
- Compare Scenario modal:
  - Checkbox list of other scenarios
  - Only one can be selected
  - "Compare" button
- Comparison view:
  - **Sector View**: Side-by-side charts and tables
  - **Consolidated View**: Dual scenario charts with color differentiation
- "Stop Comparison" button to exit mode

**Layout Changes:**
```python
if comparison_mode:
    return dbc.Row([
        dbc.Col([
            html.H6(f'Scenario 1: {scenario1}'),
            chart1,
            table1
        ], width=6),
        dbc.Col([
            html.H6(f'Scenario 2: {scenario2}'),
            chart2,
            table2
        ], width=6)
    ])
```

**Data Fetching:**
- Fetch data for both scenarios
- Store in separate dcc.Store components
- Render side-by-side or overlaid

---

### 7. Export Functionality (Priority: MEDIUM)
**Features:**
- "Save" button (green) - Save consolidated to backend
- "Save Changes" button (orange) - Re-save after modifications
- Toast notifications for success/error
- Track saved state

**Implementation:**
```python
@callback(
    Output('save-toast', 'children'),
    Input('save-consolidated-btn', 'n_clicks'),
    State('consolidated-data-store', 'data')
)
def save_consolidated(n_clicks, data):
    if n_clicks:
        response = api.save_consolidated_data(project_path, scenario, data)
        return dbc.Toast('Saved successfully!', color='success')
```

---

### 8. State Management (Priority: HIGH)
**dcc.Store Components:**
```python
dcc.Store(id='demand-viz-state', storage_type='session', data={
    'selectedScenario': None,
    'startYear': None,
    'endYear': None,
    'unit': 'mwh',
    'activeTab': 'sector',
    'demandType': 'gross',
    'selectedSector': None,
    'modelSelections': {},
    'comparisonMode': False,
    'scenariosToCompare': {'scenario1': None, 'scenario2': None},
    'consolidated': {
        'areaChartHiddenSectors': [],
        'areaChartZoom': None,
        'stackedBarChartHiddenSectors': [],
        'stackedBarChartZoom': None
    }
}),
dcc.Store(id='scenarios-list', data=[]),
dcc.Store(id='sector-data-store', data=None),
dcc.Store(id='consolidated-data-store', data=None),
dcc.Store(id='comparison-sector-data-store', data=None),
dcc.Store(id='comparison-consolidated-data-store', data=None)
```

---

### 9. Callbacks Summary (Est. 30-35 callbacks)

**Navigation & Filters:**
1. `load_scenarios_list` - On page load, fetch scenarios
2. `update_scenario_metadata` - Load target year when scenario selected
3. `validate_year_range` - Ensure start <= end <= target
4. `sync_state_to_storage` - Persist state changes

**Sector Data View:**
5. `load_sectors` - Fetch sector list for scenario
6. `load_sector_data` - Fetch sector data with year filter
7. `render_sector_line_chart` - Create line chart with models
8. `render_sector_data_table` - Display data table
9. `toggle_demand_type` - Filter gross/net/on-grid

**T&D Losses:**
10. `load_td_losses` - Fetch current losses
11. `update_td_losses` - Save new loss values
12. `render_td_losses_chart` - Area chart

**Consolidated Results:**
13. `open_model_selection_modal` - Show modal
14. `apply_model_selection` - POST to calculate consolidated
15. `load_consolidated_data` - Fetch existing consolidated
16. `render_consolidated_area_chart` - Stacked area
17. `render_consolidated_bar_chart` - Stacked bar with total line
18. `render_consolidated_data_table` - Display table
19. `toggle_area_chart_series` - Legend click handler
20. `toggle_bar_chart_series` - Legend click handler

**Comparison Mode:**
21. `open_comparison_modal` - Show scenario selection
22. `toggle_comparison_mode` - Enable/disable comparison
23. `load_comparison_scenario_data` - Fetch second scenario
24. `render_comparison_charts` - Side-by-side or overlaid

**Export:**
25. `save_consolidated_data` - POST to backend
26. `track_saved_state` - Update button color/text

**Utility:**
27. `convert_units` - Apply conversion factor
28. `format_numbers` - Locale-specific formatting
29. `update_chart_zoom` - Persist zoom state
30. `initialize_default_selections` - Set first sector/model

---

## File Structure

```
dash/pages/
├── demand_visualization.py          # Main component (Est. 1,500+ lines)
├── demand_visualization_modals.py   # Modals (Model Selection, Comparison)
└── demand_visualization_charts.py   # Chart rendering functions (optional)

dash/utils/
└── chart_utils.py                   # Forecast line, zoom helpers (optional)
```

---

## Implementation Order (Recommended)

### Phase 1: Layout & Basic Navigation (4-6 hours)
- [ ] Main layout with header
- [ ] Scenario selector
- [ ] Year range inputs
- [ ] Unit selector
- [ ] Tab navigation
- [ ] State stores setup

### Phase 2: Sector Data View (10-12 hours)
- [ ] Sector selector
- [ ] Load sector data from API
- [ ] Line chart with multiple models
- [ ] Forecast marker line
- [ ] Data table
- [ ] Demand type filter

### Phase 3: Consolidated Results (12-15 hours)
- [ ] Model selection modal
- [ ] Calculate consolidated API call
- [ ] Area chart (stacked)
- [ ] Stacked bar chart with total line
- [ ] Data table
- [ ] Legend controls
- [ ] Zoom controls

### Phase 4: T&D Losses Tab (6-8 hours)
- [ ] Load/save T&D losses
- [ ] Area chart with gradient
- [ ] Sector selector
- [ ] Input controls

### Phase 5: Comparison Mode (10-12 hours)
- [ ] Compare scenario modal
- [ ] Dual data loading
- [ ] Side-by-side sector view
- [ ] Overlaid consolidated charts
- [ ] Stop comparison

### Phase 6: Export & Polish (6-8 hours)
- [ ] Save consolidated data
- [ ] Button state management
- [ ] Toast notifications
- [ ] State persistence
- [ ] Error handling

---

## Total Estimated Time: 48-61 hours

**Aggressive Target:** 48 hours
**Conservative Target:** 61 hours
**React Component Size:** 1,223 lines
**Expected Dash Size:** 1,400-1,600 lines

---

## Key Differences from React
- **Charts:** Plotly instead of ECharts/ApexCharts
- **State:** dcc.Store instead of React useState + sessionStorage
- **Modals:** dbc.Modal instead of custom React components
- **Forms:** Dash Input/Dropdown instead of React controlled components

---

## Testing Checklist
- [ ] Scenario switching preserves state
- [ ] Year range validation works
- [ ] Unit conversion accurate across all views
- [ ] Charts render with correct data
- [ ] Model selection triggers recalculation
- [ ] Comparison mode loads both scenarios
- [ ] Save functionality persists data
- [ ] State survives page navigation
- [ ] Error handling for API failures
- [ ] Loading states during data fetch

---

**Ready to implement!** Starting with Phase 1: Layout & Basic Navigation.
