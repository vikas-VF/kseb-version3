"""
PyPSA View Results Page
========================
View and analyze PyPSA optimization results.

Features:
- Excel Results view with folder/sheet selection
- Network Analysis view with 7 tabs:
  1. Dispatch & Load
  2. Capacity
  3. Metrics
  4. Storage
  5. Emissions
  6. Costs
  7. Network
- Multi-period support (multi-year)
- Interactive charts and tables
- Info cards with statistics
"""

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import json
import pandas as pd

# Register page
dash.register_page(__name__, path='/pypsa/view-results', title='PyPSA View Results')

# Constants
PYPSA_COLORS = {
    'Solar': '#fbbf24',
    'Wind': '#3b82f6',
    'Hydro': '#06b6d4',
    'Battery': '#8b5cf6',
    'Gas': '#ef4444',
    'Coal': '#6b7280',
    'Nuclear': '#10b981',
    'Biomass': '#84cc16',
    'CCGT': '#f97316',
    'OCGT': '#dc2626',
    'Load': '#000000'
}

RESOLUTIONS = [
    {'value': '1H', 'label': '1 Hour'},
    {'value': '3H', 'label': '3 Hours'},
    {'value': '6H', 'label': '6 Hours'},
    {'value': '12H', 'label': '12 Hours'},
    {'value': '1D', 'label': '1 Day'},
    {'value': '1W', 'label': '1 Week'}
]

# Helper Functions
def format_number(value, decimals=2):
    """Format large numbers with K/M/B suffixes."""
    if value is None or pd.isna(value):
        return '-'
    try:
        value = float(value)
        if abs(value) >= 1e9:
            return f'{value/1e9:.{decimals}f} B'
        elif abs(value) >= 1e6:
            return f'{value/1e6:.{decimals}f} M'
        elif abs(value) >= 1e3:
            return f'{value/1e3:.{decimals}f} K'
        else:
            return f'{value:.{decimals}f}'
    except:
        return '-'


def format_percentage(value):
    """Format as percentage with 2 decimals."""
    if value is None or pd.isna(value):
        return '-'
    try:
        return f'{float(value):.2f}%'
    except:
        return '-'


# =====================================================================
# LAYOUT
# =====================================================================

def layout():
    """Main layout for PyPSA View Results page."""
    return html.Div([
        # State stores
        dcc.Store(id='pypsa-results-state', data={
            'viewMode': 'network',  # 'excel' or 'network'
            'selectedFolder': '',
            'selectedSheet': '',
            'chartType': 'Area',
            'selectedScenario': '',
            'selectedNetwork': '',
            'activeTab': 'dispatch',
            'resolution': '1H'
        }),

        # Main content
        html.Div([
            # Header
            html.Div([
                html.Div([
                    html.Div([
                        html.H1('View Results', className='text-2xl font-bold text-gray-900 mb-1'),
                        html.P(id='pypsa-results-project-info', className='text-sm text-gray-600')
                    ]),

                    # View Mode Toggle
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className='bi bi-file-earmark-spreadsheet me-2'), 'Excel Results'],
                                id='pypsa-excel-view-btn',
                                color='primary',
                                outline=True,
                                size='sm'
                            ),
                            dbc.Button(
                                [html.I(className='bi bi-diagram-3 me-2'), 'Network Analysis'],
                                id='pypsa-network-view-btn',
                                color='primary',
                                outline=True,
                                size='sm'
                            )
                        ])
                    ])
                ], className='d-flex justify-content-between align-items-center')
            ], className='bg-white border-bottom px-4 py-3'),

            # Content Area
            html.Div(id='pypsa-results-content', className='flex-grow-1', style={'overflowY': 'auto'})
        ], className='d-flex flex-column', style={'height': '100vh'})
    ])


# =====================================================================
# CALLBACKS - INITIALIZATION
# =====================================================================

@callback(
    Output('pypsa-results-project-info', 'children'),
    Input('active-project-store', 'data')
)
def update_project_info(active_project):
    """Update project info in header."""
    if not active_project:
        return 'No Project Loaded'
    return f"{active_project.get('name', 'Unknown')} - Analysis and Visualization"


# =====================================================================
# CALLBACKS - VIEW MODE
# =====================================================================

@callback(
    [
        Output('pypsa-results-state', 'data', allow_duplicate=True),
        Output('pypsa-excel-view-btn', 'outline'),
        Output('pypsa-network-view-btn', 'outline')
    ],
    [
        Input('pypsa-excel-view-btn', 'n_clicks'),
        Input('pypsa-network-view-btn', 'n_clicks')
    ],
    State('pypsa-results-state', 'data'),
    prevent_initial_call=True
)
def toggle_view_mode(excel_clicks, network_clicks, results_state):
    """Toggle between Excel and Network view modes."""
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'pypsa-excel-view-btn':
        results_state['viewMode'] = 'excel'
        return results_state, False, True  # Excel active, Network outline
    elif button_id == 'pypsa-network-view-btn':
        results_state['viewMode'] = 'network'
        return results_state, True, False  # Excel outline, Network active

    raise PreventUpdate


# =====================================================================
# CALLBACKS - CONTENT RENDERING
# =====================================================================

@callback(
    Output('pypsa-results-content', 'children'),
    Input('pypsa-results-state', 'data'),
    State('active-project-store', 'data')
)
def render_content(results_state, active_project):
    """Render content based on view mode."""
    if not active_project:
        return html.Div([
            html.Div([
                html.I(className='bi bi-exclamation-circle', style={'fontSize': '4rem', 'color': '#9ca3af'}),
                html.H3('No Project Loaded', className='mt-3 text-lg font-semibold text-gray-700'),
                html.P('Please load or create a project to view results.', className='text-sm text-gray-500')
            ], className='text-center py-5')
        ], className='d-flex align-items-center justify-content-center', style={'height': '80vh'})

    view_mode = results_state.get('viewMode', 'network')

    if view_mode == 'excel':
        return render_excel_view(results_state, active_project)
    else:
        return render_network_view(results_state, active_project)


def render_excel_view(results_state, active_project):
    """Render Excel Results view."""
    return html.Div([
        html.Div([
            # Folder Selection
            html.Div([
                dbc.Label('Select Optimization Folder', className='font-semibold mb-2'),
                html.Div(id='pypsa-folder-selector-container')
            ], className='bg-white rounded shadow-sm border p-4 mb-3'),

            # Sheet Selection
            html.Div(id='pypsa-sheet-selection-container'),

            # Chart Type Selection
            html.Div(id='pypsa-chart-type-container'),

            # Chart Display
            html.Div(id='pypsa-excel-chart-container')
        ], className='container-fluid py-4', style={'maxWidth': '1400px'})
    ])


def render_network_view(results_state, active_project):
    """Render Network Analysis view."""
    return html.Div([
        # Network Selector
        html.Div([
            html.Div(id='pypsa-network-selector-container')
        ], className='bg-white border-bottom px-4 py-3'),

        # Tab Content
        html.Div(id='pypsa-network-tab-content', className='flex-grow-1')
    ], className='d-flex flex-column h-100')


# =====================================================================
# EXCEL VIEW - FOLDER/SHEET SELECTION
# =====================================================================

@callback(
    Output('pypsa-folder-selector-container', 'children'),
    Input('pypsa-results-state', 'data'),
    State('active-project-store', 'data')
)
def render_folder_selector(results_state, active_project):
    """Render folder selector."""
    if results_state.get('viewMode') != 'excel':
        return html.Div()

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_optimization_folders(active_project['path'])
        folders = response.get('folders', [])

        return dbc.Select(
            id='pypsa-folder-select',
            options=[{'label': folder, 'value': folder} for folder in folders],
            value=folders[0] if folders else None,
            placeholder='-- Select Folder --'
        )
    except Exception as e:
        return dbc.Alert(f'Error loading folders: {str(e)}', color='danger')


@callback(
    [
        Output('pypsa-results-state', 'data', allow_duplicate=True),
        Output('pypsa-sheet-selection-container', 'children')
    ],
    Input('pypsa-folder-select', 'value'),
    [
        State('pypsa-results-state', 'data'),
        State('active-project-store', 'data')
    ],
    prevent_initial_call=True
)
def load_sheets(folder, results_state, active_project):
    """Load sheets for selected folder."""
    if not folder:
        return results_state, html.Div()

    results_state['selectedFolder'] = folder

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_optimization_sheets(active_project['path'], folder)
        sheets = response.get('sheets', [])

        sheet_selector = html.Div([
            dbc.Label('Select Sheet', className='font-semibold mb-2'),
            dbc.Select(
                id='pypsa-sheet-select',
                options=[{'label': sheet, 'value': sheet} for sheet in sheets],
                value=sheets[0] if sheets else None,
                placeholder='-- Select Sheet --'
            )
        ], className='bg-white rounded shadow-sm border p-4 mb-3')

        return results_state, sheet_selector
    except Exception as e:
        return results_state, dbc.Alert(f'Error loading sheets: {str(e)}', color='danger')


@callback(
    [
        Output('pypsa-results-state', 'data', allow_duplicate=True),
        Output('pypsa-chart-type-container', 'children')
    ],
    Input('pypsa-sheet-select', 'value'),
    State('pypsa-results-state', 'data'),
    prevent_initial_call=True
)
def show_chart_type_selector(sheet, results_state):
    """Show chart type selector when sheet is selected."""
    if not sheet:
        return results_state, html.Div()

    results_state['selectedSheet'] = sheet

    chart_type_selector = html.Div([
        dbc.Label('Chart Type', className='font-semibold mb-2'),
        dbc.ButtonGroup([
            dbc.Button(
                [html.I(className='bi bi-graph-up me-2'), 'Area Chart'],
                id={'type': 'pypsa-chart-type-btn', 'index': 'Area'},
                color='primary',
                size='sm'
            ),
            dbc.Button(
                [html.I(className='bi bi-bar-chart me-2'), 'Stacked Bar'],
                id={'type': 'pypsa-chart-type-btn', 'index': 'StackedBar'},
                color='primary',
                outline=True,
                size='sm'
            )
        ])
    ], className='bg-white rounded shadow-sm border p-4 mb-3')

    return results_state, chart_type_selector


@callback(
    Output('pypsa-results-state', 'data', allow_duplicate=True),
    Input({'type': 'pypsa-chart-type-btn', 'index': ALL}, 'n_clicks'),
    State('pypsa-results-state', 'data'),
    prevent_initial_call=True
)
def update_chart_type(n_clicks, results_state):
    """Update chart type."""
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    chart_type = json.loads(button_id)['index']
    results_state['chartType'] = chart_type

    return results_state


@callback(
    Output('pypsa-excel-chart-container', 'children'),
    Input('pypsa-results-state', 'data'),
    State('active-project-store', 'data')
)
def render_excel_chart(results_state, active_project):
    """Render Excel chart."""
    if results_state.get('viewMode') != 'excel':
        return html.Div()

    folder = results_state.get('selectedFolder')
    sheet = results_state.get('selectedSheet')
    chart_type = results_state.get('chartType', 'Area')

    if not folder or not sheet:
        return html.Div()

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_optimization_sheet_data(active_project['path'], folder, sheet)
        data = response.get('data', [])

        if not data:
            return dbc.Alert('No data available', color='info')

        df = pd.DataFrame(data)

        # Extract data keys (exclude Year column)
        data_keys = [col for col in df.columns if col.lower() != 'year']

        # Create chart
        fig = go.Figure()

        if chart_type == 'Area':
            for key in data_keys:
                fig.add_trace(go.Scatter(
                    x=df['Year'] if 'Year' in df.columns else df.index,
                    y=df[key],
                    mode='lines',
                    stackgroup='one',
                    name=key,
                    line=dict(color=PYPSA_COLORS.get(key, None))
                ))
        else:  # StackedBar
            for key in data_keys:
                fig.add_trace(go.Bar(
                    x=df['Year'] if 'Year' in df.columns else df.index,
                    y=df[key],
                    name=key,
                    marker=dict(color=PYPSA_COLORS.get(key, None))
                ))
            fig.update_layout(barmode='stack')

        fig.update_layout(
            height=600,
            margin=dict(l=60, r=30, t=30, b=60),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return html.Div([
            dcc.Graph(figure=fig, config={'displayModeBar': True})
        ], className='bg-white rounded shadow-sm border p-4')

    except Exception as e:
        return dbc.Alert(f'Error loading chart: {str(e)}', color='danger')


# =====================================================================
# NETWORK VIEW - NETWORK SELECTOR
# =====================================================================

@callback(
    Output('pypsa-network-selector-container', 'children'),
    Input('pypsa-results-state', 'data'),
    State('active-project-store', 'data')
)
def render_network_selector(results_state, active_project):
    """Render network selector."""
    if results_state.get('viewMode') != 'network':
        return html.Div()

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_scenarios(active_project['path'])
        scenarios = response.get('scenarios', [])

        return dbc.Row([
            dbc.Col([
                dbc.Label('Scenario', className='font-semibold mb-2'),
                dbc.Select(
                    id='pypsa-scenario-select',
                    options=[{'label': s, 'value': s} for s in scenarios],
                    value=scenarios[0] if scenarios else None,
                    placeholder='-- Select Scenario --'
                )
            ], md=6),
            dbc.Col([
                dbc.Label('Network File', className='font-semibold mb-2'),
                html.Div(id='pypsa-network-select-container')
            ], md=6)
        ], className='g-3')

    except Exception as e:
        return dbc.Alert(f'Error loading scenarios: {str(e)}', color='danger')


@callback(
    [
        Output('pypsa-results-state', 'data', allow_duplicate=True),
        Output('pypsa-network-select-container', 'children')
    ],
    Input('pypsa-scenario-select', 'value'),
    [
        State('pypsa-results-state', 'data'),
        State('active-project-store', 'data')
    ],
    prevent_initial_call=True
)
def load_networks(scenario, results_state, active_project):
    """Load networks for selected scenario."""
    if not scenario:
        return results_state, html.Div()

    results_state['selectedScenario'] = scenario

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_networks(active_project['path'], scenario)
        networks = response.get('networks', [])

        network_selector = dbc.Select(
            id='pypsa-network-select',
            options=[{'label': n, 'value': n} for n in networks],
            value=networks[0] if networks else None,
            placeholder='-- Select Network --'
        )

        return results_state, network_selector

    except Exception as e:
        return results_state, dbc.Alert(f'Error loading networks: {str(e)}', color='danger')


@callback(
    Output('pypsa-results-state', 'data', allow_duplicate=True),
    Input('pypsa-network-select', 'value'),
    State('pypsa-results-state', 'data'),
    prevent_initial_call=True
)
def update_selected_network(network, results_state):
    """Update selected network."""
    if not network:
        raise PreventUpdate

    results_state['selectedNetwork'] = network
    return results_state


# =====================================================================
# NETWORK VIEW - TAB NAVIGATION
# =====================================================================

@callback(
    Output('pypsa-network-tab-content', 'children'),
    Input('pypsa-results-state', 'data')
)
def render_network_tabs(results_state):
    """Render network tabs."""
    if results_state.get('viewMode') != 'network':
        return html.Div()

    selected_scenario = results_state.get('selectedScenario')
    selected_network = results_state.get('selectedNetwork')

    if not selected_scenario or not selected_network:
        return html.Div([
            html.Div([
                html.I(className='bi bi-diagram-3', style={'fontSize': '4rem', 'color': '#9ca3af'}),
                html.H3('Select a Network', className='mt-3 text-lg font-semibold text-gray-700'),
                html.P('Choose a scenario and network file(s) to begin analysis', className='text-sm text-gray-500')
            ], className='text-center py-5')
        ], className='d-flex align-items-center justify-content-center', style={'height': '70vh'})

    active_tab = results_state.get('activeTab', 'dispatch')

    # Tab navigation
    tabs = dbc.Tabs([
        dbc.Tab(label='Dispatch & Load', tab_id='dispatch', label_style={'cursor': 'pointer'}),
        dbc.Tab(label='Capacity', tab_id='capacity', label_style={'cursor': 'pointer'}),
        dbc.Tab(label='Metrics', tab_id='metrics', label_style={'cursor': 'pointer'}),
        dbc.Tab(label='Storage', tab_id='storage', label_style={'cursor': 'pointer'}),
        dbc.Tab(label='Emissions', tab_id='emissions', label_style={'cursor': 'pointer'}),
        dbc.Tab(label='Costs', tab_id='costs', label_style={'cursor': 'pointer'}),
        dbc.Tab(label='Network', tab_id='network', label_style={'cursor': 'pointer'})
    ], id='pypsa-tabs', active_tab=active_tab, className='mb-3')

    return html.Div([
        html.Div(tabs, className='px-4 pt-3'),
        html.Div(id='pypsa-tab-content-area', className='px-4 pb-4')
    ])


@callback(
    Output('pypsa-results-state', 'data', allow_duplicate=True),
    Input('pypsa-tabs', 'active_tab'),
    State('pypsa-results-state', 'data'),
    prevent_initial_call=True
)
def update_active_tab(active_tab, results_state):
    """Update active tab."""
    if not active_tab:
        raise PreventUpdate

    results_state['activeTab'] = active_tab
    return results_state


@callback(
    Output('pypsa-tab-content-area', 'children'),
    Input('pypsa-results-state', 'data'),
    State('active-project-store', 'data')
)
def render_tab_content(results_state, active_project):
    """Render content for active tab."""
    active_tab = results_state.get('activeTab', 'dispatch')
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    if not scenario or not network:
        return html.Div()

    if active_tab == 'dispatch':
        return render_dispatch_tab(results_state, active_project)
    elif active_tab == 'capacity':
        return render_capacity_tab(results_state, active_project)
    elif active_tab == 'metrics':
        return render_metrics_tab(results_state, active_project)
    elif active_tab == 'storage':
        return render_storage_tab(results_state, active_project)
    elif active_tab == 'emissions':
        return render_emissions_tab(results_state, active_project)
    elif active_tab == 'costs':
        return render_costs_tab(results_state, active_project)
    elif active_tab == 'network':
        return render_network_tab(results_state, active_project)

    return html.Div()


# =====================================================================
# TAB 1: DISPATCH & LOAD
# =====================================================================

def render_dispatch_tab(results_state, active_project):
    """Render Dispatch & Load tab."""
    return html.Div([
        # Resolution selector
        html.Div([
            dbc.Label('Resolution', className='font-semibold mb-2'),
            dbc.Select(
                id='pypsa-resolution-select',
                options=[{'label': r['label'], 'value': r['value']} for r in RESOLUTIONS],
                value='1H'
            )
        ], className='mb-3'),

        # Chart container
        html.Div(id='pypsa-dispatch-chart-container')
    ])


@callback(
    Output('pypsa-results-state', 'data', allow_duplicate=True),
    Input('pypsa-resolution-select', 'value'),
    State('pypsa-results-state', 'data'),
    prevent_initial_call=True
)
def update_resolution(resolution, results_state):
    """Update resolution."""
    results_state['resolution'] = resolution
    return results_state


@callback(
    Output('pypsa-dispatch-chart-container', 'children'),
    Input('pypsa-results-state', 'data'),
    State('active-project-store', 'data')
)
def render_dispatch_chart(results_state, active_project):
    """Render dispatch chart."""
    if results_state.get('activeTab') != 'dispatch':
        return html.Div()

    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')
    resolution = results_state.get('resolution', '1H')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_dispatch(active_project['path'], scenario, network, resolution)
        data = response.get('data', [])

        if not data:
            return dbc.Alert('No dispatch data available', color='info')

        df = pd.DataFrame(data)

        # Extract carrier columns (exclude timestamp and Load)
        carriers = [col for col in df.columns if col not in ['timestamp', 'Load']]

        # Create stacked area chart
        fig = go.Figure()

        for carrier in carriers:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[carrier],
                mode='lines',
                stackgroup='one',
                name=carrier,
                line=dict(color=PYPSA_COLORS.get(carrier, None)),
                fillcolor=PYPSA_COLORS.get(carrier, None)
            ))

        # Add Load line if present
        if 'Load' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['Load'],
                mode='lines',
                name='Load',
                line=dict(color='#000000', width=3, dash='dash')
            ))

        fig.update_layout(
            title='Generation Dispatch',
            xaxis_title='Time',
            yaxis_title='Power (MW)',
            height=600,
            margin=dict(l=60, r=30, t=50, b=60),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

        return html.Div([
            dcc.Graph(figure=fig, config={'displayModeBar': True})
        ], className='bg-white rounded shadow-sm border p-4')

    except Exception as e:
        return dbc.Alert(f'Error loading dispatch data: {str(e)}', color='danger')


# =====================================================================
# TAB 2: CAPACITY
# =====================================================================

def render_capacity_tab(results_state, active_project):
    """Render Capacity tab."""
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_capacity(active_project['path'], scenario, network)
        data = response.get('data', {})

        generators = data.get('generators', [])
        totals = data.get('totals', {})

        # Info cards
        cards = dbc.Row([
            dbc.Col([
                info_card(
                    'Total Generation',
                    format_number(totals.get('generation_capacity_mw', 0)) + ' MW',
                    'Installed capacity',
                    'bi-lightning-charge-fill',
                    'primary'
                )
            ], md=4),
            dbc.Col([
                info_card(
                    'Storage Power',
                    format_number(totals.get('storage_power_capacity_mw', 0)) + ' MW',
                    'Storage capacity',
                    'bi-battery-charging',
                    'success'
                )
            ], md=4),
            dbc.Col([
                info_card(
                    'Storage Energy',
                    format_number(totals.get('storage_energy_capacity_mwh', 0)) + ' MWh',
                    'Energy storage',
                    'bi-battery-full',
                    'info'
                )
            ], md=4)
        ], className='g-3 mb-4')

        # Chart
        df = pd.DataFrame(generators)

        fig = go.Figure([go.Bar(
            x=df['carrier'],
            y=df['value'],
            marker=dict(color=[PYPSA_COLORS.get(c, '#3b82f6') for c in df['carrier']])
        )])

        fig.update_layout(
            title='Generator Capacities',
            xaxis_title='Carrier',
            yaxis_title='Capacity (MW)',
            height=500,
            margin=dict(l=60, r=30, t=50, b=100),
            xaxis=dict(tickangle=-45)
        )

        chart = html.Div([
            dcc.Graph(figure=fig, config={'displayModeBar': True})
        ], className='bg-white rounded shadow-sm border p-4')

        return html.Div([cards, chart])

    except Exception as e:
        return dbc.Alert(f'Error loading capacity data: {str(e)}', color='danger')


# =====================================================================
# TAB 3: METRICS
# =====================================================================

def render_metrics_tab(results_state, active_project):
    """Render Metrics tab."""
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_renewable_share(active_project['path'], scenario, network)
        data = response.get('data', {})

        summary = data.get('summary', {})
        breakdown = data.get('breakdown', [])

        # Info cards
        cards = dbc.Row([
            dbc.Col([
                info_card(
                    'Renewable Share',
                    format_percentage(summary.get('renewable_share_percent', 0)),
                    'Of total energy',
                    'bi-graph-up-arrow',
                    'success'
                )
            ], md=3),
            dbc.Col([
                info_card(
                    'Renewable Energy',
                    format_number(summary.get('renewable_energy_mwh', 0)) + ' MWh',
                    'Total renewable generation',
                    'bi-lightning-charge',
                    'primary'
                )
            ], md=3),
            dbc.Col([
                info_card(
                    'Total Energy',
                    format_number(summary.get('total_energy_mwh', 0)) + ' MWh',
                    'System total',
                    'bi-activity',
                    'info'
                )
            ], md=3),
            dbc.Col([
                info_card(
                    'Total Curtailment',
                    format_number(summary.get('total_curtailed_mwh', 0)) + ' MWh',
                    format_percentage(summary.get('curtailment_rate_percent', 0)) + ' rate',
                    'bi-exclamation-triangle',
                    'warning'
                )
            ], md=3)
        ], className='g-3 mb-4')

        # Pie charts
        renewable_data = [
            {'name': 'Renewable', 'value': summary.get('renewable_share_percent', 0), 'color': '#10b981'},
            {'name': 'Non-Renewable', 'value': 100 - summary.get('renewable_share_percent', 0), 'color': '#ef4444'}
        ]

        fig1 = go.Figure([go.Pie(
            labels=[d['name'] for d in renewable_data],
            values=[d['value'] for d in renewable_data],
            marker=dict(colors=[d['color'] for d in renewable_data])
        )])
        fig1.update_layout(title='Renewable vs Non-Renewable', height=300)

        df_breakdown = pd.DataFrame(breakdown)
        fig2 = go.Figure([go.Pie(
            labels=df_breakdown['carrier'],
            values=df_breakdown['renewable_energy_mwh'],
            marker=dict(colors=[PYPSA_COLORS.get(c, '#3b82f6') for c in df_breakdown['carrier']])
        )])
        fig2.update_layout(title='Renewable Breakdown by Carrier', height=300)

        charts = dbc.Row([
            dbc.Col([
                html.Div([
                    dcc.Graph(figure=fig1, config={'displayModeBar': True})
                ], className='bg-white rounded shadow-sm border p-4')
            ], md=6),
            dbc.Col([
                html.Div([
                    dcc.Graph(figure=fig2, config={'displayModeBar': True})
                ], className='bg-white rounded shadow-sm border p-4')
            ], md=6)
        ], className='g-3 mb-4')

        return html.Div([cards, charts])

    except Exception as e:
        return dbc.Alert(f'Error loading metrics data: {str(e)}', color='danger')


# =====================================================================
# TAB 4: STORAGE
# =====================================================================

def render_storage_tab(results_state, active_project):
    """Render Storage tab."""
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_storage(active_project['path'], scenario, network)
        data = response.get('data', {})

        storage_units = data.get('storage_units', [])
        stores = data.get('stores', [])

        # Info cards
        cards = dbc.Row([
            dbc.Col([
                info_card(
                    'Storage Units',
                    str(len(storage_units)),
                    'Total count',
                    'bi-battery-charging',
                    'primary'
                )
            ], md=6),
            dbc.Col([
                info_card(
                    'Stores',
                    str(len(stores)),
                    'Total count',
                    'bi-battery-full',
                    'success'
                )
            ], md=6)
        ], className='g-3 mb-4')

        # Storage units chart
        if storage_units:
            df_units = pd.DataFrame(storage_units)
            fig1 = go.Figure([go.Bar(
                x=df_units['carrier'],
                y=df_units['power_capacity_mw'],
                name='Power (MW)',
                marker=dict(color=[PYPSA_COLORS.get(c, '#8b5cf6') for c in df_units['carrier']])
            )])
            fig1.update_layout(
                title='Storage Units - Power Capacity',
                xaxis_title='Carrier',
                yaxis_title='Power (MW)',
                height=400,
                margin=dict(l=60, r=30, t=50, b=100),
                xaxis=dict(tickangle=-45)
            )

            chart1 = html.Div([
                dcc.Graph(figure=fig1, config={'displayModeBar': True})
            ], className='bg-white rounded shadow-sm border p-4 mb-4')
        else:
            chart1 = dbc.Alert('No storage units data available', color='info', className='mb-4')

        # Stores chart
        if stores:
            df_stores = pd.DataFrame(stores)
            fig2 = go.Figure([go.Bar(
                x=df_stores['carrier'],
                y=df_stores['energy_capacity_mwh'],
                marker=dict(color=[PYPSA_COLORS.get(c, '#06b6d4') for c in df_stores['carrier']])
            )])
            fig2.update_layout(
                title='Stores - Energy Capacity',
                xaxis_title='Carrier',
                yaxis_title='Energy (MWh)',
                height=400,
                margin=dict(l=60, r=30, t=50, b=100),
                xaxis=dict(tickangle=-45)
            )

            chart2 = html.Div([
                dcc.Graph(figure=fig2, config={'displayModeBar': True})
            ], className='bg-white rounded shadow-sm border p-4')
        else:
            chart2 = dbc.Alert('No stores data available', color='info')

        return html.Div([cards, chart1, chart2])

    except Exception as e:
        return dbc.Alert(f'Error loading storage data: {str(e)}', color='danger')


# =====================================================================
# TAB 5: EMISSIONS
# =====================================================================

def render_emissions_tab(results_state, active_project):
    """Render Emissions tab."""
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_emissions(active_project['path'], scenario, network)
        data = response.get('data', {})

        summary = data.get('summary', {})
        breakdown = data.get('breakdown', [])

        # Info cards
        cards = dbc.Row([
            dbc.Col([
                info_card(
                    'Total Emissions',
                    format_number(summary.get('total_emissions_tco2', 0)) + ' tCO₂',
                    'System total',
                    'bi-cloud',
                    'danger'
                )
            ], md=6),
            dbc.Col([
                info_card(
                    'Emissions Intensity',
                    format_number(summary.get('emissions_intensity_gco2_kwh', 0)) + ' gCO₂/kWh',
                    'Per unit energy',
                    'bi-speedometer',
                    'warning'
                )
            ], md=6)
        ], className='g-3 mb-4')

        # Chart
        if breakdown:
            df = pd.DataFrame(breakdown)
            fig = go.Figure([go.Bar(
                x=df['carrier'],
                y=df['emissions_tco2'],
                marker=dict(color=[PYPSA_COLORS.get(c, '#ef4444') for c in df['carrier']])
            )])
            fig.update_layout(
                title='Emissions by Carrier',
                xaxis_title='Carrier',
                yaxis_title='Emissions (tCO₂)',
                height=500,
                margin=dict(l=60, r=30, t=50, b=100),
                xaxis=dict(tickangle=-45)
            )

            chart = html.Div([
                dcc.Graph(figure=fig, config={'displayModeBar': True})
            ], className='bg-white rounded shadow-sm border p-4')
        else:
            chart = dbc.Alert('No emissions data available', color='info')

        return html.Div([cards, chart])

    except Exception as e:
        return dbc.Alert(f'Error loading emissions data: {str(e)}', color='danger')


# =====================================================================
# TAB 6: COSTS
# =====================================================================

def render_costs_tab(results_state, active_project):
    """Render Costs tab."""
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_system_costs(active_project['path'], scenario, network)
        data = response.get('data', {})

        summary = data.get('summary', {})
        breakdown = data.get('breakdown', [])

        # Info card
        cards = dbc.Row([
            dbc.Col([
                info_card(
                    'Total System Cost',
                    format_number(summary.get('total_system_cost', 0)) + ' €',
                    'Optimization result',
                    'bi-currency-dollar',
                    'success'
                )
            ], md=12)
        ], className='g-3 mb-4')

        # Chart
        if breakdown:
            df = pd.DataFrame(breakdown)
            fig = go.Figure([go.Bar(
                x=df['carrier'],
                y=df['cost'],
                marker=dict(color=[PYPSA_COLORS.get(c, '#10b981') for c in df['carrier']])
            )])
            fig.update_layout(
                title='System Costs by Carrier',
                xaxis_title='Carrier',
                yaxis_title='Cost (€)',
                height=500,
                margin=dict(l=60, r=30, t=50, b=100),
                xaxis=dict(tickangle=-45)
            )

            chart = html.Div([
                dcc.Graph(figure=fig, config={'displayModeBar': True})
            ], className='bg-white rounded shadow-sm border p-4')
        else:
            chart = dbc.Alert('No cost data available', color='info')

        return html.Div([cards, chart])

    except Exception as e:
        return dbc.Alert(f'Error loading costs data: {str(e)}', color='danger')


# =====================================================================
# TAB 7: NETWORK
# =====================================================================

def render_network_tab(results_state, active_project):
    """Render Network tab."""
    scenario = results_state.get('selectedScenario')
    network = results_state.get('selectedNetwork')

    from dash.services.api_client import get_api_client
    api = get_api_client()

    try:
        response = api.get_pypsa_lines(active_project['path'], scenario, network)
        data = response.get('data', {})

        lines = data.get('lines', [])

        if not lines:
            return dbc.Alert('No network lines data available', color='info')

        df = pd.DataFrame(lines)

        # Table
        table = dbc.Table.from_dataframe(
            df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className='mb-0'
        )

        return html.Div([
            html.H5('Transmission Lines', className='mb-3'),
            html.Div([table], className='bg-white rounded shadow-sm border p-4')
        ])

    except Exception as e:
        return dbc.Alert(f'Error loading network data: {str(e)}', color='danger')


# =====================================================================
# HELPER COMPONENTS
# =====================================================================

def info_card(title, value, subtitle, icon, color):
    """Create an info card component."""
    color_classes = {
        'primary': {'bg': 'bg-primary-subtle', 'border': 'border-primary', 'text': 'text-primary'},
        'success': {'bg': 'bg-success-subtle', 'border': 'border-success', 'text': 'text-success'},
        'info': {'bg': 'bg-info-subtle', 'border': 'border-info', 'text': 'text-info'},
        'warning': {'bg': 'bg-warning-subtle', 'border': 'border-warning', 'text': 'text-warning'},
        'danger': {'bg': 'bg-danger-subtle', 'border': 'border-danger', 'text': 'text-danger'}
    }

    classes = color_classes.get(color, color_classes['primary'])

    return html.Div([
        html.Div([
            html.Div([
                html.H6(title, className='text-uppercase text-muted mb-2', style={'fontSize': '0.75rem'}),
                html.Div(value, className='h3 font-bold mb-1'),
                html.P(subtitle, className='text-sm text-muted mb-0')
            ]),
            html.I(className=f'bi {icon} {classes["text"]}', style={'fontSize': '2rem'})
        ], className='d-flex justify-content-between align-items-start')
    ], className=f'{classes["bg"]} {classes["border"]} border-2 rounded p-3 shadow-sm')
