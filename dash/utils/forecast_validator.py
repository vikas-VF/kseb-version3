"""
Forecast Configuration Validator
=================================

Validates forecast configurations before execution to prevent invalid runs.

Features:
- Pre-submission validation
- Data quality checks
- Model parameter validation
- User-friendly error/warning messages

Author: KSEB Analytics Platform
Version: 1.0
"""

import sys
import os
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.model_registry import (
    AVAILABLE_MODELS,
    DEFAULT_FORECAST_CONFIG,
    get_model_by_id,
    validate_model_parameters
)


class ValidationResult:
    """Container for validation results"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []

    @property
    def valid(self) -> bool:
        """Configuration is valid if no errors exist"""
        return len(self.errors) == 0

    def add_error(self, message: str):
        """Add a blocking error"""
        self.errors.append(message)

    def add_warning(self, message: str):
        """Add a non-blocking warning"""
        self.warnings.append(message)

    def add_suggestion(self, message: str):
        """Add a best-practice suggestion"""
        self.suggestions.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary"""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions
        }


def validate_forecast_config(
    config: Dict[str, Any],
    sector_metadata: Dict[str, Dict[str, Any]]
) -> ValidationResult:
    """
    Comprehensive validation of forecast configuration.

    Args:
        config: Forecast configuration dictionary
            {
                'scenario_name': str,
                'target_year': int,
                'exclude_covid_years': bool,
                'sectors': [
                    {
                        'name': str,
                        'models': List[str],
                        'mlr_parameters': List[str],  # Optional
                        'wam_window': int,  # Optional
                        'data': List[Dict]
                    },
                    ...
                ]
            }

        sector_metadata: Metadata per sector
            {
                'Agriculture': {
                    'row_count': 20,
                    'correlations': [...],
                    'mlr_params': ['GSDP', 'Per Capita GSDP'],
                    'max_wam_window': 18
                },
                ...
            }

    Returns:
        ValidationResult object with errors, warnings, and suggestions
    """
    result = ValidationResult()

    # ============================================================
    # LEVEL 1: BASIC CONFIGURATION CHECKS
    # ============================================================

    # Check 1: Scenario name provided
    if not config.get('scenario_name') or not config['scenario_name'].strip():
        result.add_error('Scenario name is required')

    # Check 2: Valid target year
    target_year = config.get('target_year')
    if not target_year:
        result.add_error('Target year is required')
    elif not isinstance(target_year, int):
        result.add_error('Target year must be an integer')
    elif target_year < 2025 or target_year > 2100:
        result.add_warning(f'Unusual target year: {target_year}. Verify this is correct.')

    # Check 3: At least one sector selected
    sectors = config.get('sectors', [])
    if not sectors or len(sectors) == 0:
        result.add_error('No sectors selected for forecasting')
        return result  # Cannot proceed without sectors

    # ============================================================
    # LEVEL 2: SECTOR-SPECIFIC VALIDATION
    # ============================================================

    for idx, sector_config in enumerate(sectors):
        sector_name = sector_config.get('name', f'Sector #{idx + 1}')
        models = sector_config.get('models', [])
        sector_meta = sector_metadata.get(sector_name, {})
        row_count = sector_meta.get('row_count', 0)

        # Check 4: Sector has at least one model
        if not models or len(models) == 0:
            result.add_error(f"❌ {sector_name}: No forecasting model selected")
            continue  # Skip further checks for this sector

        # Check 5: Sector has data
        if row_count == 0:
            result.add_error(f"❌ {sector_name}: No historical data available")
            continue

        # Check each selected model
        for model_id in models:
            model_config = get_model_by_id(model_id)

            if not model_config:
                result.add_error(f"❌ {sector_name}: Unknown model '{model_id}'")
                continue

            # Check 6: Model enabled
            if not model_config.get('enabled'):
                result.add_error(
                    f"❌ {sector_name}: Model '{model_id}' is not enabled. "
                    f"{model_config.get('future_release', 'Coming soon')}"
                )
                continue

            # Check 7: Sufficient data points for model
            min_required = model_config['min_data_points']
            if row_count < min_required:
                result.add_error(
                    f"❌ {sector_name} ({model_id}): Requires {min_required} data points, "
                    f"only {row_count} available"
                )

            # Check 8: Model-specific parameter validation
            if model_id == 'MLR':
                mlr_params = sector_config.get('mlr_parameters', [])
                available_params = sector_meta.get('mlr_params', [])

                if not mlr_params or len(mlr_params) == 0:
                    result.add_error(
                        f"❌ {sector_name} (MLR): No independent variables selected"
                    )
                elif not available_params or len(available_params) == 0:
                    result.add_error(
                        f"❌ {sector_name} (MLR): No correlated economic indicators found in dataset"
                    )
                else:
                    # Validate parameters exist
                    invalid_params = [p for p in mlr_params if p not in available_params]
                    if invalid_params:
                        result.add_error(
                            f"❌ {sector_name} (MLR): Invalid parameters: {', '.join(invalid_params)}"
                        )

                    # Warning for too many parameters
                    if len(mlr_params) > 3:
                        result.add_warning(
                            f"⚠️ {sector_name} (MLR): {len(mlr_params)} parameters selected. "
                            "Too many may cause overfitting."
                        )

            elif model_id == 'WAM':
                wam_window = sector_config.get('wam_window')
                max_window = sector_meta.get('max_wam_window', row_count - 2)

                if not wam_window:
                    result.add_error(
                        f"❌ {sector_name} (WAM): Window size not specified"
                    )
                elif not isinstance(wam_window, int):
                    result.add_error(
                        f"❌ {sector_name} (WAM): Window size must be an integer"
                    )
                elif wam_window < 2:
                    result.add_error(
                        f"❌ {sector_name} (WAM): Window size must be at least 2"
                    )
                elif wam_window > max_window:
                    result.add_error(
                        f"❌ {sector_name} (WAM): Window size ({wam_window}) exceeds "
                        f"maximum ({max_window})"
                    )
                elif wam_window < 3:
                    result.add_warning(
                        f"⚠️ {sector_name} (WAM): Window size ({wam_window}) is small. "
                        "May produce volatile forecasts."
                    )

        # ============================================================
        # LEVEL 3: DATA QUALITY WARNINGS
        # ============================================================

        # Warning: Limited data
        if row_count < DEFAULT_FORECAST_CONFIG['validation_rules']['warn_threshold_data_points']:
            result.add_warning(
                f"⚠️ {sector_name}: Limited historical data ({row_count} points). "
                "Forecast accuracy may be reduced."
            )

        # Warning: Only one model selected
        if len(models) == 1:
            result.add_suggestion(
                f"💡 {sector_name}: Consider selecting multiple models for comparison and validation."
            )

        # Suggestion: Missing recommended models
        recommended = sector_meta.get('recommended_models', [])
        missing_recommended = [m for m in recommended if m not in models]
        if missing_recommended:
            result.add_suggestion(
                f"💡 {sector_name}: Recommended models not selected: {', '.join(missing_recommended)}"
            )

    # ============================================================
    # LEVEL 4: GLOBAL CONFIGURATION CHECKS
    # ============================================================

    # COVID year handling
    if config.get('exclude_covid_years'):
        covid_years = config.get('covid_years', DEFAULT_FORECAST_CONFIG['covid_years'])
        result.add_suggestion(
            f"💡 COVID-19 years ({', '.join(map(str, covid_years))}) will be excluded from training. "
            "Verify this matches your fiscal year definition (Apr-Mar for India)."
        )

    # Multiple sectors
    if len(sectors) >= 5:
        result.add_suggestion(
            "💡 Processing multiple sectors. This may take several minutes. "
            "Progress updates will be shown in real-time."
        )

    return result


def validate_sector_data(sector_name: str, data: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validate sector data structure and content.

    Args:
        sector_name: Name of sector
        data: List of data dictionaries with Year, Electricity, and economic indicators

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    # Check 1: Data exists
    if not data or len(data) == 0:
        result.add_error(f"{sector_name}: No data provided")
        return result

    # Check 2: Required columns
    first_row = data[0]
    if 'Year' not in first_row:
        result.add_error(f"{sector_name}: Missing 'Year' column")
    if 'Electricity' not in first_row:
        result.add_error(f"{sector_name}: Missing 'Electricity' column")

    if not result.valid:
        return result

    # Check 3: Data completeness
    years = [row.get('Year') for row in data]
    electricity = [row.get('Electricity') for row in data]

    missing_years = sum(1 for y in years if y is None)
    missing_electricity = sum(1 for e in electricity if e is None)

    if missing_years > 0:
        result.add_warning(f"{sector_name}: {missing_years} rows have missing Year values")
    if missing_electricity > 0:
        result.add_warning(f"{sector_name}: {missing_electricity} rows have missing Electricity values")

    # Check 4: Year continuity
    valid_years = sorted([y for y in years if y is not None])
    if len(valid_years) > 1:
        year_gaps = []
        for i in range(1, len(valid_years)):
            gap = valid_years[i] - valid_years[i - 1]
            if gap > 1:
                year_gaps.append(f"{valid_years[i - 1]}-{valid_years[i]} ({gap} years)")

        if year_gaps:
            result.add_warning(
                f"{sector_name}: Data has gaps: {', '.join(year_gaps)}"
            )

    # Check 5: Negative values
    negative_electricity = sum(1 for e in electricity if e is not None and e < 0)
    if negative_electricity > 0:
        result.add_error(
            f"{sector_name}: {negative_electricity} rows have negative Electricity values"
        )

    return result


def get_validation_summary(result: ValidationResult) -> str:
    """
    Generate human-readable validation summary.

    Args:
        result: ValidationResult object

    Returns:
        Formatted string summary
    """
    lines = []

    if result.valid:
        lines.append("✅ **Configuration Valid**")
    else:
        lines.append("❌ **Configuration Invalid**")

    if result.errors:
        lines.append(f"\n**Errors ({len(result.errors)}):**")
        for error in result.errors:
            lines.append(f"  • {error}")

    if result.warnings:
        lines.append(f"\n**Warnings ({len(result.warnings)}):**")
        for warning in result.warnings:
            lines.append(f"  • {warning}")

    if result.suggestions:
        lines.append(f"\n**Suggestions ({len(result.suggestions)}):**")
        for suggestion in result.suggestions:
            lines.append(f"  • {suggestion}")

    return "\n".join(lines)


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    # Test case 1: Valid configuration
    test_config = {
        'scenario_name': 'Test_Scenario_2037',
        'target_year': 2037,
        'exclude_covid_years': True,
        'sectors': [
            {
                'name': 'Agriculture',
                'models': ['SLR', 'MLR', 'WAM'],
                'mlr_parameters': ['GSDP', 'Per Capita GSDP'],
                'wam_window': 3,
                'data': [{'Year': 2020, 'Electricity': 1000}]
            }
        ]
    }

    test_metadata = {
        'Agriculture': {
            'row_count': 20,
            'mlr_params': ['GSDP', 'Per Capita GSDP', 'Agriculture_GVA'],
            'max_wam_window': 18
        }
    }

    print("=== Test Case 1: Valid Configuration ===")
    result = validate_forecast_config(test_config, test_metadata)
    print(get_validation_summary(result))

    # Test case 2: Invalid configuration
    test_config_invalid = {
        'scenario_name': '',
        'target_year': 1990,
        'sectors': [
            {
                'name': 'Agriculture',
                'models': [],
                'data': []
            }
        ]
    }

    print("\n=== Test Case 2: Invalid Configuration ===")
    result2 = validate_forecast_config(test_config_invalid, {})
    print(get_validation_summary(result2))
