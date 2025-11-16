"""
Demand Forecasting Model Registry
==================================

Centralized configuration for all available forecasting models.
This is the single source of truth for model definitions, parameters, and constraints.

Usage:
    from config.model_registry import AVAILABLE_MODELS, DEFAULT_FORECAST_CONFIG

Author: KSEB Analytics Platform
Version: 1.0
"""

from typing import Dict, List, Any

# ==============================================================================
# MODEL REGISTRY
# ==============================================================================

AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
    'SLR': {
        'id': 'SLR',
        'name': 'Simple Linear Regression',
        'description': 'Year-based linear trend forecasting. Best for stable, linear growth patterns.',
        'requires_parameters': False,
        'min_data_points': 3,
        'enabled': True,
        'order': 1,
        'icon': '📈',
        'use_cases': [
            'Sectors with consistent historical growth',
            'Initial baseline forecasts',
            'Comparing against more complex models'
        ],
        'limitations': [
            'Cannot capture non-linear trends',
            'Ignores external economic factors'
        ]
    },

    'MLR': {
        'id': 'MLR',
        'name': 'Multiple Linear Regression',
        'description': 'Econometric parameter-based forecasting using GDP, GVA, and other indicators.',
        'requires_parameters': True,
        'parameter_config': {
            'type': 'multi_select',
            'source': 'correlation_analysis',  # Fetched from backend
            'min_selection': 1,
            'max_selection': 5,
            'label': 'Independent Variables',
            'help_text': 'Select economic indicators with strong correlation to electricity demand',
            'validation': {
                'require_high_correlation': True,
                'min_correlation_threshold': 0.3
            }
        },
        'min_data_points': 5,
        'enabled': True,
        'order': 2,
        'icon': '📊',
        'use_cases': [
            'Sectors with strong economic correlations',
            'Long-term strategic planning',
            'Policy impact analysis'
        ],
        'limitations': [
            'Requires reliable economic indicator data',
            'Assumes linear relationships',
            'Can overfit with too many parameters'
        ]
    },

    'WAM': {
        'id': 'WAM',
        'name': 'Weighted Average Method',
        'description': 'Weighted growth rate extrapolation. Recent years get higher weight.',
        'requires_parameters': True,
        'parameter_config': {
            'type': 'integer_input',
            'source': 'calculated',  # Dynamically calculated: max(3, row_count - 2)
            'min_value': 2,
            'max_value_formula': 'row_count - 2',
            'default': 3,
            'label': 'Number of Years',
            'help_text': 'Number of recent years to use for growth rate calculation',
            'validation': {
                'ensure_sufficient_data': True
            }
        },
        'min_data_points': 4,
        'enabled': True,
        'order': 3,
        'icon': '⚖️',
        'use_cases': [
            'Sectors with recent trend changes',
            'Short to medium-term forecasts',
            'Quick baseline projections'
        ],
        'limitations': [
            'Sensitive to recent volatility',
            'No consideration of external factors',
            'Can extrapolate recent anomalies'
        ]
    },

    'Time Series': {
        'id': 'Time Series',
        'name': 'Time Series Analysis (ARIMA/Prophet)',
        'description': 'Advanced statistical time series forecasting with seasonality and trend detection.',
        'requires_parameters': False,
        'min_data_points': 10,
        'enabled': False,  # Not yet implemented in UI
        'order': 4,
        'icon': '🔮',
        'use_cases': [
            'Sectors with clear seasonality',
            'Complex trend patterns',
            'Long historical data available'
        ],
        'limitations': [
            'Requires significant historical data',
            'Computationally intensive',
            'Black-box nature (less interpretable)'
        ],
        'future_release': '2025-Q2'
    }
}


# ==============================================================================
# DEFAULT PROJECT CONFIGURATION
# ==============================================================================

DEFAULT_FORECAST_CONFIG: Dict[str, Any] = {
    # COVID-19 Data Filtering
    'exclude_covid_years': True,
    'covid_years': [2020, 2021, 2022],  # Fiscal years (Indian FY: Apr-Mar)
    'covid_years_editable': True,  # Allow users to override

    # Model Selection Defaults
    'default_selected_models': ['SLR', 'MLR', 'WAM'],
    'default_wam_window': 3,

    # Advanced Options
    'auto_select_best_model': False,  # Future: ML-based model selection
    'parallel_execution': True,  # Run models concurrently per sector

    # Validation Rules
    'validation_rules': {
        'min_sectors': 1,
        'require_at_least_one_model': True,
        'warn_on_low_data_points': True,
        'warn_threshold_data_points': 10,
        'block_on_insufficient_data': True
    },

    # Output Configuration
    'output_formats': ['xlsx', 'json'],  # Excel + JSON results
    'save_model_metadata': True,  # Save model parameters and stats
    'save_diagnostics': True,  # Save R², MAPE, etc.

    # UI Preferences
    'show_model_descriptions': True,
    'show_data_quality_warnings': True,
    'enable_advanced_options': False  # Hide advanced settings by default
}


# ==============================================================================
# MODEL SELECTION HELPERS
# ==============================================================================

def get_enabled_models() -> List[Dict[str, Any]]:
    """
    Get list of enabled models sorted by order.

    Returns:
        List of model configurations (only enabled models)
    """
    return sorted(
        [m for m in AVAILABLE_MODELS.values() if m['enabled']],
        key=lambda x: x['order']
    )


def get_model_by_id(model_id: str) -> Dict[str, Any]:
    """
    Get model configuration by ID.

    Args:
        model_id: Model identifier (e.g., 'SLR', 'MLR')

    Returns:
        Model configuration dict or None if not found
    """
    return AVAILABLE_MODELS.get(model_id)


def get_available_models_for_sector(row_count: int, has_mlr_params: bool = False) -> List[Dict[str, Any]]:
    """
    Get models available for a sector based on data availability.

    Args:
        row_count: Number of data points available
        has_mlr_params: Whether MLR parameters (correlations) are available

    Returns:
        List of available model configs with availability status
    """
    available = []

    for model in get_enabled_models():
        model_copy = model.copy()

        # Check data point requirement
        meets_data_req = row_count >= model['min_data_points']

        # Special case: MLR needs correlation parameters
        if model['id'] == 'MLR':
            meets_data_req = meets_data_req and has_mlr_params

        model_copy['available'] = meets_data_req

        if not meets_data_req:
            if model['id'] == 'MLR' and not has_mlr_params:
                model_copy['unavailable_reason'] = 'No correlated economic indicators found'
            else:
                model_copy['unavailable_reason'] = (
                    f"Requires {model['min_data_points']} data points, "
                    f"only {row_count} available"
                )

        available.append(model_copy)

    return available


def calculate_wam_max_window(row_count: int) -> int:
    """
    Calculate maximum WAM window size based on available data.

    Formula: max(3, row_count - 2)
    Ensures at least 2 points remain for validation.

    Args:
        row_count: Number of historical data points

    Returns:
        Maximum allowed window size
    """
    return max(3, row_count - 2)


def get_recommended_models(row_count: int, mlr_params: List[str]) -> List[str]:
    """
    Get recommended models based on data quality and availability.

    Recommendation Logic:
    - MLR if 15+ points and strong correlations exist
    - WAM if 10+ points available
    - SLR always as baseline

    Args:
        row_count: Number of data points
        mlr_params: Available MLR parameters

    Returns:
        List of recommended model IDs
    """
    recommended = []

    # Prefer MLR for long-term forecasts with economic data
    if row_count >= 15 and len(mlr_params) >= 2:
        recommended.append('MLR')

    # WAM for medium-term with decent history
    if row_count >= 10:
        recommended.append('WAM')

    # SLR always available as baseline
    recommended.append('SLR')

    return recommended[:2]  # Return top 2


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

def validate_model_parameters(model_id: str, parameters: Any, row_count: int) -> Dict[str, Any]:
    """
    Validate model-specific parameters.

    Args:
        model_id: Model identifier
        parameters: Parameters to validate
        row_count: Number of data points available

    Returns:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str]
        }
    """
    errors = []
    warnings = []

    model = get_model_by_id(model_id)
    if not model:
        return {
            'valid': False,
            'errors': [f'Unknown model: {model_id}'],
            'warnings': []
        }

    # Check if model requires parameters
    if model['requires_parameters']:
        if model_id == 'MLR':
            if not parameters or len(parameters) == 0:
                errors.append('MLR requires at least one independent variable')
            elif len(parameters) > 5:
                warnings.append('Too many parameters may cause overfitting')

        elif model_id == 'WAM':
            if not isinstance(parameters, int):
                errors.append('WAM window must be an integer')
            elif parameters < 2:
                errors.append('WAM window must be at least 2')
            elif parameters > row_count - 2:
                errors.append(f'WAM window ({parameters}) exceeds maximum ({row_count - 2})')
            elif parameters < 3:
                warnings.append('Small window size may be too volatile')

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


# ==============================================================================
# METADATA EXPORT
# ==============================================================================

def export_model_registry() -> Dict[str, Any]:
    """
    Export complete model registry for API consumption.

    Returns:
        Dictionary with models, defaults, and metadata
    """
    return {
        'models': get_enabled_models(),
        'defaults': DEFAULT_FORECAST_CONFIG,
        'version': '1.0',
        'last_updated': '2025-11-14'
    }


if __name__ == '__main__':
    # Test/Demo
    print("=== Available Models ===")
    for model in get_enabled_models():
        print(f"\n{model['icon']} {model['name']}")
        print(f"   ID: {model['id']}")
        print(f"   Min Data Points: {model['min_data_points']}")
        print(f"   Requires Parameters: {model['requires_parameters']}")

    print("\n=== Sector Example (15 data points, 3 MLR params) ===")
    for model in get_available_models_for_sector(15, True):
        status = "✅ Available" if model['available'] else f"❌ {model.get('unavailable_reason', 'N/A')}"
        print(f"{model['name']}: {status}")

    print("\n=== Recommendations ===")
    print(f"Recommended: {get_recommended_models(15, ['GSDP', 'Per Capita GSDP', 'Manufacturing GVA'])}")
