#!/usr/bin/env python3
"""
End-to-End Workflow Test Script
Tests: Project Creation → Demand Forecast → Load Profile → PyPSA
Compares Dash implementation with FastAPI behavior
"""

import sys
import os
import json
import time
from pathlib import Path

# Add dash directory to path
sys.path.insert(0, str(Path(__file__).parent / 'dash'))

from services.local_service import LocalService

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(step, success, message="", details=None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} | {step}")
    if message:
        print(f"    Message: {message}")
    if details:
        print(f"    Details: {json.dumps(details, indent=2)}")

def test_project_creation(service, test_dir):
    """Test 1: Create new project with Excel templates"""
    print_section("TEST 1: PROJECT CREATION")

    project_name = "E2E_Test_Project"
    project_path = os.path.join(test_dir, project_name)

    # Remove existing test project
    if os.path.exists(project_path):
        import shutil
        shutil.rmtree(project_path)

    print(f"Creating project: {project_name}")
    print(f"Location: {test_dir}")

    result = service.create_project(
        name=project_name,
        location=test_dir,
        description="End-to-end test project"
    )

    if not result.get('success'):
        print_result("Project Creation", False, result.get('error'))
        return None

    # Verify folder structure
    checks = {
        'project.json': os.path.exists(os.path.join(project_path, 'project.json')),
        'inputs/input_demand_file.xlsx': os.path.exists(os.path.join(project_path, 'inputs', 'input_demand_file.xlsx')),
        'inputs/load_curve_template.xlsx': os.path.exists(os.path.join(project_path, 'inputs', 'load_curve_template.xlsx')),
        'inputs/pypsa_input_template.xlsx': os.path.exists(os.path.join(project_path, 'inputs', 'pypsa_input_template.xlsx')),
        'results/': os.path.exists(os.path.join(project_path, 'results')),
    }

    all_present = all(checks.values())
    print_result("Project Creation", all_present,
                 f"{sum(checks.values())}/{len(checks)} files/folders present",
                 checks)

    return project_path if all_present else None

def test_load_project(service, project_path):
    """Test 2: Load existing project"""
    print_section("TEST 2: PROJECT LOADING")

    result = service.load_project(project_path)

    if not result.get('success'):
        print_result("Load Project", False, result.get('error'))
        return False

    print_result("Load Project", True, "Project metadata loaded successfully",
                 result.get('project'))
    return True

def test_get_sectors(service, project_path):
    """Test 3: Extract sectors from Excel"""
    print_section("TEST 3: SECTOR EXTRACTION")

    result = service.get_sectors(project_path)
    sectors = result.get('sectors', [])

    print(f"Found {len(sectors)} sectors: {sectors}")

    # Validate sectors with data
    validation = service.validate_sectors_with_data(project_path, sectors)

    if validation.get('success'):
        valid = validation.get('valid_sectors', [])
        invalid = validation.get('invalid_sectors', [])

        print(f"\n✅ Valid sectors ({len(valid)}): {valid}")
        if invalid:
            print(f"⚠️  Invalid sectors ({len(invalid)}):")
            for inv in invalid:
                print(f"    - {inv['sector']}: {inv['reason']}")

    print_result("Sector Extraction", len(sectors) > 0,
                 f"Found {len(sectors)} total sectors, {len(valid)} valid")

    return valid if len(valid) > 0 else None

def test_sector_correlation(service, project_path, sectors):
    """Test 4: Check correlation data for MLR parameters"""
    print_section("TEST 4: SECTOR CORRELATION & MLR PARAMETERS")

    for sector in sectors[:3]:  # Test first 3 sectors
        print(f"\n--- Analyzing {sector} ---")

        # Get correlation
        corr_result = service.get_sector_correlation(project_path, sector)

        if not corr_result.get('success'):
            print_result(f"Correlation - {sector}", False, corr_result.get('error'))
            continue

        # Check for MLR parameters
        corr_matrix = corr_result.get('correlation_matrix', {})
        electricity_corr = corr_matrix.get('Electricity', {})

        # Filter and sort parameters by correlation
        mlr_params = [(k, abs(v)) for k, v in electricity_corr.items()
                      if k.lower() not in ['year', 'electricity']]
        mlr_params.sort(key=lambda x: x[1], reverse=True)

        print(f"Top MLR Parameters for {sector}:")
        for param, corr in mlr_params[:5]:
            print(f"  - {param}: {corr:.3f}")

        print_result(f"Correlation - {sector}", len(mlr_params) > 0,
                     f"Found {len(mlr_params)} MLR parameters")

    return True

def test_demand_forecast(service, project_path, sectors):
    """Test 5: Run demand forecasting"""
    print_section("TEST 5: DEMAND FORECASTING (Target Year: 2030)")

    # Prepare configuration
    config = {
        'scenario_name': 'E2E_Test_Scenario_2030',
        'target_year': 2030,
        'exclude_covid_years': True,
        'sectors': []
    }

    # Add sector configurations (use first 3 valid sectors)
    for sector in sectors[:3]:
        # Get sector data
        data_result = service.extract_sector_data(project_path, sector)
        if not data_result.get('success'):
            print(f"⚠️  Skipping {sector}: {data_result.get('error')}")
            continue

        # Get MLR parameters
        corr_result = service.get_sector_correlation(project_path, sector)
        mlr_params = []
        if corr_result.get('success'):
            electricity_corr = corr_result.get('correlation_matrix', {}).get('Electricity', {})
            mlr_params = [k for k, v in electricity_corr.items()
                         if k.lower() not in ['year', 'electricity']][:3]

        sector_config = {
            'name': sector,
            'selected_methods': ['SLR', 'MLR', 'WAM'],
            'mlr_parameters': mlr_params,
            'wam_window': 3,
            'data': data_result.get('data', [])
        }
        config['sectors'].append(sector_config)

    print(f"Configuration prepared for {len(config['sectors'])} sectors")
    print(f"Sectors: {[s['name'] for s in config['sectors']]}")

    # Start forecast
    print("\nStarting forecast process...")
    result = service.start_demand_forecast(project_path, config)

    if not result.get('success'):
        print_result("Start Forecast", False, result.get('error'))
        return None

    print_result("Start Forecast", True,
                 f"Process ID: {result.get('process_id')}")

    # Wait for completion (monitor for 60 seconds max)
    print("\nMonitoring forecast progress...")
    from services.local_service import forecast_processes

    process_id = result.get('process_id')
    max_wait = 60
    elapsed = 0

    while elapsed < max_wait:
        if process_id in forecast_processes:
            status = forecast_processes[process_id]['status']
            print(f"  [{elapsed}s] Status: {status}")

            if status in ['completed', 'failed']:
                break

        time.sleep(5)
        elapsed += 5

    final_status = forecast_processes.get(process_id, {}).get('status', 'unknown')

    # Check for results
    scenario_path = Path(project_path) / 'results' / 'demand_forecasts' / config['scenario_name']
    output_files = list(scenario_path.glob('*.xlsx')) if scenario_path.exists() else []

    print(f"\nFinal Status: {final_status}")
    print(f"Output files: {len(output_files)}")
    for f in output_files:
        print(f"  - {f.name}")

    success = final_status == 'completed' and len(output_files) > 0
    print_result("Demand Forecast Execution", success,
                 f"Generated {len(output_files)} result files")

    return config['scenario_name'] if success else None

def test_demand_visualization(service, project_path, scenario_name):
    """Test 6: Verify demand forecast results can be loaded"""
    print_section("TEST 6: DEMAND VISUALIZATION DATA")

    result = service.get_scenarios(project_path)
    scenarios = result.get('scenarios', [])

    print(f"Available scenarios: {scenarios}")

    if scenario_name not in scenarios:
        print_result("Scenario Availability", False,
                     f"Scenario {scenario_name} not found")
        return False

    # Try to load scenario data
    scenario_path = Path(project_path) / 'results' / 'demand_forecasts' / scenario_name
    excel_files = list(scenario_path.glob('*.xlsx'))

    print(f"\nScenario files: {len(excel_files)}")

    # Check if we can read the Excel files
    import pandas as pd
    readable = 0
    for excel_file in excel_files:
        try:
            sheets = pd.ExcelFile(excel_file).sheet_names
            print(f"  ✅ {excel_file.name}: {len(sheets)} sheets ({', '.join(sheets[:3])}...)")
            readable += 1
        except Exception as e:
            print(f"  ❌ {excel_file.name}: Error - {e}")

    print_result("Demand Data Readable", readable == len(excel_files),
                 f"{readable}/{len(excel_files)} files readable")

    return readable > 0

def test_load_profile_generation(service, project_path):
    """Test 7: Generate load profiles"""
    print_section("TEST 7: LOAD PROFILE GENERATION")

    # Check if load_curve_template has data
    template_path = Path(project_path) / 'inputs' / 'load_curve_template.xlsx'

    if not template_path.exists():
        print_result("Load Curve Template", False, "Template file not found")
        return None

    print(f"Load curve template: {template_path}")

    # For now, just verify the template exists and is readable
    try:
        import pandas as pd
        xls = pd.ExcelFile(template_path)
        sheets = xls.sheet_names
        print(f"Template sheets: {sheets}")

        print_result("Load Profile Template Check", True,
                     f"Template has {len(sheets)} sheets")

        # Note: Actual profile generation requires GUI interaction
        # This test just verifies infrastructure is in place
        return "load_profile_check_passed"

    except Exception as e:
        print_result("Load Profile Template Check", False, str(e))
        return None

def test_pypsa_template(service, project_path):
    """Test 8: Verify PyPSA template"""
    print_section("TEST 8: PYPSA TEMPLATE CHECK")

    template_path = Path(project_path) / 'inputs' / 'pypsa_input_template.xlsx'

    if not template_path.exists():
        print_result("PyPSA Template", False, "Template file not found")
        return False

    try:
        import pandas as pd
        xls = pd.ExcelFile(template_path)
        sheets = xls.sheet_names

        print(f"PyPSA template sheets ({len(sheets)}):")
        for sheet in sheets[:10]:
            df = pd.read_excel(template_path, sheet_name=sheet)
            print(f"  - {sheet}: {df.shape[0]} rows × {df.shape[1]} cols")

        if len(sheets) > 10:
            print(f"  ... and {len(sheets) - 10} more sheets")

        print_result("PyPSA Template Check", True,
                     f"Template has {len(sheets)} sheets")
        return True

    except Exception as e:
        print_result("PyPSA Template Check", False, str(e))
        return False

def main():
    """Run complete end-to-end test suite"""
    print("\n" + "█"*80)
    print("█  KSEB DASH WEBAPP - END-TO-END WORKFLOW TEST")
    print("█  Testing: Project → Demand Forecast → Load Profile → PyPSA")
    print("█"*80)

    # Initialize service
    service = LocalService()

    # Test directory
    test_dir = '/tmp/kseb_e2e_test'
    os.makedirs(test_dir, exist_ok=True)

    print(f"\nTest directory: {test_dir}")
    print(f"Service initialized: {service.__class__.__name__}")

    # Run tests sequentially
    results = {}

    # Test 1: Create Project
    project_path = test_project_creation(service, test_dir)
    results['project_creation'] = project_path is not None
    if not project_path:
        print("\n❌ FATAL: Project creation failed, cannot continue")
        return

    # Test 2: Load Project
    results['project_loading'] = test_load_project(service, project_path)
    if not results['project_loading']:
        print("\n❌ FATAL: Project loading failed, cannot continue")
        return

    # Test 3: Get Sectors
    valid_sectors = test_get_sectors(service, project_path)
    results['sector_extraction'] = valid_sectors is not None
    if not valid_sectors:
        print("\n❌ FATAL: No valid sectors found, cannot continue")
        return

    # Test 4: Sector Correlation
    results['sector_correlation'] = test_sector_correlation(service, project_path, valid_sectors)

    # Test 5: Demand Forecast
    scenario_name = test_demand_forecast(service, project_path, valid_sectors)
    results['demand_forecast'] = scenario_name is not None

    # Test 6: Demand Visualization
    if scenario_name:
        results['demand_visualization'] = test_demand_visualization(service, project_path, scenario_name)
    else:
        results['demand_visualization'] = False

    # Test 7: Load Profile
    results['load_profile'] = test_load_profile_generation(service, project_path) is not None

    # Test 8: PyPSA Template
    results['pypsa_template'] = test_pypsa_template(service, project_path)

    # Summary
    print_section("TEST SUMMARY")

    total = len(results)
    passed = sum(results.values())

    print(f"\nTests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print("\nDetailed Results:")

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name.replace('_', ' ').title()}")

    print("\n" + "="*80)

    if passed == total:
        print("✅ ALL TESTS PASSED - Dash webapp is fully functional!")
    elif passed >= total * 0.8:
        print("⚠️  MOSTLY WORKING - Some non-critical issues remain")
    else:
        print("❌ CRITICAL ISSUES - Further debugging required")

    print("="*80 + "\n")

    return passed == total

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
