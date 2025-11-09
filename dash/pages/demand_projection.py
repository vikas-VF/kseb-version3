"""
Demand Projection Page - Complete Implementation
Full demand forecasting configuration with ML model selection
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

def layout(active_project=None):
    if not active_project:
        return dbc.Container([
            dbc.Alert([
                html.H4('⚠️ No Project Loaded', className='alert-heading'),
                html.P('Please load or create a project first to use demand forecasting.'),
                dbc.Button('Go to Projects', id={'type': 'nav-link', 'page': 'Load Project'}, color='primary')
            ], color='warning')
        ], className='p-4')
    
    return dbc.Container([
        html.H2('📈 Demand Forecasting - Configuration & Execution', className='mb-4',
               style={'fontWeight': '700', 'color': '#1e293b'}),
        
        # Stepper/Progress indicator
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Div([
                        html.Div('1️⃣', className='step-number'),
                        html.Span('Parse Excel', className='step-label')
                    ], className='step active'),
                    html.Div('→', className='step-arrow'),
                    html.Div([
                        html.Div('2️⃣', className='step-number'),
                        html.Span('Configure', className='step-label')
                    ], className='step'),
                    html.Div('→', className='step-arrow'),
                    html.Div([
                        html.Div('3️⃣', className='step-number'),
                        html.Span('Select Models', className='step-label')
                    ], className='step'),
                    html.Div('→', className='step-arrow'),
                    html.Div([
                        html.Div('4️⃣', className='step-number'),
                        html.Span('Execute', className='step-label')
                    ], className='step')
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-around'})
            ])
        ], className='mb-4'),
        
        dbc.Row([
            # Left column - Configuration
            dbc.Col([
                # Step 1: Parse Excel
                dbc.Card([
                    dbc.CardHeader(html.H5('1️⃣ Parse Input Excel File', className='mb-0')),
                    dbc.CardBody([
                        dbc.Label('Excel File'),
                        dcc.Upload(
                            id='upload-demand-excel',
                            children=dbc.Button('📁 Upload Excel File', color='secondary', className='w-100'),
                            multiple=False
                        ),
                        html.Div(id='excel-upload-status', className='mt-2'),
                        dbc.Button('Parse File', id='parse-excel-btn', color='primary', className='w-100 mt-3')
                    ])
                ], className='mb-3'),
                
                # Step 2: Configuration
                dbc.Card([
                    dbc.CardHeader(html.H5('2️⃣ Forecast Configuration', className='mb-0')),
                    dbc.CardBody([
                        dbc.Label('Scenario Name'),
                        dbc.Input(id='forecast-scenario-name', placeholder='e.g., Baseline_2025', className='mb-3'),
                        
                        dbc.Label('Target Year'),
                        dbc.Input(id='forecast-target-year', type='number', value=2030, className='mb-3'),
                        
                        dbc.Label('Base Year'),
                        dbc.Input(id='forecast-base-year', type='number', value=2024, className='mb-3'),
                        
                        dbc.Checklist(
                            id='exclude-covid-years',
                            options=[{'label': 'Exclude COVID years (2020-2021)', 'value': 'exclude'}],
                            value=['exclude'],
                            className='mb-3'
                        )
                    ])
                ], className='mb-3'),
                
                # Step 3: Model Selection
                dbc.Card([
                    dbc.CardHeader(html.H5('3️⃣ Select Forecasting Models', className='mb-0')),
                    dbc.CardBody([
                        dbc.Checklist(
                            id='forecast-models-selection',
                            options=[
                                {'label': '📊 Simple Linear Regression (SLR)', 'value': 'SLR'},
                                {'label': '📈 Multiple Linear Regression (MLR)', 'value': 'MLR'},
                                {'label': '⚖️ Weighted Average Method (WAM)', 'value': 'WAM'},
                                {'label': '🔄 Time Series (ARIMA)', 'value': 'ARIMA'}
                            ],
                            value=['SLR', 'MLR'],
                            className='mb-3'
                        ),
                        dbc.FormText('Select one or more models to run. Results will be compared.')
                    ])
                ], className='mb-3'),
                
                # Step 4: Execute
                dbc.Card([
                    dbc.CardHeader(html.H5('4️⃣ Execute Forecasting', className='mb-0')),
                    dbc.CardBody([
                        dbc.Button(
                            '🚀 Start Forecasting',
                            id='start-forecast-btn',
                            color='success',
                            size='lg',
                            className='w-100 fw-bold'
                        ),
                        html.Div(id='forecast-execution-status', className='mt-3')
                    ])
                ])
                
            ], width=12, lg=5),
            
            # Right column - Preview & Progress
            dbc.Col([
                # Sectors preview
                dbc.Card([
                    dbc.CardHeader(html.H5('📊 Sectors to Forecast', className='mb-0')),
                    dbc.CardBody(
                        html.Div(id='sectors-list-preview', children=[
                            dbc.Alert('Upload and parse Excel file to see sectors', color='info')
                        ])
                    )
                ], className='mb-3'),
                
                # Progress panel
                dbc.Card([
                    dbc.CardHeader(html.H5('⏳ Forecasting Progress', className='mb-0')),
                    dbc.CardBody([
                        html.Div(id='forecast-progress-panel', children=[
                            html.P('No forecast running', className='text-muted text-center')
                        ])
                    ])
                ], className='mb-3'),
                
                # Quick stats
                dbc.Card([
                    dbc.CardHeader(html.H5('📈 Quick Stats', className='mb-0')),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div('0', id='total-sectors-count', className='display-4 fw-bold text-primary'),
                                html.P('Total Sectors', className='text-muted')
                            ], className='text-center'),
                            dbc.Col([
                                html.Div('0', id='models-selected-count', className='display-4 fw-bold text-success'),
                                html.P('Models Selected', className='text-muted')
                            ], className='text-center')
                        ])
                    ])
                ])
            ], width=12, lg=7)
        ])
    ], fluid=True, className='p-4')
