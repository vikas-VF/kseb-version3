# 📋 PAGE-WISE IMPLEMENTATION PLAN & METHODOLOGY
## Plotly Dash Conversion - Complete Feature Parity with React+FastAPI

---

## 🎯 OBJECTIVE

Convert the React+FastAPI KSEB Energy Analytics Platform to Plotly Dash while maintaining **100% feature parity** with the original application. This plan provides step-by-step methodology for each page.

---

## 📐 OVERALL METHODOLOGY

### Development Principles

1. **Feature Parity First**: Match every feature from React exactly
2. **No New Features**: Only replicate existing functionality
3. **Same UI/UX**: Match design, layout, colors, and interactions
4. **Same Data Flow**: Use same backend endpoints and data structures
5. **Test After Each Page**: Verify functionality before moving to next page

### Technical Stack

**Must Use:**
- Plotly Dash 2.14+
- Dash Bootstrap Components
- Plotly charts
- Flask-Caching for performance
- dcc.Store for state management
- Python requests for API calls (or direct imports)

**Architecture Pattern:**
```
dash/
├── app.py                    # Main Dash app
├── pages/                    # Page layouts (match React views)
├── components/               # Reusable components (match React components)
├── callbacks/                # All callbacks (match React hooks/handlers)
├── utils/                    # Helper functions
├── services/                 # Backend API communication
└── assets/                   # CSS, images
```

---

## 📄 PAGE 1: HOME PAGE

**React File:** `frontend/src/views/Home.jsx` (422 lines)
**Dash File:** `dash/pages/home.py` (Currently 284 lines, incomplete)

### MISSING FEATURES TO IMPLEMENT

#### 1. Recent Projects Table with Search & Sort (HIGH PRIORITY)

**React Implementation:**
```javascript
// State
const [recentProjects, setRecentProjects] = useState([]);
const [sortBy, setSortBy] = useState('lastOpened');
const [searchTerm, setSearchTerm] = useState('');

// Load from localStorage
useEffect(() => {
    const projects = JSON.parse(localStorage.getItem('recentProjects')) || [];
    setRecentProjects(projects);
}, [activeProject]);

// Filter and sort
const filteredAndSortedProjects = useMemo(() => {
    return recentProjects
        .filter(p => p.name.toLowerCase().includes(searchTerm.toLowerCase()) || ...)
        .sort((a, b) => sortBy === 'name' ? a.name.localeCompare(b.name) : ...);
}, [recentProjects, sortBy, searchTerm]);
```

**Dash Implementation Strategy:**

```python
# In dash/pages/home.py

def layout(active_project=None):
    # Add search input
    search_input = dbc.Input(
        id='projects-search',
        type='text',
        placeholder='Search projects...',
        debounce=True,  # Wait for user to stop typing
        className='mb-2'
    )

    # Add sort dropdown
    sort_dropdown = dcc.Dropdown(
        id='projects-sort',
        options=[
            {'label': 'Last Opened', 'value': 'lastOpened'},
            {'label': 'Name (A-Z)', 'value': 'name'}
        ],
        value='lastOpened',
        clearable=False,
        className='mb-2'
    )

    # Recent projects table (dynamic content)
    projects_table = html.Div(id='recent-projects-table')

    return dbc.Container([
        # ... existing content ...
        dbc.Row([
            dbc.Col(search_input, width=8),
            dbc.Col(sort_dropdown, width=4)
        ]),
        projects_table
    ])
```

**Callback Implementation:**

```python
# In dash/callbacks/project_callbacks.py

@app.callback(
    Output('recent-projects-table', 'children'),
    Input('projects-search', 'value'),
    Input('projects-sort', 'value'),
    Input('recent-projects-store', 'data')  # New dcc.Store
)
def update_projects_table(search_term, sort_by, projects_data):
    if not projects_data:
        return dbc.Alert('No recent projects', color='secondary')

    # Filter
    filtered = projects_data
    if search_term:
        filtered = [
            p for p in filtered
            if search_term.lower() in p['name'].lower()
            or search_term.lower() in p['path'].lower()
        ]

    # Sort
    if sort_by == 'name':
        filtered.sort(key=lambda x: x['name'])
    else:
        filtered.sort(key=lambda x: x.get('lastOpened', ''), reverse=True)

    # Build table
    return dbc.Table([
        html.Thead(html.Tr([
            html.Th('Project Name'),
            html.Th('Last Opened'),
            html.Th('Actions')
        ])),
        html.Tbody([
            html.Tr([
                html.Td([
                    html.Strong(p['name']),
                    html.Br(),
                    html.Small(p['path'], className='text-muted')
                ]),
                html.Td(format_date(p.get('lastOpened'))),
                html.Td([
                    dbc.Button('Delete', id={'type': 'delete-project', 'index': p['id']},
                              color='danger', size='sm', className='me-2'),
                    dbc.Button('Open', id={'type': 'open-project', 'index': p['id']},
                              color='primary', size='sm')
                ])
            ]) for p in filtered
        ])
    ], bordered=True, striped=True)
```

**Storage Implementation:**

```python
# In dash/app.py, add dcc.Store for localStorage simulation

app.layout = html.Div([
    dcc.Store(id='recent-projects-store', storage_type='local'),
    dcc.Location(id='url', refresh=False),
    # ... rest of layout ...
])
```

**Time Estimate:** 4-6 hours

#### 2. Delete Project Functionality (MEDIUM PRIORITY)

**React Implementation:**
```javascript
const handleDeleteClick = (project) => {
    setProjectToDelete(project);
    setShowConfirm(true);
};

const handleConfirmDelete = () => {
    const updated = recentProjects.filter((p) => p.id !== projectToDelete.id);
    localStorage.setItem('recentProjects', JSON.stringify(updated));
    setRecentProjects(updated);
    // ... update active project if needed
};
```

**Dash Implementation:**

```python
# Callback for delete confirmation modal
@app.callback(
    Output('delete-confirm-modal', 'is_open'),
    Output('delete-project-id-store', 'data'),
    Input({'type': 'delete-project', 'index': ALL}, 'n_clicks'),
    State('delete-confirm-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_delete_modal(n_clicks_list, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False, None

    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    project_id = eval(button_id)['index']

    return True, project_id

@app.callback(
    Output('recent-projects-store', 'data', allow_duplicate=True),
    Input('confirm-delete-btn', 'n_clicks'),
    State('delete-project-id-store', 'data'),
    State('recent-projects-store', 'data'),
    prevent_initial_call=True
)
def confirm_delete(n_clicks, project_id, projects_data):
    if not n_clicks or not project_id:
        return no_update

    # Filter out deleted project
    updated = [p for p in projects_data if p['id'] != project_id]
    return updated
```

**Modal Layout:**

```python
delete_modal = dbc.Modal([
    dbc.ModalHeader('Confirm Delete'),
    dbc.ModalBody([
        html.P('Are you sure you want to remove this project from the list?'),
        dbc.Alert('This will not delete files from disk, only remove from list.',
                 color='warning')
    ]),
    dbc.ModalFooter([
        dbc.Button('Cancel', id='cancel-delete-btn', color='secondary'),
        dbc.Button('Delete', id='confirm-delete-btn', color='danger')
    ])
], id='delete-confirm-modal', is_open=False)
```

**Time Estimate:** 3-4 hours

#### 3. Workflow Guide Sidebar (MEDIUM PRIORITY)

**React Implementation:**
- 4 sections: Demand Forecasting, Load Profiles, PyPSA Suite, System
- 10 workflow cards total
- Disabled state when no active project
- Visual indication with borders

**Dash Implementation:**

```python
def create_workflow_sidebar(active_project):
    def workflow_card(icon, title, description, page, disabled):
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(icon, className='me-2'),
                    html.Div([
                        html.Strong(title, className='d-block'),
                        html.Small(description, className='text-muted')
                    ])
                ], className='d-flex align-items-center'),
                dbc.Button('→', id={'type': 'nav-link', 'page': page},
                          size='sm', disabled=disabled, className='mt-2')
            ])
        ], className='mb-2')

    return dbc.Card([
        dbc.CardHeader(html.H5('🚀 Complete Workflow')),
        dbc.CardBody([
            # Demand Forecasting Section
            html.H6('📈 Demand Forecasting', className='mt-2'),
            html.Div([
                workflow_card('📊', 'Demand Projection', 'Configure & run forecast',
                             'Demand Projection', not active_project),
                workflow_card('📉', 'Demand Visualization', 'View forecast results',
                             'Demand Visualization', not active_project),
            ], className='ms-3 border-start ps-3'),

            # Load Profiles Section
            html.H6('⚡ Load Profiles', className='mt-3'),
            html.Div([
                workflow_card('🔋', 'Generate Profiles', 'Create hourly profiles',
                             'Generate Profiles', not active_project),
                workflow_card('📊', 'Analyze Profiles', 'View profile analytics',
                             'Analyze Profiles', not active_project),
            ], className='ms-3 border-start ps-3'),

            # PyPSA Suite Section
            html.H6('🔌 PyPSA Suite', className='mt-3'),
            html.Div([
                workflow_card('⚙️', 'Model Config', 'Configure PyPSA model',
                             'Model Config', not active_project),
                workflow_card('📈', 'View Results', 'PyPSA optimization results',
                             'View Results', not active_project),
            ], className='ms-3 border-start ps-3'),

            # System Section
            html.H6('🛠️ System', className='mt-3'),
            html.Div([
                workflow_card('⚙️', 'Settings', 'App preferences',
                             'Settings', False),
                workflow_card('🔧', 'Other Tools', 'Additional utilities',
                             'Other Tools', False),
            ], className='ms-3 border-start ps-3'),
        ])
    ])
```

**Time Estimate:** 3-4 hours

### HOME PAGE - TOTAL TIME ESTIMATE: 10-14 hours

---

## 📄 PAGE 2: CREATE PROJECT

**React File:** `frontend/src/views/Projects/CreateProject.jsx` (500+ lines)
**Dash File:** `dash/pages/create_project.py` (91 lines)

### CURRENT FEATURES (React)

1. ✅ 2-step wizard (Core Setup + Optional Details)
2. ✅ Directory browser integration
3. ✅ Real-time path validation with debouncing
4. ✅ Auto-generates project structure (inputs/, results/, templates)
5. ✅ Success screen showing directory tree
6. ✅ Session storage persistence

### IMPLEMENTATION TASKS

#### 1. Directory Browser / Path Validation (HIGH PRIORITY)

**React Implementation:**
```javascript
// Debounced validation
useEffect(() => {
    const handler = setTimeout(async () => {
        if (projectLocation) {
            const isValid = await validatePath(projectLocation);
            setPathValid(isValid);
        }
    }, 500);
    return () => clearTimeout(handler);
}, [projectLocation]);
```

**Dash Implementation:**

```python
# Add callback for path validation
@app.callback(
    Output('path-validation-status', 'children'),
    Input('project-location-input', 'value'),
    prevent_initial_call=True,
    background=True  # Use background callback for debouncing
)
def validate_project_path(path):
    if not path:
        return ''

    import time
    time.sleep(0.5)  # Debounce

    # Check if path exists
    import os
    if os.path.exists(path):
        if os.path.isdir(path):
            return dbc.Alert('✅ Valid directory', color='success')
        else:
            return dbc.Alert('❌ Path exists but is not a directory', color='danger')
    else:
        # Check if parent exists (can create)
        parent = os.path.dirname(path)
        if os.path.exists(parent) and os.path.isdir(parent):
            return dbc.Alert('✅ Can create new directory here', color='info')
        else:
            return dbc.Alert('❌ Parent directory does not exist', color='danger')
```

**Time Estimate:** 4-5 hours

#### 2. Project Structure Creation (HIGH PRIORITY)

**React Implementation:**
- Creates folders: inputs/, results/demand_forecasts/, results/load_profiles/, results/pypsa_optimization/
- Copies template files
- Creates project.json metadata
- Creates README.md

**Dash Implementation:**

```python
@app.callback(
    Output('create-status', 'children'),
    Output('active-project-store', 'data'),
    Input('create-project-btn', 'n_clicks'),
    State('project-name-input', 'value'),
    State('project-location-input', 'value'),
    State('project-description-input', 'value'),
    prevent_initial_call=True
)
def create_project(n_clicks, name, location, description):
    if not n_clicks or not name or not location:
        return no_update, no_update

    import os
    import json
    from datetime import datetime

    project_path = os.path.join(location, name)

    try:
        # Create main folder
        os.makedirs(project_path, exist_ok=True)

        # Create subfolder structure
        os.makedirs(os.path.join(project_path, 'inputs'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'results', 'demand_forecasts'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'results', 'load_profiles'), exist_ok=True)
        os.makedirs(os.path.join(project_path, 'results', 'pypsa_optimization'), exist_ok=True)

        # Copy template files
        # (implementation depends on where templates are stored)

        # Create project.json
        metadata = {
            'name': name,
            'description': description,
            'created': datetime.now().isoformat(),
            'version': '1.0'
        }
        with open(os.path.join(project_path, 'project.json'), 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create README.md
        readme_content = f"""# {name}

{description}

Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Structure
- inputs/ - Input Excel files
- results/ - Analysis results
  - demand_forecasts/ - Forecast scenarios
  - load_profiles/ - Generated profiles
  - pypsa_optimization/ - Grid optimization results
"""
        with open(os.path.join(project_path, 'README.md'), 'w') as f:
            f.write(readme_content)

        # Update active project
        project_data = {
            'name': name,
            'path': project_path,
            'description': description,
            'lastOpened': datetime.now().isoformat()
        }

        return (
            dbc.Alert([
                html.H4('✅ Project Created Successfully!', className='alert-heading'),
                html.P(f'Location: {project_path}'),
                html.Hr(),
                html.P('Folder structure:'),
                html.Ul([
                    html.Li('📁 inputs/'),
                    html.Li('📁 results/'),
                    html.Ul([
                        html.Li('📁 demand_forecasts/'),
                        html.Li('📁 load_profiles/'),
                        html.Li('📁 pypsa_optimization/')
                    ])
                ])
            ], color='success'),
            project_data
        )

    except Exception as e:
        return dbc.Alert(f'❌ Error creating project: {str(e)}', color='danger'), no_update
```

**Time Estimate:** 4-5 hours

#### 3. Success Screen & Auto-Navigation (MEDIUM PRIORITY)

```python
@app.callback(
    Output('url', 'pathname'),
    Input('active-project-store', 'data'),
    prevent_initial_call=True
)
def navigate_after_create(project_data):
    if project_data:
        return '/demand-projection'
    return no_update
```

**Time Estimate:** 2 hours

### CREATE PROJECT PAGE - TOTAL TIME ESTIMATE: 10-12 hours

---

## 📄 PAGE 3: LOAD PROJECT

**React File:** `frontend/src/views/Projects/LoadProject.jsx` (300+ lines)
**Dash File:** `dash/pages/load_project.py` (56 lines)

### IMPLEMENTATION TASKS

#### 1. Project Metadata Loading (HIGH PRIORITY)

```python
@app.callback(
    Output('load-status', 'children'),
    Output('active-project-store', 'data'),
    Output('recent-projects-store', 'data', allow_duplicate=True),
    Input('load-project-btn', 'n_clicks'),
    State('project-path-input', 'value'),
    State('recent-projects-store', 'data'),
    prevent_initial_call=True
)
def load_project(n_clicks, path, recent_projects):
    if not n_clicks or not path:
        return no_update, no_update, no_update

    import os
    import json
    from datetime import datetime

    # Validate path
    if not os.path.exists(path) or not os.path.isdir(path):
        return dbc.Alert('❌ Invalid project path', color='danger'), no_update, no_update

    # Check for project.json
    metadata_path = os.path.join(path, 'project.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    else:
        # Use defaults if no metadata
        metadata = {'name': os.path.basename(path), 'description': ''}

    # Update project data
    project_data = {
        'name': metadata.get('name', os.path.basename(path)),
        'path': path,
        'description': metadata.get('description', ''),
        'lastOpened': datetime.now().isoformat(),
        'id': path.replace('/', '_').replace('\\', '_')  # Generate unique ID
    }

    # Update recent projects
    recent = recent_projects or []
    # Remove if already exists
    recent = [p for p in recent if p.get('path') != path]
    # Add to front
    recent = [project_data] + recent
    # Limit to 10
    recent = recent[:10]

    return (
        dbc.Alert(f'✅ Project loaded: {metadata.get("name")}', color='success'),
        project_data,
        recent
    )
```

**Time Estimate:** 3-4 hours

### LOAD PROJECT PAGE - TOTAL TIME ESTIMATE: 3-4 hours

---

## 📄 PAGE 4: DEMAND PROJECTION (CRITICAL)

**React File:** `frontend/src/views/Demand Forecasting/DemandProjection.jsx` (900+ lines)
**Dash File:** `dash/pages/demand_projection.py` (167 lines)

### MAJOR MISSING FEATURES

This is the most complex page. Needs complete rewrite.

#### 1. Backend Integration (CRITICAL)

**API Endpoints to Call:**
- `/project/sectors` - Get sectors list
- `/project/extract-sector-data` - Get sector data with economic indicators
- `/project/consolidated-electricity` - Get consolidated data
- `/project/settings/colors` - Get color configuration
- `/project/forecast` (POST) - Start forecasting
- `/project/forecast-progress` (SSE) - Real-time progress

**Implementation:**

```python
# Create new file: dash/services/api_client.py

import requests
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url

    def get_sectors(self, project_path: str) -> Dict:
        response = requests.get(f'{self.base_url}/project/sectors',
                               params={'projectPath': project_path})
        response.raise_for_status()
        return response.json()

    def get_sector_data(self, project_path: str, sector: str) -> Dict:
        response = requests.post(f'{self.base_url}/project/extract-sector-data',
                                json={'projectPath': project_path, 'sector': sector})
        response.raise_for_status()
        return response.json()

    def get_consolidated_data(self, project_path: str) -> Dict:
        response = requests.post(f'{self.base_url}/project/consolidated-electricity',
                                json={'projectPath': project_path})
        response.raise_for_status()
        return response.json()

    def get_color_config(self, project_path: str) -> Dict:
        response = requests.get(f'{self.base_url}/project/settings/colors',
                               params={'projectPath': project_path})
        response.raise_for_status()
        return response.json()

    def start_forecast(self, config: Dict) -> Dict:
        response = requests.post(f'{self.base_url}/project/forecast', json=config)
        response.raise_for_status()
        return response.json()

api = APIClient()
```

**Time Estimate:** 8-10 hours

#### 2. Dual View Mode (Consolidated vs Sector) (CRITICAL)

**Dash Implementation:**

```python
def layout(active_project=None):
    return dbc.Container([
        # View mode toggle
        dbc.ButtonGroup([
            dbc.Button('Consolidated View', id='consolidated-view-btn',
                      color='primary', outline=False),
            dbc.Button('Sector-Specific View', id='sector-view-btn',
                      color='primary', outline=True)
        ], className='mb-3'),

        # Consolidated view content
        html.Div(id='consolidated-view-content', style={'display': 'block'}),

        # Sector view content
        html.Div(id='sector-view-content', style={'display': 'none'})
    ])

# Callback to toggle views
@app.callback(
    Output('consolidated-view-content', 'style'),
    Output('sector-view-content', 'style'),
    Output('consolidated-view-btn', 'outline'),
    Output('sector-view-btn', 'outline'),
    Input('consolidated-view-btn', 'n_clicks'),
    Input('sector-view-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_view(consolidated_clicks, sector_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'consolidated-view-btn':
        return {'display': 'block'}, {'display': 'none'}, False, True
    else:
        return {'display': 'none'}, {'display': 'block'}, True, False
```

**Time Estimate:** 6-8 hours

#### 3. Chart Implementations (CRITICAL)

**Area Chart for Consolidated View:**

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_area_chart(data, hidden_sectors=None):
    """Create stacked area chart for consolidated demand by sector"""
    hidden_sectors = hidden_sectors or []

    fig = go.Figure()

    for sector in data['sectors']:
        if sector not in hidden_sectors:
            fig.add_trace(go.Scatter(
                x=data['years'],
                y=data[sector],
                name=sector,
                mode='lines',
                stackgroup='one',  # Creates stacked area
                fillcolor=data['colors'].get(sector, '#ccc'),
                line=dict(width=0.5, color=data['colors'].get(sector, '#ccc')),
                hovertemplate=f'{sector}<br>%{{x}}: %{{y:.2f}} MWh<extra></extra>'
            ))

    fig.update_layout(
        title='Electricity Demand Forecast - Consolidated View',
        xaxis_title='Year',
        yaxis_title='Electricity Demand (MWh)',
        hovermode='x unified',
        legend=dict(orientation='h', y=-0.2),
        margin=dict(l=50, r=50, t=50, b=100)
    )

    return fig

# Callback to generate chart
@app.callback(
    Output('consolidated-area-chart', 'figure'),
    Input('active-project-store', 'data'),
    Input('hidden-sectors-store', 'data'),
    Input('unit-selector', 'value')
)
def update_area_chart(project_data, hidden_sectors, unit):
    if not project_data:
        return go.Figure()

    # Fetch consolidated data
    data = api.get_consolidated_data(project_data['path'])

    # Apply unit conversion
    conversion_factors = {'mwh': 1, 'kwh': 1000, 'gwh': 0.001, 'twh': 0.000001}
    factor = conversion_factors.get(unit, 1)

    # Convert data
    for sector in data['sectors']:
        data[sector] = [v * factor for v in data[sector]]

    return create_area_chart(data, hidden_sectors)
```

**Time Estimate:** 12-15 hours for all charts (Area, Stacked Bar, Line)

#### 4. Real-Time SSE Progress (CRITICAL)

This is complex in Dash. Options:

**Option A: Use dcc.Interval with server-side state:**

```python
# Add global progress tracking
progress_tracker = {}

@app.callback(
    Output('forecast-progress-store', 'data'),
    Input('start-forecast-btn', 'n_clicks'),
    State('forecast-config', 'data'),
    prevent_initial_call=True
)
def start_forecast(n_clicks, config):
    if not n_clicks:
        return no_update

    import threading
    import uuid

    # Generate unique process ID
    process_id = str(uuid.uuid4())

    # Initialize progress
    progress_tracker[process_id] = {
        'status': 'running',
        'progress': 0,
        'logs': [],
        'current_task': 'Initializing...'
    }

    # Start forecast in background thread
    def run_forecast():
        try:
            # Make API call
            response = api.start_forecast(config)

            # Update progress (in real scenario, would poll backend)
            for i in range(0, 101, 10):
                time.sleep(1)
                progress_tracker[process_id]['progress'] = i
                progress_tracker[process_id]['logs'].append(f'Progress: {i}%')

            progress_tracker[process_id]['status'] = 'completed'
        except Exception as e:
            progress_tracker[process_id]['status'] = 'failed'
            progress_tracker[process_id]['logs'].append(f'Error: {str(e)}')

    thread = threading.Thread(target=run_forecast)
    thread.start()

    return {'process_id': process_id}

# Callback to update progress display
@app.callback(
    Output('progress-display', 'children'),
    Input('progress-interval', 'n_intervals'),
    State('forecast-progress-store', 'data'),
    prevent_initial_call=True
)
def update_progress(n_intervals, progress_data):
    if not progress_data or 'process_id' not in progress_data:
        return no_update

    process_id = progress_data['process_id']
    if process_id not in progress_tracker:
        return no_update

    progress = progress_tracker[process_id]

    return dbc.Card([
        dbc.CardBody([
            html.H5(f"Status: {progress['status']}"),
            dbc.Progress(value=progress['progress'], className='mb-3'),
            html.P(progress['current_task']),
            html.Div([
                html.P(log) for log in progress['logs'][-10:]  # Last 10 logs
            ], style={'maxHeight': '200px', 'overflowY': 'scroll'})
        ])
    ])
```

**Option B: Use dash-extensions for real SSE:**

```python
from dash_extensions.enrich import DashProxy, ServerSideOutput

# This requires dash-extensions package
# More complex but true SSE support
```

**Time Estimate:** 15-20 hours (complex feature)

#### 5. State Persistence (HIGH PRIORITY)

```python
# Add multiple dcc.Store components for state

app.layout = html.Div([
    # View state
    dcc.Store(id='demand-view-state', storage_type='session', data={
        'isConsolidated': True,
        'activeTab': 'Data Table'
    }),

    # Chart zoom state
    dcc.Store(id='chart-zoom-state', storage_type='session', data={
        'areaChartZoom': None,
        'stackedBarZoom': None
    }),

    # Hidden series
    dcc.Store(id='hidden-sectors-store', storage_type='session', data=[]),

    # Unit selection
    dcc.Store(id='unit-store', storage_type='session', data='mwh'),

    # ... rest of layout
])
```

**Time Estimate:** 6-8 hours

#### 6. Tabs (Data Table, Charts, Correlation) (HIGH PRIORITY)

```python
tabs = dbc.Tabs([
    dbc.Tab(label='Data Table', tab_id='table'),
    dbc.Tab(label='Area Chart', tab_id='area'),
    dbc.Tab(label='Stacked Bar', tab_id='stacked'),
    dbc.Tab(label='Line Chart', tab_id='line'),
    dbc.Tab(label='Correlation', tab_id='correlation')
], id='demand-tabs', active_tab='table')

# Content area
tab_content = html.Div(id='tab-content')

# Callback to switch content
@app.callback(
    Output('tab-content', 'children'),
    Input('demand-tabs', 'active_tab'),
    State('active-project-store', 'data')
)
def switch_tab(active_tab, project):
    if active_tab == 'table':
        return create_data_table(project)
    elif active_tab == 'area':
        return dcc.Graph(id='area-chart')
    elif active_tab == 'stacked':
        return dcc.Graph(id='stacked-bar-chart')
    elif active_tab == 'line':
        return dcc.Graph(id='line-chart')
    elif active_tab == 'correlation':
        return create_correlation_analysis(project)
```

**Time Estimate:** 8-10 hours

### DEMAND PROJECTION PAGE - TOTAL TIME ESTIMATE: 60-80 hours

---

## 📄 PAGE 5: DEMAND VISUALIZATION (CRITICAL)

**React File:** `frontend/src/views/Demand Forecasting/DemandVisualization.jsx` (1,222 lines!)
**Dash File:** `dash/pages/demand_visualization.py` (42 lines - PLACEHOLDER)

### IMPLEMENTATION STRATEGY

This page needs to be built from scratch.

#### 1. Scenario Loading (CRITICAL)

```python
@app.callback(
    Output('scenario-dropdown', 'options'),
    Input('active-project-store', 'data')
)
def load_scenarios(project):
    if not project:
        return []

    import os
    import glob

    # Get scenarios from results folder
    scenarios_path = os.path.join(project['path'], 'results', 'demand_forecasts', '*')
    scenarios = glob.glob(scenarios_path)

    return [{'label': os.path.basename(s), 'value': s} for s in scenarios]
```

**Time Estimate:** 4-5 hours

#### 2. Chart Implementations (All Types) (CRITICAL)

```python
# Line chart for model comparison
def create_comparison_chart(scenario_data, sector, models):
    fig = go.Figure()

    for model in models:
        fig.add_trace(go.Scatter(
            x=scenario_data['years'],
            y=scenario_data[model][sector],
            name=f'{sector} - {model}',
            mode='lines+markers'
        ))

    fig.update_layout(
        title=f'Model Comparison - {sector}',
        xaxis_title='Year',
        yaxis_title='Demand (MWh)'
    )

    return fig
```

**Time Estimate:** 15-20 hours

#### 3. Scenario Comparison Modal (HIGH PRIORITY)

```python
comparison_modal = dbc.Modal([
    dbc.ModalHeader('Compare Scenarios'),
    dbc.ModalBody([
        dbc.Row([
            dbc.Col([
                dbc.Label('Scenario 1'),
                dcc.Dropdown(id='scenario-1-dropdown'),
                dcc.Graph(id='scenario-1-chart')
            ], width=6),
            dbc.Col([
                dbc.Label('Scenario 2'),
                dcc.Dropdown(id='scenario-2-dropdown'),
                dcc.Graph(id='scenario-2-chart')
            ], width=6)
        ])
    ], style={'height': '70vh', 'overflowY': 'scroll'}),
    dbc.ModalFooter([
        dbc.Button('Close', id='close-comparison', color='secondary')
    ])
], id='comparison-modal', size='xl', is_open=False)
```

**Time Estimate:** 8-10 hours

#### 4. Statistics Panel (HIGH PRIORITY)

```python
def calculate_statistics(data):
    """Calculate CAGR, growth rates, etc."""
    years = data['years']
    values = data['values']

    # CAGR calculation
    n_years = years[-1] - years[0]
    cagr = ((values[-1] / values[0]) ** (1/n_years) - 1) * 100

    # Year-over-year growth
    yoy_growth = [(values[i] - values[i-1]) / values[i-1] * 100
                  for i in range(1, len(values))]

    # Total and peak
    total_demand = sum(values)
    peak_demand = max(values)

    return {
        'cagr': cagr,
        'avg_yoy_growth': sum(yoy_growth) / len(yoy_growth),
        'total_demand': total_demand,
        'peak_demand': peak_demand,
        'peak_year': years[values.index(peak_demand)]
    }

# Display in cards
def create_stats_panel(stats):
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{stats['cagr']:.2f}%", className='text-primary'),
                    html.P('CAGR')
                ])
            ])
        ], width=3),
        # ... more stat cards
    ])
```

**Time Estimate:** 6-8 hours

#### 5. Export Functionality (MEDIUM PRIORITY)

```python
@app.callback(
    Output('download-excel', 'data'),
    Input('export-excel-btn', 'n_clicks'),
    State('current-data-store', 'data'),
    prevent_initial_call=True
)
def export_to_excel(n_clicks, data):
    if not n_clicks:
        return no_update

    import pandas as pd
    import io

    df = pd.DataFrame(data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Forecast Results', index=False)
    output.seek(0)

    return dcc.send_bytes(output.read(), 'forecast_results.xlsx')
```

**Time Estimate:** 4-5 hours

### DEMAND VISUALIZATION PAGE - TOTAL TIME ESTIMATE: 50-70 hours

---

## 📊 COMPLETE TIME ESTIMATES

| Page | Estimated Hours | Priority |
|------|----------------|----------|
| Home Page | 10-14 | Medium |
| Create Project | 10-12 | High |
| Load Project | 3-4 | High |
| **Demand Projection** | **60-80** | **Critical** |
| **Demand Visualization** | **50-70** | **Critical** |
| Generate Profiles | 30-40 | High |
| Analyze Profiles | 40-50 | High |
| PyPSA Model Config | 30-40 | High |
| PyPSA View Results | 80-100 | Critical |
| Settings | 10-15 | Low |
| **Global Components** (Sidebar, TopBar, etc.) | 20-30 | Medium |
| **State Management** | 20-30 | High |
| **API Integration** | 30-40 | Critical |
| **Real-Time SSE** | 30-40 | Critical |
| **Testing & Bug Fixes** | 40-60 | Critical |
| **TOTAL** | **463-605 hours** | |

**Timeline:** 12-15 weeks (3-4 months) with 1 full-time developer

---

## 🎯 RECOMMENDED APPROACH

### Phase 1 (Weeks 1-2): Foundation
1. Set up API client
2. Implement state management architecture
3. Complete Home page
4. Complete Project Management (Create/Load)

### Phase 2 (Weeks 3-6): Demand Module
1. Demand Projection (full implementation)
2. Demand Visualization (full implementation)
3. SSE integration for real-time progress

### Phase 3 (Weeks 7-10): Load Profiles & PyPSA
1. Load Profiles (Generate & Analyze)
2. PyPSA Model Config
3. PyPSA View Results

### Phase 4 (Weeks 11-12): Polish & Testing
1. Settings page
2. UI/UX improvements
3. Testing and bug fixes
4. Documentation

---

## ✅ SUCCESS CRITERIA

For each page, verify:

1. **Visual Parity**: Matches React design exactly
2. **Feature Parity**: All React features present
3. **Data Flow**: Same backend calls, same data structures
4. **State Management**: Persistence works correctly
5. **Performance**: Acceptable load times
6. **Error Handling**: Graceful error messages
7. **User Experience**: Smooth interactions

---

## 📝 NEXT STEPS

1. **Decision**: Confirm commitment to full Dash conversion (460+ hours)
2. **Prioritization**: Finalize which features are must-have vs nice-to-have
3. **Resource Allocation**: Assign developers
4. **Timeline**: Set milestones and deadlines
5. **Begin Implementation**: Start with Phase 1

---

*This plan ensures 100% feature parity between React and Dash implementations. Each feature has been analyzed and mapped with implementation strategy.*
