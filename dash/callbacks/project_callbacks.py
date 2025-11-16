"""
Project Management Callbacks - Complete Implementation
Handles project creation, loading, validation
"""
from dash import Input, Output, State, html, no_update
import dash_bootstrap_components as dbc
import json
from pathlib import Path
from datetime import datetime

def register_callbacks(app):
    # Note: create_project callback is now implemented in pages/create_project.py
    # to avoid duplicate callback conflicts and to use the correct component IDs
    # (project-name-input, project-location-input instead of create-project-name-input, create-project-path-input)

    # Note: load_project callback is now implemented in pages/load_project.py
    # to avoid duplicate callback conflicts and to use the correct output IDs
    pass
