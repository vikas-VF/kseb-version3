"""
Settings Page - Complete Implementation
Matches React Settings.jsx functionality with color configuration for sectors and models
"""
from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import json
import os


def layout():
    """Settings page layout with color configuration"""
    return html.Div([
        # Stores for settings
        dcc.Store(id='settings-sectors-store', storage_type='memory'),
        dcc.Store(id='settings-save-status-store', storage_type='memory', data={'saving': False, 'saved': False}),

        # Main container
        html.Div([
            # Header Section
            html.Header([
                # Left side - Title with icon
                html.Div([
                    html.Div([
                        html.I(className='bi bi-palette-fill', style={
                            'fontSize': '20px',
                            'color': '#4F46E5'
                        })
                    ], style={
                        'backgroundColor': '#EEF2FF',
                        'borderRadius': '8px',
                        'padding': '8px',
                        'display': 'inline-flex',
                        'alignItems': 'center',
                        'justifyContent': 'center'
                    }),
                    html.H1('Color Configuration', style={
                        'fontSize': '20px',
                        'fontWeight': '600',
                        'color': '#1F2937',
                        'margin': '0',
                        'display': 'inline-block',
                        'marginLeft': '12px',
                        'verticalAlign': 'middle'
                    })
                ], style={'display': 'inline-flex', 'alignItems': 'center', 'gap': '12px'}),

                # Right side - Save button
                html.Button([
                    html.I(id='settings-save-icon', className='bi bi-save', style={'marginRight': '8px'}),
                    html.Span('Save Settings', id='settings-save-text')
                ], id='save-settings-btn', n_clicks=0, style={
                    'backgroundColor': '#4F46E5',
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '8px',
                    'padding': '8px 16px',
                    'fontSize': '14px',
                    'fontWeight': '600',
                    'cursor': 'pointer',
                    'display': 'flex',
                    'alignItems': 'center',
                    'width': '140px',
                    'justifyContent': 'center',
                    'transition': 'all 0.2s'
                })
            ], style={
                'position': 'sticky',
                'top': '0',
                'zIndex': '10',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'space-between',
                'borderBottom': '1px solid #E5E7EB',
                'backgroundColor': 'white',
                'padding': '16px 24px',
                'boxShadow': '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
            }),

            # Main Content
            html.Main([
                html.Div([
                    html.Div([
                        # Sector Colors Section
                        html.Section([
                            html.H2('Sector Colors', style={
                                'marginBottom': '24px',
                                'fontSize': '20px',
                                'fontWeight': '700',
                                'color': '#1F2937'
                            }),
                            html.Div(id='sector-colors-grid')
                        ], style={
                            'borderRadius': '12px',
                            'border': '1px solid #E5E7EB',
                            'backgroundColor': 'white',
                            'padding': '24px',
                            'boxShadow': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                            'transition': 'box-shadow 0.3s'
                        }, className='hover-shadow'),

                        # Model Colors Section
                        html.Section([
                            html.H2('Model Colors', style={
                                'marginBottom': '24px',
                                'fontSize': '20px',
                                'fontWeight': '700',
                                'color': '#1F2937'
                            }),
                            html.Div(id='model-colors-grid')
                        ], style={
                            'borderRadius': '12px',
                            'border': '1px solid #E5E7EB',
                            'backgroundColor': 'white',
                            'padding': '24px',
                            'boxShadow': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                            'transition': 'box-shadow 0.3s'
                        }, className='hover-shadow')
                    ], style={
                        'display': 'grid',
                        'gridTemplateColumns': 'repeat(auto-fit, minmax(400px, 1fr))',
                        'gap': '32px'
                    })
                ], style={
                    'maxWidth': '1280px',
                    'margin': '0 auto',
                    'padding': '0 24px'
                })
            ], style={
                'flex': '1',
                'overflowY': 'auto',
                'padding': '24px 0'
            })
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'height': '100vh',
            'width': '100%',
            'backgroundColor': '#F9FAFB'
        }),

        # Toast notification
        html.Div(id='settings-toast')

    ], style={'height': '100%', 'width': '100%'})


# Callback to load sectors and initialize color configuration
@callback(
    Output('settings-sectors-store', 'data'),
    Output('sector-colors-grid', 'children'),
    Output('model-colors-grid', 'children'),
    Input('active-project-store', 'data'),
    State('color-settings-store', 'data'),
    prevent_initial_call=True
)
def load_color_configuration(active_project, current_color_settings):
    """Load sectors and initialize color pickers"""
    from services.local_service import LocalService

    service = LocalService()

    # Default model colors (base set - will be expanded with actual models from results)
    default_model_colors = {
        'Historical': '#000000',
        'SLR': '#10b981',
        'MLR': '#3b82f6',
        'WAM': '#f59e0b',
        'Time Series': '#8b5cf6',
        'User Data': '#ef4444'
    }

    # Default sector colors palette
    default_sector_colors = [
        '#3b82f6', '#ec4899', '#10b981', '#f59e0b',
        '#8b5cf6', '#f97316', '#a855f7', '#14b8a6'
    ]

    # Check if project is loaded
    if not active_project or not active_project.get('path'):
        # No project loaded - show placeholder
        sector_grid = html.Div([
            html.Div([
                html.P('Load a project to configure colors.', style={
                    'textAlign': 'center',
                    'color': '#6B7280'
                })
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center',
                'height': '192px',
                'borderRadius': '8px',
                'border': '2px dashed #D1D5DB',
                'backgroundColor': '#F9FAFB',
                'padding': '16px'
            })
        ])

        # Still show model colors
        model_grid = create_color_grid(default_models, 'model')

        return None, sector_grid, model_grid

    project_path = active_project['path']

    try:
        # Get sectors from ACTUAL FORECAST RESULTS (not input file)
        # This ensures we only show sectors that have been forecasted
        scenarios_response = service.get_scenarios(project_path)
        scenarios = scenarios_response.get('scenarios', [])

        # Collect all unique sectors from all scenarios
        all_sectors = set()
        if scenarios:
            for scenario in scenarios:
                scenario_sectors_response = service.get_scenario_sectors(project_path, scenario)
                sector_names = scenario_sectors_response.get('sectors', [])
                all_sectors.update(sector_names)

        sectors = sorted(list(all_sectors))  # Sort alphabetically

        # Also collect all unique models from all sectors/scenarios
        all_models = set()
        if scenarios:
            for scenario in scenarios:
                models_response = service.get_sector_available_models(project_path, scenario)
                if models_response.get('success'):
                    models_per_sector = models_response.get('models', {})
                    for sector_models in models_per_sector.values():
                        all_models.update(sector_models)

        # Create model colors dict with defaults for known models
        discovered_models = sorted(list(all_models))

        if not sectors:
            sector_grid = html.Div([
                html.P('No forecast results found in project.', style={
                    'textAlign': 'center',
                    'color': '#6B7280'
                })
            ], style={
                'padding': '32px',
                'textAlign': 'center'
            })
            model_grid = create_color_grid(default_model_colors, 'model')
            return {'sectors': []}, sector_grid, model_grid

        # Load or initialize color settings
        color_settings = current_color_settings or {}

        # Try to load from file
        try:
            color_result = service.get_color_settings(project_path)
            if color_result and 'colors' in color_result:
                saved_colors = color_result['colors']
                sector_colors = saved_colors.get('sectors', {})
                model_colors = saved_colors.get('models', {})
            else:
                sector_colors = {}
                model_colors = {}
        except:
            sector_colors = {}
            model_colors = {}

        # Generate default colors for sectors (only for sectors not in saved settings)
        for i, sector in enumerate(sectors):
            if sector not in sector_colors:
                sector_colors[sector] = default_sector_colors[i % len(default_sector_colors)]

        # Generate default colors for models (only for models not in saved settings)
        for model in discovered_models:
            if model not in model_colors:
                # Use default color if known, otherwise assign a color from palette
                model_colors[model] = default_model_colors.get(
                    model,
                    default_sector_colors[len(model_colors) % len(default_sector_colors)]
                )

        # Update color settings store
        new_color_settings = {
            'sectors': sector_colors,
            'models': model_colors
        }

        # Create grids
        sector_grid = create_color_grid(sector_colors, 'sector')
        model_grid = create_color_grid(model_colors, 'model')

        return {'sectors': sectors, 'colors': new_color_settings}, sector_grid, model_grid

    except Exception as e:
        print(f"Error loading color configuration: {e}")
        sector_grid = html.Div([
            html.P(f'Error loading sectors: {str(e)}', style={
                'textAlign': 'center',
                'color': '#EF4444'
            })
        ], style={'padding': '32px'})
        model_grid = create_color_grid(default_models, 'model')
        return None, sector_grid, model_grid


def create_color_grid(items_dict, item_type):
    """Create a grid of color pickers"""
    if not items_dict:
        return html.Div('No items to display')

    color_items = []
    for name, color in items_dict.items():
        color_items.append(
            html.Div([
                # Color picker input
                dcc.Input(
                    id={'type': f'{item_type}-color-picker', 'index': name},
                    type='color',
                    value=color,
                    style={
                        'height': '40px',
                        'width': '40px',
                        'cursor': 'pointer',
                        'borderRadius': '50%',
                        'border': '2px solid white',
                        'boxShadow': '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                        'transition': 'transform 0.2s'
                    },
                    className='color-picker-hover'
                ),
                # Label
                html.Span(name, style={
                    'fontSize': '14px',
                    'fontWeight': '500',
                    'color': '#374151',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'whiteSpace': 'nowrap'
                })
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'gap': '12px',
                'padding': '12px',
                'borderRadius': '8px',
                'transition': 'background-color 0.2s'
            }, className='color-picker-item')
        )

    return html.Div(color_items, style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fill, minmax(200px, 1fr))',
        'gap': '16px'
    })


# Callback to save color settings (with allow_duplicate for shared outputs)
@callback(
    Output('settings-save-status-store', 'data'),
    Output('settings-toast', 'children'),
    Output('save-settings-btn', 'style', allow_duplicate=True),
    Output('settings-save-icon', 'className', allow_duplicate=True),
    Output('settings-save-text', 'children', allow_duplicate=True),
    Output('color-settings-store', 'data',allow_duplicate=True),
    Input('save-settings-btn', 'n_clicks'),
    State('active-project-store', 'data'),
    State({'type': 'sector-color-picker', 'index': ALL}, 'id'),
    State({'type': 'sector-color-picker', 'index': ALL}, 'value'),
    State({'type': 'model-color-picker', 'index': ALL}, 'id'),
    State({'type': 'model-color-picker', 'index': ALL}, 'value'),
    State('settings-save-status-store', 'data'),
    prevent_initial_call=True
)
def save_color_settings(n_clicks, active_project, sector_ids, sector_values,
                       model_ids, model_values, current_status):
    """Save color configuration to file"""
    from services.local_service import LocalService

    if not n_clicks or n_clicks == 0:
        raise PreventUpdate

    if not active_project or not active_project.get('path'):
        return (
            {'saving': False, 'saved': False},
            dbc.Toast(
                "⚠️ Please load a project first",
                header="Cannot Save",
                icon="warning",
                duration=3000,
                is_open=True,
                style={'position': 'fixed', 'top': '20px', 'right': '20px', 'zIndex': 9999}
            ),
            {
                'backgroundColor': '#EF4444',
                'color': 'white',
                'border': 'none',
                'borderRadius': '8px',
                'padding': '8px 16px',
                'fontSize': '14px',
                'fontWeight': '600',
                'cursor': 'pointer',
                'display': 'flex',
                'alignItems': 'center',
                'width': '140px',
                'justifyContent': 'center'
            },
            'bi bi-exclamation-triangle',
            'Error',
            no_update
        )

    project_path = active_project['path']
    service = LocalService()

    # Build color configuration
    sector_colors = {}
    for idx, sector_id in enumerate(sector_ids):
        sector_name = sector_id['index']
        sector_colors[sector_name] = sector_values[idx]

    model_colors = {}
    for idx, model_id in enumerate(model_ids):
        model_name = model_id['index']
        model_colors[model_name] = model_values[idx]

    color_config = {
        'sectors': sector_colors,
        'models': model_colors
    }

    try:
        # Save to file
        service.save_color_settings(project_path, color_config)

        # Success state
        return (
            {'saving': False, 'saved': True},
            dbc.Toast(
                "✅ Settings saved successfully!",
                header="Success",
                icon="success",
                duration=2000,
                is_open=True,
                style={'position': 'fixed', 'top': '20px', 'right': '20px', 'zIndex': 9999}
            ),
            {
                'backgroundColor': '#10B981',
                'color': 'white',
                'border': 'none',
                'borderRadius': '8px',
                'padding': '8px 16px',
                'fontSize': '14px',
                'fontWeight': '600',
                'cursor': 'pointer',
                'display': 'flex',
                'alignItems': 'center',
                'width': '140px',
                'justifyContent': 'center'
            },
            'bi bi-check-circle',
            'Saved!',
            color_config
        )
    except Exception as e:
        print(f"Error saving color settings: {e}")
        return (
            {'saving': False, 'saved': False},
            dbc.Toast(
                f"❌ Error saving settings: {str(e)}",
                header="Error",
                icon="danger",
                duration=4000,
                is_open=True,
                style={'position': 'fixed', 'top': '20px', 'right': '20px', 'zIndex': 9999}
            ),
            {
                'backgroundColor': '#EF4444',
                'color': 'white',
                'border': 'none',
                'borderRadius': '8px',
                'padding': '8px 16px',
                'fontSize': '14px',
                'fontWeight': '600',
                'cursor': 'pointer',
                'display': 'flex',
                'alignItems': 'center',
                'width': '140px',
                'justifyContent': 'center'
            },
            'bi bi-exclamation-triangle',
            'Error',
            no_update
        )


# Callback to reset save button after success
@callback(
    Output('save-settings-btn', 'style', allow_duplicate=True),
    Output('settings-save-icon', 'className', allow_duplicate=True),
    Output('settings-save-text', 'children', allow_duplicate=True),
    Input('settings-save-status-store', 'data'),
    prevent_initial_call=True
)
def reset_save_button(status):
    """Reset save button to normal state after 2 seconds"""
    import time

    if not status or not status.get('saved'):
        raise PreventUpdate

    # Add a small delay
    time.sleep(2)

    return (
        {
            'backgroundColor': '#4F46E5',
            'color': 'white',
            'border': 'none',
            'borderRadius': '8px',
            'padding': '8px 16px',
            'fontSize': '14px',
            'fontWeight': '600',
            'cursor': 'pointer',
            'display': 'flex',
            'alignItems': 'center',
            'width': '140px',
            'justifyContent': 'center',
            'transition': 'all 0.2s'
        },
        'bi bi-save',
        'Save Settings'
    )
