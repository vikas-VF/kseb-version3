"""
PyPSA Network Analyzer - Complete Consolidated Module
======================================================

All-in-one PyPSA analysis module including:
- Network caching (LRU with thread safety)
- Network inspection and availability detection
- Single network comprehensive analysis
- Multi-period/multi-file detection and handling
- Component-level analysis
- System-level metrics

Version: 4.0 (Ultra-Consolidated)
Date: 2025
"""

import pypsa
import pandas as pd
import numpy as np
import logging
import warnings
import gc
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime
from collections import OrderedDict
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# Memory optimization
pd.options.mode.chained_assignment = None
pd.options.mode.copy_on_write = True


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def safe_float(value) -> Optional[float]:
    """Convert value to float safely, handling NaN and None."""
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value) -> Optional[int]:
    """Convert value to int safely, handling NaN and None."""
    try:
        if pd.isna(value):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def detect_renewable_carriers(network: pypsa.Network) -> List[str]:
    """
    Detect renewable carriers from network dynamically.

    Uses multiple strategies:
    1. Check for 'renewable' column in carriers DataFrame
    2. Check for 'co2_emissions' == 0
    3. Check carrier name patterns as fallback

    Args:
        network: PyPSA network

    Returns:
        List of renewable carrier names
    """
    renewable_carriers = []

    if not hasattr(network, 'carriers') or network.carriers.empty:
        return renewable_carriers

    carriers_df = network.carriers

    # Strategy 1: Check for explicit renewable flag
    if 'renewable' in carriers_df.columns:
        renewable_mask = carriers_df['renewable'].fillna(False).astype(bool)
        renewable_carriers = carriers_df[renewable_mask].index.tolist()
        if renewable_carriers:
            logger.info(f"Detected {len(renewable_carriers)} renewable carriers from 'renewable' column")
            return renewable_carriers

    # Strategy 2: Zero emissions carriers (excluding nuclear if co2_emissions column exists)
    if 'co2_emissions' in carriers_df.columns:
        zero_emission = carriers_df['co2_emissions'].fillna(float('inf')) == 0
        zero_emission_carriers = carriers_df[zero_emission].index.tolist()

        # Filter out non-renewable zero emission sources
        non_renewable_keywords = ['nuclear', 'uranium']
        renewable_carriers = [
            c for c in zero_emission_carriers
            if not any(keyword in c.lower() for keyword in non_renewable_keywords)
        ]

        if renewable_carriers:
            logger.info(f"Detected {len(renewable_carriers)} renewable carriers from zero emissions")
            return renewable_carriers

    # Strategy 3: Name-based detection (fallback only)
    renewable_keywords = [
        'solar', 'pv', 'wind', 'onwind', 'offwind', 'hydro', 'ror',
        'biomass', 'biogas', 'geothermal', 'wave', 'tidal'
    ]

    for carrier in carriers_df.index:
        carrier_lower = carrier.lower()
        if any(keyword in carrier_lower for keyword in renewable_keywords):
            renewable_carriers.append(carrier)

    if renewable_carriers:
        logger.info(f"Detected {len(renewable_carriers)} renewable carriers from name patterns (fallback)")
    else:
        logger.warning("No renewable carriers detected in network")

    return renewable_carriers


def get_component_columns(network: pypsa.Network, component_name: str) -> List[str]:
    """
    Get available columns for a component dynamically.

    Args:
        network: PyPSA network
        component_name: Component name (e.g., 'generators', 'buses')

    Returns:
        List of column names
    """
    if hasattr(network, component_name):
        df = getattr(network, component_name)
        if hasattr(df, 'columns'):
            return list(df.columns)
    return []


def get_timeseries_attributes(network: pypsa.Network, component_name: str) -> List[str]:
    """
    Get available time series attributes for a component.

    Args:
        network: PyPSA network
        component_name: Component name (e.g., 'generators', 'buses')

    Returns:
        List of time series attribute names
    """
    ts_name = f'{component_name}_t'
    if hasattr(network, ts_name):
        ts_dict = getattr(network, ts_name)
        if hasattr(ts_dict, 'keys'):
            return [k for k in ts_dict.keys() if hasattr(ts_dict[k], 'empty') and not ts_dict[k].empty]
    return []


def has_component(network: pypsa.Network, component_name: str) -> bool:
    """
    Check if network has a specific component with data.

    Args:
        network: PyPSA network
        component_name: Component name (e.g., 'generators', 'buses')

    Returns:
        True if component exists and has data
    """
    if hasattr(network, component_name):
        df = getattr(network, component_name)
        return hasattr(df, 'empty') and not df.empty
    return False


def get_capacity_column(network: pypsa.Network, component_name: str) -> Optional[str]:
    """
    Get the appropriate capacity column name for a component.

    Checks for optimized capacity first, then nominal capacity.

    Args:
        network: PyPSA network
        component_name: Component name

    Returns:
        Column name or None
    """
    if not has_component(network, component_name):
        return None

    df = getattr(network, component_name)

    # Check for optimized capacity (from solve)
    opt_columns = ['p_nom_opt', 's_nom_opt', 'e_nom_opt']
    for col in opt_columns:
        if col in df.columns:
            return col

    # Check for nominal capacity (input)
    nom_columns = ['p_nom', 's_nom', 'e_nom']
    for col in nom_columns:
        if col in df.columns:
            return col

    return None


# =============================================================================
# NETWORK CACHE (Thread-Safe LRU Cache)
# =============================================================================

class NetworkCache:
    """Thread-safe LRU cache for PyPSA networks with TTL support."""
    
    def __init__(self, max_size: int = 10, ttl_seconds: int = 300):
        """
        Initialize network cache.
        
        Args:
            max_size: Maximum number of networks to cache
            ttl_seconds: Time to live for cached networks (seconds)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[pypsa.Network, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        logger.info(f"NetworkCache initialized: max_size={max_size}, ttl={ttl_seconds}s")
    
    def get(self, filepath: str) -> Optional[pypsa.Network]:
        """Get network from cache if available and not expired."""
        with self._lock:
            filepath_str = str(Path(filepath).resolve())
            
            if filepath_str not in self._cache:
                self._stats['misses'] += 1
                return None
            
            network, timestamp = self._cache[filepath_str]
            age = time.time() - timestamp
            
            if age > self.ttl_seconds:
                del self._cache[filepath_str]
                self._stats['misses'] += 1
                logger.info(f"Cache expired for {Path(filepath).name}")
                return None
            
            self._cache.move_to_end(filepath_str)
            self._stats['hits'] += 1
            logger.debug(f"Cache hit for {Path(filepath).name}")
            return network
    
    def put(self, filepath: str, network: pypsa.Network):
        """Add network to cache."""
        with self._lock:
            filepath_str = str(Path(filepath).resolve())
            
            if filepath_str not in self._cache and len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats['evictions'] += 1
                logger.info(f"Cache eviction: {Path(oldest_key).name}")
            
            self._cache[filepath_str] = (network, time.time())
            if len(self._cache) > 1:
                self._cache.move_to_end(filepath_str)
            logger.debug(f"Cached network: {Path(filepath).name}")
    
    def invalidate(self, filepath: Optional[str] = None):
        """Invalidate cache entry or entire cache."""
        with self._lock:
            if filepath is None:
                self._cache.clear()
                logger.info("Cache cleared")
            else:
                filepath_str = str(Path(filepath).resolve())
                if filepath_str in self._cache:
                    del self._cache[filepath_str]
                    logger.info(f"Cache invalidated for {Path(filepath).name}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self._stats['evictions']
            }


# Global cache instance
_global_cache = NetworkCache(max_size=10, ttl_seconds=300)


def load_network_cached(filepath: str) -> pypsa.Network:
    """
    Load PyPSA network with caching.
    
    Args:
        filepath: Path to network file (.nc)
    
    Returns:
        pypsa.Network: Loaded network
    """
    network = _global_cache.get(filepath)
    
    if network is not None:
        return network
    
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Network file not found: {filepath}")
    
    if filepath.suffix != '.nc':
        raise ValueError(f"Only .nc files supported, got: {filepath.suffix}")
    
    logger.info(f"Loading network from file: {filepath.name}")
    start_time = time.time()
    network = pypsa.Network(filepath.as_posix())
    load_time = time.time() - start_time
    logger.info(f"Network loaded in {load_time:.2f}s")
    
    _global_cache.put(str(filepath), network)
    return network


def get_cache_stats() -> Dict:
    """Get cache statistics."""
    return _global_cache.get_stats()


def invalidate_network_cache(filepath: Optional[str] = None):
    """Invalidate cache."""
    _global_cache.invalidate(filepath)


# =============================================================================
# MULTI-PERIOD UTILITIES
# =============================================================================

def is_multi_period(network: pypsa.Network) -> bool:
    """
    Check if network is multi-period.
    
    Args:
        network: PyPSA network
    
    Returns:
        bool: True if multi-period
    """
    return isinstance(network.snapshots, pd.MultiIndex)


def get_periods(network: pypsa.Network) -> List[int]:
    """
    Get list of periods in network.
    
    Args:
        network: PyPSA network
    
    Returns:
        List[int]: List of period years
    """
    if is_multi_period(network):
        return sorted(network.snapshots.get_level_values(0).unique().tolist())
    else:
        # Single period - extract year from first snapshot
        if len(network.snapshots) > 0:
            first_snapshot = network.snapshots[0]
            if hasattr(first_snapshot, 'year'):
                return [first_snapshot.year]
        return [2025]  # Default year


def extract_period_networks(network_path: str, output_dir: str) -> List[Dict[str, str]]:
    """
    Extract individual period networks from multi-period network.
    
    Args:
        network_path: Path to multi-period network file
        output_dir: Directory to save extracted networks
    
    Returns:
        List of dicts with period info and file paths
    """
    network = load_network_cached(network_path)
    
    if not is_multi_period(network):
        raise ValueError("Network is not multi-period")
    
    periods = get_periods(network)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    period_files = []
    
    for period in periods:
        # Create period-specific network
        period_network = network.copy()
        
        # Filter snapshots for this period
        period_snapshots = network.snapshots[network.snapshots.get_level_values(0) == period]
        period_network.set_snapshots(period_snapshots.droplevel(0))
        
        # Filter time series data
        for component in network.iterate_components():
            comp_name = component.name
            if hasattr(network, f'{comp_name}_t'):
                comp_t = getattr(network, f'{comp_name}_t')
                if hasattr(period_network, f'{comp_name}_t'):
                    period_comp_t = getattr(period_network, f'{comp_name}_t')
                    for attr in comp_t.keys():
                        if attr in period_comp_t:
                            df = comp_t[attr]
                            if isinstance(df.index, pd.MultiIndex):
                                period_comp_t[attr] = df.loc[period].copy()
        
        # Save network
        output_file = output_dir / f"period_{period}.nc"
        period_network.export_to_netcdf(output_file)
        
        period_files.append({
            "period": period,
            "file_path": str(output_file),
            "file_name": output_file.name
        })
        
        logger.info(f"Extracted period {period} to {output_file.name}")
    
    return period_files


def process_multi_file_networks(file_paths: List[Path]) -> Dict[int, pypsa.Network]:
    """
    Process multiple network files and extract years.
    
    Args:
        file_paths: List of paths to network files
    
    Returns:
        Dict mapping years to networks
    """
    networks_by_year = {}
    
    for file_path in file_paths:
        # Extract year from filename
        year_match = re.search(r'year[_-]?(\d{4})|(\d{4})[_-]?year|(\d{4})', file_path.stem)
        
        if year_match:
            year = int(year_match.group(1) or year_match.group(2) or year_match.group(3))
        else:
            # Try to extract from first snapshot
            network = load_network_cached(str(file_path))
            if len(network.snapshots) > 0:
                first_snapshot = network.snapshots[0]
                if hasattr(first_snapshot, 'year'):
                    year = first_snapshot.year
                else:
                    year = 2025  # Default
            else:
                year = 2025
        
        network = load_network_cached(str(file_path))
        networks_by_year[year] = network
        logger.info(f"Processed {file_path.name} as year {year}")
    
    return networks_by_year


# =============================================================================
# SNAPSHOT & TIME INDEX UTILITIES (Multi-Period Aware)
# =============================================================================

def get_time_index(index: Union[pd.DatetimeIndex, pd.MultiIndex]) -> pd.DatetimeIndex:
    """
    Extract time/datetime index from snapshots.
    
    For MultiIndex (multi-period), returns the last level (timestamp).
    For DatetimeIndex, returns it directly.
    
    Args:
        index: Snapshot index (MultiIndex or DatetimeIndex)
    
    Returns:
        pd.DatetimeIndex: Time index for plotting/resampling
    """
    if isinstance(index, pd.MultiIndex):
        # Get the last level (timestamp) from MultiIndex
        time_level = index.get_level_values(-1)
        if pd.api.types.is_datetime64_any_dtype(time_level):
            return time_level
        else:
            try:
                return pd.to_datetime(time_level)
            except Exception as e:
                logger.error(f"Could not convert MultiIndex level to DatetimeIndex: {e}")
                raise TypeError("MultiIndex level is not datetime-like.")
    elif isinstance(index, pd.DatetimeIndex):
        return index
    else:
        try:
            return pd.to_datetime(index)
        except Exception as e:
            logger.error(f"Cannot convert index of type {type(index)} to DatetimeIndex: {e}")
            raise TypeError(f"Unsupported snapshot index type: {type(index)}")


def get_period_index(index: Union[pd.DatetimeIndex, pd.MultiIndex]) -> Union[pd.Index, pd.Series]:
    """
    Extract period/year index from snapshots.
    
    For MultiIndex (multi-period), returns level 0 (period).
    For DatetimeIndex, returns the year as a series.
    
    Args:
        index: Snapshot index (MultiIndex or DatetimeIndex)
    
    Returns:
        Union[pd.Index, pd.Series]: Period index for groupby operations
    """
    if isinstance(index, pd.MultiIndex):
        return index.get_level_values(0)
    elif isinstance(index, pd.DatetimeIndex):
        # Return the year as a simple way to group for "annual" analysis
        return pd.Series(index.year, index=index)
    else:
        logger.warning(f"Cannot determine period index from type {type(index)}. Returning None.")
        return None


def get_snapshot_weights(network: pypsa.Network, snapshots_idx: Union[pd.DatetimeIndex, pd.MultiIndex]) -> pd.Series:
    """
    Get snapshot weights for period aggregation.
    
    Reads n.snapshot_weightings.objective (if present) and reindexes/fills
    to match the snapshots. If missing, returns a series of ones.
    
    These weights are used for period aggregation (weighted sum / averaging).
    
    Args:
        network: PyPSA network
        snapshots_idx: Snapshot index
    
    Returns:
        pd.Series: Weight series indexed by snapshots
    """
    if hasattr(network, 'snapshot_weightings') and 'objective' in network.snapshot_weightings.columns:
        weights = network.snapshot_weightings['objective']
        # Reindex carefully to handle potential missing indices in snapshots_idx
        common_index = snapshots_idx.intersection(weights.index)
        if common_index.empty:
            logger.warning("No common index between snapshots and snapshot_weightings. Assuming weight 1.0.")
            return pd.Series(1.0, index=snapshots_idx)
        else:
            # Reindex weights to the common index, then reindex to the full snapshots_idx, filling missing with 1.0
            return weights.reindex(common_index).reindex(snapshots_idx).fillna(1.0)
    else:
        logger.warning("Snapshot weights ('objective') not found or empty. Assuming weight 1.0 for all snapshots.")
        return pd.Series(1.0, index=snapshots_idx)


# =============================================================================
# NETWORK INSPECTOR
# =============================================================================

class NetworkInspector:
    """Comprehensive network inspection and availability detection."""
    
    def __init__(self, network: pypsa.Network):
        """
        Initialize inspector.
        
        Args:
            network: PyPSA network to inspect
        """
        self.network = network
        self.n = network
    
    def get_full_availability(self) -> Dict[str, Any]:
        """
        Get comprehensive availability information.

        IMPORTANT: Returns BOTH nested structure (for detailed info) AND flat boolean flags
        (for frontend compatibility). This ensures the frontend's analysisRegistry.js
        requirements checking works correctly.

        Frontend expects:
        - has_generators: bool
        - has_storage_units: bool
        - has_stores: bool
        - has_loads: bool
        - has_lines: bool
        - has_buses: bool
        - has_carriers: bool
        - is_solved: bool
        - has_emissions_data: bool
        - carriers: []
        - technologies: []
        - regions: []
        - is_multi_period: bool
        - is_multi_file: bool
        """
        # Get detailed nested structures
        basic_info = self._get_basic_info()
        components = self._get_components_info()
        time_series = self._get_time_series_info()
        spatial_info = self._get_spatial_info()
        available_analyses = self._get_available_analyses()
        available_visualizations = self._get_available_visualizations()

        # Build comprehensive availability with BOTH nested AND flat structure
        availability = {
            # ===== FLAT BOOLEAN FLAGS (Frontend Requirements) =====
            # Component availability flags
            'has_generators': 'generators' in components and components['generators'].get('available', False),
            'has_storage_units': 'storage_units' in components and components['storage_units'].get('available', False),
            'has_stores': 'stores' in components and components['stores'].get('available', False),
            'has_loads': 'loads' in components and components['loads'].get('available', False),
            'has_lines': 'lines' in components and components['lines'].get('available', False),
            'has_links': 'links' in components and components['links'].get('available', False),
            'has_buses': 'buses' in components and components['buses'].get('available', False),
            'has_carriers': 'carriers' in components and components['carriers'].get('available', False),
            'has_transformers': 'transformers' in components and components['transformers'].get('available', False),

            # Network state flags
            'is_solved': basic_info.get('is_solved', False),
            'has_objective': basic_info.get('has_objective', False),
            'is_multi_period': basic_info.get('is_multi_period', False),
            'is_multi_file': False,  # Set by detect-network-type endpoint

            # Emissions data flag
            'has_emissions_data': self._check_emissions_data(components),

            # ===== FLAT ARRAYS (Frontend Filters) =====
            # Extract carriers from all components that have them
            'carriers': self._extract_unique_values(components, 'carriers'),
            'technologies': self._extract_unique_values(components, 'technologies'),
            'regions': spatial_info.get('zones', []),
            'zones': spatial_info.get('zones', []),
            'buses': list(self.n.buses.index) if has_component(self.n, 'buses') else [],
            'sectors': self._extract_sectors(components),
            'years': time_series.get('years', []),
            'periods': time_series.get('periods', []),

            # ===== NESTED DETAILED STRUCTURE (Backward Compatibility) =====
            'basic_info': basic_info,
            'components': components,
            'time_series': time_series,
            'spatial_info': spatial_info,
            'available_analyses': available_analyses,
            'available_visualizations': available_visualizations
        }

        logger.info(f"Availability computed: has_generators={availability['has_generators']}, "
                   f"has_storage_units={availability['has_storage_units']}, "
                   f"is_solved={availability['is_solved']}, "
                   f"carriers={len(availability['carriers'])}")

        return availability

    def _check_emissions_data(self, components: Dict) -> bool:
        """
        Check if emissions data is available in the network.

        Returns True if:
        - carriers exist AND have co2_emissions column
        - OR generators exist AND have co2_emissions in carriers
        """
        if 'carriers' in components:
            carrier_cols = components['carriers'].get('columns', [])
            if 'co2_emissions' in carrier_cols:
                return True

        # Check if any generator has emission data
        if has_component(self.n, 'carriers'):
            if 'co2_emissions' in self.n.carriers.columns:
                # Check if any carrier has non-zero emissions
                emissions = self.n.carriers['co2_emissions'].fillna(0)
                if (emissions != 0).any():
                    return True

        return False

    def _extract_unique_values(self, components: Dict, field: str) -> List[str]:
        """
        Extract unique values of a field from all components.

        For example, extract all unique carriers from generators, storage_units, etc.
        """
        values = []
        for comp_name, comp_info in components.items():
            if field in comp_info:
                values.extend(comp_info[field])

        # Remove duplicates and sort
        return sorted(list(set(values)))

    def _extract_sectors(self, components: Dict) -> List[str]:
        """Extract unique sector values from components that have them."""
        sectors = []
        for comp_name, comp_info in components.items():
            if 'columns' in comp_info and 'sector' in comp_info['columns']:
                # Get the actual component dataframe
                if hasattr(self.n, comp_name):
                    df = getattr(self.n, comp_name)
                    if 'sector' in df.columns:
                        sectors.extend(df['sector'].dropna().unique().tolist())

        return sorted(list(set(sectors)))
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """Get basic network information."""
        n = self.n
        info = {
            'name': getattr(n, 'name', 'Unnamed Network'),
            'is_solved': False,
            'has_objective': False,
            'objective_value': None,
            'is_multi_period': is_multi_period(n)
        }
        
        if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
            if not n.generators_t.p.empty:
                info['is_solved'] = True
        
        if hasattr(n, 'objective') and n.objective is not None:
            info['has_objective'] = True
            info['objective_value'] = float(n.objective)
        
        return info
    
    def _get_components_info(self) -> Dict[str, Any]:
        """
        Get detailed component information dynamically.

        Uses network.components iterator to discover ALL components in the network,
        not just a hardcoded list.

        CRITICAL: Sets 'available': True only when component has actual data.
        This ensures frontend requirements checking works correctly.
        """
        n = self.n
        components = {}

        # Iterate through ALL components in the network (dynamic)
        for component in n.iterate_components():
            comp_type = component.name  # e.g., 'Generator', 'Bus', 'Line'
            comp_list_name = component.list_name  # e.g., 'generators', 'buses', 'lines'
            df = component.df  # DataFrame with component data

            # Skip empty components - they are NOT available
            if df.empty:
                logger.debug(f"Component {comp_list_name} is empty, skipping")
                continue

            comp_info = {
                'available': True,  # Component has data
                'component_type': comp_type,  # Singular name (e.g., 'Generator')
                'list_name': comp_list_name,  # Plural name (e.g., 'generators')
                'count': len(df),
                'columns': list(df.columns),
                'has_time_series': False,
                'time_series_attributes': []
            }

            # Check time series dynamically
            ts_attrs = get_timeseries_attributes(n, comp_list_name)
            if ts_attrs:
                comp_info['has_time_series'] = True
                comp_info['time_series_attributes'] = sorted(ts_attrs)
                logger.debug(f"Component {comp_list_name} has time series: {ts_attrs}")

            # Extract carriers (if column exists)
            if 'carrier' in df.columns:
                carriers = sorted(df['carrier'].dropna().unique().tolist())
                if carriers:  # Only add if non-empty
                    comp_info['carriers'] = carriers
                    comp_info['carriers_count'] = len(carriers)
                    logger.debug(f"Component {comp_list_name} has {len(carriers)} carriers")

            # Extract technologies (if column exists)
            if 'technology' in df.columns:
                technologies = sorted(df['technology'].dropna().unique().tolist())
                if technologies:
                    comp_info['technologies'] = technologies
                    comp_info['technologies_count'] = len(technologies)
                    logger.debug(f"Component {comp_list_name} has {len(technologies)} technologies")

            # Extract zones/regions/countries (dynamic column detection)
            for zone_col in ['zone', 'region', 'country', 'area', 'sector']:
                if zone_col in df.columns:
                    zones = sorted(df[zone_col].dropna().unique().tolist())
                    if zones:
                        comp_info['zones'] = zones
                        comp_info['zones_count'] = len(zones)
                        comp_info['zone_column'] = zone_col  # Record which column was used
                        logger.debug(f"Component {comp_list_name} has {len(zones)} {zone_col}s")
                        break  # Use first available zone column

            # Add capacity information if available
            capacity_col = get_capacity_column(n, comp_list_name)
            if capacity_col:
                comp_info['capacity_column'] = capacity_col
                try:
                    total_capacity = df[capacity_col].sum()
                    comp_info['total_capacity'] = float(total_capacity)
                    logger.debug(f"Component {comp_list_name} total capacity: {total_capacity:.2f} MW")
                except Exception as e:
                    logger.warning(f"Could not compute total capacity for {comp_list_name}: {e}")

            components[comp_list_name] = comp_info
            logger.info(f"Component {comp_list_name}: {len(df)} items, time_series={comp_info['has_time_series']}")

        logger.info(f"Total components detected: {len(components)}")
        if not components:
            logger.warning("NO COMPONENTS DETECTED IN NETWORK - This will cause 'No Analysis Available' error!")

        return components
    
    def _get_time_series_info(self) -> Dict[str, Any]:
        """Get time series information."""
        n = self.n
        info = {
            'has_snapshots': hasattr(n, 'snapshots') and len(n.snapshots) > 0,
            'total_snapshots': len(n.snapshots) if hasattr(n, 'snapshots') else 0,
            'is_multi_period': is_multi_period(n),
            'periods': get_periods(n) if hasattr(n, 'snapshots') else [],
            'years': []
        }
        
        if info['has_snapshots']:
            time_index = get_time_index(n.snapshots)
            if len(time_index) > 0:
                info['time_range'] = {
                    'start': time_index[0].isoformat() if hasattr(time_index[0], 'isoformat') else str(time_index[0]),
                    'end': time_index[-1].isoformat() if hasattr(time_index[-1], 'isoformat') else str(time_index[-1])
                }
                if len(time_index) > 1:
                    resolution = time_index[1] - time_index[0]
                    try:
                        info['resolution_hours'] = round(resolution.total_seconds() / 3600, 4)
                    except Exception:
                        info['resolution_hours'] = None
            # Extract years
            if is_multi_period(n):
                info['years'] = get_periods(n)
            else:
                unique_years = []
                for snapshot in n.snapshots:
                    if hasattr(snapshot, 'year'):
                        year = snapshot.year
                        if year not in unique_years:
                            unique_years.append(year)
                info['years'] = sorted(unique_years) if unique_years else [2025]
        
        return info
    
    def _get_spatial_info(self) -> Dict[str, Any]:
        """Get spatial information."""
        n = self.n
        info = {
            'has_coordinates': False,
            'has_zones': False,
            'zones': [],
            'voltage_levels': []
        }
        
        if hasattr(n, 'buses') and not n.buses.empty:
            if 'x' in n.buses.columns and 'y' in n.buses.columns:
                has_coords = n.buses[['x', 'y']].notna().any().any()
                info['has_coordinates'] = bool(has_coords)
            
            zones = []
            if 'country' in n.buses.columns:
                zones = n.buses['country'].dropna().unique().tolist()
            elif 'zone' in n.buses.columns:
                zones = n.buses['zone'].dropna().unique().tolist()
            elif 'region' in n.buses.columns:
                zones = n.buses['region'].dropna().unique().tolist()
            
            if zones:
                zones = sorted(zones)
                info['has_zones'] = True
                info['zones'] = zones
                info['zones_count'] = len(zones)
            else:
                info['has_zones'] = False
                info['zones'] = []
                info['zones_count'] = 0
            
            if 'v_nom' in n.buses.columns:
                voltage_levels = n.buses['v_nom'].dropna().unique().tolist()
                info['voltage_levels'] = sorted([float(v) for v in voltage_levels])
                info['voltage_levels_count'] = len(info['voltage_levels'])
            else:
                info['voltage_levels'] = []
                info['voltage_levels_count'] = 0
        
        return info
    
    def _get_available_analyses(self) -> List[str]:
        """
        Get list of available analyses dynamically.

        NOTE: Like Streamlit, we show analyses if components exist,
        even if not solved/optimized. Individual methods handle missing data gracefully.
        """
        n = self.n
        analyses = []

        # Capacity analysis - show if generators exist (even without p_nom_opt)
        if has_component(n, 'generators'):
            analyses.append('total_capacities')
            analyses.append('capacity')
            logger.info("Available: total_capacities (generators exist)")

        # Generation analysis - show if generators_t.p exists (solved network)
        gen_ts_attrs = get_timeseries_attributes(n, 'generators')
        if 'p' in gen_ts_attrs:
            analyses.extend(['energy_mix', 'energy-mix', 'capacity_factors', 'cuf', 'renewable_share', 'renewable-share'])
            logger.info("Available: energy_mix, capacity_factors, renewable_share")

            # Curtailment - show if p_max_pu exists
            if 'p_max_pu' in gen_ts_attrs:
                analyses.append('curtailment')
                logger.info("Available: curtailment")

            # Daily profiles - requires generators_t.p
            analyses.append('daily_profiles')
            analyses.append('daily-profiles')
            logger.info("Available: daily_profiles")

        # Emissions analysis - show if carriers exist (even without co2_emissions column)
        if has_component(n, 'carriers'):
            analyses.append('emissions')
            logger.info("Available: emissions")
            analyses.append('carriers')
            logger.info("Available: carriers")

        # Cost analysis - show if generators exist (even without cost columns)
        if has_component(n, 'generators'):
            analyses.append('system_costs')
            analyses.append('costs')
            logger.info("Available: system_costs")

        # Storage analysis - show if storage components exist
        if has_component(n, 'storage_units'):
            analyses.append('storage_operation')
            analyses.append('storage-units')
            analyses.append('storage_units')
            logger.info("Available: storage_units (PHS)")

        if has_component(n, 'stores'):
            analyses.append('storage_operation')
            analyses.append('stores')
            analyses.append('bess')
            logger.info("Available: stores (BESS)")

        # Transmission analysis - show if lines or links exist
        if has_component(n, 'lines'):
            analyses.append('lines')
            analyses.append('transmission_flows')
            logger.info("Available: lines")

        if has_component(n, 'links'):
            analyses.append('links')
            analyses.append('transmission_flows')
            logger.info("Available: links")

        # Check for time series data for transmission
        lines_ts = get_timeseries_attributes(n, 'lines')
        links_ts = get_timeseries_attributes(n, 'links')
        if 'p0' in lines_ts or 'p0' in links_ts:
            analyses.append('network_losses')
            analyses.append('network-losses')
            logger.info("Available: network_losses")

        # Load analysis - show if loads exist
        if has_component(n, 'loads'):
            analyses.append('loads')
            logger.info("Available: loads")

            load_ts = get_timeseries_attributes(n, 'loads')
            if 'p' in load_ts:
                analyses.append('load_profiles')
                analyses.append('load-growth')
                analyses.append('duration_curves')
                analyses.append('duration-curves')
                logger.info("Available: load_profiles, duration_curves")

        # Price analysis - show if buses_t.marginal_price exists
        buses_ts = get_timeseries_attributes(n, 'buses')
        if 'marginal_price' in buses_ts:
            analyses.append('marginal_prices')
            analyses.append('marginal-prices')
            analyses.append('prices')
            logger.info("Available: marginal_prices")

        # Buses - show if buses exist
        if has_component(n, 'buses'):
            analyses.append('buses')
            logger.info("Available: buses")

        # Additional aliases for frontend compatibility
        aliases = {
            'capacity_factors': 'utilization',
            'system_costs': 'costs',
            'transmission_flows': 'lines',
            'load_profiles': 'load_growth'
        }
        for source, alias in aliases.items():
            if source in analyses and alias not in analyses:
                analyses.append(alias)

        # Remove duplicates
        analyses = list(dict.fromkeys(analyses))

        logger.info(f"Total analyses available: {len(analyses)}")
        logger.info(f"Analysis list: {analyses}")
        return analyses
    
    def _get_available_visualizations(self) -> Dict[str, bool]:
        """Get availability map for visualizations."""
        analyses = set(self._get_available_analyses())
        return {
            'capacity_bar_chart': 'total_capacities' in analyses,
            'capacity_pie_chart': 'total_capacities' in analyses,
            'energy_mix_pie': 'energy_mix' in analyses,
            'energy_dispatch_chart': 'energy_mix' in analyses,
            'utilization_chart': 'capacity_factors' in analyses or 'utilization' in analyses,
            'cost_breakdown_chart': 'system_costs' in analyses or 'costs' in analyses,
            'emissions_bar_chart': 'emissions' in analyses,
            'storage_operation_chart': 'storage_operation' in analyses,
            'transmission_flow_chart': 'transmission_flows' in analyses,
            'price_analysis_chart': 'prices' in analyses
        }


# =============================================================================
# SINGLE NETWORK ANALYZER
# =============================================================================

class PyPSASingleNetworkAnalyzer:
    """Comprehensive single network analysis."""
    
    def __init__(self, network: pypsa.Network):
        """
        Initialize analyzer.
        
        Args:
            network: PyPSA network to analyze
        """
        self.network = network
        self.n = network
        self.inspector = NetworkInspector(network)
    
    def run_all_analyses(self) -> Dict[str, Any]:
        """Run all available analyses."""
        available = self.inspector._get_available_analyses()
        
        results = {
            'availability': self.inspector.get_full_availability(),
            'analyses': {}
        }
        
        if 'total_capacities' in available:
            results['analyses']['total_capacities'] = self.get_total_capacities()
        
        if 'energy_mix' in available:
            results['analyses']['energy_mix'] = self.get_energy_mix()
        
        if 'capacity_factors' in available:
            results['analyses']['capacity_factors'] = self.get_capacity_factors()
        
        if 'renewable_share' in available:
            results['analyses']['renewable_share'] = self.get_renewable_share()
        
        if 'emissions' in available:
            results['analyses']['emissions'] = self.get_emissions_tracking()
        
        if 'system_costs' in available:
            results['analyses']['system_costs'] = self.get_system_costs()
        
        return results
    
    def get_total_capacities(self) -> Dict[str, Any]:
        """
        Get total installed capacities by carrier using dynamic column detection.

        Handles both optimized (p_nom_opt) and non-optimized (p_nom) networks gracefully.
        Returns data even if only component count exists.
        """
        n = self.n

        generator_rows: List[Dict[str, Any]] = []
        storage_unit_rows: List[Dict[str, Any]] = []
        store_rows: List[Dict[str, Any]] = []

        gen_totals = {}
        storage_power_totals = {}
        storage_energy_totals = {}

        # Generators - handle even without capacity column
        if has_component(n, 'generators') and 'carrier' in n.generators.columns:
            capacity_col = get_capacity_column(n, 'generators')

            for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
                carrier_gens = n.generators[n.generators['carrier'] == carrier]

                # Try to get capacity, default to 0 if no capacity column
                if capacity_col:
                    capacity = carrier_gens[capacity_col].sum()
                else:
                    capacity = 0
                    logger.warning(f"No capacity column for generators, showing count only")

                gen_totals[carrier] = float(capacity)

                generator_rows.append({
                    'Carrier': carrier,
                    'carrier': carrier,
                    'Technology': carrier_gens['technology'].iloc[0] if 'technology' in carrier_gens.columns else carrier,
                    'technology': carrier_gens['technology'].iloc[0] if 'technology' in carrier_gens.columns else carrier,
                    'Capacity_MW': safe_float(capacity) or 0.0,
                    'Capacity_MW_value': safe_float(capacity) or 0.0,
                    'Count': int(len(carrier_gens)),
                    'capacity_column': capacity_col if capacity_col else 'none'
                })

        # Storage Units (PHS - power capacity) - handle even without capacity column
        if has_component(n, 'storage_units') and 'carrier' in n.storage_units.columns:
            capacity_col = get_capacity_column(n, 'storage_units')

            for carrier in sorted(n.storage_units['carrier'].dropna().unique().tolist()):
                carrier_units = n.storage_units[n.storage_units['carrier'] == carrier]

                # Try to get capacity, default to 0 if no capacity column
                if capacity_col:
                    capacity = carrier_units[capacity_col].sum()
                else:
                    capacity = 0
                    logger.warning(f"No capacity column for storage_units, showing count only")

                storage_power_totals[carrier] = float(capacity)

                storage_unit_rows.append({
                    'Carrier': carrier,
                    'carrier': carrier,
                    'Technology': carrier_units['technology'].iloc[0] if 'technology' in carrier_units.columns else carrier,
                    'technology': carrier_units['technology'].iloc[0] if 'technology' in carrier_units.columns else carrier,
                    'Power_Capacity_MW': safe_float(capacity) or 0.0,
                    'Power_Capacity_MW_value': safe_float(capacity) or 0.0,
                    'Count': int(len(carrier_units)),
                    'capacity_column': capacity_col if capacity_col else 'none'
                })

        # Stores (BESS - energy capacity) - handle even without capacity column
        if has_component(n, 'stores') and 'carrier' in n.stores.columns:
            capacity_col = get_capacity_column(n, 'stores')

            for carrier in sorted(n.stores['carrier'].dropna().unique().tolist()):
                carrier_stores = n.stores[n.stores['carrier'] == carrier]

                # Try to get capacity, default to 0 if no capacity column
                if capacity_col:
                    energy_capacity = carrier_stores[capacity_col].sum()
                else:
                    energy_capacity = 0
                    logger.warning(f"No capacity column for stores, showing count only")

                storage_energy_totals[carrier] = float(energy_capacity)

                store_rows.append({
                    'Carrier': carrier,
                    'carrier': carrier,
                    'Technology': carrier_stores['technology'].iloc[0] if 'technology' in carrier_stores.columns else carrier,
                    'technology': carrier_stores['technology'].iloc[0] if 'technology' in carrier_stores.columns else carrier,
                    'Energy_Capacity_MWh': safe_float(energy_capacity) or 0.0,
                    'Energy_Capacity_MWh_value': safe_float(energy_capacity) or 0.0,
                    'Count': int(len(carrier_stores)),
                    'capacity_column': capacity_col if capacity_col else 'none'
                })

        return {
            'capacities': {
                'generators': generator_rows,
                'storage_units': storage_unit_rows,
                'stores': store_rows
            },
            'totals': {
                'generation_capacity_mw': safe_float(sum(gen_totals.values())) or 0.0,
                'storage_power_capacity_mw': safe_float(sum(storage_power_totals.values())) or 0.0,
                'storage_energy_capacity_mwh': safe_float(sum(storage_energy_totals.values())) or 0.0
            },
            'aggregates': {
                'generators_by_carrier': gen_totals,
                'storage_power_by_carrier': storage_power_totals,
                'storage_energy_by_carrier': storage_energy_totals
            }
        }
    
    def get_energy_mix(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get energy generation mix (weighted by snapshot weights for multi-period).

        Parameters
        ----------
        start_date : str, optional
            Start date for filtering (YYYY-MM-DD format)
        end_date : str, optional
            End date for filtering (YYYY-MM-DD format)

        Returns
        -------
        Dict[str, Any]
            Energy mix data with carriers, totals, and percentages
        """
        n = self.n

        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p')):
            return {
                'energy_mix': [],
                'totals': {'total_energy_mwh': 0.0},
                'percentages': {}
            }

        gen_p = n.generators_t.p.copy()
        if gen_p.empty:
            return {
                'energy_mix': [],
                'totals': {'total_energy_mwh': 0.0},
                'percentages': {}
            }

        # Filter by date range if provided
        if start_date or end_date:
            # Get the time index (handling both regular and MultiIndex)
            if isinstance(gen_p.index, pd.MultiIndex):
                # For multi-period networks, get the timestamp level
                time_index = gen_p.index.get_level_values(-1)
            else:
                time_index = gen_p.index

            # Apply date filters
            mask = pd.Series(True, index=gen_p.index)
            if start_date:
                try:
                    start_dt = pd.to_datetime(start_date)
                    mask = mask & (time_index >= start_dt)
                except Exception as e:
                    logger.warning(f"Invalid start_date format: {start_date}. Ignoring filter.")

            if end_date:
                try:
                    end_dt = pd.to_datetime(end_date)
                    mask = mask & (time_index <= end_dt)
                except Exception as e:
                    logger.warning(f"Invalid end_date format: {end_date}. Ignoring filter.")

            gen_p = gen_p[mask]

            if gen_p.empty:
                return {
                    'energy_mix': [],
                    'totals': {'total_energy_mwh': 0.0},
                    'percentages': {},
                    'message': 'No data available for the selected date range'
                }

        weights = get_snapshot_weights(n, gen_p.index)
        energy_by_carrier = {}
        if hasattr(n, 'generators') and 'carrier' in n.generators.columns:
            for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
                carrier_gens = n.generators[n.generators['carrier'] == carrier].index
                cols = gen_p.columns.intersection(carrier_gens)
                if len(cols) > 0:
                    carrier_gen_p = gen_p[cols]
                    weighted_energy = (carrier_gen_p.T * weights).T.sum().sum()
                    energy_by_carrier[carrier] = float(weighted_energy)
        
        total_energy = sum(energy_by_carrier.values())
        energy_percentages = {}
        energy_rows: List[Dict[str, Any]] = []
        for carrier, energy in energy_by_carrier.items():
            percentage = (energy / total_energy) * 100 if total_energy > 0 else 0.0
            energy_percentages[carrier] = percentage
            energy_rows.append({
                'Carrier': carrier,
                'Energy_MWh': safe_float(energy) or 0.0,
                'Share_%': safe_float(percentage) or 0.0
            })
        
        return {
            'energy_mix': energy_rows,
            'totals': {
                'total_energy_mwh': safe_float(total_energy) or 0.0
            },
            'percentages': energy_percentages
        }

    def get_dispatch_data(self, resolution: str = '1H', start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get time-series dispatch data for stacked area chart.

        Parameters
        ----------
        resolution : str
            Time resolution for resampling (e.g., '1H', '3H', '6H', '12H', '1D', '1W')
        start_date : str, optional
            Start date for filtering (YYYY-MM-DD format)
        end_date : str, optional
            End date for filtering (YYYY-MM-DD format)

        Returns
        -------
        Dict[str, Any]
            Dispatch data with timestamps and power values by carrier
        """
        n = self.n

        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p')):
            return {
                'timestamps': [],
                'generation': {},
                'load': [],
                'storage_charge': {},
                'storage_discharge': {},
                'message': 'No generation data available'
            }

        # Get generation data
        gen_p = n.generators_t.p.copy()
        if gen_p.empty:
            return {
                'timestamps': [],
                'generation': {},
                'load': [],
                'storage_charge': {},
                'storage_discharge': {},
                'message': 'Generation data is empty'
            }

        # Get time index
        if isinstance(gen_p.index, pd.MultiIndex):
            time_index = gen_p.index.get_level_values(-1)
        else:
            time_index = gen_p.index

        # Filter by date range if provided
        if start_date or end_date:
            mask = pd.Series(True, index=gen_p.index)
            if start_date:
                try:
                    start_dt = pd.to_datetime(start_date)
                    mask = mask & (time_index >= start_dt)
                except Exception as e:
                    logger.warning(f"Invalid start_date format: {start_date}")

            if end_date:
                try:
                    end_dt = pd.to_datetime(end_date)
                    mask = mask & (time_index <= end_dt)
                except Exception as e:
                    logger.warning(f"Invalid end_date format: {end_date}")

            gen_p = gen_p[mask]
            time_index = time_index[mask]

        if gen_p.empty:
            return {
                'timestamps': [],
                'generation': {},
                'load': [],
                'storage_charge': {},
                'storage_discharge': {},
                'message': 'No data available for selected date range'
            }

        # Aggregate generation by carrier
        gen_by_carrier = {}
        if hasattr(n, 'generators') and 'carrier' in n.generators.columns:
            for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
                carrier_gens = n.generators[n.generators['carrier'] == carrier].index
                cols = gen_p.columns.intersection(carrier_gens)
                if len(cols) > 0:
                    carrier_series = gen_p[cols].sum(axis=1)
                    # Only include if there's significant generation
                    if carrier_series.abs().sum() > 1e-3:
                        gen_by_carrier[carrier] = carrier_series

        # Get load data
        load_series = pd.Series(0.0, index=gen_p.index)
        if hasattr(n, 'loads_t'):
            if hasattr(n.loads_t, 'p'):
                load_series = n.loads_t.p.sum(axis=1)
            elif hasattr(n.loads_t, 'p_set'):
                load_series = n.loads_t.p_set.sum(axis=1)

        # Filter load by date range
        if start_date or end_date:
            load_series = load_series[mask]

        # Get storage data
        storage_charge = {}
        storage_discharge = {}

        # Storage units
        if hasattr(n, 'storage_units_t') and hasattr(n.storage_units_t, 'p'):
            storage_p = n.storage_units_t.p.copy()
            if start_date or end_date:
                storage_p = storage_p[mask]

            if hasattr(n, 'storage_units') and 'carrier' in n.storage_units.columns:
                for carrier in n.storage_units['carrier'].unique():
                    carrier_units = n.storage_units[n.storage_units['carrier'] == carrier].index
                    cols = storage_p.columns.intersection(carrier_units)
                    if len(cols) > 0:
                        carrier_p = storage_p[cols].sum(axis=1)
                        # Discharge (positive values)
                        discharge = carrier_p.clip(lower=0)
                        if discharge.sum() > 1e-3:
                            storage_discharge[f"{carrier} Discharge"] = discharge
                        # Charge (negative values)
                        charge = carrier_p.clip(upper=0)
                        if charge.sum() < -1e-3:
                            storage_charge[f"{carrier} Charge"] = charge

        # Stores (BESS, H2, etc.)
        if hasattr(n, 'stores_t') and hasattr(n.stores_t, 'p'):
            stores_p = n.stores_t.p.copy()
            if start_date or end_date:
                stores_p = stores_p[mask]

            if hasattr(n, 'stores') and 'carrier' in n.stores.columns:
                for carrier in n.stores['carrier'].unique():
                    carrier_stores = n.stores[n.stores['carrier'] == carrier].index
                    cols = stores_p.columns.intersection(carrier_stores)
                    if len(cols) > 0:
                        carrier_p = stores_p[cols].sum(axis=1)
                        # Discharge (positive values)
                        discharge = carrier_p.clip(lower=0)
                        if discharge.sum() > 1e-3:
                            storage_discharge[f"{carrier} Store Discharge"] = discharge
                        # Charge (negative values)
                        charge = carrier_p.clip(upper=0)
                        if charge.sum() < -1e-3:
                            storage_charge[f"{carrier} Store Charge"] = charge

        # Resample if needed
        if resolution != '1H':
            # Create a combined DataFrame for resampling
            all_data = pd.DataFrame(index=time_index)
            for carrier, series in gen_by_carrier.items():
                all_data[f"gen_{carrier}"] = series.values
            for carrier, series in storage_discharge.items():
                all_data[f"discharge_{carrier}"] = series.values
            for carrier, series in storage_charge.items():
                all_data[f"charge_{carrier}"] = series.values
            all_data['load'] = load_series.values

            # Resample
            all_data = all_data.resample(resolution).mean()

            # Extract back
            gen_by_carrier = {k: all_data[f"gen_{k}"] for k in gen_by_carrier.keys()}
            storage_discharge = {k: all_data[f"discharge_{k}"] for k in storage_discharge.keys()}
            storage_charge = {k: all_data[f"charge_{k}"] for k in storage_charge.keys()}
            load_series = all_data['load']
            time_index = all_data.index

        # Intelligent sampling to prevent browser freeze
        # Maximum 2000 points for visualization (enough for detail, small enough for performance)
        MAX_POINTS = 2000
        if len(time_index) > MAX_POINTS:
            logger.info(f"Sampling dispatch data from {len(time_index)} to {MAX_POINTS} points")

            # Use intelligent sampling - keep more points at start/end, sample middle
            sample_indices = np.linspace(0, len(time_index) - 1, MAX_POINTS, dtype=int)

            # Sample all data
            time_index = time_index[sample_indices]
            gen_by_carrier = {k: series.iloc[sample_indices] for k, series in gen_by_carrier.items()}
            storage_discharge = {k: series.iloc[sample_indices] for k, series in storage_discharge.items()}
            storage_charge = {k: series.iloc[sample_indices] for k, series in storage_charge.items()}
            load_series = load_series.iloc[sample_indices]

        # Convert to JSON-serializable format
        timestamps = [t.isoformat() for t in time_index]

        generation_data = {
            carrier: [float(v) for v in series.values]
            for carrier, series in gen_by_carrier.items()
        }

        storage_discharge_data = {
            carrier: [float(v) for v in series.values]
            for carrier, series in storage_discharge.items()
        }

        storage_charge_data = {
            carrier: [float(v) for v in series.values]
            for carrier, series in storage_charge.items()
        }

        load_data = [float(v) for v in load_series.values]

        return {
            'timestamps': timestamps,
            'generation': generation_data,
            'storage_discharge': storage_discharge_data,
            'storage_charge': storage_charge_data,
            'load': load_data,
            'resolution': resolution,
            'total_points': len(timestamps),
            'sampled': len(timestamps) < len(gen_p)
        }

    def get_network_metadata(self) -> Dict[str, Any]:
        """Get network metadata including date range from snapshots.

        Returns
        -------
        Dict[str, Any]
            Network metadata with date range, snapshot count, etc.
        """
        n = self.n

        metadata = {
            'snapshot_count': 0,
            'start_date': None,
            'end_date': None,
            'has_multiindex': False
        }

        try:
            # Check if network has data
            if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p')):
                return metadata

            gen_p = n.generators_t.p
            if gen_p.empty:
                return metadata

            # Get time index
            if isinstance(gen_p.index, pd.MultiIndex):
                time_index = gen_p.index.get_level_values(-1)
                metadata['has_multiindex'] = True
            else:
                time_index = gen_p.index

            metadata['snapshot_count'] = len(time_index)

            # Get min/max dates
            if len(time_index) > 0:
                metadata['start_date'] = time_index.min().isoformat()
                metadata['end_date'] = time_index.max().isoformat()

        except Exception as e:
            logger.error(f"Error getting network metadata: {e}")

        return metadata

    def get_capacity_factors(self) -> Dict[str, Any]:
        """Get capacity factors by carrier (weighted by snapshot weights)."""
        n = self.n
        
        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p')):
            return {
                'utilization': [],
                'overall_capacity_factor_percent': 0.0
            }
        
        gen_p = n.generators_t.p
        if gen_p.empty or not hasattr(n, 'generators'):
            return {
                'utilization': [],
                'overall_capacity_factor_percent': 0.0
            }
        
        weights = get_snapshot_weights(n, gen_p.index)
        weighted_hours = weights.sum()
        
        capacity_factors = {}
        total_energy = 0
        total_potential = 0
        
        if 'carrier' in n.generators.columns:
            for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
                carrier_gens = n.generators[n.generators['carrier'] == carrier]
                carrier_gen_names = carrier_gens.index
                cols = gen_p.columns.intersection(carrier_gen_names)
                
                if len(cols) > 0:
                    carrier_gen_p = gen_p[cols]
                    weighted_energy = (carrier_gen_p.T * weights).T.sum().sum()
                    
                    if 'p_nom_opt' in carrier_gens.columns:
                        capacity = carrier_gens['p_nom_opt'].sum()
                    elif 'p_nom' in carrier_gens.columns:
                        capacity = carrier_gens['p_nom'].sum()
                    else:
                        capacity = 0
                    
                    potential = capacity * weighted_hours
                    
                    if potential > 0:
                        cf = weighted_energy / potential
                        capacity_factors[carrier] = float(cf)
                        total_energy += weighted_energy
                        total_potential += potential
        
        overall_cf = (total_energy / total_potential) if total_potential > 0 else 0
        utilization_rows: List[Dict[str, Any]] = []
        for carrier, cf in capacity_factors.items():
            utilization_rows.append({
                'Carrier': carrier,
                'Utilization_%': safe_float(cf * 100) or 0.0,
                'Capacity_Factor': safe_float(cf) or 0.0
            })
        
        return {
            'utilization': utilization_rows,
            'overall_capacity_factor_percent': safe_float(overall_cf * 100) or 0.0,
            'overall_capacity_factor': safe_float(overall_cf) or 0.0
        }
    
    def get_renewable_share(self) -> Dict[str, Any]:
        """
        Calculate renewable energy share dynamically.

        Uses detect_renewable_carriers() to identify renewables from network.carriers.
        """
        n = self.n

        # Get renewable carriers dynamically from network
        renewable_carriers_list = detect_renewable_carriers(n)

        energy_mix = self.get_energy_mix()

        # Handle different energy_mix formats
        if 'energy_mix' in energy_mix and isinstance(energy_mix['energy_mix'], list):
            # Format: {'energy_mix': [{'Carrier': ..., 'Energy_MWh': ...}]}
            total_energy = energy_mix.get('totals', {}).get('total_energy_mwh', 0)
            renewable_energy = 0
            renewable_breakdown = {}

            for row in energy_mix['energy_mix']:
                carrier = row.get('Carrier')
                energy = row.get('Energy_MWh', 0)

                if carrier in renewable_carriers_list:
                    renewable_energy += energy
                    renewable_breakdown[carrier] = energy

        elif 'percentages' in energy_mix:
            # Format: {'percentages': {carrier: percentage}, 'totals': {...}}
            total_energy = energy_mix.get('totals', {}).get('total_energy_mwh', 0)
            renewable_energy = 0
            renewable_breakdown = {}

            for carrier, percentage in energy_mix.get('percentages', {}).items():
                if carrier in renewable_carriers_list:
                    energy = (percentage / 100) * total_energy if total_energy > 0 else 0
                    renewable_energy += energy
                    renewable_breakdown[carrier] = energy
        else:
            # Fallback: empty result
            total_energy = 0
            renewable_energy = 0
            renewable_breakdown = {}

        renewable_share = (renewable_energy / total_energy) if total_energy > 0 else 0

        breakdown_rows = []
        for carrier, energy in renewable_breakdown.items():
            breakdown_rows.append({
                'Carrier': carrier,
                'Renewable_Energy_MWh': safe_float(energy) or 0.0,
                'Share_%': safe_float((energy / total_energy) * 100) if total_energy > 0 else 0.0
            })

        return {
            'renewable_share_percent': float(renewable_share * 100),
            'renewable_energy_mwh': safe_float(renewable_energy) or 0.0,
            'total_energy_mwh': safe_float(total_energy) or 0.0,
            'renewable_carriers': renewable_carriers_list,
            'breakdown': breakdown_rows
        }
    
    def get_emissions_tracking(self) -> Dict[str, Any]:
        """Get detailed emissions tracking (weighted by snapshot weights)."""
        n = self.n
        
        if not (hasattr(n, 'carriers') and 'co2_emissions' in n.carriers.columns):
            return {
                'emissions': [],
                'total_emissions_tco2': 0.0,
                'emission_intensity_tco2_per_mwh': 0.0
            }
        
        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p')):
            return {
                'emissions': [],
                'total_emissions_tco2': 0.0,
                'emission_intensity_tco2_per_mwh': 0.0
            }
        
        gen_p = n.generators_t.p
        if gen_p.empty:
            return {
                'emissions': [],
                'total_emissions_tco2': 0.0,
                'emission_intensity_tco2_per_mwh': 0.0
            }
        
        weights = get_snapshot_weights(n, gen_p.index)
        emissions_rows: List[Dict[str, Any]] = []
        total_emissions = 0.0
        total_energy = 0.0
        
        if hasattr(n, 'generators') and 'carrier' in n.generators.columns:
            for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
                emission_factor = 0.0
                if carrier in n.carriers.index and 'co2_emissions' in n.carriers.columns:
                    emission_factor = float(n.carriers.loc[carrier, 'co2_emissions'] or 0.0)
                
                carrier_gens = n.generators[n.generators['carrier'] == carrier]
                carrier_gen_names = carrier_gens.index
                cols = gen_p.columns.intersection(carrier_gen_names)
                
                if len(cols) > 0:
                    carrier_gen_p = gen_p[cols]
                    weighted_generation = (carrier_gen_p.T * weights).T.sum().sum()
                    energy = float(weighted_generation)
                    emissions = energy * emission_factor
                    
                    total_emissions += emissions
                    total_energy += energy
                    emissions_rows.append({
                        'Carrier': carrier,
                        'CO2_Emissions_tCO2': safe_float(emissions) or 0.0,
                        'Energy_MWh': safe_float(energy) or 0.0,
                        'Emission_Factor_tCO2_per_MWh': emission_factor
                    })
        
        emission_intensity = (total_emissions / total_energy) if total_energy > 0 else 0.0
        
        return {
            'emissions': emissions_rows,
            'total_emissions_tco2': safe_float(total_emissions) or 0.0,
            'emission_intensity_tco2_per_mwh': safe_float(emission_intensity) or 0.0
        }
    
    def get_system_costs(self) -> Dict[str, Any]:
        """Get system cost breakdown."""
        n = self.n

        if not hasattr(n, 'generators') or n.generators.empty:
            return {'total_capex': 0, 'total_opex': 0, 'total_cost': 0}

        total_capex = 0
        total_opex = 0
        capex_by_carrier = {}
        opex_by_carrier = {}

        if 'carrier' in n.generators.columns:
            for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
                carrier_gens = n.generators[n.generators['carrier'] == carrier]

                if 'capital_cost' in carrier_gens.columns and 'p_nom_opt' in carrier_gens.columns:
                    capex = (carrier_gens['capital_cost'] * carrier_gens['p_nom_opt']).sum()
                    capex_by_carrier[carrier] = float(capex)
                    total_capex += capex

                if 'marginal_cost' in carrier_gens.columns:
                    if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
                        gen_p = n.generators_t.p
                        cols = gen_p.columns.intersection(carrier_gens.index)
                        if len(cols) > 0:
                            for gen in cols:
                                if gen in gen_p.columns:
                                    energy = gen_p[gen].sum()
                                    mc = carrier_gens.loc[gen, 'marginal_cost']
                                    opex = energy * mc
                                    if carrier not in opex_by_carrier:
                                        opex_by_carrier[carrier] = 0
                                    opex_by_carrier[carrier] += float(opex)
                                    total_opex += opex

        cost_rows = []
        for carrier in sorted(set(list(capex_by_carrier.keys()) + list(opex_by_carrier.keys()))):
            cost_rows.append({
                'Carrier': carrier,
                'Capital_Cost': safe_float(capex_by_carrier.get(carrier, 0)) or 0.0,
                'Marginal_Cost': safe_float(opex_by_carrier.get(carrier, 0)) or 0.0,
                'Total_Cost': safe_float(capex_by_carrier.get(carrier, 0) + opex_by_carrier.get(carrier, 0)) or 0.0
            })

        return {
            'costs': cost_rows,
            'total_costs': {
                'total_capex': float(total_capex),
                'total_opex': float(total_opex),
                'total_system_cost': float(total_capex + total_opex)
            }
        }

    def get_marginal_prices(self) -> Dict[str, Any]:
        """Get marginal prices (locational marginal prices) by bus."""
        n = self.n

        if not (hasattr(n, 'buses_t') and hasattr(n.buses_t, 'marginal_price')):
            return {
                'prices': [],
                'price_statistics': {},
                'by_bus': {}
            }

        marginal_prices = n.buses_t.marginal_price
        if marginal_prices.empty:
            return {
                'prices': [],
                'price_statistics': {},
                'by_bus': {}
            }

        # Calculate statistics for each bus
        price_rows = []
        by_bus = {}
        all_prices = []

        for bus in marginal_prices.columns:
            prices = marginal_prices[bus].dropna()
            if len(prices) > 0:
                bus_stats = {
                    'bus': bus,
                    'avg_price': safe_float(prices.mean()),
                    'min_price': safe_float(prices.min()),
                    'max_price': safe_float(prices.max()),
                    'std_price': safe_float(prices.std()),
                    'price_volatility': safe_float(prices.std() / prices.mean() * 100) if prices.mean() != 0 else 0
                }
                price_rows.append(bus_stats)
                by_bus[bus] = {
                    'mean': safe_float(prices.mean()),
                    'min': safe_float(prices.min()),
                    'max': safe_float(prices.max())
                }
                all_prices.extend(prices.values.tolist())

        # Overall statistics
        price_statistics = {}
        if all_prices:
            price_statistics = {
                'avg_price': safe_float(np.mean(all_prices)),
                'min_price': safe_float(np.min(all_prices)),
                'max_price': safe_float(np.max(all_prices)),
                'std_price': safe_float(np.std(all_prices)),
                'price_volatility': safe_float(np.std(all_prices) / np.mean(all_prices) * 100) if np.mean(all_prices) != 0 else 0
            }

        return {
            'prices': price_rows,
            'price_statistics': price_statistics,
            'by_bus': by_bus
        }

    def get_network_losses(self) -> Dict[str, Any]:
        """Get transmission and distribution losses."""
        n = self.n

        losses_data = []
        total_losses = 0

        # Line losses (AC transmission)
        if hasattr(n, 'lines_t') and hasattr(n.lines_t, 'p0') and hasattr(n.lines_t, 'p1'):
            p0 = n.lines_t.p0
            p1 = n.lines_t.p1
            if not p0.empty and not p1.empty:
                # Losses = |p0| - |p1| (considering direction)
                for line in p0.columns:
                    if line in p1.columns:
                        loss = abs(p0[line]).sum() - abs(p1[line]).sum()
                        if loss > 0:
                            losses_data.append({
                                'component': line,
                                'component_type': 'line',
                                'losses_mwh': safe_float(loss),
                                'loss_percentage': 0  # Will calculate below
                            })
                            total_losses += loss

        # Link losses (DC transmission)
        if hasattr(n, 'links_t') and hasattr(n.links_t, 'p0') and hasattr(n.links_t, 'p1'):
            p0 = n.links_t.p0
            p1 = n.links_t.p1
            if not p0.empty and not p1.empty:
                for link in p0.columns:
                    if link in p1.columns:
                        loss = abs(p0[link]).sum() - abs(p1[link]).sum()
                        if loss > 0:
                            losses_data.append({
                                'component': link,
                                'component_type': 'link',
                                'losses_mwh': safe_float(loss),
                                'loss_percentage': 0
                            })
                            total_losses += loss

        # Calculate total generation for loss percentage
        total_generation = 0
        if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
            total_generation = n.generators_t.p.sum().sum()

        # Calculate loss percentages
        loss_percentage = (total_losses / total_generation * 100) if total_generation > 0 else 0
        for item in losses_data:
            item['loss_percentage'] = safe_float(item['losses_mwh'] / total_generation * 100) if total_generation > 0 else 0

        return {
            'losses': losses_data,
            'total_losses': safe_float(total_losses),
            'loss_percentage': safe_float(loss_percentage),
            'avg_loss_rate': safe_float(loss_percentage)
        }

    def get_curtailment(self) -> Dict[str, Any]:
        """
        Get renewable curtailment analysis dynamically.

        Uses detect_renewable_carriers() to identify which generators to analyze.
        """
        n = self.n

        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p') and hasattr(n.generators_t, 'p_max_pu')):
            return {
                'curtailment': [],
                'total_curtailed': 0,
                'curtailment_rate': 0,
                'potential_generation': 0
            }

        gen_p = n.generators_t.p
        gen_p_max_pu = n.generators_t.p_max_pu

        if gen_p.empty or gen_p_max_pu.empty:
            return {
                'curtailment': [],
                'total_curtailed': 0,
                'curtailment_rate': 0,
                'potential_generation': 0
            }

        curtailment_rows = []
        total_curtailed = 0
        total_potential = 0

        # Get renewable carriers dynamically from network
        renewable_carriers_list = detect_renewable_carriers(n)

        if not renewable_carriers_list:
            logger.warning("No renewable carriers detected for curtailment analysis")
            return {
                'curtailment': [],
                'total_curtailed': 0,
                'curtailment_rate': 0,
                'potential_generation': 0
            }

        # Get capacity column dynamically
        capacity_col = get_capacity_column(n, 'generators')
        if not capacity_col:
            logger.error("No capacity column found for generators")
            return {
                'curtailment': [],
                'total_curtailed': 0,
                'curtailment_rate': 0,
                'potential_generation': 0
            }

        if hasattr(n, 'generators') and 'carrier' in n.generators.columns:
            for carrier in n.generators['carrier'].unique():
                # Only analyze renewable carriers
                if carrier not in renewable_carriers_list:
                    continue

                carrier_gens = n.generators[n.generators['carrier'] == carrier]

                for gen_name in carrier_gens.index:
                    if gen_name in gen_p.columns and gen_name in gen_p_max_pu.columns:
                        actual_gen = gen_p[gen_name].sum()

                        # Get capacity using dynamic column
                        capacity = carrier_gens.loc[gen_name, capacity_col]

                        # Calculate potential generation
                        potential_gen = (gen_p_max_pu[gen_name] * capacity).sum()

                        curtailed = potential_gen - actual_gen

                        if curtailed > 0.01:  # Small threshold to avoid rounding errors
                            curtailment_pct = (curtailed / potential_gen * 100) if potential_gen > 0 else 0

                            curtailment_rows.append({
                                'carrier': carrier,
                                'generator': gen_name,
                                'curtailment_mwh': safe_float(curtailed),
                                'curtailment_percent': safe_float(curtailment_pct),
                                'actual_generation': safe_float(actual_gen),
                                'potential_generation': safe_float(potential_gen)
                            })

                            total_curtailed += curtailed
                            total_potential += potential_gen

        curtailment_rate = (total_curtailed / total_potential * 100) if total_potential > 0 else 0

        return {
            'curtailment': curtailment_rows,
            'total_curtailed': safe_float(total_curtailed),
            'curtailment_rate': safe_float(curtailment_rate),
            'potential_generation': safe_float(total_potential),
            'renewable_carriers_analyzed': renewable_carriers_list
        }

    def _extract_years_from_multiindex(self) -> List[int]:
        """
        Extract years from multi-period network snapshots.

        Returns:
            List of years found in the network
        """
        n = self.n

        if not is_multi_period(n):
            # Try to extract year from single period snapshots
            if hasattr(n, 'snapshots') and len(n.snapshots) > 0:
                first_snapshot = n.snapshots[0]
                if isinstance(first_snapshot, pd.Timestamp):
                    return [first_snapshot.year]
            return []

        # Multi-period network
        try:
            period_index = get_period_index(n.snapshots)
            if isinstance(period_index, pd.Index):
                # Try to extract years from period values
                years = []
                for period in period_index.unique():
                    # Period might be integer year or timestamp
                    if isinstance(period, (int, np.integer)):
                        years.append(int(period))
                    elif isinstance(period, pd.Timestamp):
                        years.append(period.year)
                    elif isinstance(period, str):
                        # Try to extract year from string
                        try:
                            year = int(period)
                            years.append(year)
                        except ValueError:
                            pass
                return sorted(list(set(years)))
            return []
        except Exception as e:
            logger.error(f"Error extracting years from multi-period network: {e}")
            return []

    def get_capacity_factors_multi_period(self) -> Dict[str, Any]:
        """
        Get capacity factors aggregated by year for multi-period networks.

        Returns:
            {
                'capacity_factors': [
                    {'Carrier': 'Solar', '2025': 23.5, '2026': 24.1},
                    {'Carrier': 'Wind', '2025': 35.2, '2026': 36.8}
                ],
                'years': [2025, 2026]
            }
        """
        n = self.n

        if not is_multi_period(n):
            # Single period - use regular method and format
            single_data = self.get_capacity_factors()
            utilization = single_data.get('utilization', [])

            # Get year from snapshots
            years = self._extract_years_from_multiindex()
            year = years[0] if years else 2025

            # Transform to multi-period format
            capacity_factors = []
            for item in utilization:
                capacity_factors.append({
                    'Carrier': item['Carrier'],
                    str(year): item['Utilization_%']
                })

            return {
                'capacity_factors': capacity_factors,
                'years': [year]
            }

        # Multi-period network
        years = self._extract_years_from_multiindex()
        if not years:
            return {'capacity_factors': [], 'years': []}

        gen_p = n.generators_t.p
        if gen_p.empty or not hasattr(n, 'generators') or 'carrier' not in n.generators.columns:
            return {'capacity_factors': [], 'years': years}

        # Get capacity column
        capacity_col = 'p_nom_opt' if 'p_nom_opt' in n.generators.columns else 'p_nom'
        if capacity_col not in n.generators.columns:
            return {'capacity_factors': [], 'years': years}

        # Group by carrier and year
        carrier_year_cuf = {}
        period_index = get_period_index(n.snapshots)

        for carrier in sorted(n.generators['carrier'].dropna().unique().tolist()):
            carrier_gens = n.generators[n.generators['carrier'] == carrier]
            carrier_gen_names = carrier_gens.index
            cols = gen_p.columns.intersection(carrier_gen_names)

            if len(cols) == 0:
                continue

            carrier_data = {}

            for year in years:
                try:
                    # Filter snapshots for this year
                    year_mask = [p == year or (isinstance(p, pd.Timestamp) and p.year == year) for p in period_index]
                    year_snapshots = n.snapshots[year_mask]

                    if len(year_snapshots) == 0:
                        continue

                    # Get generation data for this year
                    year_gen_p = gen_p.loc[year_snapshots, cols]
                    weights = get_snapshot_weights(n, year_snapshots)
                    weighted_hours = weights.sum()

                    # Calculate energy and potential
                    weighted_energy = (year_gen_p.T * weights).T.sum().sum()
                    capacity = carrier_gens[capacity_col].sum()
                    potential = capacity * weighted_hours

                    if potential > 0:
                        cf = (weighted_energy / potential) * 100  # As percentage
                        carrier_data[str(year)] = safe_float(cf) or 0.0
                    else:
                        carrier_data[str(year)] = 0.0

                except Exception as e:
                    logger.error(f"Error calculating CUF for {carrier} in year {year}: {e}")
                    carrier_data[str(year)] = 0.0

            if carrier_data:
                carrier_year_cuf[carrier] = carrier_data

        # Format output
        capacity_factors = []
        for carrier, year_data in carrier_year_cuf.items():
            row = {'Carrier': carrier}
            row.update(year_data)
            capacity_factors.append(row)

        return {
            'capacity_factors': capacity_factors,
            'years': years
        }

    def get_renewable_share_multi_period(self) -> Dict[str, Any]:
        """
        Get renewable share aggregated by year for multi-period networks.

        Returns:
            {
                'renewable_share_percent': {'2025': 48.4, '2026': 52.1},
                'renewable_energy_mwh': {'2025': 15612441.2, '2026': 16800000.0},
                'total_energy_mwh': {'2025': 32256052.7, '2026': 32300000.0},
                'renewable_carriers': [...],
                'breakdown': [
                    {
                        'Carrier': 'Solar',
                        'Renewable_Energy_MWh': {'2025': 3342332.3, '2026': 3500000.0},
                        'Share_%': {'2025': 10.36, '2026': 10.83}
                    }
                ],
                'years': [2025, 2026]
            }
        """
        n = self.n

        if not is_multi_period(n):
            # Single period - use regular method and format
            single_data = self.get_renewable_share()

            # Get year
            years = self._extract_years_from_multiindex()
            year = years[0] if years else 2025
            year_str = str(year)

            # Transform to multi-period format
            result = {
                'renewable_share_percent': {year_str: single_data['renewable_share_percent']},
                'renewable_energy_mwh': {year_str: single_data['renewable_energy_mwh']},
                'total_energy_mwh': {year_str: single_data['total_energy_mwh']},
                'renewable_carriers': single_data['renewable_carriers'],
                'breakdown': [],
                'years': [year]
            }

            # Transform breakdown
            for item in single_data.get('breakdown', []):
                result['breakdown'].append({
                    'Carrier': item['Carrier'],
                    'Renewable_Energy_MWh': {year_str: item['Renewable_Energy_MWh']},
                    'Share_%': {year_str: item['Share_%']}
                })

            return result

        # Multi-period network
        years = self._extract_years_from_multiindex()
        if not years:
            return {
                'renewable_share_percent': {},
                'renewable_energy_mwh': {},
                'total_energy_mwh': {},
                'renewable_carriers': [],
                'breakdown': [],
                'years': []
            }

        renewable_carriers_list = detect_renewable_carriers(n)
        gen_p = n.generators_t.p

        if gen_p.empty or not hasattr(n, 'generators') or 'carrier' not in n.generators.columns:
            return {
                'renewable_share_percent': {str(y): 0.0 for y in years},
                'renewable_energy_mwh': {str(y): 0.0 for y in years},
                'total_energy_mwh': {str(y): 0.0 for y in years},
                'renewable_carriers': renewable_carriers_list,
                'breakdown': [],
                'years': years
            }

        period_index = get_period_index(n.snapshots)

        # Aggregate data by year
        year_data = {}
        carrier_year_data = {}

        for year in years:
            try:
                # Filter snapshots for this year
                year_mask = [p == year or (isinstance(p, pd.Timestamp) and p.year == year) for p in period_index]
                year_snapshots = n.snapshots[year_mask]

                if len(year_snapshots) == 0:
                    continue

                year_gen_p = gen_p.loc[year_snapshots]
                weights = get_snapshot_weights(n, year_snapshots)

                total_energy = 0
                renewable_energy = 0
                carrier_energies = {}

                for carrier in n.generators['carrier'].dropna().unique():
                    carrier_gens = n.generators[n.generators['carrier'] == carrier]
                    cols = year_gen_p.columns.intersection(carrier_gens.index)

                    if len(cols) > 0:
                        weighted_energy = (year_gen_p[cols].T * weights).T.sum().sum()
                        total_energy += weighted_energy
                        carrier_energies[carrier] = weighted_energy

                        if carrier in renewable_carriers_list:
                            renewable_energy += weighted_energy

                renewable_share = (renewable_energy / total_energy * 100) if total_energy > 0 else 0

                year_data[str(year)] = {
                    'renewable_share_percent': safe_float(renewable_share) or 0.0,
                    'renewable_energy_mwh': safe_float(renewable_energy) or 0.0,
                    'total_energy_mwh': safe_float(total_energy) or 0.0
                }

                # Store carrier data for this year
                for carrier, energy in carrier_energies.items():
                    if carrier not in carrier_year_data:
                        carrier_year_data[carrier] = {}
                    share_pct = (energy / total_energy * 100) if total_energy > 0 else 0
                    carrier_year_data[carrier][str(year)] = {
                        'energy': safe_float(energy) or 0.0,
                        'share': safe_float(share_pct) or 0.0
                    }

            except Exception as e:
                logger.error(f"Error processing year {year}: {e}")
                year_data[str(year)] = {
                    'renewable_share_percent': 0.0,
                    'renewable_energy_mwh': 0.0,
                    'total_energy_mwh': 0.0
                }

        # Format breakdown
        breakdown = []
        for carrier in renewable_carriers_list:
            if carrier in carrier_year_data:
                breakdown.append({
                    'Carrier': carrier,
                    'Renewable_Energy_MWh': {year: carrier_year_data[carrier][year]['energy'] for year in carrier_year_data[carrier]},
                    'Share_%': {year: carrier_year_data[carrier][year]['share'] for year in carrier_year_data[carrier]}
                })

        # Aggregate results
        return {
            'renewable_share_percent': {year: year_data[year]['renewable_share_percent'] for year in year_data},
            'renewable_energy_mwh': {year: year_data[year]['renewable_energy_mwh'] for year in year_data},
            'total_energy_mwh': {year: year_data[year]['total_energy_mwh'] for year in year_data},
            'renewable_carriers': renewable_carriers_list,
            'breakdown': breakdown,
            'years': years
        }

    def get_curtailment_multi_period(self) -> Dict[str, Any]:
        """
        Get curtailment analysis aggregated by year for multi-period networks.

        Returns:
            {
                'curtailment': [
                    {
                        'Carrier': 'Solar',
                        'Curtailment_MWh': {'2025': 1500, '2026': 1600},
                        'Potential_MWh': {'2025': 30000, '2026': 32000},
                        'Curtailment_%': {'2025': 5.0, '2026': 5.0}
                    }
                ],
                'years': [2025, 2026]
            }
        """
        n = self.n

        if not is_multi_period(n):
            # Single period - use regular method and format
            single_data = self.get_curtailment()

            # Get year
            years = self._extract_years_from_multiindex()
            year = years[0] if years else 2025
            year_str = str(year)

            # Aggregate curtailment by carrier
            curtailment_by_carrier = {}
            for item in single_data.get('curtailment', []):
                carrier = item['carrier']
                if carrier not in curtailment_by_carrier:
                    curtailment_by_carrier[carrier] = {
                        'curtailment_mwh': 0,
                        'potential_mwh': 0
                    }
                curtailment_by_carrier[carrier]['curtailment_mwh'] += item['curtailment_mwh']
                curtailment_by_carrier[carrier]['potential_mwh'] += item['potential_generation']

            # Transform to multi-period format
            curtailment = []
            for carrier, data in curtailment_by_carrier.items():
                curtailment_pct = (data['curtailment_mwh'] / data['potential_mwh'] * 100) if data['potential_mwh'] > 0 else 0
                curtailment.append({
                    'Carrier': carrier,
                    'Curtailment_MWh': {year_str: data['curtailment_mwh']},
                    'Potential_MWh': {year_str: data['potential_mwh']},
                    'Curtailment_%': {year_str: curtailment_pct}
                })

            return {
                'curtailment': curtailment,
                'years': [year]
            }

        # Multi-period network
        years = self._extract_years_from_multiindex()
        if not years:
            return {'curtailment': [], 'years': []}

        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p') and hasattr(n.generators_t, 'p_max_pu')):
            return {'curtailment': [], 'years': years}

        gen_p = n.generators_t.p
        gen_p_max_pu = n.generators_t.p_max_pu

        if gen_p.empty or gen_p_max_pu.empty:
            return {'curtailment': [], 'years': years}

        renewable_carriers_list = detect_renewable_carriers(n)
        if not renewable_carriers_list:
            return {'curtailment': [], 'years': years}

        capacity_col = get_capacity_column(n, 'generators')
        if not capacity_col:
            return {'curtailment': [], 'years': years}

        period_index = get_period_index(n.snapshots)
        carrier_year_curtailment = {}

        for year in years:
            try:
                # Filter snapshots for this year
                year_mask = [p == year or (isinstance(p, pd.Timestamp) and p.year == year) for p in period_index]
                year_snapshots = n.snapshots[year_mask]

                if len(year_snapshots) == 0:
                    continue

                year_gen_p = gen_p.loc[year_snapshots]
                year_gen_p_max_pu = gen_p_max_pu.loc[year_snapshots]
                weights = get_snapshot_weights(n, year_snapshots)
                weights_mean = weights.mean()

                for carrier in renewable_carriers_list:
                    carrier_gens = n.generators[n.generators['carrier'] == carrier]

                    for gen_name in carrier_gens.index:
                        if gen_name in year_gen_p.columns and gen_name in year_gen_p_max_pu.columns:
                            actual_gen = year_gen_p[gen_name].sum()
                            capacity = carrier_gens.loc[gen_name, capacity_col]
                            potential_gen = (year_gen_p_max_pu[gen_name] * capacity).sum()
                            curtailed = potential_gen - actual_gen

                            if curtailed > 0.01:
                                if carrier not in carrier_year_curtailment:
                                    carrier_year_curtailment[carrier] = {}

                                if str(year) not in carrier_year_curtailment[carrier]:
                                    carrier_year_curtailment[carrier][str(year)] = {
                                        'curtailment': 0,
                                        'potential': 0
                                    }

                                carrier_year_curtailment[carrier][str(year)]['curtailment'] += curtailed
                                carrier_year_curtailment[carrier][str(year)]['potential'] += potential_gen

            except Exception as e:
                logger.error(f"Error calculating curtailment for year {year}: {e}")

        # Format output
        curtailment = []
        for carrier, year_data in carrier_year_curtailment.items():
            row = {'Carrier': carrier}
            curtailment_mwh = {}
            potential_mwh = {}
            curtailment_pct = {}

            for year_str, data in year_data.items():
                curtailment_mwh[year_str] = safe_float(data['curtailment']) or 0.0
                potential_mwh[year_str] = safe_float(data['potential']) or 0.0
                pct = (data['curtailment'] / data['potential'] * 100) if data['potential'] > 0 else 0
                curtailment_pct[year_str] = safe_float(pct) or 0.0

            row['Curtailment_MWh'] = curtailment_mwh
            row['Potential_MWh'] = potential_mwh
            row['Curtailment_%'] = curtailment_pct
            curtailment.append(row)

        return {
            'curtailment': curtailment,
            'years': years
        }

    def get_daily_profiles(self) -> Dict[str, Any]:
        """Get average generation profiles by hour of day."""
        n = self.n

        if not (hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p')):
            return {
                'profiles': [],
                'by_hour': {},
                'peak_hour': None,
                'off_peak_hour': None
            }

        gen_p = n.generators_t.p
        if gen_p.empty:
            return {
                'profiles': [],
                'by_hour': {},
                'peak_hour': None,
                'off_peak_hour': None
            }

        # Extract time index
        time_index = get_time_index(n.snapshots)

        # Create DataFrame with hour of day
        hourly_data = gen_p.copy()
        hourly_data.index = time_index
        hourly_data['hour'] = hourly_data.index.hour

        # Group by hour and carrier
        profiles = []
        by_hour = {}

        if hasattr(n, 'generators') and 'carrier' in n.generators.columns:
            for hour in range(24):
                hour_data = hourly_data[hourly_data['hour'] == hour]
                by_hour[hour] = {}

                for carrier in n.generators['carrier'].unique():
                    carrier_gens = n.generators[n.generators['carrier'] == carrier].index
                    cols = hour_data.columns.intersection(carrier_gens)

                    if len(cols) > 0:
                        avg_gen = hour_data[cols].mean().mean()
                        by_hour[hour][carrier] = safe_float(avg_gen)

                        profiles.append({
                            'hour': hour,
                            'carrier': carrier,
                            'avg_generation': safe_float(avg_gen)
                        })

        # Find peak and off-peak hours
        hourly_totals = {hour: sum(by_hour.get(hour, {}).values()) for hour in range(24)}
        peak_hour = max(hourly_totals, key=hourly_totals.get) if hourly_totals else None
        off_peak_hour = min(hourly_totals, key=hourly_totals.get) if hourly_totals else None

        return {
            'profiles': profiles,
            'by_hour': by_hour,
            'peak_hour': peak_hour,
            'off_peak_hour': off_peak_hour,
            'daily_range': safe_float(hourly_totals[peak_hour] - hourly_totals[off_peak_hour]) if peak_hour and off_peak_hour else 0
        }

    def get_duration_curves(self) -> Dict[str, Any]:
        """Get load and generation duration curves."""
        n = self.n

        duration_data = []

        # Generation duration curve
        if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
            gen_p = n.generators_t.p
            if not gen_p.empty:
                total_gen = gen_p.sum(axis=1).sort_values(ascending=False).reset_index(drop=True)
                for i, value in enumerate(total_gen):
                    duration_data.append({
                        'hours': i,
                        'type': 'generation',
                        'power_mw': safe_float(value)
                    })

        # Load duration curve
        if hasattr(n, 'loads_t') and hasattr(n.loads_t, 'p'):
            load_p = n.loads_t.p
            if not load_p.empty:
                total_load = load_p.sum(axis=1).sort_values(ascending=False).reset_index(drop=True)
                for i, value in enumerate(total_load):
                    duration_data.append({
                        'hours': i,
                        'type': 'load',
                        'power_mw': safe_float(value)
                    })

        # Calculate metrics
        peak_value = None
        baseload = None
        if duration_data:
            gen_data = [d for d in duration_data if d['type'] == 'generation']
            if gen_data:
                peak_value = max(d['power_mw'] for d in gen_data)
                baseload = min(d['power_mw'] for d in gen_data)

        return {
            'duration_curves': duration_data,
            'peak_value': safe_float(peak_value) if peak_value else None,
            'baseload': safe_float(baseload) if baseload else None,
            'capacity_factor': safe_float(baseload / peak_value) if peak_value and baseload else None
        }

    def get_storage_operation(self) -> Dict[str, Any]:
        """Get detailed storage operation time series."""
        n = self.n

        storage_data = {
            'storage_units': [],
            'stores': []
        }

        # Storage units (PHS)
        if hasattr(n, 'storage_units_t') and hasattr(n.storage_units_t, 'state_of_charge'):
            soc = n.storage_units_t.state_of_charge
            if not soc.empty:
                time_index = get_time_index(n.snapshots)
                for unit in soc.columns:
                    soc_series = soc[unit]
                    storage_data['storage_units'].append({
                        'storage_unit': unit,
                        'avg_soc': safe_float(soc_series.mean()),
                        'max_soc': safe_float(soc_series.max()),
                        'min_soc': safe_float(soc_series.min()),
                        'total_cycles': safe_float(len(soc_series) / (2 * 24)) if len(soc_series) > 0 else 0  # Rough estimate
                    })

        # Stores (BESS)
        if hasattr(n, 'stores_t') and hasattr(n.stores_t, 'e'):
            store_e = n.stores_t.e
            if not store_e.empty:
                for store in store_e.columns:
                    e_series = store_e[store]
                    storage_data['stores'].append({
                        'store': store,
                        'avg_stored': safe_float(e_series.mean()),
                        'max_stored': safe_float(e_series.max()),
                        'min_stored': safe_float(e_series.min())
                    })

        return storage_data

    def get_transmission_flows(self) -> Dict[str, Any]:
        """Get transmission line flows and utilization."""
        n = self.n

        transmission_data = {
            'lines': [],
            'links': []
        }

        # AC lines
        if hasattr(n, 'lines_t') and hasattr(n.lines_t, 'p0'):
            line_flows = n.lines_t.p0
            if not line_flows.empty and hasattr(n, 'lines'):
                for line in line_flows.columns:
                    if line in n.lines.index:
                        flow_series = line_flows[line]
                        s_nom = n.lines.loc[line, 's_nom_opt'] if 's_nom_opt' in n.lines.columns else n.lines.loc[line, 's_nom']

                        avg_utilization = (abs(flow_series).mean() / s_nom * 100) if s_nom > 0 else 0

                        transmission_data['lines'].append({
                            'line': line,
                            'avg_flow_mw': safe_float(flow_series.mean()),
                            'max_flow_mw': safe_float(flow_series.max()),
                            'capacity_mw': safe_float(s_nom),
                            'avg_utilization_pct': safe_float(avg_utilization)
                        })

        # DC links
        if hasattr(n, 'links_t') and hasattr(n.links_t, 'p0'):
            link_flows = n.links_t.p0
            if not link_flows.empty and hasattr(n, 'links'):
                for link in link_flows.columns:
                    if link in n.links.index:
                        flow_series = link_flows[link]
                        p_nom = n.links.loc[link, 'p_nom_opt'] if 'p_nom_opt' in n.links.columns else n.links.loc[link, 'p_nom']

                        avg_utilization = (abs(flow_series).mean() / p_nom * 100) if p_nom > 0 else 0

                        transmission_data['links'].append({
                            'link': link,
                            'avg_flow_mw': safe_float(flow_series.mean()),
                            'max_flow_mw': safe_float(flow_series.max()),
                            'capacity_mw': safe_float(p_nom),
                            'avg_utilization_pct': safe_float(avg_utilization)
                        })

        return transmission_data

    def get_load_profiles(self) -> Dict[str, Any]:
        """Get load demand profiles and patterns."""
        n = self.n

        if not (hasattr(n, 'loads_t') and hasattr(n.loads_t, 'p')):
            return {
                'loads': [],
                'total_demand': 0,
                'peak_demand': 0,
                'avg_demand': 0
            }

        load_p = n.loads_t.p
        if load_p.empty:
            return {
                'loads': [],
                'total_demand': 0,
                'peak_demand': 0,
                'avg_demand': 0
            }

        load_rows = []
        total_demand = load_p.sum().sum()
        peak_demand = load_p.sum(axis=1).max()
        avg_demand = load_p.sum(axis=1).mean()

        for load in load_p.columns:
            load_series = load_p[load]
            load_rows.append({
                'load': load,
                'total_demand': safe_float(load_series.sum()),
                'peak_demand': safe_float(load_series.max()),
                'avg_demand': safe_float(load_series.mean())
            })

        return {
            'loads': load_rows,
            'total_demand': safe_float(total_demand),
            'peak_demand': safe_float(peak_demand),
            'avg_demand': safe_float(avg_demand)
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_single_network(network_path: str) -> Dict[str, Any]:
    """
    Analyze a single network file.
    
    Args:
        network_path: Path to network file
    
    Returns:
        Complete analysis results
    """
    network = load_network_cached(network_path)
    analyzer = PyPSASingleNetworkAnalyzer(network)
    return analyzer.run_all_analyses()


def inspect_network_file(filepath: str) -> Dict[str, Any]:
    """
    Inspect a network file and return availability.
    
    Args:
        filepath: Path to network file
    
    Returns:
        Availability information
    """
    network = load_network_cached(filepath)
    inspector = NetworkInspector(network)
    return inspector.get_full_availability()


# =============================================================================
# COLOR PALETTE
# =============================================================================

def get_color_palette() -> Dict[str, str]:
    """
    Get standard fallback color palette for carriers.

    NOTE: This is only used as a fallback when network.carriers.color is not available.
    Always check network.carriers.color first for user-defined colors.
    """
    return {
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
    """
    Get color for carrier dynamically.

    Priority:
    1. network.carriers['color'] (user-defined)
    2. Fallback color palette (standard colors)
    3. Hash-generated color (for unknown carriers)

    Args:
        carrier: Carrier name
        network: PyPSA network (optional, for carrier-specific colors)

    Returns:
        Hex color code
    """
    # Strategy 1: Check network.carriers for user-defined color
    if network and hasattr(network, 'carriers'):
        if carrier in network.carriers.index and 'color' in network.carriers.columns:
            color = network.carriers.loc[carrier, 'color']
            if pd.notna(color) and color:
                # Validate color format
                if isinstance(color, str) and (color.startswith('#') or len(color) == 6):
                    return color if color.startswith('#') else f'#{color}'

    # Strategy 2: Use fallback palette
    colors = get_color_palette()
    carrier_lower = carrier.lower()

    for key, color in colors.items():
        if key.lower() == carrier_lower or key.lower() in carrier_lower:
            return color

    # Strategy 3: Generate consistent color from carrier name hash
    color_hash = hashlib.md5(carrier.encode()).hexdigest()[:6]
    return f'#{color_hash}'


def get_all_colors_for_network(network: pypsa.Network) -> Dict[str, str]:
    """
    Get colors for all carriers in network.

    Args:
        network: PyPSA network

    Returns:
        Dict mapping carrier names to hex colors
    """
    color_map = {}

    if not (hasattr(network, 'carriers') and not network.carriers.empty):
        return color_map

    for carrier in network.carriers.index:
        color_map[carrier] = get_color(carrier, network)

    return color_map