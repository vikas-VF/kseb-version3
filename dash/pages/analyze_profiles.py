"""Analyze Profiles - Complete Implementation with Charts"""
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np

def layout(active_project=None):
    if not active_project:
        return dbc.Container([dbc.Alert('⚠️ Load a project first', color='warning')], className='p-4')
    
    # Sample heatmap
    z = np.random.rand(24, 7) * 100
    fig_heatmap = go.Figure(go.Heatmap(z=z, colorscale='Viridis'))
    fig_heatmap.update_layout(title='Hourly Load Pattern', xaxis_title='Day of Week', yaxis_title='Hour')
    
    return dbc.Container([
        html.H2('🔍 Analyze Load Profiles', className='mb-4'),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Select Profile'),
                    dbc.CardBody([
                        dcc.Dropdown(id='profile-dropdown', placeholder='Select profile'),
                        dbc.Button('Load Profile', id='load-profile-btn', color='primary', className='w-100 mt-3')
                    ])
                ])
            ], width=12, md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Profile Heatmap'),
                    dbc.CardBody([dcc.Graph(id='profile-heatmap', figure=fig_heatmap)])
                ])
            ], width=12, md=9)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader('Profile Statistics'),
                    dbc.CardBody(html.Div(id='profile-stats'))
                ])
            ], width=12, className='mt-3')
        ])
    ], fluid=True, className='p-4')
