#!/usr/bin/env python3
"""
Script to apply all remaining bug fixes to Dash webapp
Run this after the initial fixes have been committed
"""

import re
import os
from pathlib import Path


def fix_demand_projection_unit_conversion():
    """Fix remaining unit conversion in demand_projection.py"""
    file_path = Path("dash/pages/demand_projection.py")
    content = file_path.read_text()

    # Fix 1: Line 683 - df[col] = df[col] * factor
    content = re.sub(
        r"(\s+)df\[col\] = df\[col\] \* factor",
        r"\1df[col] = df[col].apply(lambda x: safe_multiply(x, factor))",
        content
    )

    # Fix 2-4: Lines 798, 853, 906 - y=df[sector] * factor
    content = re.sub(
        r"y=df\[sector\] \* factor",
        r"y=df[sector].apply(lambda x: safe_multiply(x, factor))",
        content
    )

    # Fix 5: Line 961 - df[col] = df[col] * factor (second occurrence)
    # Already fixed by first replacement

    # Fix 6: Line 1095 - y=df[electricity_col] * factor
    content = re.sub(
        r"y=df\[electricity_col\] \* factor",
        r"y=df[electricity_col].apply(lambda x: safe_multiply(x, factor))",
        content
    )

    file_path.write_text(content)
    print("✅ Fixed unit conversion in demand_projection.py")


def fix_scenario_dropdown():
    """Fix scenario dropdown not loading in demand_visualization.py"""
    file_path = Path("dash/pages/demand_visualization.py")
    content = file_path.read_text()

    # Find the scenario loading callback and ensure prevent_initial_call=False
    content = re.sub(
        r"(@callback\([^)]*Output\('viz-scenario-dropdown'.*?\n.*?prevent_initial_call)=True",
        r"\1=False",
        content,
        flags=re.DOTALL
    )

    file_path.write_text(content)
    print("✅ Fixed scenario dropdown loading")


def fix_generate_profiles_base_year():
    """Fix base year dropdown in generate_profiles.py"""
    file_path = Path("dash/pages/generate_profiles.py")
    content = file_path.read_text()

    # Ensure base year callback has prevent_initial_call=False
    content = re.sub(
        r"(def.*?base.*?year.*?\n.*?prevent_initial_call)=True",
        r"\1=False",
        content,
        flags=re.DOTALL
    )

    file_path.write_text(content)
    print("✅ Fixed base year dropdown in generate_profiles.py")


def fix_color_picker_type():
    """Fix color picker input type errors"""
    # Settings page
    settings_path = Path("dash/pages/settings_page.py")
    if settings_path.exists():
        content = settings_path.read_text()

        # Replace dcc.Input type='color' with html.Input
        content = re.sub(
            r"dcc\.Input\(\s*id=(\{[^}]+\}),\s*type=['\"]color['\"]",
            r"html.Input(id=\1, type='color'",
            content
        )

        settings_path.write_text(content)
        print("✅ Fixed color pickers in settings_page.py")

    # Demand visualization
    viz_path = Path("dash/pages/demand_visualization.py")
    if viz_path.exists():
        content = viz_path.read_text()

        # Replace dcc.Input type='color' with html.Input
        content = re.sub(
            r"dcc\.Input\(\s*id=(\{[^}]+\}),\s*type=['\"]color['\"]",
            r"html.Input(id=\1, type='color'",
            content
        )

        viz_path.write_text(content)
        print("✅ Fixed color pickers in demand_visualization.py")


def add_missing_get_generation_status_url():
    """Add missing get_generation_status_url method to local_service.py"""
    file_path = Path("dash/services/local_service.py")
    content = file_path.read_text()

    # Check if method already exists
    if "def get_generation_status_url" not in content:
        # Find the get_forecast_status_url method and add generation method after it
        insertion_point = content.find("def get_forecast_status_url")

        if insertion_point != -1:
            # Find the end of that method
            next_method = content.find("\n    def ", insertion_point + 1)
            if next_method != -1:
                new_method = '''

    def get_generation_status_url(self) -> str:
        """Get SSE URL for load profile generation progress"""
        return '/api/generation-status'
'''
                content = content[:next_method] + new_method + content[next_method:]
                file_path.write_text(content)
                print("✅ Added get_generation_status_url method to local_service.py")
    else:
        print("ℹ️  get_generation_status_url already exists")


def fix_pypsa_scenario_loading():
    """Fix PyPSA scenario loading in view_results.py"""
    file_path = Path("dash/pages/view_results.py")
    if file_path.exists():
        content = file_path.read_text()

        # Ensure scenario loading callback exists with prevent_initial_call=False
        if "get_pypsa_scenarios" not in content:
            print("⚠️  Need to add PyPSA scenario loading callback manually")
        else:
            print("ℹ️  PyPSA scenario loading callback exists")


def main():
    """Apply all fixes"""
    print("=" * 60)
    print("Applying Remaining Bug Fixes to Dash Webapp")
    print("=" * 60)

    try:
        print("\n1. Fixing unit conversion in demand_projection.py...")
        fix_demand_projection_unit_conversion()

        print("\n2. Fixing scenario dropdown loading...")
        fix_scenario_dropdown()

        print("\n3. Fixing base year dropdown...")
        fix_generate_profiles_base_year()

        print("\n4. Fixing color picker input types...")
        fix_color_picker_type()

        print("\n5. Adding missing get_generation_status_url method...")
        add_missing_get_generation_status_url()

        print("\n6. Checking PyPSA scenario loading...")
        fix_pypsa_scenario_loading()

        print("\n" + "=" * 60)
        print("✅ All automated fixes applied successfully!")
        print("=" * 60)
        print("\nREMAINING MANUAL FIXES NEEDED:")
        print("1. Fix method selection (RadioItems vs Checklist)")
        print("2. Fix profile dropdowns in analyze_profiles.py")
        print("3. Fix PyPSA run model functionality")
        print("4. Remove orphaned source-radio callbacks")
        print("5. Make MLR parameters dynamic based on correlations")
        print("\nSee CRITICAL_BUG_FIXES.md for detailed instructions")

    except Exception as e:
        print(f"\n❌ Error applying fixes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
