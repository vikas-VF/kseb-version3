"""
Demand Projection Page - Part 2 IMPLEMENTATION
Continuing from Part 1 - Additional callbacks and features

Features in this file:
- Stacked Bar Chart (Consolidated)
- Line Chart (Consolidated)
- Sector-specific view tabs (Data Table, Line Chart, Correlation)
- Configure Forecast Modal
- Real-time SSE Progress Tracking
"""

from dash import html, dcc, callback, Input, Output, State, ALL, MATCH, callback_context, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api_client import api
from utils.state_manager import StateManager, ConversionFactors


# ============================================================================
# CALLBACKS - STACKED BAR CHART TAB (Consolidated)
# ============================================================================

@callback(
    Output('consolidated-stacked-bar-content', 'children'),
    Input('consolidated-data-store', 'data'),
    Input('consolidated-unit-selector', 'value'),
    State('sectors-store', 'data'),
    State('color-config-store', 'data')
)
def render_consolidated_stacked_bar(data, unit, sectors, colors):
    """Render consolidated stacked bar chart"""
    if not data or not sectors:
        return dbc.Alert('No data available for chart.', color='info')

    try:
        df = pd.DataFrame(data)

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)

        # Create figure
        fig = go.Figure()

        # Add bars for each sector (stacked)
        for sector in sectors:
            if sector in df.columns:
                fig.add_trace(go.Bar(
                    x=df['Year'],
                    y=df[sector] * factor,
                    name=sector,
                    marker_color=colors.get(sector, '#ccc'),
                    hovertemplate=f'{sector}<br>Year: %{{x}}<br>Demand: %{{y:.2f}} {ConversionFactors.get_label(unit)}<extra></extra>'
                ))

        fig.update_layout(
            title=f'Consolidated Demand Forecast - Stacked Bar ({ConversionFactors.get_label(unit)})',
            xaxis_title='Year',
            yaxis_title=f'Electricity Demand ({ConversionFactors.get_label(unit)})',
            barmode='stack',
            hovermode='x unified',
            legend=dict(orientation='h', y=-0.2),
            height=500,
            template='plotly_white'
        )

        return dcc.Graph(figure=fig, config={'displayModeBar': True})

    except Exception as e:
        return dbc.Alert(f'Error rendering chart: {str(e)}', color='danger')


# ============================================================================
# CALLBACKS - LINE CHART TAB (Consolidated)
# ============================================================================

@callback(
    Output('consolidated-line-chart-content', 'children'),
    Input('consolidated-data-store', 'data'),
    Input('consolidated-unit-selector', 'value'),
    State('sectors-store', 'data'),
    State('color-config-store', 'data')
)
def render_consolidated_line_chart(data, unit, sectors, colors):
    """Render consolidated line chart (all sectors as separate lines)"""
    if not data or not sectors:
        return dbc.Alert('No data available for chart.', color='info')

    try:
        df = pd.DataFrame(data)

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)

        # Create figure
        fig = go.Figure()

        # Add line for each sector
        for sector in sectors:
            if sector in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['Year'],
                    y=df[sector] * factor,
                    name=sector,
                    mode='lines+markers',
                    line=dict(width=2, color=colors.get(sector, '#ccc')),
                    marker=dict(size=6),
                    hovertemplate=f'{sector}<br>Year: %{{x}}<br>Demand: %{{y:.2f}} {ConversionFactors.get_label(unit)}<extra></extra>'
                ))

        fig.update_layout(
            title=f'Consolidated Demand Forecast - Line Chart ({ConversionFactors.get_label(unit)})',
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


# ============================================================================
# CALLBACKS - SECTOR DATA TABLE TAB
# ============================================================================

@callback(
    Output('sector-data-table-content', 'children'),
    Input('sector-data-store', 'data'),
    Input('sector-unit-selector', 'value'),
    State('sector-selector', 'value'),
    State('sectors-store', 'data')
)
def render_sector_data_table(data, unit, sector_idx, sectors):
    """Render sector-specific data table"""
    if not data or sector_idx is None or not sectors:
        return dbc.Alert('No data available. Please select a sector.', color='info')

    try:
        sector_name = sectors[sector_idx]

        # Convert data to DataFrame
        df = pd.DataFrame(data)

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)
        numeric_cols = [col for col in df.columns if col not in ['Year', 'year']]

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
                html.H5(f'{sector_name} - Demand Data ({ConversionFactors.get_label(unit)})',
                       className='mb-3')
            ]),
            table,
            html.P(
                f'Showing data in {ConversionFactors.get_label(unit)}',
                className='text-muted mt-3 mb-0',
                style={'fontSize': '0.875rem'}
            )
        ])

    except Exception as e:
        return dbc.Alert(f'Error rendering table: {str(e)}', color='danger')


# ============================================================================
# CALLBACKS - SECTOR LINE CHART TAB
# ============================================================================

@callback(
    Output('sector-line-chart-content', 'children'),
    Input('sector-data-store', 'data'),
    Input('sector-unit-selector', 'value'),
    State('sector-selector', 'value'),
    State('sectors-store', 'data'),
    State('color-config-store', 'data')
)
def render_sector_line_chart(data, unit, sector_idx, sectors, colors):
    """Render sector-specific line chart (multiple models if available)"""
    if not data or sector_idx is None or not sectors:
        return dbc.Alert('No data available for chart.', color='info')

    try:
        sector_name = sectors[sector_idx]
        df = pd.DataFrame(data)

        # Apply unit conversion
        factor = ConversionFactors.FACTORS.get(unit, 1)

        # Create figure
        fig = go.Figure()

        # Models/columns to plot (excluding Year)
        model_columns = [col for col in df.columns if col not in ['Year', 'year']]

        # Define colors for different models
        model_colors = {
            'SLR': '#3b82f6',
            'MLR': '#10b981',
            'WAM': '#f59e0b',
            'Time Series': '#8b5cf6',
            'Ensemble': '#ef4444'
        }

        # Add line for each model
        for col in model_columns:
            fig.add_trace(go.Scatter(
                x=df['Year'] if 'Year' in df.columns else df['year'],
                y=df[col] * factor,
                name=col,
                mode='lines+markers',
                line=dict(width=2, color=model_colors.get(col, colors.get(sector_name, '#ccc'))),
                marker=dict(size=6),
                hovertemplate=f'{col}<br>Year: %{{x}}<br>Demand: %{{y:.2f}} {ConversionFactors.get_label(unit)}<extra></extra>'
            ))

        fig.update_layout(
            title=f'{sector_name} - Model Comparison ({ConversionFactors.get_label(unit)})',
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


# ============================================================================
# CALLBACKS - SECTOR CORRELATION TAB
# ============================================================================

@callback(
    Output('sector-correlation-content', 'children'),
    Input('sector-data-store', 'data'),
    State('sector-selector', 'value'),
    State('sectors-store', 'data'),
    State('active-project-store', 'data')
)
def render_sector_correlation(data, sector_idx, sectors, active_project):
    """Render sector correlation analysis"""
    if not data or sector_idx is None or not sectors or not active_project:
        return dbc.Alert('No data available for correlation analysis.', color='info')

    try:
        sector_name = sectors[sector_idx]

        # Fetch correlation data from backend
        correlation_response = api.get_sector_correlation(
            active_project['path'],
            sector_name
        )

        correlation_matrix = correlation_response.get('correlation_matrix', {})
        drivers = correlation_response.get('drivers', [])

        if not correlation_matrix or not drivers:
            return dbc.Alert('No correlation data available for this sector.', color='info')

        # Create correlation heatmap
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.get('values', []),
            x=drivers,
            y=drivers,
            colorscale='RdBu',
            zmid=0,
            text=correlation_matrix.get('values', []),
            texttemplate='%{text:.3f}',
            textfont={"size": 10},
            colorbar=dict(title='Correlation')
        ))

        fig.update_layout(
            title=f'{sector_name} - Correlation Matrix',
            xaxis_title='Drivers',
            yaxis_title='Drivers',
            height=600,
            template='plotly_white'
        )

        # Summary statistics
        summary_stats = html.Div([
            html.H6('Correlation Summary', className='mt-4 mb-3'),
            dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Driver Pair'),
                        html.Th('Correlation'),
                        html.Th('Strength')
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(f"{pair['driver1']} - {pair['driver2']}"),
                        html.Td(f"{pair['value']:.3f}"),
                        html.Td(
                            html.Span(
                                pair['strength'],
                                className=f"badge bg-{pair['badge_color']}"
                            )
                        )
                    ]) for pair in correlation_response.get('top_correlations', [])
                ])
            ], bordered=True, striped=True, hover=True, size='sm')
        ])

        return html.Div([
            dcc.Graph(figure=fig, config={'displayModeBar': True}),
            summary_stats
        ])

    except Exception as e:
        # If correlation endpoint doesn't exist or fails, show graceful fallback
        return dbc.Alert([
            html.H5('Correlation Analysis', className='alert-heading'),
            html.P('Correlation analysis will be available once forecast models are run.'),
            html.Hr(),
            html.P('Run a forecast first using the "Configure Forecast" button.', className='mb-0')
        ], color='info')


# ============================================================================
# CALLBACKS - CONFIGURE FORECAST MODAL
# ============================================================================

@callback(
    Output('configure-forecast-modal', 'is_open'),
    Output('configure-forecast-modal-content', 'children'),
    Input('open-configure-forecast-btn', 'n_clicks'),
    Input('cancel-forecast-btn', 'n_clicks'),
    Input('start-forecast-btn', 'n_clicks'),
    State('configure-forecast-modal', 'is_open'),
    State('active-project-store', 'data'),
    State('sectors-store', 'data'),
    prevent_initial_call=True
)
def toggle_configure_modal(open_clicks, cancel_clicks, start_clicks, is_open, active_project, sectors):
    """Toggle configure forecast modal and render content"""
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Close modal if cancel or start button clicked
    if button_id in ['cancel-forecast-btn', 'start-forecast-btn']:
        return False, no_update

    # Open modal and render content
    if button_id == 'open-configure-forecast-btn':
        if not active_project or not sectors:
            return True, dbc.Alert('Please load a project first.', color='warning')

        # Render configure form
        modal_content = html.Div([
            dbc.Tabs([
                # Basic Configuration Tab
                dbc.Tab([
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Scenario Name *', className='fw-bold'),
                                dbc.Input(
                                    id='forecast-scenario-name',
                                    type='text',
                                    placeholder='e.g., Base Case 2024',
                                    className='mb-3'
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Base Year *', className='fw-bold'),
                                dbc.Input(
                                    id='forecast-base-year',
                                    type='number',
                                    placeholder='e.g., 2023',
                                    min=2000,
                                    max=2100,
                                    className='mb-3'
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label('Target Year *', className='fw-bold'),
                                dbc.Input(
                                    id='forecast-target-year',
                                    type='number',
                                    placeholder='e.g., 2050',
                                    min=2000,
                                    max=2100,
                                    className='mb-3'
                                )
                            ], width=6)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Forecasting Models', className='fw-bold mb-2'),
                                dbc.Checklist(
                                    id='forecast-models',
                                    options=[
                                        {'label': ' Simple Linear Regression (SLR)', 'value': 'SLR'},
                                        {'label': ' Multiple Linear Regression (MLR)', 'value': 'MLR'},
                                        {'label': ' Weighted Average Method (WAM)', 'value': 'WAM'},
                                        {'label': ' Time Series Analysis', 'value': 'TimeSeries'}
                                    ],
                                    value=['SLR', 'MLR'],
                                    className='mb-3'
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Sectors to Forecast', className='fw-bold mb-2'),
                                dbc.Checklist(
                                    id='forecast-sectors',
                                    options=[{'label': f' {sector}', 'value': idx}
                                            for idx, sector in enumerate(sectors)],
                                    value=list(range(len(sectors))),  # All selected by default
                                    className='mb-3'
                                )
                            ], width=12)
                        ])
                    ], className='p-3')
                ], label='⚙️ Basic Configuration', tab_id='basic'),

                # T&D Losses Tab
                dbc.Tab([
                    html.Div([
                        dbc.Alert([
                            html.H6('Transmission & Distribution Losses', className='alert-heading'),
                            html.P('Configure T&D loss percentages for each sector. These losses will be factored into the final demand calculations.')
                        ], color='info', className='mb-3'),

                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label(sector, className='fw-bold'),
                                    dbc.InputGroup([
                                        dbc.Input(
                                            id={'type': 'td-loss', 'sector': idx},
                                            type='number',
                                            value=5.0,
                                            min=0,
                                            max=100,
                                            step=0.1
                                        ),
                                        dbc.InputGroupText('%')
                                    ], className='mb-3')
                                ], width=6)
                            ]) for idx, sector in enumerate(sectors)
                        ])
                    ], className='p-3')
                ], label='⚡ T&D Losses', tab_id='td_losses'),

                # Advanced Options Tab
                dbc.Tab([
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Confidence Interval', className='fw-bold'),
                                dcc.Slider(
                                    id='forecast-confidence',
                                    min=80,
                                    max=99,
                                    step=1,
                                    value=95,
                                    marks={80: '80%', 85: '85%', 90: '90%', 95: '95%', 99: '99%'},
                                    className='mb-4'
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Data Validation', className='fw-bold'),
                                dbc.Checklist(
                                    id='forecast-validation-options',
                                    options=[
                                        {'label': ' Remove outliers', 'value': 'remove_outliers'},
                                        {'label': ' Interpolate missing values', 'value': 'interpolate'},
                                        {'label': ' Apply seasonal adjustments', 'value': 'seasonal'}
                                    ],
                                    value=['interpolate'],
                                    className='mb-3'
                                )
                            ], width=12)
                        ]),

                        dbc.Row([
                            dbc.Col([
                                dbc.Label('Output Options', className='fw-bold'),
                                dbc.Checklist(
                                    id='forecast-output-options',
                                    options=[
                                        {'label': ' Generate detailed report', 'value': 'report'},
                                        {'label': ' Export to Excel', 'value': 'excel'},
                                        {'label': ' Save visualization charts', 'value': 'charts'}
                                    ],
                                    value=['report'],
                                    className='mb-3'
                                )
                            ], width=12)
                        ])
                    ], className='p-3')
                ], label='🔧 Advanced Options', tab_id='advanced')
            ], id='configure-tabs', active_tab='basic')
        ])

        return True, modal_content

    return no_update, no_update


# ============================================================================
# CALLBACKS - START FORECASTING
# ============================================================================

@callback(
    Output('forecast-progress-modal', 'is_open', allow_duplicate=True),
    Output('forecast-process-state', 'data', allow_duplicate=True),
    Output('forecast-progress-interval', 'disabled', allow_duplicate=True),
    Input('start-forecast-btn', 'n_clicks'),
    State('forecast-scenario-name', 'value'),
    State('forecast-base-year', 'value'),
    State('forecast-target-year', 'value'),
    State('forecast-models', 'value'),
    State('forecast-sectors', 'value'),
    State({'type': 'td-loss', 'sector': ALL}, 'value'),
    State('active-project-store', 'data'),
    State('sectors-store', 'data'),
    prevent_initial_call=True
)
def start_forecasting(n_clicks, scenario_name, base_year, target_year, models,
                     selected_sectors, td_losses, active_project, sectors):
    """Start forecasting process and open progress modal"""
    if not n_clicks:
        return no_update, no_update, no_update

    # Validation
    if not scenario_name or not base_year or not target_year:
        return no_update, no_update, no_update

    if not models or not selected_sectors:
        return no_update, no_update, no_update

    try:
        # Prepare forecast configuration
        forecast_config = {
            'scenario_name': scenario_name,
            'base_year': int(base_year),
            'target_year': int(target_year),
            'models': models,
            'sectors': [sectors[idx] for idx in selected_sectors],
            'td_losses': {sectors[idx]: td_losses[idx] for idx in selected_sectors}
        }

        # Start forecast via API
        response = api.start_demand_forecast(
            active_project['path'],
            forecast_config
        )

        # Store process ID for tracking
        process_state = {
            'process_id': response.get('process_id'),
            'status': 'running',
            'progress': 0,
            'current_task': 'Initializing forecast...'
        }

        # Open progress modal and enable interval for polling
        return True, process_state, False

    except Exception as e:
        print(f"Error starting forecast: {e}")
        return no_update, no_update, no_update


# ============================================================================
# CALLBACKS - FORECAST PROGRESS TRACKING (SSE Alternative)
# ============================================================================

@callback(
    Output('forecast-progress-content', 'children'),
    Output('forecast-process-state', 'data', allow_duplicate=True),
    Output('forecast-progress-interval', 'disabled', allow_duplicate=True),
    Input('forecast-progress-interval', 'n_intervals'),
    State('forecast-process-state', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def update_forecast_progress(n_intervals, process_state, active_project):
    """Poll backend for forecast progress updates"""
    if not process_state or not process_state.get('process_id'):
        return no_update, no_update, no_update

    try:
        # Poll progress from backend
        progress_response = api.get_forecast_progress(
            active_project['path'],
            process_state['process_id']
        )

        status = progress_response.get('status', 'running')
        progress = progress_response.get('progress', 0)
        current_task = progress_response.get('current_task', '')
        logs = progress_response.get('logs', [])

        # Update process state
        updated_state = {
            'process_id': process_state['process_id'],
            'status': status,
            'progress': progress,
            'current_task': current_task
        }

        # Render progress content
        progress_content = html.Div([
            # Progress bar
            html.Div([
                html.Div([
                    html.Strong('Progress: '),
                    html.Span(f'{progress}%')
                ], className='mb-2'),
                dbc.Progress(
                    value=progress,
                    color='success' if status == 'completed' else 'primary',
                    striped=True,
                    animated=status == 'running',
                    className='mb-3'
                )
            ]),

            # Current task
            html.Div([
                html.Strong('Current Task: '),
                html.Span(current_task)
            ], className='mb-3'),

            # Logs
            html.Div([
                html.H6('Process Logs:', className='mb-2'),
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Div(log, className='mb-1', style={'fontSize': '0.875rem'})
                            for log in logs[-20:]  # Show last 20 logs
                        ], style={
                            'maxHeight': '300px',
                            'overflowY': 'auto',
                            'fontFamily': 'monospace',
                            'backgroundColor': '#f8f9fa',
                            'padding': '0.5rem'
                        })
                    ], className='p-2')
                ])
            ]),

            # Completion message
            dbc.Alert([
                html.H5('✅ Forecast Completed!', className='alert-heading'),
                html.P('Your demand forecast has been generated successfully.'),
                dbc.Button('View Results', id='view-forecast-results-btn', color='success')
            ], color='success', className='mt-3') if status == 'completed' else html.Div()
        ])

        # Stop interval if completed or failed
        stop_interval = status in ['completed', 'failed', 'cancelled']

        return progress_content, updated_state, stop_interval

    except Exception as e:
        print(f"Error fetching progress: {e}")
        return no_update, no_update, no_update


# ============================================================================
# CALLBACKS - PROGRESS MODAL CONTROLS
# ============================================================================

@callback(
    Output('forecast-progress-modal', 'is_open', allow_duplicate=True),
    Output('floating-process-indicator', 'style', allow_duplicate=True),
    Output('floating-process-indicator', 'children', allow_duplicate=True),
    Input('close-progress-modal', 'n_clicks'),
    Input('minimize-progress-modal', 'n_clicks'),
    State('forecast-process-state', 'data'),
    prevent_initial_call=True
)
def control_progress_modal(close_clicks, minimize_clicks, process_state):
    """Control progress modal visibility and floating indicator"""
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'close-progress-modal':
        # Close modal completely
        return False, {'display': 'none'}, ''

    if button_id == 'minimize-progress-modal':
        # Minimize modal, show floating indicator
        if process_state and process_state.get('status') == 'running':
            floating_indicator = dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span('🔄 Forecasting in progress...', className='me-3'),
                        html.Span(f"{process_state.get('progress', 0)}%", className='badge bg-primary me-2'),
                        dbc.Button('Show', id='show-progress-modal', size='sm', color='link')
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], className='py-2 px-3')
            ], style={
                'position': 'fixed',
                'bottom': '20px',
                'right': '20px',
                'zIndex': '1050',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
            })

            return False, {'display': 'block'}, floating_indicator

    return no_update, no_update, no_update


@callback(
    Output('forecast-progress-modal', 'is_open', allow_duplicate=True),
    Output('floating-process-indicator', 'style', allow_duplicate=True),
    Input('show-progress-modal', 'n_clicks'),
    prevent_initial_call=True
)
def show_progress_modal(n_clicks):
    """Show progress modal when floating indicator clicked"""
    if n_clicks:
        return True, {'display': 'none'}
    return no_update, no_update


# ============================================================================
# CALLBACKS - CANCEL FORECASTING
# ============================================================================

@callback(
    Output('forecast-process-state', 'data', allow_duplicate=True),
    Output('forecast-progress-interval', 'disabled', allow_duplicate=True),
    Input('cancel-forecasting-btn', 'n_clicks'),
    State('forecast-process-state', 'data'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def cancel_forecasting(n_clicks, process_state, active_project):
    """Cancel ongoing forecast process"""
    if not n_clicks or not process_state:
        return no_update, no_update

    try:
        # Call API to cancel process
        api.cancel_forecast(
            active_project['path'],
            process_state['process_id']
        )

        # Update state
        updated_state = {
            **process_state,
            'status': 'cancelled'
        }

        return updated_state, True  # Stop interval

    except Exception as e:
        print(f"Error cancelling forecast: {e}")
        return no_update, no_update


# ============================================================================
# UNIT CONVERSION STATE SYNC
# ============================================================================

@callback(
    Output('demand-projection-state', 'data', allow_duplicate=True),
    Input('consolidated-unit-selector', 'value'),
    Input('sector-unit-selector', 'value'),
    State('demand-projection-state', 'data'),
    prevent_initial_call=True
)
def sync_unit_state(consolidated_unit, sector_unit, current_state):
    """Sync unit selection to state"""
    ctx = callback_context
    if not ctx.triggered:
        return no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'consolidated-unit-selector':
        return StateManager.merge_state(current_state, {
            'consolidated': {**current_state.get('consolidated', {}), 'selectedUnit': consolidated_unit}
        })
    elif trigger_id == 'sector-unit-selector':
        return StateManager.merge_state(current_state, {
            'sectorView': {**current_state.get('sectorView', {}), 'selectedUnit': sector_unit}
        })

    return no_update


# ============================================================================
# TAB STATE SYNC
# ============================================================================

@callback(
    Output('demand-projection-state', 'data', allow_duplicate=True),
    Input('consolidated-tabs', 'active_tab'),
    Input('sector-tabs', 'active_tab'),
    State('demand-projection-state', 'data'),
    prevent_initial_call=True
)
def sync_tab_state(consolidated_tab, sector_tab, current_state):
    """Sync active tab to state"""
    ctx = callback_context
    if not ctx.triggered:
        return no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'consolidated-tabs':
        return StateManager.merge_state(current_state, {
            'consolidated': {**current_state.get('consolidated', {}), 'activeTab': consolidated_tab}
        })
    elif trigger_id == 'sector-tabs':
        return StateManager.merge_state(current_state, {
            'sectorView': {**current_state.get('sectorView', {}), 'activeTab': sector_tab}
        })

    return no_update


# END OF PART 2
# To integrate: Import these callbacks in main app after importing Part 1
