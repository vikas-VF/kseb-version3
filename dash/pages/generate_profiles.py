"""
Load Profile Generation - Clean Dash Implementation
Based on comprehensive analysis of React+FastAPI implementation
Using Dash best practices: all components in layout, conditional visibility
"""

from dash import html, dcc, callback, Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from services.local_service import LocalService
import time

# Import application config
import sys
import os
config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
if config_path not in sys.path:
    sys.path.insert(0, config_path)
from app_config import TemplateFiles, DirectoryStructure, InputDemandSheets, LoadCurveSheets



api = LocalService()

def layout(active_project):
    """
    4-Step Wizard Layout
    ALL components exist from start, visibility controlled by CSS display property
    """

    return dbc.Container([
        # Header with gradient
        html.Div([
            html.H2([
                html.I(className='bi bi-graph-up-arrow me-3'),
                'Load Profile Generation'
            ], className='mb-2 text-white'),
            html.P(
                'Create hourly electricity demand profiles for future years',
                className='mb-0 text-white-50'
            )
        ], className='p-4 rounded-3 mb-4', style={
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }),

        # Progress Stepper
        html.Div(id='profile-stepper', className='mb-4'),

        # Step 1: Method & Timeframe
        html.Div([
            html.H3('Method & Timeframe', className='mb-3'),

            # Profile Name
            dbc.Row([
                dbc.Col([
                    dbc.Label('Profile Name', html_for='prof-name'),
                    dbc.Input(id='prof-name', placeholder='e.g., Project_Profile_V1'),
                    html.Div(id='prof-name-feedback', className='small mt-1')
                ], md=12)
            ], className='mb-3'),

            # Years
            dbc.Row([
                dbc.Col([
                    dbc.Label('Start Year', html_for='prof-start-year'),
                    dbc.Input(id='prof-start-year', type='number', placeholder='2024', min=2000, max=2100)
                ], md=6),
                dbc.Col([
                    dbc.Label('End Year', html_for='prof-end-year'),
                    dbc.Input(id='prof-end-year', type='number', placeholder='2035', min=2000, max=2100)
                ], md=6),
            ], className='mb-4'),

            # Method Selection
            html.H5('Select Method', className='mb-3'),
            dbc.RadioItems(
                id='prof-method',
                options=[
                    {'label': html.Div([
                        html.Strong('Base Profile Method'),
                        html.Br(),
                        html.Small('Extrapolates from a single historical reference year', className='text-muted')
                    ]), 'value': 'base'},
                    {'label': html.Div([
                        html.Strong('STL Decomposition'),
                        html.Br(),
                        html.Small('Advanced seasonal-trend analysis for better accuracy', className='text-muted')
                    ]), 'value': 'stl'},
                ],
                inline=False,
                className='mb-3'
            ),

            # Base Year Dropdown (conditional)
            html.Div([
                dbc.Label('Base Year', html_for='prof-base-year'),
                dbc.Select(id='prof-base-year', placeholder='Select base year')
            ], id='base-year-container', style={'display': 'none'}, className='mb-3'),

        ], id='step-1-container'),

        # Step 2: Data Source
        html.Div([
            html.H3('Total Demand Source', className='mb-3'),
            dbc.RadioItems(
                id='prof-demand-source',
                options=[
                    {'label': html.Div([
                        html.Strong("Use 'Total Demand' Sheet"),
                        html.Br(),
                        html.Small("Reads from 'Total_Demand' sheet in input Excel file", className='text-muted')
                    ]), 'value': 'template'},
                    {'label': html.Div([
                        html.Strong('Use Demand Projection Scenario'),
                        html.Br(),
                        html.Small('Uses consolidated results from a forecast scenario', className='text-muted')
                    ]), 'value': 'projection'},
                ],
                inline=False,
                className='mb-3'
            ),

            # Scenario Dropdown (conditional)
            html.Div([
                dbc.Label('Projection Scenario', html_for='prof-scenario'),
                dbc.Select(id='prof-scenario', placeholder='Select scenario')
            ], id='scenario-container', style={'display': 'none'}),

        ], id='step-2-container', style={'display': 'none'}),

        # Step 3: Constraints
        html.Div([
            html.H3('Monthly Constraints', className='mb-3'),
            html.P('Choose how to apply monthly peak/min constraints', className='text-muted'),
            dbc.RadioItems(
                id='prof-constraints',
                options=[
                    {'label': html.Div([
                        html.Strong('Auto-calculate from base year'),
                        html.Br(),
                        html.Small('Derive constraints from historical data', className='text-muted')
                    ]), 'value': 'auto'},
                    {'label': html.Div([
                        html.Strong('Use constraints from Excel'),
                        html.Br(),
                        html.Small('Read pre-defined constraints from template', className='text-muted')
                    ]), 'value': 'excel'},
                    {'label': html.Div([
                        html.Strong('No constraints'),
                        html.Br(),
                        html.Small('Generate without peak/min limits', className='text-muted')
                    ]), 'value': 'none'},
                ],
                value='none',
                inline=False
            ),
        ], id='step-3-container', style={'display': 'none'}),

        # Step 4: Review
        html.Div([
            html.H3('Review Configuration', className='mb-3'),
            dbc.Card([
                dbc.CardBody(id='prof-review-summary')
            ], className='mb-3'),
        ], id='step-4-container', style={'display': 'none'}),

        # Navigation Buttons
        html.Div([
            dbc.Button('Back', id='prof-back-btn', color='light', size='lg', className='me-2'),
            dbc.Button('Next', id='prof-next-btn', color='primary', size='lg', className='me-2'),
            dbc.Button([
                html.I(className='bi bi-rocket-takeoff me-2'),
                'Generate Profile'
            ], id='prof-generate-btn', color='success', size='lg', style={'display': 'none'}),
        ], className='d-flex justify-content-end mt-4'),

        # State Storage
        dcc.Store(id='prof-wizard-state', storage_type='session', data={
            'currentStep': 1,
            'profileName': '',
            'startYear': None,
            'endYear': None,
            'method': None,
            'baseYear': None,
            'demandSource': None,
            'scenario': None,
            'constraints': 'none',
            'profileNameValid': False
        }),

        # Base Years Data
        dcc.Store(id='prof-base-years-store', data=[]),

        # Scenarios Data
        dcc.Store(id='prof-scenarios-store', data=[]),

        # Validation Interval (debounce)
        dcc.Interval(id='prof-validation-interval', interval=500, max_intervals=0),

        # Process State (for generation progress)
        dcc.Store(id='prof-process-state', storage_type='memory', data={
            'isRunning': False,
            'status': 'idle',
            'percentage': 0,
            'message': '',
            'error': None
        }),

        # Progress Polling Interval
        dcc.Interval(id='prof-progress-interval', interval=1000, disabled=True),

        # Generation result alert (will be shown after generation completes)
        html.Div(id='prof-generation-alert', className='mt-3'),

        # Logs Store (accumulates logs from SSE)
        dcc.Store(id='prof-logs-store', storage_type='memory', data=[]),

        # Copy logs notification
        html.Div(id='prof-copy-notification'),

        # Progress Modal (hidden initially)
        dbc.Modal([
            dbc.ModalHeader([
                html.Div([
                    html.I(id='prof-modal-icon', className='bi bi-hourglass-split me-2'),
                    html.Span(id='prof-modal-title', children='Load Profile Generation')
                ], className='d-flex align-items-center')
            ]),
            dbc.ModalBody([
                # Progress Bar Section
                html.Div([
                    html.Div([
                        html.Span(id='prof-progress-message', children='Starting...', className='small fw-semibold'),
                        html.Span(id='prof-progress-percentage', children='0%', className='small fw-bold text-primary')
                    ], className='d-flex justify-content-between mb-2'),
                    dbc.Progress(id='prof-progress-bar', value=0, className='mb-3', style={'height': '8px'})
                ]),

                # Logs Display Section
                html.Div([
                    html.Div([
                        html.H6('Process Logs', className='mb-2'),
                        dbc.Button([
                            html.I(id='prof-copy-icon', className='bi bi-clipboard me-1'),
                            'Copy Logs'
                        ], id='prof-copy-logs-btn', size='sm', color='secondary', outline=True, className='mb-2')
                    ], className='d-flex justify-content-between align-items-center'),

                    # Log container with auto-scroll
                    html.Div(
                        id='prof-logs-container',
                        style={
                            'backgroundColor': '#1e293b',  # slate-900
                            'color': '#e2e8f0',  # slate-200
                            'fontFamily': 'monospace',
                            'fontSize': '13px',
                            'padding': '1rem',
                            'borderRadius': '8px',
                            'maxHeight': '400px',
                            'overflowY': 'auto',
                            'whiteSpace': 'pre-wrap',
                            'wordBreak': 'break-word'
                        },
                        children=[
                            html.Div('Initializing process...', className='text-muted small')
                        ]
                    )
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Close', id='prof-modal-close-btn', color='secondary', className='me-2', disabled=True),
                dbc.Button('Stop Process', id='prof-modal-stop-btn', color='danger', outline=True)
            ])
        ], id='prof-progress-modal', is_open=False, size='xl', backdrop='static'),

        # Clipboard component for copying logs
        dcc.Clipboard(id='prof-clipboard', style={'display': 'none'}),

    ], fluid=True, className='py-4', style={'maxWidth': '900px'})


# ============================================================================
# CALLBACKS
# ============================================================================

# 1. Update stepper visualization
@callback(
    Output('profile-stepper', 'children'),
    Input('prof-wizard-state', 'data')
)
def update_stepper(state):
    """Render progress stepper based on current step"""
    current = state.get('currentStep', 1)

    steps = [
        {'num': 1, 'title': 'Method & Timeframe'},
        {'num': 2, 'title': 'Data Source'},
        {'num': 3, 'title': 'Constraints'},
        {'num': 4, 'title': 'Review & Generate'},
    ]

    items = []
    for i, step in enumerate(steps):
        is_active = step['num'] == current
        is_complete = step['num'] < current

        # Circle
        if is_complete:
            circle_style = {'backgroundColor': '#10b981', 'color': 'white'}
            circle_content = html.I(className='bi bi-check')
        elif is_active:
            circle_style = {'backgroundColor': '#667eea', 'color': 'white'}
            circle_content = str(step['num'])
        else:
            circle_style = {'backgroundColor': '#e5e7eb', 'color': '#9ca3af'}
            circle_content = str(step['num'])

        circle = html.Div(
            circle_content,
            style={
                **circle_style,
                'width': '40px',
                'height': '40px',
                'borderRadius': '50%',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'fontWeight': 'bold'
            }
        )

        items.append(html.Div([
            circle,
            html.Div(step['title'], className='small mt-2', style={
                'color': '#667eea' if is_active else '#6b7280'
            })
        ], style={'textAlign': 'center'}))

        # Add connector
        if i < len(steps) - 1:
            items.append(html.Div(style={
                'flex': '1',
                'height': '2px',
                'backgroundColor': '#10b981' if is_complete else '#e5e7eb',
                'margin': '20px 10px 0 10px'
            }))

    return html.Div(items, className='d-flex align-items-start justify-content-center')


# 2. Show/hide step containers
@callback(
    Output('step-1-container', 'style'),
    Output('step-2-container', 'style'),
    Output('step-3-container', 'style'),
    Output('step-4-container', 'style'),
    Output('prof-back-btn', 'style'),
    Output('prof-next-btn', 'style'),
    Output('prof-generate-btn', 'style'),
    Input('prof-wizard-state', 'data')
)
def show_hide_steps(state):
    """Control visibility of step containers and buttons"""
    current = state.get('currentStep', 1)

    step1_style = {} if current == 1 else {'display': 'none'}
    step2_style = {} if current == 2 else {'display': 'none'}
    step3_style = {} if current == 3 else {'display': 'none'}
    step4_style = {} if current == 4 else {'display': 'none'}

    back_style = {'display': 'none'} if current == 1 else {}
    next_style = {} if current < 4 else {'display': 'none'}
    generate_style = {} if current == 4 else {'display': 'none'}

    return step1_style, step2_style, step3_style, step4_style, back_style, next_style, generate_style


# 3. Show/hide conditional fields
@callback(
    Output('base-year-container', 'style'),
    Output('scenario-container', 'style'),
    Input('prof-wizard-state', 'data')
)
def show_hide_conditional_fields(state):
    """Show base year dropdown when method=base, scenario dropdown when source=projection"""
    base_year_style = {} if state.get('method') == 'base' else {'display': 'none'}
    scenario_style = {} if state.get('demandSource') == 'projection' else {'display': 'none'}
    return base_year_style, scenario_style


# 4. Update wizard state from all inputs (SINGLE callback for all fields)
@callback(
    Output('prof-wizard-state', 'data'),
    Output('prof-validation-interval', 'max_intervals'),
    Input('prof-name', 'value'),
    Input('prof-start-year', 'value'),
    Input('prof-end-year', 'value'),
    Input('prof-method', 'value'),
    Input('prof-base-year', 'value'),
    Input('prof-demand-source', 'value'),
    Input('prof-scenario', 'value'),
    Input('prof-constraints', 'value'),
    State('prof-wizard-state', 'data'),
    prevent_initial_call=True
)
def update_state(name, start, end, method, base_year, source, scenario, constraints, state):
    """Update wizard state when any input changes"""
    triggered = ctx.triggered_id

    print(f"[UPDATE_STATE] Triggered by: {triggered}, value: {ctx.triggered[0]['value']}")

    state = state.copy()
    trigger_validation = 0

    if triggered == 'prof-name':
        state['profileName'] = name or ''
        trigger_validation = 1  # Trigger debounced validation
    elif triggered == 'prof-start-year':
        state['startYear'] = int(start) if start else None
    elif triggered == 'prof-end-year':
        state['endYear'] = int(end) if end else None
    elif triggered == 'prof-method':
        state['method'] = method
        if method != 'base':
            state['baseYear'] = None
    elif triggered == 'prof-base-year':
        state['baseYear'] = base_year
    elif triggered == 'prof-demand-source':
        state['demandSource'] = source
        if source != 'projection':
            state['scenario'] = None
    elif triggered == 'prof-scenario':
        state['scenario'] = scenario
    elif triggered == 'prof-constraints':
        state['constraints'] = constraints

    print(f"[UPDATE_STATE] New state: {state}")
    return state, trigger_validation


# 5. Validate profile name (debounced)
@callback(
    Output('prof-name-feedback', 'children'),
    Output('prof-wizard-state', 'data', allow_duplicate=True),
    Input('prof-validation-interval', 'n_intervals'),
    State('prof-wizard-state', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def validate_profile_name(n, state, project):
    """Check if profile name exists"""
    name = state.get('profileName', '')

    if not name or not project:
        state['profileNameValid'] = False
        return '', state

    try:
        result = api.check_profile_exists(project['path'], name)
        exists = result.get('exists', False)

        if exists:
            state['profileNameValid'] = False
            return html.Div([
                html.I(className='bi bi-x-circle text-danger me-2'),
                'This profile name already exists'
            ], className='text-danger'), state
        else:
            state['profileNameValid'] = True
            return html.Div([
                html.I(className='bi bi-check-circle text-success me-2'),
                'Profile name is available'
            ], className='text-success'), state
    except Exception as e:
        print(f"[VALIDATE] Error: {e}")
        state['profileNameValid'] = False
        return '', state


# 6. Fetch base years when method selected
@callback(
    Output('prof-base-years-store', 'data'),
    Output('prof-base-year', 'options'),
    Input('prof-wizard-state', 'data'),
    State('active-project-store', 'data'),
    State('prof-base-years-store', 'data'),
)
def fetch_base_years(state, project, current_years):
    """Load base years from API when method=base"""
    if state.get('method') != 'base' or not project:
        return no_update, no_update

    if current_years:  # Already loaded
        options = [{'label': y, 'value': y} for y in current_years]
        return no_update, options

    try:
        result = api.get_available_base_years(project['path'])
        years = result.get('years', [])
        options = [{'label': y, 'value': y} for y in years]
        return years, options
    except Exception as e:
        print(f"[FETCH_BASE_YEARS] Error: {e}")
        return [], []


# 7. Fetch scenarios when source selected
@callback(
    Output('prof-scenarios-store', 'data'),
    Output('prof-scenario', 'options'),
    Input('prof-wizard-state', 'data'),
    State('active-project-store', 'data'),
    State('prof-scenarios-store', 'data'),
)
def fetch_scenarios(state, project, current_scenarios):
    """Load scenarios from API when source=projection"""
    if state.get('demandSource') != 'projection' or not project:
        return no_update, no_update

    if current_scenarios:  # Already loaded
        options = [{'label': s, 'value': s} for s in current_scenarios]
        return no_update, options

    try:
        result = api.get_available_scenarios_for_profiles(project['path'])
        scenarios = result.get('scenarios', [])
        options = [{'label': s, 'value': s} for s in scenarios]
        return scenarios, options
    except Exception as e:
        print(f"[FETCH_SCENARIOS] Error: {e}")
        return [], []


# 8. Navigate back
@callback(
    Output('prof-wizard-state', 'data', allow_duplicate=True),
    Input('prof-back-btn', 'n_clicks'),
    State('prof-wizard-state', 'data'),
    prevent_initial_call=True
)
def go_back(n, state):
    """Go to previous step"""
    state = state.copy()
    if state['currentStep'] > 1:
        state['currentStep'] -= 1
    return state


# 9. Navigate next with validation
@callback(
    Output('prof-wizard-state', 'data', allow_duplicate=True),
    Input('prof-next-btn', 'n_clicks'),
    State('prof-wizard-state', 'data'),
    prevent_initial_call=True
)
def go_next(n, state):
    """Go to next step if current step is valid"""
    current = state.get('currentStep', 1)

    # Validation logic
    valid = False
    if current == 1:
        valid = (
            state.get('profileName') and
            state.get('profileNameValid') and
            state.get('startYear') and
            state.get('endYear') and
            state.get('method') and
            (state.get('method') != 'base' or state.get('baseYear'))
        )
        print(f"[GO_NEXT] Step 1 valid: {valid}, data: {state}")
    elif current == 2:
        valid = (
            state.get('demandSource') and
            (state.get('demandSource') != 'projection' or state.get('scenario'))
        )
        print(f"[GO_NEXT] Step 2 valid: {valid}, data: {state}")
    elif current == 3:
        valid = state.get('constraints') is not None
        print(f"[GO_NEXT] Step 3 valid: {valid}, data: {state}")

    if valid and current < 4:
        state = state.copy()
        state['currentStep'] = current + 1
        return state

    return no_update


# 10. Update review summary
@callback(
    Output('prof-review-summary', 'children'),
    Input('prof-wizard-state', 'data')
)
def update_review(state):
    """Display configuration summary in step 4"""
    return html.Div([
        html.Div([html.Strong('Profile Name: '), state.get('profileName', 'N/A')], className='mb-2'),
        html.Div([html.Strong('Timeframe: '), f"{state.get('startYear', '?')} to {state.get('endYear', '?')}"], className='mb-2'),
        html.Div([html.Strong('Method: '), 'Base Profile' if state.get('method') == 'base' else 'STL Decomposition'], className='mb-2'),
        html.Div([html.Strong('Base Year: '), state.get('baseYear', 'N/A')], className='mb-2') if state.get('method') == 'base' else None,
        html.Div([html.Strong('Data Source: '), 'Template' if state.get('demandSource') == 'template' else 'Projection'], className='mb-2'),
        html.Div([html.Strong('Scenario: '), state.get('scenario', 'N/A')], className='mb-2') if state.get('demandSource') == 'projection' else None,
        html.Div([html.Strong('Constraints: '), (state.get('constraints') or 'none').capitalize()], className='mb-2'),
    ])


# 11. Generate profile
@callback(
    [
        Output('prof-process-state', 'data'),
        Output('prof-progress-interval', 'disabled'),
        Output('prof-progress-modal', 'is_open'),
        Output('prof-logs-store', 'data'),
    ],
    Input('prof-generate-btn', 'n_clicks'),
    [
        State('prof-wizard-state', 'data'),
        State('active-project-store', 'data'),
        State('prof-process-state', 'data')
    ],
    prevent_initial_call=True
)
def generate_profile(n_clicks, state, project, process_state):
    """Start load profile generation process and open progress modal"""
    if not n_clicks:
        raise PreventUpdate

    if not project or not project.get('path'):
        # Show error in alert instead
        return no_update, no_update, False, no_update

    if process_state.get('isRunning'):
        # Already running
        return no_update, no_update, False, no_update

    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.local_service import service as api
    import threading

    # Build configuration payload matching FastAPI structure
    config = {
        'project_path': project['path'],
        'profile_configuration': {
            'general': {
                'profile_name': state['profileName'],
                'start_year': str(state['startYear']),
                'end_year': str(state['endYear'])
            },
            'generation_method': {
                'type': state['method'],
                'base_year': state.get('baseYear') if state['method'] == 'base' else None
            },
            'data_source': {
                'type': state['demandSource'],
                'scenario_name': state.get('scenario') if state['demandSource'] == 'projection' else None
            },
            'constraints': {
                'monthly_method': state.get('constraints', 'none')
            }
        }
    }

    print(f"[GENERATE_PROFILE] Starting with config: {config}")

    try:
        # Call API to start subprocess (which will stream to SSE)
        result = api.generate_profile(config)

        if not result.get('success'):
            print(f"[GENERATE_PROFILE] Failed to start: {result.get('error')}")
            return no_update, no_update, False, no_update

        print(f"[GENERATE_PROFILE] Started successfully, process_id: {result.get('process_id')}")

        # Update process state to running
        process_state_updated = {
            'isRunning': True,
            'status': 'running',
            'percentage': 0,
            'message': 'Starting...',
            'error': None,
            'process_id': result.get('process_id')
        }

        # Initialize logs with starting message
        initial_logs = [{
            'type': 'info',
            'text': f'Starting profile generation for {state["profileName"]}...',
            'timestamp': time.strftime('%H:%M:%S')
        }]

        # Open modal, enable polling, clear logs
        return process_state_updated, False, True, initial_logs

    except Exception as e:
        print(f"[GENERATE_PROFILE] Error: {e}")
        import traceback
        traceback.print_exc()
        return no_update, no_update, False, no_update


# 12. Poll SSE queue for progress updates
@callback(
    [
        Output('prof-process-state', 'data', allow_duplicate=True),
        Output('prof-logs-store', 'data', allow_duplicate=True),
        Output('prof-progress-interval', 'disabled', allow_duplicate=True)
    ],
    Input('prof-progress-interval', 'n_intervals'),
    [
        State('prof-process-state', 'data'),
        State('prof-logs-store', 'data')
    ],
    prevent_initial_call=True
)
def poll_sse_progress(n_intervals, process_state, current_logs):
    """Poll SSE queue for new progress events"""
    if not process_state or not process_state.get('isRunning'):
        return no_update, no_update, True  # Disable polling

    try:
        # Import SSE queue
        from services.local_service import profile_sse_queue

        # Read all available events from queue (non-blocking)
        events = []
        while not profile_sse_queue.empty():
            try:
                event = profile_sse_queue.get_nowait()
                events.append(event)
                print(f"[PROF_PROGRESS] Got SSE event: {event}")
            except:
                break

        if not events:
            return no_update, no_update, False  # Keep polling

        # Process events and update state
        new_state = dict(process_state)
        new_logs = list(current_logs) if current_logs else []

        for event in events:
            event_type = event.get('type')
            timestamp = event.get('timestamp', time.strftime('%H:%M:%S'))

            if event_type == 'progress':
                # Update progress bar
                new_state['percentage'] = event.get('percentage', 0)
                new_state['message'] = event.get('message', 'Processing...')

                # Add to logs
                new_logs.append({
                    'type': 'progress',
                    'text': event.get('message', ''),
                    'timestamp': timestamp
                })

            elif event_type == 'log':
                # Regular log entry
                new_logs.append({
                    'type': 'info',
                    'text': event.get('text', ''),
                    'timestamp': timestamp
                })

            elif event_type == 'error':
                # Error log entry
                new_logs.append({
                    'type': 'error',
                    'text': event.get('text', ''),
                    'timestamp': timestamp
                })

            elif event_type == 'end':
                # Process completed or failed
                status = event.get('status', 'completed')
                new_state['status'] = status
                new_state['isRunning'] = False

                if status == 'completed':
                    new_state['percentage'] = 100
                    new_state['message'] = event.get('message', 'Completed successfully!')
                    new_logs.append({
                        'type': 'success',
                        'text': event.get('message', 'Profile generated successfully!'),
                        'timestamp': timestamp
                    })
                else:
                    new_state['error'] = event.get('error', 'Unknown error')
                    new_logs.append({
                        'type': 'error',
                        'text': f"Failed: {event.get('error', 'Unknown error')}",
                        'timestamp': timestamp
                    })

                return new_state, new_logs, True  # Disable polling

        return new_state, new_logs, False  # Keep polling

    except Exception as e:
        print(f"[PROF_PROGRESS] Error: {e}")
        import traceback
        traceback.print_exc()
        return no_update, no_update, False


# 13. Update modal UI (progress bar, logs, icon, buttons)
@callback(
    [
        Output('prof-progress-bar', 'value'),
        Output('prof-progress-percentage', 'children'),
        Output('prof-progress-message', 'children'),
        Output('prof-logs-container', 'children'),
        Output('prof-modal-icon', 'className'),
        Output('prof-modal-title', 'children'),
        Output('prof-modal-close-btn', 'disabled'),
        Output('prof-modal-stop-btn', 'style')
    ],
    [
        Input('prof-process-state', 'data'),
        Input('prof-logs-store', 'data')
    ]
)
def update_modal_ui(process_state, logs):
    """Update all modal UI elements based on process state and logs"""
    if not process_state:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    # Progress bar
    percentage = min(100, max(0, process_state.get('percentage', 0)))
    percentage_text = f"{percentage}%"
    message = process_state.get('message', 'Processing...')

    # Status icon and title
    status = process_state.get('status', 'running')
    if status == 'running':
        icon_class = 'bi bi-hourglass-split me-2 text-primary'
        title = 'Load Profile Generation - In Progress'
        close_disabled = True
        stop_visible = {'display': 'inline-block'}
    elif status == 'completed':
        icon_class = 'bi bi-check-circle-fill me-2 text-success'
        title = 'Load Profile Generation - Completed'
        close_disabled = False
        stop_visible = {'display': 'none'}
    elif status == 'failed':
        icon_class = 'bi bi-exclamation-triangle-fill me-2 text-danger'
        title = 'Load Profile Generation - Failed'
        close_disabled = False
        stop_visible = {'display': 'none'}
    else:
        icon_class = 'bi bi-hourglass-split me-2'
        title = 'Load Profile Generation'
        close_disabled = True
        stop_visible = {'display': 'inline-block'}

    # Logs display with color coding
    log_elements = []
    if logs:
        for i, log in enumerate(logs):
            log_type = log.get('type', 'info')
            text = log.get('text', '')
            timestamp = log.get('timestamp', '')

            # Color coding based on type
            if log_type == 'error':
                color = '#fca5a5'  # red-300
                type_label = 'ERROR'
                type_color = '#f87171'  # red-400
            elif log_type == 'success':
                color = '#86efac'  # green-300
                type_label = 'SUCCESS'
                type_color = '#4ade80'  # green-400
            elif log_type == 'progress':
                color = '#67e8f9'  # cyan-300
                type_label = 'PROGRESS'
                type_color = '#22d3ee'  # cyan-400
            elif log_type == 'warning':
                color = '#fde047'  # yellow-300
                type_label = 'WARNING'
                type_color = '#facc15'  # yellow-400
            else:
                color = '#e2e8f0'  # slate-200
                type_label = 'INFO'
                type_color = '#cbd5e1'  # slate-300

            log_elements.append(html.Div([
                html.Span(timestamp, style={'color': '#94a3b8', 'fontSize': '11px', 'marginRight': '8px'}),
                html.Span(f'[{type_label}]', style={'color': type_color, 'fontSize': '11px', 'fontWeight': 'bold', 'marginRight': '8px'}),
                html.Span(text, style={'color': color})
            ], style={'marginBottom': '4px'}, key=f'log-{i}'))
    else:
        log_elements = [html.Div('Initializing...', className='text-muted small')]

    return percentage, percentage_text, message, log_elements, icon_class, title, close_disabled, stop_visible


# 14. Copy logs to clipboard
@callback(
    [
        Output('prof-clipboard', 'content'),
        Output('prof-copy-icon', 'className'),
        Output('prof-copy-notification', 'children')
    ],
    Input('prof-copy-logs-btn', 'n_clicks'),
    State('prof-logs-store', 'data'),
    prevent_initial_call=True
)
def copy_logs(n_clicks, logs):
    """Copy logs to clipboard"""
    if not n_clicks or not logs:
        raise PreventUpdate

    # Format logs as text
    logs_text = '\n'.join([
        f"[{log.get('timestamp', '')}] [{log.get('type', 'INFO').upper()}] {log.get('text', '')}"
        for log in logs
    ])

    # Show success notification
    notification = dbc.Toast(
        'Logs copied to clipboard!',
        icon='success',
        duration=2000,
        is_open=True,
        style={'position': 'fixed', 'top': 66, 'right': 10, 'width': 350}
    )

    # Change icon to checkmark briefly
    return logs_text, 'bi bi-check me-1', notification


# 15. Reset copy icon after 2 seconds
@callback(
    Output('prof-copy-icon', 'className', allow_duplicate=True),
    Input('prof-copy-icon', 'className'),
    prevent_initial_call=True
)
def reset_copy_icon(current_class):
    """Reset copy icon back to clipboard after showing checkmark"""
    if 'check' in current_class:
        import dash
        import time
        time.sleep(2)
        return 'bi bi-clipboard me-1'
    raise PreventUpdate


# 16. Close modal
@callback(
    Output('prof-progress-modal', 'is_open', allow_duplicate=True),
    Input('prof-modal-close-btn', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(n_clicks):
    """Close the progress modal"""
    if n_clicks:
        return False
    raise PreventUpdate
