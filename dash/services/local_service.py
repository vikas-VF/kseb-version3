"""
Local Service - Direct Business Logic Execution (No FastAPI)
Replaces api_client.py for fully self-contained Dash webapp
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class LocalService:
    """
    Local service that directly executes business logic without HTTP calls.
    Provides same interface as APIClient but uses direct function calls.
    """

    def __init__(self):
        pass

    # ==================== PROJECT MANAGEMENT ====================

    def create_project(self, name: str, location: str, description: str = '') -> Dict:
        """Create new project with folder structure"""
        try:
            project_path = os.path.join(location, name)

            # Create directory structure
            os.makedirs(project_path, exist_ok=True)
            os.makedirs(os.path.join(project_path, 'inputs'), exist_ok=True)
            os.makedirs(os.path.join(project_path, 'results', 'demand_forecasts'), exist_ok=True)
            os.makedirs(os.path.join(project_path, 'results', 'load_profiles'), exist_ok=True)
            os.makedirs(os.path.join(project_path, 'results', 'pypsa_optimization'), exist_ok=True)

            # Create project.json
            project_meta = {
                'name': name,
                'path': project_path,
                'description': description,
                'created': pd.Timestamp.now().isoformat()
            }

            with open(os.path.join(project_path, 'project.json'), 'w') as f:
                json.dump(project_meta, f, indent=2)

            return {'success': True, 'project': project_meta}

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return {'success': False, 'error': str(e)}

    def load_project(self, project_path: str) -> Dict:
        """Load existing project"""
        try:
            project_json = os.path.join(project_path, 'project.json')

            if not os.path.exists(project_json):
                return {'success': False, 'error': 'project.json not found'}

            with open(project_json, 'r') as f:
                project_meta = json.load(f)

            return {'success': True, 'project': project_meta}

        except Exception as e:
            logger.error(f"Error loading project: {e}")
            return {'success': False, 'error': str(e)}

    def check_directory(self, path: str) -> Dict:
        """Validate directory path"""
        exists = os.path.exists(path) and os.path.isdir(path)
        return {'exists': exists, 'is_directory': exists}

    # ==================== SECTORS ====================

    def get_sectors(self, project_path: str) -> Dict:
        """Get consumption sectors from Excel file"""
        try:
            # Look for input Excel file
            inputs_dir = os.path.join(project_path, 'inputs')
            excel_files = [f for f in os.listdir(inputs_dir) if f.endswith('.xlsx') or f.endswith('.xls')]

            if not excel_files:
                return {'sectors': ['Residential', 'Commercial', 'Industrial', 'Agriculture', 'Public Lighting']}

            # Read first Excel file to get sectors
            excel_path = os.path.join(inputs_dir, excel_files[0])
            xls = pd.ExcelFile(excel_path)

            # Filter out sheets that are sectors (exclude metadata sheets)
            sectors = [sheet for sheet in xls.sheet_names
                      if sheet not in ['Metadata', 'Info', 'Config', 'Summary']]

            return {'sectors': sectors}

        except Exception as e:
            logger.error(f"Error getting sectors: {e}")
            # Return default sectors
            return {'sectors': ['Residential', 'Commercial', 'Industrial', 'Agriculture', 'Public Lighting']}

    # ==================== EXCEL PARSING ====================

    def extract_sector_data(self, project_path: str, sector: str) -> Dict:
        """Extract sector data from Excel"""
        try:
            inputs_dir = os.path.join(project_path, 'inputs')
            excel_files = [f for f in os.listdir(inputs_dir) if f.endswith('.xlsx')]

            if not excel_files:
                return {'success': False, 'error': 'No Excel file found'}

            excel_path = os.path.join(inputs_dir, excel_files[0])
            df = pd.read_excel(excel_path, sheet_name=sector)

            return {
                'success': True,
                'data': df.to_dict('records'),
                'columns': df.columns.tolist()
            }

        except Exception as e:
            logger.error(f"Error extracting sector data: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== CONSOLIDATED VIEW ====================

    def get_consolidated_electricity(self, project_path: str, sectors: Optional[List[str]] = None) -> Dict:
        """Get consolidated electricity data"""
        try:
            inputs_dir = os.path.join(project_path, 'inputs')
            excel_files = [f for f in os.listdir(inputs_dir) if f.endswith('.xlsx')]

            if not excel_files:
                return {'success': False, 'error': 'No Excel file found'}

            excel_path = os.path.join(inputs_dir, excel_files[0])

            # Read all sectors and aggregate
            if sectors is None:
                sectors_response = self.get_sectors(project_path)
                sectors = sectors_response.get('sectors', [])

            consolidated_data = []
            for sector in sectors:
                try:
                    df = pd.read_excel(excel_path, sheet_name=sector)
                    if 'Year' in df.columns and 'Electricity' in df.columns:
                        consolidated_data.append(df[['Year', 'Electricity']])
                except:
                    continue

            if consolidated_data:
                # Merge all sectors
                result = consolidated_data[0].copy()
                for df in consolidated_data[1:]:
                    result = result.merge(df, on='Year', how='outer', suffixes=('', '_dup'))

                # Sum electricity columns
                elec_cols = [col for col in result.columns if 'Electricity' in col]
                result['Total_Electricity'] = result[elec_cols].sum(axis=1)

                return {
                    'success': True,
                    'data': result[['Year', 'Total_Electricity']].to_dict('records')
                }

            return {'success': False, 'error': 'No valid data found'}

        except Exception as e:
            logger.error(f"Error getting consolidated data: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== COLOR SETTINGS ====================

    def get_color_settings(self, project_path: str) -> Dict:
        """Get color configuration"""
        try:
            color_file = os.path.join(project_path, 'color.json')

            if os.path.exists(color_file):
                with open(color_file, 'r') as f:
                    colors = json.load(f)
                return {'colors': colors}

            # Return default colors
            default_colors = {
                'Residential': '#3b82f6',
                'Commercial': '#10b981',
                'Industrial': '#f59e0b',
                'Agriculture': '#8b5cf6',
                'Public Lighting': '#ec4899'
            }
            return {'colors': default_colors}

        except Exception as e:
            logger.error(f"Error getting colors: {e}")
            return {'colors': {}}

    def save_color_settings(self, project_path: str, colors: Dict) -> Dict:
        """Save color configuration"""
        try:
            color_file = os.path.join(project_path, 'color.json')

            with open(color_file, 'w') as f:
                json.dump(colors, f, indent=2)

            return {'success': True}

        except Exception as e:
            logger.error(f"Error saving colors: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== CORRELATION ====================

    def get_sector_correlation(self, project_path: str, sector: str) -> Dict:
        """Calculate correlation for sector"""
        try:
            # Extract sector data
            data_response = self.extract_sector_data(project_path, sector)

            if not data_response.get('success'):
                return {'success': False, 'error': 'Could not load sector data'}

            df = pd.DataFrame(data_response['data'])

            # Calculate correlation matrix
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            correlation_matrix = df[numeric_cols].corr()

            return {
                'success': True,
                'correlation_matrix': correlation_matrix.to_dict(),
                'top_correlations': []  # TODO: Extract top correlations
            }

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== FORECASTING ====================

    def start_demand_forecast(self, project_path: str, config: Dict) -> Dict:
        """Start demand forecasting process"""
        try:
            # Import forecasting model
            import sys
            models_path = os.path.join(os.path.dirname(__file__), '..', 'models')
            if models_path not in sys.path:
                sys.path.insert(0, models_path)

            from forecasting import DemandForecaster

            # Create forecaster instance
            forecaster = DemandForecaster(project_path)

            # Execute forecasting
            results = forecaster.run_forecast(config)

            return {
                'success': True,
                'process_id': 'local_forecast',
                'results': results
            }

        except Exception as e:
            logger.error(f"Error starting forecast: {e}")
            return {'success': False, 'error': str(e)}

    def get_forecast_progress(self, project_path: str, process_id: str) -> Dict:
        """Get forecast progress (for local execution, return completed)"""
        # For local execution, forecasting is synchronous
        return {
            'status': 'completed',
            'progress': 100,
            'current_task': 'Forecast completed',
            'logs': ['Forecast executed successfully']
        }

    def cancel_forecast(self, process_id: str) -> Dict:
        """Cancel forecast (not applicable for local execution)"""
        return {'success': False, 'error': 'Cannot cancel local execution'}

    # ==================== SCENARIOS ====================

    def get_scenarios(self, project_path: str) -> Dict:
        """List all forecast scenarios"""
        try:
            scenarios_dir = os.path.join(project_path, 'results', 'demand_forecasts')

            if not os.path.exists(scenarios_dir):
                return {'scenarios': []}

            scenarios = [d for d in os.listdir(scenarios_dir)
                        if os.path.isdir(os.path.join(scenarios_dir, d))]

            return {'scenarios': scenarios}

        except Exception as e:
            logger.error(f"Error getting scenarios: {e}")
            return {'scenarios': []}

    def get_scenario_sectors(self, project_path: str, scenario_name: str) -> Dict:
        """Get sectors in scenario"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            excel_path = os.path.join(scenario_dir, 'forecast_results.xlsx')

            if not os.path.exists(excel_path):
                return {'sectors': []}

            xls = pd.ExcelFile(excel_path)
            sectors = [sheet for sheet in xls.sheet_names if sheet != 'Consolidated']

            return {'sectors': sectors}

        except Exception as e:
            logger.error(f"Error getting scenario sectors: {e}")
            return {'sectors': []}

    def get_sector_data(self, project_path: str, scenario_name: str, sector_name: str) -> Dict:
        """Get forecast data for specific sector"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            excel_path = os.path.join(scenario_dir, 'forecast_results.xlsx')

            if not os.path.exists(excel_path):
                return {'success': False, 'error': 'Results file not found'}

            df = pd.read_excel(excel_path, sheet_name=sector_name)

            return {
                'success': True,
                'data': df.to_dict('records'),
                'columns': df.columns.tolist()
            }

        except Exception as e:
            logger.error(f"Error getting sector data: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== LOAD PROFILES ====================

    def get_load_profiles(self, project_path: str) -> Dict:
        """List all load profile files"""
        try:
            profiles_dir = os.path.join(project_path, 'results', 'load_profiles')

            if not os.path.exists(profiles_dir):
                return {'profiles': []}

            profiles = [d for d in os.listdir(profiles_dir)
                       if os.path.isdir(os.path.join(profiles_dir, d))]

            return {'profiles': profiles}

        except Exception as e:
            logger.error(f"Error getting profiles: {e}")
            return {'profiles': []}

    def generate_profile(self, config: Dict) -> Dict:
        """Start load profile generation"""
        try:
            # Import load profile generation model
            import sys
            models_path = os.path.join(os.path.dirname(__file__), '..', 'models')
            if models_path not in sys.path:
                sys.path.insert(0, models_path)

            from load_profile_generation import LoadProfileGenerator

            # Create generator instance
            generator = LoadProfileGenerator(config['project_path'])

            # Execute generation
            results = generator.generate(config)

            return {
                'success': True,
                'process_id': 'local_profile_gen',
                'results': results
            }

        except Exception as e:
            logger.error(f"Error generating profile: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== PyPSA ====================

    def get_pypsa_scenarios(self, project_path: str) -> Dict:
        """List all PyPSA scenarios"""
        try:
            pypsa_dir = os.path.join(project_path, 'results', 'pypsa_optimization')

            if not os.path.exists(pypsa_dir):
                return {'scenarios': []}

            scenarios = [d for d in os.listdir(pypsa_dir)
                        if os.path.isdir(os.path.join(pypsa_dir, d))]

            return {'scenarios': scenarios}

        except Exception as e:
            logger.error(f"Error getting PyPSA scenarios: {e}")
            return {'scenarios': []}

    def run_pypsa_model(self, config: Dict) -> Dict:
        """Execute PyPSA model"""
        try:
            # Import PyPSA model executor
            import sys
            models_path = os.path.join(os.path.dirname(__file__), '..', 'models')
            if models_path not in sys.path:
                sys.path.insert(0, models_path)

            from pypsa_model_executor import run_pypsa_model_complete

            # Execute PyPSA optimization
            results = run_pypsa_model_complete(config)

            return {
                'success': True,
                'process_id': 'local_pypsa',
                'results': results
            }

        except Exception as e:
            logger.error(f"Error running PyPSA model: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== T&D LOSSES ====================

    def get_td_losses(self, project_path: str, scenario_name: str) -> Dict:
        """Get T&D loss configuration"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            meta_file = os.path.join(scenario_dir, 'metadata.json')

            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                return {'td_losses': metadata.get('td_losses', {})}

            return {'td_losses': {}}

        except Exception as e:
            logger.error(f"Error getting T&D losses: {e}")
            return {'td_losses': {}}

    def save_td_losses(self, project_path: str, scenario_name: str, losses: Dict) -> Dict:
        """Save T&D loss configuration"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            meta_file = os.path.join(scenario_dir, 'metadata.json')

            metadata = {}
            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)

            metadata['td_losses'] = losses

            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            return {'success': True}

        except Exception as e:
            logger.error(f"Error saving T&D losses: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== METADATA ====================

    def get_scenario_metadata(self, project_path: str, scenario_name: str) -> Dict:
        """Get scenario metadata"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            meta_file = os.path.join(scenario_dir, 'metadata.json')

            if os.path.exists(meta_file):
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                return metadata

            return {}

        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            return {}

    def get_available_models(self, project_path: str, scenario_name: str) -> Dict:
        """Get available forecast models in scenario"""
        metadata = self.get_scenario_metadata(project_path, scenario_name)
        return {'models': metadata.get('models', [])}

    def calculate_consolidated(self, project_path: str, scenario_name: str, config: Dict) -> Dict:
        """Calculate consolidated forecast from sectors"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            excel_path = os.path.join(scenario_dir, 'forecast_results.xlsx')

            if not os.path.exists(excel_path):
                return {'success': False, 'error': 'Results file not found'}

            xls = pd.ExcelFile(excel_path)
            sectors = [sheet for sheet in xls.sheet_names if sheet != 'Consolidated']

            # Aggregate all sectors
            consolidated = None
            for sector in sectors:
                df = pd.read_excel(excel_path, sheet_name=sector)
                if consolidated is None:
                    consolidated = df.copy()
                else:
                    # Sum numeric columns
                    for col in df.columns:
                        if col != 'Year' and pd.api.types.is_numeric_dtype(df[col]):
                            consolidated[col] = consolidated.get(col, 0) + df[col]

            return {
                'success': True,
                'data': consolidated.to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error calculating consolidated: {e}")
            return {'success': False, 'error': str(e)}

    def save_consolidated_data(self, project_path: str, scenario_name: str, data: Dict) -> Dict:
        """Save consolidated results to Excel"""
        try:
            scenario_dir = os.path.join(project_path, 'results', 'demand_forecasts', scenario_name)
            excel_path = os.path.join(scenario_dir, 'forecast_results.xlsx')

            df = pd.DataFrame(data)

            # Append to existing Excel or create new
            with pd.ExcelWriter(excel_path, mode='a' if os.path.exists(excel_path) else 'w') as writer:
                df.to_excel(writer, sheet_name='Consolidated', index=False)

            return {'success': True}

        except Exception as e:
            logger.error(f"Error saving consolidated data: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== PyPSA NETWORK METHODS ====================

    def get_pypsa_networks(self, project_path: str, scenario_name: str) -> Dict:
        """List all .nc network files in PyPSA scenario folder"""
        try:
            pypsa_dir = os.path.join(project_path, 'results', 'pypsa_optimization', scenario_name)

            if not os.path.exists(pypsa_dir):
                return {'networks': []}

            networks = [f for f in os.listdir(pypsa_dir) if f.endswith('.nc')]

            return {'networks': networks}

        except Exception as e:
            logger.error(f"Error getting PyPSA networks: {e}")
            return {'networks': []}

    def get_network_info(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Load PyPSA network and extract metadata"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            if not os.path.exists(network_path):
                return {'success': False, 'error': 'Network file not found'}

            # Load network
            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            # Extract metadata
            info = {
                'success': True,
                'buses': len(network.buses),
                'generators': len(network.generators),
                'lines': len(network.lines),
                'loads': len(network.loads),
                'storage_units': len(network.storage_units),
                'snapshots': len(network.snapshots),
                'multi_period': False
            }

            # Check for multi-period
            if hasattr(network, 'investment_periods'):
                info['multi_period'] = len(network.investment_periods) > 0
                if info['multi_period']:
                    info['investment_periods'] = network.investment_periods.tolist()

            return info

        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {'success': False, 'error': str(e)}

    def get_pypsa_buses(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all buses from PyPSA network"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            return {
                'success': True,
                'buses': network.buses.reset_index().to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error getting buses: {e}")
            return {'success': False, 'error': str(e)}

    def get_pypsa_generators(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all generators from PyPSA network"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            return {
                'success': True,
                'generators': network.generators.reset_index().to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error getting generators: {e}")
            return {'success': False, 'error': str(e)}

    def get_pypsa_storage_units(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all storage units from PyPSA network"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            return {
                'success': True,
                'storage_units': network.storage_units.reset_index().to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error getting storage units: {e}")
            return {'success': False, 'error': str(e)}

    def get_pypsa_lines(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all transmission lines from PyPSA network"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            return {
                'success': True,
                'lines': network.lines.reset_index().to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error getting lines: {e}")
            return {'success': False, 'error': str(e)}

    def get_pypsa_loads(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all loads from PyPSA network"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            return {
                'success': True,
                'loads': network.loads.reset_index().to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error getting loads: {e}")
            return {'success': False, 'error': str(e)}

    def get_comprehensive_analysis(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get comprehensive network analysis including dispatch, capacity, etc."""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            analysis = {
                'success': True,
                'network_name': network_file,
                'snapshots': len(network.snapshots),
                'components': {
                    'buses': len(network.buses),
                    'generators': len(network.generators),
                    'storage_units': len(network.storage_units),
                    'lines': len(network.lines),
                    'loads': len(network.loads)
                }
            }

            # Get generator dispatch (time series)
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                dispatch = network.generators_t.p
                analysis['dispatch'] = {
                    'timestamps': dispatch.index.tolist(),
                    'data': dispatch.to_dict()
                }

            # Get load time series
            if hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p'):
                loads = network.loads_t.p
                analysis['loads_t'] = {
                    'timestamps': loads.index.tolist(),
                    'data': loads.to_dict()
                }

            # Get storage state of charge
            if hasattr(network, 'storage_units_t') and hasattr(network.storage_units_t, 'state_of_charge'):
                soc = network.storage_units_t.state_of_charge
                analysis['storage_soc'] = {
                    'timestamps': soc.index.tolist(),
                    'data': soc.to_dict()
                }

            return analysis

        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'success': False, 'error': str(e)}

    def get_available_years(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get available years for multi-period networks"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            years = []
            if hasattr(network, 'investment_periods') and len(network.investment_periods) > 0:
                years = network.investment_periods.tolist()
            else:
                # Single period - extract year from snapshots
                if len(network.snapshots) > 0:
                    years = [network.snapshots[0].year]

            return {'years': years}

        except Exception as e:
            logger.error(f"Error getting available years: {e}")
            return {'years': []}

    def get_plot_availability(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Detect which plot types are available based on network data"""
        try:
            import pypsa

            network_path = os.path.join(project_path, 'results', 'pypsa_optimization',
                                       scenario_name, network_file)

            network = pypsa.Network()
            network.import_from_netcdf(network_path)

            availability = {
                'dispatch': hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'),
                'capacity': len(network.generators) > 0,
                'storage': len(network.storage_units) > 0,
                'lines': len(network.lines) > 0,
                'loads': len(network.loads) > 0,
                'multi_period': hasattr(network, 'investment_periods') and len(network.investment_periods) > 0
            }

            return availability

        except Exception as e:
            logger.error(f"Error checking plot availability: {e}")
            return {}

    # ==================== LOAD PROFILE ANALYSIS METHODS ====================

    def get_analysis_data(self, project_path: str, profile_name: str) -> Dict:
        """Get monthly/seasonal analysis data for load profile"""
        try:
            profile_dir = os.path.join(project_path, 'results', 'load_profiles', profile_name)

            # Check for pre-computed statistics
            stats_file = os.path.join(profile_dir, 'statistics.json')
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    return json.load(f)

            # If not found, calculate from CSV
            csv_file = os.path.join(profile_dir, 'hourly_profile.csv')
            if not os.path.exists(csv_file):
                return {'success': False, 'error': 'Profile CSV not found'}

            df = pd.read_csv(csv_file, parse_dates=['Timestamp'] if 'Timestamp' in pd.read_csv(csv_file, nrows=1).columns else None)

            # Calculate monthly statistics
            if 'Timestamp' in df.columns:
                df['Month'] = pd.to_datetime(df['Timestamp']).dt.month
                monthly = df.groupby('Month')['Load_MW'].agg(['mean', 'max', 'min', 'sum']).to_dict('index')
            else:
                monthly = {}

            return {
                'success': True,
                'monthly': monthly,
                'overall': {
                    'peak': df['Load_MW'].max(),
                    'average': df['Load_MW'].mean(),
                    'min': df['Load_MW'].min()
                }
            }

        except Exception as e:
            logger.error(f"Error getting analysis data: {e}")
            return {'success': False, 'error': str(e)}

    def get_profile_years(self, project_path: str, profile_name: str) -> Dict:
        """Get fiscal years available in load profile"""
        try:
            csv_file = os.path.join(project_path, 'results', 'load_profiles', profile_name, 'hourly_profile.csv')

            if not os.path.exists(csv_file):
                return {'years': []}

            df = pd.read_csv(csv_file)

            years = []
            if 'FiscalYear' in df.columns:
                years = sorted(df['FiscalYear'].unique().tolist())
            elif 'Timestamp' in df.columns:
                df['Year'] = pd.to_datetime(df['Timestamp']).dt.year
                years = sorted(df['Year'].unique().tolist())

            return {'years': years}

        except Exception as e:
            logger.error(f"Error getting profile years: {e}")
            return {'years': []}

    def get_load_duration_curve(self, project_path: str, profile_name: str, fiscal_year: str) -> Dict:
        """Get load duration curve data (sorted loads)"""
        try:
            csv_file = os.path.join(project_path, 'results', 'load_profiles', profile_name, 'hourly_profile.csv')

            df = pd.read_csv(csv_file)

            # Filter by fiscal year if specified
            if fiscal_year and 'FiscalYear' in df.columns:
                df = df[df['FiscalYear'] == fiscal_year]

            # Sort loads in descending order
            loads_sorted = df['Load_MW'].sort_values(ascending=False).reset_index(drop=True)

            # Calculate cumulative percentage
            hours = list(range(len(loads_sorted)))
            percentages = [(h / len(loads_sorted)) * 100 for h in hours]

            return {
                'success': True,
                'hours': hours,
                'loads': loads_sorted.tolist(),
                'percentages': percentages
            }

        except Exception as e:
            logger.error(f"Error getting load duration curve: {e}")
            return {'success': False, 'error': str(e)}

    def get_full_load_profile(self, project_path: str, profile_name: str,
                              fiscal_year: Optional[str] = None,
                              month: Optional[str] = None,
                              season: Optional[str] = None) -> Dict:
        """Get full hourly load profile data with optional filters"""
        try:
            csv_file = os.path.join(project_path, 'results', 'load_profiles', profile_name, 'hourly_profile.csv')

            df = pd.read_csv(csv_file, parse_dates=['Timestamp'] if 'Timestamp' in pd.read_csv(csv_file, nrows=1).columns else None)

            # Apply filters
            if fiscal_year and 'FiscalYear' in df.columns:
                df = df[df['FiscalYear'] == fiscal_year]

            if month and 'Timestamp' in df.columns:
                df['Month'] = pd.to_datetime(df['Timestamp']).dt.month
                df = df[df['Month'] == int(month)]

            if season and 'Season' in df.columns:
                df = df[df['Season'] == season]

            return {
                'success': True,
                'data': df.to_dict('records')
            }

        except Exception as e:
            logger.error(f"Error getting full load profile: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== ADDITIONAL HELPER METHODS ====================

    def get_available_base_years(self, project_path: str) -> Dict:
        """Get available base years from load curve template"""
        try:
            inputs_dir = os.path.join(project_path, 'inputs')
            load_curve_file = os.path.join(inputs_dir, 'load_curve.xlsx')

            if not os.path.exists(load_curve_file):
                return {'years': []}

            # Read sheet names (each sheet = year)
            xls = pd.ExcelFile(load_curve_file)
            years = [sheet for sheet in xls.sheet_names if sheet.isdigit()]

            return {'years': sorted(years)}

        except Exception as e:
            logger.error(f"Error getting base years: {e}")
            return {'years': []}

    def get_available_scenarios_for_profiles(self, project_path: str) -> Dict:
        """Get completed forecast scenarios for profile generation"""
        try:
            scenarios_dir = os.path.join(project_path, 'results', 'demand_forecasts')

            if not os.path.exists(scenarios_dir):
                return {'scenarios': []}

            # List scenarios with valid results
            scenarios = []
            for scenario in os.listdir(scenarios_dir):
                scenario_path = os.path.join(scenarios_dir, scenario)
                if os.path.isdir(scenario_path):
                    results_file = os.path.join(scenario_path, 'forecast_results.xlsx')
                    if os.path.exists(results_file):
                        scenarios.append(scenario)

            return {'scenarios': sorted(scenarios)}

        except Exception as e:
            logger.error(f"Error getting scenarios for profiles: {e}")
            return {'scenarios': []}

    def check_profile_exists(self, project_path: str, profile_name: str) -> Dict:
        """Check if a load profile already exists"""
        try:
            profile_path = os.path.join(project_path, 'results', 'load_profiles', profile_name)
            exists = os.path.exists(profile_path) and os.path.isdir(profile_path)

            return {'exists': exists}

        except Exception as e:
            logger.error(f"Error checking profile exists: {e}")
            return {'exists': False}

    def save_model_config(self, project_path: str, config: Dict) -> Dict:
        """Save PyPSA model configuration"""
        try:
            config_dir = os.path.join(project_path, 'results', 'pypsa_optimization')
            os.makedirs(config_dir, exist_ok=True)

            config_file = os.path.join(config_dir, 'model_config.json')

            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            return {'success': True}

        except Exception as e:
            logger.error(f"Error saving model config: {e}")
            return {'success': False, 'error': str(e)}


# Global service instance
service = LocalService()
