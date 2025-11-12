"""
API Client for FastAPI Backend Communication
Handles all HTTP requests to the backend_fastapi server
"""

import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with FastAPI backend"""

    def __init__(self, base_url: str = 'http://localhost:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"Response: {response.text}")
            raise
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            logger.error(f"Response: {response.text}")
            raise

    # ==================== PROJECT MANAGEMENT ====================

    def create_project(self, name: str, location: str, description: str = '') -> Dict:
        """Create new project"""
        response = self.session.post(
            f'{self.base_url}/project/create',
            json={
                'name': name,
                'location': location,
                'description': description
            }
        )
        return self._handle_response(response)

    def load_project(self, project_path: str) -> Dict:
        """Load existing project"""
        response = self.session.post(
            f'{self.base_url}/project/load',
            json={'projectPath': project_path}
        )
        return self._handle_response(response)

    def check_directory(self, path: str) -> Dict:
        """Validate directory path"""
        response = self.session.get(
            f'{self.base_url}/project/check-directory',
            params={'path': path}
        )
        return self._handle_response(response)

    # ==================== SECTORS ====================

    def get_sectors(self, project_path: str) -> Dict:
        """Get consumption sectors from project"""
        response = self.session.get(
            f'{self.base_url}/project/sectors',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    # ==================== EXCEL PARSING ====================

    def extract_sector_data(self, project_path: str, sector: str) -> Dict:
        """Extract sector data with economic indicators"""
        response = self.session.post(
            f'{self.base_url}/project/extract-sector-data',
            json={
                'projectPath': project_path,
                'sector': sector
            }
        )
        return self._handle_response(response)

    # ==================== CONSOLIDATED VIEW ====================

    def get_consolidated_electricity(self, project_path: str, sectors: Optional[List[str]] = None) -> Dict:
        """Get consolidated electricity data"""
        response = self.session.post(
            f'{self.base_url}/project/consolidated-electricity',
            json={
                'projectPath': project_path,
                'sectors': sectors
            }
        )
        return self._handle_response(response)

    # ==================== CORRELATION ====================

    def get_correlation_matrix(self, project_path: str, sector: str) -> Dict:
        """Calculate correlation matrix"""
        response = self.session.post(
            f'{self.base_url}/project/correlation-matrix',
            json={
                'projectPath': project_path,
                'sector': sector
            }
        )
        return self._handle_response(response)

    def get_correlation(self, project_path: str, sector: str) -> Dict:
        """Get correlation with electricity"""
        response = self.session.post(
            f'{self.base_url}/project/correlation',
            json={
                'projectPath': project_path,
                'sector': sector
            }
        )
        return self._handle_response(response)

    # ==================== FORECASTING ====================

    def start_forecast(self, config: Dict) -> Dict:
        """Start demand forecasting process"""
        response = self.session.post(
            f'{self.base_url}/project/forecast',
            json=config
        )
        return self._handle_response(response)

    def get_forecast_progress_url(self) -> str:
        """Get SSE URL for forecast progress"""
        return f'{self.base_url}/project/forecast-progress'

    # ==================== SCENARIOS ====================

    def get_scenarios(self, project_path: str) -> Dict:
        """List all forecast scenarios"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_scenario_meta(self, project_path: str, scenario_name: str) -> Dict:
        """Get scenario metadata"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios/{scenario_name}/meta',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_scenario_sectors(self, project_path: str, scenario_name: str) -> Dict:
        """Get sectors in scenario"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios/{scenario_name}/sectors',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_scenario_models(self, project_path: str, scenario_name: str) -> Dict:
        """Get available models by sector"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios/{scenario_name}/models',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_sector_forecast(self, project_path: str, scenario_name: str, sector_name: str) -> Dict:
        """Get forecast data for specific sector"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios/{scenario_name}/sectors/{sector_name}',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_td_losses(self, project_path: str, scenario_name: str) -> Dict:
        """Get T&D loss configuration"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios/{scenario_name}/td-losses',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def save_td_losses(self, project_path: str, scenario_name: str, losses: Dict) -> Dict:
        """Save T&D loss configuration"""
        response = self.session.post(
            f'{self.base_url}/project/scenarios/{scenario_name}/td-losses',
            json={
                'projectPath': project_path,
                'losses': losses
            }
        )
        return self._handle_response(response)

    def check_consolidated_exists(self, project_path: str, scenario_name: str) -> Dict:
        """Check if consolidated file exists"""
        response = self.session.get(
            f'{self.base_url}/project/scenarios/{scenario_name}/consolidated/exists',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def generate_consolidated(self, project_path: str, scenario_name: str) -> Dict:
        """Generate consolidated results"""
        response = self.session.post(
            f'{self.base_url}/project/scenarios/{scenario_name}/consolidated',
            json={'projectPath': project_path}
        )
        return self._handle_response(response)

    def save_consolidated(self, project_path: str, scenario_name: str, data: Dict) -> Dict:
        """Save consolidated results to Excel"""
        response = self.session.post(
            f'{self.base_url}/project/save-consolidated',
            json={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'data': data
            }
        )
        return self._handle_response(response)

    # ==================== LOAD PROFILES ====================

    def get_available_base_years(self, project_path: str) -> Dict:
        """Get available base years from load curve template"""
        response = self.session.get(
            f'{self.base_url}/project/available-base-years',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_available_scenarios_for_profiles(self, project_path: str) -> Dict:
        """Get completed forecast scenarios for profile generation"""
        response = self.session.get(
            f'{self.base_url}/project/available-scenarios',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def check_profile_exists(self, project_path: str, profile_name: str) -> Dict:
        """Check if profile file exists"""
        response = self.session.get(
            f'{self.base_url}/project/check-profile-exists',
            params={
                'projectPath': project_path,
                'profileName': profile_name
            }
        )
        return self._handle_response(response)

    def generate_profile(self, config: Dict) -> Dict:
        """Start load profile generation"""
        response = self.session.post(
            f'{self.base_url}/project/generate-profile',
            json=config
        )
        return self._handle_response(response)

    def get_generation_status_url(self) -> str:
        """Get SSE URL for profile generation status"""
        return f'{self.base_url}/project/generation-status'

    def get_load_profiles(self, project_path: str) -> Dict:
        """List all load profile files"""
        response = self.session.get(
            f'{self.base_url}/project/load-profiles',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    # ==================== ANALYSIS ====================

    def get_analysis_data(self, project_path: str, profile_name: str) -> Dict:
        """Get monthly/seasonal analysis data"""
        response = self.session.get(
            f'{self.base_url}/project/analysis-data',
            params={
                'projectPath': project_path,
                'profileName': profile_name
            }
        )
        return self._handle_response(response)

    def get_profile_years(self, project_path: str, profile_name: str) -> Dict:
        """Get fiscal years in profile"""
        response = self.session.get(
            f'{self.base_url}/project/profile-years',
            params={
                'projectPath': project_path,
                'profileName': profile_name
            }
        )
        return self._handle_response(response)

    def get_load_duration_curve(self, project_path: str, profile_name: str, fiscal_year: str) -> Dict:
        """Get load duration curve data"""
        response = self.session.get(
            f'{self.base_url}/project/load-duration-curve',
            params={
                'projectPath': project_path,
                'profileName': profile_name,
                'fiscalYear': fiscal_year
            }
        )
        return self._handle_response(response)

    # ==================== TIME SERIES ====================

    def get_full_load_profile(self, project_path: str, profile_name: str,
                             fiscal_year: Optional[str] = None,
                             month: Optional[str] = None,
                             season: Optional[str] = None) -> Dict:
        """Get hourly load data with filters"""
        params = {
            'projectPath': project_path,
            'profileName': profile_name
        }
        if fiscal_year:
            params['fiscalYear'] = fiscal_year
        if month:
            params['month'] = month
        if season:
            params['season'] = season

        response = self.session.get(
            f'{self.base_url}/project/full-load-profile',
            params=params
        )
        return self._handle_response(response)

    # ==================== SETTINGS ====================

    def get_color_settings(self, project_path: str) -> Dict:
        """Get color configuration"""
        response = self.session.get(
            f'{self.base_url}/project/settings/colors',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def save_color_settings(self, project_path: str, colors: Dict) -> Dict:
        """Save color configuration"""
        response = self.session.post(
            f'{self.base_url}/project/settings/save-colors',
            json={
                'projectPath': project_path,
                'colors': colors
            }
        )
        return self._handle_response(response)

    # ==================== PyPSA ANALYSIS ====================

    def get_pypsa_scenarios(self, project_path: str) -> Dict:
        """List all PyPSA scenarios"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/scenarios',
            params={'projectPath': project_path}
        )
        return self._handle_response(response)

    def get_pypsa_networks(self, project_path: str, scenario_name: str) -> Dict:
        """List .nc network files in scenario"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/networks',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name
            }
        )
        return self._handle_response(response)

    def get_network_info(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get network metadata & detection"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/network-info',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_pypsa_buses(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all bus nodes"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/buses',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_pypsa_generators(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get all generators"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/generators',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_pypsa_storage_units(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get storage units"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/storage-units',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_pypsa_lines(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get transmission lines"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/lines',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_pypsa_loads(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get load nodes"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/loads',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_component_details(self, project_path: str, scenario_name: str,
                            network_file: str, component_type: str) -> Dict:
        """Get detailed component analysis"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/component-details',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file,
                'componentType': component_type
            }
        )
        return self._handle_response(response)

    def get_comprehensive_analysis(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get full network analysis"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/comprehensive-analysis',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    # ==================== PyPSA VISUALIZATION ====================

    def generate_pypsa_plot(self, config: Dict) -> Dict:
        """Generate PyPSA plot"""
        response = self.session.post(
            f'{self.base_url}/project/pypsa/plot/generate',
            json=config
        )
        return self._handle_response(response)

    def get_available_years(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Get years for multi-period networks"""
        response = self.session.get(
            f'{self.base_url}/project/pypsa/plot/available-years',
            params={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    def get_plot_availability(self, project_path: str, scenario_name: str, network_file: str) -> Dict:
        """Detect available plot types"""
        response = self.session.post(
            f'{self.base_url}/project/pypsa/plot/availability',
            json={
                'projectPath': project_path,
                'scenarioName': scenario_name,
                'networkFile': network_file
            }
        )
        return self._handle_response(response)

    # ==================== PyPSA MODEL EXECUTION ====================

    def save_model_config(self, project_path: str, config: Dict) -> Dict:
        """Save PyPSA model configuration"""
        response = self.session.post(
            f'{self.base_url}/project/save-model-config',
            json={
                'projectPath': project_path,
                'config': config
            }
        )
        return self._handle_response(response)

    def run_pypsa_model(self, config: Dict) -> Dict:
        """Execute PyPSA model"""
        response = self.session.post(
            f'{self.base_url}/project/run-pypsa-model',
            json=config
        )
        return self._handle_response(response)

    def get_pypsa_progress_url(self) -> str:
        """Get SSE URL for PyPSA model progress"""
        return f'{self.base_url}/project/pypsa-model-progress'

    def stop_pypsa_model(self) -> Dict:
        """Stop running PyPSA model"""
        response = self.session.post(f'{self.base_url}/project/stop-pypsa-model')
        return self._handle_response(response)


# Global API client instance
api = APIClient()
