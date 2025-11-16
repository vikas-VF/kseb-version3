#!/usr/bin/env python3
"""
Test script to identify issues with the Dash app
"""

import sys
import traceback

print("=" * 80)
print("DASH APP DIAGNOSTIC TEST")
print("=" * 80)

# Test 1: Check imports
print("\n[TEST 1] Checking imports...")
try:
    import dash
    print("✅ dash imported")
    import dash_bootstrap_components as dbc
    print("✅ dash_bootstrap_components imported")
    import plotly
    print("✅ plotly imported")
    import pandas
    print("✅ pandas imported")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 2: Try to import app module
print("\n[TEST 2] Importing app module...")
try:
    import app
    print("✅ app module imported")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check if app instance exists
print("\n[TEST 3] Checking app instance...")
try:
    if hasattr(app, 'app'):
        print("✅ app.app exists")
        print(f"   Dash version: {dash.__version__}")
        print(f"   App title: {app.app.title}")
    else:
        print("❌ app.app not found")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error checking app: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check callbacks
print("\n[TEST 4] Checking registered callbacks...")
try:
    callbacks = app.app.callback_map
    print(f"✅ Total callbacks registered: {len(callbacks)}")

    # Check for specific critical callbacks
    critical_callbacks = [
        'selected-page-store.data',
        'main-content.children',
        'topbar-container.children',
        'sidebar-container.children'
    ]

    for callback_id in critical_callbacks:
        if callback_id in callbacks:
            print(f"   ✅ {callback_id}")
        else:
            print(f"   ⚠️  {callback_id} NOT FOUND")

except Exception as e:
    print(f"❌ Error checking callbacks: {e}")
    traceback.print_exc()

# Test 5: Check for duplicate outputs
print("\n[TEST 5] Checking for duplicate callback outputs...")
try:
    outputs_seen = {}
    duplicates = []

    for callback_id, callback_info in app.app.callback_map.items():
        if callback_id in outputs_seen:
            duplicates.append(callback_id)
            print(f"   ⚠️  DUPLICATE OUTPUT: {callback_id}")
        else:
            outputs_seen[callback_id] = True

    if not duplicates:
        print("✅ No duplicate outputs found")
    else:
        print(f"❌ Found {len(duplicates)} duplicate outputs!")

except Exception as e:
    print(f"❌ Error checking duplicates: {e}")
    traceback.print_exc()

# Test 6: Check page modules
print("\n[TEST 6] Testing page module imports...")
try:
    from pages import home, create_project, load_project
    print("✅ Core page modules import successfully")

    # Test if layout functions exist
    if hasattr(create_project, 'layout'):
        print("   ✅ create_project.layout exists")
    else:
        print("   ❌ create_project.layout NOT FOUND")

    if hasattr(load_project, 'layout'):
        print("   ✅ load_project.layout exists")
    else:
        print("   ❌ load_project.layout NOT FOUND")

except Exception as e:
    print(f"❌ Error importing pages: {e}")
    traceback.print_exc()

# Test 7: Try to render a page
print("\n[TEST 7] Testing page rendering...")
try:
    from pages import create_project
    layout = create_project.layout()
    print("✅ create_project.layout() renders without errors")
except Exception as e:
    print(f"❌ Error rendering create_project layout: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nIf all tests passed, the app should work correctly.")
print("If tests failed, check the error messages above for details.")
