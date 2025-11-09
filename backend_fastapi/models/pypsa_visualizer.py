"""
PyPSA Network Visualizer - Complete Consolidated Module
========================================================

All-in-one PyPSA visualization module including:
- Dispatch plots with filters
- Capacity analysis charts
- Storage operation visualizations
- Transmission flow analysis
- Price analysis and duration curves
- Multi-period support
- Interactive Plotly-based visualizations

Version: 4.0 (Ultra-Consolidated)
Date: 2025
"""

import pypsa
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# COLOR MANAGEMENT
# ============================================================================

DEFAULT_COLORS = {
    'coal': '#000000', 'lignite': '#4B4B4B', 'oil': '#FF4500',
    'gas': '#FF6347', 'OCGT': '#FFA07A', 'CCGT': '#FF6B6B',
    'nuclear': '#800080',
    'solar': '#FFD700', 'pv': '#FFD700', 'solar thermal': '#FFA500',
    'wind': '#ADD8E6', 'onwind': '#ADD8E6', 'offwind': '#87CEEB',
    'hydro': '#0073CF', 'ror': '#3399FF', 'reservoir': '#0056A3',
    'biomass': '#228B22', 'biogas': '#32CD32',
    'phs': '#3399FF', 'PHS': '#3399FF', 'pumped hydro': '#3399FF',
    'battery': '#005B5B', 'Battery': '#005B5B', 'li-ion': '#005B5B',
    'hydrogen': '#AFEEEE', 'H2': '#AFEEEE',
    'load': '#000000', 'curtailment': '#FF00FF', 'other': '#D3D3D3'
}


def get_color(carrier: str, network: pypsa.Network = None) -> str:
    """Get color for carrier with fallback."""
    if network and hasattr(network, 'carriers'):
        if carrier in network.carriers.index and 'color' in network.carriers.columns:
            color = network.carriers.loc[carrier, 'color']
            if pd.notna(color):
                return color
    
    carrier_lower = carrier.lower()
    for key, color in DEFAULT_COLORS.items():
        if key.lower() == carrier_lower or key.lower() in carrier_lower:
            return color
    
    # Generate from hash
    import hashlib
    color_hash = hashlib.md5(carrier.encode()).hexdigest()[:6]
    return f'#{color_hash}'


# ============================================================================
# VISUALIZER CLASS
# ============================================================================

class PyPSAVisualizer:
    """Comprehensive visualization suite for PyPSA networks."""
    
    def __init__(self, network: pypsa.Network):
        """
        Initialize visualizer.
        
        Args:
            network: PyPSA network to visualize
        """
        self.network = network
        self.n = network
        self.is_multi_period = isinstance(network.snapshots, pd.MultiIndex)
        self._network_info = None
        logger.info(f"Visualizer initialized (multi-period: {self.is_multi_period})")
    
    @property
    def network_info(self) -> Dict[str, Any]:
        """
        Get comprehensive network information.
        
        Returns:
            Dict with network characteristics and available data
        """
        if self._network_info is None:
            self._network_info = self._analyze_network()
        return self._network_info
    
    def _analyze_network(self) -> Dict[str, Any]:
        """Analyze network structure and data availability."""
        n = self.n
        
        has_generators = hasattr(n, 'generators') and not n.generators.empty
        has_storage_units = hasattr(n, 'storage_units') and not n.storage_units.empty
        has_stores = hasattr(n, 'stores') and not n.stores.empty
        has_loads = hasattr(n, 'loads') and not n.loads.empty
        
        # Check if solved (has time series results)
        is_solved = (hasattr(n, 'generators_t') and 
                    hasattr(n.generators_t, 'p') and 
                    not n.generators_t.p.empty)
        
        # Get time series attributes
        ts_attrs = {
            'generators': [attr for attr in dir(n.generators_t) if not attr.startswith('_')] if hasattr(n, 'generators_t') else [],
            'storage_units': [attr for attr in dir(n.storage_units_t) if not attr.startswith('_')] if hasattr(n, 'storage_units_t') else [],
            'stores': [attr for attr in dir(n.stores_t) if not attr.startswith('_')] if hasattr(n, 'stores_t') else [],
            'loads': [attr for attr in dir(n.loads_t) if not attr.startswith('_')] if hasattr(n, 'loads_t') else [],
            'buses': [attr for attr in dir(n.buses_t) if not attr.startswith('_')] if hasattr(n, 'buses_t') else []
        }
        
        return {
            'is_solved': is_solved,
            'has_generators': has_generators,
            'has_storage_units': has_storage_units,
            'has_stores': has_stores,
            'has_loads': has_loads,
            'time_series_attributes': ts_attrs,
            'num_generators': len(n.generators) if has_generators else 0,
            'num_storage_units': len(n.storage_units) if has_storage_units else 0,
            'num_stores': len(n.stores) if has_stores else 0,
            'num_loads': len(n.loads) if has_loads else 0,
            'num_snapshots': len(n.snapshots) if hasattr(n, 'snapshots') else 0,
            'is_multi_period': self.is_multi_period
        }
    
    # ========================================================================
    # DISPATCH PLOTS
    # ========================================================================
    
    def plot_dispatch(self,
                     resolution: str = '1H',
                     **kwargs) -> go.Figure:
        """
        Create an intelligent dispatch plot that adapts based on available data.
        
        Parameters
        ----------
        resolution : str
            Time resolution for resampling (e.g., '1H', '1D', '1W')
        **kwargs
            Additional plotting parameters:
            - start_date: Start date (YYYY-MM-DD)
            - end_date: End date (YYYY-MM-DD)
            - carriers: List of carriers to include
            - stacked: Stack generation areas (default: True)
            - show_storage: Include storage operation (default: True)
            - show_load: Show load line (default: True)
            - period: For multi-period networks
            
        Returns
        -------
        plotly.graph_objects.Figure
            Interactive dispatch plot
        """
        # Extract parameters
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        carriers = kwargs.get('carriers')
        stacked = kwargs.get('stacked', True)
        show_storage = kwargs.get('show_storage', True)
        show_load = kwargs.get('show_load', True)
        period = kwargs.get('period')
        
        logger.info(f"Creating dispatch plot (resolution: {resolution})")
        
        if not self.network_info['is_solved']:
            fig = go.Figure()
            fig.add_annotation(
                text="Network has not been solved. No dispatch data available.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        n = self.network
        
        # Get generation data
        if not (self.network_info['has_generators'] and 
                'p' in self.network_info['time_series_attributes'].get('generators', [])):
            return self._empty_figure("No generation data available")
        
        gen_data = n.generators_t.p.copy()
        
        # Filter by period
        if self.is_multi_period and period is not None:
            if isinstance(gen_data.index, pd.MultiIndex):
                gen_data = gen_data.loc[period]
        
        # Get time index
        time_index = self._get_time_index(gen_data.index)
        
        # Filter date range
        if start_date:
            mask = time_index >= pd.to_datetime(start_date)
            gen_data = gen_data[mask]
            time_index = time_index[mask]
        if end_date:
            mask = time_index <= pd.to_datetime(end_date)
            gen_data = gen_data[mask]
            time_index = time_index[mask]
        
        if len(gen_data) == 0:
            return self._empty_figure("No data available for selected date range")
        
        # Resample if needed
        if resolution != '1H':
            gen_data.index = time_index
            gen_data = gen_data.resample(resolution).mean()
            time_index = gen_data.index
        
        # Aggregate by carrier with filtering
        gen_by_carrier = pd.DataFrame()
        if 'carrier' in n.generators.columns:
            available_carriers = sorted(n.generators.carrier.unique())
            carriers_to_plot = carriers if carriers else available_carriers
            
            for carrier in carriers_to_plot:
                if carrier in available_carriers:
                    gens = n.generators[n.generators.carrier == carrier].index
                    cols = gen_data.columns.intersection(gens)
                    if len(cols) > 0:
                        gen_by_carrier[carrier] = gen_data[cols].sum(axis=1)
        
        fig = go.Figure()
        
        # Plot generation stacks (sorted for consistent ordering)
        if stacked:
            carrier_totals = gen_by_carrier.sum().sort_values(ascending=False)
            for carrier in carrier_totals.index:
                if gen_by_carrier[carrier].sum() > 0:  # Only plot if there's generation
                    color = get_color(carrier, n)
                    fig.add_trace(go.Scatter(
                        x=time_index,
                        y=gen_by_carrier[carrier],
                        name=carrier.capitalize(),
                        stackgroup='generation',
                        fillcolor=color,
                        line=dict(width=0),
                        hovertemplate='<b>%{fullData.name}</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
        else:
            for carrier in gen_by_carrier.columns:
                if gen_by_carrier[carrier].sum() > 0:
                    color = get_color(carrier, n)
                    fig.add_trace(go.Scatter(
                        x=time_index,
                        y=gen_by_carrier[carrier],
                        name=carrier.capitalize(),
                        mode='lines',
                        line=dict(color=color, width=2),
                        hovertemplate='<b>%{fullData.name}</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
        
        # Add storage discharge (positive values)
        if show_storage and self.network_info['has_storage_units'] and \
           'p' in self.network_info['time_series_attributes'].get('storage_units', []):
            try:
                storage_p = n.storage_units_t.p.copy()
                
                if self.is_multi_period and period is not None:
                    if isinstance(storage_p.index, pd.MultiIndex):
                        storage_p = storage_p.loc[period]
                
                if resolution != '1H':
                    storage_p.index = self._get_time_index(storage_p.index)
                    storage_p = storage_p.resample(resolution).mean()
                
                discharge = storage_p.clip(lower=0).sum(axis=1)
                if discharge.sum() > 0:
                    fig.add_trace(go.Scatter(
                        x=time_index[:len(discharge)],
                        y=discharge,
                        name='Battery Discharge',
                        stackgroup='generation',
                        fillcolor=get_color('battery', n),
                        line=dict(width=0),
                        hovertemplate='<b>Battery Discharge</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
            except Exception as e:
                logger.warning(f"Could not plot storage unit discharge: {e}")
        
        # Add stores discharge (positive values)
        if show_storage and self.network_info['has_stores'] and \
           'p' in self.network_info['time_series_attributes'].get('stores', []):
            try:
                stores_p = n.stores_t.p.copy()
                
                if self.is_multi_period and period is not None:
                    if isinstance(stores_p.index, pd.MultiIndex):
                        stores_p = stores_p.loc[period]
                
                if resolution != '1H':
                    stores_p.index = self._get_time_index(stores_p.index)
                    stores_p = stores_p.resample(resolution).mean()
                
                discharge = stores_p.clip(lower=0).sum(axis=1)
                if discharge.sum() > 0:
                    fig.add_trace(go.Scatter(
                        x=time_index[:len(discharge)],
                        y=discharge,
                        name='H2 Storage Discharge',
                        stackgroup='generation',
                        fillcolor=get_color('h2', n),
                        line=dict(width=0),
                        hovertemplate='<b>H2 Storage Discharge</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
            except Exception as e:
                logger.warning(f"Could not plot store discharge: {e}")
        
        # Add load as a prominent line
        if show_load and self.network_info['has_loads']:
            try:
                load_attr = 'p' if 'p' in self.network_info['time_series_attributes'].get('loads', []) else 'p_set'
                if load_attr in self.network_info['time_series_attributes'].get('loads', []):
                    load_data = getattr(n.loads_t, load_attr).sum(axis=1)
                    
                    if self.is_multi_period and period is not None:
                        if isinstance(load_data.index, pd.MultiIndex):
                            load_data = load_data.loc[period]
                    
                    if resolution != '1H':
                        load_data.index = self._get_time_index(load_data.index)
                        load_data = load_data.resample(resolution).mean()
                    
                    fig.add_trace(go.Scatter(
                        x=time_index[:len(load_data)],
                        y=load_data,
                        name='Load',
                        mode='lines',
                        line=dict(color='black', width=2.5, dash='dash'),
                        hovertemplate='<b>Load</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
            except Exception as e:
                logger.warning(f"Could not plot load data: {e}")
        
        # Add storage charge (negative values - shown below zero line)
        if show_storage and self.network_info['has_storage_units'] and \
           'p' in self.network_info['time_series_attributes'].get('storage_units', []):
            try:
                storage_p = n.storage_units_t.p.copy()
                
                if self.is_multi_period and period is not None:
                    if isinstance(storage_p.index, pd.MultiIndex):
                        storage_p = storage_p.loc[period]
                
                if resolution != '1H':
                    storage_p.index = self._get_time_index(storage_p.index)
                    storage_p = storage_p.resample(resolution).mean()
                
                charge = storage_p.clip(upper=0).sum(axis=1)
                if charge.sum() < 0:
                    fig.add_trace(go.Scatter(
                        x=time_index[:len(charge)],
                        y=charge,
                        name='Battery Charge',
                        mode='lines',
                        fill='tozeroy',
                        fillcolor=f"rgba(0, 91, 91, 0.3)",
                        line=dict(color=get_color('battery', n), width=1),
                        hovertemplate='<b>Battery Charge</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
            except Exception as e:
                logger.warning(f"Could not plot storage unit charge: {e}")
        
        # Add stores charge (negative values - shown below zero line)
        if show_storage and self.network_info['has_stores'] and \
           'p' in self.network_info['time_series_attributes'].get('stores', []):
            try:
                stores_p = n.stores_t.p.copy()
                
                if self.is_multi_period and period is not None:
                    if isinstance(stores_p.index, pd.MultiIndex):
                        stores_p = stores_p.loc[period]
                
                if resolution != '1H':
                    stores_p.index = self._get_time_index(stores_p.index)
                    stores_p = stores_p.resample(resolution).mean()
                
                charge = stores_p.clip(upper=0).sum(axis=1)
                if charge.sum() < 0:
                    fig.add_trace(go.Scatter(
                        x=time_index[:len(charge)],
                        y=charge,
                        name='H2 Storage Charge',
                        mode='lines',
                        fill='tozeroy',
                        fillcolor=f"rgba(175, 238, 238, 0.3)",
                        line=dict(color=get_color('h2', n), width=1),
                        hovertemplate='<b>H2 Storage Charge</b><br>%{x}<br>%{y:.1f} MW<extra></extra>'
                    ))
            except Exception as e:
                logger.warning(f"Could not plot store charge: {e}")
        
        # Update layout
        fig.update_layout(
            title=f'Power Dispatch ({resolution} resolution)',
            xaxis_title='Time',
            yaxis_title='Power (MW)',
            hovermode='x unified',
            height=600,
            yaxis=dict(
                zeroline=True,
                zerolinecolor='gray',
                zerolinewidth=2
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            template='plotly_white'
        )
        
        return fig
    
    def plot_dispatch_by_year(self,
                            year: Optional[int] = None,
                            resolution: str = '1H',
                            **kwargs) -> go.Figure:
        """
        Create dispatch plot for multi-period networks, optionally filtered by year.
        
        Parameters
        ----------
        year : int, optional
            Specific year to plot (for multi-period networks)
        resolution : str
            Time resolution for resampling
        **kwargs
            Additional parameters (carriers, stacked, show_storage, show_load)
            
        Returns
        -------
        plotly.graph_objects.Figure
            Dispatch plot for selected year
        """
        if not self.is_multi_period:
            return self.plot_dispatch(resolution=resolution, **kwargs)
        
        if year is None:
            available_years = self._get_available_years()
            if available_years:
                year = available_years[0]
        
        logger.info(f"Creating dispatch plot for year {year}")
        return self.plot_dispatch(resolution=resolution, period=year, **kwargs)
    
    def _get_available_years(self) -> List[int]:
        """Get list of unique years in multi-period network."""
        if not self.is_multi_period or not hasattr(self.n, 'snapshots'):
            return []
        
        if isinstance(self.n.snapshots, pd.MultiIndex):
            periods = self.n.snapshots.get_level_values(0).unique()
            return sorted(periods.tolist())
        
        return []
    
    def plot_dispatch_multi_network(self,
                                   networks: List[pypsa.Network],
                                   labels: Optional[List[str]] = None,
                                   resolution: str = '1H',
                                   **kwargs) -> go.Figure:
        """
        Compare dispatch across multiple networks.
        
        Parameters
        ----------
        networks : list of pypsa.Network
            Networks to compare
        labels : list of str, optional
            Labels for each network
        resolution : str
            Time resolution
        **kwargs
            Additional parameters
            
        Returns
        -------
        plotly.graph_objects.Figure
            Comparative dispatch plot
        """
        if not networks:
            return self._empty_figure("No networks provided")
        
        if labels is None:
            labels = [f"Network {i+1}" for i in range(len(networks))]
        
        from plotly.subplots import make_subplots
        
        rows = len(networks)
        fig = make_subplots(
            rows=rows, cols=1,
            subplot_titles=labels,
            vertical_spacing=0.12
        )
        
        for idx, network in enumerate(networks, 1):
            try:
                viz = PyPSAVisualizer(network)
                plot_fig = viz.plot_dispatch(resolution=resolution, **kwargs)
                
                # Copy traces to subplot
                for trace in plot_fig.data:
                    fig.add_trace(trace, row=idx, col=1)
            except Exception as e:
                logger.warning(f"Error plotting network {idx}: {e}")
        
        fig.update_layout(
            title='Comparative Dispatch Analysis',
            height=300 * rows,
            showlegend=True
        )
        
        return fig
    
    # ========================================================================
    # CAPACITY ANALYSIS
    # ========================================================================
    
    def plot_capacity_bar_chart(self,
                                carriers: Optional[List[str]] = None,
                                capacity_type: str = 'optimal') -> go.Figure:
        """Create bar chart for installed capacity."""
        logger.info("Creating capacity bar chart")
        
        data = self._collect_capacity_data(capacity_type, carriers)
        
        if data.empty:
            return self._empty_figure("No capacity data available")
        
        carriers_sum = data.groupby('Carrier')['Capacity_MW'].sum().sort_values(ascending=False)
        colors = [get_color(c, self.n) for c in carriers_sum.index]
        
        fig = go.Figure(data=[
            go.Bar(
                x=carriers_sum.index,
                y=carriers_sum.values,
                marker_color=colors,
                text=[f"{v:.0f}" for v in carriers_sum.values],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>%{y:.0f} MW<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Installed Capacity by Technology',
            xaxis_title='Technology',
            yaxis_title='Capacity (MW)',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def plot_capacity_pie_chart(self,
                                carriers: Optional[List[str]] = None,
                                capacity_type: str = 'optimal') -> go.Figure:
        """Create pie chart for capacity mix."""
        logger.info("Creating capacity pie chart")
        
        data = self._collect_capacity_data(capacity_type, carriers)
        
        if data.empty:
            return self._empty_figure("No capacity data available")
        
        carriers_sum = data.groupby('Carrier')['Capacity_MW'].sum()
        colors = [get_color(c, self.n) for c in carriers_sum.index]
        
        fig = go.Figure(data=[go.Pie(
            labels=carriers_sum.index,
            values=carriers_sum.values,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>%{value:.0f} MW<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title='Capacity Mix',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    # ========================================================================
    # STORAGE OPERATION
    # ========================================================================
    
    def plot_storage_operation(self,
                              resolution: str = '1H',
                              period: Optional[int] = None) -> go.Figure:
        """
        Create storage operation plot.
        
        Args:
            resolution: Time resolution
            period: For multi-period networks
        
        Returns:
            Storage operation plot with power and SOC
        """
        logger.info("Creating storage operation plot")
        
        has_su = hasattr(self.n, 'storage_units') and not self.n.storage_units.empty
        has_stores = hasattr(self.n, 'stores') and not self.n.stores.empty
        
        if not (has_su or has_stores):
            return self._empty_figure("No storage components in network")
        
        # Determine subplot layout
        rows = 0
        row_titles = []
        if has_su:
            rows += 2
            row_titles.extend(['Storage Units Power', 'Storage Units SOC'])
        if has_stores:
            rows += 2
            row_titles.extend(['Stores Power', 'Stores Energy'])
        
        if rows == 0:
            return self._empty_figure("No storage data available")
        
        fig = make_subplots(
            rows=rows, cols=1,
            subplot_titles=row_titles,
            vertical_spacing=0.08
        )
        
        current_row = 1
        
        # Storage units
        if has_su:
            self._add_storage_unit_plots(fig, current_row, resolution, period)
            current_row += 2
        
        # Stores
        if has_stores:
            self._add_store_plots(fig, current_row, resolution, period)
        
        fig.update_layout(
            title='Storage Operation',
            height=300 * rows,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    # ========================================================================
    # TRANSMISSION FLOWS
    # ========================================================================
    
    def plot_transmission_flows(self,
                                resolution: str = '1H',
                                period: Optional[int] = None) -> go.Figure:
        """
        Create transmission flows visualization.
        
        Args:
            resolution: Time resolution
            period: For multi-period networks
        
        Returns:
            Transmission flows plot
        """
        logger.info("Creating transmission flows plot")
        
        has_lines = (hasattr(self.n, 'lines_t') and hasattr(self.n.lines_t, 'p0') 
                     and not self.n.lines_t.p0.empty)
        has_links = (hasattr(self.n, 'links_t') and hasattr(self.n.links_t, 'p0') 
                     and not self.n.links_t.p0.empty)
        
        if not (has_lines or has_links):
            return self._empty_figure("No transmission flow data available")
        
        fig = go.Figure()
        
        # AC lines
        if has_lines:
            lines_p = self.n.lines_t.p0.copy()
            
            if self.is_multi_period and period is not None:
                if isinstance(lines_p.index, pd.MultiIndex):
                    lines_p = lines_p.loc[period]
            
            time_index = self._get_time_index(lines_p.index)
            
            # Aggregate flows
            total_flow = lines_p.abs().sum(axis=1)
            
            fig.add_trace(go.Scatter(
                x=time_index,
                y=total_flow,
                name='AC Lines',
                mode='lines',
                line=dict(color='#0073CF', width=2)
            ))
        
        # DC links
        if has_links:
            links_p = self.n.links_t.p0.copy()
            
            if self.is_multi_period and period is not None:
                if isinstance(links_p.index, pd.MultiIndex):
                    links_p = links_p.loc[period]
            
            time_index = self._get_time_index(links_p.index)
            
            # Aggregate flows
            total_flow = links_p.abs().sum(axis=1)
            
            fig.add_trace(go.Scatter(
                x=time_index,
                y=total_flow,
                name='DC Links',
                mode='lines',
                line=dict(color='#DC143C', width=2)
            ))
        
        fig.update_layout(
            title='Transmission Flows',
            xaxis_title='Time',
            yaxis_title='Flow (MW)',
            height=600,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    # ========================================================================
    # PRICE ANALYSIS
    # ========================================================================
    
    def plot_price_analysis(self,
                           resolution: str = '1H',
                           buses: Optional[List[str]] = None,
                           period: Optional[int] = None) -> go.Figure:
        """
        Create price analysis plot.
        
        Args:
            resolution: Time resolution
            buses: Specific buses to plot
            period: For multi-period networks
        
        Returns:
            Price analysis plot
        """
        logger.info("Creating price analysis plot")
        
        if not (hasattr(self.n, 'buses_t') and hasattr(self.n.buses_t, 'marginal_price')):
            return self._empty_figure("No price data available")
        
        prices = self.n.buses_t.marginal_price.copy()
        
        if prices.empty:
            return self._empty_figure("No price data available")
        
        # Filter by period
        if self.is_multi_period and period is not None:
            if isinstance(prices.index, pd.MultiIndex):
                prices = prices.loc[period]
        
        time_index = self._get_time_index(prices.index)
        
        # Filter buses
        if buses:
            cols = prices.columns.intersection(buses)
            if len(cols) == 0:
                return self._empty_figure(f"No price data for buses: {buses}")
            prices = prices[cols]
        
        # Resample if needed
        if resolution != '1H':
            prices.index = time_index
            prices = prices.resample(resolution).mean()
            time_index = prices.index
        
        fig = go.Figure()
        
        # Plot up to 10 buses
        for bus in prices.columns[:10]:
            fig.add_trace(go.Scatter(
                x=time_index,
                y=prices[bus],
                name=bus,
                mode='lines',
                line=dict(width=1.5)
            ))
        
        fig.update_layout(
            title='Nodal Electricity Prices',
            xaxis_title='Time',
            yaxis_title='Price (€/MWh)',
            height=600,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    # ========================================================================
    # DURATION CURVES
    # ========================================================================
    
    def plot_duration_curve(self, carriers: Optional[List[str]] = None) -> go.Figure:
        """
        Create load duration curve.
        
        Args:
            carriers: Carriers to include
        
        Returns:
            Duration curve plot
        """
        logger.info("Creating duration curve")
        
        if not (hasattr(self.n, 'generators_t') and hasattr(self.n.generators_t, 'p')):
            return self._empty_figure("No generation data available")
        
        gen_p = self.n.generators_t.p
        
        # Aggregate by carrier
        curves = {}
        if 'carrier' in self.n.generators.columns:
            available_carriers = self.n.generators['carrier'].unique()
            carriers_to_plot = carriers if carriers else available_carriers
            
            for carrier in carriers_to_plot:
                if carrier in available_carriers:
                    carrier_gens = self.n.generators[self.n.generators['carrier'] == carrier].index
                    cols = gen_p.columns.intersection(carrier_gens)
                    if len(cols) > 0:
                        total = gen_p[cols].sum(axis=1)
                        sorted_vals = total.sort_values(ascending=False).values
                        curves[carrier] = sorted_vals
        
        if not curves:
            return self._empty_figure("No data for duration curves")
        
        fig = go.Figure()
        
        for carrier, values in curves.items():
            hours = np.arange(len(values))
            color = get_color(carrier, self.n)
            
            fig.add_trace(go.Scatter(
                x=hours,
                y=values,
                name=carrier,
                mode='lines',
                line=dict(color=color, width=2)
            ))
        
        fig.update_layout(
            title='Generation Duration Curves',
            xaxis_title='Hours',
            yaxis_title='Power (MW)',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    # ========================================================================
    # DAILY PROFILES
    # ========================================================================
    
    def plot_daily_profile(self, carriers: Optional[List[str]] = None) -> go.Figure:
        """
        Create typical daily generation profile.
        
        Args:
            carriers: Carriers to include
        
        Returns:
            Daily profile plot
        """
        logger.info("Creating daily profile")
        
        if not (hasattr(self.n, 'generators_t') and hasattr(self.n.generators_t, 'p')):
            return self._empty_figure("No generation data available")
        
        gen_p = self.n.generators_t.p.copy()
        time_index = self._get_time_index(gen_p.index)
        
        # Extract hour of day
        gen_p.index = time_index
        gen_p['hour'] = gen_p.index.hour
        
        # Aggregate by carrier and hour
        profiles = {}
        if 'carrier' in self.n.generators.columns:
            available_carriers = self.n.generators['carrier'].unique()
            carriers_to_plot = carriers if carriers else available_carriers
            
            for carrier in carriers_to_plot:
                if carrier in available_carriers:
                    carrier_gens = self.n.generators[self.n.generators['carrier'] == carrier].index
                    cols = [c for c in gen_p.columns if c in carrier_gens]
                    if len(cols) > 0:
                        hourly_avg = gen_p.groupby('hour')[cols].sum().sum(axis=1)
                        profiles[carrier] = hourly_avg
        
        if not profiles:
            return self._empty_figure("No data for daily profiles")
        
        fig = go.Figure()
        
        for carrier, profile in profiles.items():
            hours = profile.index
            color = get_color(carrier, self.n)
            
            fig.add_trace(go.Scatter(
                x=hours,
                y=profile.values,
                name=carrier,
                mode='lines+markers',
                line=dict(color=color, width=2),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title='Typical Daily Generation Profile',
            xaxis_title='Hour of Day',
            yaxis_title='Average Power (MW)',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    # ========================================================================
    # DASHBOARD
    # ========================================================================
    
    def create_dashboard(self) -> go.Figure:
        """
        Create comprehensive dashboard.
        
        Returns:
            Multi-plot dashboard
        """
        logger.info("Creating comprehensive dashboard")
        
        # This would create a multi-subplot dashboard
        # For now, return capacity chart as placeholder
        return self.plot_capacity_bar_chart()
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_time_index(self, index: pd.Index) -> pd.DatetimeIndex:
        """
        Extract time level from index.

        For MultiIndex returns the timestamp level (last level).
        For DatetimeIndex returns it directly.
        """
        if isinstance(index, pd.MultiIndex):
            return index.get_level_values(-1)
        return pd.to_datetime(index) if not isinstance(index, pd.DatetimeIndex) else index

    def _get_period_index(self, index: pd.Index) -> pd.Series:
        """
        Extract period index from snapshots.

        Returns either:
        - For MultiIndex: level 0 (period)
        - For DatetimeIndex: Series of years

        This is the canonical way the code groups by "period".
        """
        if isinstance(index, pd.MultiIndex):
            return index.get_level_values(0)
        else:
            # For single DatetimeIndex, extract years
            datetime_index = pd.to_datetime(index) if not isinstance(index, pd.DatetimeIndex) else index
            return pd.Series(datetime_index.year, index=index)

    def _get_snapshot_weights(self, snapshots_idx: Optional[pd.Index] = None) -> pd.Series:
        """
        Get snapshot weights for period aggregation.

        Reads n.snapshot_weightings.objective if present and reindexes/fills
        to match the snapshots. If missing, returns a series of ones.

        These weights are used for period aggregation (weighted sum / averaging).
        """
        if snapshots_idx is None:
            snapshots_idx = self.n.snapshots

        if hasattr(self.n, 'snapshot_weightings') and 'objective' in self.n.snapshot_weightings.columns:
            weights = self.n.snapshot_weightings['objective']
            # Reindex to match snapshots
            weights = weights.reindex(snapshots_idx, fill_value=1.0)
        else:
            # Default to ones if no weightings present
            weights = pd.Series(1.0, index=snapshots_idx)

        return weights
    
    def _collect_capacity_data(self, capacity_type: str, carriers_filter: Optional[List[str]]) -> pd.DataFrame:
        """Collect capacity data from all components."""
        data = []
        
        if hasattr(self.n, 'generators') and not self.n.generators.empty:
            gens = self.n.generators
            cap_col = 'p_nom_opt' if capacity_type == 'optimal' and 'p_nom_opt' in gens.columns else 'p_nom'
            
            if 'carrier' in gens.columns:
                for carrier in gens['carrier'].unique():
                    if carriers_filter and carrier not in carriers_filter:
                        continue
                    
                    carrier_gens = gens[gens['carrier'] == carrier]
                    data.append({
                        'Carrier': carrier,
                        'Capacity_MW': carrier_gens[cap_col].sum(),
                        'Type': 'Generator'
                    })
        
        return pd.DataFrame(data)
    
    def _add_storage_to_dispatch(self, fig, time_index, resolution, period):
        """Add storage operation to dispatch plot."""
        if hasattr(self.n, 'storage_units_t') and hasattr(self.n.storage_units_t, 'p'):
            su_p = self.n.storage_units_t.p.copy()
            
            if self.is_multi_period and period is not None:
                if isinstance(su_p.index, pd.MultiIndex):
                    su_p = su_p.loc[period]
            
            if len(su_p) > 0:
                if resolution != '1H' and len(su_p) > 0:
                    su_p_index = self._get_time_index(su_p.index)
                    su_p.index = su_p_index
                    su_p = su_p.resample(resolution).mean()
                
                discharge = su_p.clip(lower=0).sum(axis=1)
                charge = su_p.clip(upper=0).sum(axis=1)
                
                if discharge.sum() > 0:
                    fig.add_trace(go.Scatter(
                        x=discharge.index,
                        y=discharge,
                        name='Storage Discharge',
                        mode='lines',
                        stackgroup='generation',
                        fillcolor='#3399FF',
                        line=dict(width=0.5)
                    ))
                
                if charge.sum() < 0:
                    fig.add_trace(go.Scatter(
                        x=charge.index,
                        y=charge,
                        name='Storage Charge',
                        mode='lines',
                        fill='tozeroy',
                        fillcolor='rgba(51, 153, 255, 0.3)',
                        line=dict(width=1, color='#3399FF')
                    ))
    
    def _get_load_data(self, time_index, resolution, period):
        """Get load data."""
        if not hasattr(self.n, 'loads_t'):
            return None
        
        for attr in ['p', 'p_set']:
            if hasattr(self.n.loads_t, attr):
                load_data = getattr(self.n.loads_t, attr).sum(axis=1)
                
                if self.is_multi_period and period is not None:
                    if isinstance(load_data.index, pd.MultiIndex):
                        load_data = load_data.loc[period]
                
                if resolution != '1H' and len(load_data) > 0:
                    load_data_index = self._get_time_index(load_data.index)
                    load_data.index = load_data_index
                    load_data = load_data.resample(resolution).mean()
                
                return load_data
        
        return None
    
    def _add_storage_unit_plots(self, fig, row, resolution, period):
        """Add storage unit plots."""
        if not (hasattr(self.n, 'storage_units_t') and hasattr(self.n.storage_units_t, 'p')):
            return
        
        su_p = self.n.storage_units_t.p.copy()
        
        if self.is_multi_period and period is not None:
            if isinstance(su_p.index, pd.MultiIndex):
                su_p = su_p.loc[period]
        
        if len(su_p) == 0:
            return
        
        time_index = self._get_time_index(su_p.index)
        
        discharge = su_p.clip(lower=0).sum(axis=1)
        charge = -su_p.clip(upper=0).sum(axis=1)
        
        fig.add_trace(go.Scatter(
            x=time_index,
            y=discharge,
            name='Discharge',
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(51, 153, 255, 0.5)',
            line=dict(color='#3399FF', width=2)
        ), row=row, col=1)
        
        fig.add_trace(go.Scatter(
            x=time_index,
            y=-charge,
            name='Charge',
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(255, 153, 51, 0.5)',
            line=dict(color='#FF9933', width=2)
        ), row=row, col=1)
        
        if hasattr(self.n.storage_units_t, 'state_of_charge'):
            soc = self.n.storage_units_t.state_of_charge.copy()
            
            if self.is_multi_period and period is not None:
                if isinstance(soc.index, pd.MultiIndex):
                    soc = soc.loc[period]
            
            if len(soc) > 0:
                soc_total = soc.sum(axis=1)
                
                fig.add_trace(go.Scatter(
                    x=time_index[:len(soc_total)],
                    y=soc_total,
                    name='State of Charge',
                    mode='lines',
                    line=dict(color='#0073CF', width=2)
                ), row=row+1, col=1)
    
    def _add_store_plots(self, fig, row, resolution, period):
        """Add store plots."""
        if not (hasattr(self.n, 'stores_t') and hasattr(self.n.stores_t, 'p')):
            return
        
        stores_p = self.n.stores_t.p.copy()
        
        if self.is_multi_period and period is not None:
            if isinstance(stores_p.index, pd.MultiIndex):
                stores_p = stores_p.loc[period]
        
        if len(stores_p) == 0:
            return
        
        time_index = self._get_time_index(stores_p.index)
        
        discharge = stores_p.clip(lower=0).sum(axis=1)
        charge = -stores_p.clip(upper=0).sum(axis=1)
        
        fig.add_trace(go.Scatter(
            x=time_index,
            y=discharge,
            name='Discharge',
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(0, 91, 91, 0.5)',
            line=dict(color='#005B5B', width=2)
        ), row=row, col=1)
        
        fig.add_trace(go.Scatter(
            x=time_index,
            y=-charge,
            name='Charge',
            mode='lines',
            fill='tozeroy',
            fillcolor='rgba(255, 165, 0, 0.5)',
            line=dict(color='#FFA500', width=2)
        ), row=row, col=1)
        
        if hasattr(self.n.stores_t, 'e'):
            energy = self.n.stores_t.e.copy()
            
            if self.is_multi_period and period is not None:
                if isinstance(energy.index, pd.MultiIndex):
                    energy = energy.loc[period]
            
            if len(energy) > 0:
                energy_total = energy.sum(axis=1)
                
                fig.add_trace(go.Scatter(
                    x=time_index[:len(energy_total)],
                    y=energy_total,
                    name='Energy State',
                    mode='lines',
                    line=dict(color='#005B5B', width=2)
                ), row=row+1, col=1)
    
    def _empty_figure(self, message: str) -> go.Figure:
        """Create empty figure with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
            template='plotly_white'
        )
        return fig


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_dispatch_plot(network: pypsa.Network, **kwargs) -> go.Figure:
    """Create dispatch plot."""
    viz = PyPSAVisualizer(network)
    return viz.plot_dispatch(**kwargs)


def create_capacity_chart(network: pypsa.Network, chart_type: str = 'bar', **kwargs) -> go.Figure:
    """Create capacity chart."""
    viz = PyPSAVisualizer(network)
    if chart_type == 'bar':
        return viz.plot_capacity_bar_chart(**kwargs)
    elif chart_type == 'pie':
        return viz.plot_capacity_pie_chart(**kwargs)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")