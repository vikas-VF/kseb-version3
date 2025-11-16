# """
# Workflow Stepper Component - Right sidebar showing workflow progress
# Converted from React WorkflowStepper component to Dash
# """

# from dash import html

# def create_workflow_stepper(selected_page='Home', active_project=None):
#     """
#     Create the workflow stepper sidebar

#     Args:
#         selected_page: Currently selected page
#         active_project: Active project dict
#     """

#     # Define workflow steps
#     workflow_steps = [
#         {'name': 'Create Project', 'icon': '📁', 'group': 'Projects'},
#         {'name': 'Demand Projection', 'icon': '📈', 'group': 'Forecasting'},
#         {'name': 'Demand Visualization', 'icon': '📊', 'group': 'Forecasting'},
#         {'name': 'Generate Profiles', 'icon': '⚡', 'group': 'Profiles'},
#         {'name': 'Analyze Profiles', 'icon': '🔍', 'group': 'Profiles'},
#         {'name': 'Model Config', 'icon': '⚙️', 'group': 'PyPSA'},
#         {'name': 'View Results', 'icon': '📉', 'group': 'PyPSA'}
#     ]

#     def create_step_card(step, index):
#         """Create a single workflow step card"""
#         is_active = selected_page == step['name']
#         step_num = index + 1

#         card_style = {
#             'width': '100%',
#             'padding': '0.75rem 0.5rem',
#             'marginBottom': '0.75rem',
#             'borderRadius': '0.5rem',
#             'backgroundColor': '#4f46e5' if is_active else 'rgba(71, 85, 105, 0.3)',  # indigo-600 or slate-700/30
#             'border': '2px solid #6366f1' if is_active else '2px solid transparent',
#             'cursor': 'pointer',
#             'transition': 'all 0.2s',
#             'display': 'flex',
#             'flexDirection': 'column',
#             'alignItems': 'center',
#             'gap': '0.25rem',
#             'boxShadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1)' if is_active else 'none'
#         }

#         return html.Button(
#             [
#                 # Step number
#                 html.Div(
#                     str(step_num),
#                     style={
#                         'width': '24px',
#                         'height': '24px',
#                         'borderRadius': '50%',
#                         'backgroundColor': '#ffffff' if is_active else '#475569',
#                         'color': '#4f46e5' if is_active else '#e2e8f0',
#                         'display': 'flex',
#                         'alignItems': 'center',
#                         'justifyContent': 'center',
#                         'fontSize': '0.75rem',
#                         'fontWeight': '700',
#                         'marginBottom': '0.25rem'
#                     }
#                 ),
#                 # Icon
#                 html.Div(
#                     step['icon'],
#                     style={
#                         'fontSize': '1.5rem',
#                         'marginBottom': '0.25rem'
#                     }
#                 ),
#                 # Step name (vertical text)
#                 html.Div(
#                     step['name'],
#                     style={
#                         'fontSize': '0.625rem',
#                         'fontWeight': '600',
#                         'color': '#ffffff' if is_active else '#cbd5e1',
#                         'textAlign': 'center',
#                         'lineHeight': '1.2',
#                         'maxWidth': '60px',
#                         'wordWrap': 'break-word'
#                     }
#                 ),
#                 # Group label
#                 html.Div(
#                     step['group'],
#                     style={
#                         'fontSize': '0.5rem',
#                         'color': '#94a3b8',
#                         'marginTop': '0.25rem',
#                         'fontWeight': '500'
#                     }
#                 )
#             ],
#             id={'type': 'nav-link', 'page': step['name']},
#             style=card_style,
#             className='workflow-step-card'
#         )

#     # Disable if no project is active (except for Create Project)
#     if not active_project:
#         # Only show Create Project step when no project is active
#         return html.Div([
#             html.Div(
#                 '🚀',
#                 style={
#                     'fontSize': '2rem',
#                     'textAlign': 'center',
#                     'marginBottom': '1rem',
#                     'opacity': '0.5'
#                 }
#             ),
#             html.Div(
#                 'Workflow',
#                 style={
#                     'fontSize': '0.75rem',
#                     'fontWeight': '700',
#                     'color': '#94a3b8',
#                     'textAlign': 'center',
#                     'marginBottom': '1.5rem',
#                     'letterSpacing': '0.05em'
#                 }
#             ),
#             create_step_card(workflow_steps[0], 0),  # Only Create Project
#             html.Div(
#                 'Load a project to see workflow',
#                 style={
#                     'fontSize': '0.625rem',
#                     'color': '#64748b',
#                     'textAlign': 'center',
#                     'marginTop': '1rem',
#                     'lineHeight': '1.4'
#                 }
#             )
#         ], style={
#             'height': '100%',
#             'display': 'flex',
#             'flexDirection': 'column',
#             'alignItems': 'center',
#             'paddingTop': '1rem'
#         })

#     # Full workflow when project is active
#     return html.Div([
#         # Header
#         html.Div(
#             '🚀',
#             style={
#                 'fontSize': '2rem',
#                 'textAlign': 'center',
#                 'marginBottom': '1rem'
#             }
#         ),
#         html.Div(
#             'Workflow',
#             style={
#                 'fontSize': '0.75rem',
#                 'fontWeight': '700',
#                 'color': '#a5b4fc',  # indigo-400
#                 'textAlign': 'center',
#                 'marginBottom': '1.5rem',
#                 'letterSpacing': '0.05em'
#             }
#         ),

#         # Steps
#         html.Div([
#             create_step_card(step, index)
#             for index, step in enumerate(workflow_steps)
#         ], style={
#             'display': 'flex',
#             'flexDirection': 'column',
#             'gap': '0.5rem',
#             'overflowY': 'auto',
#             'flexGrow': 1
#         }),

#         # Progress indicator
#         html.Div([
#             html.Div(
#                 style={
#                     'width': '100%',
#                     'height': '4px',
#                     'backgroundColor': 'rgba(71, 85, 105, 0.5)',
#                     'borderRadius': '9999px',
#                     'overflow': 'hidden'
#                 },
#                 children=html.Div(
#                     style={
#                         'height': '100%',
#                         'backgroundColor': '#6366f1',  # indigo-500
#                         'width': f'{((workflow_steps.index(next((s for s in workflow_steps if s["name"] == selected_page), workflow_steps[0])) + 1) / len(workflow_steps)) * 100}%',
#                         'transition': 'width 0.3s'
#                     }
#                 )
#             ),
#             html.Div(
#                 f'{((workflow_steps.index(next((s for s in workflow_steps if s["name"] == selected_page), workflow_steps[0])) + 1) / len(workflow_steps)) * 100:.0f}% Complete',
#                 style={
#                     'fontSize': '0.625rem',
#                     'color': '#94a3b8',
#                     'textAlign': 'center',
#                     'marginTop': '0.5rem'
#                 }
#             )
#         ], style={
#             'marginTop': '1rem',
#             'padding': '0 0.5rem'
#         })
#     ], style={
#         'height': '100%',
#         'display': 'flex',
#         'flexDirection': 'column',
#         'alignItems': 'stretch',
#         'paddingTop': '1rem'
#     })
"""
Workflow Stepper Component - Right sidebar showing workflow progress
Converted from React WorkflowStepper component to Dash
"""

from dash import html

# Theme constants (matching sidebar for consistency)
THEME = {
    'bg': 'rgba(30, 41, 59, 0.98)',
    'active_bg': '#4f46e5',  # indigo-600
    'active_border': '#6366f1',  # indigo-500
    'card_bg': 'rgba(71, 85, 105, 0.3)',  # slate-700/30
    'text': '#94a3b8',  # slate-400
    'active_text': '#e0e7ff',  # slate-100
    'header_text': '#a5b4fc',  # indigo-400
    'progress_bg': 'rgba(71, 85, 105, 0.5)',  # slate-500/50
    'progress_fill': '#6366f1',  # indigo-500
    'shadow': '0 1px 3px rgba(0, 0, 0, 0.1)',
    'active_shadow': '0 4px 6px -1px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05)'
}

def create_workflow_stepper(selected_page='Home', active_project=None):
    """
    Create the workflow stepper sidebar

    Args:
        selected_page: Currently selected page
        active_project: Active project dict
    """
    # Define workflow steps
    workflow_steps = [
        {'name': 'Create Project',  'group': 'Projects'},
        {'name': 'Demand Projection', 'group': 'Forecasting'},
        {'name': 'Demand Visualization', 'group': 'Forecasting'},
        {'name': 'Generate Profiles',  'group': 'Profiles'},
        {'name': 'Analyze Profiles',  'group': 'Profiles'},
        {'name': 'Model Config',  'group': 'PyPSA'},
        {'name': 'View Results',  'group': 'PyPSA'}
    ]

    def get_progress_index():
        """Get the current step index safely"""
        try:
            return next((i for i, s in enumerate(workflow_steps) if s['name'] == selected_page), 0)
        except StopIteration:
            return 0

    def create_step_card(step, index):
        """Create a single workflow step card"""
        is_active = selected_page == step['name']
        step_num = index + 1

        # Compact, formal card style
        card_style = {
            'width': '100%',
            'padding': '0.5rem 0.375rem',  # Reduced for compactness
            'marginBottom': '0.375rem',
            'borderRadius': '0.375rem',
            'backgroundColor': THEME['active_bg'] if is_active else THEME['card_bg'],
            'border': f'2px solid {THEME["active_border"]}' if is_active else '2px solid transparent',
            'cursor': 'pointer',
            'transition': 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'gap': '0.25rem',
            'boxShadow': THEME['active_shadow'] if is_active else THEME['shadow'],
            'outline': 'none',
            'position': 'relative',
            'overflow': 'hidden'
        }
        if is_active:
            card_style['transform'] = 'scale(1.02)'

        # Hover effect (inline, as Dash doesn't support :hover easily)
        hover_style = {**card_style, 'backgroundColor': THEME['active_bg'], 'transform': 'scale(1.02)'}

        step_num_style = {
            'width': '20px',
            'height': '20px',
            'borderRadius': '50%',
            'backgroundColor': '#ffffff' if is_active else '#475569',
            'color': THEME['active_bg'] if is_active else '#e2e8f0',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'fontSize': '0.6875rem',
            'fontWeight': '700',
            'lineHeight': 1
        }

 

        name_style = {
            'fontSize': '0.5625rem',  # Compact
            'fontWeight': '600',
            'color': THEME['active_text'] if is_active else THEME['text'],
            'textAlign': 'center',
            'lineHeight': '1.2',
            'maxWidth': '50px',
            'wordWrap': 'break-word',
            'whiteSpace': 'normal'
        }

        group_style = {
            'fontSize': '0.4375rem',
            'color': THEME['text'],
            'marginTop': '0.125rem',
            'fontWeight': '500',
            'opacity': 0.8
        }

        aria_label = f"Go to step {step_num}: {step['name']} ({step['group']})"
        return html.Button(
            [
                html.Div(str(step_num), style=step_num_style),
         
                html.Div(step['name'], style=name_style),
                html.Div(step['group'], style=group_style)
            ],
            id={'type': 'nav-link', 'page': step['name']},
            style=card_style,
            **{'aria-label': aria_label},
            role='button',
            className='workflow-step-card'
        )

    # No project: Minimal view, only Create Project
    if not active_project:
        return html.Div([

            create_step_card(workflow_steps[0], 0),
            html.Div(
                'Load a project to see full workflow',
                style={
                    'fontSize': '0.5625rem',
                    'color': THEME['text'],
                    'textAlign': 'center',
                    'marginTop': '0.75rem',
                    'lineHeight': '1.3',
                    'padding': '0 0.5rem',
                    'opacity': 0.7
                }
            )
        ], style={
            'height': '100%',
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '1rem 0.5rem',
            'backgroundColor': THEME['bg']
        })

    # Full workflow: Compact vertical stack
    current_index = get_progress_index()
    progress_percent = ((current_index + 1) / len(workflow_steps)) * 100

    return html.Div([
        # Header - more formal


        # Steps container - tight spacing, no scroll needed (7 steps ~200px total)
        html.Div([
            create_step_card(step, index)
            for index, step in enumerate(workflow_steps)
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '0.25rem',  # Reduced
            'flexGrow': 1,
            'paddingBottom': '0.5rem'
        }),

        # Progress bar - sleek, at bottom
        html.Div([
            html.Div(
                style={
                    'width': '100%',
                    'height': '3px',  # Thinner
                    'backgroundColor': THEME['progress_bg'],
                    'borderRadius': '9999px',
                    'overflow': 'hidden',
                    'transition': 'all 0.3s ease'
                },
                children=html.Div(
                    style={
                        'height': '100%',
                        'backgroundColor': THEME['progress_fill'],
                        'width': f'{progress_percent}%',
                        'transition': 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                    }
                )
            ),
            html.Div(
                f'{progress_percent:.0f}% Complete',
                style={
                    'fontSize': '0.5625rem',
                    'color': THEME['text'],
                    'textAlign': 'center',
                    'marginTop': '0.375rem',
                    'fontWeight': '500'
                }
            )
        ], style={
            'marginTop': 'auto',
            'padding': '0.5rem 0.375rem 0.5rem',
            'backgroundColor': 'rgba(71, 85, 105, 0.1)'
        })
    ], style={
        'height': '100%',
        'display': 'flex',
        'flexDirection': 'column',
        'backgroundColor': THEME['bg'],
        'padding': '0.75rem 0.5rem',  # Overall padding reduced
        'borderLeft': f'1px solid {THEME["progress_bg"]}',
        'overflow': 'hidden'  # No scroll, fits viewport
    })