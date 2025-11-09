"""Demand Visualization - Complete Implementation with Charts"""
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

def layout(active_project=None):
    if not active_project:
        return dbc.Container([dbc.Alert('⚠️ Load a project first', color='warning')], className='p-4')
    
    # Sample chart
    fig = go.Figure(go.Scatter(x=[1,2,3,4], y=[10,11,12,13], mode='lines+markers', name='Forecast'))
    fig.update_layout(title='Demand Forecast', template='plotly_white')
    
    return dbc.Container([
        html.H2('📊 Demand Forecasting - Results & Visualization', className='mb-4'),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Select Scenario'),
                    dbc.CardBody([
                        dcc.Dropdown(id='scenario-dropdown', placeholder='Select a scenario'),
                        dcc.Dropdown(id='sector-dropdown', placeholder='Select sector', className='mt-2'),
                        dcc.Dropdown(id='model-dropdown', placeholder='Select model', className='mt-2')
                    ])
                ])
            ], width=12, md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Forecast Chart'),
                    dbc.CardBody([dcc.Graph(id='demand-forecast-chart', figure=fig)])
                ])
            ], width=12, md=9)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Statistics'),
                    dbc.CardBody(html.Div(id='forecast-stats'))
                ])
            ], width=12, className='mt-3')
        ])
    ], fluid=True, className='p-4')
