"""
Workflow Stepper Component - Right sidebar showing workflow progress
Converted from React WorkflowStepper component to Dash
"""

from dash import html

def create_workflow_stepper(selected_page='Home', active_project=None):
    """
    Create the workflow stepper sidebar

    Args:
        selected_page: Currently selected page
        active_project: Active project dict
    """

    # Define workflow steps
    workflow_steps = [
        {'name': 'Create Project', 'icon': '📁', 'group': 'Projects'},
        {'name': 'Demand Projection', 'icon': '📈', 'group': 'Forecasting'},
        {'name': 'Demand Visualization', 'icon': '📊', 'group': 'Forecasting'},
        {'name': 'Generate Profiles', 'icon': '⚡', 'group': 'Profiles'},
        {'name': 'Analyze Profiles', 'icon': '🔍', 'group': 'Profiles'},
        {'name': 'Model Config', 'icon': '⚙️', 'group': 'PyPSA'},
        {'name': 'View Results', 'icon': '📉', 'group': 'PyPSA'}
    ]

    def create_step_card(step, index):
        """Create a single workflow step card"""
        is_active = selected_page == step['name']
        step_num = index + 1

        card_style = {
            'width': '100%',
            'padding': '0.75rem 0.5rem',
            'marginBottom': '0.75rem',
            'borderRadius': '0.5rem',
            'backgroundColor': '#4f46e5' if is_active else 'rgba(71, 85, 105, 0.3)',  # indigo-600 or slate-700/30
            'border': '2px solid #6366f1' if is_active else '2px solid transparent',
            'cursor': 'pointer',
            'transition': 'all 0.2s',
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'gap': '0.25rem',
            'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)' if is_active else 'none'
        }

        return html.Button(
            [
                # Step number
                html.Div(
                    str(step_num),
                    style={
                        'width': '24px',
                        'height': '24px',
                        'borderRadius': '50%',
                        'backgroundColor': '#ffffff' if is_active else '#475569',
                        'color': '#4f46e5' if is_active else '#e2e8f0',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'fontSize': '0.75rem',
                        'fontWeight': '700',
                        'marginBottom': '0.25rem'
                    }
                ),
                # Icon
                html.Div(
                    step['icon'],
                    style={
                        'fontSize': '1.5rem',
                        'marginBottom': '0.25rem'
                    }
                ),
                # Step name (vertical text)
                html.Div(
                    step['name'],
                    style={
                        'fontSize': '0.625rem',
                        'fontWeight': '600',
                        'color': '#ffffff' if is_active else '#cbd5e1',
                        'textAlign': 'center',
                        'lineHeight': '1.2',
                        'maxWidth': '60px',
                        'wordWrap': 'break-word'
                    }
                ),
                # Group label
                html.Div(
                    step['group'],
                    style={
                        'fontSize': '0.5rem',
                        'color': '#94a3b8',
                        'marginTop': '0.25rem',
                        'fontWeight': '500'
                    }
                )
            ],
            id={'type': 'nav-link', 'page': step['name']},
            style=card_style,
            className='workflow-step-card'
        )

    # Disable if no project is active (except for Create Project)
    if not active_project:
        # Only show Create Project step when no project is active
        return html.Div([
            html.Div(
                '🚀',
                style={
                    'fontSize': '2rem',
                    'textAlign': 'center',
                    'marginBottom': '1rem',
                    'opacity': '0.5'
                }
            ),
            html.Div(
                'Workflow',
                style={
                    'fontSize': '0.75rem',
                    'fontWeight': '700',
                    'color': '#94a3b8',
                    'textAlign': 'center',
                    'marginBottom': '1.5rem',
                    'letterSpacing': '0.05em'
                }
            ),
            create_step_card(workflow_steps[0], 0),  # Only Create Project
            html.Div(
                'Load a project to see workflow',
                style={
                    'fontSize': '0.625rem',
                    'color': '#64748b',
                    'textAlign': 'center',
                    'marginTop': '1rem',
                    'lineHeight': '1.4'
                }
            )
        ], style={
            'height': '100%',
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'paddingTop': '1rem'
        })

    # Full workflow when project is active
    return html.Div([
        # Header
        html.Div(
            '🚀',
            style={
                'fontSize': '2rem',
                'textAlign': 'center',
                'marginBottom': '1rem'
            }
        ),
        html.Div(
            'Workflow',
            style={
                'fontSize': '0.75rem',
                'fontWeight': '700',
                'color': '#a5b4fc',  # indigo-400
                'textAlign': 'center',
                'marginBottom': '1.5rem',
                'letterSpacing': '0.05em'
            }
        ),

        # Steps
        html.Div([
            create_step_card(step, index)
            for index, step in enumerate(workflow_steps)
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '0.5rem',
            'overflowY': 'auto',
            'flexGrow': 1
        }),

        # Progress indicator
        html.Div([
            html.Div(
                style={
                    'width': '100%',
                    'height': '4px',
                    'backgroundColor': 'rgba(71, 85, 105, 0.5)',
                    'borderRadius': '9999px',
                    'overflow': 'hidden'
                },
                children=html.Div(
                    style={
                        'height': '100%',
                        'backgroundColor': '#6366f1',  # indigo-500
                        'width': f'{((workflow_steps.index(next((s for s in workflow_steps if s["name"] == selected_page), workflow_steps[0])) + 1) / len(workflow_steps)) * 100}%',
                        'transition': 'width 0.3s'
                    }
                )
            ),
            html.Div(
                f'{((workflow_steps.index(next((s for s in workflow_steps if s["name"] == selected_page), workflow_steps[0])) + 1) / len(workflow_steps)) * 100:.0f}% Complete',
                style={
                    'fontSize': '0.625rem',
                    'color': '#94a3b8',
                    'textAlign': 'center',
                    'marginTop': '0.5rem'
                }
            )
        ], style={
            'marginTop': '1rem',
            'padding': '0 0.5rem'
        })
    ], style={
        'height': '100%',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'stretch',
        'paddingTop': '1rem'
    })
