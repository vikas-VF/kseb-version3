"""
State Management Utilities
Helpers for managing complex state in Dash with dcc.Store
"""

from typing import Dict, Any, List, Optional
import json


class StateManager:
    """Helper class for managing application state"""

    @staticmethod
    def create_project_state(name: str, path: str, description: str = '') -> Dict[str, Any]:
        """Create project state object"""
        from datetime import datetime
        return {
            'name': name,
            'path': path,
            'description': description,
            'lastOpened': datetime.now().isoformat(),
            'id': path.replace('/', '_').replace('\\', '_').replace(':', '_')
        }

    @staticmethod
    def create_demand_state() -> Dict[str, Any]:
        """Create demand projection state"""
        return {
            'isConsolidated': True,
            'consolidated': {
                'activeTab': 'Data Table',
                'areaChartHiddenSectors': [],
                'stackedBarChartHiddenSectors': [],
                'areaChartZoom': None,
                'stackedBarChartZoom': None,
            },
            'sector': {
                'activeTab': 'Data Table',
                'activeSectorIndex': 0,
                'lineChartHiddenSeries': [],
                'lineChartZoom': None,
            },
            'selectedUnit': 'mwh'
        }

    @staticmethod
    def create_profile_state() -> Dict[str, Any]:
        """Create load profile analysis state"""
        return {
            'selectedProfile': None,
            'selectedYear': None,
            'activeTab': 'Overview',
            'monthlyHeatmapZoom': None,
            'seasonalHeatmapZoom': None,
            'timeSeriesZoom': None
        }

    @staticmethod
    def create_pypsa_state() -> Dict[str, Any]:
        """Create PyPSA analysis state"""
        return {
            'selectedScenario': None,
            'selectedNetwork': None,
            'activeTab': 'Overview',
            'selectedPeriod': None,
            'selectedComponent': None
        }

    @staticmethod
    def update_recent_projects(recent_projects: Optional[List[Dict]],
                              new_project: Dict,
                              max_items: int = 10) -> List[Dict]:
        """
        Update recent projects list
        - Removes duplicates (by path)
        - Adds new project to front
        - Limits to max_items
        """
        recent = recent_projects or []

        # Remove if already exists
        recent = [p for p in recent if p.get('path') != new_project.get('path')]

        # Add to front
        recent = [new_project] + recent

        # Limit to max_items
        recent = recent[:max_items]

        return recent

    @staticmethod
    def toggle_hidden_series(hidden_list: Optional[List[str]], series_name: str) -> List[str]:
        """
        Toggle series visibility in chart
        Add if not present, remove if present
        """
        hidden = hidden_list or []

        if series_name in hidden:
            return [s for s in hidden if s != series_name]
        else:
            return hidden + [series_name]

    @staticmethod
    def update_zoom_state(zoom_data: Optional[Dict], axis_range: Dict) -> Dict:
        """Update chart zoom state"""
        return {
            'xaxis': axis_range.get('xaxis', {}).get('range'),
            'yaxis': axis_range.get('yaxis', {}).get('range')
        }

    @staticmethod
    def merge_state(current_state: Optional[Dict], updates: Dict) -> Dict:
        """Deep merge state updates"""
        if current_state is None:
            return updates

        result = current_state.copy()

        for key, value in updates.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = StateManager.merge_state(result[key], value)
            else:
                result[key] = value

        return result


class ProcessState:
    """Helper for managing process states (forecasting, profile generation, PyPSA)"""

    @staticmethod
    def create_process_state(process_id: str = None) -> Dict[str, Any]:
        """Create initial process state"""
        from datetime import datetime
        import uuid

        return {
            'id': process_id or str(uuid.uuid4()),
            'status': 'idle',  # idle, running, completed, failed, cancelled
            'progress': 0,
            'taskProgress': {'current': 0, 'total': 0},
            'logs': [],
            'startTime': None,
            'endTime': None,
            'error': None
        }

    @staticmethod
    def update_progress(state: Dict, progress: int, message: str = None) -> Dict:
        """Update process progress"""
        updated = state.copy()
        updated['progress'] = min(100, max(0, progress))

        if message:
            updated['logs'].append({
                'timestamp': ProcessState._get_timestamp(),
                'message': message
            })

        return updated

    @staticmethod
    def update_task_progress(state: Dict, current: int, total: int) -> Dict:
        """Update task progress (e.g., 5/10 years)"""
        updated = state.copy()
        updated['taskProgress'] = {
            'current': current,
            'total': total
        }
        return updated

    @staticmethod
    def add_log(state: Dict, message: str, level: str = 'info') -> Dict:
        """Add log message"""
        updated = state.copy()
        updated['logs'].append({
            'timestamp': ProcessState._get_timestamp(),
            'message': message,
            'level': level
        })
        # Keep only last 100 logs
        if len(updated['logs']) > 100:
            updated['logs'] = updated['logs'][-100:]
        return updated

    @staticmethod
    def set_status(state: Dict, status: str, error: str = None) -> Dict:
        """Set process status"""
        from datetime import datetime

        updated = state.copy()
        updated['status'] = status

        if status == 'running' and not updated.get('startTime'):
            updated['startTime'] = datetime.now().isoformat()

        if status in ['completed', 'failed', 'cancelled']:
            updated['endTime'] = datetime.now().isoformat()
            if status == 'failed' and error:
                updated['error'] = error

        return updated

    @staticmethod
    def _get_timestamp():
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


class ConversionFactors:
    """Unit conversion factors for energy"""

    FACTORS = {
        'mwh': 1,
        'kwh': 1000,
        'gwh': 0.001,
        'twh': 0.000001
    }

    LABELS = {
        'mwh': 'MWh',
        'kwh': 'kWh',
        'gwh': 'GWh',
        'twh': 'TWh'
    }

    @staticmethod
    def convert(value: float, from_unit: str, to_unit: str) -> float:
        """Convert energy value between units"""
        from_factor = ConversionFactors.FACTORS.get(from_unit.lower(), 1)
        to_factor = ConversionFactors.FACTORS.get(to_unit.lower(), 1)

        # Convert to MWh first, then to target unit
        mwh_value = value / from_factor
        return mwh_value * to_factor

    @staticmethod
    def get_label(unit: str) -> str:
        """Get display label for unit"""
        return ConversionFactors.LABELS.get(unit.lower(), unit.upper())


def format_date(iso_string: Optional[str], format_type: str = 'full') -> str:
    """
    Format ISO date string for display

    Args:
        iso_string: ISO format datetime string
        format_type: 'full', 'date', 'time', 'relative'
    """
    if not iso_string:
        return 'N/A'

    from datetime import datetime

    try:
        dt = datetime.fromisoformat(iso_string)

        if format_type == 'full':
            return dt.strftime('%B %d, %Y at %I:%M %p')
        elif format_type == 'date':
            return dt.strftime('%B %d, %Y')
        elif format_type == 'time':
            return dt.strftime('%I:%M %p')
        elif format_type == 'relative':
            from datetime import datetime
            now = datetime.now()
            diff = now - dt

            if diff.days == 0:
                if diff.seconds < 60:
                    return 'Just now'
                elif diff.seconds < 3600:
                    return f'{diff.seconds // 60} minutes ago'
                else:
                    return f'{diff.seconds // 3600} hours ago'
            elif diff.days == 1:
                return 'Yesterday'
            elif diff.days < 7:
                return f'{diff.days} days ago'
            elif diff.days < 30:
                return f'{diff.days // 7} weeks ago'
            elif diff.days < 365:
                return f'{diff.days // 30} months ago'
            else:
                return f'{diff.days // 365} years ago'
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    except Exception:
        return iso_string


def safe_json_loads(json_string: Optional[str], default: Any = None) -> Any:
    """Safely parse JSON string"""
    if not json_string:
        return default

    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = '{}') -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return default


def safe_numeric(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float, handling strings, None, and other types.

    Args:
        value: Value to convert (can be str, int, float, None, etc.)
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if value is None or value == '' or value == 'N/A':
        return default

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            # Remove commas and spaces
            cleaned = value.replace(',', '').replace(' ', '').strip()
            if cleaned == '' or cleaned == 'N/A':
                return default
            return float(cleaned)
        except (ValueError, AttributeError):
            return default

    return default


def safe_multiply(value: Any, factor: float, default: float = 0.0) -> float:
    """
    Safely multiply a value by a factor, handling non-numeric values.

    Args:
        value: Value to multiply
        factor: Multiplication factor
        default: Default value if conversion fails

    Returns:
        Result of multiplication or default
    """
    numeric_value = safe_numeric(value, default)
    return numeric_value * factor
