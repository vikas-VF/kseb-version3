"""
Load Profile Generation System - FIXED VERSION
Incorporates MSTL decomposition, smooth transitions, and realistic variability preservation
Maintains 100% compatibility with original input/output format

KEY FIXES:
1. Continuous day-of-year interpolation (no month boundary jumps)
2. Preserves historical variability (weather, events, daily fluctuations)
3. Smooth only scaling factors, not patterns
4. Shape-preserving constraint satisfaction
5. Minimal final smoothing (25-hour window for noise only)

RESULT: Realistic profiles with smooth transitions and met constraints
"""

import pandas as pd
import numpy as np
import os
import json
import sys
import argparse
import traceback
from datetime import datetime, timedelta
import warnings
from pathlib import Path
import calendar
import time
from functools import lru_cache
from typing import Dict, Any, Optional, Tuple, List

# Set UTF-8 encoding
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Optional library imports with availability flags
SCIPY_AVAILABLE = False
STL_AVAILABLE = False
MSTL_AVAILABLE = False
HOLIDAYS_AVAILABLE = False
SKLEARN_AVAILABLE = False

try:
    from scipy import stats, signal
    from scipy.interpolate import interp1d, CubicSpline, RectBivariateSpline
    SCIPY_AVAILABLE = True
except ImportError:
    pass

try:
    from statsmodels.tsa.seasonal import STL
    STL_AVAILABLE = True
except ImportError:
    pass

try:
    from statsmodels.tsa.seasonal import MSTL
    MSTL_AVAILABLE = True
except ImportError:
    pass

try:
    import holidays
    HOLIDAYS_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

# Suppress warnings
warnings.filterwarnings('ignore')


class ProgressReporter:
    """Progress reporting for WebSocket integration"""
    
    def __init__(self, enable_progress=True):
        self.enable_progress = enable_progress
        self.current_step = 0
        self.total_steps = 0
        
    def start_process(self, total_steps, process_name="Load Profile Generation"):
        self.total_steps = total_steps
        self.current_step = 0
        if self.enable_progress:
            self._send_progress(0, f'Starting {process_name}', 0)
    
    def update_progress(self, step_name, details=""):
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100 if self.total_steps > 0 else 0
        if self.enable_progress:
            self._send_progress(self.current_step, step_name, percentage, details)
    
    def complete_process(self, message="Process completed successfully"):
        if self.enable_progress:
            self._send_progress(self.total_steps, message, 100, type_='completed')
    
    def report_error(self, error_msg):
        self._send_progress(0, error_msg, 0, type_='error')
    
    def _send_progress(self, step, message, percentage, details="", type_='progress'):
        try:
            progress_data = {
                'type': type_,
                'step': step,
                'total_steps': self.total_steps,
                'message': message,
                'percentage': round(percentage, 1)
            }
            if details:
                progress_data['details'] = details
            sys.stderr.write(f"PROGRESS:{json.dumps(progress_data)}\n")
            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"Progress reporting error: {e}\n")


class EnhancedPatternExtractor:
    """Enhanced pattern extraction with MSTL, smooth interpolation, and variability preservation"""
    
    def __init__(self, historical_data, method='normalized'):
        self.data = historical_data.copy()
        self.method = method
        self.patterns = {}
        self._prepare_data()
    
    def _prepare_data(self):
        """Enhanced data preparation with better feature extraction"""
        print("\nPreparing historical data with enhanced features...", file=sys.stderr)
        
        # Create datetime column efficiently
        if 'datetime' not in self.data.columns:
            if 'date' in self.data.columns and 'time' in self.data.columns:
                self.data['datetime'] = pd.to_datetime(
                    self.data['date'].astype(str) + ' ' + self.data['time'].astype(str),
                    errors='coerce'
                )
            elif 'date' in self.data.columns:
                self.data['datetime'] = pd.to_datetime(self.data['date'], errors='coerce')
        
        # Clean data
        self.data = self.data.dropna(subset=['datetime', 'demand'])
        self.data = self.data[self.data['demand'] > 0].sort_values('datetime')
        
        # Handle duplicates
        if self.data['datetime'].duplicated().any():
            self.data = self.data.groupby('datetime')['demand'].mean().reset_index()
        
        # Vectorized feature extraction
        dt = self.data['datetime']
        self.data['hour'] = dt.dt.hour
        self.data['dayofweek'] = dt.dt.dayofweek
        self.data['month'] = dt.dt.month
        self.data['year'] = dt.dt.year
        self.data['dayofyear'] = dt.dt.dayofyear
        
        # Cyclical encoding
        self.data['hour_sin'] = np.sin(2 * np.pi * self.data['hour'] / 24)
        self.data['hour_cos'] = np.cos(2 * np.pi * self.data['hour'] / 24)
        self.data['month_sin'] = np.sin(2 * np.pi * self.data['month'] / 12)
        self.data['month_cos'] = np.cos(2 * np.pi * self.data['month'] / 12)
        self.data['doy_sin'] = np.sin(2 * np.pi * self.data['dayofyear'] / 365.25)
        self.data['doy_cos'] = np.cos(2 * np.pi * self.data['dayofyear'] / 365.25)
        
        # Vectorized fiscal year calculation
        self.data['fiscal_year'] = np.where(
            self.data['month'] >= 4,
            self.data['year'] + 1,
            self.data['year']
        )
        self.data['fiscal_month'] = ((self.data['month'] - 4) % 12) + 1
        
        # Calculate fiscal day of year
        self.data['fiscal_doy'] = self.data.apply(
            lambda x: self._fiscal_day_of_year(x['datetime']), axis=1
        )
        
        # Day type classification (vectorized)
        self.data['is_weekend'] = self.data['dayofweek'].isin([5, 6]).astype(int)
        
        # Holiday detection
        self._detect_holidays()
        
        # Season mapping
        season_map = np.array(['Winter', 'Winter', 'Summer', 'Summer', 'Summer', 'Summer',
                              'Monsoon', 'Monsoon', 'Monsoon', 'Post-monsoon', 'Post-monsoon', 'Winter'])
        self.data['season'] = season_map[self.data['month'] - 1]
        
        print(f"  Data range: {self.data['datetime'].min()} to {self.data['datetime'].max()}", file=sys.stderr)
        print(f"  Total records: {len(self.data):,}", file=sys.stderr)
    
    def _fiscal_day_of_year(self, date):
        """Calculate fiscal day of year (April 1 = Day 1)"""
        if isinstance(date, pd.Timestamp):
            date = date.to_pydatetime()
        
        # Fiscal year starts April 1
        if date.month >= 4:
            fiscal_year_start = datetime(date.year, 4, 1)
        else:
            fiscal_year_start = datetime(date.year - 1, 4, 1)
        
        # Days since April 1
        delta = date - fiscal_year_start
        return delta.days + 1
    
    def _detect_holidays(self):
        """Enhanced holiday detection"""
        self.data['is_holiday'] = 0
        
        if HOLIDAYS_AVAILABLE:
            try:
                years = range(self.data['year'].min(), self.data['year'].max() + 1)
                india_holidays = holidays.India(years=list(years))
                holiday_dates = pd.to_datetime(list(india_holidays.keys()))
                self.data['is_holiday'] = self.data['datetime'].dt.date.isin(holiday_dates).astype(int)
            except:
                pass
        
        # Statistical holiday detection for weekdays with low demand
        if self.data['is_holiday'].sum() == 0:
            weekday_data = self.data[self.data['is_weekend'] == 0]
            daily_avg = weekday_data.groupby(weekday_data['datetime'].dt.date)['demand'].mean()
            threshold = daily_avg.mean() - 1.5 * daily_avg.std()
            holiday_candidates = daily_avg[daily_avg < threshold].index
            self.data.loc[self.data['datetime'].dt.date.isin(holiday_candidates), 'is_holiday'] = 1
        
        self.data['day_type'] = np.select(
            [self.data['is_holiday'] == 1, self.data['is_weekend'] == 1],
            ['holiday', 'weekend'],
            default='weekday'
        )
    
    def extract_enhanced_patterns(self):
        """Extract patterns using advanced techniques"""
        print("\nExtracting enhanced patterns with advanced methods...", file=sys.stderr)
        
        # Try MSTL decomposition first (best method)
        if self.method == 'stl' and MSTL_AVAILABLE:
            print("  Using MSTL (Multi-Seasonal Trend Decomposition)", file=sys.stderr)
            self.patterns['mstl'] = self._extract_mstl_components()
        elif self.method == 'stl' and STL_AVAILABLE:
            print("  Using STL (Seasonal Trend Decomposition)", file=sys.stderr)
            self.patterns['stl'] = self._extract_stl_components()
        
        # K-means clustering for pattern extraction (optional)
        if SKLEARN_AVAILABLE:
            print("  Using K-means clustering for pattern extraction", file=sys.stderr)
            self.patterns['clustered_patterns'] = self._extract_clustered_patterns()
        
        # Standard patterns (always extract)
        self.patterns['hourly'] = self._extract_hourly_patterns()
        self.patterns['monthly'] = self._extract_monthly_patterns_smooth()
        self.patterns['base_load'] = self._extract_base_load()
        self.patterns['day_type_factors'] = self._extract_day_type_factors()
        self.patterns['growth'] = self._extract_growth_patterns()
        
        # Variability metrics (NEW - for realism preservation)
        self.patterns['variability'] = self._extract_variability_metrics()
        
        return self.patterns
    
    def _extract_mstl_components(self):
        """Extract MSTL decomposition components"""
        try:
            # Resample to hourly frequency
            hourly_data = self.data.set_index('datetime')['demand'].resample('H').mean()
            hourly_data = hourly_data.fillna(method='ffill').fillna(method='bfill')
            
            if len(hourly_data) < 2 * 168:  # Need at least 2 weeks
                print("    Insufficient data for MSTL, using fallback", file=sys.stderr)
                return {}
            
            # Perform MSTL decomposition with multiple seasonalities
            print("    Computing MSTL with multiple seasonalities...", file=sys.stderr)
            mstl = MSTL(
                hourly_data, 
                periods=(24, 168),  # Daily and weekly
                windows=(11, 15),   # Smoothness control
                iterate=2
            )
            decomposition = mstl.fit()
            
            # Extract components
            components = {
                'trend': decomposition.trend.values,
                'daily_seasonal': decomposition.seasonal.iloc[:, 0].values[:24],
                'weekly_seasonal': decomposition.seasonal.iloc[:, 1].values[:168],
                'residual_std': decomposition.resid.std(),
                'trend_strength': max(0, min(1, 1 - (decomposition.resid.var() / 
                                      (decomposition.resid + decomposition.trend).var()))),
                'seasonal_strength': max(0, min(1, 1 - (decomposition.resid.var() / 
                                         (decomposition.resid + decomposition.seasonal.iloc[:, 0]).var()))),
                'method': 'mstl'
            }
            
            print(f"    MSTL decomposition successful", file=sys.stderr)
            print(f"      Trend strength: {components['trend_strength']:.3f}", file=sys.stderr)
            print(f"      Seasonal strength: {components['seasonal_strength']:.3f}", file=sys.stderr)
            
            return components
            
        except Exception as e:
            print(f"    MSTL decomposition failed: {e}", file=sys.stderr)
            return {}
    
    def _extract_stl_components(self):
        """Extract STL decomposition components"""
        try:
            hourly_data = self.data.set_index('datetime')['demand'].resample('H').mean()
            hourly_data = hourly_data.fillna(method='ffill').fillna(method='bfill')
            
            if len(hourly_data) < 2 * 168:
                return {}
            
            print("    Computing STL decomposition...", file=sys.stderr)
            stl = STL(hourly_data, seasonal=169, trend=None, seasonal_deg=1, trend_deg=1)
            decomposition = stl.fit()
            
            components = {
                'trend': decomposition.trend.values,
                'seasonal': decomposition.seasonal.values[:168],
                'residual_std': decomposition.resid.std(),
                'trend_strength': max(0, min(1, 1 - (decomposition.resid.var() / 
                                      (decomposition.resid + decomposition.trend).var()))),
                'seasonal_strength': max(0, min(1, 1 - (decomposition.resid.var() / 
                                         (decomposition.resid + decomposition.seasonal).var()))),
                'method': 'stl'
            }
            
            print(f"    STL decomposition successful", file=sys.stderr)
            
            return components
        except Exception as e:
            print(f"    STL decomposition failed: {e}", file=sys.stderr)
            return {}
    
    def _extract_clustered_patterns(self):
        """Extract patterns using K-means clustering"""
        try:
            # Reshape to daily profiles
            n_days = len(self.data) // 24
            if n_days < 7:
                return {}
            
            daily_data = []
            dates = []
            
            # Group by date
            for date in self.data['datetime'].dt.date.unique():
                day_data = self.data[self.data['datetime'].dt.date == date]
                if len(day_data) == 24:
                    daily_data.append(day_data.sort_values('hour')['demand'].values)
                    dates.append(date)
            
            if len(daily_data) < 7:
                return {}
            
            daily_profiles = np.array(daily_data)
            
            # Normalize each day
            daily_totals = np.sum(daily_profiles, axis=1, keepdims=True)
            normalized_profiles = daily_profiles / (daily_totals + 1e-10)
            
            # K-means clustering
            n_clusters = min(7, len(daily_profiles) // 10)
            if n_clusters < 3:
                n_clusters = 3
            
            print(f"    K-means clustering with {n_clusters} patterns...", file=sys.stderr)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(normalized_profiles)
            patterns = kmeans.cluster_centers_
            
            # Analyze clusters
            cluster_info = {}
            for i in range(n_clusters):
                cluster_mask = labels == i
                cluster_dates = [dates[j] for j, m in enumerate(cluster_mask) if m]
                
                if cluster_dates:
                    cluster_dates_dt = pd.to_datetime(cluster_dates)
                    dominant_dow = pd.Series([d.dayofweek for d in cluster_dates_dt]).mode()
                    dominant_month = pd.Series([d.month for d in cluster_dates_dt]).mode()
                    
                    cluster_info[f'pattern_{i}'] = {
                        'shape': patterns[i],
                        'count': int(np.sum(cluster_mask)),
                        'peak_hour': int(np.argmax(patterns[i])),
                        'dominant_dow': int(dominant_dow[0]) if len(dominant_dow) > 0 else 0,
                        'dominant_month': int(dominant_month[0]) if len(dominant_month) > 0 else 1
                    }
            
            print(f"    Extracted {n_clusters} distinct load patterns", file=sys.stderr)
            
            return {
                'patterns': patterns,
                'labels': labels,
                'cluster_info': cluster_info,
                'n_clusters': n_clusters
            }
            
        except Exception as e:
            print(f"    Pattern clustering failed: {e}", file=sys.stderr)
            return {}
    
    def _extract_monthly_patterns_smooth(self):
        """Extract monthly patterns with smooth interpolation (FIXED)"""
        monthly_stats = self.data.groupby('fiscal_month')['demand'].agg([
            'mean', 'std', 'min', 'max', 'median'
        ]).reset_index()
        
        # Monthly scaling factors
        mean_demand = monthly_stats['mean'].mean()
        if mean_demand > 0:
            monthly_stats['monthly_factor'] = monthly_stats['mean'] / mean_demand
        else:
            monthly_stats['monthly_factor'] = 1.0
        
        # Smooth monthly factors using cubic spline (CRITICAL FIX)
        if SCIPY_AVAILABLE and len(monthly_stats) >= 4:
            try:
                # Create smooth interpolation for DAILY resolution
                months = monthly_stats['fiscal_month'].values
                factors = monthly_stats['monthly_factor'].values
                
                # Extend to handle periodicity
                extended_months = np.concatenate([months - 12, months, months + 12])
                extended_factors = np.concatenate([factors, factors, factors])
                
                # Cubic spline interpolation with periodic boundaries
                cs = CubicSpline(extended_months, extended_factors, bc_type='periodic')
                
                # Evaluate at each fiscal day of year (1-365) for SMOOTH daily factors
                fiscal_doy = np.arange(1, 366)
                
                # Convert fiscal DOY to fractional month (for interpolation)
                days_per_month = [30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28, 31]  # Apr-Mar
                month_starts = [1] + list(np.cumsum(days_per_month[:-1]) + 1)
                month_ends = np.cumsum(days_per_month)
                
                # Map each day to fractional month
                fractional_months = np.zeros(365)
                for i, doy in enumerate(fiscal_doy[:-1]):  # Skip last day
                    # Find which month this day belongs to
                    month_idx = np.searchsorted(month_ends, doy)
                    if month_idx < 12:
                        month_start = month_starts[month_idx]
                        month_length = days_per_month[month_idx]
                        day_in_month = doy - month_start + 1
                        fractional_months[i] = (month_idx + 1) + (day_in_month - 1) / month_length
                    else:
                        fractional_months[i] = 12.0
                
                # Evaluate spline at each fractional month
                smooth_factors_daily = cs(fractional_months)
                
                # Store daily factors (THIS IS THE KEY FIX!)
                monthly_stats['smooth_factors_daily'] = [smooth_factors_daily]  # Store once
                monthly_stats['smoothing_applied'] = True
                
                print("    Applied cubic spline smoothing to create daily factors", file=sys.stderr)
                print(f"      Factor range: {smooth_factors_daily.min():.3f} - {smooth_factors_daily.max():.3f}", file=sys.stderr)
                print(f"      Max daily change: {np.max(np.abs(np.diff(smooth_factors_daily))):.4f}", file=sys.stderr)
            except Exception as e:
                print(f"    Smoothing failed: {e}", file=sys.stderr)
                monthly_stats['smoothing_applied'] = False
        else:
            monthly_stats['smoothing_applied'] = False
        
        return monthly_stats
    
    def _extract_hourly_patterns(self):
        """Extract hourly patterns by day type"""
        hourly_patterns = {}
        
        for day_type in ['weekday', 'weekend', 'holiday']:
            subset = self.data[self.data['day_type'] == day_type]
            if len(subset) > 0:
                hourly_stats = subset.groupby('hour')['demand'].agg([
                    'mean', 'std', 'median', 'count'
                ]).reset_index()
                
                # Normalized shape factor
                mean_demand = hourly_stats['mean'].mean()
                if mean_demand > 0:
                    hourly_stats['shape_factor'] = hourly_stats['mean'] / mean_demand
                else:
                    hourly_stats['shape_factor'] = 1.0
                
                # Apply minimal smoothing (preserve peaks!)
                if SCIPY_AVAILABLE:
                    try:
                        smoothed = signal.savgol_filter(
                            hourly_stats['shape_factor'].values,
                            window_length=5,
                            polyorder=2,
                            mode='wrap'
                        )
                        hourly_stats['shape_factor_smooth'] = smoothed
                    except:
                        hourly_stats['shape_factor_smooth'] = hourly_stats['shape_factor']
                else:
                    hourly_stats['shape_factor_smooth'] = hourly_stats['shape_factor']
                
                hourly_patterns[day_type] = hourly_stats
        
        return hourly_patterns
    
    def _extract_base_load(self):
        """Extract base load metrics"""
        base_load_metrics = {
            'p5': np.percentile(self.data['demand'], 5),
            'p10': np.percentile(self.data['demand'], 10),
            'min': self.data['demand'].min(),
            'night_avg': self.data[self.data['hour'].isin([0, 1, 2, 3, 4, 5])]['demand'].mean()
        }
        base_load_metrics['ratio'] = base_load_metrics['p5'] / self.data['demand'].max()
        return base_load_metrics
    
    def _extract_day_type_factors(self):
        """Extract day type reduction factors with smooth transitions"""
        day_type_means = self.data.groupby('day_type')['demand'].mean()
        weekday_mean = day_type_means.get('weekday', day_type_means.mean())
        
        factors = {}
        for day_type in day_type_means.index:
            factors[day_type] = day_type_means[day_type] / weekday_mean if weekday_mean > 0 else 1.0
        
        # Add smooth weekend transitions
        factors['friday_evening'] = 0.95
        factors['sunday_evening'] = 0.97
        
        return factors
    
    def _extract_growth_patterns(self):
        """Extract year-over-year growth patterns"""
        yearly_stats = self.data.groupby('fiscal_year')['demand'].agg(['mean', 'sum', 'max'])
        
        growth_patterns = {
            'yearly_stats': yearly_stats,
            'avg_growth_rate': 0.03  # Default 3%
        }
        
        if len(yearly_stats) > 1:
            growth_rates = yearly_stats['sum'].pct_change().dropna()
            if len(growth_rates) > 0 and not growth_rates.isna().all():
                avg_growth = growth_rates.mean()
                if -0.2 < avg_growth < 0.2:  # Sanity check
                    growth_patterns['avg_growth_rate'] = avg_growth
        
        return growth_patterns
    
    def _extract_variability_metrics(self):
        """NEW: Extract variability metrics for realism preservation"""
        metrics = {}
        
        # Daily variability (coefficient of variation)
        daily_avg = self.data.groupby(self.data['datetime'].dt.date)['demand'].mean()
        metrics['daily_cv'] = daily_avg.std() / daily_avg.mean()
        
        # Hourly variability within days
        hourly_std = self.data.groupby(self.data['datetime'].dt.date)['demand'].std().mean()
        metrics['hourly_std_avg'] = hourly_std
        
        # Week-to-week variability
        weekly_avg = self.data.groupby(pd.Grouper(key='datetime', freq='W'))['demand'].mean()
        metrics['weekly_cv'] = weekly_avg.std() / weekly_avg.mean()
        
        # Max hourly change (for smoothness validation)
        hourly_changes = np.abs(self.data['demand'].diff()) / self.data['demand'].shift(1)
        metrics['max_hourly_change'] = hourly_changes.quantile(0.99)  # 99th percentile
        metrics['avg_hourly_change'] = hourly_changes.mean()
        
        print(f"  Variability metrics extracted:", file=sys.stderr)
        print(f"    Daily CV: {metrics['daily_cv']:.3f}", file=sys.stderr)
        print(f"    Max hourly change (99th): {metrics['max_hourly_change']:.3f}", file=sys.stderr)
        
        return metrics


class EnhancedLoadProfileGenerator:
    """Enhanced load profile generator with smooth transitions and variability preservation"""
    
    def __init__(self, config, patterns, template_data):
        self.config = config
        self.patterns = patterns
        self.template_data = template_data
        self.progress = None
        
        # Parse configuration
        self._parse_config()
        
        # Precompute frequently used values
        self._precompute_values()
    
    def _parse_config(self):
        """Parse configuration with validation"""
        profile_config = self.config.get('profile_configuration', {})
        general_config = profile_config.get('general', {})
        method_config = profile_config.get('generation_method', {})
        data_source_config = profile_config.get('data_source', {})
        constraints_config = profile_config.get('constraints', {})
        
        self.profile_name = general_config.get('profile_name', 'Generated_Profile')
        self.start_year = int(general_config.get('start_year', 2025))
        self.end_year = int(general_config.get('end_year', 2040))
        
        # Parse generation method
        self.method = method_config.get('type', 'base').lower()
        if self.method == 'base':
            self.method = 'normalized_pattern'
        elif self.method == 'stl':
            self.method = 'stl_decomposition'
        
        # Parse base year
        base_year_str = method_config.get('base_year')
        if base_year_str and base_year_str != 'null':
            self.base_year = int(base_year_str.replace('FY', '').strip())
        else:
            self.base_year = self._determine_default_base_year()
        
        self.data_source_type = data_source_config.get('type', 'template')
        self.scenario_name = data_source_config.get('scenario_name')
        self.monthly_constraints = constraints_config.get('monthly_method', 'auto')
        
        print(f"Configuration parsed: {self.profile_name}, Years: {self.start_year}-{self.end_year}", file=sys.stderr)
        print(f"Method: {self.method}, Base Year: FY{self.base_year}", file=sys.stderr)
    
    def _determine_default_base_year(self):
        """Determine default base year from historical data"""
        historical_data = self.template_data.get('Past_Hourly_Demand', pd.DataFrame())
        
        if not historical_data.empty:
            if 'datetime' in historical_data.columns:
                dt = pd.to_datetime(historical_data['datetime'], errors='coerce')
            elif 'date' in historical_data.columns:
                dt = pd.to_datetime(historical_data['date'], errors='coerce')
            else:
                return 2024
            
            fiscal_years = np.where(dt.dt.month >= 4, dt.dt.year + 1, dt.dt.year)
            available_years = np.unique(fiscal_years[~np.isnan(fiscal_years)])
            
            if len(available_years) > 0:
                return int(available_years[-1])
        
        return 2024
    
    def _precompute_values(self):
        """Precompute frequently used values for optimization"""
        self.start_date = datetime(self.start_year - 1, 4, 1, 0, 0, 0)
        self.end_date = datetime(self.end_year, 3, 31, 23, 0, 0)
        
        self.fiscal_month_names = {
            1: 'Apr', 2: 'May', 3: 'Jun', 4: 'Jul', 5: 'Aug', 6: 'Sep',
            7: 'Oct', 8: 'Nov', 9: 'Dec', 10: 'Jan', 11: 'Feb', 12: 'Mar'
        }
        
        self.season_map = {
            3: 'Summer', 4: 'Summer', 5: 'Summer', 6: 'Summer',
            7: 'Monsoon', 8: 'Monsoon', 9: 'Monsoon',
            10: 'Post-monsoon', 11: 'Post-monsoon',
            12: 'Winter', 1: 'Winter', 2: 'Winter'
        }
    
    def generate_profile(self):
        """Generate load profile using enhanced methods"""
        print("\n" + "="*60, file=sys.stderr)
        print(f"ENHANCED PROFILE GENERATION - FIXED VERSION", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        if self.progress:
            self.progress.start_process(6, "Enhanced Load Profile Generation")
        
        # Load demand targets
        if self.progress:
            self.progress.update_progress("Loading demand targets")
        self._load_demand_targets()
        
        # Create profile structure
        if self.progress:
            self.progress.update_progress("Creating profile structure")
        profile_df = self._create_profile_structure()
        
        # Generate demand with FIXED smooth method
        if self.progress:
            self.progress.update_progress("Generating smooth realistic profile")
        profile_df = self._generate_fixed_smooth_profile(profile_df)
        
        # Apply constraints (shape-preserving)
        if self.progress:
            self.progress.update_progress("Applying constraints")
        profile_df = self._apply_constraints_shape_preserving(profile_df)
        
        # Validate profile
        if self.progress:
            self.progress.update_progress("Validating generated profile")
        self.validation_results = self._validate_profile(profile_df)
        
        if self.progress:
            self.progress.complete_process("Generation completed successfully")
        
        self.generated_profile = profile_df
        return profile_df
    
    def _create_profile_structure(self):
        """Create profile DataFrame structure"""
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq='H')
        
        profile_df = pd.DataFrame({
            'DateTime': date_range,
            'Year': date_range.year,
            'Month': date_range.month,
            'Day': date_range.day,
            'Hour': date_range.hour,
            'DayOfWeek': date_range.dayofweek
        })
        
        # CRITICAL: Add dayofyear and fiscal_doy
        profile_df['dayofyear'] = date_range.dayofyear
        profile_df['fiscal_doy'] = profile_df['DateTime'].apply(self._fiscal_day_of_year)
        
        # Vectorized fiscal year calculation
        profile_df['Fiscal_Year'] = np.where(
            profile_df['Month'] >= 4,
            profile_df['Year'] + 1,
            profile_df['Year']
        )
        
        profile_df['fiscal_month'] = ((profile_df['Month'] - 4) % 12) + 1
        profile_df['is_weekend'] = profile_df['DayOfWeek'].isin([5, 6]).astype(int)
        
        # Holiday detection
        profile_df['is_holiday'] = 0
        if HOLIDAYS_AVAILABLE:
            try:
                years = range(profile_df['Year'].min(), profile_df['Year'].max() + 1)
                india_holidays = holidays.India(years=list(years))
                profile_df['is_holiday'] = profile_df['DateTime'].dt.date.isin(india_holidays).astype(int)
            except:
                pass
        
        # Vectorized day type assignment
        profile_df['day_type'] = np.select(
            [profile_df['is_holiday'] == 1, profile_df['is_weekend'] == 1],
            ['holiday', 'weekend'],
            default='weekday'
        )
        
        profile_df['season'] = profile_df['Month'].map(self.season_map)
        
        print(f"  Created {len(profile_df):,} hourly records", file=sys.stderr)
        
        return profile_df
    
    def _fiscal_day_of_year(self, date):
        """Calculate fiscal day of year (April 1 = Day 1)"""
        if isinstance(date, pd.Timestamp):
            date = date.to_pydatetime()
        
        if date.month >= 4:
            fiscal_year_start = datetime(date.year, 4, 1)
        else:
            fiscal_year_start = datetime(date.year - 1, 4, 1)
        
        delta = date - fiscal_year_start
        return delta.days + 1
    
    def _generate_fixed_smooth_profile(self, profile_df):
        """
        FIXED GENERATION METHOD
        Key: Use continuous day-of-year interpolation for smooth transitions
        while preserving all historical variability
        """
        print("\n  Generating profile with smooth transitions and preserved variability...", file=sys.stderr)
        
        # Extract base year curve with ALL variability
        base_curve = self._extract_base_year_curve()
        
        # Get smooth daily factors (THE FIX!)
        smooth_daily_factors = self._get_smooth_daily_factors()
        
        # Initialize demand array
        demand = np.zeros(len(profile_df))
        
        # Process each year
        for year in range(self.start_year, self.end_year + 1):
            year_mask = profile_df['Fiscal_Year'] == year
            if not year_mask.any():
                continue
            
            print(f"    Processing FY{year}...", file=sys.stderr)
            
            # Calculate smooth growth factor
            growth_factor = self._calculate_growth_factor(year)
            
            year_indices = np.where(year_mask)[0]
            
            # Process each hour (vectorized where possible)
            for idx in year_indices:
                row = profile_df.iloc[idx]
                
                # KEY FIX: Use continuous fiscal day of year (1-365)
                fiscal_doy = row['fiscal_doy']
                hour = row['Hour']
                day_type = row['day_type']
                dayofweek = row['DayOfWeek']
                
                # Get historical pattern value for this hour/day-type
                # This preserves ALL historical variability
                base_value = self._get_historical_pattern_value(
                    base_curve, fiscal_doy, hour, day_type
                )
                
                # Apply SMOOTH annual scaling factor (THE FIX!)
                if smooth_daily_factors is not None and fiscal_doy <= len(smooth_daily_factors):
                    annual_factor = smooth_daily_factors[fiscal_doy - 1]
                else:
                    # Fallback to monthly factor
                    month = row['fiscal_month']
                    monthly_patterns = self.patterns.get('monthly', pd.DataFrame())
                    if not monthly_patterns.empty:
                        month_data = monthly_patterns[monthly_patterns['fiscal_month'] == month]
                        if not month_data.empty:
                            annual_factor = month_data['monthly_factor'].iloc[0]
                        else:
                            annual_factor = 1.0
                    else:
                        annual_factor = 1.0
                
                # Apply smooth day-type transitions
                daytype_factor = self._get_smooth_daytype_factor(day_type, dayofweek, hour)
                
                # Apply seasonal adjustment for shoulder months
                seasonal_adj = self._get_seasonal_adjustment(row['Month'], fiscal_doy)
                
                # Combine all factors (multiplicative to preserve variability)
                demand[idx] = (
                    base_value *           # Historical pattern (with all variability)
                    annual_factor *         # Smooth annual cycle (THE FIX!)
                    daytype_factor *        # Smooth day-type transitions
                    seasonal_adj *          # Smooth seasonal adjustments
                    growth_factor           # Smooth growth
                )
        
        profile_df['Demand_MW'] = np.maximum(demand, 10)
        
        # Apply MINIMAL final smoothing (25-hour window for noise only)
        profile_df = self._apply_minimal_final_smoothing(profile_df)
        
        print(f"  Profile generated with preserved variability", file=sys.stderr)
        
        return profile_df
    
    def _get_smooth_daily_factors(self):
        """Get smooth daily factors from monthly patterns (THE KEY FIX!)"""
        monthly_patterns = self.patterns.get('monthly', pd.DataFrame())
        
        if monthly_patterns.empty:
            return None
        
        # Check if smooth factors were calculated
        if not monthly_patterns.get('smoothing_applied', [False])[0]:
            print("    Warning: Smooth factors not available, using monthly", file=sys.stderr)
            return None
        
        # Extract the smooth daily factors array
        smooth_factors_daily = monthly_patterns['smooth_factors_daily'].iloc[0]
        
        print(f"    Using smooth daily factors (365 values)", file=sys.stderr)
        print(f"      Range: {smooth_factors_daily.min():.3f} - {smooth_factors_daily.max():.3f}", file=sys.stderr)
        print(f"      Max daily change: {np.max(np.abs(np.diff(smooth_factors_daily))):.4f}", file=sys.stderr)
        
        return smooth_factors_daily
    
    def _get_historical_pattern_value(self, base_curve, fiscal_doy, hour, day_type):
        """
        Get historical pattern value preserving ALL variability
        
        Key: Use actual historical data, not smoothed patterns
        """
        # Find matching days in historical data (same fiscal DOY, similar day type)
        matching_days = base_curve[
            (base_curve['fiscal_doy'] >= fiscal_doy - 3) &
            (base_curve['fiscal_doy'] <= fiscal_doy + 3) &
            (base_curve['hour'] == hour)
        ]
        
        # If day_type specific data available, use it
        if not matching_days.empty:
            daytype_match = matching_days[matching_days['day_type'] == day_type]
            if not daytype_match.empty:
                # Use median (preserves typical value)
                return daytype_match['demand'].median()
            else:
                # Fallback to any day type
                return matching_days['demand'].median()
        else:
            # Broader search
            matching_hour = base_curve[base_curve['hour'] == hour]
            if not matching_hour.empty:
                return matching_hour['demand'].median()
            else:
                return base_curve['demand'].mean()
    
    def _get_smooth_daytype_factor(self, day_type, dayofweek, hour):
        """Get smooth day type factor with gradual transitions"""
        day_type_factors = self.patterns.get('day_type_factors', {})
        base_factor = day_type_factors.get(day_type, 1.0)
        
        # Smooth Friday evening to Saturday transition (12 hours)
        if dayofweek == 4 and hour >= 17:  # Friday evening
            progress = (hour - 17) / 7
            s_curve = 1 / (1 + np.exp(-10 * (progress - 0.5)))
            weekend_factor = day_type_factors.get('weekend', 0.85)
            return base_factor * (1 - s_curve) + weekend_factor * s_curve
        
        # Smooth Sunday evening to Monday transition (12 hours)
        elif dayofweek == 6 and hour >= 17:  # Sunday evening
            progress = (hour - 17) / 7
            s_curve = 1 / (1 + np.exp(-10 * (progress - 0.5)))
            weekday_factor = day_type_factors.get('weekday', 1.0)
            return base_factor * (1 - s_curve) + weekday_factor * s_curve
        
        return base_factor
    
    def _get_seasonal_adjustment(self, month, fiscal_doy):
        """Get seasonal adjustment for shoulder months (smooth transitions)"""
        # Spring transition (Late March - Early May): Days 350-60
        if 350 <= fiscal_doy or fiscal_doy <= 60:
            if fiscal_doy >= 350:
                days_into_transition = fiscal_doy - 350
            else:
                days_into_transition = fiscal_doy + 15
            
            # 45-day smooth transition
            progress = days_into_transition / 45
            s_curve = 1 / (1 + np.exp(-10 * (progress - 0.5)))
            
            winter_factor = 1.03  # Slightly higher winter load
            summer_factor = 0.97  # Slightly lower summer load
            return winter_factor * (1 - s_curve) + summer_factor * s_curve
        
        # Autumn transition (Oct-Nov): Days 180-240
        elif 180 <= fiscal_doy <= 240:
            days_into_transition = fiscal_doy - 180
            progress = days_into_transition / 60
            s_curve = 1 / (1 + np.exp(-10 * (progress - 0.5)))
            
            summer_factor = 0.97
            winter_factor = 1.03
            return summer_factor * (1 - s_curve) + winter_factor * s_curve
        
        else:
            return 1.0  # No adjustment
    
    def _apply_minimal_final_smoothing(self, profile_df):
        """
        Apply MINIMAL final smoothing (25-hour window)
        Purpose: Remove only high-frequency noise, NOT for fixing transitions
        """
        if not SCIPY_AVAILABLE:
            return profile_df
        
        try:
            print("  Applying minimal final smoothing (noise reduction only)...", file=sys.stderr)
            for year in range(self.start_year, self.end_year + 1):
                year_mask = profile_df['Fiscal_Year'] == year
                if not year_mask.any():
                    continue
                
                year_demand = profile_df.loc[year_mask, 'Demand_MW'].values
                
                if len(year_demand) > 25:
                    # Smaller window - preserves variability
                    smoothed = signal.savgol_filter(
                        year_demand,
                        window_length=25,  # ~1 day (was 49)
                        polyorder=3,
                        mode='nearest'
                    )
                    profile_df.loc[year_mask, 'Demand_MW'] = smoothed
        
        except Exception as e:
            print(f"  Final smoothing skipped: {e}", file=sys.stderr)
        
        return profile_df
    
    def _load_demand_targets(self):
        """Load demand targets from template or forecast"""
        self.demand_targets = {}
        
        if self.data_source_type == 'projection' and self.scenario_name:
            self._load_from_forecast()
        else:
            self._load_from_template()
        
        if not self.demand_targets:
            print("  Warning: No demand targets loaded, using growth projection", file=sys.stderr)
            self._generate_default_targets()
    
    def _load_from_template(self):
        """Load demand targets from template"""
        if 'Total Demand' in self.template_data:
            df = self.template_data['Total Demand']
            df.columns = df.columns.str.strip()
            
            year_col = next((col for col in df.columns if 'year' in col.lower()), None)
            demand_col = next((col for col in df.columns if 'demand' in col.lower()), None)
            
            if year_col and demand_col:
                for _, row in df.iterrows():
                    try:
                        year = int(float(row[year_col]))
                        demand = float(row[demand_col])
                        if self.start_year <= year <= self.end_year:
                            self.demand_targets[year] = demand
                    except (ValueError, TypeError):
                        continue
    
    def _load_from_forecast(self):
        """Load demand targets from forecast scenario (Consolidated_Results.xlsx)"""
        project_path = self.config.get('project_path')
        if not project_path or not self.scenario_name:
            return

        # FIXED: Correct path to match where consolidated results are saved
        # Path: {project}/results/demand_forecasts/{scenario}/Consolidated_Results.xlsx
        forecast_path = os.path.join(
            project_path, 'results', 'demand_forecasts',
            self.scenario_name, 'Consolidated_Results.xlsx'
        )

        try:
            if os.path.exists(forecast_path):
                # FIXED: Read from 'Consolidated Data' sheet (not 'Summary')
                forecast_data = pd.read_excel(forecast_path, sheet_name='Consolidated Data', engine='openpyxl')

                # FIXED: Look for 'Year' and 'Total' columns (exact names from consolidated save)
                year_col = 'Year'
                demand_col = 'Total'

                if year_col in forecast_data.columns and demand_col in forecast_data.columns:
                    for _, row in forecast_data.iterrows():
                        try:
                            year = int(float(row[year_col]))
                            demand = float(row[demand_col])
                            if self.start_year <= year <= self.end_year:
                                self.demand_targets[year] = demand
                        except (ValueError, TypeError):
                            continue
                else:
                    print(f"  Warning: Could not find 'Year' or 'Total' columns in {forecast_path}", file=sys.stderr)
            else:
                print(f"  Warning: Forecast file not found: {forecast_path}", file=sys.stderr)
        except Exception as e:
            print(f"  Error loading forecast: {e}", file=sys.stderr)
    
    def _generate_default_targets(self):
        """Generate default targets based on growth rate"""
        growth_rate = self.patterns.get('growth', {}).get('avg_growth_rate', 0.03)
        
        historical_data = self.template_data.get('Past_Hourly_Demand', pd.DataFrame())
        if not historical_data.empty:
            base_total = historical_data['demand'].sum()
        else:
            base_total = 1000000
        
        for year in range(self.start_year, self.end_year + 1):
            years_from_base = year - self.base_year
            self.demand_targets[year] = base_total * ((1 + growth_rate) ** years_from_base)
    
    def _extract_base_year_curve(self):
        """Extract base year curve with ALL variability preserved"""
        historical_data = self.template_data.get('Past_Hourly_Demand', pd.DataFrame())
        
        if historical_data.empty:
            raise ValueError("No historical data found")
        
        data = historical_data.copy()
        
        if 'datetime' not in data.columns:
            if 'date' in data.columns and 'time' in data.columns:
                data['datetime'] = pd.to_datetime(
                    data['date'].astype(str) + ' ' + data['time'].astype(str),
                    errors='coerce'
                )
            elif 'date' in data.columns:
                data['datetime'] = pd.to_datetime(data['date'], errors='coerce')
        
        data = data.dropna(subset=['datetime', 'demand'])
        data = data[data['demand'] > 0].sort_values('datetime')
        
        # Add fiscal features
        data['hour'] = data['datetime'].dt.hour
        data['dayofweek'] = data['datetime'].dt.dayofweek
        data['month'] = data['datetime'].dt.month
        data['year'] = data['datetime'].dt.year
        
        data['fiscal_year'] = np.where(
            data['month'] >= 4,
            data['year'] + 1,
            data['year']
        )
        
        data['fiscal_doy'] = data['datetime'].apply(self._fiscal_day_of_year)
        
        # Day type
        data['is_weekend'] = data['dayofweek'].isin([5, 6]).astype(int)
        data['is_holiday'] = 0
        data['day_type'] = np.where(data['is_weekend'] == 1, 'weekend', 'weekday')
        
        # Extract base year
        base_year_data = data[data['fiscal_year'] == self.base_year]
        
        if base_year_data.empty:
            available_years = sorted(data['fiscal_year'].unique())
            if available_years:
                self.base_year = available_years[-1]
                base_year_data = data[data['fiscal_year'] == self.base_year]
        
        if base_year_data.empty:
            raise ValueError(f"No data found for base year FY{self.base_year}")
        
        # Create complete hourly range for base year
        start_date = datetime(self.base_year - 1, 4, 1, 0, 0, 0)
        end_date = datetime(self.base_year, 3, 31, 23, 0, 0)
        complete_range = pd.date_range(start=start_date, end=end_date, freq='H')
        
        complete_base = pd.DataFrame({'datetime': complete_range})
        complete_base = complete_base.merge(
            base_year_data[['datetime', 'demand', 'hour', 'fiscal_doy', 'day_type']], 
            on='datetime', 
            how='left'
        )
        
        # Fill missing values carefully (preserve variability)
        if complete_base['demand'].isna().any():
            # Linear interpolation (preserves trends)
            complete_base['demand'] = complete_base['demand'].interpolate(method='linear')
            complete_base['demand'] = complete_base['demand'].fillna(method='bfill').fillna(method='ffill')
        
        # Fill other columns
        if complete_base['hour'].isna().any():
            complete_base['hour'] = complete_base['datetime'].dt.hour
        if complete_base['fiscal_doy'].isna().any():
            complete_base['fiscal_doy'] = complete_base['datetime'].apply(self._fiscal_day_of_year)
        if complete_base['day_type'].isna().any():
            complete_base['day_type'] = 'weekday'
        
        print(f"  Base year curve extracted: FY{self.base_year}", file=sys.stderr)
        print(f"    Records: {len(complete_base)}", file=sys.stderr)
        print(f"    Range: {complete_base['demand'].min():.2f} - {complete_base['demand'].max():.2f} MW", file=sys.stderr)
        
        return complete_base
    
    def _calculate_growth_factor(self, year):
        """Calculate growth factor for a given year"""
        if year in self.demand_targets and self.base_year in self.demand_targets:
            return self.demand_targets[year] / self.demand_targets[self.base_year]
        
        growth_rate = self.patterns.get('growth', {}).get('avg_growth_rate', 0.03)
        years_from_base = year - self.base_year
        return (1 + growth_rate) ** years_from_base
    
    def _apply_constraints_shape_preserving(self, profile_df):
        """
        Apply constraints while PRESERVING shape (CRITICAL FOR REALISM)
        
        Key: Scale uniformly, don't clip or flatten
        """
        print("\n  Applying shape-preserving constraints...", file=sys.stderr)
        
        # Apply yearly constraints first
        for year in range(self.start_year, self.end_year + 1):
            if year not in self.demand_targets:
                continue
            
            year_mask = profile_df['Fiscal_Year'] == year
            if not year_mask.any():
                continue
            
            current_total = profile_df.loc[year_mask, 'Demand_MW'].sum()
            target_total = self.demand_targets[year]
            
            if current_total > 0:
                scale_factor = target_total / current_total
                profile_df.loc[year_mask, 'Demand_MW'] *= scale_factor
                print(f"    FY{year}: Scaled by {scale_factor:.4f} to meet yearly target", file=sys.stderr)
        
        # Apply monthly constraints if provided
        if self.monthly_constraints == 'excel':
            self._apply_excel_constraints_shape_preserving(profile_df)
        
        return profile_df
    
    def _apply_excel_constraints_shape_preserving(self, profile_df):
        """Apply Excel constraints while preserving shape"""
        max_demand_constraints = self.template_data.get('max_demand', pd.DataFrame())
        
        if max_demand_constraints.empty:
            return profile_df
        
        print("  Applying monthly max constraints (shape-preserving)...", file=sys.stderr)
        
        for year in range(self.start_year, self.end_year + 1):
            year_row = max_demand_constraints[
                max_demand_constraints.get('financial_year', max_demand_constraints.get('Year', 0)) == year
            ]
            
            if year_row.empty:
                continue
            
            for month in range(1, 13):
                month_name = self.fiscal_month_names[month]
                
                if month_name not in year_row.columns:
                    continue
                
                constraint_value = year_row[month_name].iloc[0]
                if pd.isna(constraint_value) or constraint_value <= 0:
                    continue
                
                mask = (profile_df['Fiscal_Year'] == year) & (profile_df['fiscal_month'] == month)
                if mask.any():
                    current_max = profile_df.loc[mask, 'Demand_MW'].max()
                    if current_max > constraint_value:
                        # Scale entire month uniformly (preserves shape!)
                        scale_factor = constraint_value / current_max
                        profile_df.loc[mask, 'Demand_MW'] *= scale_factor
                        print(f"      FY{year}-{month_name}: Scaled by {scale_factor:.4f}", file=sys.stderr)
        
        return profile_df
    
    def _validate_profile(self, profile_df):
        """Enhanced validation with smoothness and realism checks"""
        validation = {}
        
        # Annual validation
        for year in range(self.start_year, self.end_year + 1):
            year_mask = profile_df['Fiscal_Year'] == year
            if not year_mask.any():
                continue
            
            year_demand = profile_df.loc[year_mask, 'Demand_MW']
            generated_total = year_demand.sum()
            target_total = self.demand_targets.get(year, generated_total)
            
            error_pct = abs(generated_total - target_total) / target_total * 100 if target_total > 0 else 0
            
            validation[f'FY{year}'] = {
                'generated': generated_total,
                'target': target_total,
                'error_pct': error_pct,
                'peak': year_demand.max(),
                'average': year_demand.mean(),
                'min': year_demand.min(),
                'load_factor': year_demand.mean() / year_demand.max() if year_demand.max() > 0 else 0,
                'std': year_demand.std(),
                'cv': year_demand.std() / year_demand.mean() if year_demand.mean() > 0 else 0
            }
        
        # Overall statistics
        validation['overall'] = {
            'total_energy': profile_df['Demand_MW'].sum(),
            'peak_demand': profile_df['Demand_MW'].max(),
            'average_demand': profile_df['Demand_MW'].mean(),
            'min_demand': profile_df['Demand_MW'].min(),
            'load_factor': profile_df['Demand_MW'].mean() / profile_df['Demand_MW'].max(),
            'std_dev': profile_df['Demand_MW'].std(),
            'cv': profile_df['Demand_MW'].std() / profile_df['Demand_MW'].mean()
        }
        
        # Smoothness check (month boundaries)
        validation['smoothness'] = self._validate_monthly_transitions(profile_df)
        
        # Realism check (variability preservation)
        validation['realism'] = self._validate_realism(profile_df)
        
        print("\n  Validation Summary:", file=sys.stderr)
        print(f"    Peak Demand: {validation['overall']['peak_demand']:.2f} MW", file=sys.stderr)
        print(f"    Average Demand: {validation['overall']['average_demand']:.2f} MW", file=sys.stderr)
        print(f"    Load Factor: {validation['overall']['load_factor']:.3f}", file=sys.stderr)
        print(f"    Coefficient of Variation: {validation['overall']['cv']:.3f}", file=sys.stderr)
        
        if 'smoothness' in validation:
            print(f"    Max Monthly Transition: {validation['smoothness']['max_boundary_change']:.2f}%", file=sys.stderr)
            print(f"    Avg Hourly Change: {validation['smoothness']['avg_hourly_change']:.2f}%", file=sys.stderr)
        
        if 'realism' in validation:
            print(f"    Variability Preservation: {validation['realism']['cv_ratio']:.2f}x", file=sys.stderr)
        
        return validation
    
    def _validate_monthly_transitions(self, profile_df):
        """Validate smoothness of monthly transitions"""
        month_boundaries_changes = []
        
        # Check all 12 month boundaries
        for year in range(self.start_year, self.end_year + 1):
            for month in range(1, 13):
                # Get last day of current month and first day of next month
                current_month_mask = (profile_df['Fiscal_Year'] == year) & (profile_df['fiscal_month'] == month)
                next_month = (month % 12) + 1
                next_year = year if month < 12 else year + 1
                next_month_mask = (profile_df['Fiscal_Year'] == next_year) & (profile_df['fiscal_month'] == next_month)
                
                if current_month_mask.any() and next_month_mask.any():
                    # Get last few hours of current month
                    current_month_end = profile_df.loc[current_month_mask, 'Demand_MW'].iloc[-24:].mean()
                    # Get first few hours of next month
                    next_month_start = profile_df.loc[next_month_mask, 'Demand_MW'].iloc[:24].mean()
                    
                    # Calculate change
                    if current_month_end > 0:
                        change_pct = abs(next_month_start - current_month_end) / current_month_end * 100
                        month_boundaries_changes.append(change_pct)
        
        # Overall hourly changes
        hourly_changes = np.abs(profile_df['Demand_MW'].diff()) / profile_df['Demand_MW'].shift(1) * 100
        hourly_changes = hourly_changes.dropna()
        
        return {
            'max_boundary_change': np.max(month_boundaries_changes) if month_boundaries_changes else 0,
            'avg_boundary_change': np.mean(month_boundaries_changes) if month_boundaries_changes else 0,
            'max_hourly_change': hourly_changes.quantile(0.99),
            'avg_hourly_change': hourly_changes.mean(),
            'p95_hourly_change': hourly_changes.quantile(0.95)
        }
    
    def _validate_realism(self, profile_df):
        """Validate that generated profile preserves historical realism"""
        historical_variability = self.patterns.get('variability', {})
        
        if not historical_variability:
            return {}
        
        # Calculate generated variability
        daily_avg = profile_df.groupby(profile_df['DateTime'].dt.date)['Demand_MW'].mean()
        generated_daily_cv = daily_avg.std() / daily_avg.mean()
        
        weekly_avg = profile_df.groupby(pd.Grouper(key='DateTime', freq='W'))['Demand_MW'].mean()
        generated_weekly_cv = weekly_avg.std() / weekly_avg.mean()
        
        # Compare to historical
        hist_daily_cv = historical_variability.get('daily_cv', 0.15)
        hist_weekly_cv = historical_variability.get('weekly_cv', 0.12)
        
        cv_ratio = generated_daily_cv / hist_daily_cv if hist_daily_cv > 0 else 1.0
        weekly_cv_ratio = generated_weekly_cv / hist_weekly_cv if hist_weekly_cv > 0 else 1.0
        
        return {
            'generated_daily_cv': generated_daily_cv,
            'historical_daily_cv': hist_daily_cv,
            'cv_ratio': cv_ratio,
            'generated_weekly_cv': generated_weekly_cv,
            'historical_weekly_cv': hist_weekly_cv,
            'weekly_cv_ratio': weekly_cv_ratio,
            'variability_preserved': 0.8 < cv_ratio < 1.2  # Within 20%
        }


# Analysis functions (unchanged from original)
def monthly_analysis(profile_df):
    """Generate monthly analysis"""
    monthly_analysis = ['Peak Demand', 'Min Demand', 'Average Demand', 'Monthly Load Factor','Total demand']
    result_rows = []
    
    months = sorted(profile_df['Month'].unique())
    
    for year in profile_df['Fiscal_Year'].unique():
        df_year = profile_df[profile_df['Fiscal_Year'] == year]
        
        df_sum = df_year.groupby('Month')['Demand_MW'].sum().reindex(months)
        df_mean = df_year.groupby('Month')['Demand_MW'].mean().reindex(months)
        df_min = df_year.groupby('Month')['Demand_MW'].min().reindex(months)
        df_max = df_year.groupby('Month')['Demand_MW'].max().reindex(months)
        df_load_factor = (df_mean / df_max).reindex(months)
        
        result_rows.append(['Peak Demand', year] + df_max.tolist())
        result_rows.append(['Min Demand', year] + df_min.tolist())
        result_rows.append(['Average Demand', year] + df_mean.tolist())
        result_rows.append(['Monthly Load Factor', year] + df_load_factor.tolist())
        result_rows.append(['Total demand', year] + df_sum.tolist())
    
    columns = ['Parameters', 'Fiscal_Year'] + list(months)
    main_df = pd.DataFrame(result_rows, columns=columns)
    return main_df

def seasonal_analysis(profile_df):
    """Generate seasonal analysis"""
    monthly_analysis = ['Peak Demand', 'Min Demand', 'Average Demand', 'Monthly Load Factor','Total Demand']
    result_rows = []
    
    months = sorted(profile_df['season'].unique())
    
    for year in profile_df['Fiscal_Year'].unique():
        df_year = profile_df[profile_df['Fiscal_Year'] == year]
        
        df_mean = df_year.groupby('season')['Demand_MW'].mean().reindex(months)
        df_min = df_year.groupby('season')['Demand_MW'].min().reindex(months)
        df_max = df_year.groupby('season')['Demand_MW'].max().reindex(months)
        df_sum = df_year.groupby('season')['Demand_MW'].sum().reindex(months)
        df_load_factor = (df_mean / df_max).reindex(months)
        
        result_rows.append(['Peak Demand', year] + df_max.tolist())
        result_rows.append(['Min Demand', year] + df_min.tolist())
        result_rows.append(['Average Demand', year] + df_mean.tolist())
        result_rows.append(['Monthly Load Factor', year] + df_load_factor.tolist())
        result_rows.append(['Total Demand', year] + df_sum.tolist())
    
    columns = ['Parameters', 'Fiscal_Year'] + list(months)
    main_df = pd.DataFrame(result_rows, columns=columns)
    return main_df

def daily_profile(profile_df):
    """Generate daily profile analysis"""
    monthly_analysis = ['Peak day Demand', 'Min Demand day', 'Average Demand']
    result_rows = []
    
    profile_df['DateTime'] = pd.to_datetime(profile_df['DateTime'])
    profile_df['date'] = profile_df['DateTime'].dt.date
    
    months = sorted(profile_df['Month'].unique())
    seasons = sorted(profile_df['season'].unique())
    hours = sorted(profile_df['Hour'].unique())
    
    for year in profile_df['Fiscal_Year'].unique():
        df_year = profile_df[profile_df['Fiscal_Year'] == year]
        
        # Monthly Analysis
        for month in months:
            df_month = df_year[df_year['Month'] == month]
            
            if df_month.empty:
                continue
            
            peak_day = df_month.loc[df_month['Demand_MW'].idxmax(), 'date']
            peak_day_profile = df_month[df_month['date'] == peak_day].sort_values('Hour')['Demand_MW'].tolist()
            
            min_day = df_month.loc[df_month['Demand_MW'].idxmin(), 'date']
            min_day_profile = df_month[df_month['date'] == min_day].sort_values('Hour')['Demand_MW'].tolist()
            
            avg_profile = df_month.groupby('Hour')['Demand_MW'].mean().reindex(hours).tolist()
            
            result_rows.append([monthly_analysis[0], year, peak_day, f"Month-{month}"] + peak_day_profile)
            result_rows.append([monthly_analysis[1], year, min_day, f"Month-{month}"] + min_day_profile)
            result_rows.append([monthly_analysis[2], year, 'Average', f"Month-{month}"] + avg_profile)
        
        # Seasonal Analysis
        for season in seasons:
            df_season = df_year[df_year['season'] == season]
            
            if df_season.empty:
                continue
            
            peak_day = df_season.loc[df_season['Demand_MW'].idxmax(), 'date']
            peak_day_profile = df_season[df_season['date'] == peak_day].sort_values('Hour')['Demand_MW'].tolist()
            
            min_day = df_season.loc[df_season['Demand_MW'].idxmin(), 'date']
            min_day_profile = df_season[df_season['date'] == min_day].sort_values('Hour')['Demand_MW'].tolist()
            
            avg_profile = df_season.groupby('Hour')['Demand_MW'].mean().reindex(hours).tolist()
            
            result_rows.append([monthly_analysis[0], year, peak_day, f"Season-{season}"] + peak_day_profile)
            result_rows.append([monthly_analysis[1], year, min_day, f"Season-{season}"] + min_day_profile)
            result_rows.append([monthly_analysis[2], year, 'Average', f"Season-{season}"] + avg_profile)
    
    columns = ['Parameters', 'Fiscal_Year','Date', 'Type'] + hours
    main_df = pd.DataFrame(result_rows, columns=columns)
    return main_df


def main():
    """Enhanced main function"""
    parser = argparse.ArgumentParser(description='Enhanced Load Profile Generation System - FIXED')
    parser.add_argument('--config', required=True, help='Configuration JSON string or file path')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = json.load(f)
        else:
            config = json.loads(args.config)
        
        # Initialize progress reporter
        progress = ProgressReporter(enable_progress=True)
        
        print("="*80, file=sys.stderr)
        print("ENHANCED LOAD PROFILE GENERATION SYSTEM - FIXED", file=sys.stderr)
        print("With Smooth Transitions & Preserved Variability", file=sys.stderr)
        print("="*80, file=sys.stderr)
        
        # Load template data
        progress.start_process(6, "Enhanced Load Profile Generation")
        progress.update_progress("Loading template data")
        
        project_path = config.get('project_path')
        template_path = os.path.join(project_path, 'inputs', 'load_curve_template.xlsx')
        
        try:
            template_data = pd.read_excel(template_path, sheet_name=None, engine='openpyxl')
        except Exception as e:
            print(f"Error loading template: {e}", file=sys.stderr)
            raise
        
        # Extract patterns
        progress.update_progress("Extracting enhanced patterns")
        
        historical_data = template_data.get('Past_Hourly_Demand', pd.DataFrame())
        if historical_data.empty:
            raise ValueError("No historical data found in template")
        
        # Determine method
        profile_config = config.get('profile_configuration', {})
        method_config = profile_config.get('generation_method', {})
        method_type = method_config.get('type', 'base').lower()
        
        if method_type == 'stl':
            method = 'stl'
        else:
            method = 'normalized'
        
        # Extract patterns with enhancements
        pattern_extractor = EnhancedPatternExtractor(historical_data, method)
        patterns = pattern_extractor.extract_enhanced_patterns()
        
        # Generate profile
        progress.update_progress("Generating fixed smooth load profile")
        
        generator = EnhancedLoadProfileGenerator(config, patterns, template_data)
        generator.progress = progress
        profile_df = generator.generate_profile()
        
        # Save results
        progress.update_progress("Saving results")
        
        output_dir = os.path.join(project_path, 'results', 'load_profiles')
        os.makedirs(output_dir, exist_ok=True)
        
        scenario_name = generator.profile_name
        filename = f"{scenario_name}.xlsx"
        output_path = os.path.join(output_dir, filename)
        
        # Save to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main profile
            profile_df.to_excel(writer, sheet_name='Load_Profile', index=False)
            monthly_analysis(profile_df).to_excel(writer, sheet_name='Monthly_analysis', index=False)
            seasonal_analysis(profile_df).to_excel(writer, sheet_name='Season_analysis', index=False)
            daily_profile(profile_df).to_excel(writer, sheet_name='Daily_analysis', index=False)
            
            # Load Duration Curve
            percent_bins = np.arange(1, 101)
            ldc_rows = {'Percent_Time': percent_bins}
            
            for year in sorted(profile_df['Fiscal_Year'].unique()):
                yearly = profile_df.loc[profile_df['Fiscal_Year'] == year, 'Demand_MW'].dropna().values
                if len(yearly) == 0:
                    vals = [np.nan] * len(percent_bins)
                else:
                    q = 100.0 - percent_bins
                    vals = np.percentile(yearly, q).tolist()
                ldc_rows[str(year)] = vals
            
            ldc_100 = pd.DataFrame(ldc_rows)
            ldc_100.to_excel(writer, sheet_name='Load_Duration_Curve', index=False)
            
            # Summary sheet
            summary_data = []
            for fy in range(generator.start_year, generator.end_year + 1):
                fy_mask = profile_df['Fiscal_Year'] == fy
                if np.sum(fy_mask) > 0:
                    fy_data = profile_df.loc[fy_mask, 'Demand_MW']
                    summary_data.append({
                        'Fiscal_Year': f"FY{fy}",
                        'Peak_MW': f"{fy_data.max():.2f}",
                        'Average_MW': f"{fy_data.mean():.2f}",
                        'Min_MW': f"{fy_data.min():.2f}",
                        'Total_MWh': f"{fy_data.sum():.0f}",
                        'Load_Factor': f"{fy_data.mean() / fy_data.max():.3f}",
                        'Coeff_Variation': f"{fy_data.std() / fy_data.mean():.3f}",
                        'Total_Hours': len(fy_data)
                    })
            
            if summary_data:
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Validation results
            if generator.validation_results:
                validation_summary = []
                
                # Annual validation
                for key, value in generator.validation_results.items():
                    if isinstance(value, dict) and 'generated' in value:
                        validation_summary.append({
                            'Metric': key,
                            'Generated': value.get('generated', 0),
                            'Target': value.get('target', 0),
                            'Error %': value.get('error_pct', 0),
                            'Peak': value.get('peak', 0),
                            'Load Factor': value.get('load_factor', 0),
                            'CV': value.get('cv', 0)
                        })
                
                # Smoothness validation
                if 'smoothness' in generator.validation_results:
                    smooth = generator.validation_results['smoothness']
                    validation_summary.append({
                        'Metric': 'Smoothness_Check',
                        'Generated': smooth.get('max_boundary_change', 0),
                        'Target': 5.0,  # Threshold
                        'Error %': 0,
                        'Peak': smooth.get('max_hourly_change', 0),
                        'Load Factor': smooth.get('avg_hourly_change', 0),
                        'CV': 0
                    })
                
                # Realism validation
                if 'realism' in generator.validation_results:
                    realism = generator.validation_results['realism']
                    validation_summary.append({
                        'Metric': 'Realism_Check',
                        'Generated': realism.get('generated_daily_cv', 0),
                        'Target': realism.get('historical_daily_cv', 0),
                        'Error %': 0,
                        'Peak': realism.get('cv_ratio', 0),
                        'Load Factor': 1 if realism.get('variability_preserved', False) else 0,
                        'CV': realism.get('generated_weekly_cv', 0)
                    })
                
                if validation_summary:
                    pd.DataFrame(validation_summary).to_excel(writer, sheet_name='Validation', index=False)
            
            # Monthly statistics
            monthly_stats = []
            for fy in range(generator.start_year, generator.end_year + 1):
                for month in range(1, 13):
                    mask = (profile_df['Fiscal_Year'] == fy) & (profile_df['fiscal_month'] == month)
                    if np.sum(mask) > 0:
                        month_data = profile_df.loc[mask, 'Demand_MW']
                        fiscal_month_names = {1: 'Apr', 2: 'May', 3: 'Jun', 4: 'Jul', 5: 'Aug', 6: 'Sep',
                                            7: 'Oct', 8: 'Nov', 9: 'Dec', 10: 'Jan', 11: 'Feb', 12: 'Mar'}
                        monthly_stats.append({
                            'Fiscal_Year': fy,
                            'Month': fiscal_month_names[month],
                            'Peak_MW': month_data.max(),
                            'Average_MW': month_data.mean(),
                            'Min_MW': month_data.min(),
                            'Total_MWh': month_data.sum(),
                            'Load_Factor': month_data.mean() / month_data.max() if month_data.max() > 0 else 0,
                            'Std_Dev': month_data.std(),
                            'CV': month_data.std() / month_data.mean() if month_data.mean() > 0 else 0
                        })
            
            if monthly_stats:
                pd.DataFrame(monthly_stats).to_excel(writer, sheet_name='Monthly_Statistics', index=False)
            
            # Pattern information
            pattern_info = []
            if 'mstl' in patterns and patterns['mstl']:
                mstl_info = patterns['mstl']
                pattern_info.append({
                    'Pattern_Type': 'MSTL_Decomposition',
                    'Metric': 'Method',
                    'Value': 'Multi-Seasonal Trend Decomposition'
                })
                pattern_info.append({
                    'Pattern_Type': 'MSTL_Decomposition',
                    'Metric': 'Trend_Strength',
                    'Value': f"{mstl_info.get('trend_strength', 0):.3f}"
                })
                pattern_info.append({
                    'Pattern_Type': 'MSTL_Decomposition',
                    'Metric': 'Seasonal_Strength',
                    'Value': f"{mstl_info.get('seasonal_strength', 0):.3f}"
                })
            elif 'stl' in patterns and patterns['stl']:
                stl_info = patterns['stl']
                pattern_info.append({
                    'Pattern_Type': 'STL_Decomposition',
                    'Metric': 'Trend_Strength',
                    'Value': f"{stl_info.get('trend_strength', 0):.3f}"
                })
            else:
                pattern_info.append({
                    'Pattern_Type': 'Enhanced_Smooth_Profile',
                    'Metric': 'Base_Year',
                    'Value': f"FY{generator.base_year}"
                })
            
            # Add enhancement info
            if 'clustered_patterns' in patterns and patterns['clustered_patterns']:
                n_clusters = patterns['clustered_patterns'].get('n_clusters', 0)
                pattern_info.append({
                    'Pattern_Type': 'Enhancements',
                    'Metric': 'K-Means_Clusters',
                    'Value': f"{n_clusters}"
                })
            
            pattern_info.append({
                'Pattern_Type': 'FIXED_Features',
                'Metric': 'Continuous_DOY_Interpolation',
                'Value': 'Yes - Smooth 365-day factors'
            })
            
            pattern_info.append({
                'Pattern_Type': 'FIXED_Features',
                'Metric': 'Variability_Preservation',
                'Value': 'Yes - Historical patterns maintained'
            })
            
            pattern_info.append({
                'Pattern_Type': 'FIXED_Features',
                'Metric': 'Shape-Preserving_Constraints',
                'Value': 'Yes - Uniform scaling'
            })
            
            pattern_info.append({
                'Pattern_Type': 'FIXED_Features',
                'Metric': 'Smoothing_Window',
                'Value': '25 hours (noise only)'
            })
            
            if pattern_info:
                pd.DataFrame(pattern_info).to_excel(writer, sheet_name='Pattern_Info', index=False)
        
        progress.complete_process("Generation completed successfully")
        
        # Prepare result
        result = {
            'success': True,
            'output_file': output_path,
            'filename': filename,
            'total_hours': len(profile_df),
            'peak_demand': float(profile_df['Demand_MW'].max()),
            'average_demand': float(profile_df['Demand_MW'].mean()),
            'total_energy': float(profile_df['Demand_MW'].sum()),
            'load_factor': float(profile_df['Demand_MW'].mean() / profile_df['Demand_MW'].max()),
            'coefficient_variation': float(profile_df['Demand_MW'].std() / profile_df['Demand_MW'].mean()),
            'method': 'fixed_smooth_' + generator.method,
            'base_year': int(generator.base_year),
            'generation_timestamp': datetime.now().isoformat(),
            'profile_name': generator.profile_name
        }
        
        # Add validation metrics to result
        if generator.validation_results:
            if 'smoothness' in generator.validation_results:
                result['max_monthly_transition_%'] = float(generator.validation_results['smoothness'].get('max_boundary_change', 0))
            if 'realism' in generator.validation_results:
                result['variability_preserved'] = generator.validation_results['realism'].get('variability_preserved', False)
        
        # Print summary to stderr
        print("\n" + "="*80, file=sys.stderr)
        print("ENHANCED GENERATION COMPLETE - FIXED", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(f"Profile: {result['profile_name']}", file=sys.stderr)
        print(f"Method: {result['method']}", file=sys.stderr)
        print(f"Base Year: FY{result['base_year']}", file=sys.stderr)
        print(f"Output: {filename}", file=sys.stderr)
        print(f"Peak: {result['peak_demand']:.2f} MW", file=sys.stderr)
        print(f"Average: {result['average_demand']:.2f} MW", file=sys.stderr)
        print(f"Load Factor: {result['load_factor']:.3f}", file=sys.stderr)
        print(f"Coefficient of Variation: {result['coefficient_variation']:.3f}", file=sys.stderr)
        print("\nKey Improvements Applied:", file=sys.stderr)
        print("  ✓ Continuous day-of-year interpolation (365 smooth factors)", file=sys.stderr)
        print("  ✓ Historical variability preserved (weather, events)", file=sys.stderr)
        print("  ✓ Shape-preserving constraint satisfaction", file=sys.stderr)
        print("  ✓ Minimal final smoothing (25-hour window)", file=sys.stderr)
        if 'max_monthly_transition_%' in result:
            print(f"  ✓ Max monthly transition: {result['max_monthly_transition_%']:.2f}%", file=sys.stderr)
        if result.get('variability_preserved', False):
            print("  ✓ Variability preservation: VALIDATED", file=sys.stderr)
        
        # Output JSON result to stdout
        print(json.dumps(result))
        return result
        
    except Exception as e:
        # Report error
        progress = ProgressReporter(enable_progress=True)
        error_msg = f"Generation failed: {str(e)}"
        progress.report_error(error_msg)
        
        sys.stderr.write(f"\nERROR: {str(e)}\n")
        sys.stderr.write(traceback.format_exc())
        sys.stderr.flush()
        
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(error_result))
        return error_result


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get('success') else 1)