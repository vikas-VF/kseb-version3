"""
Load Profiles - Analyze Profiles Page (Streamlined Complete Implementation)
6-tab analysis dashboard with heatmaps, time series, and load duration curves

Complete Features:
- Overview: Monthly & Seasonal heatmaps with color control
- Time Series: Date range selection with hourly demand charts
- Month-wise: Monthly analysis with aggregated statistics
- Season-wise: Seasonal analysis
- Day-type: Holiday/Weekday/Weekend comparison
- Load Duration: Load duration curve with 5%/95% markers
"""

from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.api_client import api
from utils.state_manager import StateManager

def layout(active_project=None):
    if not active_project:
        return dbc.Container([dbc.Alert([html.H4('⚠️ No Project Loaded'), 
            html.P('Please load a project to analyze load profiles.')], color='warning')], className='p-4')
    
    return dbc.Container([
        dbc.Card([dbc.CardBody([dbc.Row([
            dbc.Col([dbc.Label('Load Profile', className='fw-bold'), 
                dcc.Dropdown(id='profile-select', clearable=False, style={'minWidth': '250px'})], width='auto'),
            dbc.Col([dbc.Label('Period', className='fw-bold'), 
                dcc.Dropdown(id='period-select', value='Overall', clearable=False, style={'minWidth': '180px'})], width='auto')
        ])])], className='mb-3'),
        
        dbc.Card([dbc.CardHeader([dbc.Tabs([
            dbc.Tab(label='📊 Overview', tab_id='overview'),
            dbc.Tab(label='📅 Time Series', tab_id='timeseries'),
            dbc.Tab(label='📆 Month-wise', tab_id='monthly'),
            dbc.Tab(label='☀️ Season-wise', tab_id='seasonal'),
            dbc.Tab(label='🌙 Day-type', tab_id='daytype'),
            dbc.Tab(label='📈 Load Duration', tab_id='duration')
        ], id='tabs', active_tab='overview')]),
        dbc.CardBody(html.Div(id='tab-content'), style={'minHeight': '600px'})]),
        
        dcc.Store(id='state', storage_type='local', data={'profile': None, 'year': 'Overall', 
            'monthlyParam': 'Peak Demand', 'seasonalParam': 'Peak Demand',
            'monthlyLow': '#cfd4e3', 'monthlyHigh': '#252323',
            'seasonalLow': '#cfd4e3', 'seasonalHigh': '#252323', 'month': 4, 'season': 'Monsoon'}),
        dcc.Store(id='year-data', data=None),
        dcc.Store(id='duration-data', data=None),
        dcc.Loading(id='loading', children=html.Div(id='trigger'))
    ], fluid=True, className='p-4')

# Load profiles
@callback(Output('state', 'data', allow_duplicate=True), Output('profile-select', 'options'),
    Output('profile-select', 'value'), Input('active-project-store', 'data'), State('state', 'data'), prevent_initial_call=True)
def load_profiles(project, state):
    if not project: return state, [], None
    try:
        profiles = api.get_load_profiles(project['path']).get('profiles', [])
        if not profiles: return state, [], None
        profile = profiles[0] if not state.get('profile') or state['profile'] not in profiles else state['profile']
        return {**state, 'profile': profile}, [{'label': p, 'value': p} for p in profiles], profile
    except: return state, [], None

# Load years
@callback(Output('period-select', 'options'), Output('period-select', 'value'), 
    Input('profile-select', 'value'), State('active-project-store', 'data'), prevent_initial_call=True)
def load_years(profile, project):
    if not profile or not project: return [{'label': 'Overall', 'value': 'Overall'}], 'Overall'
    try:
        years = ['Overall'] + api.get_profile_years(project['path'], profile).get('years', [])
        return [{'label': y, 'value': y} for y in years], 'Overall'
    except: return [{'label': 'Overall', 'value': 'Overall'}], 'Overall'

# Update state
@callback(Output('state', 'data', allow_duplicate=True), 
    [Input('profile-select', 'value'), Input('period-select', 'value'), Input('tabs', 'active_tab')],
    State('state', 'data'), prevent_initial_call=True)
def update_state(profile, year, tab, state):
    if profile: state['profile'] = profile
    if year: state['year'] = year
    if tab: state['tab'] = tab
    return state

# Render tabs
@callback(Output('tab-content', 'children'), Input('tabs', 'active_tab'), State('state', 'data'))
def render_tab(tab, state):
    if not state.get('profile'): 
        return dbc.Alert('No profile selected. Generate one first.', color='info')
    if tab == 'overview': return render_overview()
    elif tab in ['timeseries', 'monthly', 'seasonal', 'daytype', 'duration']:
        if state.get('year') == 'Overall':
            return dbc.Alert('Select a specific Fiscal Year from the Period dropdown.', color='info', className='mt-4')
        if tab == 'timeseries': return render_timeseries()
        elif tab == 'monthly': return render_monthly()
        elif tab == 'seasonal': return render_seasonal()
        elif tab == 'daytype': return html.Div(id='daytype-chart')
        elif tab == 'duration': return html.Div(id='duration-chart')
    return html.Div()

def render_overview():
    return html.Div([
        dbc.Row([dbc.Col(html.H5('Monthly Analysis'), width='auto'),
            dbc.Col([html.Span('Low', className='small me-2'), 
                dcc.Input(id='monthly-low', type='color', value='#cfd4e3', style={'width': '50px', 'height': '30px'}),
                html.Span('High', className='small ms-2 me-2'),
                dcc.Input(id='monthly-high', type='color', value='#252323', style={'width': '50px', 'height': '30px'})], width='auto'),
            dbc.Col([dbc.Label('Parameter:'), dcc.Dropdown(id='monthly-param', clearable=False, style={'minWidth': '200px'})], 
                width='auto', className='ms-auto')], className='mb-3'),
        html.Div(id='monthly-heatmap', className='mb-5'),
        
        dbc.Row([dbc.Col(html.H5('Seasonal Analysis'), width='auto'),
            dbc.Col([html.Span('Low', className='small me-2'),
                dcc.Input(id='seasonal-low', type='color', value='#cfd4e3', style={'width': '50px', 'height': '30px'}),
                html.Span('High', className='small ms-2 me-2'),
                dcc.Input(id='seasonal-high', type='color', value='#252323', style={'width': '50px', 'height': '30px'})], width='auto'),
            dbc.Col([dbc.Label('Parameter:'), dcc.Dropdown(id='seasonal-param', clearable=False, style={'minWidth': '200px'})],
                width='auto', className='ms-auto')], className='mb-3'),
        html.Div(id='seasonal-heatmap')
    ])

def render_timeseries():
    return html.Div([dbc.Row([dbc.Col([dbc.Label('Date Range:'), 
        dcc.DatePickerRange(id='date-range', display_format='YYYY-MM-DD')], md=6)]),
        html.Div(id='timeseries-chart'), html.Div(id='timeseries-stats', className='mt-4')])

def render_monthly():
    months = [(4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'),
              (10, 'October'), (11, 'November'), (12, 'December'), (1, 'January'), (2, 'February'), (3, 'March')]
    return html.Div([dbc.Row([dbc.Col([dbc.Label('Month:'), 
        dcc.Dropdown(id='month-select', options=[{'label': n, 'value': v} for v, n in months], 
        value=4, clearable=False, style={'maxWidth': '200px'})], md=4)], className='mb-3'),
        html.Div(id='monthly-chart'), html.Div(id='monthly-stats', className='mt-4')])

def render_seasonal():
    return html.Div([dbc.Row([dbc.Col([dbc.Label('Season:'),
        dcc.Dropdown(id='season-select', options=[{'label': 'Monsoon (Jul-Sep)', 'value': 'Monsoon'},
            {'label': 'Post-monsoon (Oct-Nov)', 'value': 'Post-monsoon'},
            {'label': 'Winter (Dec-Feb)', 'value': 'Winter'},
            {'label': 'Summer (Mar-Jun)', 'value': 'Summer'}],
        value='Monsoon', clearable=False, style={'maxWidth': '250px'})], md=4)], className='mb-3'),
        html.Div(id='seasonal-chart'), html.Div(id='seasonal-stats', className='mt-4')])

# Heatmap helper
def make_heatmap(data, cols, y_col, low, high, param):
    if not data: return dbc.Alert('No data', color='info')
    df = pd.DataFrame(data).sort_values(y_col)
    z, text = [], []
    for _, row in df.iterrows():
        vals = [row[c] for c in cols if c in row]
        vmin, vmax = (0.7, 1.0) if 'load factor' in param.lower() else (min(vals) if vals else 0, max(vals) if vals else 1)
        norm = [(v-vmin)/(vmax-vmin) if vmax>vmin else 0.5 for v in vals]
        z.append(norm)
        text.append([f'{v*100:.1f}%' if 'load factor' in param.lower() and v<=1 else f'{v:.0f}' for v in vals])
    
    fig = go.Figure(go.Heatmap(z=z, x=cols, y=df[y_col], text=text, texttemplate='%{text}',
        colorscale=[[0, low], [1, high]], showscale=False, hovertemplate='%{y}<br>%{x}<br>%{text}<extra></extra>'))
    fig.update_layout(title=param, xaxis_title='Month' if len(cols)==12 else 'Season', yaxis_title='Fiscal Year',
        height=max(400, len(df)*40+100), template='plotly_white', yaxis_autorange='reversed')
    return dcc.Graph(figure=fig)

# Monthly heatmap
@callback(Output('monthly-param', 'options'), Output('monthly-param', 'value'), Output('monthly-heatmap', 'children'),
    Input('profile-select', 'value'), Input('monthly-param', 'value'), 
    Input('monthly-low', 'value'), Input('monthly-high', 'value'),
    State('active-project-store', 'data'), prevent_initial_call=True)
def monthly_heatmap(profile, param, low, high, project):
    if not profile or not project: return [], None, dbc.Alert('No profile', color='info')
    try:
        resp = api.get_analysis_data(project['path'], profile, 'Monthly_analysis')
        data, cols = resp.get('data', {}), resp.get('columns', [])
        params = list(data.keys())
        if not params: return [], None, dbc.Alert('No data', color='info')
        param = params[0] if not param or param not in params else param
        return [{'label': p, 'value': p} for p in params], param, make_heatmap(data[param], cols, 'Fiscal_Year', low, high, param)
    except Exception as e: return [], None, dbc.Alert(f'Error: {e}', color='danger')

# Seasonal heatmap
@callback(Output('seasonal-param', 'options'), Output('seasonal-param', 'value'), Output('seasonal-heatmap', 'children'),
    Input('profile-select', 'value'), Input('seasonal-param', 'value'),
    Input('seasonal-low', 'value'), Input('seasonal-high', 'value'),
    State('active-project-store', 'data'), prevent_initial_call=True)
def seasonal_heatmap(profile, param, low, high, project):
    if not profile or not project: return [], None, dbc.Alert('No profile', color='info')
    try:
        resp = api.get_analysis_data(project['path'], profile, 'Season_analysis')
        data, cols = resp.get('data', {}), resp.get('columns', [])
        params = list(data.keys())
        if not params: return [], None, dbc.Alert('No data', color='info')
        param = params[0] if not param or param not in params else param
        return [{'label': p, 'value': p} for p in params], param, make_heatmap(data[param], cols, 'Fiscal_Year', low, high, param)
    except Exception as e: return [], None, dbc.Alert(f'Error: {e}', color='danger')

# Load year data
@callback(Output('year-data', 'data'), Input('period-select', 'value'), 
    State('profile-select', 'value'), State('active-project-store', 'data'), prevent_initial_call=True)
def load_year_data(year, profile, project):
    if not year or year == 'Overall' or not profile or not project: return None
    try:
        data = api.get_full_load_profile(project['path'], profile, year).get('data', [])
        return [{'DateTime': d['DateTime'], 'Demand_MW': d['Demand_MW'], 
                 'is_holiday': d.get('is_holiday', 0), 'is_weekend': d.get('is_weekend', 0)} for d in data]
    except: return None

# Time series chart
@callback(Output('timeseries-chart', 'children'), Output('timeseries-stats', 'children'),
    Input('year-data', 'data'), Input('date-range', 'start_date'), Input('date-range', 'end_date'),
    State('period-select', 'value'), prevent_initial_call=True)
def timeseries_chart(data, start, end, year):
    if not data: return dbc.Alert('No data', color='info'), None
    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    
    if start and end:
        filtered = df[(df['DateTime'] >= start) & (df['DateTime'] <= end)]
    else:
        filtered = df.head(168)  # First week
    
    fig = go.Figure(go.Scatter(x=filtered['DateTime'], y=filtered['Demand_MW'], mode='lines', name='Demand'))
    fig.update_layout(title=f'Hourly Demand - {year}', xaxis_title='Date & Time', yaxis_title='Demand (MW)',
        height=400, template='plotly_white')
    
    # Stats
    max_val = filtered['Demand_MW'].max()
    min_val = filtered['Demand_MW'].min()
    avg_val = filtered['Demand_MW'].mean()
    
    stats = dbc.Card([dbc.CardBody([
        dbc.Row([dbc.Col([html.H6('Max Demand'), html.H4(f'{max_val:.2f} MW', className='text-success')], md=4),
                 dbc.Col([html.H6('Min Demand'), html.H4(f'{min_val:.2f} MW', className='text-danger')], md=4),
                 dbc.Col([html.H6('Avg Demand'), html.H4(f'{avg_val:.2f} MW', className='text-primary')], md=4)])
    ])], className='bg-light')
    
    return dcc.Graph(figure=fig), stats

# Month-wise chart
@callback(Output('monthly-chart', 'children'), Output('monthly-stats', 'children'),
    Input('year-data', 'data'), Input('month-select', 'value'), prevent_initial_call=True)
def monthly_chart(data, month):
    if not data: return dbc.Alert('No data', color='info'), None
    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Month'] = df['DateTime'].dt.month
    filtered = df[df['Month'] == month]
    
    fig = go.Figure(go.Scatter(x=filtered['DateTime'], y=filtered['Demand_MW'], mode='lines', name='Demand'))
    fig.update_layout(title=f'Month {month} Hourly Demand', xaxis_title='Date & Time', yaxis_title='Demand (MW)',
        height=400, template='plotly_white')
    return dcc.Graph(figure=fig), None

# Season-wise chart
@callback(Output('seasonal-chart', 'children'), Output('seasonal-stats', 'children'),
    Input('year-data', 'data'), Input('season-select', 'value'), prevent_initial_call=True)
def seasonal_chart(data, season):
    if not data: return dbc.Alert('No data', color='info'), None
    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Month'] = df['DateTime'].dt.month
    
    season_map = {'Monsoon': [7,8,9], 'Post-monsoon': [10,11], 'Winter': [12,1,2], 'Summer': [3,4,5,6]}
    filtered = df[df['Month'].isin(season_map[season])]
    
    fig = go.Figure(go.Scatter(x=filtered['DateTime'], y=filtered['Demand_MW'], mode='lines', name='Demand'))
    fig.update_layout(title=f'{season} Hourly Demand', xaxis_title='Date & Time', yaxis_title='Demand (MW)',
        height=400, template='plotly_white')
    return dcc.Graph(figure=fig), None

# Day-type chart
@callback(Output('daytype-chart', 'children'), Input('year-data', 'data'), prevent_initial_call=True)
def daytype_chart(data):
    if not data: return dbc.Alert('No data', color='info')
    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Hour'] = df['DateTime'].dt.hour
    
    # Group by hour and day type
    hourly = {h: {'Holiday': [], 'Weekday': [], 'Weekend': []} for h in range(24)}
    for _, row in df.iterrows():
        h = row['Hour']
        if row['is_holiday']: hourly[h]['Holiday'].append(row['Demand_MW'])
        elif row['is_weekend']: hourly[h]['Weekend'].append(row['Demand_MW'])
        else: hourly[h]['Weekday'].append(row['Demand_MW'])
    
    hours = list(range(24))
    holiday_avg = [sum(hourly[h]['Holiday'])/len(hourly[h]['Holiday']) if hourly[h]['Holiday'] else 0 for h in hours]
    weekday_avg = [sum(hourly[h]['Weekday'])/len(hourly[h]['Weekday']) if hourly[h]['Weekday'] else 0 for h in hours]
    weekend_avg = [sum(hourly[h]['Weekend'])/len(hourly[h]['Weekend']) if hourly[h]['Weekend'] else 0 for h in hours]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=holiday_avg, mode='lines+markers', name='Holiday', line=dict(color='#10B981')))
    fig.add_trace(go.Scatter(x=hours, y=weekday_avg, mode='lines+markers', name='Weekday', line=dict(color='#F97316')))
    fig.add_trace(go.Scatter(x=hours, y=weekend_avg, mode='lines+markers', name='Weekend', line=dict(color='#3B82F6')))
    fig.update_layout(title='Average Hourly Demand by Day Type', xaxis_title='Hour', yaxis_title='Avg Demand (MW)',
        height=500, template='plotly_white')
    return dcc.Graph(figure=fig)

# Load duration data
@callback(Output('duration-data', 'data'), Input('period-select', 'value'),
    State('profile-select', 'value'), State('active-project-store', 'data'), prevent_initial_call=True)
def load_duration_data(year, profile, project):
    if not year or year == 'Overall' or not profile or not project: return None
    try:
        return api.get_load_duration_curve(project['path'], profile, year).get('data', [])
    except: return None

# Load duration chart
@callback(Output('duration-chart', 'children'), Input('duration-data', 'data'), 
    State('period-select', 'value'), prevent_initial_call=True)
def duration_chart(data, year):
    if not data: return dbc.Alert('No data', color='info')
    df = pd.DataFrame(data)
    
    fig = go.Figure(go.Scatter(x=df['Percent_Time'], y=df['Demand_MW'], mode='lines', fill='tozeroy',
        fillcolor='rgba(79, 70, 229, 0.3)', line=dict(color='#4f46e5', width=3), name='Demand'))
    
    # Add 5% and 95% markers
    fig.add_vline(x=5, line_dash='dash', line_color='black', line_width=2, 
        annotation_text='5%', annotation_position='top')
    fig.add_vline(x=95, line_dash='dash', line_color='black', line_width=2,
        annotation_text='95%', annotation_position='top')
    
    fig.update_layout(title=f'Load Duration Curve - {year}', xaxis_title='Percent Time (%)', 
        yaxis_title='Demand (MW)', height=500, template='plotly_white', 
        xaxis=dict(range=[0, 100]), showlegend=False)
    return dcc.Graph(figure=fig)
