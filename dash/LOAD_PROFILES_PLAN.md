# Load Profiles - Implementation Plan

## Overview
Complete Plotly Dash implementation matching React Load Profiles module (2,000 lines total)

**Two Main Pages:**
1. **Generate Profiles** (GenerateProfiles.jsx - 426 lines)
2. **Analyze Profiles** (AnalyzeProfiles.jsx - 1,567 lines)

---

## PAGE 1: Generate Profiles - Implementation Plan

### Features Breakdown

#### 1. 4-Step Wizard Flow (Priority: HIGH)
**Components:**
- Step indicator with progress
- Step 1: Method & Timeframe
- Step 2: Data Source
- Step 3: Constraints
- Step 4: Review & Generate
- Navigation buttons (Back/Next/Generate)

**State Required:**
- Current step (1-4)
- Profile name
- Start year / End year
- Selected method (base/stl)
- Base year (for base method)
- Demand source (template/projection)
- Projection scenario
- Monthly constraint (auto/excel/none)
- Validation errors

**Validation:**
- Step 1: Name valid, years valid, method selected, base year selected if needed
- Step 2: Source selected, scenario selected if needed
- Step 3: Constraint method selected

---

#### 2. Step 1: Method & Timeframe (Priority: HIGH)
**Features:**
- Profile name input with existence check
- Start/End year inputs
- Method selection cards:
  - Base Profile Method (with base year dropdown)
  - STL Decomposition Method
- Real-time validation feedback
- Expandable base year selector

**API Endpoints:**
- `GET /project/available-base-years?projectPath=X` - Get available base years
- `GET /project/check-profile-exists?projectPath=X&profileName=Y` - Check if profile exists

**Validation:**
- Profile name: Required, unique check
- Years: Required, valid range
- Method: Required
- Base year: Required if base method selected

---

#### 3. Step 2: Data Source (Priority: HIGH)
**Features:**
- Two source options:
  - Use 'Total Demand' sheet from Excel
  - Use demand projection scenario
- Scenario selector dropdown (loads scenarios dynamically)
- Expandable controls when scenario source selected

**API Endpoints:**
- `GET /project/available-scenarios?projectPath=X` - Get scenarios list

---

#### 4. Step 3: Constraints (Priority: HIGH)
**Features:**
- Three constraint options (radio buttons):
  - Auto-calculate from base year
  - Use constraints from Excel file
  - No monthly constraints
- Option descriptions

---

#### 5. Step 4: Review & Generate (Priority: HIGH)
**Features:**
- Summary display showing all selections
- Grid layout with all configuration details
- Generate button
- Process modal with progress tracking

**Display Fields:**
- Profile Name
- Timeframe (start - end)
- Generation Method
- Base Profile Year (if applicable)
- Total Demand Source
- Projection Scenario (if applicable)
- Monthly Constraints method

---

#### 6. Process Tracking with SSE (Priority: HIGH)
**Features:**
- Start generation via POST endpoint
- SSE connection for real-time updates
- Progress modal with:
  - Percentage progress bar
  - Current task message
  - Task progress (e.g., "5/10 years")
  - Process logs with timestamps
  - Minimize/maximize functionality
  - Floating indicator when minimized
- Success/failure handling
- Auto-navigation to Analyze on completion

**API Endpoints:**
- `POST /project/generate-profile` - Start generation
- `GET /project/generation-status` - SSE endpoint for progress

**SSE Message Parsing:**
- PROGRESS: JSON with percentage and message
- YEAR_PROGRESS: Processing FY{year} ({current}/{total})
- GENERATION COMPLETE: Success marker
- FAILED/ERROR: Failure markers

---

### File Structure

```
dash/pages/
├── load_profiles_generate.py   # Generate Profiles page (Est. 500-600 lines)
```

---

### Implementation Order (Generate Profiles)

**Part 1: Wizard Layout & State (150 lines)**
- [ ] Main wizard layout with stepper
- [ ] State stores (profile config, validation)
- [ ] Step navigation logic
- [ ] Footer with Back/Next/Generate buttons

**Part 2: Step 1 - Method & Timeframe (150 lines)**
- [ ] Profile name input with debounced validation
- [ ] Year inputs
- [ ] Method selection cards (base/stl)
- [ ] Base year dropdown with dynamic loading
- [ ] Step validation logic

**Part 3: Step 2 - Data Source (100 lines)**
- [ ] Source selection cards
- [ ] Scenario selector with dynamic loading
- [ ] Conditional rendering based on source

**Part 4: Step 3 & 4 - Constraints & Review (100 lines)**
- [ ] Constraint radio options
- [ ] Review summary grid
- [ ] Final validation before generation

**Part 5: Process Tracking (150 lines)**
- [ ] Generate button handler
- [ ] SSE connection setup
- [ ] Progress modal integration
- [ ] Log parsing and display
- [ ] Success/failure handling
- [ ] Navigation to Analyze page

---

## PAGE 2: Analyze Profiles - Implementation Plan

### Features Breakdown

#### 1. Main Layout & Controls (Priority: HIGH)
**Components:**
- Profile selector dropdown (loads from backend)
- Period selector (Overall + individual fiscal years)
- Tab navigation (6 tabs)
- Main content area

**State Required (Per Profile):**
- Selected profile name
- Available years
- Selected year/period
- Active tab
- Tab-specific state (date range, month, season)

**Zustand Store Replacement:**
- Use dcc.Store with localStorage/sessionStorage
- Nested state per profile
- Profile-specific state persistence

---

#### 2. Tab 1: Overview Dashboard (Priority: HIGH)
**Features:**
- Monthly Analysis heatmap
  - Parameter selector dropdown
  - Color picker (low/high)
  - ApexCharts heatmap with month labels (Jan-Dec)
  - Row-wise normalization
  - Data labels with original values
- Seasonal Analysis heatmap
  - Same features as monthly
  - Season labels (Monsoon, Post-monsoon, Winter, Summer)

**API Endpoints:**
- `GET /project/analysis-data?projectPath=X&profileName=Y&sheetName=Monthly_analysis`
- `GET /project/analysis-data?projectPath=X&profileName=Y&sheetName=Season_analysis`

**Charts:**
- ApexCharts Heatmap (using plotly equivalent or custom implementation)
- Color interpolation function
- Dynamic categories (months/seasons)

---

#### 3. Tab 2: Time Series Analysis (Priority: HIGH)
**Features:**
- Date range picker (DayPicker equivalent in Dash)
- Hourly demand line chart with brush zoom
- Max/Min/Average demand chart for selected range
- Custom tooltips

**API Endpoints:**
- `GET /project/full-load-profile?projectPath=X&profileName=Y&fiscalYear=FY2023`

**Charts:**
- Recharts-equivalent line chart with brush
- ApexCharts line chart for max/min/avg

**Requires:**
- Fiscal year selection (not "Overall")
- Date range within fiscal year bounds

---

#### 4. Tab 3: Month-wise Analysis (Priority: HIGH)
**Features:**
- Month selector dropdown (Apr-Mar)
- Hourly demand line chart for selected month
- Max/Min/Average demand chart for month
- Brush zoom functionality

**Uses:**
- Same API as Time Series
- Filter data by selected month

---

#### 5. Tab 4: Season-wise Analysis (Priority: HIGH)
**Features:**
- Season selector dropdown (Monsoon/Post-monsoon/Winter/Summer)
- Hourly demand line chart for season
- Max/Min/Average demand chart for season
- Brush zoom functionality

**Season Mapping:**
- Monsoon: Jul, Aug, Sep (7, 8, 9)
- Post-monsoon: Oct, Nov (10, 11)
- Winter: Dec, Jan, Feb (12, 1, 2)
- Summer: Mar, Apr, May, Jun (3, 4, 5, 6)

---

#### 6. Tab 5: Day-type Analysis (Priority: HIGH)
**Features:**
- Average hourly demand by day type chart
- Three series: Holiday, Weekday, Weekend
- 24-hour comparison
- Computed from full year data

**Calculation:**
- Group by hour (0-23)
- Separate by is_holiday, is_weekend flags
- Calculate averages per hour per type

---

#### 7. Tab 6: Load Duration Curve (Priority: HIGH)
**Features:**
- Area chart with demand on Y-axis, percent time on X-axis
- Gradient fill
- Annotations at 5% and 95% marks
- Zoom and pan tools
- Custom tooltip

**API Endpoints:**
- `GET /project/load-duration-curve?projectPath=X&profileName=Y&fiscalYear=FY2023`

**Chart:**
- ApexCharts area chart (or Plotly equivalent)
- X-axis: Percent Time (0-100%)
- Y-axis: Demand (MW)

---

#### 8. State Management (Priority: HIGH)
**Approach:**
- Single dcc.Store for analyze-profiles-state
- Nested structure: `{ profileName: { selectedYear, activeTab, dateRange, ... } }`
- Per-profile state isolation
- LocalStorage persistence

**State Schema:**
```python
{
    'selectedProfile': 'profile1',
    'availableProfiles': ['profile1', 'profile2'],
    'profilesState': {
        'profile1': {
            'selectedYear': 'FY2023',
            'availableYears': ['Overall', 'FY2023', 'FY2024'],
            'activeTab': 'Overview',
            'dateRange': {'from': '2023-04-01', 'to': '2023-04-07'},
            'selectedMonth': 4,
            'selectedSeason': 'Monsoon',
            'overviewMonthlyParam': 'Peak Demand',
            'overviewSeasonalParam': 'Peak Demand',
            'overviewMonthlyLowColor': '#cfd4e3',
            'overviewMonthlyHighColor': '#252323',
            'overviewSeasonalLowColor': '#cfd4e3',
            'overviewSeasonalHighColor': '#252323'
        }
    }
}
```

---

### Callbacks Summary (Analyze Profiles - Est. 25-30 callbacks)

**Profile & Year Management:**
1. `load_profiles_list` - Fetch available profiles
2. `load_profile_years` - Fetch years for selected profile
3. `update_selected_profile` - Change profile
4. `update_selected_year` - Change year/period

**Tab Navigation:**
5. `render_tab_content` - Render active tab content

**Overview Tab:**
6. `load_monthly_analysis_data` - Fetch monthly heatmap data
7. `load_seasonal_analysis_data` - Fetch seasonal heatmap data
8. `render_monthly_heatmap` - Render monthly heatmap
9. `render_seasonal_heatmap` - Render seasonal heatmap
10. `update_monthly_param` - Change monthly parameter
11. `update_seasonal_param` - Change seasonal parameter
12. `update_monthly_colors` - Change monthly colors
13. `update_seasonal_colors` - Change seasonal colors

**Time Series Tab:**
14. `load_full_year_data` - Fetch full load profile
15. `render_time_series_chart` - Main time series line chart
16. `render_time_series_max_min_avg` - Max/min/avg chart
17. `update_date_range` - Change date range

**Month-wise Tab:**
18. `update_selected_month` - Change month
19. `render_month_wise_chart` - Month-specific chart
20. `render_month_wise_max_min_avg` - Month max/min/avg

**Season-wise Tab:**
21. `update_selected_season` - Change season
22. `render_season_wise_chart` - Season-specific chart
23. `render_season_wise_max_min_avg` - Season max/min/avg

**Day-type Tab:**
24. `render_day_type_chart` - Day type analysis chart

**Load Duration Tab:**
25. `load_load_duration_data` - Fetch load duration curve data
26. `render_load_duration_chart` - Render load duration curve

**State Sync:**
27. `sync_state_to_storage` - Persist state changes

---

### File Structure

```
dash/pages/
├── load_profiles_analyze.py    # Analyze Profiles page (Est. 1,800-2,000 lines)
```

---

### Implementation Order (Analyze Profiles)

**Phase 1: Layout & Profile Management (200 lines)**
- [ ] Main layout with profile selector
- [ ] Period selector
- [ ] Tab navigation
- [ ] State stores setup
- [ ] Profile/year loading callbacks

**Phase 2: Overview Tab (350 lines)**
- [ ] Monthly analysis heatmap
- [ ] Seasonal analysis heatmap
- [ ] Parameter selectors
- [ ] Color pickers
- [ ] Data loading and rendering

**Phase 3: Time Series Tab (350 lines)**
- [ ] Date picker component
- [ ] Full year data loading
- [ ] Main line chart with brush
- [ ] Max/min/avg chart
- [ ] Date range filtering

**Phase 4: Month-wise & Season-wise Tabs (300 lines)**
- [ ] Month selector
- [ ] Season selector
- [ ] Filtered data calculations
- [ ] Charts with brush zoom
- [ ] Max/min/avg charts

**Phase 5: Day-type Tab (200 lines)**
- [ ] Day type calculation logic
- [ ] Hourly average computation
- [ ] Three-series chart (Holiday/Weekday/Weekend)

**Phase 6: Load Duration Tab (200 lines)**
- [ ] Load duration data loading
- [ ] Area chart with annotations
- [ ] 5% and 95% markers
- [ ] Tooltip customization

**Phase 7: State Persistence (200 lines)**
- [ ] State sync callbacks
- [ ] LocalStorage integration
- [ ] Per-profile state isolation

---

## Total Estimated Time

**Generate Profiles:** 8-12 hours
**Analyze Profiles:** 25-35 hours
**Testing & Polish:** 5-8 hours

**Total:** 38-55 hours

**React Code Size:** ~2,000 lines
**Expected Dash Size:** 2,300-2,600 lines

---

## Key Differences from React

- **Charts:** Plotly instead of ApexCharts/Recharts
- **Date Picker:** dcc.DatePickerRange instead of DayPicker
- **State:** dcc.Store instead of Zustand
- **SSE:** Dash doesn't support SSE natively - use dcc.Interval polling or websockets
- **Forms:** Dash Input/Dropdown instead of React controlled components

---

## Testing Checklist

Generate Profiles:
- [ ] Profile name validation works
- [ ] Base year loads dynamically
- [ ] Scenarios load for projection source
- [ ] Step validation prevents invalid progression
- [ ] Generation starts and tracks progress
- [ ] SSE updates display correctly
- [ ] Success navigates to Analyze
- [ ] Failure displays error

Analyze Profiles:
- [ ] Profiles load from backend
- [ ] Years load per profile
- [ ] State persists across navigation
- [ ] All 6 tabs render correctly
- [ ] Charts display with correct data
- [ ] Date range picker works
- [ ] Month/Season filters work
- [ ] Day-type calculation accurate
- [ ] Load duration curve displays
- [ ] State isolated per profile

---

**Ready to implement!** Starting with Generate Profiles, then Analyze Profiles.
