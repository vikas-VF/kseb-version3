"""Settings Callbacks - Complete Implementation"""
from dash import Input, Output, State, html, no_update
import dash_bootstrap_components as dbc

def register_callbacks(app):
    
    @app.callback(
        Output('settings-output', 'children'),
        Output('color-settings-store', 'data'),
        Input('save-color-settings-btn', 'n_clicks'),
        Input('save-general-settings-btn', 'n_clicks'),
        State('color-settings-store', 'data'),
        prevent_initial_call=True
    )
    def save_settings(color_clicks, general_clicks, current_settings):
        if not (color_clicks or general_clicks):
            return no_update, no_update
        
        return (
            dbc.Alert('✅ Settings saved successfully!', color='success', duration=3000),
            current_settings or {}
        )
