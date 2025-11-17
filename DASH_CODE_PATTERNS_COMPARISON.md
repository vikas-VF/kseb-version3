# DASH vs REACT+FASTAPI - CODE PATTERNS COMPARISON

---

## 1. NAVIGATION PATTERN

### React+FastAPI (URL-based)
```javascript
// App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/projects/create" element={<CreateProject />} />
        <Route path="/demand" element={<DemandProjection />} />
        <Route path="/profiles/analyze" element={<AnalyzeProfiles />} />
      </Routes>
    </BrowserRouter>
  );
}

// In component
const navigate = useNavigate();
navigate('/demand-projection');
```

### Dash (Store-based)
```python
# app.py
app = Dash(__name__, suppress_callback_exceptions=True)

@app.callback(
    Output('selected-page-store', 'data'),
    Input({'type': 'nav-link', 'page': ALL}, 'n_clicks'),
    State('selected-page-store', 'data'),
    prevent_initial_call=True
)
def navigate_to_page(n_clicks, current_page):
    """Handle navigation when sidebar items are clicked"""
    button_id = callback_context.triggered[0]['prop_id']
    button_dict = json.loads(button_id.split('.')[0])
    page_name = button_dict.get('page')
    return page_name if page_name else current_page

@app.callback(
    Output('main-content', 'children'),
    Input('selected-page-store', 'data'),
    Input('active-project-store', 'data'),
    prevent_initial_call=False
)
def render_page_content(selected_page, active_project):
    """Render the main content based on selected page"""
    if selected_page == 'Demand Projection':
        page_module = _lazy_import_page('demand_projection')
        return page_module.layout(active_project)
    elif selected_page == 'Create Project':
        page_module = _lazy_import_page('create_project')
        return page_module.layout()
    # ... more pages
```

**Key Differences:**
- React uses URL paths, Dash uses store values
- React Router handles routing, Dash uses pattern callbacks
- No browser history in Dash
- Cannot deep-link in Dash

---

## 2. STATE MANAGEMENT PATTERN

### React+FastAPI (React Hooks + localStorage)
```javascript
// DemandProjection.jsx
import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'zustand';

export default function DemandProjection() {
  const [viewMode, setViewMode] = useState(() => {
    const saved = sessionStorage.getItem('demandVizMode');
    return saved ? JSON.parse(saved) : 'consolidated';
  });
  
  const [colorConfig, setColorConfig] = useState(() => {
    const saved = localStorage.getItem('color-config');
    return saved ? JSON.parse(saved) : DEFAULT_COLORS;
  });
  
  // Auto-sync to storage
  useEffect(() => {
    sessionStorage.setItem('demandVizMode', JSON.stringify(viewMode));
  }, [viewMode]);
  
  useEffect(() => {
    localStorage.setItem('color-config', JSON.stringify(colorConfig));
  }, [colorConfig]);
  
  return (
    <div>
      <button onClick={() => setViewMode('consolidated')}>Consolidated</button>
      <button onClick={() => setViewMode('sector')}>Sector</button>
    </div>
  );
}
```

### Dash (dcc.Store)
```python
# demand_projection.py
def layout(active_project=None):
    return html.Div([
        # Stores created by page
        dcc.Store(id='consolidated-data-store', data=None),
        dcc.Store(id='color-config-store', data={}),
        dcc.Store(id='demand-viz-state', storage_type='session', data={
            'viewMode': 'consolidated',
            'unit': 'mwh'
        }),
        
        # View toggle buttons
        dbc.ButtonGroup([
            dbc.Button('Consolidated', id='consolidated-view-btn', active=True),
            dbc.Button('Sector', id='sector-view-btn')
        ])
    ])

# Callback to handle view toggle
@callback(
    Output('demand-viz-state', 'data'),
    Input('consolidated-view-btn', 'n_clicks'),
    Input('sector-view-btn', 'n_clicks'),
    State('demand-viz-state', 'data'),
    prevent_initial_call=True
)
def toggle_view(consol_clicks, sector_clicks, state):
    """Handle view mode toggle"""
    if not state:
        state = {'viewMode': 'consolidated', 'unit': 'mwh'}
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if 'consolidated-view-btn' in trigger_id:
        state['viewMode'] = 'consolidated'
    elif 'sector-view-btn' in trigger_id:
        state['viewMode'] = 'sector'
    
    return state

# Callback to load color config
@callback(
    Output('color-config-store', 'data'),
    Input('consolidated-data-store', 'data')
)
def load_colors(data):
    """Load color configuration"""
    if not data:
        return {}
    
    return api.get_color_config()
```

**Key Differences:**
- React: Manual useEffect syncing required
- Dash: Automatic sync (specify storage_type)
- React: useState imperative updates
- Dash: Callback-based reactive updates
- React: Can use hooks anywhere
- Dash: Callbacks defined globally

---

## 3. REAL-TIME PROGRESS TRACKING

### React+FastAPI (Pure SSE)
```javascript
// DemandProjection.jsx
const handleStartForecast = async (config) => {
  try {
    // 1. Start the process
    const response = await api.post('/forecast/start', config);
    const processId = response.data.process_id;
    
    // 2. Show progress modal
    setShowProgressModal(true);
    setProcessId(processId);
    
    // 3. Open SSE connection
    const eventSource = new EventSource(`/api/forecast-progress`);
    
    // 4. Listen for progress events
    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      setProgress({
        percentage: data.progress,
        message: data.message,
        sector: data.sector
      });
    });
    
    // 5. Listen for completion
    eventSource.addEventListener('end', (event) => {
      const data = JSON.parse(event.data);
      eventSource.close();
      
      if (data.status === 'completed') {
        showNotification('success', 'Forecast completed!');
      } else {
        showNotification('error', data.error);
      }
      setShowProgressModal(false);
    });
    
  } catch (error) {
    showNotification('error', error.message);
  }
};
```

### Dash (SSE + Polling Hybrid)
```python
# demand_projection.py
def layout(active_project=None):
    return html.Div([
        # Stores
        dcc.Store(id='forecast-sse-control', 
                 data={'action': 'idle', 'url': ''}),
        dcc.Store(id='forecast-process-state', data=None),
        
        # Interval for polling fallback
        dcc.Interval(id='forecast-progress-interval', 
                    interval=1000, disabled=True),
        
        # Progress modal
        dbc.Modal([
            dbc.ModalHeader('Forecasting in Progress'),
            dbc.ModalBody([
                html.Div(id='forecast-progress-content')
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancel', id='cancel-forecasting-btn')
            ])
        ], id='forecast-progress-modal', is_open=False),
        
        # Client-side SSE handler script
        html.Script('''
            window.dash_clientside = window.dash_clientside || {};
            window.dash_clientside.forecast_sse = {
                handle_sse: function(sse_control, current_state) {
                    const action = sse_control.action;
                    const url = sse_control.url;
                    
                    if (action === 'start' && url) {
                        const eventSource = new EventSource(url);
                        
                        eventSource.addEventListener('progress', (event) => {
                            const data = JSON.parse(event.data);
                            const newState = {...current_state};
                            newState.progress = data.progress || 0;
                            newState.message = data.message || 'Processing...';
                            
                            // Update store
                            window.dash_clientside.set_props(
                                'forecast-process-state', 
                                {data: newState}
                            );
                        });
                        
                        eventSource.addEventListener('end', (event) => {
                            eventSource.close();
                            const data = JSON.parse(event.data);
                            // Handle completion
                        });
                    }
                }
            };
        ''')
    ])

# Callback to start forecast
@callback(
    Output('forecast-sse-control', 'data'),
    Output('forecast-progress-modal', 'is_open'),
    Input('start-forecast-btn', 'n_clicks'),
    State('forecast-config-store', 'data'),
    prevent_initial_call=True
)
def start_forecast(n_clicks, config):
    """Start forecast and open SSE connection"""
    try:
        # Start the subprocess
        result = api.start_demand_forecast(
            active_project['path'], 
            config
        )
        
        if result['success']:
            # Start SSE
            return {
                'action': 'start',
                'url': '/api/forecast-progress'
            }, True
        
    except Exception as e:
        # Show error
        return no_update, False

# Clientside callback to handle SSE (no Dash server round-trip)
app.clientside_callback(
    '''
    function(sse_control, current_state) {
        return window.dash_clientside.forecast_sse.handle_sse(
            sse_control, current_state
        );
    }
    ''',
    Output('forecast-sse-status', 'children'),
    Input('forecast-sse-control', 'data'),
    State('forecast-process-state', 'data')
)

# Progress display callback
@callback(
    Output('forecast-progress-content', 'children'),
    Input('forecast-process-state', 'data')
)
def update_progress_display(state):
    """Update progress display from store"""
    if not state:
        return "Waiting to start..."
    
    progress = state.get('progress', 0)
    message = state.get('message', '')
    logs = state.get('logs', [])
    
    return html.Div([
        dbc.Progress(value=progress, label=f"{progress}%"),
        html.P(message),
        html.Div([html.P(log) for log in logs[-10:]]),  # Last 10 logs
    ])
```

**Backend (local_service.py):**
```python
# Global queue for SSE
forecast_sse_queue = queue.Queue()

def start_demand_forecast(self, project_path, config):
    """Start subprocess in background thread"""
    process_id = f"forecast_{config['scenario_name']}"
    
    # Start subprocess in thread
    thread = threading.Thread(
        target=self._run_forecast_subprocess,
        args=(config_path, process_id, config['scenario_name'])
    )
    thread.daemon = True
    thread.start()
    
    # Track globally
    forecast_processes[process_id] = {
        'thread': thread,
        'status': 'running'
    }
    
    return {'success': True, 'process_id': process_id}

def _run_forecast_subprocess(self, config_path, process_id, scenario_name):
    """Execute subprocess and stream progress to queue"""
    process = subprocess.Popen(
        ['python', 'forecasting.py', '--config', str(config_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Read output line by line
    for line in iter(process.stdout.readline, ''):
        if line.startswith('PROGRESS:'):
            # Parse progress JSON
            data = json.loads(line[9:])
            # Put in queue for SSE to pick up
            forecast_sse_queue.put(data)
    
    process.wait()
    
    # Send completion
    if process.returncode == 0:
        forecast_sse_queue.put({'type': 'end', 'status': 'completed'})
    else:
        forecast_sse_queue.put({'type': 'end', 'status': 'failed'})

# Flask SSE endpoint (in app.py)
@server.route('/api/forecast-progress')
def forecast_progress_sse():
    """SSE endpoint for progress streaming"""
    def generate():
        while True:
            try:
                event = forecast_sse_queue.get(timeout=15)
                event_type = event.get('type', 'progress')
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event)}\n\n"
                
                if event_type == 'end':
                    break
            except queue.Empty:
                yield ": keep-alive\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )
```

**Key Differences:**
- React: Simple async/await with EventSource
- Dash: Complex setup with clientside callbacks + SSE
- React: All in component
- Dash: Spread across page, app.py, and local_service.py
- Dash includes polling fallback (Interval)
- Dash uses queue for subprocess IPC

---

## 4. ACTIVE PROJECT MANAGEMENT

### React+FastAPI
```javascript
// App.jsx or context
const [activeProject, setActiveProject] = useState(() => {
  const saved = sessionStorage.getItem('activeProject');
  return saved ? JSON.parse(saved) : null;
});

useEffect(() => {
  sessionStorage.setItem('activeProject', JSON.stringify(activeProject));
}, [activeProject]);

// When creating/loading project
const handleCreateProject = async (name, location) => {
  const response = await api.post('/project/create', {name, location});
  const newProject = response.data.project;
  
  setActiveProject(newProject);
  // Storage synced by useEffect above
};
```

### Dash
```python
# app.py
app.layout = html.Div([
    # Store for active project (auto-syncs to sessionStorage)
    dcc.Store(id='active-project-store', storage_type='session'),
    
    # ... rest of layout
])

# Validation on app load
@app.callback(
    Output('active-project-store', 'data', allow_duplicate=True),
    Input('active-project-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def validate_project_on_load(active_project):
    """Validate the active project exists when app loads"""
    if active_project and active_project.get('path'):
        project_path = Path(active_project['path'])
        if not project_path.exists():
            return None  # Clear if deleted
    return active_project

# When creating project (in create_project.py)
@callback(
    Output('active-project-store', 'data'),
    Output('selected-page-store', 'data'),
    Input('create-project-btn', 'n_clicks'),
    State('project-name-input', 'value'),
    State('project-location-input', 'value'),
    prevent_initial_call=True
)
def create_project(n_clicks, name, location):
    """Create new project and set as active"""
    if not name or not location:
        return no_update, no_update
    
    result = api.create_project(name, location)
    
    if result['success']:
        new_project = {
            'name': name,
            'path': result['project_path'],
            'lastOpened': datetime.now().isoformat(),
            'id': result['project_id']
        }
        
        # Return both outputs
        # Store auto-saves to sessionStorage
        # Page navigates to next step
        return new_project, 'Demand Projection'
    
    return no_update, no_update
```

**Key Differences:**
- React: Manual useEffect syncing
- Dash: Automatic syncing (storage_type='session')
- React: Imperative updates
- Dash: Declarative callback outputs
- Dash validates on load (React doesn't)

---

## 5. COLORS & SETTINGS MANAGEMENT

### React+FastAPI
```javascript
// Settings/SettingsPage.jsx
import { useState, useEffect } from 'react';
import { useColorConfigStore } from '../stores/colorConfigStore';

export default function SettingsPage() {
  const { colorConfig, setColor } = useColorConfigStore();
  const [colors, setColors] = useState(colorConfig);
  
  useEffect(() => {
    // Load from localStorage or API
    const saved = localStorage.getItem('color-config');
    if (saved) {
      setColors(JSON.parse(saved));
    }
  }, []);
  
  const handleColorChange = (sector, color) => {
    const updated = {...colors, [sector]: color};
    setColors(updated);
    setColor(sector, color);
    
    // Persist
    localStorage.setItem('color-config', JSON.stringify(updated));
  };
  
  return (
    <div className="settings-grid">
      {SECTORS.map(sector => (
        <div key={sector}>
          <label>{sector}</label>
          <input 
            type="color"
            value={colors[sector] || '#000000'}
            onChange={(e) => handleColorChange(sector, e.target.value)}
          />
        </div>
      ))}
    </div>
  );
}

// Store (Zustand)
import create from 'zustand';
import { persist } from 'zustand/middleware';

export const useColorConfigStore = create(
  persist(
    (set) => ({
      colorConfig: {},
      setColor: (sector, color) =>
        set((state) => ({
          colorConfig: {...state.colorConfig, [sector]: color}
        }))
    }),
    {
      name: 'color-config'  // localStorage key
    }
  )
);
```

### Dash
```python
# pages/settings_page.py
def layout():
    """Settings page for color configuration"""
    
    color_config = api.get_color_config()
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3('Color Configuration'),
                html.Div([
                    dbc.FormGroup([
                        dbc.Label(sector),
                        dcc.Input(
                            type='color',
                            id={'type': 'color-input', 'sector': sector},
                            value=color_config['sectors'].get(sector, '#000000'),
                            style={'width': '100%', 'height': '40px'}
                        )
                    ])
                    for sector in color_config['sectors'].keys()
                ]),
                dbc.Button('Save Colors', id='save-colors-btn', color='primary')
            ])
        ]),
        
        # Store for color config
        dcc.Store(id='color-settings-store', 
                 storage_type='local',
                 data=color_config)
    ])

# Callback to handle color changes
@callback(
    Output('color-settings-store', 'data'),
    Input('save-colors-btn', 'n_clicks'),
    [State({'type': 'color-input', 'sector': ALL}, 'value')],
    [State({'type': 'color-input', 'sector': ALL}, 'id')],
    prevent_initial_call=True
)
def save_colors(n_clicks, values, ids):
    """Save color configuration"""
    if not n_clicks:
        return no_update
    
    # Reconstruct color dict from pattern-matching inputs
    colors = {}
    for color_id, value in zip(ids, values):
        sector = color_id['sector']
        colors[sector] = value
    
    # Persist via API
    api.save_color_config({'sectors': colors})
    
    return {'sectors': colors}

# Service (local_service.py)
def get_color_config(self) -> Dict:
    """Get color configuration for sectors"""
    return {
        'sectors': {
            'Agriculture': '#fbbf24',
            'Industrial': '#3b82f6',
            'Domestic': '#10b981',
            'Commercial': '#f97316',
            'Street Lighting': '#8b5cf6'
        }
    }

def save_color_config(self, config: Dict) -> Dict:
    """Save color configuration"""
    # Would save to project.json or database
    return {'success': True}
```

**Key Differences:**
- React: Zustand store with persist middleware
- Dash: dcc.Store with storage_type='local'
- React: Pattern matching in Zustand
- Dash: Pattern matching IDs in callbacks
- React: Can subscribe to changes
- Dash: Must use Input to react to changes

---

## SUMMARY TABLE

| Pattern | React | Dash | Complexity |
|---------|-------|------|------------|
| Navigation | React Router + hooks | dcc.Store + callbacks | Equal |
| State | useState + Zustand | dcc.Store | Simpler in Dash |
| Real-time | EventSource + state | EventSource + store + polling | More complex in Dash |
| Async | async/await + fetch | threading + subprocess | More complex in Dash |
| Sync to Storage | useEffect | Automatic (storage_type) | Simpler in Dash |
| Colors | Zustand persist | dcc.Store + callbacks | Similar |
| Error Handling | try/catch + state | callbacks + exceptions | More complex in Dash |
| Type Safety | TypeScript | Python hints | Better in React |

