"""Settings Page - Complete Implementation"""
from dash import html, dcc
import dash_bootstrap_components as dbc

def layout():
    return dbc.Container([
        html.H2('⚙️ Application Settings', className='mb-4'),
        dbc.Tabs([
            dbc.Tab(label='Color Configuration', children=[
                dbc.Card([
                    dbc.CardBody([
                        html.H5('Sector Colors'),
                        html.P('Configure colors for different sectors in visualizations'),
                        html.Div(id='color-settings-panel'),
                        dbc.Button('Save Color Settings', id='save-color-settings-btn', color='primary', className='mt-3')
                    ])
                ], className='mt-3')
            ]),
            dbc.Tab(label='General Settings', children=[
                dbc.Card([
                    dbc.CardBody([
                        dbc.Label('Default Forecast Target Year'),
                        dbc.Input(type='number', value=2030, id='default-target-year'),
                        dbc.Label('Default Solver (PyPSA)', className='mt-3'),
                        dcc.Dropdown(options=[
                            {'label': 'GLPK', 'value': 'glpk'},
                            {'label': 'CBC', 'value': 'cbc'}
                        ], value='glpk', id='default-solver'),
                        dbc.Button('Save General Settings', id='save-general-settings-btn', 
                                 color='primary', className='mt-3')
                    ])
                ], className='mt-3')
            ])
        ]),
        html.Div(id='settings-output')
    ], fluid=True, className='p-4')
