# """
# Sidebar Component - Navigation Menu
# Converted from React Sidebar component to Dash
# """

# from dash import html, dcc
# import dash_bootstrap_components as dbc

# def create_sidebar(selected_page='Home', collapsed=False):
#     """
#     Create the sidebar navigation menu

#     Args:
#         selected_page: Currently selected page name
#         collapsed: Whether sidebar is collapsed
#     """

#     # Menu structure (matching React version)
#     menu_items = [
#         {
#             'name': 'Home',
#             'icon': '🏠',
#             'type': 'single'
#         },
#         {
#             'name': 'Projects',
#             'icon': '📁',
#             'type': 'dropdown',
#             'children': [
#                 {'name': 'Create Project', 'icon': '📝'},
#                 {'name': 'Load Project', 'icon': '📂'}
#             ]
#         },
#         {
#             'name': 'Demand Forecasting',
#             'icon': '📈',
#             'type': 'dropdown',
#             'children': [
#                 {'name': 'Demand Projection', 'icon': '📊'},
#                 {'name': 'Demand Visualization', 'icon': '📉'}
#             ]
#         },
#         {
#             'name': 'Load Profiles',
#             'icon': '⚡',
#             'type': 'dropdown',
#             'children': [
#                 {'name': 'Generate Profiles', 'icon': '🔧'},
#                 {'name': 'Analyze Profiles', 'icon': '🔍'}
#             ]
#         },
#         {
#             'name': 'PyPSA Suite',
#             'icon': '🔌',
#             'type': 'dropdown',
#             'children': [
#                 {'name': 'Model Config', 'icon': '⚙️'},
#                 {'name': 'View Results', 'icon': '📊'}
#             ]
#         }
#     ]

#     bottom_items = [
#         {'name': 'Settings', 'icon': '⚙️'},
#         {'name': 'Other Tools', 'icon': '🔧'}
#     ]

#     def create_nav_button(item_name, icon, is_child=False):
#         """Create a navigation button"""
#         is_active = selected_page == item_name

#         button_style = {
#             'width': '100%',
#             'display': 'flex',
#             'alignItems': 'center',
#             'gap': '1rem',
#             'padding': '0.5rem' if not is_child else '0.375rem',
#             'borderRadius': '0.5rem',
#             'border': 'none',
#             'cursor': 'pointer',
#             'transition': 'all 0.2s',
#             'backgroundColor': 'rgba(99, 102, 241, 0.1)' if is_active else 'transparent',
#             'color': '#a5b4fc' if is_active else '#cbd5e1',
#             'fontSize': '0.875rem' if not is_child else '0.8125rem',
#             'fontWeight': '600' if is_active and not is_child else '500',
#             'justifyContent': 'center' if collapsed else 'flex-start',
#             'marginLeft': '1.5rem' if is_child and not collapsed else '0'
#         }

#         hover_style = {
#             **button_style,
#             'backgroundColor': 'rgba(71, 85, 105, 0.5)',
#             'color': '#ffffff'
#         }

#         return html.Button(
#             [
#                 html.Span(icon, style={'fontSize': '1.25rem'}),
#                 html.Span(item_name, style={'display': 'none' if collapsed else 'inline'})
#             ],
#             id={'type': 'nav-link', 'page': item_name},
#             style=button_style,
#             className='nav-button'
#         )

#     def create_dropdown_section(item):
#         """Create a dropdown menu section"""
#         is_parent_active = any(child['name'] == selected_page for child in item.get('children', []))

#         section_children = [
#             html.Button(
#                 [
#                     html.Div([
#                         html.Span(item['icon'], style={'fontSize': '1.25rem'}),
#                         html.Span(item['name'], style={'display': 'none' if collapsed else 'inline', 'marginLeft': '1rem'})
#                     ], style={'display': 'flex', 'alignItems': 'center'}),
#                     html.Span('▼', style={
#                         'fontSize': '0.75rem',
#                         'display': 'none' if collapsed else 'inline',
#                         'transition': 'transform 0.3s'
#                     }) if not collapsed else None
#                 ],
#                 id={'type': 'dropdown-toggle', 'name': item['name']},
#                 style={
#                     'width': '100%',
#                     'display': 'flex',
#                     'alignItems': 'center',
#                     'justifyContent': 'space-between' if not collapsed else 'center',
#                     'padding': '0.5rem',
#                     'borderRadius': '0.5rem',
#                     'border': 'none',
#                     'cursor': 'pointer',
#                     'backgroundColor': 'rgba(99, 102, 241, 0.1)' if is_parent_active else 'transparent',
#                     'color': '#a5b4fc' if is_parent_active else '#cbd5e1',
#                     'fontSize': '0.875rem',
#                     'fontWeight': '500',
#                     'transition': 'all 0.2s'
#                 },
#                 className='dropdown-toggle-btn'
#             )
#         ]

#         # Add children if not collapsed
#         if not collapsed and item.get('children'):
#             children_div = html.Div(
#                 [create_nav_button(child['name'], child['icon'], is_child=True)
#                  for child in item['children']],
#                 style={
#                     'marginTop': '0.25rem',
#                     'paddingLeft': '0.75rem',
#                     'borderLeft': '2px solid rgba(71, 85, 105, 1)',
#                     'marginLeft': '1.5rem',
#                     'display': 'flex',
#                     'flexDirection': 'column',
#                     'gap': '0.125rem'
#                 }
#             )
#             section_children.append(children_div)

#         return html.Div(section_children, style={'marginBottom': '0.375rem'})

#     # Build sidebar content
#     sidebar_content = []

#     # Home button at top
#     sidebar_content.append(
#         html.Div(
#             create_nav_button('Home', '🏠'),
#             style={'padding': '1rem', 'paddingBottom': '0.5rem'}
#         )
#     )

#     # Main navigation
#     nav_section = html.Nav([
#         create_dropdown_section(item) if item['type'] == 'dropdown'
#         else html.Div(create_nav_button(item['name'], item['icon']), style={'marginBottom': '0.375rem'})
#         for item in menu_items if item['name'] != 'Home'
#     ], style={'padding': '0 1rem 1rem 1rem', 'display': 'flex', 'flexDirection': 'column', 'gap': '0.375rem'})

#     sidebar_content.append(nav_section)

#     # Spacer
#     sidebar_content.append(html.Div(style={'flexGrow': 1}))

#     # Bottom section
#     bottom_section = html.Div([
#         create_nav_button(item['name'], item['icon'])
#         for item in bottom_items
#     ] + [
#         html.Button(
#             [
#                 html.Span('⬅️' if not collapsed else '➡️', style={'fontSize': '1.25rem'})
#             ],
#             id='toggle-sidebar-btn',
#             style={
#                 'width': '100%',
#                 'display': 'flex',
#                 'alignItems': 'center',
#                 'justifyContent': 'center',
#                 'padding': '0.5rem',
#                 'borderRadius': '0.5rem',
#                 'border': 'none',
#                 'cursor': 'pointer',
#                 'backgroundColor': 'transparent',
#                 'color': '#94a3b8',
#                 'fontSize': '0.875rem',
#                 'fontWeight': '500',
#                 'transition': 'all 0.2s',
#                 'marginTop': '0.25rem'
#             }
#         )
#     ], style={
#         'padding': '0.75rem 1rem',
#         'borderTop': '1px solid rgba(71, 85, 105, 0.5)',
#         'display': 'flex',
#         'flexDirection': 'column',
#         'gap': '0.25rem'
#     })

#     sidebar_content.append(bottom_section)

#     return html.Div(
#         sidebar_content,
#         style={
#             'height': '100%',
#             'display': 'flex',
#             'flexDirection': 'column',
#             'overflow': 'hidden' if collapsed else 'auto'
#         }
#     )
from dash import html, dcc
import dash_bootstrap_components as dbc

# Style constants for maintainability (modern formal theme: indigo on slate)
THEME = {
    'bg': 'rgba(30, 41, 59, 0.98)',
    'active_bg': 'rgba(99, 102, 241, 0.12)',
    'hover_bg': 'rgba(71, 85, 105, 0.6)',
    'text': '#94a3b8',
    'active_text': '#e0e7ff',
    'border': 'rgba(71, 85, 105, 0.2)',
    'accent_border': 'rgba(99, 102, 241, 0.3)',
    'shadow': '0 1px 2px rgba(0, 0, 0, 0.05)',
    'focus_shadow': '0 0 0 2px rgba(99, 102, 241, 0.5)'
}

SIDEBAR_WIDTHS = {'expanded': '256px', 'collapsed': '72px'}  # Suggested widths for caller

def create_sidebar(selected_page='Home', collapsed=False):
    """
    Create the sidebar navigation menu
    Args:
        selected_page: Currently selected page name
        collapsed: Whether sidebar is collapsed (text hidden, icons only)
    Usage Note: Set container width to SIDEBAR_WIDTHS['collapsed' if collapsed else 'expanded']
    """
    # Menu structure (matching React version)
    menu_items = [
        {
            'name': 'Home',
            'icon': '🏠',
            'type': 'single'
        },
        {
            'name': 'Projects',
            'icon': '📁',
            'type': 'dropdown',
            'children': [
                {'name': 'Create Project', 'icon': '📝'},
                {'name': 'Load Project', 'icon': '📂'}
            ]
        },
        {
            'name': 'Demand Forecasting',
            'icon': '📈',
            'type': 'dropdown',
            'children': [
                {'name': 'Demand Projection', 'icon': '📊'},
                {'name': 'Demand Visualization', 'icon': '📉'}
            ]
        },
        {
            'name': 'Load Profiles',
            'icon': '⚡',
            'type': 'dropdown',
            'children': [
                {'name': 'Generate Profiles', 'icon': '🔧'},
                {'name': 'Analyze Profiles', 'icon': '🔍'}
            ]
        },
        {
            'name': 'PyPSA Suite',
            'icon': '🔌',
            'type': 'dropdown',
            'children': [
                {'name': 'Model Config', 'icon': '⚙️'},
                {'name': 'View Results', 'icon': '📊'}
            ]
        }
    ]
    bottom_items = [
        {'name': 'Settings', 'icon': '⚙️'},
        {'name': 'Other Tools', 'icon': '🔧'}
    ]

    def get_base_style(is_active=False, is_child=False, is_dropdown=False, extra_overrides={}):
        """Generate base style for buttons (DRY)"""
        style = {
            'width': '100%',
            'display': 'flex',
            'alignItems': 'center',
            'gap': '0.375rem',
            'padding': '0.4rem 0.625rem' if not is_child else '0.3rem 0.625rem 0.3rem 1.75rem',
            'borderRadius': '0.25rem',
            'border': 'none',
            'cursor': 'pointer',
            'transition': 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            'backgroundColor': THEME['active_bg'] if is_active else 'transparent',
            'color': THEME['active_text'] if is_active else THEME['text'],
            'fontSize': '0.7rem',
            'fontWeight': '600' if is_active else '400',
            'justifyContent': 'center' if collapsed else 'flex-start',
            'marginLeft': '0',
            'position': 'relative',
            'lineHeight': '1.25',
            'boxShadow': THEME['shadow'],
            'outline': 'none'
        }
        if is_active:
            style['boxShadow'] = f'inset 2px 0 0 {THEME["accent_border"]}, {THEME["shadow"]}'
        if is_dropdown and not collapsed:
            style['justifyContent'] = 'space-between'
        style.update(extra_overrides)
        return style

    def create_nav_button(item_name, icon, is_child=False):
        """Create a navigation button"""
        is_active = selected_page == item_name
        base_style = get_base_style(is_active=is_active, is_child=is_child)
        
        icon_style = {'fontSize': '0.875rem' if collapsed else '0.9375rem', 'flexShrink': 0, 'transition': 'all 0.25s'}
        text_style = {'display': 'none' if collapsed else 'inline', 'transition': 'opacity 0.25s', 'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}
        
        aria_props = {'aria-label': f"Navigate to {item_name}"}
        
        return html.Button(
            [
                html.Span(icon, style=icon_style),
                html.Span(item_name, style=text_style)
            ],
            id={'type': 'nav-link', 'page': item_name},
            style=base_style,
            title=item_name if collapsed else '',
            role='button',
            className='nav-button',
            **aria_props
        )

    def create_dropdown_section(item):
        """Create a dropdown menu section"""
        is_parent_active = any(child['name'] == selected_page for child in item.get('children', []))
        
        # Formal chevron with rotation
        chevron_style = {
            'fontSize': '0.625rem',
            'transition': 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            'transform': 'rotate(90deg)' if not collapsed else 'rotate(0deg)',
            'display': 'inline-flex' if not collapsed else 'none',
            'alignItems': 'center',
            'justifyContent': 'center',
            'width': '0.75rem',
            'height': '0.75rem',
            'marginLeft': 'auto',
            'color': THEME['text']
        }
        chevron = html.Span('▸', style=chevron_style)
        
        parent_icon_style = {'fontSize': '0.875rem' if collapsed else '0.9375rem', 'flexShrink': 0}
        parent_text_style = {'display': 'none' if collapsed else 'inline', 'marginLeft': '0.375rem', 'fontWeight': '400', 'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}
        
        parent_content = [
            html.Div([
                html.Span(item['icon'], style=parent_icon_style),
                html.Span(item['name'], style=parent_text_style)
            ], style={'display': 'flex', 'alignItems': 'center', 'flex': 1}),
            chevron
        ] if not collapsed else [html.Span(item['icon'], style={'fontSize': '0.875rem'})]
        
        dropdown_overrides = {'justifyContent': 'center'} if collapsed else {}
        base_style = get_base_style(is_active=is_parent_active, is_dropdown=True, extra_overrides=dropdown_overrides)
        
        aria_props = {'aria-label': f"Toggle {item['name']} section"}
        
        section_children = [
            html.Button(
                parent_content,
                id={'type': 'dropdown-toggle', 'name': item['name']},
                style=base_style,
                title=item['name'] if collapsed else '',
                role='button',
                className='dropdown-toggle-btn',
                **aria_props
            )
        ]
        # Compact children (hidden in collapsed)
        if not collapsed and item.get('children'):
            children_div = html.Div(
                [create_nav_button(child['name'], child['icon'], is_child=True)
                 for child in item['children']],
                style={
                    'marginTop': '0.125rem',
                    'paddingLeft': '0.25rem',
                    'borderLeft': f'1px solid {THEME["accent_border"]}',
                    'display': 'flex',
                    'flexDirection': 'column',
                    'gap': '0.0625rem',
                    'transition': 'all 0.25s ease'
                }
            )
            section_children.append(children_div)
        return html.Div(section_children, style={'marginBottom': '0.125rem'})

    # Build sidebar content - ultra-compact overall
    sidebar_content = []
    # Home button at top
    sidebar_content.append(
        html.Div(
            create_nav_button('Home', '🏠'),
            style={'padding': '0.75rem 0.625rem 0.5rem 0.625rem'}
        )
    )
    # Main navigation
    nav_section = html.Nav([
        create_dropdown_section(item) if item['type'] == 'dropdown'
        else html.Div(create_nav_button(item['name'], item['icon']), style={'marginBottom': '0.125rem'})
        for item in menu_items if item['name'] != 'Home'
    ], style={'padding': '0 0.625rem 0.75rem 0.625rem', 'display': 'flex', 'flexDirection': 'column', 'gap': '0.125rem'})
    sidebar_content.append(nav_section)
    # Spacer
    sidebar_content.append(html.Div(style={'flexGrow': 1}))
    # Bottom section
    toggle_icon = '↩️' if not collapsed else '→'
    toggle_title = 'Collapse sidebar' if not collapsed else 'Expand'
    toggle_aria = {'aria-label': 'Toggle sidebar visibility'}
    
    bottom_section = html.Div([
        create_nav_button(item['name'], item['icon'])
        for item in bottom_items
    ] + [
        html.Button(
            [
                html.Span(toggle_icon, style={'fontSize': '0.875rem', 'transition': 'all 0.25s'})
            ],
            id='toggle-sidebar-btn',
            style=get_base_style(extra_overrides={
                'justifyContent': 'center',
                'padding': '0.4rem 0.625rem',
                'marginTop': '0.125rem',
                'backgroundColor': 'transparent'
            }),
            title=toggle_title,
            role='button',
            **toggle_aria
        )
    ], style={
        'padding': '0.5rem 0.625rem 0.75rem 0.625rem',
        'borderTop': f'1px solid {THEME["border"]}',
        'display': 'flex',
        'flexDirection': 'column',
        'gap': '0.125rem'
    })
    sidebar_content.append(bottom_section)
    
    aria_props_outer = {'aria-label': 'Main navigation menu'}
    
    return html.Div(
        sidebar_content,
        style={
            'height': '100%',
            'display': 'flex',
            'flexDirection': 'column',
            'overflowY': 'auto' if not collapsed else 'hidden',
            'backgroundColor': THEME['bg'],
            'backdropFilter': 'blur(16px)',
            'borderRight': f'1px solid {THEME["border"]}'
        },
        role='navigation',
        **aria_props_outer
    )