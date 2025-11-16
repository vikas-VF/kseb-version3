"""
PyPSA Model Configuration Page
================================
Configure and execute PyPSA optimization models.

Features:
- Scenario name configuration with duplicate check
- Solver selection (Highs)
- Configuration summary display
- Model execution with progress tracking
- Real-time logs via polling
- Process modal with minimize/maximize
- Floating indicator when minimized
- Stop model functionality
"""

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json

# Note: This page uses manual routing in app.py, not dash.register_page()

# Constants
DEFAULT_SCENARIO_NAME = 'PyPSA_Scenario_V1'
SOLVER_OPTIONS = [
    {'value': 'highs', 'label': 'Highs', 'description': 'Fast and reliable open-source solver (Default)'}
]

# =====================================================================
# LAYOUT
# =====================================================================

def layout(active_project=None):
    """Main layout for PyPSA Model Configuration page."""
    return html.Div([
        # State stores
        dcc.Store(id='pypsa-config-state', data={
            'scenarioName': DEFAULT_SCENARIO_NAME,
            'solver': 'highs',
            'existingScenarios': [],
            'error': ''
        }),
        dcc.Store(id='pypsa-process-state', data={
            'isRunning': False,
            'status': 'idle',  # idle, running, completed, failed
            'percentage': 0,
            'message': '',
            'logs': [],
            'modalVisible': False,
            'modalMinimized': False
        }),

        # Polling interval for progress (disabled by default)
        dcc.Interval(id='pypsa-progress-interval', interval=1000, disabled=True),

        # Main content
        html.Div([
            html.Div([
                # Centered card
                html.Div([
                    # Header
                    html.Header([
                        html.Div([
                            html.I(className='bi bi-gear-fill', style={
                                'fontSize': '1.75rem',
                                'color': '#4f46e5'
                            }),
                            html.Div([
                                html.H1('PyPSA Model Configuration', className='text-xl font-bold text-slate-800 mb-0'),
                                html.P('Configure scenario and solver settings for grid optimization',
                                      className='text-sm text-slate-600 mb-0')
                            ], className='ms-3')
                        ], className='d-flex align-items-center gap-3')
                    ], className='px-4 py-3 border-bottom border-slate-200', style={
                        'background': 'linear-gradient(to right, #e0e7ff, #f3e8ff)'
                    }),

                    # Main content
                    html.Main([
                        # Error banner
                        html.Div(id='pypsa-error-banner'),

                        # Basic Configuration
                        html.Div([
                            html.H3('Basic Configuration', className='text-base font-bold text-slate-800 mb-3'),

                            dbc.Row([
                                # Scenario Name
                                dbc.Col([
                                    dbc.Label('Scenario Name', html_for='pypsa-scenario-name',
                                             className='text-sm font-bold text-slate-700 mb-2'),
                                    html.Span(' *', className='text-danger'),
                                    dbc.Input(
                                        id='pypsa-scenario-name',
                                        type='text',
                                        placeholder=DEFAULT_SCENARIO_NAME,
                                        value=DEFAULT_SCENARIO_NAME,
                                        className='mb-2'
                                    ),
                                    html.P('Enter a unique name for your scenario',
                                          className='text-xs text-slate-500 mb-2'),
                                    html.Div(id='pypsa-duplicate-warning')
                                ], md=6),

                                # Solver Selection
                                dbc.Col([
                                    dbc.Label('Optimization Solver', html_for='pypsa-solver',
                                             className='text-sm font-bold text-slate-700 mb-2'),
                                    html.Span(' *', className='text-danger'),
                                    dbc.Select(
                                        id='pypsa-solver',
                                        options=[
                                            {'label': opt['label'], 'value': opt['value']}
                                            for opt in SOLVER_OPTIONS
                                        ],
                                        value='highs',
                                        className='mb-2'
                                    ),
                                    html.P(id='pypsa-solver-description',
                                          className='text-xs text-slate-500')
                                ], md=6)
                            ], className='g-3')
                        ], className='mb-4'),

                        # Info Box
                        dbc.Alert([
                            html.Div([
                                html.I(className='bi bi-info-circle-fill text-primary',
                                      style={'fontSize': '1.25rem'}),
                                html.Div([
                                    html.P('About PyPSA Optimization',
                                          className='font-semibold mb-2 text-sm'),
                                    html.P([
                                        'PyPSA (Python for Power System Analysis) performs optimal power flow and capacity ',
                                        'expansion planning. The selected solver will be used to optimize the power system ',
                                        'network based on your input data.'
                                    ], className='mb-2 text-sm'),
                                    html.P([
                                        html.Strong('Recommended: '),
                                        'Highs solver offers the best balance of speed and reliability for most use cases.'
                                    ], className='mb-0 text-sm')
                                ], className='ms-3')
                            ], className='d-flex gap-3')
                        ], color='info', className='mb-4'),

                        # Configuration Summary
                        html.Div([
                            html.Div([
                                html.I(className='bi bi-check-circle-fill text-indigo-600 me-2',
                                      style={'fontSize': '1.25rem'}),
                                html.H3('Configuration Summary',
                                       className='text-base font-bold text-slate-800 mb-0')
                            ], className='d-flex align-items-center mb-3'),

                            html.Div(id='pypsa-config-summary')
                        ], className='p-4 rounded border-2', style={
                            'background': 'linear-gradient(to bottom right, #e0e7ff, #f3e8ff)',
                            'borderColor': '#a5b4fc'
                        })
                    ], className='p-4', style={'maxHeight': '70vh', 'overflowY': 'auto'}),

                    # Footer
                    html.Footer([
                        dbc.Button(
                            id='pypsa-run-model-btn',
                            children=[
                                html.I(className='bi bi-play-fill me-2'),
                                'Apply Configuration & Run Model'
                            ],
                            color='primary',
                            className='px-4 py-2',
                            size='lg'
                        )
                    ], className='d-flex justify-content-end gap-3 px-4 py-3 bg-slate-50 border-top')
                ], className='bg-white rounded shadow-lg border', style={
                    'maxWidth': '72rem',
                    'maxHeight': '90vh',
                    'display': 'flex',
                    'flexDirection': 'column'
                })
            ], className='d-flex align-items-center justify-content-center', style={
                'minHeight': '100vh',
                'padding': '1.5rem'
            })
        ], style={
            'background': 'linear-gradient(to bottom right, #f8fafc, #f1f5f9)',
            'minHeight': '100vh'
        }),

        # Process Modal
        html.Div(id='pypsa-process-modal-container'),

        # Floating Indicator
        html.Div(id='pypsa-floating-indicator')
    ])


# =====================================================================
# CALLBACKS - INITIALIZATION
# =====================================================================

@callback(
    Output('pypsa-config-state', 'data', allow_duplicate=True),
    Input('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_existing_scenarios(active_project):
    """Load existing PyPSA scenarios from backend."""
    if not active_project or not active_project.get('path'):
        return dash.no_update

    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.local_service import service as api

    try:
        response = api.get_pypsa_scenarios(active_project['path'])
        scenarios = response.get('scenarios', [])

        return {
            'scenarioName': DEFAULT_SCENARIO_NAME,
            'solver': 'highs',
            'existingScenarios': scenarios,
            'error': ''
        }
    except Exception as e:
        print(f'[PyPSA Config] Error loading scenarios: {e}')
        return {
            'scenarioName': DEFAULT_SCENARIO_NAME,
            'solver': 'highs',
            'existingScenarios': [],
            'error': ''
        }


# =====================================================================
# CALLBACKS - FORM UPDATES
# =====================================================================

@callback(
    Output('pypsa-config-state', 'data', allow_duplicate=True),
    Input('pypsa-scenario-name', 'value'),
    State('pypsa-config-state', 'data'),
    prevent_initial_call=True
)
def update_scenario_name(name, config_state):
    """Update scenario name in state."""
    config_state['scenarioName'] = name or DEFAULT_SCENARIO_NAME
    return config_state


@callback(
    Output('pypsa-config-state', 'data', allow_duplicate=True),
    Input('pypsa-solver', 'value'),
    State('pypsa-config-state', 'data'),
    prevent_initial_call=True
)
def update_solver(solver, config_state):
    """Update solver in state."""
    config_state['solver'] = solver
    return config_state


@callback(
    Output('pypsa-solver-description', 'children'),
    Input('pypsa-solver', 'value')
)
def update_solver_description(solver):
    """Update solver description based on selection."""
    for opt in SOLVER_OPTIONS:
        if opt['value'] == solver:
            return opt['description']
    return ''


@callback(
    Output('pypsa-duplicate-warning', 'children'),
    Input('pypsa-config-state', 'data')
)
def show_duplicate_warning(config_state):
    """Show warning if scenario name already exists."""
    scenario_name = config_state.get('scenarioName', '').strip() or DEFAULT_SCENARIO_NAME
    existing = config_state.get('existingScenarios', [])

    is_duplicate = any(
        existing_name.lower() == scenario_name.lower()
        for existing_name in existing
    )

    if is_duplicate and scenario_name:
        return dbc.Alert([
            html.P([
                html.I(className='bi bi-exclamation-triangle-fill me-2'),
                html.Strong('Warning: This scenario name already exists')
            ], className='text-sm mb-1'),
            html.P(
                'Running this configuration will overwrite the old scenario results with new results.',
                className='text-xs mb-0'
            )
        ], color='warning', className='mt-2 py-2')

    return html.Div()


@callback(
    Output('pypsa-config-summary', 'children'),
    Input('pypsa-config-state', 'data'),
    State('active-project-store', 'data')
)
def update_config_summary(config_state, active_project):
    """Update configuration summary display."""
    scenario_name = config_state.get('scenarioName', DEFAULT_SCENARIO_NAME) or DEFAULT_SCENARIO_NAME
    solver = config_state.get('solver', 'highs')
    project_path = active_project.get('path', '(no project loaded)') if active_project else '(no project loaded)'

    solver_label = next((opt['label'] for opt in SOLVER_OPTIONS if opt['value'] == solver), solver)

    return html.Div([
        # Scenario Name
        html.Div([
            html.Div([
                html.I(className='bi bi-file-text text-indigo-600 me-3',
                      style={'fontSize': '1rem'}),
                html.Span('Scenario Name', className='text-sm font-medium text-slate-600')
            ], className='d-flex align-items-center'),
            html.Span(scenario_name, className='text-sm font-bold text-slate-800')
        ], className='d-flex justify-content-between align-items-center bg-white rounded px-3 py-2 shadow-sm mb-2'),

        # Solver
        html.Div([
            html.Div([
                html.I(className='bi bi-wrench text-indigo-600 me-3',
                      style={'fontSize': '1rem'}),
                html.Span('Solver', className='text-sm font-medium text-slate-600')
            ], className='d-flex align-items-center'),
            html.Span(solver_label, className='text-sm font-bold text-slate-800')
        ], className='d-flex justify-content-between align-items-center bg-white rounded px-3 py-2 shadow-sm mb-2'),

        # Project Path
        html.Div([
            html.Div([
                html.I(className='bi bi-folder-fill text-indigo-600 me-3',
                      style={'fontSize': '1rem'}),
                html.Span('Project Path', className='text-sm font-medium text-slate-600')
            ], className='d-flex align-items-center'),
            html.Span(project_path, className='text-xs font-medium text-slate-700',
                     style={'maxWidth': '24rem', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
                     title=project_path)
        ], className='d-flex justify-content-between align-items-center bg-white rounded px-3 py-2 shadow-sm')
    ])


@callback(
    Output('pypsa-error-banner', 'children'),
    Input('pypsa-config-state', 'data')
)
def show_error_banner(config_state):
    """Show error banner if there's an error."""
    error = config_state.get('error', '')

    if error:
        return dbc.Alert([
            html.I(className='bi bi-exclamation-triangle-fill me-3',
                  style={'fontSize': '1.25rem'}),
            html.Div([
                html.P('Configuration Error', className='font-bold mb-1'),
                html.P(error, className='mb-0')
            ])
        ], color='danger', className='d-flex align-items-start gap-3 mb-3')

    return html.Div()


# =====================================================================
# CALLBACKS - MODEL EXECUTION
# =====================================================================

@callback(
    [
        Output('pypsa-process-state', 'data', allow_duplicate=True),
        Output('pypsa-progress-interval', 'disabled', allow_duplicate=True),
        Output('pypsa-config-state', 'data', allow_duplicate=True)
    ],
    Input('pypsa-run-model-btn', 'n_clicks'),
    [
        State('pypsa-config-state', 'data'),
        State('pypsa-process-state', 'data'),
        State('active-project-store', 'data')
    ],
    prevent_initial_call=True
)
def start_model_execution(n_clicks, config_state, process_state, active_project):
    """Start PyPSA model execution."""
    if not n_clicks:
        raise PreventUpdate

    if not active_project or not active_project.get('path'):
        config_state['error'] = 'No active project found. Please load a project first.'
        return dash.no_update, dash.no_update, config_state

    if process_state.get('isRunning'):
        config_state['error'] = 'A PyPSA model is already running. Please wait for it to complete or stop it first.'
        return dash.no_update, dash.no_update, config_state

    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.local_service import service as api
    import uuid

    scenario_name = config_state.get('scenarioName', '').strip() or DEFAULT_SCENARIO_NAME
    solver = config_state.get('solver', 'highs')
    project_path = active_project['path']

    try:
        # Generate unique process ID (CRITICAL FIX: Now properly tracked)
        process_id = str(uuid.uuid4())

        # Update process state immediately
        process_state['process_id'] = process_id  # ✅ FIX: Store process_id
        process_state['isRunning'] = True
        process_state['status'] = 'running'
        process_state['percentage'] = 10
        process_state['message'] = 'Starting PyPSA model execution...'
        process_state['logs'] = [
            {'timestamp': time.strftime('%H:%M:%S'), 'level': 'info', 'text': f'Started PyPSA model: {scenario_name}'},
            {'timestamp': time.strftime('%H:%M:%S'), 'level': 'info', 'text': f'Solver: {solver}'},
            {'timestamp': time.strftime('%H:%M:%S'), 'level': 'info', 'text': f'Process ID: {process_id}'},
            {'timestamp': time.strftime('%H:%M:%S'), 'level': 'info', 'text': 'Initializing model...'}
        ]
        process_state['modalVisible'] = True
        process_state['modalMinimized'] = False

        # Prepare config for PyPSA model
        pypsa_config = {
            'project_path': project_path,
            'scenario_name': scenario_name,
            'solver': solver
        }

        # ✅ FIX: Start execution in background using new async method
        result = api.run_pypsa_model(pypsa_config, process_id=process_id)

        if not result.get('success'):
            # Failed to start
            process_state['isRunning'] = False
            process_state['status'] = 'failed'
            process_state['logs'].append({
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'error',
                'text': f'❌ Failed to start: {result.get("error", "Unknown error")}'
            })
            config_state['error'] = result.get('error', 'Failed to start model')
            return process_state, True, config_state  # Disable polling

        # Successfully started
        print(f"[PyPSA] Model execution started with process_id: {process_id}")
        config_state['error'] = ''

        return process_state, False, config_state  # Enable polling

    except Exception as e:
        config_state['error'] = f'Failed to start model: {str(e)}'
        return dash.no_update, dash.no_update, config_state


@callback(
    [
        Output('pypsa-process-state', 'data', allow_duplicate=True),
        Output('pypsa-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('pypsa-progress-interval', 'n_intervals'),
    [
        State('pypsa-process-state', 'data'),
        State('active-project-store', 'data'),
        State('selected-page-store', 'data')  # CRITICAL FIX: Check current page
    ],
    prevent_initial_call=True
)
def poll_model_progress(n_intervals, process_state, active_project, current_page):
    """Poll model progress from backend."""
    # CRITICAL FIX: Stop polling if navigated away from Model Config page
    # This prevents React warnings about updating unmounted components
    if current_page != 'Model Config':
        return dash.no_update, True  # Disable polling

    if not process_state.get('isRunning'):
        return dash.no_update, True  # Disable polling

    # ✅ FIX: Poll REAL progress from backend (not simulated)

    try:
        process_id = process_state.get('process_id')

        if not process_id:
            print('[PyPSA Config] Warning: No process_id found, stopping polling')
            return process_state, True  # Disable polling

        # Get real progress from backend
        from services.local_service import service as api
        progress_result = api.get_pypsa_progress(process_id)

        if not progress_result.get('success'):
            # Process not found or error
            print(f'[PyPSA Config] Error getting progress: {progress_result.get("error")}')
            process_state['isRunning'] = False
            process_state['status'] = 'failed'
            process_state['logs'].append({
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'error',
                'text': f'❌ Error: {progress_result.get("error", "Unknown error")}'
            })
            return process_state, True  # Disable polling

        # Update process state with real data
        backend_status = progress_result.get('status', 'unknown')
        process_state['status'] = backend_status
        process_state['percentage'] = progress_result.get('progress', 0)
        process_state['message'] = progress_result.get('message', '')

        # Append new logs (only logs not already shown)
        backend_logs = progress_result.get('logs', [])
        current_log_count = len(process_state.get('logs', []))
        new_logs = backend_logs[current_log_count:]  # Get only new logs
        if new_logs:
            process_state['logs'].extend(new_logs)

        # Check if completed or failed
        if backend_status == 'completed':
            process_state['isRunning'] = False
            print(f'[PyPSA Config] Model completed successfully')
            return process_state, True  # Disable polling

        elif backend_status == 'failed':
            process_state['isRunning'] = False
            error_msg = progress_result.get('error', 'Unknown error')
            print(f'[PyPSA Config] Model failed: {error_msg}')
            return process_state, True  # Disable polling

        # Still running, continue polling
        return process_state, False

    except Exception as e:
        print(f'[PyPSA Config] Exception polling progress: {e}')
        import traceback
        traceback.print_exc()
        process_state['isRunning'] = False
        process_state['status'] = 'failed'
        process_state['logs'].append({
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'error',
            'text': f'❌ Exception: {str(e)}'
        })
        return process_state, True  # Disable polling


# =====================================================================
# CALLBACKS - PROCESS MODAL
# =====================================================================

@callback(
    Output('pypsa-process-modal-container', 'children'),
    Input('pypsa-process-state', 'data')
)
def render_process_modal(process_state):
    """Render process modal."""
    if not process_state.get('modalVisible'):
        return html.Div()

    if process_state.get('modalMinimized'):
        return html.Div()

    status = process_state.get('status', 'idle')
    percentage = process_state.get('percentage', 0)
    message = process_state.get('message', '')
    logs = process_state.get('logs', [])
    is_running = process_state.get('isRunning', False)

    # Status icon and color
    if status == 'completed':
        status_icon = 'bi-check-circle-fill'
        status_color = 'success'
    elif status == 'failed':
        status_icon = 'bi-x-circle-fill'
        status_color = 'danger'
    else:
        status_icon = 'bi-arrow-repeat'
        status_color = 'primary'

    return dbc.Modal([
        dbc.ModalHeader([
            html.Div([
                html.I(className=f'bi {status_icon} me-2', style={'fontSize': '1.25rem'}),
                html.H5('PyPSA Model Execution', className='mb-0')
            ], className='d-flex align-items-center')
        ]),
        dbc.ModalBody([
            # Progress bar
            html.Div([
                dbc.Progress(
                    value=percentage,
                    label=f'{percentage}%',
                    className='mb-2',
                    style={'height': '24px'},
                    color=status_color
                ),
                html.P(message, className='text-sm text-muted mb-3')
            ]),

            # Logs
            html.Div([
                html.H6('Process Logs:', className='mb-2'),
                html.Div([
                    html.Div([
                        html.Span(log.get('timestamp', ''), className='text-muted me-2', style={'fontFamily': 'monospace'}),
                        html.Span(log.get('text', ''), className='text-sm')
                    ], className='mb-1')
                    for log in logs[-20:]  # Show last 20 logs
                ], className='border rounded p-3', style={
                    'maxHeight': '300px',
                    'overflowY': 'auto',
                    'fontFamily': 'monospace',
                    'fontSize': '0.875rem',
                    'backgroundColor': '#f8f9fa'
                })
            ])
        ], style={'maxHeight': '70vh', 'overflowY': 'auto'}),
        dbc.ModalFooter([
            dbc.Button(
                [html.I(className='bi bi-dash-lg me-2'), 'Minimize'],
                id='pypsa-minimize-modal-btn',
                color='secondary',
                outline=True,
                size='sm'
            ),
            dbc.Button(
                [html.I(className='bi bi-stop-fill me-2'), 'Stop Model'],
                id='pypsa-stop-model-btn',
                color='danger',
                size='sm',
                disabled=not is_running
            ),
            dbc.Button(
                'Close',
                id='pypsa-close-modal-btn',
                color='primary',
                size='sm',
                disabled=is_running
            )
        ])
    ], is_open=True, size='lg', backdrop='static')


@callback(
    Output('pypsa-process-state', 'data', allow_duplicate=True),
    Input('pypsa-minimize-modal-btn', 'n_clicks'),
    State('pypsa-process-state', 'data'),
    prevent_initial_call=True
)
def minimize_modal(n_clicks, process_state):
    """Minimize process modal."""
    if not n_clicks:
        raise PreventUpdate

    process_state['modalMinimized'] = True
    return process_state


@callback(
    Output('pypsa-process-state', 'data', allow_duplicate=True),
    Input('pypsa-close-modal-btn', 'n_clicks'),
    State('pypsa-process-state', 'data'),
    prevent_initial_call=True
)
def close_modal(n_clicks, process_state):
    """Close process modal."""
    if not n_clicks:
        raise PreventUpdate

    process_state['modalVisible'] = False
    process_state['modalMinimized'] = False

    # Reset if completed
    if process_state.get('status') in ['completed', 'failed']:
        process_state['isRunning'] = False
        process_state['status'] = 'idle'
        process_state['percentage'] = 0
        process_state['message'] = ''
        process_state['logs'] = []

    return process_state


@callback(
    [
        Output('pypsa-process-state', 'data', allow_duplicate=True),
        Output('pypsa-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('pypsa-stop-model-btn', 'n_clicks'),
    State('pypsa-process-state', 'data'),
    prevent_initial_call=True
)
def stop_model(n_clicks, process_state):
    """Stop PyPSA model execution."""
    print("\n" + "="*80)
    print("[DEBUG] stop_model callback triggered")
    print(f"[DEBUG] n_clicks: {n_clicks}")
    print(f"[DEBUG] process_state: {process_state}")
    print("="*80 + "\n")

    if not n_clicks:
        print("[DEBUG] Preventing update: n_clicks is None or 0")
        raise PreventUpdate

    # Get process ID and call cancellation method
    process_id = process_state.get('process_id')
    print(f"[DEBUG] Extracted process_id: {process_id}")

    if not process_id:
        print("[DEBUG] No process_id found in state")
        process_state['logs'].append({
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'error',
            'text': '❌ No process ID found for cancellation'
        })
        return process_state, dash.no_update

    try:
        # Call cancellation method from local_service
        from services.local_service import service as api
        print(f"[DEBUG] Calling api.cancel_pypsa_model with process_id: {process_id}")
        result = api.cancel_pypsa_model(process_id)
        print(f"[DEBUG] Cancel PyPSA model result: {result}")

        if result.get('success'):
            print(f"[DEBUG] Cancellation successful")
            process_state['isRunning'] = False
            process_state['status'] = 'cancelled'
            process_state['logs'].append({
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'info',
                'text': f'✅ {result.get("message", "Model cancelled successfully")}'
            })
        else:
            print(f"[DEBUG] Cancellation failed: {result.get('error')}")
            process_state['logs'].append({
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'error',
                'text': f'❌ {result.get("error", "Failed to cancel model")}'
            })

        print(f"[DEBUG] Returning updated process_state and disabling interval")
        return process_state, True  # Disable polling

    except Exception as e:
        print(f"[ERROR] Exception in stop_model callback: {e}")
        import traceback
        traceback.print_exc()
        process_state['logs'].append({
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'error',
            'text': f'❌ Error stopping model: {str(e)}'
        })
        return process_state, dash.no_update


# =====================================================================
# CALLBACKS - FLOATING INDICATOR
# =====================================================================

@callback(
    Output('pypsa-floating-indicator', 'children'),
    Input('pypsa-process-state', 'data')
)
def render_floating_indicator(process_state):
    """Render floating indicator when modal is minimized."""
    is_minimized = process_state.get('modalMinimized', False)
    is_running = process_state.get('isRunning', False)

    if not is_minimized or not is_running:
        return html.Div()

    percentage = process_state.get('percentage', 0)
    message = process_state.get('message', '')

    return html.Div([
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='bi bi-arrow-repeat me-2',
                          style={'fontSize': '1rem', 'animation': 'spin 1s linear infinite'}),
                    html.Span('PyPSA Model Execution', className='font-bold')
                ], className='d-flex align-items-center mb-2'),
                dbc.Progress(value=percentage, style={'height': '8px'}, className='mb-2'),
                html.Div(f'{percentage}% complete', className='text-xs text-muted mb-2'),
                html.Div([
                    dbc.Button(
                        'Show',
                        id='pypsa-show-modal-btn',
                        size='sm',
                        color='primary',
                        outline=True,
                        className='me-2'
                    ),
                    dbc.Button(
                        [html.I(className='bi bi-stop-fill')],
                        id='pypsa-stop-from-indicator-btn',
                        size='sm',
                        color='danger',
                        outline=True
                    )
                ], className='d-flex gap-2')
            ], className='p-3')
        ], className='shadow-lg')
    ], style={
        'position': 'fixed',
        'bottom': '20px',
        'right': '20px',
        'width': '300px',
        'zIndex': 9999
    })


@callback(
    Output('pypsa-process-state', 'data', allow_duplicate=True),
    Input('pypsa-show-modal-btn', 'n_clicks'),
    State('pypsa-process-state', 'data'),
    prevent_initial_call=True
)
def show_modal_from_indicator(n_clicks, process_state):
    """Show modal from floating indicator."""
    if not n_clicks:
        raise PreventUpdate

    process_state['modalMinimized'] = False
    return process_state


@callback(
    [
        Output('pypsa-process-state', 'data', allow_duplicate=True),
        Output('pypsa-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('pypsa-stop-from-indicator-btn', 'n_clicks'),
    State('pypsa-process-state', 'data'),
    prevent_initial_call=True
)
def stop_model_from_indicator(n_clicks, process_state):
    """Stop model from floating indicator."""
    print("\n" + "="*80)
    print("[DEBUG] stop_model_from_indicator callback triggered")
    print(f"[DEBUG] n_clicks: {n_clicks}")
    print(f"[DEBUG] process_state: {process_state}")
    print("="*80 + "\n")

    if not n_clicks:
        print("[DEBUG] Preventing update: n_clicks is None or 0")
        raise PreventUpdate

    # Get process ID and call cancellation method
    process_id = process_state.get('process_id')
    print(f"[DEBUG] Extracted process_id: {process_id}")

    if not process_id:
        print("[DEBUG] No process_id found in state, showing modal with error")
        process_state['logs'].append({
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'error',
            'text': '❌ No process ID found for cancellation'
        })
        process_state['modalMinimized'] = False  # Show modal to display error
        return process_state, dash.no_update

    try:
        # Call cancellation method from local_service
        from services.local_service import service as api
        print(f"[DEBUG] Calling api.cancel_pypsa_model with process_id: {process_id}")
        result = api.cancel_pypsa_model(process_id)
        print(f"[DEBUG] Cancel PyPSA model result: {result}")

        if result.get('success'):
            print(f"[DEBUG] Cancellation successful, showing modal with success message")
            process_state['isRunning'] = False
            process_state['status'] = 'cancelled'
            process_state['modalMinimized'] = False  # Show modal to display cancellation
            process_state['logs'].append({
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'info',
                'text': f'✅ {result.get("message", "Model cancelled successfully")}'
            })
        else:
            print(f"[DEBUG] Cancellation failed: {result.get('error')}, showing modal with error")
            process_state['modalMinimized'] = False  # Show modal to display error
            process_state['logs'].append({
                'timestamp': time.strftime('%H:%M:%S'),
                'level': 'error',
                'text': f'❌ {result.get("error", "Failed to cancel model")}'
            })

        print(f"[DEBUG] Returning updated process_state and disabling interval")
        return process_state, True  # Disable polling

    except Exception as e:
        print(f"[ERROR] Exception in stop_model_from_indicator callback: {e}")
        import traceback
        traceback.print_exc()
        process_state['modalMinimized'] = False  # Show modal to display error
        process_state['logs'].append({
            'timestamp': time.strftime('%H:%M:%S'),
            'level': 'error',
            'text': f'❌ Error stopping model: {str(e)}'
        })
        return process_state, dash.no_update


# =====================================================================
# CALLBACKS - BUTTON STATE
# =====================================================================

@callback(
    [
        Output('pypsa-run-model-btn', 'disabled'),
        Output('pypsa-run-model-btn', 'children')
    ],
    Input('pypsa-process-state', 'data')
)
def update_run_button(process_state):
    """Update run button state based on process state."""
    is_running = process_state.get('isRunning', False)

    if is_running:
        return True, [
            html.I(className='bi bi-arrow-repeat me-2',
                  style={'animation': 'spin 1s linear infinite'}),
            'Running Model...'
        ]
    else:
        return False, [
            html.I(className='bi bi-play-fill me-2'),
            'Apply Configuration & Run Model'
        ]
