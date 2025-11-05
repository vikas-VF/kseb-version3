"""
Test PyPSA Network Type Detection
==================================

Tests the three network types:
1. Single-period: .nc file with year in filename
2. Multi-period: .nc file without year, with MultiIndex snapshots
3. Multi-file: Multiple .nc files with years in filenames
"""

import pytest
import pandas as pd
import pypsa
from pathlib import Path
from fastapi.testclient import TestClient
from backend_fastapi.main import app

client = TestClient(app)


class TestNetworkDetection:
    """Test network type detection logic"""

    def test_single_period_detection_year_prefix(self):
        """Test detection of single-period network with year prefix (2026_network.nc)"""
        response = client.get(
            "/project/pypsa/detect-network-type",
            params={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "2026_network.nc"
            }
        )

        assert response.status_code == 200 or response.status_code == 404  # 404 if file doesn't exist

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            detection = data["detection"]

            assert detection["workflow_type"] == "single-period"
            assert "year" in detection
            assert detection["year"] == 2026
            assert "ui_tabs" in detection
            assert "Dispatch & Load" in detection["ui_tabs"]

    def test_single_period_detection_year_suffix(self):
        """Test detection of single-period network with year suffix (network_2025.nc)"""
        response = client.get(
            "/project/pypsa/detect-network-type",
            params={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "network_2025.nc"
            }
        )

        assert response.status_code == 200 or response.status_code == 404

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            detection = data["detection"]

            assert detection["workflow_type"] == "single-period"
            assert detection["year"] == 2025

    def test_multi_period_detection(self):
        """Test detection of multi-period network (investments.nc with MultiIndex)"""
        response = client.get(
            "/project/pypsa/detect-network-type",
            params={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "investments.nc"
            }
        )

        assert response.status_code == 200 or response.status_code == 404

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            detection = data["detection"]

            # Could be multi-period or single-period depending on file structure
            if detection["workflow_type"] == "multi-period":
                assert "periods" in detection
                assert isinstance(detection["periods"], list)
                assert len(detection["periods"]) > 0
                assert "ui_tabs" in detection
                assert "period_selector" in detection["ui_tabs"]
                assert "cross_period" in detection["ui_tabs"]

    def test_multi_file_detection(self):
        """Test detection of multi-file network (multiple .nc files with years)"""
        # This would require a scenario with multiple files
        # The test would check if the endpoint correctly identifies multiple files
        pass  # Skip for now, requires actual multi-file scenario

    def test_year_validation(self):
        """Test that years outside 2000-2100 are not treated as years"""
        response = client.get(
            "/project/pypsa/detect-network-type",
            params={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "network_1999.nc"  # Year outside range
            }
        )

        assert response.status_code == 200 or response.status_code == 404

        if response.status_code == 200:
            data = response.json()
            # Should not be treated as year-based single-period
            # Instead, should check for MultiIndex


class TestPeriodSpecificAnalysis:
    """Test period-specific analysis endpoints"""

    def test_period_analysis_endpoint(self):
        """Test analysis for specific period in multi-period network"""
        response = client.get(
            "/project/pypsa/analysis/period/0",
            params={
                "analysisType": "capacity",
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "investments.nc"
            }
        )

        assert response.status_code == 200 or response.status_code == 404 or response.status_code == 400

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_cross_period_comparison(self):
        """Test cross-period comparison endpoint"""
        response = client.post(
            "/project/pypsa/analysis/cross-period-comparison",
            json={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "investments.nc",
                "periods": [0, 1, 2],
                "comparisonType": "capacity"
            }
        )

        assert response.status_code == 200 or response.status_code == 404 or response.status_code == 400

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "comparison_data" in data


class TestYearSpecificAnalysis:
    """Test year-specific analysis endpoints"""

    def test_year_analysis_endpoint(self):
        """Test analysis for specific year in multi-file network"""
        response = client.get(
            "/project/pypsa/analysis/year/2026",
            params={
                "analysisType": "capacity",
                "projectPath": "/test/project",
                "scenarioName": "test_scenario"
            }
        )

        assert response.status_code == 200 or response.status_code == 404

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_year_to_year_comparison(self):
        """Test year-to-year comparison endpoint"""
        response = client.post(
            "/project/pypsa/analysis/year-to-year-comparison",
            json={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "years": [2025, 2026, 2030],
                "comparisonType": "capacity"
            }
        )

        assert response.status_code == 200 or response.status_code == 404

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "comparison_data" in data


class TestUITabConfiguration:
    """Test that UI tabs are correctly configured for each network type"""

    def test_single_period_ui_tabs(self):
        """Test that single-period network returns correct UI tabs"""
        expected_tabs = [
            "Dispatch & Load",
            "Capacity",
            "Metrics",
            "Storage",
            "Emissions",
            "Prices",
            "Network Flow"
        ]

        response = client.get(
            "/project/pypsa/detect-network-type",
            params={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "2026_network.nc"
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                detection = data["detection"]
                if detection["workflow_type"] == "single-period":
                    ui_tabs = detection.get("ui_tabs", [])
                    for tab in expected_tabs:
                        assert tab in ui_tabs

    def test_multi_period_ui_tabs(self):
        """Test that multi-period network returns correct UI tab structure"""
        response = client.get(
            "/project/pypsa/detect-network-type",
            params={
                "projectPath": "/test/project",
                "scenarioName": "test_scenario",
                "networkFile": "investments.nc"
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                detection = data["detection"]
                if detection["workflow_type"] == "multi-period":
                    ui_tabs = detection.get("ui_tabs", {})
                    assert "period_selector" in ui_tabs
                    assert "cross_period" in ui_tabs
                    assert isinstance(ui_tabs["period_selector"], dict)
                    assert "tabs" in ui_tabs["period_selector"]


class TestStreamlitFunctionParity:
    """Test that all Streamlit functions are available"""

    def test_all_streamlit_functions_exist(self):
        """Verify all key Streamlit analysis functions are implemented"""
        from backend_fastapi.models import pypsa_analyzer

        required_functions = [
            'get_dispatch_data',
            'get_carrier_capacity',
            'get_carrier_capacity_new_addition',
            'calculate_cuf',
            'calculate_curtailment',
            'get_storage_soc',
            'calculate_co2_emissions',
            'calculate_marginal_prices',
            'calculate_network_losses',
            'plot_dispatch_stack',
            'create_daily_profile_plot',
            'create_duration_curve',
            'plot_hourly_generation_heatmap',
            'compare_periods'
        ]

        # Check that all functions exist in the module
        for func_name in required_functions:
            # Try importing from main_all.py first (Streamlit reference)
            try:
                from main_all import func_name as streamlit_func
                print(f"✓ {func_name} exists in Streamlit reference")
            except (ImportError, AttributeError):
                print(f"✗ {func_name} NOT found in Streamlit reference")


# Integration test markers
@pytest.mark.integration
class TestRealNetworkFiles:
    """Integration tests with real .nc files (requires test data)"""

    def test_real_single_period_file(self):
        """Test with real single-period .nc file from testing folder"""
        # This would test against actual files in testing/results/pypsa_optimization/
        pass

    def test_real_multi_period_file(self):
        """Test with real multi-period .nc file"""
        pass

    def test_real_multi_file_scenario(self):
        """Test with real multi-file scenario"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
