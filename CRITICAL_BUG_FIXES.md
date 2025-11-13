# Critical Bug Fixes Required - Dash Webapp
## Comprehensive Issue List and Solutions

**Date**: 2025-11-13
**Priority**: HIGH - Production Blockers

---

## ✅ ISSUE 1: AttributeError - LocalService has no 'base_url'

**Location**: `dash/pages/demand_projection.py:1617`

**Error**:
```
AttributeError: 'LocalService' object has no attribute 'base_url'
```

**Root Cause**: LocalService doesn't have a base_url attribute (FastAPI API client does, but not LocalService)

**Fix**: ✅ COMPLETED
```python
# BEFORE (Line 1617):
sse_url = f'{api.base_url}/project/forecast-progress'

# AFTER:
sse_url = api.get_forecast_status_url()
```

**Status**: ✅ FIXED

---

## ⚠️ ISSUE 2: Unit Conversion Errors

**Location**: `dash/pages/demand_visualization.py` (multiple locations)

**Error**:
```
Error rendering table: can't multiply sequence by non-int of type 'float'
```

**Root Cause**: Data values are strings, not numbers. Unit conversion trying to multiply strings.

**Analysis**: When reading from Excel or calculating values, they're being stored as strings instead of numeric types.

**Fix Required**:

### A. Add safe numeric conversion helper:
```python
def safe_numeric(value):
    """Convert value to float safely"""
    if value is None or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            # Remove commas if present
            cleaned = value.replace(',', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return 0.0
    return 0.0
```

### B. Update unit conversion functions:
```python
def convert_unit(value, from_unit, to_unit):
    """Convert energy units with safe numeric handling"""
    # Convert to numeric
    numeric_value = safe_numeric(value)

    # MWh as base unit
    if from_unit == 'MWh':
        if to_unit == 'GWh':
            return numeric_value / 1000
        elif to_unit == 'TWh':
            return numeric_value / 1_000_000
        elif to_unit == 'kWh':
            return numeric_value * 1000

    # Add conversions from other units
    elif from_unit == 'GWh':
        if to_unit == 'MWh':
            return numeric_value * 1000
        elif to_unit == 'TWh':
            return numeric_value / 1000
        elif to_unit == 'kWh':
            return numeric_value * 1_000_000

    return numeric_value
```

### C. Apply conversion in data loading:
```python
# When loading scenario data
for row in data:
    for key in row:
        if key != 'Year' and isinstance(row[key], str):
            row[key] = safe_numeric(row[key])
```

**Files to Modify**:
1. `dash/pages/demand_visualization.py` - Add helper functions
2. All data loading callbacks - Convert strings to numbers

---

## ⚠️ ISSUE 3: MLR Parameters Not Dynamic

**Location**: `dash/pages/demand_projection.py` - Configure Forecast modal

**Current Behavior**: MLR parameters are hardcoded or not based on sector correlations

**Expected Behavior**: Should show economic indicators with strong correlation (>0.5) for each sector

**Fix Required**:

### A. Fetch correlation data when sector is selected:
```python
@callback(
    Output('mlr-parameters-container', 'children'),
    Input('sector-selector', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def update_mlr_parameters(sector_name, active_project):
    if not sector_name or not active_project:
        return []

    # Get sector data with economic indicators
    sector_data = api.extract_sector_data({
        'projectPath': active_project['path'],
        'sectorName': sector_name
    })

    if not sector_data.get('success'):
        return []

    # Calculate correlations
    correlation_result = api.get_sector_correlation({
        'projectPath': active_project['path'],
        'data': sector_data['data']
    })

    if not correlation_result.get('success'):
        return []

    # Filter indicators with strong correlation (>0.5)
    correlations = correlation_result.get('correlations', [])
    strong_correlations = [
        c for c in correlations
        if abs(c['correlation']) > 0.5 and c['variable'] != 'Electricity'
    ]

    # Create checkboxes for each strong indicator
    return dbc.Checklist(
        id='mlr-parameters-checklist',
        options=[
            {
                'label': f"{item['variable']} (r={item['correlation']:.3f})",
                'value': item['variable']
            }
            for item in strong_correlations
        ],
        value=[item['variable'] for item in strong_correlations],  # Pre-select all
        inline=False
    )
```

### B. Update forecast configuration to use selected parameters:
```python
# In forecast configuration builder
for sector in selected_sectors:
    # Get MLR parameters for this sector
    mlr_params = mlr_parameters_state.get(sector['name'], [])

    sector_configs.append({
        'name': sector['name'],
        'selected_methods': sector['methods'],
        'mlr_parameters': mlr_params,  # Dynamic based on correlation
        'wam_window': sector.get('wam_window', 10),
        'data': sector['data']
    })
```

**Files to Modify**:
1. `dash/pages/demand_projection.py` - Add correlation-based parameter selection
2. Add per-sector MLR parameter configuration

---

## ⚠️ ISSUE 4: No Scenarios Showing in Demand Visualization

**Location**: `dash/pages/demand_visualization.py`

**Current Behavior**: Scenario dropdown shows "Select scenario..." but no options

**Root Cause**: Scenarios not being loaded or callback not triggering

**Fix Required**:

### A. Check scenario loading callback:
```python
@callback(
    Output('scenario-dropdown', 'options'),
    Output('scenario-dropdown', 'value'),
    Input('active-project-store', 'data'),
    prevent_initial_call=False  # Load on page mount
)
def load_scenarios(active_project):
    if not active_project:
        return [], None

    # Get scenarios
    result = api.get_scenarios(active_project['path'])

    if not result.get('success') or not result.get('scenarios'):
        return [], None

    scenarios = result['scenarios']
    options = [{'label': s, 'value': s} for s in scenarios]

    # Auto-select first scenario
    default_value = scenarios[0] if scenarios else None

    return options, default_value
```

### B. Verify scenario folder structure:
```python
# In local_service.py - get_scenarios()
def get_scenarios(self, project_path: str) -> Dict:
    """List all forecast scenarios"""
    try:
        scenarios_dir = Path(project_path) / 'results' / 'demand_forecasts'

        if not scenarios_dir.exists():
            return {'success': True, 'scenarios': []}

        # Get all directories in demand_forecasts
        scenarios = [
            d.name for d in scenarios_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        return {'success': True, 'scenarios': sorted(scenarios)}

    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        return {'success': False, 'error': str(e), 'scenarios': []}
```

**Files to Modify**:
1. `dash/pages/demand_visualization.py` - Fix scenario loading callback
2. `dash/services/local_service.py` - Verify get_scenarios() implementation

---

## ⚠️ ISSUE 5: Base Year Dropdown Not Showing in Load Profile Generation

**Location**: `dash/pages/generate_profiles.py`

**Current Behavior**: When selecting "Base Profile Method", base year dropdown doesn't appear

**Root Cause**: Conditional rendering not working or callback not triggering

**Fix Required**:

### A. Update method selection callback:
```python
@callback(
    Output('base-year-container', 'style'),
    Output('base-year-select', 'options'),
    Input('method-radio', 'value'),
    State('available-base-years', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=False
)
def update_base_year_visibility(selected_method, cached_years, active_project):
    if selected_method == 'base':
        # Show base year dropdown
        style = {'display': 'block'}

        # Load available base years if not cached
        if not cached_years and active_project:
            result = api.get_available_base_years(active_project['path'])
            years = result.get('years', [])
            options = [{'label': y, 'value': y} for y in years]
        else:
            options = [{'label': y, 'value': y} for y in (cached_years or [])]

        return style, options
    else:
        # Hide base year dropdown for STL method
        return {'display': 'none'}, []
```

### B. Verify radio button IDs match:
```python
# In layout, method selection should be:
dbc.RadioItems(
    id='method-radio',
    options=[
        {'label': 'Base Profile Method', 'value': 'base'},
        {'label': 'STL Decomposition', 'value': 'stl'}
    ],
    value=None,  # No default selection
    inline=False
)
```

**Files to Modify**:
1. `dash/pages/generate_profiles.py` - Fix conditional rendering
2. Ensure base year dropdown has correct parent container ID

---

## ⚠️ ISSUE 6: Both Methods Selected at Same Time

**Location**: `dash/pages/generate_profiles.py` - Method selection

**Current Behavior**: Both "Base Profile" and "STL Decomposition" can be selected simultaneously

**Root Cause**: Using Checklist instead of RadioItems, or multiple selection enabled

**Fix Required**:

### Ensure RadioItems (not Checklist):
```python
# Method selection (MUST be RadioItems for single selection)
dbc.RadioItems(
    id='method-radio',
    options=[
        {'label': '📊 Base Profile Method', 'value': 'base'},
        {'label': '📈 STL Decomposition', 'value': 'stl'}
    ],
    value=None,  # Force user to select
    inline=False,
    labelStyle={'display': 'block', 'marginBottom': '0.5rem'}
)
```

**Note**: If using dbc.RadioItems, only one can be selected. If both appear selected, check CSS or state management.

**Files to Modify**:
1. `dash/pages/generate_profiles.py` - Verify RadioItems component

---

## ⚠️ ISSUE 7: No Profile/Scenario Dropdowns in Analyze Profiles

**Location**: `dash/pages/analyze_profiles.py`

**Current Behavior**: Dropdowns show "Select..." but no options

**Root Cause**: Profiles not being loaded or wrong directory path

**Fix Required**:

### A. Update profile loading:
```python
@callback(
    Output('profile-dropdown', 'options'),
    Output('profile-dropdown', 'value'),
    Input('active-project-store', 'data'),
    prevent_initial_call=False
)
def load_profiles(active_project):
    if not active_project:
        return [], None

    # Get load profiles
    result = api.get_load_profiles(active_project['path'])

    if not result or 'profiles' not in result:
        return [], None

    profiles = result['profiles']

    if not profiles:
        return [], None

    options = [{'label': p, 'value': p} for p in profiles]
    default_value = profiles[0] if profiles else None

    return options, default_value
```

### B. Verify directory structure:
```python
# In local_service.py - get_load_profiles()
def get_load_profiles(self, project_path: str) -> Dict:
    """List all load profile directories"""
    try:
        profiles_dir = Path(project_path) / 'results' / 'load_profiles'

        if not profiles_dir.exists():
            return {'profiles': []}

        # Get all directories (each profile is a folder)
        profiles = [
            d.name for d in profiles_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        return {'profiles': sorted(profiles)}

    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        return {'profiles': []}
```

**Files to Modify**:
1. `dash/pages/analyze_profiles.py` - Fix profile loading
2. `dash/services/local_service.py` - Verify get_load_profiles()

---

## ⚠️ ISSUE 8: PyPSA Config Page - Can't Run Model

**Location**: `dash/pages/model_config.py`

**Current Behavior**: "Apply Configuration & Run Model" button doesn't work

**Root Cause**: Missing callback or run_pypsa_model() not properly implemented

**Fix Required**:

### A. Verify run button callback:
```python
@callback(
    Output('pypsa-process-state', 'data'),
    Output('pypsa-progress-interval', 'disabled'),
    Output('pypsa-config-state', 'data'),
    Input('run-model-btn', 'n_clicks'),
    State('scenario-name-input', 'value'),
    State('solver-dropdown', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def run_pypsa_model(n_clicks, scenario_name, solver, active_project):
    if not n_clicks or not scenario_name or not active_project:
        raise PreventUpdate

    # Apply configuration first
    config_result = api.apply_pypsa_configuration({
        'projectPath': active_project['path'],
        'scenarioName': scenario_name,
        'solver': solver or 'highs'
    })

    if not config_result.get('success'):
        return {
            'status': 'failed',
            'error': config_result.get('error', 'Configuration failed')
        }, True, no_update

    # Run model
    result = api.run_pypsa_model({
        'projectPath': active_project['path'],
        'scenarioName': scenario_name
    })

    if result.get('success'):
        return {
            'status': 'running',
            'message': 'Model execution started',
            'progress': 0
        }, False, {'scenario': scenario_name}
    else:
        return {
            'status': 'failed',
            'error': result.get('error', 'Failed to start model')
        }, True, no_update
```

### B. Verify local_service.py implementation:
```python
def run_pypsa_model(self, config: Dict) -> Dict:
    """Execute PyPSA model"""
    try:
        from models.pypsa_model_executor import PyPSAModelExecutor

        project_path = config['projectPath']
        scenario_name = config['scenarioName']

        # Initialize executor
        executor = PyPSAModelExecutor(project_path, scenario_name)

        # Run model in background thread
        thread = threading.Thread(
            target=executor.run,
            daemon=True
        )
        thread.start()

        return {
            'success': True,
            'message': 'Model execution started',
            'scenario': scenario_name
        }

    except Exception as e:
        logger.error(f"Error running PyPSA model: {e}")
        return {'success': False, 'error': str(e)}
```

**Files to Modify**:
1. `dash/pages/model_config.py` - Fix run button callback
2. `dash/services/local_service.py` - Implement run_pypsa_model()

---

## ⚠️ ISSUE 9: PyPSA Visualization - No Scenario Selection

**Location**: `dash/pages/view_results.py`

**Current Behavior**: No scenarios showing in dropdown for results/pypsa_optimization

**Root Cause**: Similar to Issue 4 - scenarios not being loaded

**Fix Required**:

### Update scenario loading for PyPSA:
```python
@callback(
    Output('pypsa-scenario-dropdown', 'options'),
    Output('pypsa-scenario-dropdown', 'value'),
    Input('active-project-store', 'data'),
    prevent_initial_call=False
)
def load_pypsa_scenarios(active_project):
    if not active_project:
        return [], None

    # Get PyPSA scenarios
    result = api.get_pypsa_scenarios(active_project['path'])

    if not result.get('success') or not result.get('scenarios'):
        return [], None

    scenarios = result['scenarios']
    options = [{'label': s, 'value': s} for s in scenarios]
    default_value = scenarios[0] if scenarios else None

    return options, default_value
```

**Files to Modify**:
1. `dash/pages/view_results.py` - Add scenario loading callback
2. Verify `get_pypsa_scenarios()` in local_service.py

---

## ⚠️ ISSUE 10: Color Picker Input Type Error

**Location**: Multiple pages (settings, demand_visualization)

**Error**:
```
Invalid argument `type` passed into Input.
Expected one of ["text","number","password",...].
Value provided: "color"
```

**Root Cause**: Dash dcc.Input doesn't support `type="color"` - need to use dbc.Input or HTML input

**Fix Required**:

### Replace dcc.Input with HTML color input:
```python
# BEFORE (doesn't work):
dcc.Input(
    id={'type': 'model-color-picker', 'index': model},
    type='color',  # ❌ Not supported by dcc.Input
    value=color
)

# AFTER (works):
html.Input(
    id={'type': 'model-color-picker', 'index': model},
    type='color',  # ✅ HTML input supports color type
    value=color,
    style={'width': '50px', 'height': '30px', 'border': 'none', 'cursor': 'pointer'}
)
```

**Alternative**: Use dbc.Input if available:
```python
dbc.Input(
    id={'type': 'model-color-picker', 'index': model},
    type='color',
    value=color,
    style={'width': '50px', 'height': '30px'}
)
```

**Files to Modify**:
1. `dash/pages/settings_page.py` - Replace color inputs
2. `dash/pages/demand_visualization.py` - Replace color inputs
3. Any other pages with color pickers

---

## ⚠️ ISSUE 11: Missing source-radio Callback Errors

**Error**:
```
A nonexistent object was used in an `Input` of a Dash callback.
The id of this object is `source-radio` and the property is `value`.
```

**Root Cause**: Callback referencing `source-radio` ID that doesn't exist in layout

**Fix Required**:

### A. Find and remove orphaned callback:
```bash
# Search for source-radio in all pages
grep -r "source-radio" dash/pages/
```

### B. Either add the component or remove the callback:
```python
# Option 1: Add missing component
dbc.RadioItems(
    id='source-radio',
    options=[...],
    value=None
)

# Option 2: Remove callback that references it
# Delete or comment out the callback using Input('source-radio', 'value')
```

**Files to Modify**:
1. Search all files for 'source-radio' references
2. Remove orphaned callbacks or add missing components

---

## ⚠️ ISSUE 12: Unit Conversion Not Applied to Sector-Wise View

**Location**: `dash/pages/demand_visualization.py` - Sector view tables

**Current Behavior**: Unit conversion only works in consolidated view

**Fix Required**:

### Apply unit conversion in all views:
```python
def apply_unit_conversion_to_data(data, unit='MWh'):
    """Apply unit conversion to all numeric columns except Year"""
    converted_data = []

    for row in data:
        converted_row = {'Year': row['Year']}
        for key, value in row.items():
            if key != 'Year':
                numeric_value = safe_numeric(value)
                converted_value = convert_unit(numeric_value, 'MWh', unit)
                converted_row[key] = round(converted_value, 2)

        converted_data.append(converted_row)

    return converted_data

# Use in both consolidated and sector-specific callbacks
@callback(
    Output('sector-data-table', 'data'),
    Input('unit-dropdown', 'value'),
    State('raw-sector-data', 'data')
)
def update_sector_table(selected_unit, raw_data):
    if not raw_data:
        return []

    # Apply conversion
    converted = apply_unit_conversion_to_data(raw_data, selected_unit)
    return converted
```

**Files to Modify**:
1. `dash/pages/demand_visualization.py` - Apply to sector view callbacks
2. Ensure all electricity values go through conversion

---

## 📋 SUMMARY OF FILES TO MODIFY

### Critical Priority (Blockers):
1. ✅ `dash/pages/demand_projection.py` - Fixed base_url issue
2. ⚠️ `dash/pages/demand_visualization.py` - Unit conversion fixes
3. ⚠️ `dash/pages/generate_profiles.py` - Method selection, base year dropdown
4. ⚠️ `dash/pages/analyze_profiles.py` - Profile loading
5. ⚠️ `dash/pages/model_config.py` - Run model functionality
6. ⚠️ `dash/pages/view_results.py` - Scenario loading
7. ⚠️ `dash/pages/settings_page.py` - Color picker fix
8. ⚠️ `dash/services/local_service.py` - Verify all API methods

### Implementation Order:
1. **Phase 1** (Immediate): Fix all callback errors and missing components
2. **Phase 2** (High): Fix dropdown loading issues (scenarios, profiles)
3. **Phase 3** (High): Fix unit conversion throughout
4. **Phase 4** (Medium): Make MLR parameters dynamic
5. **Phase 5** (Medium): Fix PyPSA execution

---

## 🎯 TESTING CHECKLIST

After implementing fixes, test:
- [ ] Create project → Templates copied
- [ ] Run demand forecast → SSE progress works
- [ ] View demand visualization → Scenarios load, unit conversion works
- [ ] Generate load profile → Method selection works, base year shows
- [ ] Analyze profiles → Profiles load, all tabs work
- [ ] Run PyPSA model → Model executes, progress shows
- [ ] View PyPSA results → Scenarios load, all tabs work
- [ ] Change colors → Color pickers work
- [ ] No console errors or callback warnings

---

**Document Created**: 2025-11-13
**Total Issues**: 12 critical bugs
**Fixed**: 1
**Remaining**: 11
**Estimated Fix Time**: 6-8 hours for complete implementation
