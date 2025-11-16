"""
TopBar Component - Header with Project Info and Process Status
Converted from React TopBar component to Dash
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

def create_topbar(active_project=None, process_state=None):
    """
    Create the top bar header

    Args:
        active_project: Currently active project dict
        process_state: Current process states dict
    """

    # Project info section
    project_name = active_project['name'] if active_project else 'No Project Loaded'

    # Process notification bell
    has_running_processes = False
    running_count = 0

    if process_state:
        running_processes = [p for p in process_state.values() if p.get('status') == 'running']
        has_running_processes = len(running_processes) > 0
        running_count = len(running_processes)

    # Calculate overall progress
    overall_progress = 0
    if process_state and has_running_processes:
        running_processes = [p for p in process_state.values() if p.get('status') == 'running']
        if running_processes:
            overall_progress = sum(p.get('progress', {}).get('percentage', 0) for p in running_processes) / len(running_processes)

    return html.Div([
        # Left section - Project info
        html.Div([
            html.Div(
                '📁',
                style={
                    'width': '40px',
                    'height': '40px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'backgroundColor': '#334155',  # slate-700
                    'borderRadius': '0.5rem',
                    'fontSize': '1.25rem'
                }
            ),
            html.Div([
                html.P(
                    'Active Project:',
                    style={
                        'fontSize': '0.875rem',
                        'fontWeight': '700',
                        'color': '#a5b4fc',  # indigo-400
                        'margin': '0'
                    }
                ),
                html.H1(
                    project_name,
                    title=project_name,
                    style={
                        'fontSize': '1rem',
                        'fontWeight': '700',
                        'color': '#ffffff',
                        'margin': '0',
                        'maxWidth': '500px',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'whiteSpace': 'nowrap'
                    }
                )
            ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '0.125rem'})
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '0.75rem'}),

        # Right section - Notifications and settings
        html.Div([
            # Notification bell with progress indicator
            html.Div([
                html.Button(
                    [
                        # Progress circle if running
                        html.Div([
                            # SVG progress circle
                            html.Div(
                                style={
                                    'position': 'relative',
                                    'width': '20px',
                                    'height': '20px',
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'center'
                                },
                                children=[
                                    # Background circle
                                    html.Div(
                                        style={
                                            'position': 'absolute',
                                            'width': '100%',
                                            'height': '100%',
                                            'borderRadius': '50%',
                                            'border': '2px solid #475569'  # slate-600
                                        }
                                    ),
                                    # Progress circle
                                    html.Div(
                                        style={
                                            'position': 'absolute',
                                            'width': '100%',
                                            'height': '100%',
                                            'borderRadius': '50%',
                                            'border': '2px solid #6366f1',  # indigo-500
                                            'borderTopColor': 'transparent',
                                            'transform': f'rotate({(overall_progress / 100) * 360}deg)',
                                            'transition': 'transform 0.3s'
                                        }
                                    ) if has_running_processes else None,
                                    # Bell icon
                                    html.Span('🔔', style={'fontSize': '0.75rem'}),
                                    # Count badge
                                    html.Div(
                                        str(running_count),
                                        style={
                                            'position': 'absolute',
                                            'top': '-4px',
                                            'right': '-4px',
                                            'width': '16px',
                                            'height': '16px',
                                            'backgroundColor': '#ef4444',  # red-500
                                            'borderRadius': '50%',
                                            'display': 'flex',
                                            'alignItems': 'center',
                                            'justifyContent': 'center',
                                            'fontSize': '0.625rem',
                                            'fontWeight': '700',
                                            'color': '#ffffff'
                                        }
                                    ) if running_count > 0 else None
                                ]
                            )
                        ] if has_running_processes else ['🔔'])
                    ],
                    id='notification-bell-btn',
                    style={
                        'padding': '0.5rem',
                        'borderRadius': '50%',
                        'border': 'none',
                        'backgroundColor': 'transparent',
                        'color': '#94a3b8',  # slate-400
                        'cursor': 'pointer',
                        'transition': 'all 0.2s',
                        'fontSize': '1.25rem'
                    }
                ),
                # Progress panel dropdown (will be handled by callbacks)
                html.Div(id='progress-panel-container')
            ], style={'position': 'relative'}),

            # Settings button
            html.Button(
                '⚙️',
                id={'type': 'nav-link', 'page': 'Settings'},
                style={
                    'padding': '0.5rem',
                    'borderRadius': '50%',
                    'border': 'none',
                    'backgroundColor': 'transparent',
                    'color': '#94a3b8',
                    'cursor': 'pointer',
                    'transition': 'all 0.2s',
                    'fontSize': '1.25rem'
                }
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'gap': '1.25rem'})
    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'width': '100%',
        'height': '100%'
    })

def create_progress_panel(processes):
    """
    Create the progress panel dropdown that shows active processes

    Args:
        processes: Dict of process states
    """
    if not processes:
        return html.Div(
            "No active processes.",
            style={
                'position': 'absolute',
                'top': '48px',
                'right': '0',
                'width': '384px',
                'backgroundColor': '#1e293b',  # slate-800
                'border': '1px solid #334155',  # slate-700
                'borderRadius': '0.5rem',
                'padding': '1rem',
                'textAlign': 'center',
                'color': '#94a3b8',  # slate-400
                'boxShadow': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                'zIndex': 50
            }
        )

    running_processes = [p for p in processes.values() if p.get('status') == 'running']
    completed_processes = [p for p in processes.values() if p.get('status') == 'completed']
    failed_processes = [p for p in processes.values() if p.get('status') == 'failed']

    def get_status_badge(status):
        """Get styled badge for process status"""
        colors = {
            'running': '#4f46e5',  # indigo-600
            'completed': '#16a34a',  # green-600
            'failed': '#dc2626',  # red-600
            'cancelled': '#ea580c'  # orange-600
        }
        return html.Span(
            status.upper(),
            style={
                'padding': '0.25rem 0.5rem',
                'borderRadius': '0.25rem',
                'fontSize': '0.75rem',
                'fontWeight': '700',
                'backgroundColor': colors.get(status, '#4b5563'),
                'color': '#ffffff'
            }
        )

    def get_process_icon(status):
        """Get icon for process status"""
        icons = {
            'running': '⏳',
            'completed': '✅',
            'failed': '⚠️',
            'cancelled': '❌'
        }
        return icons.get(status, '❓')

    def create_process_card(process_type, process):
        """Create a card for a single process"""
        percentage = min(100, max(0, round(process.get('progress', {}).get('percentage', 0))))

        return html.Div([
            # Header
            html.Div([
                html.Div([
                    html.Span(get_process_icon(process.get('status', 'running')),
                             style={'marginRight': '0.5rem'}),
                    html.Span(process.get('title', 'Processing...'),
                             style={'fontWeight': '700', 'color': '#ffffff'})
                ], style={'display': 'flex', 'alignItems': 'center'}),
                get_status_badge(process.get('status', 'running'))
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '0.75rem'}),

            # Scenario name if exists
            html.Div([
                html.Span('Scenario:', style={'color': '#94a3b8', 'fontSize': '0.875rem'}),
                html.Span(process.get('scenarioName', 'N/A'),
                         style={'color': '#ffffff', 'fontWeight': '600', 'fontSize': '0.875rem', 'marginLeft': '0.5rem'})
            ], style={'marginBottom': '0.5rem'}) if process.get('scenarioName') else None,

            # Running time
            html.Div([
                html.Span('Running Time:', style={'color': '#94a3b8', 'fontSize': '0.875rem'}),
                html.Span(process.get('elapsedTime', '00:00'),
                         style={'color': '#ffffff', 'fontWeight': '600', 'fontSize': '0.875rem', 'marginLeft': '0.5rem'})
            ], style={'marginBottom': '0.75rem'}),

            # Progress bar (if running)
            html.Div([
                html.Div(
                    style={
                        'width': '100%',
                        'height': '8px',
                        'backgroundColor': '#334155',
                        'borderRadius': '9999px',
                        'overflow': 'hidden',
                        'marginBottom': '0.5rem'
                    },
                    children=html.Div(
                        style={
                            'height': '100%',
                            'backgroundColor': '#6366f1',  # indigo-500
                            'borderRadius': '9999px',
                            'width': f'{percentage}%',
                            'transition': 'width 0.3s'
                        }
                    )
                ),
                html.Div([
                    html.Span(process.get('progress', {}).get('message', 'Processing...'),
                             style={'fontSize': '0.75rem', 'color': '#94a3b8'}),
                    html.Span(f'{percentage}%',
                             style={'fontSize': '0.75rem', 'fontWeight': '700', 'color': '#a5b4fc'})
                ], style={'display': 'flex', 'justifyContent': 'space-between'})
            ]) if process.get('status') == 'running' else None,

            # View logs button
            html.Button(
                'View Full Logs',
                id={'type': 'view-logs-btn', 'process': process_type},
                style={
                    'width': '100%',
                    'padding': '0.5rem',
                    'backgroundColor': '#4f46e5',  # indigo-600
                    'color': '#ffffff',
                    'border': 'none',
                    'borderRadius': '0.375rem',
                    'fontWeight': '600',
                    'fontSize': '0.875rem',
                    'cursor': 'pointer',
                    'transition': 'all 0.2s',
                    'marginTop': '0.75rem'
                }
            )
        ], style={
            'padding': '1rem',
            'borderBottom': '1px solid #334155',
            'backgroundColor': 'rgba(71, 85, 105, 0.1)',
            'transition': 'background-color 0.2s'
        })

    return html.Div([
        # Header
        html.Div([
            html.H3('Active Processes',
                   style={'fontWeight': '700', 'color': '#ffffff', 'fontSize': '1.125rem', 'margin': '0'}),
            html.Div([
                html.Span(f'{len(running_processes)} Running',
                         style={
                             'backgroundColor': '#4f46e5',
                             'color': '#ffffff',
                             'padding': '0.25rem 0.5rem',
                             'borderRadius': '0.25rem',
                             'fontSize': '0.75rem',
                             'marginRight': '0.5rem'
                         }) if running_processes else None,
                html.Span(f'{len(completed_processes)} Completed',
                         style={
                             'backgroundColor': '#16a34a',
                             'color': '#ffffff',
                             'padding': '0.25rem 0.5rem',
                             'borderRadius': '0.25rem',
                             'fontSize': '0.75rem',
                             'marginRight': '0.5rem'
                         }) if completed_processes else None,
                html.Span(f'{len(failed_processes)} Failed',
                         style={
                             'backgroundColor': '#dc2626',
                             'color': '#ffffff',
                             'padding': '0.25rem 0.5rem',
                             'borderRadius': '0.25rem',
                             'fontSize': '0.75rem'
                         }) if failed_processes else None
            ], style={'display': 'flex', 'gap': '0.5rem', 'marginTop': '0.5rem'})
        ], style={
            'padding': '1rem',
            'borderBottom': '1px solid #334155',
            'position': 'sticky',
            'top': '0',
            'backgroundColor': '#1e293b',
            'zIndex': 10
        }),

        # Process cards
        html.Div([
            create_process_card(proc_type, proc)
            for proc_type, proc in processes.items()
        ])
    ], style={
        'position': 'absolute',
        'top': '48px',
        'right': '0',
        'width': '384px',
        'backgroundColor': '#1e293b',
        'border': '1px solid #334155',
        'borderRadius': '0.5rem',
        'boxShadow': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'zIndex': 50,
        'maxHeight': '600px',
        'overflow': 'auto',
        'color': '#cbd5e1'
    })
