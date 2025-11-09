"""Generate Profiles - Complete Implementation"""
from dash import html, dcc
import dash_bootstrap_components as dbc

def layout(active_project=None):
    if not active_project:
        return dbc.Container([dbc.Alert('⚠️ Load a project first', color='warning')], className='p-4')
    
    return dbc.Container([
        html.H2('⚡ Generate Load Profiles', className='mb-4'),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Configuration'),
                    dbc.CardBody([
                        dbc.Label('Scenario to Use'),
                        dcc.Dropdown(id='profile-scenario-dropdown', placeholder='Select forecast scenario'),
                        dbc.Label('Profile Method', className='mt-3'),
                        dcc.Dropdown(id='profile-method-dropdown', options=[
                            {'label': 'Statistical Profiling', 'value': 'statistical'},
                            {'label': 'Historical Pattern', 'value': 'historical'}
                        ], value='statistical'),
                        dbc.Label('Profile Name', className='mt-3'),
                        dbc.Input(id='profile-name-input', placeholder='e.g., Baseline_Hourly'),
                        dbc.Button('🚀 Generate Profiles', id='start-profile-gen-btn', 
                                 color='success', className='w-100 mt-4 fw-bold', size='lg')
                    ])
                ])
            ], width=12, md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Generation Progress'),
                    dbc.CardBody([
                        html.Div(id='profile-gen-progress'),
                        html.Div(id='profile-gen-output')
                    ])
                ])
            ], width=12, md=8)
        ])
    ], fluid=True, className='p-4')
