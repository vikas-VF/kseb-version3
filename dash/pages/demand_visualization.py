"""
Demand Visualization Page - PHASE 1 & 2: Layout + Sector Data View
Full feature parity with React DemandVisualization.jsx

Part 1: Layout, state management, scenario loading, tab navigation
Part 2: Sector data view with line charts, models, forecast markers
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
    State('demand-viz-state', 'data'),
    State('viz-sectors-list', 'data')
)
def render_tab_content(active_tab, state, sectors):
    """Render content based on active tab"""

    if not active_tab or not state.get('selectedScenario'):
        return dbc.Alert('Please select a scenario to begin.', color='info')

    if active_tab == 'sector':
        return render_sector_data_view(state, sectors)
    elif active_tab == 'td_losses':
        return html.Div([
            html.H5('T&D Losses - Coming in Part 3', className='text-muted'),
            dbc.Alert('Transmission & Distribution losses configuration and visualization.', color='info')
        ])
    elif active_tab == 'consolidated':
        return html.Div([
            html.H5('Consolidated Results - Coming in Part 3', className='text-muted'),
            dbc.Alert('Consolidated demand results with area charts, stacked bar charts, and model selection.', color='info')
        ])

    return html.Div('Unknown tab')


def render_sector_data_view(state, sectors):
    """Render Sector Data tab content with controls and chart"""

    if not sectors:
        return dbc.Alert('No sectors available for this scenario.', color='info')

    selected_sector = state.get('selectedSector') or (sectors[0] if sectors else None)
    demand_type = state.get('demandType', 'gross')

    return dbc.Container([
        # Controls Row
        dbc.Row([
            dbc.Col([
                dbc.Label('Sector:', className='fw-bold mb-1'),
                dcc.Dropdown(
                    id='viz-sector-selector',
                    options=[{'label': s, 'value': s} for s in sectors],
                    value=selected_sector,
                    clearable=False
                )
            ], width=6),
            dbc.Col([
                dbc.Label('Demand Type:', className='fw-bold mb-1'),
                dbc.RadioItems(
                    id='viz-demand-type-selector',
                    options=[
                        {'label': ' Gross', 'value': 'gross'},
                        {'label': ' Net', 'value': 'net'},
                        {'label': ' On-Grid', 'value': 'on_grid'}
                    ],
                    value=demand_type,
                    inline=True
                )
            ], width=6)
        ], className='mb-3'),

        # Line Chart
        html.Div(id='viz-sector-line-chart'),

        # Data Table
        html.Div(id='viz-sector-data-table', className='mt-3')
    ], fluid=True)


# ==================================================
# PART 2: SECTOR DATA VIEW
# ==================================================

# Load sectors for selected scenario
@callback(
    Output('viz-sectors-list', 'data'),
    Input('viz-scenario-selector', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_sectors(scenario, active_project):
    """Load sectors for selected scenario"""
    if not scenario or not active_project:
        return []

    try:
        response = api.get_scenario_sectors(active_project['path'], scenario)
        sectors = response.get('sectors', [])
        return sectors
    except Exception as e:
        print(f"Error loading sectors: {e}")
        return []


# Update selected sector in state
@callback(
    Output('demand-viz-state', 'data', allow_duplicate=True),
    Input('viz-sector-selector', 'value'),
    State('demand-viz-state', 'data'),
    prevent_initial_call=True
)
def update_selected_sector(sector, state):
    """Update selected sector in state"""
    if not sector:
        return no_update

    updated = StateManager.merge_state(state, {'selectedSector': sector})
    return updated


# Update demand type in state
@callback(
    Output('demand-viz-state', 'data', allow_duplicate=True),
    Input('viz-demand-type-selector', 'value'),
    State('demand-viz-state', 'data'),
    prevent_initial_call=True
)
def update_demand_type(demand_type, state):
    """Update demand type in state"""
    if not demand_type:
        return no_update

    updated = StateManager.merge_state(state, {'demandType': demand_type})
    return updated


# Load sector data from API
@callback(
    Output('viz-sector-data', 'data'),
    Input('viz-sector-selector', 'value'),
    Input('viz-start-year', 'value'),
    Input('viz-end-year', 'value'),
    State('viz-scenario-selector', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_sector_data(sector, start_year, end_year, scenario, active_project):
    """Load sector data from backend"""
    if not sector or not scenario or not active_project:
        return None

    if not start_year or not end_year:
        return None

    try:
        response = api.get_sector_data(
            active_project['path'],
            scenario,
            sector,
            start_year=start_year,
            end_year=end_year
        )
        return response.get('data', {})
    except Exception as e:
        print(f"Error loading sector data: {e}")
        return None


# Render sector line chart
@callback(
    Output('viz-sector-line-chart', 'children'),
    Input('viz-sector-data', 'data'),
    State('viz-unit-selector', 'value'),
    State('viz-sector-selector', 'value'),
    State('demand-viz-state', 'data')
)
def render_sector_line_chart(data, unit, sector, state):
    """Render line chart with multiple models and forecast marker"""
    if not data or not sector:
        return dbc.Alert('No data available. Please select a sector.', color='info')

    try:
        # Extract data
        years = data.get('years', [])
        forecast_start_year = data.get('forecastStartYear')
        models = data.get('models', {})

        if not years or not models:
            return dbc.Alert('No model data available for this sector.', color='warning')

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)

        # Create figure
        fig = go.Figure()

        # Define model colors
        model_colors = {
            'Historical': '#000000',
            'MLR': '#3b82f6',
            'SLR': '#10b981',
            'WAM': '#f59e0b',
            'Time Series': '#8b5cf6',
            'User Data': '#ef4444'
        }

        # Add trace for each model
        for model_name, model_data in models.items():
            if model_data:
                fig.add_trace(go.Scatter(
                    x=years,
                    y=[v * factor if v is not None else None for v in model_data],
                    name=model_name,
                    mode='lines+markers',
                    line=dict(
                        width=2,
                        color=model_colors.get(model_name, '#6b7280'),
                        dash='solid' if model_name != 'Historical' else 'solid'
                    ),
                    marker=dict(size=4),
                    hovertemplate=f'{model_name}<br>Year: %{{x}}<br>Demand: %{{y:.2f}} {ConversionFactors.get_label(unit)}<extra></extra>'
                ))

        # Add forecast marker line (dashed red vertical line)
        if forecast_start_year and forecast_start_year in years:
            y_min = 0
            y_max = max([max([v for v in model_data if v is not None], default=0) * factor
                        for model_data in models.values()], default=100) * 1.1

            fig.add_trace(go.Scatter(
                x=[forecast_start_year, forecast_start_year],
                y=[y_min, y_max],
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                showlegend=False,
                hoverinfo='skip'
            ))

            # Add labels for Historical and Projected regions
            mid_y = y_max / 2

            fig.add_annotation(
                x=years[0] + (forecast_start_year - years[0]) / 2,
                y=y_max * 0.95,
                text='Historical/Actual',
                showarrow=False,
                font=dict(size=10, color='#64748b'),
                bgcolor='rgba(255,255,255,0.8)'
            )

            fig.add_annotation(
                x=forecast_start_year + (years[-1] - forecast_start_year) / 2,
                y=y_max * 0.95,
                text='Projected',
                showarrow=False,
                font=dict(size=10, color='#64748b'),
                bgcolor='rgba(255,255,255,0.8)'
            )

        # Update layout
        fig.update_layout(
            title=f'{sector} - Demand Forecast ({ConversionFactors.get_label(unit)})',
            xaxis_title='Year',
            yaxis_title=f'Electricity Demand ({ConversionFactors.get_label(unit)})',
            hovermode='x unified',
            legend=dict(orientation='h', y=-0.2),
            height=500,
            template='plotly_white',
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='linear'
            )
        )

        return dcc.Graph(figure=fig, config={'displayModeBar': True})

    except Exception as e:
        return dbc.Alert(f'Error rendering chart: {str(e)}', color='danger')


# Render sector data table
@callback(
    Output('viz-sector-data-table', 'children'),
    Input('viz-sector-data', 'data'),
    State('viz-unit-selector', 'value'),
    State('viz-sector-selector', 'value')
)
def render_sector_data_table(data, unit, sector):
    """Render data table with all models"""
    if not data or not sector:
        return dbc.Alert('No data available.', color='info')

    try:
        years = data.get('years', [])
        models = data.get('models', {})

        if not years or not models:
            return dbc.Alert('No model data available.', color='warning')

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)

        # Build table data
        table_data = {'Year': years}
        for model_name, model_data in models.items():
            table_data[model_name] = [v * factor if v is not None else 'N/A' for v in model_data]

        df = pd.DataFrame(table_data)

        # Format numbers
        for col in df.columns:
            if col != 'Year':
                df[col] = df[col].apply(lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else x)

        # Create table
        table = dbc.Table.from_dataframe(
            df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm',
            className='mb-0'
        )

        return html.Div([
            html.H5(f'{sector} - Data Table ({ConversionFactors.get_label(unit)})', className='mb-3'),
            html.Div([
                table
            ], style={'maxHeight': '400px', 'overflowY': 'auto'}),
            html.P(
                f'Showing data in {ConversionFactors.get_label(unit)}. Models: {", ".join(models.keys())}',
                className='text-muted mt-3 mb-0',
                style={'fontSize': '0.875rem'}
            )
        ])

    except Exception as e:
        return dbc.Alert(f'Error rendering table: {str(e)}', color='danger')


# THIS IS PART 1 & 2 - Foundation + Sector Data View complete!
# Next parts will add:
# - T&D losses tab (Part 3)
# - Consolidated results with area/bar charts (Part 4)
# - Model selection modal (Part 5)
# - Comparison mode (Part 6)
# - Export functionality (Part 7)
