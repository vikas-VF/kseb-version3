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


# Global service instance
service = LocalService()
