"""PyPSA Model Configuration - Complete Implementation"""
from dash import html, dcc
import dash_bootstrap_components as dbc

def layout(active_project=None):
    if not active_project:
        return dbc.Container([dbc.Alert('⚠️ Load a project first', color='warning')], className='p-4')
    
    return dbc.Container([
        html.H2('🔌 PyPSA Grid Optimization - Model Configuration', className='mb-4'),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Network Configuration'),
                    dbc.CardBody([
                        dbc.Label('Load Profile to Use'),
                        dcc.Dropdown(id='pypsa-profile-dropdown', placeholder='Select load profile'),
                        dbc.Label('Optimization Type', className='mt-3'),
                        dcc.Dropdown(id='pypsa-optimization-type', options=[
                            {'label': 'LOPF (Linear Optimal Power Flow)', 'value': 'lopf'},
                            {'label': 'Capacity Expansion', 'value': 'expansion'}
                        ], value='lopf'),
                        dbc.Label('Solver', className='mt-3'),
                        dcc.Dropdown(id='pypsa-solver', options=[
                            {'label': 'Gurobi', 'value': 'gurobi'},
                            {'label': 'CBC', 'value': 'cbc'},
                            {'label': 'GLPK', 'value': 'glpk'}
                        ], value='glpk'),
                        dbc.Label('Network Name', className='mt-3'),
                        dbc.Input(id='pypsa-network-name', placeholder='e.g., KSEB_Network_2025'),
                        dbc.Button('🚀 Run Optimization', id='start-pypsa-btn', 
                                 color='success', className='w-100 mt-4 fw-bold', size='lg')
                    ])
                ])
            ], width=12, md=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Optimization Progress'),
                    dbc.CardBody([
                        html.Div(id='pypsa-progress'),
                        html.Div(id='pypsa-output')
                    ])
                ]),
                dbc.Card([
                    dbc.CardHeader('Network Components', className='mt-3'),
                    dbc.CardBody([
                        html.Ul([
                            html.Li('Generators: Configure power plants'),
                            html.Li('Storage: Battery/hydro systems'),
                            html.Li('Lines: Transmission corridors'),
                            html.Li('Loads: Demand centers'),
                            html.Li('Transformers: Voltage conversion')
                        ])
                    ])
                ], className='mt-3')
            ], width=12, md=7)
        ])
    ], fluid=True, className='p-4')
