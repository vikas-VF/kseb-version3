"""
Home Page - COMPLETE IMPLEMENTATION
Full feature parity with React Home.jsx
Includes: search, sort, delete, workflow guide, recent projects
"""

from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, callback_context, no_update
import dash_bootstrap_components as dbc
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.state_manager import StateManager, format_date


def layout(active_project=None):
    """
    Complete home page with all features
    """

    # Action cards configuration
    action_cards = [
        {
            'id': 'create-project',
            'title': 'Create New Project',
            'icon': '📝',
            'description': 'Start a new energy analytics project',
            'page': 'Create Project',
            'color': '#4f46e5',
            'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        },
        {
            'id': 'load-project',
            'title': 'Load Project',
            'icon': '📂',
            'description': 'Open an existing project workspace',
            'page': 'Load Project',
            'color': '#0891b2',
            'gradient': 'linear-gradient(135deg, #0891b2 0%, #06b6d4 100%)'
        }
    ]

    # Create action card component
    def create_action_card(card):
        return dbc.Card(
            dbc.CardBody([
                html.Div(
                    card['icon'],
                    style={
                        'fontSize': '3.5rem',
                        'marginBottom': '1rem',
                        'textAlign': 'center'
                    }
                ),
                html.H4(
                    card['title'],
                    className="card-title text-center",
                    style={
                        'fontWeight': '700',
                        'color': '#1e293b',
                        'marginBottom': '0.75rem',
                        'fontSize': '1.125rem'
                    }
                ),
                html.P(
                    card['description'],
                    className="card-text text-center",
                    style={
                        'color': '#64748b',
                        'fontSize': '0.875rem',
                        'lineHeight': '1.6',
                        'minHeight': '50px'
                    }
                ),
                dbc.Button(
                    'Open →',
                    id={'type': 'nav-link', 'page': card['page']},
                    className='w-100',
                    style={
                        'background': card['gradient'],
                        'border': 'none',
                        'color': 'white',
                        'padding': '0.5rem',
                        'borderRadius': '0.375rem',
                        'fontWeight': '600',
                        'marginTop': '0.5rem'
                    }
                )
            ]),
            style={
                'height': '100%',
                'border': f'2px solid {card["color"]}20',
                'borderRadius': '0.75rem',
                'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                'transition': 'all 0.3s',
                'background': 'white'
            },
            className='action-card hover-shadow'
        )

    # Active project banner
    project_banner = None
    if active_project:
        project_banner = dbc.Alert([
            html.Div([
                html.Div('✅', style={'fontSize': '2.5rem', 'marginRight': '1rem'}),
                html.Div([
                    html.H3(
                        active_project.get('name', 'Unknown Project'),
                        style={'margin': '0', 'color': 'white', 'fontWeight': '700'}
                    ),
                    html.P(
                        f"📁 {active_project.get('path', 'N/A')}",
                        style={'margin': '0.25rem 0 0 0', 'color': '#cbd5e1', 'fontSize': '0.875rem'}
                    ),
                    html.P(
                        f"🕒 Loaded: {format_date(active_project.get('lastOpened'), 'full')}",
                        style={'margin': '0.25rem 0 0 0', 'color': '#94a3b8', 'fontSize': '0.8125rem'}
                    )
                ], style={'flex': '1'})
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], color='primary', style={'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'border': 'none', 'marginBottom': '2rem'})
    else:
        project_banner = dbc.Alert([
            html.Div([
                html.Div('ℹ️', style={'fontSize': '1.5rem', 'marginRight': '1rem'}),
                html.Div([
                    html.Strong('No Project Loaded'),
                    html.P('Create a new project or load an existing one to get started',
                          style={'margin': '0.25rem 0 0 0', 'fontSize': '0.875rem'})
                ])
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], color='info', style={'marginBottom': '2rem'})

    # Statistics cards
    stats_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div('📊', style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3('0', id='total-projects-count', style={'margin': '0', 'fontWeight': '700', 'color': '#1e293b'}),
                            html.P('Total Projects', style={'margin': '0', 'color': '#64748b', 'fontSize': '0.875rem'})
                        ], style={'marginLeft': '1rem'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ])
            ], style={'border': '1px solid #e2e8f0'})
        ], width=12, md=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div('📈', style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3('0', id='total-forecasts-count', style={'margin': '0', 'fontWeight': '700', 'color': '#1e293b'}),
                            html.P('Forecasts Run', style={'margin': '0', 'color': '#64748b', 'fontSize': '0.875rem'})
                        ], style={'marginLeft': '1rem'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ])
            ], style={'border': '1px solid #e2e8f0'})
        ], width=12, md=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div('⚡', style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3('0', id='total-profiles-count', style={'margin': '0', 'fontWeight': '700', 'color': '#1e293b'}),
                            html.P('Load Profiles', style={'margin': '0', 'color': '#64748b', 'fontSize': '0.875rem'})
                        ], style={'marginLeft': '1rem'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ])
            ], style={'border': '1px solid #e2e8f0'})
        ], width=12, md=4)
    ], className='mb-4')

    # Main layout
    return dbc.Container([
        # Delete confirmation modal
        dbc.Modal([
            dbc.ModalHeader('Confirm Delete'),
            dbc.ModalBody([
                html.P(id='delete-confirm-message'),
                dbc.Alert(
                    'Note: This will only remove the project from this list. It will not delete any files from your computer.',
                    color='warning',
                    className='mb-0'
                )
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancel', id='cancel-delete-btn', color='secondary', className='me-2'),
                dbc.Button('Delete', id='confirm-delete-btn', color='danger')
            ])
        ], id='delete-confirm-modal', is_open=False),

        # Header
        html.Div([
            html.H1(
                '🏢 KSEB Energy Analytics Platform',
                style={
                    'fontSize': '2.25rem',
                    'fontWeight': '700',
                    'color': '#0f172a',
                    'marginBottom': '0.5rem',
                    'textAlign': 'center'
                }
            ),
            html.P(
                'Comprehensive energy demand forecasting, load profile generation, and grid optimization suite',
                style={
                    'fontSize': '1.125rem',
                    'color': '#475569',
                    'marginBottom': '2rem',
                    'textAlign': 'center'
                }
            )
        ]),

        # Active project banner
        project_banner,

        # Statistics
        stats_cards,

        # Main content row
        dbc.Row([
            # Left column - Quick Actions and Recent Projects
            dbc.Col([
                # Quick Actions
                html.H2(
                    '🚀 Quick Actions',
                    style={
                        'fontSize': '1.5rem',
                        'fontWeight': '700',
                        'color': '#1e293b',
                        'marginBottom': '1.5rem'
                    }
                ),
                dbc.Row([
                    dbc.Col(create_action_card(card), width=12, md=6, className='mb-4')
                    for card in action_cards
                ], className='mb-4'),

                # Recent Projects
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H4('📂 Recent Projects', className='mb-0',
                                   style={'fontWeight': '700', 'color': '#1e293b'}),
                        ]),
                    ]),
                    dbc.CardBody([
                        # Search and Sort row
                        dbc.Row([
                            dbc.Col([
                                dbc.InputGroup([
                                    dbc.InputGroupText('🔍'),
                                    dbc.Input(
                                        id='projects-search',
                                        type='text',
                                        placeholder='Search projects...',
                                        debounce=True
                                    )
                                ])
                            ], width=8),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='projects-sort',
                                    options=[
                                        {'label': 'Last Opened', 'value': 'lastOpened'},
                                        {'label': 'Name (A-Z)', 'value': 'name'}
                                    ],
                                    value='lastOpened',
                                    clearable=False
                                )
                            ], width=4)
                        ], className='mb-3'),

                        # Projects table
                        html.Div(id='recent-projects-table')
                    ])
                ], style={'border': '1px solid #e2e8f0'})
            ], width=12, lg=8),

            # Right column - Workflow Guide
            dbc.Col([
                create_workflow_sidebar(active_project)
            ], width=12, lg=4)
        ])

    ], fluid=True, style={'padding': '2rem'})


def create_workflow_sidebar(active_project):
    """Create workflow guide sidebar"""

    def workflow_card(icon, title, description, page, disabled):
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(icon, style={'fontSize': '1.2rem', 'marginRight': '0.75rem'}),
                    html.Div([
                        html.Strong(title, style={'fontSize': '0.9rem', 'display': 'block'}),
                        html.Small(description, className='text-muted')
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'alignItems': 'center'}),
                dbc.Button(
                    '→',
                    id={'type': 'nav-link', 'page': page},
                    size='sm',
                    disabled=disabled,
                    color='primary' if not disabled else 'secondary',
                    className='mt-2 w-100'
                )
            ], style={'padding': '0.75rem'})
        ], className='mb-2', style={'border': '1px solid #e2e8f0'})

    return dbc.Card([
        dbc.CardHeader(
            html.H5('🚀 Complete Workflow', className='mb-0',
                   style={'fontWeight': '700', 'color': '#1e293b'})
        ),
        dbc.CardBody([
            # Demand Forecasting Section
            html.H6('📈 Demand Forecasting', className='mt-2 mb-2',
                   style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#4f46e5'}),
            html.Div([
                workflow_card('📊', 'Demand Projection', 'Configure & run forecast',
                             'Demand Projection', not active_project),
                workflow_card('📉', 'Demand Visualization', 'View forecast results',
                             'Demand Visualization', not active_project),
            ], className='ms-3 border-start border-2 ps-3 mb-3'),

            # Load Profiles Section
            html.H6('⚡ Load Profiles', className='mt-3 mb-2',
                   style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#ea580c'}),
            html.Div([
                workflow_card('🔋', 'Generate Profiles', 'Create hourly profiles',
                             'Generate Profiles', not active_project),
                workflow_card('📊', 'Analyze Profiles', 'View profile analytics',
                             'Analyze Profiles', not active_project),
            ], className='ms-3 border-start border-2 ps-3 mb-3'),

            # PyPSA Suite Section
            html.H6('🔌 PyPSA Suite', className='mt-3 mb-2',
                   style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#9333ea'}),
            html.Div([
                workflow_card('⚙️', 'Model Config', 'Configure PyPSA model',
                             'Model Config', not active_project),
                workflow_card('📈', 'View Results', 'PyPSA optimization results',
                             'View Results', not active_project),
            ], className='ms-3 border-start border-2 ps-3 mb-3'),

            # System Section
            html.H6('🛠️ System', className='mt-3 mb-2',
                   style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#64748b'}),
            html.Div([
                workflow_card('⚙️', 'Settings', 'App preferences',
                             'Settings', False),
            ], className='ms-3 border-start border-2 ps-3'),
        ])
    ], style={'border': '1px solid #e2e8f0'})


# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    Output('recent-projects-table', 'children'),
    Output('total-projects-count', 'children'),
    Input('projects-search', 'value'),
    Input('projects-sort', 'value'),
    Input('recent-projects-store', 'data'),
    State('active-project-store', 'data')
)
def update_projects_table(search_term, sort_by, projects_data, active_project):
    """Update recent projects table with search and sort"""

    if not projects_data:
        return dbc.Alert(
            'No recent projects. Create or load a project to get started!',
            color='secondary'
        ), '0'

    # Filter
    filtered = projects_data
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            p for p in filtered
            if search_lower in p.get('name', '').lower()
            or search_lower in p.get('path', '').lower()
        ]

    # Sort
    if sort_by == 'name':
        filtered.sort(key=lambda x: x.get('name', '').lower())
    else:
        filtered.sort(key=lambda x: x.get('lastOpened', ''), reverse=True)

    if not filtered:
        return dbc.Alert(
            '🔍 No projects found matching your search.',
            color='secondary'
        ), str(len(projects_data))

    # Build table
    active_path = active_project.get('path') if active_project else None

    rows = []
    for project in filtered:
        is_active = project.get('path') == active_path

        row_style = {}
        if is_active:
            row_style = {'backgroundColor': '#f0f4ff', 'fontWeight': '500'}

        rows.append(
            html.Tr([
                # Project Name Column
                html.Td([
                    html.Div([
                        html.Span('● ', style={'color': '#10b981', 'fontSize': '1.2rem'}) if is_active else '',
                        html.Strong(project.get('name', 'Unknown'), className='me-2'),
                        html.Span('(Active)', className='badge bg-success') if is_active else ''
                    ], className='mb-1'),
                    html.Small(
                        f"📁 {project.get('path', 'N/A')}",
                        className='text-muted d-block'
                    )
                ], style={'verticalAlign': 'middle'}),

                # Last Opened Column
                html.Td(
                    format_date(project.get('lastOpened'), 'full'),
                    style={'verticalAlign': 'middle', 'fontSize': '0.875rem'}
                ),

                # Actions Column
                html.Td([
                    dbc.ButtonGroup([
                        dbc.Button(
                            '🗑️',
                            id={'type': 'delete-project-btn', 'index': project.get('id')},
                            color='danger',
                            size='sm',
                            outline=True,
                            title='Remove from list'
                        ),
                        dbc.Button(
                            '📂 Open',
                            id={'type': 'open-project-btn', 'index': project.get('id')},
                            color='primary',
                            size='sm'
                        )
                    ], size='sm')
                ], style={'verticalAlign': 'middle', 'textAlign': 'right'})
            ], style=row_style)
        )

    table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th('Project Name', style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#64748b'}),
                html.Th('Last Opened', style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#64748b'}),
                html.Th('Actions', style={'fontSize': '0.875rem', 'fontWeight': '600', 'color': '#64748b', 'textAlign': 'right'})
            ])
        ], className='border-bottom'),
        html.Tbody(rows)
    ], bordered=True, hover=True, responsive=True, className='mb-0')

    return table, str(len(projects_data))


@callback(
    Output('delete-confirm-modal', 'is_open'),
    Output('delete-project-id-store', 'data'),
    Output('delete-confirm-message', 'children'),
    Input({'type': 'delete-project-btn', 'index': ALL}, 'n_clicks'),
    State('delete-confirm-modal', 'is_open'),
    State('recent-projects-store', 'data'),
    prevent_initial_call=True
)
def toggle_delete_modal(n_clicks_list, is_open, projects_data):
    """Show delete confirmation modal"""

    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return False, None, ''

    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json
    project_id = json.loads(button_id)['index']

    # Find project name
    project = next((p for p in projects_data if p.get('id') == project_id), None)
    if not project:
        return False, None, ''

    message = f'Are you sure you want to remove "{project.get("name")}" from the recent projects list?'

    return True, project_id, message


@callback(
    Output('recent-projects-store', 'data', allow_duplicate=True),
    Output('active-project-store', 'data', allow_duplicate=True),
    Output('delete-confirm-modal', 'is_open', allow_duplicate=True),
    Input('confirm-delete-btn', 'n_clicks'),
    Input('cancel-delete-btn', 'n_clicks'),
    State('delete-project-id-store', 'data'),
    State('recent-projects-store', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def handle_delete(confirm_clicks, cancel_clicks, project_id, projects_data, active_project):
    """Handle project deletion"""

    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, False

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'cancel-delete-btn':
        return no_update, no_update, False

    if button_id == 'confirm-delete-btn' and confirm_clicks and project_id:
        # Remove project from list
        updated_projects = [p for p in projects_data if p.get('id') != project_id]

        # Clear active project if it's the one being deleted
        updated_active = active_project
        if active_project and active_project.get('id') == project_id:
            updated_active = None

        return updated_projects, updated_active, False

    return no_update, no_update, no_update


@callback(
    Output('active-project-store', 'data', allow_duplicate=True),
    Output('recent-projects-store', 'data', allow_duplicate=True),
    Output('url', 'pathname', allow_duplicate=True),
    Input({'type': 'open-project-btn', 'index': ALL}, 'n_clicks'),
    State('recent-projects-store', 'data'),
    prevent_initial_call=True
)
def open_project(n_clicks_list, projects_data):
    """Open project and navigate to Demand Projection"""

    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return no_update, no_update, no_update

    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json
    project_id = json.loads(button_id)['index']

    # Find project
    project = next((p for p in projects_data if p.get('id') == project_id), None)
    if not project:
        return no_update, no_update, no_update

    # Update lastOpened
    from datetime import datetime
    updated_project = project.copy()
    updated_project['lastOpened'] = datetime.now().isoformat()

    # Update recent projects list (move to front)
    updated_recent = StateManager.update_recent_projects(projects_data, updated_project)

    # Navigate to Demand Projection
    return updated_project, updated_recent, '/demand-projection'
