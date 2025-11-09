"""
Load Project Page - COMPLETE IMPLEMENTATION
Full feature parity with React LoadProject.jsx
Includes: path validation, metadata loading, recent projects integration
"""

from dash import html, dcc, callback, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_client import api
from utils.state_manager import StateManager, format_date


def layout():
    """
    Complete load project page
    """

    return dbc.Container([
        # Header
        html.Div([
            html.H1(
                '📂 Load Existing Project',
                style={
                    'fontSize': '2rem',
                    'fontWeight': '700',
                    'color': '#0f172a',
                    'marginBottom': '0.5rem'
                }
            ),
            html.P(
                'Open an existing energy analytics project workspace',
                style={
                    'fontSize': '1rem',
                    'color': '#475569',
                    'marginBottom': '2rem'
                }
            )
        ]),

        # Main form
        dbc.Row([
            # Left column - Load form
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5('📁 Project Location', className='mb-0',
                               style={'fontWeight': '700', 'color': '#1e293b'})
                    ),
                    dbc.CardBody([
                        dbc.Label('Project Directory Path *', className='fw-bold mb-2'),
                        dbc.InputGroup([
                            dbc.Input(
                                id='load-project-path-input',
                                type='text',
                                placeholder='e.g., C:\\Projects\\MyProject or /home/user/projects/MyProject',
                                className='mb-2'
                            ),
                            dbc.Button(
                                '📁 Browse',
                                id='browse-project-btn',
                                color='secondary',
                                outline=True
                            )
                        ], className='mb-2'),

                        # Validation feedback
                        html.Div(id='load-path-validation-feedback', className='mb-3'),

                        # Project info preview (when valid)
                        html.Div(id='project-info-preview', className='mb-3'),

                        # Load button
                        dbc.Button(
                            '📂 Load Project',
                            id='load-project-btn',
                            color='primary',
                            size='lg',
                            className='w-100'
                        ),

                        # Status messages
                        html.Div(id='load-project-status', className='mt-3')
                    ])
                ], className='mb-4')
            ], width=12, md=7),

            # Right column - Quick tips
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        html.H5('💡 Quick Tips', className='mb-0',
                               style={'fontWeight': '700', 'color': '#1e293b'})
                    ),
                    dbc.CardBody([
                        html.Ul([
                            html.Li([
                                html.Strong('Valid Project: '),
                                'Must contain ',
                                html.Code('inputs/'),
                                ' and ',
                                html.Code('results/'),
                                ' folders'
                            ], className='mb-2'),
                            html.Li([
                                html.Strong('Metadata: '),
                                'If ',
                                html.Code('project.json'),
                                ' exists, project info will be loaded automatically'
                            ], className='mb-2'),
                            html.Li([
                                html.Strong('Recent Projects: '),
                                'Loaded projects appear in Home page recent list'
                            ], className='mb-2'),
                            html.Li([
                                html.Strong('Auto-Navigation: '),
                                'After loading, you\'ll be directed to Demand Projection'
                            ])
                        ], className='mb-0', style={'fontSize': '0.875rem'})
                    ])
                ], className='mb-4', style={'border': '1px solid #e2e8f0'}),

                # Project structure reference
                dbc.Card([
                    dbc.CardHeader(
                        html.H5('📁 Expected Structure', className='mb-0',
                               style={'fontWeight': '700', 'color': '#1e293b'})
                    ),
                    dbc.CardBody([
                        html.Div([
                            html.Div('ProjectName/', className='fw-bold'),
                            html.Div('├─ 📁 inputs/', className='ms-3 font-monospace'),
                            html.Div('├─ 📁 results/', className='ms-3 font-monospace'),
                            html.Div('│  ├─ demand_forecasts/', className='ms-4 font-monospace text-muted'),
                            html.Div('│  ├─ load_profiles/', className='ms-4 font-monospace text-muted'),
                            html.Div('│  └─ pypsa_optimization/', className='ms-4 font-monospace text-muted'),
                            html.Div('└─ 📄 project.json', className='ms-3 font-monospace text-muted'),
                        ], style={'fontSize': '0.875rem'})
                    ])
                ], style={'border': '1px solid #e2e8f0'})
            ], width=12, md=5)
        ])

    ], fluid=True, style={'maxWidth': '1200px', 'padding': '2rem'})


# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    Output('load-path-validation-feedback', 'children'),
    Output('project-info-preview', 'children'),
    Input('load-project-path-input', 'value')
)
def validate_and_preview_project(path):
    """
    Validate project path and show preview if valid
    """
    if not path:
        return '', ''

    if not path.strip():
        return dbc.Alert('❌ Path cannot be empty', color='danger', className='py-2'), ''

    # Check if path exists
    if not os.path.exists(path):
        return dbc.Alert('❌ Directory does not exist', color='danger', className='py-2'), ''

    if not os.path.isdir(path):
        return dbc.Alert('❌ Path is not a directory', color='danger', className='py-2'), ''

    # Check for required folders
    inputs_path = os.path.join(path, 'inputs')
    results_path = os.path.join(path, 'results')

    missing_folders = []
    if not os.path.exists(inputs_path):
        missing_folders.append('inputs/')
    if not os.path.exists(results_path):
        missing_folders.append('results/')

    if missing_folders:
        return dbc.Alert([
            html.Strong('⚠️ Not a valid project directory'),
            html.P(f'Missing required folders: {", ".join(missing_folders)}', className='mb-0 mt-1')
        ], color='warning', className='py-2'), ''

    # Valid project - load metadata if available
    validation_alert = dbc.Alert('✅ Valid project directory', color='success', className='py-2')

    # Try to load project.json
    metadata_path = os.path.join(path, 'project.json')
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Show project info preview
            preview_card = dbc.Card([
                dbc.CardHeader(
                    html.H6('📊 Project Information', className='mb-0')
                ),
                dbc.CardBody([
                    html.Div([
                        html.Strong('Name: '),
                        html.Span(metadata.get('name', 'Unknown'))
                    ], className='mb-2'),
                    html.Div([
                        html.Strong('Description: '),
                        html.Span(metadata.get('description', 'No description'))
                    ], className='mb-2') if metadata.get('description') else '',
                    html.Div([
                        html.Strong('Created: '),
                        html.Span(format_date(metadata.get('created'), 'full'))
                    ], className='mb-2') if metadata.get('created') else '',
                    html.Div([
                        html.Strong('Version: '),
                        html.Span(metadata.get('version', 'N/A'))
                    ])
                ], className='py-2')
            ], className='mt-2', color='light')

            return validation_alert, preview_card

        except Exception as e:
            # Metadata exists but couldn't read it
            preview_note = dbc.Alert(
                f'ℹ️ project.json found but couldn\'t read: {str(e)}',
                color='info',
                className='py-2 mt-2'
            )
            return validation_alert, preview_note

    # Valid project but no metadata
    preview_note = dbc.Alert(
        'ℹ️ No project.json found. Project name will be derived from folder name.',
        color='info',
        className='py-2 mt-2'
    )

    return validation_alert, preview_note


@callback(
    Output('load-project-status', 'children'),
    Output('active-project-store', 'data', allow_duplicate=True),
    Output('recent-projects-store', 'data', allow_duplicate=True),
    Output('url', 'pathname', allow_duplicate=True),
    Input('load-project-btn', 'n_clicks'),
    State('load-project-path-input', 'value'),
    State('recent-projects-store', 'data'),
    prevent_initial_call=True
)
def load_project(n_clicks, path, recent_projects):
    """
    Load project and update stores
    """
    if not n_clicks:
        return no_update, no_update, no_update, no_update

    # Validation
    if not path or not path.strip():
        return dbc.Alert('❌ Please enter a project path', color='danger'), no_update, no_update, no_update

    if not os.path.exists(path) or not os.path.isdir(path):
        return dbc.Alert('❌ Invalid project path', color='danger'), no_update, no_update, no_update

    # Check for required folders
    inputs_path = os.path.join(path, 'inputs')
    results_path = os.path.join(path, 'results')

    if not os.path.exists(inputs_path) or not os.path.exists(results_path):
        return dbc.Alert(
            '❌ Not a valid project directory (missing inputs/ or results/ folders)',
            color='danger'
        ), no_update, no_update, no_update

    try:
        # Try to load metadata
        metadata_path = os.path.join(path, 'project.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            project_name = metadata.get('name', os.path.basename(path))
            project_description = metadata.get('description', '')
        else:
            # Use folder name as project name
            project_name = os.path.basename(path)
            project_description = ''

        # Create project data
        project_data = StateManager.create_project_state(
            name=project_name,
            path=path,
            description=project_description
        )

        # Update recent projects
        updated_recent = StateManager.update_recent_projects(recent_projects, project_data)

        # Success and navigate
        success_alert = dbc.Alert([
            html.H5('✅ Project Loaded Successfully!', className='alert-heading'),
            html.P([
                html.Strong('Name: '), project_name
            ], className='mb-1'),
            html.P([
                html.Strong('Path: '), html.Code(path)
            ], className='mb-0')
        ], color='success')

        # Navigate to Demand Projection after a moment
        return success_alert, project_data, updated_recent, '/demand-projection'

    except Exception as e:
        return dbc.Alert(
            f'❌ Error loading project: {str(e)}',
            color='danger'
        ), no_update, no_update, no_update
