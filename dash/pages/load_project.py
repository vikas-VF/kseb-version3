"""
Load Project Page - Full Implementation  
Complete project loading with validation and recent projects list
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2('📂 Load Existing Project', className='mb-4',
                       style={'fontWeight': '700', 'color': '#1e293b'}),
                
                dbc.Card([
                    dbc.CardBody([
                        # Project path input
                        html.Label('Project Path', className='form-label fw-bold'),
                        dbc.InputGroup([
                            dbc.Input(
                                id='load-project-path-input',
                                type='text',
                                placeholder='/path/to/project/folder',
                            ),
                            dbc.Button('Browse', id='browse-project-btn', color='secondary')
                        ], className='mb-3'),
                        dbc.FormText('Enter the full path to an existing project directory'),
                        
                        # Load button
                        html.Div([
                            dbc.Button(
                                '🚀 Load Project',
                                id='load-project-btn',
                                color='primary',
                                size='lg',
                                className='w-100 fw-bold mt-3'
                            )
                        ]),
                        
                        # Output/feedback
                        html.Div(id='load-project-output', className='mt-3')
                    ])
                ], className='shadow-sm'),
                
                # Recent projects
                dbc.Card([
                    dbc.CardHeader(html.H5('🕒 Recent Projects', className='mb-0')),
                    dbc.CardBody(
                        html.Div(id='recent-projects-list-load')
                    )
                ], className='mt-4')
                
            ], width=12, lg=8, className='mx-auto')
        ])
    ], fluid=True, className='p-4')
