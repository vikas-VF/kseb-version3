"""
Load Profiles - Analyze Profiles Page (ENHANCED - React Parity)
6-tab analysis dashboard with per-profile state, max/min/avg charts, and brush zoom

IMPROVEMENTS:
- ✅ Per-profile state management (React parity)
- ✅ Max/Min/Avg 24-hour profiles in Time Series
- ✅ Rangeslider (brush zoom) in charts
- ✅ Better color persistence per profile
- ✅ Tab state preserved per profile
"""

from dash import html, dcc, callback, Input, Output, State, no_update, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.local_service import service as api
from utils.state_manager import StateManager

# Default state for a single profile
def get_default_profile_state():
    return {
        'year': 'Overall',
        'tab': 'overview',
        'monthlyParam': 'Peak Demand',
        'seasonalParam': 'Peak Demand',
        'monthlyLow': '#cfd4e3',
        'monthlyHigh': '#252323',
        'seasonalLow': '#cfd4e3',
        'seasonalHigh': '#252323',
        'month': 4,
        'season': 'Monsoon',
        'dateRangeStart': None,
        'dateRangeEnd': None
    }

def layout(active_project=None):
    if not active_project:
        return dbc.Container([dbc.Alert([html.H4('⚠️ No Project Loaded'),
            html.P('Please load a project to analyze load profiles.')], color='warning')], className='p-4')

    return dbc.Container([
        dbc.Card([dbc.CardBody([dbc.Row([
            dbc.Col([dbc.Label('Load Profile', className='fw-bold'),
                dcc.Dropdown(id='profile-select', clearable=False, style={'minWidth': '250px'})], width='auto'),
            dbc.Col([dbc.Label('Period', className='fw-bold'),
                dcc.Dropdown(id='period-select', clearable=False, style={'minWidth': '180px'})], width='auto')
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

        # PER-PROFILE STATE MANAGEMENT (React parity)
        dcc.Store(id='profiles-state', storage_type='local', data={
            'selectedProfile': None,
            'profilesState': {}  # Nested: {profileName: {year, tab, colors, etc.}}
        }),
        dcc.Store(id='year-data', data=None),
        dcc.Store(id='duration-data', data=None),
        dcc.Loading(id='loading', children=html.Div(id='trigger'))
    ], fluid=True, className='p-4')

# Load profiles - with per-profile state initialization
@callback(
    Output('profiles-state', 'data', allow_duplicate=True),
    Output('profile-select', 'options'),
    Output('profile-select', 'value'),
    Input('active-project-store', 'data'),
    State('profiles-state', 'data'),
    prevent_initial_call=False
)
def load_profiles(project, profiles_state):
    if not project:
        return profiles_state, [], None

    try:
        profiles = api.get_load_profiles(project['path']).get('profiles', [])
        if not profiles:
            return profiles_state, [], None

        # Select profile (preserve if exists)
        current_profile = profiles_state.get('selectedProfile')
        if not current_profile or current_profile not in profiles:
            current_profile = profiles[0]

        # Initialize state for new profiles
        profile_states = profiles_state.get('profilesState', {})
        for profile in profiles:
            if profile not in profile_states:
                profile_states[profile] = get_default_profile_state()

        return {
            'selectedProfile': current_profile,
            'profilesState': profile_states
        }, [{'label': p, 'value': p} for p in profiles], current_profile

    except:
        return profiles_state, [], None

# Update selected profile
@callback(
    Output('profiles-state', 'data', allow_duplicate=True),
    Input('profile-select', 'value'),
    State('profiles-state', 'data'),
    prevent_initial_call=True
)
def update_selected_profile(profile, profiles_state):
    if not profile:
        return no_update

    # Initialize state if new profile
    profile_states = profiles_state.get('profilesState', {})
    if profile not in profile_states:
        profile_states[profile] = get_default_profile_state()

    return {
        'selectedProfile': profile,
        'profilesState': profile_states
    }

# Load years for selected profile
@callback(
    Output('period-select', 'options'),
    Output('period-select', 'value'),
    Input('profile-select', 'value'),
    State('active-project-store', 'data'),
    State('profiles-state', 'data'),
    prevent_initial_call=True
)
def load_years(profile, project, profiles_state):
    if not profile or not project:
        return [{'label': 'Overall', 'value': 'Overall'}], 'Overall'

    try:
        years = ['Overall'] + api.get_profile_years(project['path'], profile).get('years', [])

        # Get profile's saved year
        profile_states = profiles_state.get('profilesState', {})
        profile_state = profile_states.get(profile, get_default_profile_state())
        saved_year = profile_state.get('year', 'Overall')

        # Use saved year if still valid
        current_year = saved_year if saved_year in years else 'Overall'

        return [{'label': y, 'value': y} for y in years], current_year
    except:
        return [{'label': 'Overall', 'value': 'Overall'}], 'Overall'

# Update current profile state (year, tab, colors, etc.)
@callback(
    Output('profiles-state', 'data', allow_duplicate=True),
    [
        Input('period-select', 'value'),
        Input('tabs', 'active_tab'),
        Input('month-select', 'value'),
        Input('season-select', 'value'),
        Input('monthly-param', 'value'),
        Input('seasonal-param', 'value'),
        Input('monthly-low', 'value'),
        Input('monthly-high', 'value'),
        Input('seasonal-low', 'value'),
        Input('seasonal-high', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ],
    State('profiles-state', 'data'),
    prevent_initial_call=True
)
def update_current_profile_state(year, tab, month, season, monthly_param, seasonal_param,
                                 monthly_low, monthly_high, seasonal_low, seasonal_high,
                                 date_start, date_end, profiles_state):
    ctx = callback_context
    if not ctx.triggered:
        return no_update

    selected_profile = profiles_state.get('selectedProfile')
    if not selected_profile:
        return no_update

    profile_states = profiles_state.get('profilesState', {})
    current_state = profile_states.get(selected_profile, get_default_profile_state())

    # Update based on what changed
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'period-select' and year:
        current_state['year'] = year
    elif trigger_id == 'tabs' and tab:
        current_state['tab'] = tab
    elif trigger_id == 'month-select' and month:
        current_state['month'] = month
    elif trigger_id == 'season-select' and season:
        current_state['season'] = season
    elif trigger_id == 'monthly-param' and monthly_param:
        current_state['monthlyParam'] = monthly_param
    elif trigger_id == 'seasonal-param' and seasonal_param:
        current_state['seasonalParam'] = seasonal_param
    elif trigger_id == 'monthly-low' and monthly_low:
        current_state['monthlyLow'] = monthly_low
    elif trigger_id == 'monthly-high' and monthly_high:
        current_state['monthlyHigh'] = monthly_high
    elif trigger_id == 'seasonal-low' and seasonal_low:
        current_state['seasonalLow'] = seasonal_low
    elif trigger_id == 'seasonal-high' and seasonal_high:
        current_state['seasonalHigh'] = seasonal_high
    elif trigger_id == 'date-range':
        current_state['dateRangeStart'] = date_start
        current_state['dateRangeEnd'] = date_end

    profile_states[selected_profile] = current_state

    return {
        'selectedProfile': selected_profile,
        'profilesState': profile_states
    }

# Get current profile state helper
def get_current_profile_state(profiles_state):
    selected_profile = profiles_state.get('selectedProfile')
    if not selected_profile:
        return get_default_profile_state()

    profile_states = profiles_state.get('profilesState', {})
    return profile_states.get(selected_profile, get_default_profile_state())

# Render tabs
@callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab'),
    State('profiles-state', 'data')
)
def render_tab(tab, profiles_state):
    profile_state = get_current_profile_state(profiles_state)
    selected_profile = profiles_state.get('selectedProfile')

    if not selected_profile:
        return dbc.Alert('No profile selected. Generate one first.', color='info')

    if tab == 'overview':
        return render_overview(profile_state)
    elif tab in ['timeseries', 'monthly', 'seasonal', 'daytype', 'duration']:
        if profile_state.get('year') == 'Overall':
            return dbc.Alert('Select a specific Fiscal Year from the Period dropdown.',
                           color='info', className='mt-4')
        if tab == 'timeseries':
            return render_timeseries(profile_state)
        elif tab == 'monthly':
            return render_monthly(profile_state)
        elif tab == 'seasonal':
            return render_seasonal(profile_state)
        elif tab == 'daytype':
            return html.Div(id='daytype-chart')
        elif tab == 'duration':
            return html.Div(id='duration-chart')
    return html.Div()

def render_overview(profile_state):
    return html.Div([
        dbc.Row([dbc.Col(html.H5('Monthly Analysis'), width='auto'),
            dbc.Col([html.Span('Low', className='small me-2'),
                dcc.Input(id='monthly-low', type='color',
                         value=profile_state.get('monthlyLow', '#cfd4e3'),
                         style={'width': '50px', 'height': '30px'}),
                html.Span('High', className='small ms-2 me-2'),
                dcc.Input(id='monthly-high', type='color',
                         value=profile_state.get('monthlyHigh', '#252323'),
                         style={'width': '50px', 'height': '30px'})], width='auto'),
            dbc.Col([dbc.Label('Parameter:'),
                    dcc.Dropdown(id='monthly-param', clearable=False,
                               style={'minWidth': '200px'})],
                width='auto', className='ms-auto')], className='mb-3'),
        html.Div(id='monthly-heatmap', className='mb-5'),

        dbc.Row([dbc.Col(html.H5('Seasonal Analysis'), width='auto'),
            dbc.Col([html.Span('Low', className='small me-2'),
                dcc.Input(id='seasonal-low', type='color',
                         value=profile_state.get('seasonalLow', '#cfd4e3'),
                         style={'width': '50px', 'height': '30px'}),
                html.Span('High', className='small ms-2 me-2'),
                dcc.Input(id='seasonal-high', type='color',
                         value=profile_state.get('seasonalHigh', '#252323'),
                         style={'width': '50px', 'height': '30px'})], width='auto'),
            dbc.Col([dbc.Label('Parameter:'),
                    dcc.Dropdown(id='seasonal-param', clearable=False,
                               style={'minWidth': '200px'})],
                width='auto', className='ms-auto')], className='mb-3'),
        html.Div(id='seasonal-heatmap')
    ])

def render_timeseries(profile_state):
    return html.Div([
        dbc.Row([dbc.Col([dbc.Label('Date Range:'),
            dcc.DatePickerRange(
                id='date-range',
                display_format='YYYY-MM-DD',
                start_date=profile_state.get('dateRangeStart'),
                end_date=profile_state.get('dateRangeEnd')
            )], md=6)]),
        html.Div(id='timeseries-chart'),
        html.Div(id='timeseries-stats', className='mt-4'),
        # MAX/MIN/AVG CHART (NEW!)
        html.Hr(),
        html.H5('Max, Min, and Average Hourly Demand Profiles', className='mt-4 mb-3'),
        html.Div(id='maxminavg-chart')
    ])

def render_monthly(profile_state):
    months = [(4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'),
              (10, 'October'), (11, 'November'), (12, 'December'), (1, 'January'), (2, 'February'), (3, 'March')]
    return html.Div([
        dbc.Row([dbc.Col([dbc.Label('Month:'),
            dcc.Dropdown(id='month-select',
                        options=[{'label': n, 'value': v} for v, n in months],
                        value=profile_state.get('month', 4),
                        clearable=False,
                        style={'maxWidth': '200px'})], md=4)], className='mb-3'),
        html.Div(id='monthly-chart'),
        html.Div(id='monthly-stats', className='mt-4')
    ])

def render_seasonal(profile_state):
    return html.Div([
        dbc.Row([dbc.Col([dbc.Label('Season:'),
            dcc.Dropdown(id='season-select',
                        options=[
                            {'label': 'Monsoon (Jul-Sep)', 'value': 'Monsoon'},
                            {'label': 'Post-monsoon (Oct-Nov)', 'value': 'Post-monsoon'},
                            {'label': 'Winter (Dec-Feb)', 'value': 'Winter'},
                            {'label': 'Summer (Mar-Jun)', 'value': 'Summer'}
                        ],
                        value=profile_state.get('season', 'Monsoon'),
                        clearable=False,
                        style={'maxWidth': '250px'})], md=4)], className='mb-3'),
        html.Div(id='seasonal-chart'),
        html.Div(id='seasonal-stats', className='mt-4')
    ])

# Heatmap helper with 10-step color gradient (React parity)
def make_heatmap(data, cols, y_col, low, high, param):
    if not data:
        return dbc.Alert('No data', color='info')

    df = pd.DataFrame(data).sort_values(y_col)
    z, text = [], []

    for _, row in df.iterrows():
        vals = [row[c] for c in cols if c in row]
        vmin, vmax = (0.7, 1.0) if 'load factor' in param.lower() else \
            (min(vals) if vals else 0, max(vals) if vals else 1)
        norm = [(v-vmin)/(vmax-vmin) if vmax>vmin else 0.5 for v in vals]
        z.append(norm)
        text.append([f'{v*100:.1f}%' if 'load factor' in param.lower() and v<=1
                    else f'{v:.0f}' for v in vals])

    # 10-step color gradient (React parity)
    colorscale = []
    steps = 10
    for i in range(steps):
        fraction = i / (steps - 1)
        color = interpolate_color(low, high, fraction)
        colorscale.append([fraction, color])

    fig = go.Figure(go.Heatmap(
        z=z, x=cols, y=df[y_col], text=text, texttemplate='%{text}',
        colorscale=colorscale, showscale=False,
        hovertemplate='%{y}<br>%{x}<br>%{text}<extra></extra>'
    ))

    fig.update_layout(
        title=param,
        xaxis_title='Month' if len(cols)==12 else 'Season',
        yaxis_title='Fiscal Year',
        height=max(400, len(df)*40+100),
        template='plotly_white',
        yaxis_autorange='reversed'
    )

    return dcc.Graph(figure=fig)

def interpolate_color(color1, color2, factor):
    """Interpolate between two hex colors (React parity)"""
    factor = max(0, min(1, factor))

    r1 = int(color1[1:3], 16)
    g1 = int(color1[3:5], 16)
    b1 = int(color1[5:7], 16)

    r2 = int(color2[1:3], 16)
    g2 = int(color2[3:5], 16)
    b2 = int(color2[5:7], 16)

    r = int(r1 + factor * (r2 - r1))
    g = int(g1 + factor * (g2 - g1))
    b = int(b1 + factor * (b2 - b1))

    return f'#{r:02x}{g:02x}{b:02x}'

# Monthly heatmap
@callback(
    Output('monthly-param', 'options'),
    Output('monthly-param', 'value'),
    Output('monthly-heatmap', 'children'),
    Input('profile-select', 'value'),
    Input('monthly-param', 'value'),
    Input('monthly-low', 'value'),
    Input('monthly-high', 'value'),
    State('active-project-store', 'data'),
    State('profiles-state', 'data'),
    prevent_initial_call=True
)
def monthly_heatmap(profile, param, low, high, project, profiles_state):
    if not profile or not project:
        return [], None, dbc.Alert('No profile', color='info')

    # Get profile state for param default
    profile_state = get_current_profile_state(profiles_state)

    try:
        resp = api.get_analysis_data(project['path'], profile, 'Monthly_analysis')
        data, cols = resp.get('data', {}), resp.get('columns', [])
        params = list(data.keys())

        if not params:
            return [], None, dbc.Alert('No data', color='info')

        # Use saved param or default
        if not param or param not in params:
            param = profile_state.get('monthlyParam', params[0])
            if param not in params:
                param = params[0]

        return (
            [{'label': p, 'value': p} for p in params],
            param,
            make_heatmap(data[param], cols, 'Fiscal_Year', low, high, param)
        )
    except Exception as e:
        return [], None, dbc.Alert(f'Error: {e}', color='danger')

# Seasonal heatmap
@callback(
    Output('seasonal-param', 'options'),
    Output('seasonal-param', 'value'),
    Output('seasonal-heatmap', 'children'),
    Input('profile-select', 'value'),
    Input('seasonal-param', 'value'),
    Input('seasonal-low', 'value'),
    Input('seasonal-high', 'value'),
    State('active-project-store', 'data'),
    State('profiles-state', 'data'),
    prevent_initial_call=True
)
def seasonal_heatmap(profile, param, low, high, project, profiles_state):
    if not profile or not project:
        return [], None, dbc.Alert('No profile', color='info')

    # Get profile state for param default
    profile_state = get_current_profile_state(profiles_state)

    try:
        resp = api.get_analysis_data(project['path'], profile, 'Season_analysis')
        data, cols = resp.get('data', {}), resp.get('columns', [])
        params = list(data.keys())

        if not params:
            return [], None, dbc.Alert('No data', color='info')

        # Use saved param or default
        if not param or param not in params:
            param = profile_state.get('seasonalParam', params[0])
            if param not in params:
                param = params[0]

        return (
            [{'label': p, 'value': p} for p in params],
            param,
            make_heatmap(data[param], cols, 'Fiscal_Year', low, high, param)
        )
    except Exception as e:
        return [], None, dbc.Alert(f'Error: {e}', color='danger')

# Load year data
@callback(
    Output('year-data', 'data'),
    Input('period-select', 'value'),
    State('profile-select', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_year_data(year, profile, project):
    if not year or year == 'Overall' or not profile or not project:
        return None
    try:
        data = api.get_full_load_profile(project['path'], profile, year).get('data', [])
        return [{'DateTime': d['DateTime'], 'Demand_MW': d['Demand_MW'],
                 'is_holiday': d.get('is_holiday', 0), 'is_weekend': d.get('is_weekend', 0)}
                for d in data]
    except:
        return None

# Time series chart with rangeslider (brush zoom)
@callback(
    Output('timeseries-chart', 'children'),
    Output('timeseries-stats', 'children'),
    Input('year-data', 'data'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    State('period-select', 'value'),
    prevent_initial_call=True
)
def timeseries_chart(data, start, end, year):
    if not data:
        return dbc.Alert('No data', color='info'), None

    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])

    if start and end:
        filtered = df[(df['DateTime'] >= start) & (df['DateTime'] <= end)]
    else:
        filtered = df.head(168)  # First week

    # Create chart with RANGESLIDER (brush zoom - React parity)
    fig = go.Figure(go.Scatter(
        x=filtered['DateTime'],
        y=filtered['Demand_MW'],
        mode='lines',
        name='Demand',
        line=dict(color='#3B82F6', width=2)
    ))

    fig.update_layout(
        title=f'Hourly Demand - {year}',
        xaxis_title='Date & Time',
        yaxis_title='Demand (MW)',
        height=450,
        template='plotly_white',
        # RANGESLIDER (brush zoom)
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.05),
            type='date'
        ),
        hovermode='x unified'
    )

    # Stats
    max_val = filtered['Demand_MW'].max()
    min_val = filtered['Demand_MW'].min()
    avg_val = filtered['Demand_MW'].mean()

    stats = dbc.Card([dbc.CardBody([
        dbc.Row([
            dbc.Col([html.H6('Max Demand'),
                    html.H4(f'{max_val:.2f} MW', className='text-success')], md=4),
            dbc.Col([html.H6('Min Demand'),
                    html.H4(f'{min_val:.2f} MW', className='text-danger')], md=4),
            dbc.Col([html.H6('Avg Demand'),
                    html.H4(f'{avg_val:.2f} MW', className='text-primary')], md=4)
        ])
    ])], className='bg-light')

    return dcc.Graph(figure=fig, config={'displayModeBar': True}), stats

# MAX/MIN/AVG 24-HOUR PROFILES (NEW - React parity)
@callback(
    Output('maxminavg-chart', 'children'),
    Input('year-data', 'data'),
    State('period-select', 'value'),
    prevent_initial_call=True
)
def maxminavg_chart(data, year):
    if not data:
        return dbc.Alert('No data', color='info')

    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Hour'] = df['DateTime'].dt.hour
    df['Date'] = df['DateTime'].dt.date

    # Find max demand day
    max_demand_value = df['Demand_MW'].max()
    max_demand_row = df[df['Demand_MW'] == max_demand_value].iloc[0]
    max_demand_date = max_demand_row['Date']
    max_day_data = df[df['Date'] == max_demand_date].sort_values('Hour')

    # Find min demand day
    min_demand_value = df['Demand_MW'].min()
    min_demand_row = df[df['Demand_MW'] == min_demand_value].iloc[0]
    min_demand_date = min_demand_row['Date']
    min_day_data = df[df['Date'] == min_demand_date].sort_values('Hour')

    # Calculate hourly averages
    hourly_avg = df.groupby('Hour')['Demand_MW'].mean().reset_index()

    # Create figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=max_day_data['Hour'],
        y=max_day_data['Demand_MW'],
        mode='lines+markers',
        name=f'Maximum Demand (on {max_demand_date})',
        line=dict(color='#10B981', width=2),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=min_day_data['Hour'],
        y=min_day_data['Demand_MW'],
        mode='lines+markers',
        name=f'Minimum Demand (on {min_demand_date})',
        line=dict(color='#F97316', width=2),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=hourly_avg['Hour'],
        y=hourly_avg['Demand_MW'],
        mode='lines+markers',
        name='Average Demand',
        line=dict(color='#3B82F6', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f'Max, Min, and Average Hourly Demand for {year}',
        xaxis_title='Hour',
        yaxis_title='Demand (MW)',
        height=400,
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    return dcc.Graph(figure=fig)

# Month-wise chart with rangeslider
@callback(
    Output('monthly-chart', 'children'),
    Output('monthly-stats', 'children'),
    Input('year-data', 'data'),
    Input('month-select', 'value'),
    prevent_initial_call=True
)
def monthly_chart(data, month):
    if not data:
        return dbc.Alert('No data', color='info'), None

    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Month'] = df['DateTime'].dt.month
    filtered = df[df['Month'] == month]

    fig = go.Figure(go.Scatter(
        x=filtered['DateTime'],
        y=filtered['Demand_MW'],
        mode='lines',
        name='Demand',
        line=dict(color='#3B82F6', width=2)
    ))

    fig.update_layout(
        title=f'Month {month} Hourly Demand',
        xaxis_title='Date & Time',
        yaxis_title='Demand (MW)',
        height=450,
        template='plotly_white',
        xaxis=dict(rangeslider=dict(visible=True, thickness=0.05))
    )

    return dcc.Graph(figure=fig), None

# Season-wise chart with rangeslider
@callback(
    Output('seasonal-chart', 'children'),
    Output('seasonal-stats', 'children'),
    Input('year-data', 'data'),
    Input('season-select', 'value'),
    prevent_initial_call=True
)
def seasonal_chart(data, season):
    if not data:
        return dbc.Alert('No data', color='info'), None

    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Month'] = df['DateTime'].dt.month

    season_map = {
        'Monsoon': [7,8,9],
        'Post-monsoon': [10,11],
        'Winter': [12,1,2],
        'Summer': [3,4,5,6]
    }
    filtered = df[df['Month'].isin(season_map[season])]

    fig = go.Figure(go.Scatter(
        x=filtered['DateTime'],
        y=filtered['Demand_MW'],
        mode='lines',
        name='Demand',
        line=dict(color='#3B82F6', width=2)
    ))

    fig.update_layout(
        title=f'{season} Hourly Demand',
        xaxis_title='Date & Time',
        yaxis_title='Demand (MW)',
        height=450,
        template='plotly_white',
        xaxis=dict(rangeslider=dict(visible=True, thickness=0.05))
    )

    return dcc.Graph(figure=fig), None

# Day-type chart
@callback(
    Output('daytype-chart', 'children'),
    Input('year-data', 'data'),
    prevent_initial_call=True
)
def daytype_chart(data):
    if not data:
        return dbc.Alert('No data', color='info')

    df = pd.DataFrame(data)
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df['Hour'] = df['DateTime'].dt.hour

    # Group by hour and day type
    hourly = {h: {'Holiday': [], 'Weekday': [], 'Weekend': []} for h in range(24)}
    for _, row in df.iterrows():
        h = row['Hour']
        if row['is_holiday']:
            hourly[h]['Holiday'].append(row['Demand_MW'])
        elif row['is_weekend']:
            hourly[h]['Weekend'].append(row['Demand_MW'])
        else:
            hourly[h]['Weekday'].append(row['Demand_MW'])

    hours = list(range(24))
    holiday_avg = [sum(hourly[h]['Holiday'])/len(hourly[h]['Holiday'])
                   if hourly[h]['Holiday'] else 0 for h in hours]
    weekday_avg = [sum(hourly[h]['Weekday'])/len(hourly[h]['Weekday'])
                   if hourly[h]['Weekday'] else 0 for h in hours]
    weekend_avg = [sum(hourly[h]['Weekend'])/len(hourly[h]['Weekend'])
                   if hourly[h]['Weekend'] else 0 for h in hours]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=holiday_avg, mode='lines+markers',
                            name='Holiday', line=dict(color='#10B981', width=2)))
    fig.add_trace(go.Scatter(x=hours, y=weekday_avg, mode='lines+markers',
                            name='Weekday', line=dict(color='#F97316', width=2)))
    fig.add_trace(go.Scatter(x=hours, y=weekend_avg, mode='lines+markers',
                            name='Weekend', line=dict(color='#3B82F6', width=2)))

    fig.update_layout(
        title='Average Hourly Demand by Day Type',
        xaxis_title='Hour',
        yaxis_title='Avg Demand (MW)',
        height=500,
        template='plotly_white',
        hovermode='x unified'
    )

    return dcc.Graph(figure=fig)

# Load duration data
@callback(
    Output('duration-data', 'data'),
    Input('period-select', 'value'),
    State('profile-select', 'value'),
    State('active-project-store', 'data'),
    prevent_initial_call=True
)
def load_duration_data(year, profile, project):
    if not year or year == 'Overall' or not profile or not project:
        return None
    try:
        return api.get_load_duration_curve(project['path'], profile, year).get('data', [])
    except:
        return None

# Load duration chart
@callback(
    Output('duration-chart', 'children'),
    Input('duration-data', 'data'),
    State('period-select', 'value'),
    prevent_initial_call=True
)
def duration_chart(data, year):
    if not data:
        return dbc.Alert('No data', color='info')

    df = pd.DataFrame(data)

    fig = go.Figure(go.Scatter(
        x=df['Percent_Time'],
        y=df['Demand_MW'],
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(79, 70, 229, 0.3)',
        line=dict(color='#4f46e5', width=3),
        name='Demand'
    ))

    # Add 5% and 95% markers
    fig.add_vline(x=5, line_dash='dash', line_color='black', line_width=2,
                  annotation_text='5%', annotation_position='top')
    fig.add_vline(x=95, line_dash='dash', line_color='black', line_width=2,
                  annotation_text='95%', annotation_position='top')

    fig.update_layout(
        title=f'Load Duration Curve - {year}',
        xaxis_title='Percent Time (%)',
        yaxis_title='Demand (MW)',
        height=500,
        template='plotly_white',
        xaxis=dict(range=[0, 100]),
        showlegend=False
    )

    return dcc.Graph(figure=fig)
