"""
Application Configuration
=========================
Centralized configuration for the KSEB Energy Analytics Dash Application.
Contains all file names, sheet names, column names, and application constants.

This ensures consistency across the application and makes it easy to update
file names or add new templates without changing multiple files.

Author: KSEB Analytics Team
Date: 2025-11-16
"""

from pathlib import Path
from typing import Dict, List

# ==================== FILE PATHS & NAMES ====================

class TemplateFiles:
    """Excel template file names used throughout the application."""

    # Input template files (located in project/inputs/ directory)
    INPUT_DEMAND_FILE = 'input_demand_file.xlsx'
    LOAD_CURVE_TEMPLATE = 'load_curve_template.xlsx'
    PYPSA_INPUT_TEMPLATE = 'pypsa_input_template.xlsx'

    # All required template files
    ALL_TEMPLATES = [
        INPUT_DEMAND_FILE,
        LOAD_CURVE_TEMPLATE,
        PYPSA_INPUT_TEMPLATE
    ]


class InputDemandSheets:
    """Sheet names in input_demand_file.xlsx"""

    # Main configuration sheets
    MAIN = 'main'
    COMMONS = 'commons'
    ECONOMIC_INDICATORS = 'Economic_Indicators'
    UNITS = 'units'

    # Sector sheets
    DOMESTIC_LT = 'Domestic_lt'
    COMMERCIAL_LT = 'Commercial_lt'
    INDUSTRIAL_LT = 'industrial_lt'
    HT_EHT = 'ht_eht'
    PUBLIC_LIGHTING = 'public_lighting'
    RAILWAY_TRACTION = 'railway_traction'
    ROAD_TRANSPORT = 'Road transport'
    AGRICULTURE = 'Agriculture'
    SOLAR_ROOFTOP = 'solar_rooftop'
    EV_TRANSPORT = 'ev_transport'
    GREEN_HYDROGEN = 'green_hydrogen'
    OTHERS = 'others'
    LICENCEES = 'licencees'

    # All sector sheets
    SECTOR_SHEETS = [
        DOMESTIC_LT,
        COMMERCIAL_LT,
        INDUSTRIAL_LT,
        HT_EHT,
        PUBLIC_LIGHTING,
        RAILWAY_TRACTION,
        ROAD_TRANSPORT,
        AGRICULTURE,
        SOLAR_ROOFTOP,
        EV_TRANSPORT,
        GREEN_HYDROGEN,
        OTHERS,
        LICENCEES
    ]


class LoadCurveSheets:
    """Sheet names in load_curve_template.xlsx"""

    TOTAL_DEMAND = 'Total Demand'
    HOLIDAYS = 'Holidays'
    PAST_HOURLY_DEMAND = 'Past_Hourly_Demand'
    AVERAGE_DEMAND = 'average_demand'
    MAX_DEMAND = 'max_demand'
    LOAD_FACTOR = 'load_factor'

    ALL_SHEETS = [
        TOTAL_DEMAND,
        HOLIDAYS,
        PAST_HOURLY_DEMAND,
        AVERAGE_DEMAND,
        MAX_DEMAND,
        LOAD_FACTOR
    ]


class PyPSASheets:
    """Sheet names in pypsa_input_template.xlsx"""

    # Generator sheets
    BASE_GENERATORS = 'base Generators'
    GENERATORS = 'Generators'
    NEW_GENERATORS = 'New_Generators'
    PIPELINE_GENERATORS_P_MAX = 'Pipe_Line_Generators_p_max'
    PIPELINE_GENERATORS_P_MIN = 'Pipe_Line_Generators_p_min'

    # Storage sheets
    NEW_STORAGE = 'New_Storage'
    PIPELINE_STORAGE_P_MIN = 'Pipe_Line_Storage_p_min'

    # Network sheets
    BUSES = 'Buses'
    LINKS = 'Links'

    # Demand sheets
    DEMAND = 'Demand'
    DEMAND_FINAL = 'Demand_final'

    # Cost & Parameter sheets
    FUEL_COST = 'Fuel_cost'
    CAPITAL_COST = 'Capital_cost'
    STARTUP_COST = 'Startupcost'
    FOM = 'FOM'
    P_MIN_PU = 'P_min_pu'
    P_MAX_PU = 'P_max_pu'
    CO2 = 'CO2'
    WACC = 'wacc'
    LIFETIME = 'Lifetime'

    # Configuration sheets
    SETTINGS = 'Settings'
    CUSTOM_DAYS = 'Custom days'

    ALL_SHEETS = [
        BASE_GENERATORS, GENERATORS, NEW_GENERATORS,
        PIPELINE_GENERATORS_P_MAX, PIPELINE_GENERATORS_P_MIN,
        NEW_STORAGE, PIPELINE_STORAGE_P_MIN,
        BUSES, LINKS,
        DEMAND, DEMAND_FINAL,
        FUEL_COST, CAPITAL_COST, STARTUP_COST, FOM,
        P_MIN_PU, P_MAX_PU, CO2, WACC, LIFETIME,
        SETTINGS, CUSTOM_DAYS
    ]


class ColumnNames:
    """Common column names used across Excel files."""

    # Time columns
    YEAR = 'Year'
    DATE = 'Date'
    HOUR = 'Hour'

    # Demand columns
    ELECTRICITY = 'Electricity'
    DEMAND = 'Demand'

    # Economic indicators
    TOTAL_POPULATION = 'Total Population'
    GSDP = 'GSDP'
    PER_CAPITA_GSDP = 'Per Capita GSDP'
    AGRICULTURE_GVA = 'Agriculture_GVA'
    NO_OF_HOUSEHOLDS = 'No of Households'
    RAINFALL = 'Rainfall'
    MANUFACTURING_GVA = 'Manufacturing GVA'
    COMMERCIAL_GVA = 'Commercial gva'


# ==================== APPLICATION CONSTANTS ====================

class AppDefaults:
    """Default values and constants for the application."""

    # Forecasting defaults
    MIN_DATA_POINTS_FORECASTING = 5
    DEFAULT_FORECAST_YEARS = 10

    # Load profile defaults
    HOURS_PER_YEAR = 8760

    # PyPSA defaults
    DEFAULT_PYPSA_SCENARIO = 'PyPSA_Scenario_V1'
    DEFAULT_SOLVER = 'highs'

    # Cache settings
    NETWORK_CACHE_MAX_SIZE = 10
    NETWORK_CACHE_TTL_SECONDS = 300  # 5 minutes

    # Progress polling intervals (milliseconds)
    FORECAST_PROGRESS_INTERVAL = 1000
    PROFILE_PROGRESS_INTERVAL = 1000
    PYPSA_PROGRESS_INTERVAL = 1000


class DirectoryStructure:
    """Standard project directory structure."""

    INPUTS = 'inputs'
    RESULTS = 'results'

    # Results subdirectories
    DEMAND_FORECASTS = 'demand_forecasts'
    LOAD_PROFILES = 'load_profiles'
    PYPSA_OPTIMIZATION = 'pypsa_optimization'

    @classmethod
    def get_results_subdirs(cls) -> List[str]:
        """Get all results subdirectory names."""
        return [
            cls.DEMAND_FORECASTS,
            cls.LOAD_PROFILES,
            cls.PYPSA_OPTIMIZATION
        ]


class DataMarkers:
    """Special markers used in Excel files to indicate sections."""

    # Markers in input_demand_file.xlsx
    ECONOMETRIC_PARAMETERS = '~Econometric_Parameters'
    SOLAR_SHARE = '~Solar_share'
    FORECAST_CONFIG = '~Forecast_Config'

    # Markers in load_curve_template.xlsx
    HOLIDAY_DATES = '~Holiday_Dates'

    # Markers in pypsa_input_template.xlsx
    CUSTOM_DAYS_MARKER = '~Custom_Days'


class UIConstants:
    """UI/UX constants for consistent styling."""

    # Color palette
    PRIMARY_COLOR = '#4f46e5'  # Indigo-600
    SECONDARY_COLOR = '#6366f1'  # Indigo-500
    SUCCESS_COLOR = '#10b981'  # Green-500
    WARNING_COLOR = '#f59e0b'  # Amber-500
    ERROR_COLOR = '#ef4444'  # Red-500
    INFO_COLOR = '#3b82f6'  # Blue-500

    # Background colors
    BG_SLATE_900 = '#0f172a'
    BG_SLATE_800 = '#1e293b'
    BG_SLATE_50 = '#f8fafc'

    # Text colors
    TEXT_SLATE_900 = '#0f172a'
    TEXT_SLATE_600 = '#475569'
    TEXT_SLATE_500 = '#64748b'

    # Layout dimensions
    TOPBAR_HEIGHT = '64px'
    SIDEBAR_WIDTH = '288px'
    SIDEBAR_COLLAPSED_WIDTH = '80px'
    WORKFLOW_WIDTH = '80px'

    # Chart colors for PyPSA
    PYPSA_COLORS = {
        'Solar': '#fbbf24',
        'Wind': '#3b82f6',
        'Hydro': '#06b6d4',
        'Battery': '#8b5cf6',
        'Gas': '#ef4444',
        'Coal': '#6b7280',
        'Nuclear': '#10b981',
        'Biomass': '#84cc16',
        'CCGT': '#f97316',
        'OCGT': '#dc2626',
        'Load': '#000000'
    }


# ==================== HELPER FUNCTIONS ====================

def get_project_template_path(project_path: str, template_name: str) -> Path:
    """
    Get the full path to a template file in a project's inputs directory.

    Parameters
    ----------
    project_path : str
        Path to the project folder
    template_name : str
        Name of the template file (e.g., 'input_demand_file.xlsx')

    Returns
    -------
    Path
        Full path to the template file
    """
    return Path(project_path) / DirectoryStructure.INPUTS / template_name


def get_project_results_path(project_path: str, results_type: str) -> Path:
    """
    Get the full path to a results subdirectory.

    Parameters
    ----------
    project_path : str
        Path to the project folder
    results_type : str
        Type of results ('demand_forecasts', 'load_profiles', 'pypsa_optimization')

    Returns
    -------
    Path
        Full path to the results subdirectory
    """
    return Path(project_path) / DirectoryStructure.RESULTS / results_type


def validate_template_file(file_path: Path) -> Dict[str, any]:
    """
    Validate that a template file exists and is accessible.

    Parameters
    ----------
    file_path : Path
        Path to the template file

    Returns
    -------
    dict
        Validation result with 'valid' (bool) and 'message' (str) keys
    """
    if not file_path.exists():
        return {
            'valid': False,
            'message': f'Template file not found: {file_path.name}'
        }

    if not file_path.is_file():
        return {
            'valid': False,
            'message': f'Path is not a file: {file_path.name}'
        }

    if file_path.suffix not in ['.xlsx', '.xls']:
        return {
            'valid': False,
            'message': f'Invalid file type: {file_path.suffix}. Expected .xlsx or .xls'
        }

    return {
        'valid': True,
        'message': 'Template file is valid'
    }


# Export all classes for easy import
__all__ = [
    'TemplateFiles',
    'InputDemandSheets',
    'LoadCurveSheets',
    'PyPSASheets',
    'ColumnNames',
    'AppDefaults',
    'DirectoryStructure',
    'DataMarkers',
    'UIConstants',
    'get_project_template_path',
    'get_project_results_path',
    'validate_template_file'
]
