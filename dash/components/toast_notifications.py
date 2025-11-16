"""
Toast Notification System for Dash
Implements React+FastAPI toast notification pattern using dash-bootstrap-components
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Literal, Optional

# Toast icons by type
TOAST_ICONS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️'
}

# Toast colors by type
TOAST_COLORS = {
    'success': '#10b981',  # green-500
    'error': '#ef4444',    # red-500
    'warning': '#f59e0b',  # amber-500
    'info': '#3b82f6'      # blue-500
}

def create_toast(
    message: str,
    toast_type: Literal['success', 'error', 'warning', 'info'] = 'info',
    duration: int = 4000,
    toast_id: Optional[str] = None
):
    """
    Create a toast notification (React+FastAPI pattern).

    Args:
        message: Message to display
        toast_type: Type of toast (success, error, warning, info)
        duration: Duration in milliseconds
        toast_id: Optional custom ID for the toast

    Returns:
        dbc.Toast component
    """
    if toast_id is None:
        import uuid
        toast_id = f'toast-{uuid.uuid4()}'

    icon = TOAST_ICONS.get(toast_type, 'ℹ️')
    color = TOAST_COLORS.get(toast_type, TOAST_COLORS['info'])

    return dbc.Toast(
        message,
        id=toast_id,
        header=f"{icon} {toast_type.capitalize()}",
        is_open=True,
        dismissable=True,
        duration=duration,
        icon=toast_type,
        style={
            'position': 'fixed',
            'top': '80px',
            'right': '20px',
            'minWidth': '300px',
            'zIndex': 9999,
            'boxShadow': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
        },
        className='toast-notification'
    )


def create_toast_container():
    """
    Create toast container for displaying notifications.

    Returns:
        html.Div containing toast notification area
    """
    return html.Div(
        id='toast-container',
        children=[],
        style={
            'position': 'fixed',
            'top': '80px',
            'right': '20px',
            'zIndex': 9999,
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '0.5rem',
            'maxWidth': '400px'
        }
    )


def show_toast(message: str, toast_type: str = 'info'):
    """
    Helper function to create toast for callback returns.

    Usage in callbacks:
        return show_toast('Project created successfully!', 'success')

    Args:
        message: Message to display
        toast_type: Type of toast

    Returns:
        Toast component ready for callback Output
    """
    return create_toast(message, toast_type)


# Common toast messages for reuse
TOAST_MESSAGES = {
    'project_created': ('Project created successfully!', 'success'),
    'project_loaded': ('Project loaded successfully!', 'success'),
    'project_error': ('Failed to load project', 'error'),
    'forecast_started': ('Demand forecast started', 'info'),
    'forecast_complete': ('Forecast completed successfully!', 'success'),
    'forecast_error': ('Forecast failed', 'error'),
    'profile_started': ('Load profile generation started', 'info'),
    'profile_complete': ('Profiles generated successfully!', 'success'),
    'profile_error': ('Profile generation failed', 'error'),
    'pypsa_started': ('PyPSA optimization started', 'info'),
    'pypsa_complete': ('Optimization completed successfully!', 'success'),
    'pypsa_error': ('Optimization failed', 'error'),
    'pypsa_cancelled': ('Optimization cancelled', 'warning'),
    'save_success': ('Changes saved successfully!', 'success'),
    'save_error': ('Failed to save changes', 'error'),
    'invalid_input': ('Please check your input values', 'warning'),
    'no_project': ('Please load or create a project first', 'warning'),
    'network_error': ('Network error. Please try again.', 'error'),
}


def get_toast_message(key: str, custom_message: Optional[str] = None):
    """
    Get a predefined toast message or use custom message.

    Args:
        key: Key from TOAST_MESSAGES
        custom_message: Optional custom message to override default

    Returns:
        Tuple of (message, type)
    """
    if custom_message:
        message, toast_type = TOAST_MESSAGES.get(key, (custom_message, 'info'))
        return (custom_message, toast_type)
    return TOAST_MESSAGES.get(key, ('Operation completed', 'info'))
