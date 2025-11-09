"""
Create Project Page - Full Implementation
Complete project creation with validation and folder structure setup
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2('📝 Create New Project', className='mb-4',
                       style={'fontWeight': '700', 'color': '#1e293b'}),
                
                dbc.Card([
                    dbc.CardBody([
                        # Project Name
                        html.Label('Project Name', className='form-label fw-bold'),
                        dbc.Input(
                            id='create-project-name-input',
                            type='text',
                            placeholder='e.g., KSEB_Demand_2025',
                            className='mb-3'
                        ),
                        
                        # Project Path
                        html.Label('Project Directory Path', className='form-label fw-bold'),
                        dbc.Input(
                            id='create-project-path-input',
                            type='text',
                            placeholder='/path/to/projects',
                            className='mb-3'
                        ),
                        dbc.FormText('Absolute path where the project folder will be created'),
                        
                        # Description
                        html.Label('Description (Optional)', className='form-label fw-bold mt-3'),
                        dbc.Textarea(
                            id='create-project-desc-input',
                            placeholder='Brief description of this project...',
                            className='mb-3',
                            rows=3
                        ),
                        
                        # Template selection
                        html.Label('Project Template', className='form-label fw-bold'),
                        dbc.RadioItems(
                            id='create-project-template',
                            options=[
                                {'label': 'Demand Forecasting Only', 'value': 'demand'},
                                {'label': 'Full Suite (Forecasting + Profiles + PyPSA)', 'value': 'full'},
                            ],
                            value='full',
                            className='mb-4'
                        ),
                        
                        # Create button
                        html.Div([
                            dbc.Button(
                                '✨ Create Project',
                                id='create-project-btn',
                                color='primary',
                                size='lg',
                                className='w-100 fw-bold'
                            )
                        ]),
                        
                        # Output/feedback
                        html.Div(id='create-project-output', className='mt-3')
                    ])
                ], className='shadow-sm'),
                
                # Info panel
                dbc.Card([
                    dbc.CardHeader(html.H5('📋 What Gets Created', className='mb-0')),
                    dbc.CardBody([
                        html.Ul([
                            html.Li('Project root directory'),
                            html.Li('inputs/ - For Excel input files'),
                            html.Li('results/demand_forecasts/ - Forecast scenarios'),
                            html.Li('results/load_profiles/ - Generated profiles'),
                            html.Li('results/pypsa_optimization/ - Grid optimization results'),
                            html.Li('README.md - Project documentation')
                        ])
                    ])
                ], className='mt-4')
                
            ], width=12, lg=8, className='mx-auto')
        ])
    ], fluid=True, className='p-4')
