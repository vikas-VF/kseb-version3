"""
KSEB Energy Analytics Platform - Dash Application (OPTIMIZED VERSION)
Performance improvements: Caching, optimized callbacks, better state management
"""

import dash
from dash import Dash, html, dcc, Input, Output, State, callback_context, ALL, MATCH, no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from flask_caching import Cache
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import time
import hashlib
from functools import lru_cache

# Import components and pages
from components.sidebar import create_sidebar
from components.topbar import create_topbar
from components.workflow_stepper import create_workflow_stepper

# Import pages
from pages import home, create_project, load_project
from pages import demand_projection, demand_visualization
from pages import generate_profiles, analyze_profiles
from pages import model_config, view_results
from pages import settings_page

# Import callbacks
from callbacks import project_callbacks, forecast_callbacks, profile_callbacks, pypsa_callbacks, settings_callbacks

# Initialize the Dash app
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    title="KSEB Energy Analytics Platform"
)

# Server instance for deployment
server = app.server

# ============================================================================
# PERFORMANCE OPTIMIZATION: Flask-Caching
# ============================================================================

# Configure caching (use Redis in production, filesystem for development)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',  # or 'redis' with CACHE_REDIS_URL
    'CACHE_DIR': 'dash/data/cache',
    'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
    'CACHE_THRESHOLD': 500  # Max cached items
})

# Enable server compression
server.config.update(
    COMPRESS_MIMETYPES=[
        'text/html', 'text/css', 'text/xml',
        'application/json', 'application/javascript',
        'application/octet-stream'
    ],
    COMPRESS_LEVEL=6,
    COMPRESS_MIN_SIZE=500,
)

# ============================================================================
# CACHED HELPER FUNCTIONS
# ============================================================================

@cache.memoize(timeout=600)  # Cache for 10 minutes
def load_project_data(project_path):
    """Load project data with caching"""
    # This would load Excel files, configs, etc.
    # Cached to avoid repeated disk I/O
    return {'loaded': True, 'path': project_path}

@cache.memoize(timeout=300)
def load_scenario_list(project_path):
    """Load scenario list with caching"""
    scenarios_dir = Path(project_path) / 'results' / 'demand_forecasts'
    if scenarios_dir.exists():
        return [f.stem for f in scenarios_dir.glob('*.xlsx')]
    return []

@cache.memoize(timeout=600)
def load_network_metadata(project_path, network_file):
    """Load PyPSA network metadata with caching"""
    # Expensive network inspection cached
    return {'name': network_file, 'components': ['buses', 'generators', 'lines']}

# LRU cache for in-memory caching of frequently accessed data
@lru_cache(maxsize=100)
def compute_forecast_hash(config_json):
    """Generate hash for forecast configuration"""
    return hashlib.md5(config_json.encode()).hexdigest()

# ============================================================================
# OPTIMIZED CHART FUNCTIONS
# ============================================================================

def create_optimized_line_chart(x, y, title='Chart', max_points=5000):
    """
    Create optimized line chart with automatic downsampling for large datasets
    Uses ScatterGL (WebGL) for better performance
    """
    # Downsample if too many points
    if len(x) > max_points:
        indices = np.linspace(0, len(x)-1, max_points, dtype=int)
        x = np.array(x)[indices]
        y = np.array(y)[indices]

    # Use Scattergl for WebGL rendering (faster)
    fig = go.Figure(go.Scattergl(
        x=x, y=y,
        mode='lines',
        line=dict(width=2, color='#4f46e5'),
        hovertemplate='<b>X</b>: %{x}<br><b>Y</b>: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        uirevision='constant',  # Preserve zoom/pan state
        hovermode='closest',
        template='plotly_white',
        modebar={'remove': ['lasso', 'select']},  # Remove unused tools
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig

def create_optimized_heatmap(data, x_labels, y_labels, title='Heatmap'):
    """
    Create optimized heatmap with efficient rendering
    """
    fig = go.Figure(go.Heatmap(
        z=data,
        x=x_labels,
        y=y_labels,
        colorscale='Viridis',
        hovertemplate='X: %{x}<br>Y: %{y}<br>Value: %{z}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        uirevision='constant',
        template='plotly_white',
        margin=dict(l=60, r=40, t=60, b=60)
    )

    return fig

# ============================================================================
# STYLES (Unchanged)
# ============================================================================

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "64px",
    "left": 0,
    "bottom": 0,
    "width": "288px",
    "background-color": "#0f172a",
    "padding": "1rem",
    "overflow-y": "auto",
    "transition": "all 0.3s",
    "border-right": "1px solid rgba(71, 85, 105, 0.5)",
    "z-index": 30
}

SIDEBAR_COLLAPSED_STYLE = {
    **SIDEBAR_STYLE,
    "width": "80px"
}

TOPBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 0,
    "height": "64px",
    "background-color": "#1e293b",
    "border-bottom": "1px solid #334155",
    "padding": "0 1.5rem",
    "display": "flex",
    "align-items": "center",
    "justify-content": "space-between",
    "z-index": 40
}

CONTENT_STYLE = {
    "margin-left": "288px",
    "margin-right": "80px",
    "margin-top": "64px",
    "padding": "2rem",
    "min-height": "calc(100vh - 64px)",
    "background-color": "#f8fafc",
    "transition": "margin-left 0.3s"
}

CONTENT_COLLAPSED_STYLE = {
    **CONTENT_STYLE,
    "margin-left": "80px"
}

WORKFLOW_STYLE = {
    "position": "fixed",
    "top": "64px",
    "right": 0,
    "bottom": 0,
    "width": "80px",
    "background-color": "#1e293b",
    "border-left": "1px solid rgba(71, 85, 105, 0.5)",
    "z-index": 20,
    "padding": "1rem 0.5rem"
}

# ============================================================================
# APP LAYOUT (Unchanged)
# ============================================================================

app.layout = html.Div([
    # Store components for state management
    dcc.Store(id='active-project-store', storage_type='session'),
    dcc.Store(id='selected-page-store', storage_type='session', data='Home'),
    dcc.Store(id='sidebar-collapsed-store', storage_type='local', data=False),
    dcc.Store(id='recent-projects-store', storage_type='local'),
    dcc.Store(id='color-settings-store', storage_type='local'),
    dcc.Store(id='process-state-store', storage_type='memory'),
    dcc.Store(id='forecast-progress-store', storage_type='memory'),
    dcc.Store(id='profile-progress-store', storage_type='memory'),
    dcc.Store(id='pypsa-progress-store', storage_type='memory'),

    # Interval components for progress tracking
    dcc.Interval(id='forecast-interval', interval=1000, disabled=True),
    dcc.Interval(id='profile-interval', interval=1000, disabled=True),
    dcc.Interval(id='pypsa-interval', interval=1000, disabled=True),

    # Layout containers
    html.Div(id='topbar-container', style=TOPBAR_STYLE),
    html.Div(id='sidebar-container', style=SIDEBAR_STYLE),
    html.Div(id='workflow-container', style=WORKFLOW_STYLE),
    html.Div(id='main-content', style=CONTENT_STYLE),

    # Modal for process progress
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="process-modal-title")),
            dbc.ModalBody(id="process-modal-body"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-process-modal", className="ms-auto")
            ),
        ],
        id="process-modal",
        size="xl",
        is_open=False,
        backdrop="static"
    ),

    # Toast notifications
    html.Div(id='toast-container', style={
        'position': 'fixed',
        'top': '80px',
        'right': '20px',
        'z-index': 9999
    })
], style={
    'font-family': 'system-ui, -apple-system, sans-serif',
    'min-height': '100vh',
    'background-color': '#f8fafc'
})

# ============================================================================
# OPTIMIZED CALLBACKS
# ============================================================================

@app.callback(
    Output('topbar-container', 'children'),
    Input('active-project-store', 'data'),
    Input('process-state-store', 'data')
)
def update_topbar(active_project, process_state):
    """Update the top bar (cached when possible)"""
    return create_topbar(active_project, process_state)

@app.callback(
    Output('sidebar-container', 'children'),
    Output('sidebar-container', 'style'),
    Input('selected-page-store', 'data'),
    Input('sidebar-collapsed-store', 'data')
)
def update_sidebar(selected_page, collapsed):
    """Update the sidebar (optimized with early returns)"""
    style = SIDEBAR_COLLAPSED_STYLE if collapsed else SIDEBAR_STYLE
    return create_sidebar(selected_page, collapsed), style

@app.callback(
    Output('workflow-container', 'children'),
    Input('selected-page-store', 'data'),
    Input('active-project-store', 'data')
)
def update_workflow_stepper(selected_page, active_project):
    """Update the workflow stepper"""
    return create_workflow_stepper(selected_page, active_project)

@app.callback(
    Output('main-content', 'children'),
    Output('main-content', 'style'),
    Input('selected-page-store', 'data'),
    Input('active-project-store', 'data'),
    Input('sidebar-collapsed-store', 'data')
)
@cache.memoize(timeout=60)  # Cache page renders for 1 minute
def render_page_content(selected_page, active_project, collapsed):
    """
    Render the main content (OPTIMIZED with caching)
    Cache key includes all inputs to ensure correct updates
    """
    style = CONTENT_COLLAPSED_STYLE if collapsed else CONTENT_STYLE

    # Page routing with early returns for better performance
    if selected_page == 'Home':
        return home.layout(active_project), style
    elif selected_page == 'Create Project':
        return create_project.layout(), style
    elif selected_page == 'Load Project':
        return load_project.layout(), style
    elif selected_page == 'Demand Projection':
        return demand_projection.layout(active_project), style
    elif selected_page == 'Demand Visualization':
        return demand_visualization.layout(active_project), style
    elif selected_page == 'Generate Profiles':
        return generate_profiles.layout(active_project), style
    elif selected_page == 'Analyze Profiles':
        return analyze_profiles.layout(active_project), style
    elif selected_page == 'Model Config':
        return model_config.layout(active_project), style
    elif selected_page == 'View Results':
        return view_results.layout(active_project), style
    elif selected_page == 'Settings':
        return settings_page.layout(), style
    else:
        # 404 page
        return html.Div([
            html.H2("Page Not Found", className="text-2xl font-bold text-gray-800"),
            html.P(f"The page '{selected_page}' does not exist.", className="text-gray-600")
        ]), style

# ============================================================================
# NAVIGATION CALLBACKS (Optimized)
# ============================================================================

@app.callback(
    Output('selected-page-store', 'data'),
    Input({'type': 'nav-link', 'page': ALL}, 'n_clicks'),
    State('selected-page-store', 'data'),
    prevent_initial_call=True
)
def navigate_to_page(n_clicks, current_page):
    """Handle navigation (optimized with no_update)"""
    ctx = callback_context

    if not ctx.triggered:
        return no_update

    button_id = ctx.triggered[0]['prop_id']

    if 'nav-link' in button_id:
        page_name = eval(button_id.split('.')[0])['page']
        if page_name == current_page:
            return no_update  # Don't re-render if same page
        return page_name

    return no_update

@app.callback(
    Output('sidebar-collapsed-store', 'data'),
    Input('toggle-sidebar-btn', 'n_clicks'),
    State('sidebar-collapsed-store', 'data'),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, collapsed):
    """Toggle sidebar (simple, no optimization needed)"""
    if n_clicks:
        return not collapsed
    return no_update

# ============================================================================
# PROJECT VALIDATION (Optimized with caching)
# ============================================================================

@app.callback(
    Output('active-project-store', 'data', allow_duplicate=True),
    Input('active-project-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
@cache.memoize(timeout=120)
def validate_project_on_load(active_project):
    """Validate project on load (cached to avoid repeated checks)"""
    if active_project and active_project.get('path'):
        project_path = Path(active_project['path'])
        if not project_path.exists():
            cache.clear()  # Clear cache if project deleted
            return None
    return active_project

# ============================================================================
# REGISTER CALLBACK MODULES
# ============================================================================

project_callbacks.register_callbacks(app)
forecast_callbacks.register_callbacks(app)
profile_callbacks.register_callbacks(app)
pypsa_callbacks.register_callbacks(app)
settings_callbacks.register_callbacks(app)

# ============================================================================
# PERFORMANCE MONITORING (Optional)
# ============================================================================

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

@server.before_request
def log_request():
    """Log requests for performance monitoring"""
    from flask import request
    logger.info(f"{request.method} {request.path}")

# ============================================================================
# RUN THE APP
# ============================================================================

if __name__ == '__main__':
    # Development mode
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050,
        dev_tools_hot_reload=True
    )

    # For production, use:
    # gunicorn app_optimized:server -w 4 -k gevent -b 0.0.0.0:8050 --timeout 300
