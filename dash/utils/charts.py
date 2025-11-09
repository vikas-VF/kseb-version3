"""
Advanced Chart Components
Reusable Plotly chart functions for all visualizations
"""
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd

def create_line_chart(df, x_col, y_cols, title="Line Chart", template='plotly_white'):
    """Create interactive line chart"""
    fig = go.Figure()

    if isinstance(y_cols, str):
        y_cols = [y_cols]

    for col in y_cols:
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>%{x}<br>%{y:.2f}<extra></extra>'
        ))

    fig.update_layout(
        title=title,
        template=template,
        hovermode='x unified',
        showlegend=True,
        height=450
    )
    return fig

def create_stacked_area_chart(data_dict, title="Stacked Area Chart", x_label="Time", y_label="Value"):
    """Create stacked area chart for dispatch analysis"""
    fig = go.Figure()

    for name, values in data_dict.items():
        fig.add_trace(go.Scatter(
            name=name,
            x=list(range(len(values))),
            y=values,
            mode='lines',
            stackgroup='one',
            line=dict(width=0.5),
            fillcolor=f'rgba({np.random.randint(0,255)},{np.random.randint(0,255)},{np.random.randint(0,255)},0.6)'
        ))

    fig.update_layout(
        title=title,
        template='plotly_white',
        hovermode='x unified',
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=450
    )
    return fig

def create_bar_chart(categories, values, title="Bar Chart", orientation='v', color='#4f46e5'):
    """Create bar chart"""
    fig = go.Figure(go.Bar(
        x=categories if orientation == 'v' else values,
        y=values if orientation == 'v' else categories,
        orientation=orientation,
        marker_color=color,
        text=values,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>%{y:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        template='plotly_white',
        height=450
    )
    return fig

def create_gauge_chart(value, title="Gauge", max_value=100, threshold=80):
    """Create gauge chart for KPIs"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24}},
        delta={'reference': threshold},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "#4f46e5"},
            'steps': [
                {'range': [0, max_value*0.5], 'color': "lightgray"},
                {'range': [max_value*0.5, max_value*0.8], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': threshold
            }
        }
    ))

    fig.update_layout(height=350)
    return fig

def create_sankey_diagram(sources, targets, values, labels, title="Energy Flow"):
    """Create Sankey diagram for energy flow"""
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=['#4f46e5', '#0891b2', '#059669', '#ea580c', '#9333ea']
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(79, 70, 229, 0.3)'
        )
    ))

    fig.update_layout(title=title, font_size=12, height=500)
    return fig

def create_waterfall_chart(categories, values, title="Waterfall Chart"):
    """Create waterfall chart for cost breakdown"""
    fig = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=["relative"] * (len(categories) - 1) + ["total"],
        x=categories,
        textposition="outside",
        text=[f"{v:+.2f}" for v in values],
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))

    fig.update_layout(title=title, showlegend=False, height=450)
    return fig

def create_treemap(labels, parents, values, title="Treemap"):
    """Create treemap for hierarchical data"""
    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        textinfo="label+value+percent parent",
        marker=dict(
            colorscale='Viridis',
            line=dict(width=2, color='white')
        )
    ))

    fig.update_layout(title=title, height=500)
    return fig

def create_heatmap_24x7(data_matrix, title="Hourly Load Pattern"):
    """Create 24x7 heatmap for hourly analysis"""
    fig = go.Figure(go.Heatmap(
        z=data_matrix,
        x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        y=[f'{h:02d}:00' for h in range(24)],
        colorscale='Viridis',
        hovertemplate='Day: %{x}<br>Hour: %{y}<br>Value: %{z:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Day of Week",
        yaxis_title="Hour of Day",
        height=600
    )
    return fig

def create_pie_chart(labels, values, title="Distribution"):
    """Create pie chart"""
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.3,  # Donut chart
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>%{value:.2f}<br>%{percent}<extra></extra>'
    ))

    fig.update_layout(title=title, height=450)
    return fig
