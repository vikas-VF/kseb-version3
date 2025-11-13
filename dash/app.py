"""
KSEB Energy Analytics Platform - Dash Application
This is a complete conversion of the React + FastAPI application to Dash/Plotly Dash
"""

import dash
from dash import Dash, html, dcc, Input, Output, State, callback_context, ALL, MATCH
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
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

# Import components and pages
from components.sidebar import create_sidebar
from components.topbar import create_topbar
from components.workflow_stepper import create_workflow_stepper

# Import pages
from pages import home, create_project, load_project
from pages import demand_projection, demand_visualization
from pages import generate_profiles, analyze_profiles
from pages import model_config, view_results
from pages import settings_page, other_tools

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

# Global styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "64px",
    "left": 0,
    "bottom": 0,
    "width": "288px",
    "backgroundColor": "#0f172a",  # slate-900
    "padding": "1rem",
    "overflowY": "auto",
    "transition": "all 0.3s",
    "borderRight": "1px solid rgba(71, 85, 105, 0.5)",  # slate-700/50
    "zIndex": 30
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
    "backgroundColor": "#1e293b",  # slate-800
    "borderBottom": "1px solid #334155",  # slate-700
    "padding": "0 1.5rem",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "zIndex": 40
}

CONTENT_STYLE = {
    "marginLeft": "288px",
    "marginRight": "80px",
    "marginTop": "64px",
    "padding": "2rem",
    "minHeight": "calc(100vh - 64px)",
    "backgroundColor": "#f8fafc",  # slate-50
    "transition": "margin-left 0.3s"
}

CONTENT_COLLAPSED_STYLE = {
    **CONTENT_STYLE,
    "marginLeft": "80px"
}

WORKFLOW_STYLE = {
    "position": "fixed",
    "top": "64px",
    "right": 0,
    "bottom": 0,
    "width": "80px",
    "backgroundColor": "#1e293b",  # slate-800
    "borderLeft": "1px solid rgba(71, 85, 105, 0.5)",
    "zIndex": 20,
    "padding": "1rem 0.5rem"
}

# App layout
app.layout = html.Div([
    # Location component for URL-based navigation
    dcc.Location(id='url', refresh=False),

    # Store components for state management (replacing React state/Zustand)
    dcc.Store(id='active-project-store', storage_type='session'),  # Active project
    dcc.Store(id='selected-page-store', storage_type='session', data='Home'),  # Current page
    dcc.Store(id='sidebar-collapsed-store', storage_type='local', data=False),  # Sidebar state
    dcc.Store(id='recent-projects-store', storage_type='local'),  # Recent projects
    dcc.Store(id='color-settings-store', storage_type='local'),  # Color settings
    dcc.Store(id='process-state-store', storage_type='memory'),  # Process states
    dcc.Store(id='forecast-progress-store', storage_type='memory'),  # Forecast progress
    dcc.Store(id='profile-progress-store', storage_type='memory'),  # Profile progress
    dcc.Store(id='pypsa-progress-store', storage_type='memory'),  # PyPSA progress

    # Interval components for progress tracking (replacing SSE)
    dcc.Interval(id='forecast-interval', interval=1000, disabled=True),  # 1 second
    dcc.Interval(id='profile-interval', interval=1000, disabled=True),
    dcc.Interval(id='pypsa-interval', interval=1000, disabled=True),

    # Top bar (fixed header)
    html.Div(id='topbar-container', style=TOPBAR_STYLE),

    # Sidebar (fixed left navigation)
    html.Div(id='sidebar-container', style=SIDEBAR_STYLE),

    # Workflow stepper (fixed right sidebar)
    html.Div(id='workflow-container', style=WORKFLOW_STYLE),

    # Main content area (dynamic based on selected page)
    html.Div(id='main-content', style=CONTENT_STYLE),

    # Modal for process progress (replacing ProcessModal)
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

    # Toast notifications (replacing react-hot-toast)
    html.Div(id='toast-container', style={
        'position': 'fixed',
        'top': '80px',
        'right': '20px',
        'zIndex': 9999
    })
], style={
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'minHeight': '100vh',
    'backgroundColor': '#f8fafc'
})

# =============================================================================
# MAIN LAYOUT CALLBACKS
# =============================================================================

@app.callback(
    Output('topbar-container', 'children'),
    Input('active-project-store', 'data'),
    Input('process-state-store', 'data')
)
def update_topbar(active_project, process_state):
    """Update the top bar with active project and process status"""
    return create_topbar(active_project, process_state)

@app.callback(
    Output('sidebar-container', 'children'),
    Output('sidebar-container', 'style'),
    Input('selected-page-store', 'data'),
    Input('sidebar-collapsed-store', 'data')
)
def update_sidebar(selected_page, collapsed):
    """Update the sidebar based on selected page and collapsed state"""
    style = SIDEBAR_COLLAPSED_STYLE if collapsed else SIDEBAR_STYLE
    return create_sidebar(selected_page, collapsed), style

@app.callback(
    Output('workflow-container', 'children'),
    Input('selected-page-store', 'data'),
    Input('active-project-store', 'data')
)
def update_workflow_stepper(selected_page, active_project):
    """Update the workflow stepper based on selected page"""
    return create_workflow_stepper(selected_page, active_project)

@app.callback(
    Output('main-content', 'children'),
    Output('main-content', 'style'),
    Input('selected-page-store', 'data'),
    Input('active-project-store', 'data'),
    Input('sidebar-collapsed-store', 'data')
)
def render_page_content(selected_page, active_project, collapsed):
    """Render the main content based on selected page"""
    style = CONTENT_COLLAPSED_STYLE if collapsed else CONTENT_STYLE

    # Page routing
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
    elif selected_page == 'Other Tools':
        return other_tools.layout(), style
    else:
        return html.Div([
            html.H2("Page Not Found", className="text-2xl font-bold text-gray-800"),
            html.P(f"The page '{selected_page}' does not exist.", className="text-gray-600")
        ]), style

# =============================================================================
# NAVIGATION CALLBACKS
# =============================================================================

@app.callback(
    Output('selected-page-store', 'data'),
    Input({'type': 'nav-link', 'page': ALL}, 'n_clicks'),
    State('selected-page-store', 'data'),
    prevent_initial_call=True
)
def navigate_to_page(n_clicks, current_page):
    """Handle navigation when sidebar items are clicked"""
    if not callback_context.triggered:
        raise PreventUpdate

    button_id = callback_context.triggered[0]['prop_id']
    if 'nav-link' in button_id:
        # Extract the page name from the button ID
        page_name = eval(button_id.split('.')[0])['page']
        return page_name

    return current_page

@app.callback(
    Output('sidebar-collapsed-store', 'data'),
    Input('toggle-sidebar-btn', 'n_clicks'),
    State('sidebar-collapsed-store', 'data'),
    prevent_initial_call=True
)
def toggle_sidebar(n_clicks, collapsed):
    """Toggle sidebar collapsed state"""
    if n_clicks:
        return not collapsed
    return collapsed

# =============================================================================
# PROJECT VALIDATION ON APP LOAD
# =============================================================================

@app.callback(
    Output('active-project-store', 'data', allow_duplicate=True),
    Input('active-project-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def validate_project_on_load(active_project):
    """Validate the active project when the app loads"""
    if active_project and active_project.get('path'):
        # Check if the project directory still exists
        project_path = Path(active_project['path'])
        if not project_path.exists():
            # Project no longer exists, clear it
            return None
    return active_project

# =============================================================================
# REGISTER ALL CALLBACKS FROM CALLBACK MODULES
# =============================================================================

# Register project management callbacks
project_callbacks.register_callbacks(app)

# Register forecast callbacks
forecast_callbacks.register_callbacks(app)

# Register profile callbacks
profile_callbacks.register_callbacks(app)

# Register PyPSA callbacks
pypsa_callbacks.register_callbacks(app)

# Register settings callbacks
settings_callbacks.register_callbacks(app)

# =============================================================================
# FLASK SSE ROUTES (Server-Sent Events for Real-Time Progress)
# =============================================================================

from flask import Response, stream_with_context
import queue as queue_module

# Import the global forecast SSE queue from local_service
from services.local_service import forecast_sse_queue

@server.route('/api/forecast-progress')
def forecast_progress_sse():
    """
    Server-Sent Events endpoint for demand forecast progress.
    Streams progress events from the forecasting subprocess to the frontend.
    Matches FastAPI implementation in forecast_routes.py:49-108
    """
    def generate():
        try:
            while True:
                try:
                    # Get event from queue (blocks until available or timeout)
                    event = forecast_sse_queue.get(timeout=15)

                    # Send event
                    event_type = event.get('type', 'progress')
                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event)}\n\n"

                    # Check if this is the end event
                    if event_type == 'end':
                        break

                except queue_module.Empty:
                    # Timeout - send keep-alive comment
                    yield ": keep-alive\n\n"

        except Exception as e:
            print(f"SSE error: {e}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

# =============================================================================
# RUN THE APP
# =============================================================================

if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050,
        dev_tools_hot_reload=True
    )
