"""
Other Tools Page - Complete Implementation
Matches React OtherTools.jsx with tool cards for additional features
"""
from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    """Other Tools page layout with tool cards"""

    # Tool definitions matching React version
    tools = [
        {
            'icon': 'bi-sun-fill',
            'title': 'Rooftop Solar Projection',
            'description': 'Model and forecast the growth of distributed rooftop solar capacity and generation.',
            'color': '#4F46E5'
        },
        {
            'icon': 'bi-beaker',
            'title': 'Hydrogen Demand Modeling',
            'description': 'Analyze and project the future energy requirements for green hydrogen production.',
            'color': '#4F46E5'
        },
        {
            'icon': 'bi-lightning-charge-fill',
            'title': 'EV Penetration Modeling',
            'description': 'Simulate the adoption rate of electric vehicles and their impact on electricity demand.',
            'color': '#4F46E5'
        },
        {
            'icon': 'bi-grid-3x3-gap-fill',
            'title': 'Upcoming Tools',
            'description': 'A preview of new and exciting features currently in development for the platform.',
            'color': '#4F46E5'
        }
    ]

    return html.Div([
        # Main container
        html.Div([
            # Header section
            html.Div([
                html.H1('Other Tools', style={
                    'fontSize': '30px',
                    'fontWeight': '700',
                    'color': '#1E293B',
                    'marginBottom': '8px'
                }),
                html.P('A collection of utilities to assist with your modeling and analysis workflow.', style={
                    'fontSize': '16px',
                    'color': '#64748B',
                    'marginBottom': '32px'
                })
            ]),

            # Tools grid
            html.Div([
                create_tool_card(tool) for tool in tools
            ], style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(auto-fill, minmax(250px, 1fr))',
                'gap': '24px'
            })

        ], style={
            'maxWidth': '1280px',
            'margin': '0 auto',
            'padding': '32px'
        })
    ], style={
        'height': '100%',
        'width': '100%',
        'backgroundColor': '#F8FAFC',
        'overflowY': 'auto'
    })


def create_tool_card(tool):
    """Create a single tool card"""
    return html.Div([
        # Icon circle
        html.Div([
            html.I(className=tool['icon'], style={
                'fontSize': '28px',
                'color': tool['color']
            })
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'width': '56px',
            'height': '56px',
            'backgroundColor': '#EEF2FF',
            'borderRadius': '50%',
            'marginBottom': '16px',
            'border': '4px solid white',
            'boxShadow': '0 0 0 4px #EEF2FF'
        }),

        # Title
        html.H3(tool['title'], style={
            'fontSize': '18px',
            'fontWeight': '600',
            'color': '#1E293B',
            'marginBottom': '8px'
        }),

        # Description
        html.P(tool['description'], style={
            'fontSize': '14px',
            'color': '#64748B',
            'marginBottom': '16px',
            'lineHeight': '1.5'
        }),

        # Launch button
        html.Button([
            'Launch Tool'
        ], style={
            'width': '100%',
            'fontSize': '14px',
            'fontWeight': '600',
            'color': '#4F46E5',
            'backgroundColor': '#EEF2FF',
            'border': 'none',
            'borderRadius': '8px',
            'padding': '8px 16px',
            'cursor': 'pointer',
            'transition': 'background-color 0.2s'
        }, className='tool-launch-btn')

    ], style={
        'backgroundColor': 'white',
        'border': '1px solid #E2E8F0',
        'borderRadius': '12px',
        'padding': '24px',
        'transition': 'all 0.3s ease-in-out',
        'cursor': 'pointer'
    }, className='tool-card')
