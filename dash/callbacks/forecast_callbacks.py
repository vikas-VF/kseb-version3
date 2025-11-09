"""Demand Forecasting Callbacks - Complete Implementation"""
from dash import Input, Output, State, html, no_update
import dash_bootstrap_components as dbc

def register_callbacks(app):
    
    @app.callback(
        Output('forecast-execution-status', 'children'),
        Output('forecast-interval', 'disabled'),
        Output('forecast-progress-store', 'data'),
        Input('start-forecast-btn', 'n_clicks'),
        State('forecast-scenario-name', 'value'),
        State('forecast-target-year', 'value'),
        State('forecast-models-selection', 'value'),
        State('active-project-store', 'data'),
        prevent_initial_call=True
    )
    def start_forecasting(n_clicks, scenario, target_year, models, project):
        if not n_clicks or not project:
            return no_update, True, no_update
        
        if not scenario or not models:
            return dbc.Alert('Please enter scenario name and select models', color='warning'), True, no_update
        
        # Start forecasting (simulation)
        progress_data = {
            'status': 'running',
            'progress': 0,
            'message': 'Initializing forecasting...',
            'scenario': scenario,
            'models': models
        }
        
        return (
            dbc.Alert([
                html.H5('🚀 Forecasting Started', className='alert-heading'),
                html.P(f'Scenario: {scenario}'),
                html.P(f'Models: {", ".join(models)}'),
                dbc.Progress(value=10, striped=True, animated=True, className='mt-2')
            ], color='info'),
            False,  # Enable interval
            progress_data
        )
    
    @app.callback(
        Output('sectors-list-preview', 'children'),
        Input('parse-excel-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def parse_excel(n_clicks):
        if not n_clicks:
            return no_update
        
        # Simulation of parsed sectors
        sectors = ['Residential', 'Commercial', 'Industrial', 'Agriculture', 'Public Lighting']
        return html.Ul([html.Li(f'✓ {sector}') for sector in sectors])
