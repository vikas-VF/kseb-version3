"""
Home Page - Complete Dashboard with Working UI
Full implementation with action cards and recent projects
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import os
from pathlib import Path

def layout(active_project=None):
    """
    Create complete home page with working dashboard
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
        },
        {
            'id': 'demand-forecast',
            'title': 'Demand Forecasting',
            'icon': '📈',
            'description': 'Forecast energy demand using ML models',
            'page': 'Demand Projection',
            'color': '#059669',
            'gradient': 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
        },
        {
            'id': 'load-profiles',
            'title': 'Load Profiles',
            'icon': '⚡',
            'description': 'Generate and analyze hourly load profiles',
            'page': 'Generate Profiles',
            'color': '#ea580c',
            'gradient': 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)'
        },
        {
            'id': 'pypsa-optimization',
            'title': 'PyPSA Grid Optimization',
            'icon': '🔌',
            'description': 'Optimize power grid with PyPSA suite',
            'page': 'Model Config',
            'color': '#9333ea',
            'gradient': 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)'
        },
        {
            'id': 'settings',
            'title': 'Settings',
            'icon': '⚙️',
            'description': 'Configure application preferences',
            'page': 'Settings',
            'color': '#64748b',
            'gradient': 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)'
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
                html.Button(
                    'Open →',
                    id={'type': 'nav-link', 'page': card['page']},
                    className='btn btn-sm w-100',
                    style={
                        'background': card['gradient'],
                        'border': 'none',
                        'color': 'white',
                        'padding': '0.5rem',
                        'borderRadius': '0.375rem',
                        'fontWeight': '600',
                        'marginTop': '0.5rem',
                        'cursor': 'pointer',
                        'transition': 'all 0.2s'
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
                        f"🕒 Loaded: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
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

    # Recent projects section
    recent_projects_section = dbc.Card([
        dbc.CardHeader(
            html.H4('📂 Recent Projects', style={'margin': '0', 'fontWeight': '700', 'color': '#1e293b'})
        ),
        dbc.CardBody(
            html.Div(
                id='recent-projects-list',
                children=[
                    dbc.Alert(
                        'No recent projects. Create or load a project to get started!',
                        color='secondary'
                    )
                ]
            )
        )
    ], style={'marginTop': '2rem', 'border': '1px solid #e2e8f0'})

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

        # Quick Actions
        html.H2(
            '🚀 Quick Actions',
            style={
                'fontSize': '1.5rem',
                'fontWeight': '700',
                'color': '#1e293b',
                'marginBottom': '1.5rem',
                'marginTop': '2rem'
            }
        ),
        dbc.Row([
            dbc.Col(create_action_card(card), width=12, md=6, lg=4, className='mb-4')
            for card in action_cards
        ]),

        # Recent projects
        recent_projects_section

    ], fluid=True, style={'padding': '2rem'})
