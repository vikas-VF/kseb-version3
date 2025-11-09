"""
Demand Visualization Page - PHASE 1: Layout & Navigation
Full feature parity with React DemandVisualization.jsx

This is Part 1 of the implementation.
Includes: Layout, state management, scenario loading, tab navigation
"""

from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_client import api
from utils.state_manager import StateManager, ConversionFactors


def layout(active_project=None):
    """Complete Demand Visualization page with scenario analysis"""

    if not active_project:
        return dbc.Container([
            dbc.Alert([
                html.H4('⚠️ No Project Loaded', className='alert-heading'),
                html.P('Please load or create a project first to visualize demand forecasts.'),
                dbc.Button('Go to Projects', id={'type': 'nav-link', 'page': 'Load Project'},
                          color='primary')
            ], color='warning')
        ], className='p-4')

    return dbc.Container([
        # Model Selection Modal
        dbc.Modal([
            dbc.ModalHeader('🎯 Model Selection'),
            dbc.ModalBody([
                dbc.Alert('Select forecasting model for each sector:', color='info', className='mb-3'),
                html.Div(id='model-selection-content')
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancel', id='cancel-model-selection-btn', color='secondary', className='me-2'),
                dbc.Button('Apply & Calculate', id='apply-model-selection-btn', color='primary')
            ])
        ], id='model-selection-modal', is_open=False, size='lg'),

        # Compare Scenario Modal
        dbc.Modal([
            dbc.ModalHeader('📊 Compare Scenarios'),
            dbc.ModalBody([
                dbc.Alert('Select a scenario to compare with the current selection:', color='info', className='mb-3'),
                html.Div(id='compare-scenario-content')
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancel', id='cancel-compare-btn', color='secondary', className='me-2'),
                dbc.Button('Compare', id='apply-compare-btn', color='success')
            ])
        ], id='compare-scenario-modal', is_open=False),

        # Header
        html.Div([
            html.Div([
                html.H2(
                    '📊 Demand Visualization - Scenario Analysis',
                    style={'fontSize': '1.75rem', 'fontWeight': '700',
                          'color': '#1e293b', 'marginBottom': '0.5rem'}
                ),
                html.P(
                    f'Project: {active_project.get("name", "Unknown")}',
                    style={'fontSize': '0.875rem', 'color': '#64748b', 'marginBottom': '0'}
                )
            ], style={'flex': '1'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '1.5rem'}),

        # Controls Row
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # Scenario Selector
                    dbc.Col([
                        dbc.Label('Scenario:', className='fw-bold mb-1', style={'fontSize': '0.875rem'}),
                        dcc.Dropdown(
                            id='viz-scenario-selector',
                            placeholder='Select scenario...',
                            clearable=False,
                            style={'minWidth': '200px'}
                        )
                    ], width='auto'),

                    # Start Year
                    dbc.Col([
                        dbc.Label('Start Year:', className='fw-bold mb-1', style={'fontSize': '0.875rem'}),
                        dbc.Input(
                            id='viz-start-year',
                            type='number',
                            min=2000,
                            max=2100,
                            step=1,
                            style={'width': '120px'}
                        )
                    ], width='auto'),

                    # End Year
                    dbc.Col([
                        dbc.Label('End Year:', className='fw-bold mb-1', style={'fontSize': '0.875rem'}),
                        dbc.Input(
                            id='viz-end-year',
                            type='number',
                            min=2000,
                            max=2100,
                            step=1,
                            style={'width': '120px'}
                        )
                    ], width='auto'),

                    # Unit Selector
                    dbc.Col([
                        dbc.Label('Unit:', className='fw-bold mb-1', style={'fontSize': '0.875rem'}),
                        dcc.Dropdown(
                            id='viz-unit-selector',
                            options=[
                                {'label': 'MWh', 'value': 'mwh'},
                                {'label': 'kWh', 'value': 'kwh'},
                                {'label': 'GWh', 'value': 'gwh'},
                                {'label': 'TWh', 'value': 'twh'}
                            ],
                            value='mwh',
                            clearable=False,
                            style={'width': '120px'}
                        )
                    ], width='auto'),

                    # Action Buttons
                    dbc.Col([
                        dbc.Label(html.Span('\u00A0'), className='mb-1', style={'fontSize': '0.875rem'}),
                        html.Div([
                            dbc.Button(
                                [html.I(className='bi bi-gear me-2'), 'Model Selection'],
                                id='open-model-selection-btn',
                                color='primary',
                                outline=True,
                                size='sm',
                                className='me-2'
                            ),
                            dbc.Button(
                                [html.I(className='bi bi-arrow-left-right me-2'), 'Compare Scenario'],
                                id='open-compare-btn',
                                color='info',
                                outline=True,
                                size='sm'
                            )
                        ])
                    ], width='auto', className='ms-auto')
                ], align='center')
            ], className='p-3')
        ], className='mb-3'),

        # Comparison Mode Banner
        html.Div(id='comparison-banner'),

        # Main Content Tabs
        dbc.Card([
            dbc.CardHeader([
                dbc.Tabs([
                    dbc.Tab(label='📈 Sector Data', tab_id='sector'),
                    dbc.Tab(label='⚡ T&D Losses', tab_id='td_losses'),
                    dbc.Tab(label='📊 Consolidated Results', tab_id='consolidated')
                ], id='viz-main-tabs', active_tab='sector')
            ]),
            dbc.CardBody([
                html.Div(id='viz-tab-content')
            ])
        ]),

        # Loading overlay
        dcc.Loading(
            id='demand-viz-loading',
            type='circle',
            children=html.Div(id='viz-loading-trigger')
        ),

        # Toast container
        html.Div(id='viz-toast-container', style={
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'zIndex': '9999'
        }),

        # State stores
        dcc.Store(id='demand-viz-state', storage_type='session', data={
            'selectedScenario': None,
            'startYear': None,
            'endYear': None,
            'targetYear': None,
            'unit': 'mwh',
            'activeTab': 'sector',
            'demandType': 'gross',
            'selectedSector': None,
            'modelSelections': {},
            'comparisonMode': False,
            'scenariosToCompare': {'scenario1': None, 'scenario2': None}
        }),
        dcc.Store(id='viz-scenarios-list', data=[]),
        dcc.Store(id='viz-sectors-list', data=[]),
        dcc.Store(id='viz-available-models', data={}),
        dcc.Store(id='viz-sector-data', data=None),
        dcc.Store(id='viz-consolidated-data', data=None),
        dcc.Store(id='viz-comparison-sector-data', data=None),
        dcc.Store(id='viz-td-losses', data={}),
        dcc.Store(id='viz-saved-state', data={'isSaved': False})

    ], fluid=True, style={'padding': '2rem'})


# ==================================================
# SCENARIO LOADING
# ==================================================

@callback(
    Output('viz-scenarios-list', 'data'),
    Output('viz-scenario-selector', 'options'),
    Input('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_scenarios(active_project):
    """Load scenarios for the project"""
    if not active_project or not active_project.get('path'):
        return [], []

    try:
        response = api.get_scenarios(active_project['path'])
        scenarios = response.get('scenarios', [])
        options = [{'label': s, 'value': s} for s in scenarios]
        return scenarios, options
    except Exception as e:
        print(f"Error loading scenarios: {e}")
        return [], []


@callback(
    Output('demand-viz-state', 'data', allow_duplicate=True),
    Output('viz-scenario-selector', 'value'),
    Input('viz-scenarios-list', 'data'),
    State('demand-viz-state', 'data'),
    prevent_initial_call=True
)
def init_first_scenario(scenarios, state):
    """Auto-select first scenario"""
    if scenarios and not state.get('selectedScenario'):
        first = scenarios[0]
        updated = StateManager.merge_state(state, {'selectedScenario': first})
        return updated, first
    return no_update, no_update


# ========================================
# TAB CONTENT RENDERING
# ========================================

@callback(
    Output('viz-tab-content', 'children'),
    Input('viz-main-tabs', 'active_tab'),
    State('demand-viz-state', 'data')
)
def render_tab_content(active_tab, state):
    """Render content based on active tab"""

    if not active_tab or not state.get('selectedScenario'):
        return dbc.Alert('Please select a scenario to begin.', color='info')

    if active_tab == 'sector':
        return html.Div([
            html.H5('Sector Data View - Coming in Part 2', className='text-muted'),
            dbc.Alert('Sector data visualization with line charts, multiple models, and forecast markers.', color='info')
        ])
    elif active_tab == 'td_losses':
        return html.Div([
            html.H5('T&D Losses - Coming in Part 2', className='text-muted'),
            dbc.Alert('Transmission & Distribution losses configuration and visualization.', color='info')
        ])
    elif active_tab == 'consolidated':
        return html.Div([
            html.H5('Consolidated Results - Coming in Part 2', className='text-muted'),
            dbc.Alert('Consolidated demand results with area charts, stacked bar charts, and model selection.', color='info')
        ])

    return html.Div('Unknown tab')


# THIS IS PART 1 - Foundation complete!
# Next parts will add:
# - Sector data view with line charts
# - T&D losses tab
# - Consolidated results with area/bar charts
# - Model selection modal
# - Comparison mode
# - Export functionality
