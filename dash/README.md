# KSEB Energy Analytics Platform - Dash Application

## Overview

This is a complete conversion of the KSEB Energy Analytics Platform from **React + FastAPI** to **Dash/Plotly Dash**. The application maintains all the original functionality while leveraging Dash's Python-based framework for both frontend and backend.

### Original Architecture (React + FastAPI)
- **Frontend**: React 19 (~10,938 LOC)
- **Backend**: FastAPI (~16,717 LOC)
- **Total**: ~27,655 lines of code
- **Communication**: REST API + Server-Sent Events (SSE)

### New Architecture (Dash)
- **Framework**: Dash + Plotly
- **Language**: 100% Python
- **Communication**: Dash callbacks (replacing REST API and SSE)
- **State Management**: dcc.Store components (replacing React state/Zustand)

---

## Features

### 1. Project Management
- Create new energy analytics projects
- Load existing projects
- Project validation and workspace management
- Folder structure:
  ```
  ProjectName/
  ├── inputs/               # Excel templates
  │   └── input_demand_file.xlsx
  │   └── load_curve_template.xlsx
  │   └── pypsa_input_template.xlsx
  └── results/
      ├── demand_forecasts/     # Forecast scenarios
      ├── load_profiles/        # Generated profiles
      └── pypsa_optimization/   # Grid optimization results
  ```

### 2. Demand Forecasting
- **Models**: Simple Linear Regression (SLR), Multiple Linear Regression (MLR), Weighted Average Method (WAM), Time Series
- **Features**:
  - Multi-sector forecasting
  - COVID year exclusion
  - Correlation analysis
  - Model comparison
  - T&D loss calculation
  - Solar share integration
  - Real-time progress tracking

### 3. Load Profile Generation
- **Methods**: Statistical profiling, historical pattern matching
- **Features**:
  - Hourly/sub-hourly profiles
  - Holiday detection
  - Seasonal adjustment
  - Peak demand identification
  - Heatmap visualization

### 4. PyPSA Grid Optimization Suite
- **Capabilities**:
  - Network optimization modeling
  - Multi-period optimization
  - Component analysis (generators, storage, lines, loads)
  - Dispatch analysis
  - Energy balance calculation
  - Curtailment analysis
  - Cost breakdown
- **Visualizations**:
  - Network topology maps
  - Dispatch stacked area charts
  - Capacity bar charts
  - Storage state of charge
  - Energy balance diagrams

### 5. Settings & Configuration
- Color configuration per sector/model
- Application preferences
- User settings persistence

---

## Installation

### Prerequisites
- Python 3.9+
- pip or conda

### Setup

1. **Navigate to the dash directory**:
   ```bash
   cd dash
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the app**:
   Open your browser to `http://localhost:8050`

---

## Project Structure

```
dash/
├── app.py                      # Main Dash application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── components/                 # Reusable UI components
│   ├── __init__.py
│   ├── sidebar.py             # Navigation sidebar
│   ├── topbar.py              # Header with project info
│   └── workflow_stepper.py    # Right sidebar workflow
│
├── pages/                      # Page layouts
│   ├── __init__.py
│   ├── home.py                # Dashboard/home page
│   ├── create_project.py      # Project creation
│   ├── load_project.py        # Project loading
│   ├── demand_projection.py   # Forecasting config
│   ├── demand_visualization.py # Forecast results
│   ├── generate_profiles.py   # Profile generation
│   ├── analyze_profiles.py    # Profile analysis
│   ├── model_config.py        # PyPSA configuration
│   ├── view_results.py        # PyPSA results
│   └── settings_page.py       # App settings
│
├── callbacks/                  # Dash callbacks (replacing REST API)
│   ├── __init__.py
│   ├── project_callbacks.py   # Project management
│   ├── forecast_callbacks.py  # Demand forecasting
│   ├── profile_callbacks.py   # Load profiles
│   ├── pypsa_callbacks.py     # Grid optimization
│   └── settings_callbacks.py  # Settings management
│
├── models/                     # Business logic (from backend)
│   ├── forecasting.py         # ML forecasting models
│   ├── load_profile_generation.py # Profile generation
│   ├── pypsa_analyzer.py      # PyPSA network analysis
│   ├── pypsa_visualizer.py    # PyPSA visualization
│   ├── pypsa_model_executor.py # PyPSA model execution
│   ├── network_cache.py       # Network caching
│   └── validation_models.py   # Pydantic models
│
├── utils/                      # Utility functions
│   └── __init__.py
│
├── assets/                     # Static assets
│   ├── css/                   # Custom CSS
│   └── images/                # Images
│
└── data/                       # Data storage (optional)
```

---

## Architecture Details

### State Management

**React (Before)**: Zustand + React Context + sessionStorage/localStorage

**Dash (After)**: dcc.Store components
- `active-project-store` (session) - Current project
- `selected-page-store` (session) - Current page
- `sidebar-collapsed-store` (local) - Sidebar state
- `recent-projects-store` (local) - Recent projects
- `color-settings-store` (local) - Color settings
- `process-state-store` (memory) - Process states
- `forecast-progress-store` (memory) - Forecast progress
- `profile-progress-store` (memory) - Profile progress
- `pypsa-progress-store` (memory) - PyPSA progress

### Real-time Updates

**React (Before)**: Server-Sent Events (SSE)

**Dash (After)**: dcc.Interval components
- `forecast-interval` - Updates every 1 second during forecasting
- `profile-interval` - Updates every 1 second during profile generation
- `pypsa-interval` - Updates every 1 second during optimization

### Data Flow

**Before (React + FastAPI)**:
```
User Action → React Component → Axios HTTP Request → FastAPI Route →
Business Logic → Response → React State Update → UI Update
```

**After (Dash)**:
```
User Action → Dash Callback → Business Logic →
Return Values → Component Props Update → UI Update
```

### Key Conversions

| React Concept | Dash Equivalent |
|--------------|-----------------|
| React Component | Python function returning html.Div() |
| useState | dcc.Store + callback |
| useEffect | @app.callback with Input/State |
| Axios GET/POST | Direct Python function call in callback |
| Server-Sent Events | dcc.Interval component |
| React Router | Conditional rendering based on selected_page |
| Context API | dcc.Store (session/local/memory) |
| Zustand | dcc.Store with localStorage |

---

## Usage Guide

### 1. Creating a Project

1. Navigate to **Projects → Create Project**
2. Enter project name and path
3. Click "Create Project"
4. Project structure will be created automatically

### 2. Running Demand Forecasting

1. Load a project (**Projects → Load Project**)
2. Go to **Demand Forecasting → Demand Projection**
3. Configure forecast parameters (target year, models, sectors)
4. Click "Start Forecasting"
5. Monitor progress in the notification bell
6. View results in **Demand Forecasting → Demand Visualization**

### 3. Generating Load Profiles

1. Ensure demand forecasting is complete
2. Go to **Load Profiles → Generate Profiles**
3. Configure profile generation settings
4. Click "Generate Profiles"
5. Monitor progress
6. Analyze results in **Load Profiles → Analyze Profiles**

### 4. Running PyPSA Optimization

1. Ensure load profiles are generated
2. Go to **PyPSA Suite → Model Config**
3. Configure network and optimization parameters
4. Click "Run Optimization"
5. Monitor progress
6. View results in **PyPSA Suite → View Results**

---

## Key Differences from Original React App

### Advantages of Dash Version

1. **Single Language**: 100% Python (no JavaScript)
2. **Simpler Deployment**: One Python process instead of separate frontend/backend
3. **Easier Maintenance**: No need to maintain two codebases
4. **Native Integration**: Direct access to Python ML/data science libraries
5. **Plotly Charts**: Native Plotly integration (better than converting React charts)

### Considerations

1. **Performance**: Dash may be slower for very complex UIs compared to React
2. **Customization**: Less flexible styling compared to React + TailwindCSS
3. **Ecosystem**: Smaller ecosystem than React
4. **Real-time**: dcc.Interval polling vs. WebSocket/SSE (less efficient)

---

## Development

### Adding New Pages

1. Create a new file in `pages/`:
   ```python
   # pages/new_page.py
   from dash import html

   def layout(active_project=None):
       return html.Div([
           html.H2("New Page"),
           # Add content here
       ])
   ```

2. Import in `pages/__init__.py`:
   ```python
   from . import new_page
   __all__ = [..., 'new_page']
   ```

3. Add routing in `app.py`:
   ```python
   elif selected_page == 'New Page':
       return new_page.layout(active_project), style
   ```

### Adding New Callbacks

1. Create callback in appropriate file in `callbacks/`:
   ```python
   def register_callbacks(app):
       @app.callback(
           Output('output-id', 'children'),
           Input('input-id', 'n_clicks')
       )
       def my_callback(n_clicks):
           return f"Clicked {n_clicks} times"
   ```

2. Register in `app.py`:
   ```python
   from callbacks import my_callbacks
   my_callbacks.register_callbacks(app)
   ```

---

## Production Deployment

### Option 1: Gunicorn (Linux/Mac)

```bash
gunicorn app:server -b 0.0.0.0:8050 -w 4
```

### Option 2: Waitress (Windows)

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=8050 app:server
```

### Option 3: Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:server", "-b", "0.0.0.0:8050", "-w", "4"]
```

---

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Port Already in Use**: Change port in `app.py`:
   ```python
   app.run_server(port=8051)
   ```

3. **Callback Errors**: Check callback signatures match Input/Output definitions

4. **Store Not Persisting**: Verify storage_type ('local', 'session', 'memory')

---

## Contributing

This conversion maintains all functionality from the original React + FastAPI application. To enhance or modify:

1. Follow the existing code structure
2. Keep business logic in `models/`
3. Keep UI logic in `pages/` and `components/`
4. Keep interactions in `callbacks/`
5. Document any new features

---

## License

Same as the original KSEB Energy Analytics Platform

---

## Credits

**Original Application**: React 19 + FastAPI
**Converted to Dash**: Python-based Dash/Plotly framework
**Conversion Date**: 2025
**Maintained By**: KSEB Analytics Team

---

## Support

For issues or questions:
1. Check this README
2. Review the original React codebase documentation
3. Consult Dash documentation: https://dash.plotly.com/
4. Contact the development team

---

**Note**: This Dash conversion maintains 100% of the original functionality while providing a unified Python-based framework for easier maintenance and deployment.
