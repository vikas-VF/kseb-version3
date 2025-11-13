"""
Load Profiles - Generate Profiles Page
Complete 4-step wizard for load profile generation with real-time progress tracking

Features:
- 4-step wizard (Method & Timeframe → Data Source → Constraints → Review & Generate)
- Real-time profile name validation
- Dynamic base year and scenario loading
- Progress tracking with SSE-style polling
- Process modal with logs and progress
- Auto-navigation to Analyze page on completion
"""

from dash import html, dcc, callback, Input, Output, State, callback_context, no_update, ALL
import dash_bootstrap_components as dbc
import sys
import os
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.local_service import service as api
from utils.state_manager import StateManager, ProcessState


def layout(active_project=None):
    """Generate Profiles wizard page"""

    if not active_project:
        return dbc.Container([
            dbc.Alert([
                html.H4('⚠️ No Project Loaded', className='alert-heading'),
                html.P('Please load or create a project first to generate load profiles.'),
                dbc.Button('Go to Projects', href='/load-project', color='primary')
            ], color='warning')
        ], className='p-4')

    return dbc.Container([
        # Progress Modal
        dbc.Modal([
            dbc.ModalHeader('🚀 Load Profile Generation'),
            dbc.ModalBody([
                # Progress section
                html.Div([
                    html.Div(id='generate-progress-text', className='mb-2'),
                    dbc.Progress(id='generate-progress-bar', value=0, className='mb-3'),
                    html.Div(id='generate-task-progress', className='text-muted small mb-3')
                ]),
                # Logs section
                html.Div([
                    html.H6('Process Logs:', className='mb-2'),
                    html.Div(
                        id='generate-logs-container',
                        style={
                            'maxHeight': '300px',
                            'overflowY': 'auto',
                            'backgroundColor': '#f8f9fa',
                            'padding': '10px',
                            'borderRadius': '5px',
                            'fontFamily': 'monospace',
                            'fontSize': '0.85rem'
                        }
                    )
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button('Minimize', id='minimize-generate-modal-btn', color='secondary', outline=True),
                dbc.Button('Close', id='close-generate-modal-btn', color='primary')
            ])
        ], id='generate-progress-modal', is_open=False, size='lg', backdrop='static'),

        # Floating Indicator (when minimized)
        html.Div(
            id='generate-floating-indicator',
            style={'display': 'none'}
        ),

        # Main Wizard Card
        dbc.Card([
            dbc.CardHeader([
                html.Div(id='wizard-stepper', className='py-3')
            ]),
            dbc.CardBody([
                html.Div(id='wizard-step-content', className='py-4')
            ]),
            dbc.CardFooter([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className='bi bi-arrow-left me-2'), 'Back'],
                            id='wizard-back-btn',
                            color='secondary',
                            outline=True,
                            className='me-2'
                        )
                    ], width='auto'),
                    dbc.Col([
                        dbc.Button(
                            [html.I(className='bi bi-arrow-right me-2'), 'Next'],
                            id='wizard-next-btn',
                            color='primary',
                            className='me-2'
                        ),
                        dbc.Button(
                            [html.I(className='bi bi-rocket me-2'), 'Generate Profile'],
                            id='wizard-generate-btn',
                            color='success',
                            style={'display': 'none'}
                        )
                    ], width='auto', className='ms-auto')
                ], align='center')
            ], className='bg-light')
        ], className='shadow-sm'),

        # State stores
        dcc.Store(id='wizard-state', storage_type='session', data={
            'currentStep': 1,
            'profileName': '',
            'startYear': '',
            'endYear': '',
            'selectedMethod': None,
            'baseYear': '',
            'demandSource': None,
            'projectionScenario': '',
            'monthlyConstraint': None,
            'profileNameError': ''
        }),
        dcc.Store(id='available-base-years', data=[]),
        dcc.Store(id='available-scenarios', data=[]),
        dcc.Store(id='generation-process-state', data={
            'isRunning': False,
            'percentage': 0,
            'message': '',
            'taskProgress': '',
            'logs': [],
            'status': 'idle',
            'modalVisible': False,
            'modalMinimized': False
        }),

        # SSE control store (triggers SSE connection start/stop)
        dcc.Store(id='sse-control-store', data={'action': 'idle', 'url': ''}),

        # Hidden div for SSE clientside callback output
        html.Div(id='sse-connection-status', style={'display': 'none'}),

        # Hidden source-radio (always present for callbacks, actual selection happens in Step 2)
        dbc.RadioItems(
            id='source-radio',
            options=[
                {'label': 'Template', 'value': 'template'},
                {'label': 'Projection', 'value': 'projection'}
            ],
            value='template',
            style={'display': 'none'}
        ),

        # SSE Handler Script (clientside callback in JavaScript)
        html.Script('''
            // Global EventSource instance
            window.profileGenerationEventSource = null;

            // Clientside callback to handle SSE connection
            if (!window.dash_clientside) { window.dash_clientside = {}; }
            window.dash_clientside.generation_sse = {
                handle_sse: function(sse_control, current_process_state) {
                    if (!sse_control || !current_process_state) {
                        return [window.dash_clientside.no_update, 'idle'];
                    }

                    const action = sse_control.action;
                    const url = sse_control.url;

                    // Close existing connection if any
                    if (action === 'stop' || action === 'start') {
                        if (window.profileGenerationEventSource) {
                            window.profileGenerationEventSource.close();
                            window.profileGenerationEventSource = null;
                        }
                    }

                    // Start new SSE connection
                    if (action === 'start' && url) {
                        const eventSource = new EventSource(url);
                        window.profileGenerationEventSource = eventSource;

                        eventSource.onmessage = function(event) {
                            try {
                                const log = event.data;

                                // Clean up log text
                                let cleanLog = log.replace(/^\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2},\\d{3}\\s+-\\s+\\w+\\s+-\\s+\\[Profile Generation (STDERR|STDOUT)\\]:\\s+/, '');

                                // Skip empty logs
                                if (!cleanLog.trim() || /^=+$/.test(cleanLog.trim())) {
                                    return;
                                }

                                // Get current timestamp
                                const now = new Date();
                                const timeStr = now.toTimeString().split(' ')[0];

                                // Create new process state
                                const newState = {...current_process_state};

                                // Parse different log types
                                if (log.includes('PROGRESS:')) {
                                    const jsonStart = log.indexOf('{');
                                    if (jsonStart !== -1) {
                                        try {
                                            const progressData = JSON.parse(log.substring(jsonStart));
                                            newState.message = progressData.message || 'Processing...';
                                            if (progressData.percentage !== undefined) {
                                                newState.percentage = progressData.percentage;
                                            }
                                            newState.logs = [...(newState.logs || []), {
                                                time: timeStr,
                                                type: 'progress',
                                                text: progressData.message || cleanLog
                                            }];
                                        } catch (e) {
                                            console.error('Error parsing progress JSON:', e);
                                        }
                                    }
                                } else if (log.includes('YEAR_PROGRESS:')) {
                                    const match = log.match(/Processing FY(\\d+) \\((\\d+)\\/(\\d+)\\)/);
                                    if (match) {
                                        const year = match[1];
                                        const current = parseInt(match[2], 10);
                                        const total = parseInt(match[3], 10);

                                        if (total > 0) {
                                            const basePercentage = 5;
                                            const workRange = 94;
                                            const calculatedPercentage = basePercentage + (current / total) * workRange;
                                            newState.percentage = Math.min(99, calculatedPercentage);
                                            newState.message = `Processing FY${year} (${current}/${total})`;
                                            newState.taskProgress = `${current}/${total} years`;
                                        }

                                        newState.logs = [...(newState.logs || []), {
                                            time: timeStr,
                                            type: 'progress',
                                            text: `Processing FY${year} (${current}/${total} years)`
                                        }];
                                    }
                                } else if (log.includes('GENERATION COMPLETE') || log.includes('Generation completed successfully')) {
                                    newState.isRunning = false;
                                    newState.status = 'completed';
                                    newState.percentage = 100;
                                    newState.message = 'Profile generation completed!';
                                    newState.logs = [...(newState.logs || []), {
                                        time: timeStr,
                                        type: 'success',
                                        text: '✅ Load profile generation completed successfully!'
                                    }];
                                    eventSource.close();
                                } else if (log.includes('FAILED') && log.includes('profile generation')) {
                                    newState.isRunning = false;
                                    newState.status = 'failed';
                                    newState.logs = [...(newState.logs || []), {
                                        time: timeStr,
                                        type: 'error',
                                        text: '❌ Profile generation failed'
                                    }];
                                    eventSource.close();
                                } else {
                                    // Determine log type
                                    let logType = 'info';
                                    if (cleanLog.includes('✓') || cleanLog.includes('✅') || cleanLog.includes('successfully') || cleanLog.includes('completed')) {
                                        logType = 'success';
                                    } else if (cleanLog.includes('Processing') || cleanLog.includes('Generating') || cleanLog.includes('Loading') || cleanLog.includes('Extracting')) {
                                        logType = 'progress';
                                    } else if (cleanLog.includes('Warning') || cleanLog.includes('Note:')) {
                                        logType = 'warning';
                                    }

                                    newState.logs = [...(newState.logs || []), {
                                        time: timeStr,
                                        type: logType,
                                        text: cleanLog
                                    }];
                                }

                                // Keep last 50 logs
                                if (newState.logs && newState.logs.length > 50) {
                                    newState.logs = newState.logs.slice(-50);
                                }

                                // Trigger update by setting store data
                                const storeDiv = document.getElementById('generation-process-state');
                                if (storeDiv && storeDiv._dashprivate_layout && storeDiv._dashprivate_layout.props) {
                                    storeDiv._dashprivate_layout.props.data = newState;
                                    // Trigger Dash callback
                                    if (window.dash_clientside && window.dash_clientside.set_props) {
                                        window.dash_clientside.set_props('generation-process-state', {data: newState});
                                    }
                                }
                            } catch (error) {
                                console.error('Error processing SSE message:', error);
                            }
                        };

                        eventSource.onerror = function() {
                            console.error('SSE connection error');
                            eventSource.close();
                            window.profileGenerationEventSource = null;
                        };

                        return [window.dash_clientside.no_update, 'connected'];
                    }

                    return [window.dash_clientside.no_update, 'idle'];
                }
            };
        ''')

    ], fluid=True, className='p-4')


# =====================================================
# SSE CLIENTSIDE CALLBACK REGISTRATION
# =====================================================

from dash import clientside_callback, ClientsideFunction

# Register clientside callback for SSE handling
clientside_callback(
    ClientsideFunction(
        namespace='generation_sse',
        function_name='handle_sse'
    ),
    Output('generation-process-state', 'data', allow_duplicate=True),
    Output('sse-connection-status', 'children'),
    Input('sse-control-store', 'data'),
    State('generation-process-state', 'data'),
    prevent_initial_call=False
)


# =====================================================
# STEPPER RENDERING
# =====================================================

def render_stepper(current_step):
    """Render step indicator"""
    steps = [
        {'number': 1, 'title': 'Method & Timeframe', 'icon': 'bi-activity'},
        {'number': 2, 'title': 'Data Source', 'icon': 'bi-database'},
        {'number': 3, 'title': 'Constraints', 'icon': 'bi-sliders'},
        {'number': 4, 'title': 'Review & Generate', 'icon': 'bi-file-text'}
    ]

    stepper_items = []
    for i, step in enumerate(steps):
        is_active = current_step >= step['number']
        is_current = current_step == step['number']

        # Step circle
        circle_class = 'bg-primary text-white' if is_active else 'bg-secondary text-white'
        step_circle = html.Div([
            html.I(className=f'bi {step["icon"]}' if is_active else 'bi bi-circle')
        ], className=f'rounded-circle d-flex align-items-center justify-center {circle_class}',
           style={'width': '40px', 'height': '40px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})

        # Step info
        step_info = html.Div([
            html.Div(f'Step {step["number"]}', className='small text-muted'),
            html.Div(step['title'], className=f'fw-bold {"text-primary" if is_current else "text-dark"}')
        ], className='ms-2')

        step_item = html.Div([step_circle, step_info], className='d-flex align-items-center')

        stepper_items.append(html.Div(step_item, className='flex-shrink-0'))

        # Add connector line (except after last step)
        if i < len(steps) - 1:
            line_class = 'bg-primary' if current_step > step['number'] else 'bg-secondary'
            stepper_items.append(
                html.Div(className=f'flex-grow-1 {line_class}', style={'height': '2px', 'margin': '0 15px'})
            )

    return html.Div(stepper_items, className='d-flex align-items-center justify-content-center')


# =====================================================
# STEP 1: METHOD & TIMEFRAME
# =====================================================

def render_step_1(state, base_years):
    """Render Step 1: Method & Timeframe"""
    return html.Div([
        html.H3('Method & Timeframe', className='mb-3'),
        html.P('Choose the core method and define the profile\'s timeframe.', className='text-muted mb-4'),

        # Profile Details Section
        html.H5('Profile Details', className='text-uppercase text-muted small mb-3'),
        dbc.Row([
            dbc.Col([
                dbc.Label('Profile Name', className='fw-bold'),
                dbc.Input(
                    id='profile-name-input',
                    placeholder='Project_Profile_V1',
                    value=state.get('profileName', ''),
                    invalid=bool(state.get('profileNameError'))
                ),
                dbc.FormFeedback(state.get('profileNameError', ''), type='invalid')
            ], md=4),
            dbc.Col([
                dbc.Label('Start Year', className='fw-bold'),
                dbc.Input(
                    id='start-year-input',
                    type='number',
                    min=2000,
                    max=2100,
                    value=state.get('startYear', '')
                )
            ], md=4),
            dbc.Col([
                dbc.Label('End Year', className='fw-bold'),
                dbc.Input(
                    id='end-year-input',
                    type='number',
                    min=2000,
                    max=2100,
                    value=state.get('endYear', '')
                )
            ], md=4)
        ], className='mb-4'),

        # Method Selection Section
        html.H5('Select Method', className='text-uppercase text-muted small mb-3'),

        # Single RadioItems for method selection (fixes duplicate ID issue)
        dbc.RadioItems(
            id='method-radio',
            options=[
                {'label': 'Base Profile Method', 'value': 'base'},
                {'label': 'STL Decomposition', 'value': 'stl'}
            ],
            value=state.get('selectedMethod', 'base'),
            inline=False,
            className='mb-3'
        ),

        # Conditional display based on selected method
        dbc.Collapse(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className='bi bi-graph-up me-2'),
                        html.H6('Base Profile Method', className='d-inline')
                    ], className='mb-2'),
                    html.P('Extrapolates a profile based on a single historical reference year.',
                          className='small text-muted mb-3'),
                    dbc.Label('Select Base Year:', className='fw-bold mb-2'),
                    dbc.Select(
                        id='base-year-select',
                        options=[{'label': str(y), 'value': y} for y in base_years] if base_years else [],
                        value=state.get('baseYear', base_years[0] if base_years else None),
                        disabled=not base_years
                    )
                ])
            ], className='border-primary', style={'borderWidth': '2px'}),
            is_open=state.get('selectedMethod') == 'base'
        ),

        dbc.Collapse(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className='bi bi-bezier2 me-2'),
                        html.H6('STL Decomposition', className='d-inline')
                    ], className='mb-2'),
                    html.P('Advanced seasonal-trend analysis for better accuracy. This method uses historical data patterns to generate more accurate profiles.',
                          className='small text-muted mb-3')
                ])
            ], className='border-primary', style={'borderWidth': '2px'}),
            is_open=state.get('selectedMethod') == 'stl'
        )
    ])


# =====================================================
# STEP 2: DATA SOURCE
# =====================================================

def render_step_2(state, scenarios):
    """Render Step 2: Data Source"""
    return html.Div([
        html.H3('Total Demand Source', className='mb-3 text-center'),
        html.P('Choose where to pull annual demand targets from.', className='text-muted mb-4 text-center'),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className='bi bi-file-spreadsheet me-2'),
                            html.H6('Use \'Total Demand\' sheet', className='d-inline')
                        ], className='mb-2'),
                        html.P('Requires a \'Total_Demand\' sheet in your input Excel file.',
                              className='small text-muted mb-3'),
                        dbc.Button(
                            'Select',
                            id='select-template-btn',
                            color='primary' if state.get('demandSource') == 'template' else 'outline-primary',
                            size='sm'
                        )
                    ])
                ], className='h-100 border-primary' if state.get('demandSource') == 'template' else 'h-100',
                   style={'borderWidth': '2px' if state.get('demandSource') == 'template' else '1px'})
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className='bi bi-check-circle me-2'),
                            html.H6('Use demand projection scenario', className='d-inline')
                        ], className='mb-2'),
                        html.P('Uses the consolidated results from a previously run forecast.',
                              className='small text-muted mb-3'),
                        dbc.Collapse(
                            dbc.Select(
                                id='projection-scenario-select',
                                options=[{'label': s, 'value': s} for s in scenarios] if scenarios else [],
                                value=state.get('projectionScenario', scenarios[0] if scenarios else None),
                                disabled=not scenarios
                            ),
                            is_open=state.get('demandSource') == 'projection'
                        ),
                        dbc.Button(
                            'Select',
                            id='select-projection-btn',
                            color='primary' if state.get('demandSource') == 'projection' else 'outline-primary',
                            size='sm',
                            disabled=not scenarios
                        )
                    ])
                ], className='h-100 border-primary' if state.get('demandSource') == 'projection' else 'h-100',
                   style={'borderWidth': '2px' if state.get('demandSource') == 'projection' else '1px'})
            ], md=6)
        ], className='justify-content-center')
    ])


# =====================================================
# STEP 3: CONSTRAINTS
# =====================================================

def render_step_3(state):
    """Render Step 3: Constraints"""
    constraint_options = [
        {'value': 'auto', 'title': 'Auto-calculate from base year', 'desc': 'Automatically derive constraints from the selected base year data.'},
        {'value': 'excel', 'title': 'Use constraints from Excel file', 'desc': 'Read peak and minimum constraints from the input Excel template.'},
        {'value': 'none', 'title': 'No monthly constraints', 'desc': 'Generate the profile without applying any monthly constraints.'}
    ]

    return html.Div([
        html.H3('Monthly Constraints', className='mb-3 text-center'),
        html.P('Choose how to apply monthly peak/min constraints to shape the profile.',
              className='text-muted mb-4 text-center'),

        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.RadioItems(
                                id='constraint-radio',
                                options=[{
                                    'label': html.Div([
                                        html.H6(opt['title'], className='mb-1'),
                                        html.P(opt['desc'], className='small text-muted mb-0')
                                    ]),
                                    'value': opt['value']
                                } for opt in constraint_options],
                                value=state.get('monthlyConstraint'),
                                className='d-flex flex-column gap-3'
                            )
                        ])
                    ])
                ])
            ], md=8, className='mx-auto')
        ])
    ])


# =====================================================
# STEP 4: REVIEW & GENERATE
# =====================================================

def render_step_4(state):
    """Render Step 4: Review & Generate"""

    summary_items = [
        ('Profile Name', state.get('profileName', 'N/A')),
        ('Timeframe', f"{state.get('startYear', 'N/A')} to {state.get('endYear', 'N/A')}"),
        ('Generation Method', 'Base Profile' if state.get('selectedMethod') == 'base' else 'STL Decomposition'),
        ('Base Profile Year', state.get('baseYear', 'N/A') if state.get('selectedMethod') == 'base' else 'N/A'),
        ('Total Demand Source', 'Template Sheet' if state.get('demandSource') == 'template' else 'Projection Scenario'),
        ('Projection Scenario', state.get('projectionScenario', 'N/A') if state.get('demandSource') == 'projection' else 'N/A'),
        ('Monthly Constraints', (state.get('monthlyConstraint', '').capitalize() if state.get('monthlyConstraint') else 'None'))
    ]

    return html.Div([
        html.H3('Review & Generate', className='mb-3'),
        html.P('Confirm the settings below before starting the generation process.', className='text-muted mb-4'),

        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Dt(label, className='text-muted small mb-1'),
                        html.Dd(value, className='fw-bold mb-3')
                    ], md=4)
                    for label, value in summary_items
                ])
            ], className='bg-light')
        ])
    ])


# =====================================================
# CALLBACKS
# =====================================================

# Wizard stepper rendering
@callback(
    Output('wizard-stepper', 'children'),
    Input('wizard-state', 'data')
)
def update_stepper(state):
    return render_stepper(state.get('currentStep', 1))


# Step content rendering
@callback(
    Output('wizard-step-content', 'children'),
    Input('wizard-state', 'data'),
    State('available-base-years', 'data'),
    State('available-scenarios', 'data')
)
def render_step_content(state, base_years, scenarios):
    step = state.get('currentStep', 1)
    if step == 1:
        return render_step_1(state, base_years)
    elif step == 2:
        return render_step_2(state, scenarios)
    elif step == 3:
        return render_step_3(state)
    elif step == 4:
        return render_step_4(state)
    return html.Div()


# Navigation button visibility
@callback(
    Output('wizard-back-btn', 'style'),
    Output('wizard-next-btn', 'style'),
    Output('wizard-generate-btn', 'style'),
    Input('wizard-state', 'data')
)
def update_button_visibility(state):
    step = state.get('currentStep', 1)
    back_style = {'display': 'none'} if step == 1 else {}
    next_style = {} if step < 4 else {'display': 'none'}
    generate_style = {} if step == 4 else {'display': 'none'}
    return back_style, next_style, generate_style


# Profile name validation (debounced)
@callback(
    Output('wizard-state', 'data', allow_duplicate=True),
    Input('profile-name-input', 'value'),
    State('wizard-state', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=False
)
def validate_profile_name(profile_name, state, active_project):
    if not profile_name or not active_project:
        return StateManager.merge_state(state, {'profileName': profile_name, 'profileNameError': ''})

    try:
        # Check if profile exists
        response = api.check_profile_exists(active_project['path'], profile_name)
        exists = response.get('exists', False)
        error = 'This profile name already exists.' if exists else ''
        return StateManager.merge_state(state, {'profileName': profile_name, 'profileNameError': error})
    except:
        return StateManager.merge_state(state, {'profileName': profile_name, 'profileNameError': ''})


# Update state from inputs (generic)
@callback(
    Output('wizard-state', 'data', allow_duplicate=True),
    Input('start-year-input', 'value'),
    Input('end-year-input', 'value'),
    Input('method-radio', 'value'),
    Input('base-year-select', 'value'),
    Input('source-radio', 'value'),
    Input('projection-scenario-select', 'value'),
    Input('constraint-radio', 'value'),
    State('wizard-state', 'data'),
    prevent_initial_call=False
)
def update_wizard_state(start_year, end_year, method, base_year, source, scenario, constraint, state):
    ctx = callback_context
    if not ctx.triggered:
        return no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    updates = {}
    if trigger_id == 'start-year-input':
        updates['startYear'] = start_year
    elif trigger_id == 'end-year-input':
        updates['endYear'] = end_year
    elif trigger_id == 'method-radio':
        updates['selectedMethod'] = method
    elif trigger_id == 'base-year-select':
        updates['baseYear'] = base_year
    elif trigger_id == 'source-radio':
        updates['demandSource'] = source
    elif trigger_id == 'projection-scenario-select':
        updates['projectionScenario'] = scenario
    elif trigger_id == 'constraint-radio':
        updates['monthlyConstraint'] = constraint

    return StateManager.merge_state(state, updates)


# Load base years when method is base
@callback(
    Output('available-base-years', 'data'),
    Input('method-radio', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=False
)
def load_base_years(method, active_project):
    if method != 'base' or not active_project:
        return []

    try:
        response = api.get_available_base_years(active_project['path'])
        return response.get('years', [])
    except:
        return []


# Load scenarios when source is projection
@callback(
    Output('available-scenarios', 'data'),
    Input('source-radio', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=False
)
def load_scenarios(source, active_project):
    if source != 'projection' or not active_project:
        return []

    try:
        response = api.get_scenarios(active_project['path'])
        return response.get('scenarios', [])
    except:
        return []


# Navigation - Back button
@callback(
    Output('wizard-state', 'data', allow_duplicate=True),
    Input('wizard-back-btn', 'n_clicks'),
    State('wizard-state', 'data'),
    prevent_initial_call=True
)
def go_back(n_clicks, state):
    if not n_clicks:
        return no_update
    current_step = state.get('currentStep', 1)
    return StateManager.merge_state(state, {'currentStep': max(1, current_step - 1)})


# Navigation - Next button with validation
@callback(
    Output('wizard-state', 'data', allow_duplicate=True),
    Input('wizard-next-btn', 'n_clicks'),
    State('wizard-state', 'data'),
    prevent_initial_call=True
)
def go_next(n_clicks, state):
    if not n_clicks:
        return no_update

    current_step = state.get('currentStep', 1)

    # Validation per step
    if current_step == 1:
        is_valid = (
            state.get('profileName') and
            not state.get('profileNameError') and
            state.get('startYear') and
            state.get('endYear') and
            state.get('selectedMethod') and
            (state.get('selectedMethod') != 'base' or state.get('baseYear'))
        )
    elif current_step == 2:
        is_valid = (
            state.get('demandSource') and
            (state.get('demandSource') != 'projection' or state.get('projectionScenario'))
        )
    elif current_step == 3:
        is_valid = bool(state.get('monthlyConstraint'))
    else:
        is_valid = True

    if is_valid:
        return StateManager.merge_state(state, {'currentStep': min(4, current_step + 1)})

    return no_update


# Generate button - start generation with SSE
@callback(
    Output('generation-process-state', 'data', allow_duplicate=True),
    Output('generate-progress-modal', 'is_open', allow_duplicate=True),
    Output('sse-control-store', 'data', allow_duplicate=True),
    Input('wizard-generate-btn', 'n_clicks'),
    State('wizard-state', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def start_generation(n_clicks, wizard_state, active_project):
    if not n_clicks or not active_project:
        return no_update, no_update, no_update

    # Build payload
    payload = {
        'projectPath': active_project['path'],
        'profileConfiguration': {
            'general': {
                'profile_name': wizard_state.get('profileName'),
                'start_year': wizard_state.get('startYear'),
                'end_year': wizard_state.get('endYear')
            },
            'generation_method': {
                'type': wizard_state.get('selectedMethod'),
                'base_year': wizard_state.get('baseYear') if wizard_state.get('selectedMethod') == 'base' else None
            },
            'data_source': {
                'type': wizard_state.get('demandSource'),
                'scenario_name': wizard_state.get('projectionScenario') if wizard_state.get('demandSource') == 'projection' else None
            },
            'constraints': {
                'monthly_method': wizard_state.get('monthlyConstraint')
            }
        }
    }

    try:
        # Start generation
        api.generate_profile(payload)

        # Update process state
        process_state = {
            'isRunning': True,
            'percentage': 5,
            'message': 'Starting profile generation...',
            'taskProgress': '',
            'logs': [{'time': datetime.now().strftime('%H:%M:%S'), 'type': 'info', 'text': 'Generation started'}],
            'status': 'running',
            'modalVisible': True,
            'modalMinimized': False
        }

        # Trigger SSE connection (React parity)
        sse_url = api.get_generation_status_url()
        sse_control = {'action': 'start', 'url': sse_url}

        return process_state, True, sse_control
    except Exception as e:
        process_state = {
            'isRunning': False,
            'status': 'failed',
            'logs': [{'time': datetime.now().strftime('%H:%M:%S'), 'type': 'error', 'text': f'Failed to start: {str(e)}'}],
            'modalVisible': True
        }
        return process_state, True, no_update


# REMOVED: Old polling callback - replaced with SSE for real-time updates (React parity)
# SSE provides instant updates without 1-second polling delay


# Update progress modal UI
@callback(
    Output('generate-progress-text', 'children'),
    Output('generate-progress-bar', 'value'),
    Output('generate-task-progress', 'children'),
    Output('generate-logs-container', 'children'),
    Input('generation-process-state', 'data')
)
def update_progress_ui(process_state):
    message = process_state.get('message', 'Processing...')
    percentage = process_state.get('percentage', 0)
    task_progress = process_state.get('taskProgress', '')
    logs = process_state.get('logs', [])

    # Format logs
    log_elements = []
    for log in logs[-20:]:  # Show last 20 logs
        color_map = {
            'success': 'text-success',
            'error': 'text-danger',
            'warning': 'text-warning',
            'progress': 'text-primary',
            'info': 'text-muted'
        }
        color_class = color_map.get(log.get('type', 'info'), 'text-muted')
        log_elements.append(
            html.Div([
                html.Span(f"[{log.get('time')}] ", className='text-muted'),
                html.Span(log.get('text', ''), className=color_class)
            ], className='mb-1')
        )

    return message, percentage, task_progress, log_elements


# Modal minimize/maximize
@callback(
    Output('generation-process-state', 'data', allow_duplicate=True),
    Output('generate-progress-modal', 'is_open', allow_duplicate=True),
    Input('minimize-generate-modal-btn', 'n_clicks'),
    Input('generate-floating-indicator', 'n_clicks'),
    State('generation-process-state', 'data'),
    prevent_initial_call=False
)
def toggle_modal_minimize(minimize_n, indicator_n, process_state):
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'minimize-generate-modal-btn':
        # Minimize modal
        process_state['modalMinimized'] = True
        return process_state, False

    elif trigger_id == 'generate-floating-indicator':
        # Show modal from floating indicator
        process_state['modalMinimized'] = False
        return process_state, True

    return no_update, no_update


# Floating indicator visibility
@callback(
    Output('generate-floating-indicator', 'style'),
    Output('generate-floating-indicator', 'children'),
    Input('generation-process-state', 'data')
)
def update_floating_indicator(process_state):
    is_minimized = process_state.get('modalMinimized', False)
    is_running = process_state.get('isRunning', False)

    if is_minimized and is_running:
        percentage = process_state.get('percentage', 0)
        style = {
            'position': 'fixed',
            'bottom': '20px',
            'right': '20px',
            'zIndex': '9999',
            'cursor': 'pointer',
            'display': 'block'
        }
        content = dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className='bi bi-arrow-repeat spin me-2'),
                    html.Span('Profile Generation', className='fw-bold')
                ], className='mb-2'),
                dbc.Progress(value=percentage, className='mb-1', style={'height': '8px'}),
                html.Div(f'{percentage}% complete', className='small text-muted')
            ], className='p-2')
        ], className='shadow-lg border-primary', style={'minWidth': '250px'})
        return style, content
    else:
        return {'display': 'none'}, None


# Close modal button with AUTO-NAVIGATION and SSE cleanup (React parity)
@callback(
    Output('generate-progress-modal', 'is_open', allow_duplicate=True),
    Output('generation-process-state', 'data', allow_duplicate=True),
    Output('selected-page-store', 'data', allow_duplicate=True),
    Output('sse-control-store', 'data', allow_duplicate=True),
    Input('close-generate-modal-btn', 'n_clicks'),
    State('generation-process-state', 'data'),
    State('url', 'pathname'),
    prevent_initial_call=True
)
def close_modal_and_navigate(n_clicks, process_state, current_path):
    if not n_clicks:
        return no_update, no_update, no_update, no_update

    # Stop SSE connection when closing modal
    sse_control = {'action': 'stop', 'url': ''}

    # If completed, navigate to analyze page (AUTO-NAVIGATION)
    if process_state.get('status') == 'completed':
        # Reset process state
        process_state = {
            'isRunning': False,
            'percentage': 0,
            'message': '',
            'taskProgress': '',
            'logs': [],
            'status': 'idle',
            'modalVisible': False,
            'modalMinimized': False
        }
        # Navigate to Analyze Profiles page ✅
        return False, process_state, 'Analyze Profiles', sse_control

    # Otherwise just close
    process_state['modalVisible'] = False
    return False, process_state, no_update, sse_control
