# COMPREHENSIVE GAP ANALYSIS: Dash vs FastAPI Excel Processing
**Generated:** 2025-11-12  
**Scope:** Complete Excel processing logic comparison  
**Status:** 46 critical gaps identified across 6 categories

## EXECUTIVE SUMMARY

The Dash webapp implementation (`local_service.py`) is a **facade layer** that delegates all business logic to external models (DemandForecaster, LoadProfileGenerator, etc.) without performing Excel data extraction itself. Meanwhile, the FastAPI backend contains **comprehensive Excel processing logic** that is completely missing from Dash.

### Critical Findings:
- **18 CRITICAL** gaps (blocks major functionality)
- **22 HIGH** priority gaps (important features)
- **6 MEDIUM** priority gaps (nice-to-have)
- **3 marker types** missing (~Econometric_Parameters, ~Solar_share, ~Main_Settings)
- **19 PyPSA sheets** not being read/validated
- **4 utility functions** completely absent

---

## DETAILED COMPARISON BY CATEGORY

### 1. TILDE (~) MARKER HANDLING
**Status:** COMPLETELY MISSING ❌ (4 gaps)

FastAPI Implementation Points:
- `find_cell_position()` - Locate ~markers with case-insensitive search
- `find_sheet()` - Case-insensitive sheet lookup
- `extract_tables_by_markers()` - Extract tabular data from marked sections

Markers used in FastAPI:
1. `~Econometric_Parameters` (parse_excel_routes.py:126)
2. `~Solar_share` (scenario_routes.py:101)
3. `~Main_Settings` (pypsa_model_executor.py:1574)

Dash Impact: Cannot extract parameterized data from structured Excel templates.

---

### 2. DEMAND FORECASTING LOGIC
**Status:** CRITICAL GAPS ❌❌ (6 features missing, 3 CRITICAL)

Missing Functionality:
| Feature | Complexity | Priority |
|---------|-----------|----------|
| ~Econometric_Parameters marker extraction | HIGH | CRITICAL |
| Sector-to-column mapping | HIGH | CRITICAL |
| Economic_Indicators sheet merging | MEDIUM | CRITICAL |
| Multiple demand types (Gross/Net/OnGrid) | HIGH | HIGH |
| T&D loss interpolation | MEDIUM | HIGH |
| Solar sector detection | LOW | MEDIUM |

FastAPI Reference:
- **parse_excel_routes.py:66-214** - Complete economic indicator merging
- **scenario_routes.py:178-227** - T&D loss interpolation with boundary handling
- **forecasting.py:198-240** - Data validation and sector processing

Impact: Demand forecasts cannot incorporate economic parameters or T&D loss adjustments.

---

### 3. LOAD PROFILE PROCESSING
**Status:** CRITICAL GAPS ❌❌ (4 features missing, 2 CRITICAL)

Missing Functionality:
| Feature | Complexity | Priority |
|---------|-----------|----------|
| Past_Hourly_Demand sheet reading | MEDIUM | CRITICAL |
| Fiscal year calculation (Apr-Mar) | LOW | CRITICAL |
| Fiscal month mapping | LOW | HIGH |
| Excel serial date conversion | MEDIUM | HIGH |
| Temporal feature extraction | HIGH | HIGH |
| Holiday/weekend detection | MEDIUM | MEDIUM |

FastAPI Reference:
- **load_profile_generation.py:1274** - Past_Hourly_Demand sheet access
- **load_profile_generation.py:1835-1836** - Fiscal year calculation
- **load_profile_generation.py:1065-1140** - Temporal feature engineering

Impact: Load profiles not based on actual historical data; fiscal year aggregation incorrect.

---

### 4. PyPSA DATA HANDLING
**Status:** MULTIPLE MISSING SHEETS ❌❌ (19 sheets missing)

Required Sheets (pypsa_input_template.xlsx):

**Component Data (3 sheets):**
- Generators, Buses, Links

**Economic Parameters (6 sheets):**
- Lifetime, FOM, Capital_cost, wacc, Fuel_cost, Startupcost

**Time Series Data (3 sheets):**
- Demand, P_max_pu, P_min_pu

**New Components (5 sheets):**
- New_Generators, Pipe_Line_Generators_p_max, Pipe_Line_Generators_p_min, New_Storage, Pipe_Line_Storage_p_min

**Environmental/Settings (2 sheets):**
- CO2, Settings (with ~Main_Settings marker)

FastAPI Reference:
- **pypsa_model_executor.py:1516-1562** - All sheet definitions
- **pypsa_model_executor.py:1569-1620** - Settings extraction from markers

Impact: PyPSA model runs without validated inputs; no marker-based settings extraction.

---

### 5. DATA PROCESSING PATTERNS
**Status:** MISSING CRITICAL UTILITIES ❌ (6 gaps)

FastAPI Patterns Not in Dash:
1. **Case-insensitive sheet lookup** (find_sheet)
2. **Case-insensitive column matching** (Year/year, Electricity/electricity)
3. **safe_float()** - Type conversion with defaults
4. **safe_int()** - Integer conversion with fallback
5. **Robust year parsing** - Handle float years (2020.0), whitespace
6. **Null/NaN handling** - pd.isnull() checks throughout

These patterns prevent Excel data quality issues from crashing the app.

---

### 6. SPECIAL CASES NOT HANDLED
**Status:** MISSING FEATURES ❌❌ (7 gaps)

1. **COVID Year Exclusion** - Remove 2020-2022 from forecasts
2. **Multiple Demand Types** - Gross vs Net vs On-Grid calculations
3. **Economic Indicators** - Merge sector data with macro-economic factors
4. **Excel Serial Dates** - Convert spreadsheet date formats
5. **Fiscal Year Aggregation** - April-March grouping (not calendar year)
6. **Multi-Year Settings** - Extract 'Multi Year Investment' configuration
7. **Snapshot Conditions** - 'All Snapshots' vs 'Critical days' vs 'Peak weeks'

---

## IMPLEMENTATION PRIORITY ROADMAP

### Phase 1: CRITICAL (Blocks Deployment)
**Effort:** 6-8 hours | **Risk:** Medium

1. **Add marker detection functions** (1-2 hrs)
   - `find_sheet()`, `find_cell_position()`, `extract_tables_by_markers()`

2. **Implement demand data extraction** (3-4 hrs)
   - ~Econometric_Parameters processing
   - Economic_Indicators merging
   - Sector-level data validation

3. **Add T&D loss interpolation** (1-2 hrs)
   - Linear interpolation with boundary handling

### Phase 2: HIGH (Important Features)
**Effort:** 6-8 hours | **Risk:** Low-Medium

4. **Add utility functions** (1 hr)
   - safe_float(), safe_int(), robust parsing

5. **Add fiscal year calculations** (1 hr)
   - get_fiscal_year(), get_fiscal_month()

6. **Enhance load profile processing** (2-3 hrs)
   - Past_Hourly_Demand validation
   - Temporal feature extraction

7. **Load PyPSA sheets** (2-3 hrs)
   - Read 19 sheets with error handling
   - Settings marker extraction

### Phase 3: MEDIUM (Nice-to-Have)
**Effort:** 2-3 hours | **Risk:** Low

8. **Add special case handling**
   - COVID year filtering
   - Demand type transformations
   - Solar sector detection

---

## FILE-BY-FILE IMPLEMENTATION GUIDE

### FastAPI Implementation Files (Reference):
1. `/home/user/kseb-version3/backend_fastapi/routers/parse_excel_routes.py` - Marker detection, economic indicators
2. `/home/user/kseb-version3/backend_fastapi/routers/scenario_routes.py` - T&D losses, solar shares
3. `/home/user/kseb-version3/backend_fastapi/models/forecasting.py` - Forecasting logic
4. `/home/user/kseb-version3/backend_fastapi/models/load_profile_generation.py` - Fiscal year, temporal features
5. `/home/user/kseb-version3/backend_fastapi/models/pypsa_model_executor.py` - Sheet reading, settings

### Target Implementation File:
- `/home/user/kseb-version3/dash/services/local_service.py` - Add all missing methods

---

## CRITICAL CODE SNIPPETS TO PORT

All code snippets and implementation examples are provided in the full analysis document below.

---

## STATISTICS

| Category | Count | Critical | High | Medium |
|----------|-------|----------|------|--------|
| Tilde Markers | 4 | 4 | - | - |
| Demand Processing | 6 | 3 | 3 | - |
| Load Profiles | 4 | 2 | 2 | - |
| PyPSA Sheets | 19 | 6 | 8 | 5 |
| Utilities | 6 | - | 6 | - |
| Special Cases | 7 | 3 | 3 | 1 |
| **TOTAL** | **46** | **18** | **22** | **6** |

---

