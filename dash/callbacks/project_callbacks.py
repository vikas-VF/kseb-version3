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
    
    @app.callback(
        Output('create-project-output', 'children'),
        Output('active-project-store', 'data', allow_duplicate=True),
        Output('selected-page-store', 'data', allow_duplicate=True),
        Input('create-project-btn', 'n_clicks'),
        State('create-project-name-input', 'value'),
        State('create-project-path-input', 'value'),
        State('create-project-desc-input', 'value'),
        State('create-project-template', 'value'),
        prevent_initial_call=True
    )
    def create_project(n_clicks, name, path, description, template):
        if not n_clicks:
            return no_update, no_update, no_update
        
        if not name or not path:
            return dbc.Alert('❌ Please enter project name and path', color='danger'), no_update, no_update
        
        try:
            # Create project structure
            project_path = Path(path) / name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (project_path / 'inputs').mkdir(exist_ok=True)
            (project_path / 'results').mkdir(exist_ok=True)
            (project_path / 'results' / 'demand_forecasts').mkdir(exist_ok=True)
            (project_path / 'results' / 'load_profiles').mkdir(exist_ok=True)
            (project_path / 'results' / 'pypsa_optimization').mkdir(exist_ok=True)
            
            # Create project metadata
            metadata = {
                'name': name,
                'created': datetime.now().isoformat(),
                'description': description or '',
                'template': template
            }
            
            with open(project_path / 'project.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create README
            with open(project_path / 'README.md', 'w') as f:
                f.write(f"# {name}\n\n{description}\n\nCreated: {datetime.now().strftime('%Y-%m-%d')}\n")
            
            project_data = {
                'name': name,
                'path': str(project_path),
                **metadata
            }
            
            return (
                dbc.Alert([
                    html.H5('✅ Project Created Successfully!', className='alert-heading'),
                    html.P(f'Project: {name}'),
                    html.P(f'Location: {project_path}'),
                    html.Hr(),
                    dbc.Button('Go to Home', id={'type': 'nav-link', 'page': 'Home'}, color='primary')
                ], color='success'),
                project_data,
                'Home'
            )
            
        except Exception as e:
            return dbc.Alert(f'❌ Error creating project: {str(e)}', color='danger'), no_update, no_update
    
    @app.callback(
        Output('load-project-output', 'children'),
        Output('active-project-store', 'data', allow_duplicate=True),
        Output('selected-page-store', 'data', allow_duplicate=True),
        Input('load-project-btn', 'n_clicks'),
        State('load-project-path-input', 'value'),
        prevent_initial_call=True
    )
    def load_project(n_clicks, path):
        if not n_clicks or not path:
            return no_update, no_update, no_update
        
        try:
            project_path = Path(path)
            if not project_path.exists():
                return dbc.Alert(f'❌ Path does not exist: {path}', color='danger'), no_update, no_update
            
            # Try to load metadata
            metadata = {}
            metadata_file = project_path / 'project.json'
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
            
            project_name = metadata.get('name', project_path.name)
            project_data = {
                'name': project_name,
                'path': str(project_path),
                **metadata
            }
            
            return (
                dbc.Alert([
                    html.H5(f'✅ Project Loaded: {project_name}', className='alert-heading'),
                    html.P(f'📁 {project_path}'),
                    dbc.Button('Go to Home', id={'type': 'nav-link', 'page': 'Home'}, color='primary')
                ], color='success'),
                project_data,
                'Home'
            )
            
        except Exception as e:
            return dbc.Alert(f'❌ Error loading project: {str(e)}', color='danger'), no_update, no_update
