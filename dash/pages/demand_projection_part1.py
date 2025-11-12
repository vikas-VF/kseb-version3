"""
Demand Projection Page - COMPLETE IMPLEMENTATION
Full feature parity with React DemandProjection.jsx

Features:
- Dual view mode (Consolidated vs Sector-specific)
- Backend integration (sectors, data, color config)
- 5 tabs per view (Data Table, Area Chart, Stacked Bar, Line Chart, Correlation)
- Unit conversion (MWh, kWh, GWh, TWh)
- State persistence
- Configure Forecast modal
- Real-time SSE progress tracking
"""

from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_client import api
from utils.state_manager import StateManager, ConversionFactors


def layout(active_project=None):
    """
    Complete Demand Projection page with dual views
    """

    if not active_project:
        return dbc.Container([
            dbc.Alert([
                html.H4('⚠️ No Project Loaded', className='alert-heading'),
                html.P('Please load or create a project first to use demand forecasting.'),
                dbc.Button('Go to Projects', id={'type': 'nav-link', 'page': 'Load Project'},
                          color='primary')
            ], color='warning')
        ], className='p-4')

    return dbc.Container([
        # Configure Forecast Modal
        dbc.Modal([
            dbc.ModalHeader('⚙️ Configure Demand Forecast'),
            dbc.ModalBody([
                html.Div(id='configure-forecast-modal-content')
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancel', id='cancel-forecast-btn', color='secondary', className='me-2'),
                dbc.Button('🚀 Start Forecasting', id='start-forecast-btn', color='success')
            ])
        ], id='configure-forecast-modal', is_open=False, size='xl'),

        # Progress Modal
        dbc.Modal([
            dbc.ModalHeader([
                html.Div([
                    html.H5('📊 Demand Forecasting in Progress', className='mb-0'),
                    dbc.Button('−', id='minimize-progress-modal', color='link',
                              className='ms-auto', style={'fontSize': '1.5rem'})
                ], style={'display': 'flex', 'width': '100%', 'alignItems': 'center'})
            ]),
            dbc.ModalBody([
                html.Div(id='forecast-progress-content')
            ]),
            dbc.ModalFooter([
                dbc.Button('Cancel Forecasting', id='cancel-forecasting-btn',
                          color='danger', outline=True, className='me-2'),
                dbc.Button('Close', id='close-progress-modal', color='secondary')
            ])
        ], id='forecast-progress-modal', is_open=False, size='lg'),

        # Floating process indicator (when modal minimized)
        html.Div(
            id='floating-process-indicator',
            style={'display': 'none'}
        ),

        # Header
        html.Div([
            html.Div([
                html.H2(
                    '📈 Demand Forecasting - Analysis & Configuration',
                    style={'fontSize': '1.75rem', 'fontWeight': '700',
                          'color': '#1e293b', 'marginBottom': '0.5rem'}
                ),
                html.P(
                    f'Project: {active_project.get("name", "Unknown")}',
                    style={'fontSize': '0.875rem', 'color': '#64748b', 'marginBottom': '0'}
                )
            ], style={'flex': '1'}),

            html.Div([
                dbc.Button(
                    '⚙️ Configure Forecast',
                    id='open-configure-forecast-btn',
                    color='success',
                    size='lg'
                )
            ])
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '1.5rem'}),

        # View Toggle
        dbc.Card([
            dbc.CardBody([
                dbc.ButtonGroup([
                    dbc.Button(
                        [
                            html.Span('📊 ', style={'marginRight': '0.5rem'}),
                            'Consolidated View'
                        ],
                        id='consolidated-view-btn',
                        color='primary',
                        outline=False,
                        className='px-4'
                    ),
                    dbc.Button(
                        [
                            html.Span('🎯 ', style={'marginRight': '0.5rem'}),
                            'Sector-Specific View'
                        ],
                        id='sector-view-btn',
                        color='primary',
                        outline=True,
                        className='px-4'
                    )
                ], size='lg', className='w-100')
            ], className='p-2')
        ], className='mb-3'),

        # Consolidated View Content
        html.Div([
            # Top controls row
            dbc.Row([
                dbc.Col([
                    dbc.Label('Unit:', className='fw-bold me-2'),
                    dcc.Dropdown(
                        id='consolidated-unit-selector',
                        options=[
                            {'label': 'MWh', 'value': 'mwh'},
                            {'label': 'kWh', 'value': 'kwh'},
                            {'label': 'GWh', 'value': 'gwh'},
                            {'label': 'TWh', 'value': 'twh'}
                        ],
                        value='mwh',
                        clearable=False,
                        style={'width': '150px'}
                    )
                ], width='auto')
            ], className='mb-3'),

            # Tabs
            dbc.Tabs([
                dbc.Tab(
                    html.Div(id='consolidated-data-table-content', className='p-3'),
                    label='📋 Data Table',
                    tab_id='table'
                ),
                dbc.Tab(
                    html.Div(id='consolidated-area-chart-content', className='p-3'),
                    label='📊 Area Chart',
                    tab_id='area'
                ),
                dbc.Tab(
                    html.Div(id='consolidated-stacked-bar-content', className='p-3'),
                    label='📈 Stacked Bar Chart',
                    tab_id='stacked'
                ),
                dbc.Tab(
                    html.Div(id='consolidated-line-chart-content', className='p-3'),
                    label='📉 Line Chart',
                    tab_id='line'
                ),
            ], id='consolidated-tabs', active_tab='table', className='mb-3')
        ], id='consolidated-view-content', style={'display': 'block'}),

        # Sector-Specific View Content
        html.Div([
            # Sector selector and unit
            dbc.Row([
                dbc.Col([
                    dbc.Label('Sector:', className='fw-bold me-2'),
                    dcc.Dropdown(
                        id='sector-selector',
                        options=[],
                        value=None,
                        clearable=False,
                        style={'width': '300px'}
                    )
                ], width='auto'),
                dbc.Col([
                    dbc.Label('Unit:', className='fw-bold me-2'),
                    dcc.Dropdown(
                        id='sector-unit-selector',
                        options=[
                            {'label': 'MWh', 'value': 'mwh'},
                            {'label': 'kWh', 'value': 'kwh'},
                            {'label': 'GWh', 'value': 'gwh'},
                            {'label': 'TWh', 'value': 'twh'}
                        ],
                        value='mwh',
                        clearable=False,
                        style={'width': '150px'}
                    )
                ], width='auto')
            ], className='mb-3'),

            # Tabs
            dbc.Tabs([
                dbc.Tab(
                    html.Div(id='sector-data-table-content', className='p-3'),
                    label='📋 Data Table',
                    tab_id='table'
                ),
                dbc.Tab(
                    html.Div(id='sector-line-chart-content', className='p-3'),
                    label='📉 Line Chart',
                    tab_id='line'
                ),
                dbc.Tab(
                    html.Div(id='sector-correlation-content', className='p-3'),
                    label='🔗 Correlation',
                    tab_id='correlation'
                ),
            ], id='sector-tabs', active_tab='table', className='mb-3')
        ], id='sector-view-content', style={'display': 'none'}),

        # Loading overlay
        dcc.Loading(
            id='demand-projection-loading',
            type='circle',
            children=html.Div(id='loading-trigger')
        ),

        # Hidden stores for state management
        dcc.Store(id='demand-projection-state', storage_type='session', data=StateManager.create_demand_state()),
        dcc.Store(id='sectors-store', data=[]),
        dcc.Store(id='consolidated-data-store', data=None),
        dcc.Store(id='sector-data-store', data=None),
        dcc.Store(id='color-config-store', data={}),
        dcc.Store(id='forecast-process-state', data=None),

        # Interval for SSE polling (alternative to EventSource)
        dcc.Interval(id='forecast-progress-interval', interval=1000, disabled=True)

    ], fluid=True, style={'padding': '2rem'})


# ============================================================================
# CALLBACKS - VIEW TOGGLING
# ============================================================================

@callback(
    Output('consolidated-view-content', 'style'),
    Output('sector-view-content', 'style'),
    Output('consolidated-view-btn', 'outline'),
    Output('sector-view-btn', 'outline'),
    Output('demand-projection-state', 'data', allow_duplicate=True),
    Input('consolidated-view-btn', 'n_clicks'),
    Input('sector-view-btn', 'n_clicks'),
    State('demand-projection-state', 'data'),
    prevent_initial_call=True
)
def toggle_view_mode(consolidated_clicks, sector_clicks, current_state):
    """Toggle between Consolidated and Sector-specific views"""
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'consolidated-view-btn':
        # Show consolidated view
        updated_state = StateManager.merge_state(current_state, {'isConsolidated': True})
        return (
            {'display': 'block'},
            {'display': 'none'},
            False,  # Consolidated button solid
            True,   # Sector button outline
            updated_state
        )
    else:
        # Show sector view
        updated_state = StateManager.merge_state(current_state, {'isConsolidated': False})
        return (
            {'display': 'none'},
            {'display': 'block'},
            True,   # Consolidated button outline
            False,  # Sector button solid
            updated_state
        )


# ============================================================================
# CALLBACKS - BACKEND INTEGRATION
# ============================================================================

@callback(
    Output('sectors-store', 'data'),
    Output('sector-selector', 'options'),
    Output('color-config-store', 'data'),
    Input('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_project_sectors(active_project):
    """Load sectors and color configuration when project loads"""
    if not active_project or not active_project.get('path'):
        return [], [], {}

    try:
        # Fetch sectors
        sectors_response = api.get_sectors(active_project['path'])
        sectors = sectors_response.get('sectors', [])

        # Create dropdown options
        sector_options = [{'label': sector, 'value': idx}
                         for idx, sector in enumerate(sectors)]

        # Fetch color configuration
        try:
            color_response = api.get_color_settings(active_project['path'])
            colors = color_response.get('colors', {})
        except:
            colors = {}

        return sectors, sector_options, colors

    except Exception as e:
        print(f"Error loading sectors: {e}")
        return [], [], {}


@callback(
    Output('consolidated-data-store', 'data'),
    Input('sectors-store', 'data'),
    Input('demand-projection-state', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_consolidated_data(sectors, state, active_project):
    """Load consolidated data when in consolidated view"""
    if not active_project or not sectors:
        return None

    if not state or not state.get('isConsolidated'):
        return no_update

    try:
        response = api.get_consolidated_electricity(
            active_project['path'],
            sectors=sectors
        )
        return response.get('data', [])
    except Exception as e:
        print(f"Error loading consolidated data: {e}")
        return None


@callback(
    Output('sector-data-store', 'data'),
    Input('sector-selector', 'value'),
    State('sectors-store', 'data'),
    State('active-project-store', 'data'),
    State('demand-projection-state', 'data'),
    prevent_initial_call=True
)
def load_sector_data(sector_idx, sectors, active_project, state):
    """Load sector-specific data"""
    if sector_idx is None or not sectors or not active_project:
        return None

    if state and state.get('isConsolidated'):
        return no_update

    try:
        sector_name = sectors[sector_idx]
        response = api.extract_sector_data(
            active_project['path'],
            sector_name
        )
        return response.get('data', [])
    except Exception as e:
        print(f"Error loading sector data: {e}")
        return None


# ============================================================================
# CALLBACKS - DATA TABLE TAB (Consolidated)
# ============================================================================

@callback(
    Output('consolidated-data-table-content', 'children'),
    Input('consolidated-data-store', 'data'),
    Input('consolidated-unit-selector', 'value'),
    State('sectors-store', 'data')
)
def render_consolidated_data_table(data, unit, sectors):
    """Render consolidated data table"""
    if not data or not sectors:
        return dbc.Alert('No data available. Please load project data.', color='info')

    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)
        numeric_cols = [col for col in df.columns if col != 'Year']

        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col] * factor

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
            html.Div([
                html.H5(f'Consolidated Electricity Demand ({ConversionFactors.get_label(unit)})',
                       className='mb-3')
            ]),
            table,
            html.P(
                f'Showing data in {ConversionFactors.get_label(unit)}. Total sectors: {len(sectors)}',
                className='text-muted mt-3 mb-0',
                style={'fontSize': '0.875rem'}
            )
        ])

    except Exception as e:
        return dbc.Alert(f'Error rendering table: {str(e)}', color='danger')


# ============================================================================
# CALLBACKS - AREA CHART TAB (Consolidated)
# ============================================================================

@callback(
    Output('consolidated-area-chart-content', 'children'),
    Input('consolidated-data-store', 'data'),
    Input('consolidated-unit-selector', 'value'),
    State('sectors-store', 'data'),
    State('color-config-store', 'data')
)
def render_consolidated_area_chart(data, unit, sectors, colors):
    """Render consolidated area chart (stacked)"""
    if not data or not sectors:
        return dbc.Alert('No data available for chart.', color='info')

    try:
        df = pd.DataFrame(data)

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)

        # Create figure
        fig = go.Figure()

        # Add traces for each sector (stacked area)
        for sector in sectors:
            if sector in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Year'],
                    y=df[sector] * factor,
                    name=sector,
                    mode='lines',
                    stackgroup='one',
                    fillcolor=colors.get(sector, '#ccc'),
                    line=dict(width=0.5, color=colors.get(sector, '#ccc')),
                    hovertemplate=f'{sector}<br>Year: %{{x}}<br>Demand: %{{y:.2f}} {ConversionFactors.get_label(unit)}<extra></extra>'
                ))

        fig.update_layout(
            title=f'Consolidated Demand Forecast - Stacked Area ({ConversionFactors.get_label(unit)})',
            xaxis_title='Year',
            yaxis_title=f'Electricity Demand ({ConversionFactors.get_label(unit)})',
            hovermode='x unified',
            legend=dict(orientation='h', y=-0.2),
            height=500,
            template='plotly_white'
        )

        return dcc.Graph(figure=fig, config={'displayModeBar': True})

    except Exception as e:
        return dbc.Alert(f'Error rendering chart: {str(e)}', color='danger')


# Initialize sector selector with first sector
@callback(
    Output('sector-selector', 'value'),
    Input('sector-selector', 'options'),
    State('sector-selector', 'value'),
    prevent_initial_call=True
)
def initialize_sector_selector(options, current_value):
    """Set first sector as default"""
    if options and current_value is None:
        return 0
    return no_update


# TO BE CONTINUED - This is Part 1 of the implementation
# Next: Stacked Bar Chart, Line Chart, Sector views, Correlation, Configure Modal, SSE
