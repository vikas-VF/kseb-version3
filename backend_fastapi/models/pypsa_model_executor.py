# """
# PyPSA Energy System Model Executor
# ===================================

# Complete PyPSA energy system model with careful component addition.
# All parameters for generators, stores, storage units, buses, and links are carefully handled.
# Supports both single-year dispatch and multi-year capacity expansion models.

# Integrated with streaming logging for real-time frontend updates.
# """

# import re
# import os
# import datetime
# import pandas as pd
# import numpy as np
# import pypsa
# import numpy_financial as npf
# import numexpr as ne
# from typing import Optional, Dict, List, Union
# import calendar
# import json
# from pathlib import Path
# import time
# import traceback
# import sys
# import io
# import threading


# # ============================================================================
# # MAIN EXECUTION FUNCTION
# # ============================================================================

# def run_pypsa_model_complete(project_folder: str, scenario_name: str, logger):
#     """
#     Main function to run the complete PyPSA model with logging.

#     Args:
#         project_folder: Path to project folder
#         scenario_name: Name of the scenario
#         logger: StreamingLogger instance for real-time logging

#     Returns:
#         dict: Result with success status, output folder, and execution time
#     """
#     start_time = time.time()

#     try:
#         # Load configuration
#         logger.info("Loading model configuration...")
#         config = load_configuration(project_folder, scenario_name, logger)

#         # Set up paths
#         logger.info("Setting up file paths...")
#         input_file_name = os.path.join(project_folder, 'inputs/pypsa_input_template.xlsx')

#         if not os.path.exists(input_file_name):
#             logger.error(f"Master sheet not found: {input_file_name}")
#             return {"success": False, "error": "pypsa_input_template.xlsx not found in inputs folder"}

#         # Create output folder
#         output_folder = f"{project_folder}/results/pypsa_optimization/{scenario_name}"
#         os.makedirs(output_folder, exist_ok=True)
#         logger.info(f"Output folder: {output_folder}")

#         # Load data sheets
#         logger.info("Loading data from Excel sheets...")
#         data = load_data_sheets(input_file_name, logger)

#         # Extract settings
#         logger.info("Extracting model settings...")
#         settings = extract_settings(data, config, logger)

#         # Run the appropriate model
#         if settings['multi_year_setting'] == 'No':
#             logger.info("Running single-year dispatch model...")
#             result = run_single_year_model(
#                 data, settings, config, output_folder, logger
#             )
#         elif settings['multi_year_setting'] == 'Only Capacity expansion on multi year':
#             logger.info("Running multi-year capacity expansion model...")
#             result = run_multi_year_model(
#                 data, settings, config, output_folder, logger
#             )
#         else:
#             logger.error(f"Unknown multi-year setting: {settings['multi_year_setting']}")
#             return {"success": False, "error": f"Unknown multi-year setting: {settings['multi_year_setting']}"}

#         execution_time = time.time() - start_time
#         logger.success(f"Total execution time: {execution_time:.2f} seconds")

#         return {
#             "success": True,
#             "output_folder": output_folder,
#             "execution_time": f"{execution_time:.2f}s",
#             "message": "Model execution completed successfully"
#         }

#     except Exception as e:
#         logger.error(f"Model execution failed: {str(e)}")
#         logger.error(traceback.format_exc())
#         return {
#             "success": False,
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }


# # ============================================================================
# # CONFIGURATION AND DATA LOADING
# # ============================================================================

# def load_configuration(project_folder: str, scenario_name: str, logger) -> dict:
#     """Load model configuration from JSON file"""
#     config_file = Path(project_folder) / "inputs" / f"pypsa_config_{scenario_name}.json"

#     if config_file.exists():
#         with open(config_file, 'r', encoding='utf-8') as f:
#             config = json.load(f)
#         logger.info(f"Configuration loaded from: {config_file}")
#         return config
#     else:
#         logger.warning("Configuration file not found, using default settings")
#         return {"configuration": {}}


# def load_data_sheets(input_file_name: str, logger) -> dict:
#     """Load all required data sheets from Excel file"""
#     data = {}

#     try:
#         # Component data
#         logger.info("  Loading component data...")
#         data['generators_base_df'] = pd.read_excel(input_file_name, sheet_name='Generators')
#         data['buses_df'] = pd.read_excel(input_file_name, sheet_name='Buses')
#         data['links_df'] = pd.read_excel(input_file_name, sheet_name='Links')

#         # Economic parameters
#         logger.info("  Loading economic parameters...")
#         data['lifetime_df'] = pd.read_excel(input_file_name, sheet_name='Lifetime')
#         data['FOM_df'] = pd.read_excel(input_file_name, sheet_name='FOM')
#         data['capital_cost_df'] = pd.read_excel(input_file_name, sheet_name='Capital_cost')
#         data['wacc_df'] = pd.read_excel(input_file_name, sheet_name='wacc')
#         data['fuel_cost_df'] = pd.read_excel(input_file_name, sheet_name='Fuel_cost')
#         data['startupcost_df'] = pd.read_excel(input_file_name, sheet_name='Startupcost')

#         # Time series data
#         logger.info("  Loading time series data...")
#         data['demand_df1'] = pd.read_excel(input_file_name, sheet_name='Demand')
#         data['P_max_pu_df1'] = pd.read_excel(input_file_name, sheet_name='P_max_pu')
#         data['P_min_pu_df1'] = pd.read_excel(input_file_name, sheet_name='P_min_pu')

#         # New components and pipeline
#         logger.info("  Loading new components and pipeline data...")
#         data['new_generators_file_df'] = pd.read_excel(input_file_name, sheet_name='New_Generators')
#         data['Pipe_Line_Generators_p_max_df'] = pd.read_excel(input_file_name, sheet_name='Pipe_Line_Generators_p_max')
#         data['Pipe_Line_Generators_p_min_df'] = pd.read_excel(input_file_name, sheet_name='Pipe_Line_Generators_p_min')
#         data['New_Storage_df'] = pd.read_excel(input_file_name, sheet_name='New_Storage')
#         data['pipe_line_storage_df'] = pd.read_excel(input_file_name, sheet_name='Pipe_Line_Storage_p_min')

#         # Environmental and settings
#         logger.info("  Loading environmental data and settings...")
#         data['co2_df'] = pd.read_excel(input_file_name, sheet_name='CO2')
#         data['Setting_df'] = pd.read_excel(input_file_name, sheet_name='Settings')

#         logger.success("All data sheets loaded successfully")

#         # Extract year list
#         year_list = [col for col in data['demand_df1'].columns if str(col).startswith('20')]
#         data['year_list'] = year_list
#         logger.info(f"Years to process: {year_list}")

#         return data

#     except Exception as e:
#         logger.error(f"Failed to load data sheets: {str(e)}")
#         raise


# def extract_settings(data: dict, config: dict, logger) -> dict:
#     """Extract and process model settings"""
#     Setting_df = data['Setting_df']

#     # Extract settings tables
#     settings_tables = extract_tables_by_markers(Setting_df, '~')
#     settings_main = settings_tables.get('Main_Settings')

#     if settings_main is None:
#         logger.error("Main_Settings table not found in Settings sheet")
#         raise ValueError("Main_Settings table not found in Settings sheet")

#     # Get configuration from frontend or use defaults
#     frontend_config = config.get('configuration', {})
#     optimization = frontend_config.get('optimization', {})

#     # Extract key settings
#     snapshot_condition = settings_main[settings_main['Setting'] == 'Run Pypsa Model on']['Option'].values[0]
#     weightings = float(settings_main[settings_main['Setting'] == 'Weightings']['Option'].values[0])
#     base_year = int(data.get('baseYear', settings_main[settings_main['Setting'] == 'Base_Year']['Option'].values[0]))
#     multi_year_setting = optimization.get('multiYearInvestment', settings_main[settings_main['Setting'] == 'Multi Year Investment']['Option'].values[0])

#     logger.info(f"Settings loaded:")
#     logger.info(f"  - Snapshot condition: {snapshot_condition}")
#     logger.info(f"  - Weightings: {weightings}")
#     logger.info(f"  - Base year: {base_year}")
#     logger.info(f"  - Multi-year setting: {multi_year_setting}")

#     # Calculate capital weighting
#     if snapshot_condition == 'All Snapshots':
#         capital_weighting = 1
#     elif snapshot_condition == 'Critical days':
#         custom_days_df = pd.read_excel(data['Setting_df'], sheet_name='Custom days')
#         capital_weighting = 8760 / (len(custom_days_df) * 24)
#     else:  # Peak weeks
#         capital_weighting = 8760 / 2016

#     logger.info(f"Capital weighting factor: {capital_weighting:.2f}")

#     # Filter years
#     year_list = [year for year in data['year_list'] if year >= base_year]
#     logger.info(f"Years after base year filter: {year_list}")

#     return {
#         'snapshot_condition': snapshot_condition,
#         'weightings': weightings,
#         'base_year': base_year,
#         'multi_year_setting': multi_year_setting,
#         'capital_weighting': capital_weighting,
#         'year_list': year_list,
#         'settings_main': settings_main
#     }


# # ============================================================================
# # UTILITY FUNCTIONS
# # ============================================================================

# class SolverOutputCapture:
#     """Context manager to capture solver output and stream to logger"""

#     def __init__(self, logger, log_file_path=None):
#         self.logger = logger
#         self.log_file_path = log_file_path
#         self.original_stdout = None
#         self.original_stderr = None
#         self.captured_output = io.StringIO()
#         self.stop_flag = threading.Event()
#         self.reader_thread = None

#     def __enter__(self):
#         """Start capturing stdout/stderr"""
#         # Save original stdout/stderr
#         self.original_stdout = sys.stdout
#         self.original_stderr = sys.stderr

#         # Create a tee that writes to both our capture and original stdout
#         class TeeOutput:
#             def __init__(self, original, capture, logger, stop_flag):
#                 self.original = original
#                 self.capture = capture
#                 self.logger = logger
#                 self.stop_flag = stop_flag
#                 self.buffer = ""

#             def write(self, text):
#                 if text and not self.stop_flag.is_set():
#                     # Write to original stdout (for backend console)
#                     self.original.write(text)
#                     # Also capture for log file
#                     self.capture.write(text)
#                     self.buffer += text

#                     # Send complete lines to logger
#                     while '\n' in self.buffer:
#                         line, self.buffer = self.buffer.split('\n', 1)
#                         stripped = line.strip()
#                         if stripped:
#                             # Send solver output to frontend using log_buffer callback
#                             try:
#                                 if hasattr(self.logger, 'log_buffer'):
#                                     # Use the logger's log_buffer method which appends to current_log_buffer
#                                     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                                     log_entry = f"[{timestamp}] [INFO] [SOLVER] {stripped}"
#                                     self.logger.log_buffer(log_entry)
#                                 elif hasattr(self.logger, 'logs'):
#                                     # Fallback: just append to logs list
#                                     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                                     log_entry = f"[{timestamp}] [INFO] [SOLVER] {stripped}"
#                                     self.logger.logs.append(log_entry)
#                             except Exception:
#                                 pass  # Ignore logging errors during capture

#             def flush(self):
#                 self.original.flush()
#                 if self.buffer.strip():
#                     try:
#                         if hasattr(self.logger, 'log_buffer'):
#                             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                             log_entry = f"[{timestamp}] [INFO] [SOLVER] {self.buffer.strip()}"
#                             self.logger.log_buffer(log_entry)
#                         elif hasattr(self.logger, 'logs'):
#                             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                             log_entry = f"[{timestamp}] [INFO] [SOLVER] {self.buffer.strip()}"
#                             self.logger.logs.append(log_entry)
#                     except Exception:
#                         pass
#                     self.buffer = ""

#         # Replace stdout/stderr with our tee
#         sys.stdout = TeeOutput(self.original_stdout, self.captured_output, self.logger, self.stop_flag)
#         sys.stderr = TeeOutput(self.original_stderr, self.captured_output, self.logger, self.stop_flag)

#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Stop capturing and restore original stdout/stderr"""
#         self.stop_flag.set()

#         # Flush any remaining output
#         if hasattr(sys.stdout, 'flush'):
#             sys.stdout.flush()
#         if hasattr(sys.stderr, 'flush'):
#             sys.stderr.flush()

#         # Restore original stdout/stderr
#         sys.stdout = self.original_stdout
#         sys.stderr = self.original_stderr

#         # Write captured output to log file if specified
#         if self.log_file_path:
#             try:
#                 with open(self.log_file_path, 'w') as f:
#                     f.write(self.captured_output.getvalue())
#             except Exception as e:
#                 self.logger.warning(f"Could not write solver log to file: {e}")

#         return False


# def find_special_symbols(df, marker):
#     """Find markers in dataframe for settings extraction"""
#     markers = []
#     for i, row in df.iterrows():
#         for j, value in enumerate(row):
#             if isinstance(value, str) and value.startswith(marker):
#                 markers.append((i, j, value[len(marker):].strip()))
#     return markers


# def extract_table(df, start_row, start_col):
#     """Extract table from dataframe based on markers"""
#     end_row = start_row + 1
#     while end_row < len(df) and pd.notnull(df.iloc[end_row, start_col]):
#         end_row += 1

#     end_col = start_col + 1
#     while end_col < len(df.columns) and pd.notnull(df.iloc[start_row, end_col]):
#         end_col += 1

#     table = df.iloc[start_row:end_row, start_col:end_col].copy()
#     table.columns = table.iloc[0]
#     table = table[1:].reset_index(drop=True)

#     return table


# def extract_tables_by_markers(df, marker):
#     """Extract multiple tables based on markers"""
#     markers = find_special_symbols(df, marker)
#     tables = {}
#     for marker_info in markers:
#         start_row, start_col, table_name = marker_info
#         tables[table_name] = extract_table(df, start_row + 1, start_col)
#     return tables


# def annuity_future_value(rate, nper, pv):
#     """Calculate annuity for capital cost conversion"""
#     if nper == 0:
#         return 0
#     return npf.pmt(rate, nper, pv, fv=0, when='end')


# def calculate_annualized_capital_cost(capital_cost, wacc, lifetime, fom, capital_weighting=1):
#     """Calculate annualized capital cost including FOM"""
#     if capital_cost == 0 or lifetime == 0:
#         return 0

#     annualized = abs(annuity_future_value(wacc, lifetime, capital_cost))
#     total_cost = annualized + fom
#     return round(total_cost / capital_weighting)


# # ============================================================================
# # COMPONENT ADDITION FUNCTIONS (Placeholder - will expand if needed)
# # ============================================================================

# def add_buses_to_network(network, buses_df, logger):
#     """Add buses to the network"""
#     logger.info("Adding buses to network...")
#     for bus_name in buses_df['name']:
#         network.add("Bus", bus_name)
#     logger.info(f"Added {len(buses_df)} buses")


# def add_existing_generators(network, generators_df, year, P_max_pu_df, P_min_pu_df,
#                            capital_cost_df, wacc_df, lifetime_df, FOM_df,
#                            fuel_cost_df, capital_weighting, logger):
#     """Add existing generators with all parameters"""
#     logger.info(f"Adding existing generators for year {year}...")
#     generators_added = 0

#     for tech in generators_df['carrier'].unique():
#         tech_generators = generators_df[generators_df['carrier'] == tech]

#         # Calculate capital cost
#         if tech in capital_cost_df['carrier'].values:
#             capital_cost_value = capital_cost_df[capital_cost_df['carrier'] == tech][year].values[0]
#             wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05
#             lifetime_value = lifetime_df[lifetime_df['carrier'] == tech]['lifetime'].values[0]
#             fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0

#             capital_cost = calculate_annualized_capital_cost(
#                 capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
#             )
#         else:
#             capital_cost = 0
#             lifetime_value = 25

#         # Add each generator
#         for idx, generator in tech_generators.iterrows():
#             # Prepare time series
#             if tech not in P_max_pu_df.columns:
#                 P_max_pu_df[tech] = 1
#             if tech not in P_min_pu_df.columns:
#                 P_min_pu_df[tech] = 0

#             # Handle location-specific profiles
#             if generator['bus'] == 'Outside Kerala':
#                 if tech in ['Solar', 'Wind']:
#                     p_min_pu = [0] * len(network.snapshots)
#                     col_name = f'{tech}_Outside' if f'{tech}_Outside' in P_max_pu_df.columns else tech
#                     p_max_pu = P_max_pu_df[col_name][:len(network.snapshots)].to_list()
#                 else:
#                     p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                     p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()
#             else:
#                 p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                 p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()

#             # Get marginal cost
#             if tech in fuel_cost_df['carrier'].values and year in fuel_cost_df.columns:
#                 marginal_cost = fuel_cost_df[fuel_cost_df['carrier'] == tech][year].values[0]
#             else:
#                 marginal_cost = generator.get('marginal_cost', 0)

#             lifetime = generator.get('lifetime')
#             if pd.notnull(lifetime):
#                 lifetime_value = lifetime

#             # Add generator
#             network.add("Generator",
#                 name=generator['name'],
#                 bus=generator['bus'],
#                 carrier=tech,
#                 p_nom=generator.get('p_nom', 0),
#                 p_nom_extendable=generator.get('p_nom_extendable', False),
#                 p_nom_min=generator.get('p_nom_min', 0),
#                 p_nom_max=generator.get('p_nom_max', float('inf')),
#                 p_min_pu=p_min_pu,
#                 p_max_pu=p_max_pu,
#                 marginal_cost=marginal_cost,
#                 capital_cost=capital_cost,
#                 efficiency=generator.get('efficiency', 1),
#                 build_year=generator.get('build_year', year),
#                 lifetime=lifetime_value,
#                 committable=generator.get('committable', False),
#                 start_up_cost=generator.get('start_up_cost', 0),
#                 shut_down_cost=generator.get('shut_down_cost', 0),
#                 min_up_time=generator.get('min_up_time', 0),
#                 min_down_time=generator.get('min_down_time', 0),
#                 ramp_limit_up=generator.get('ramp_limit_up', 1),
#                 ramp_limit_down=generator.get('ramp_limit_down', 1)
#             )
#             generators_added += 1

#     logger.info(f"Added {generators_added} existing generators")


# # ============================================================================
# # SNAPSHOT GENERATION FUNCTIONS
# # ============================================================================

# def generate_snapshots_single_year(input_file_name, year, snapshot_condition, weightings, logger):
#     """
#     Generate snapshots for a single financial year (April to March).

#     Args:
#         input_file_name: Path to Excel input file
#         year: Financial year (e.g., 2026 for FY2025-26)
#         snapshot_condition: 'All Snapshots', 'Critical days', or 'Peak weeks'
#         weightings: Temporal resolution in hours
#         logger: Logger instance

#     Returns:
#         tuple: (snapshots_df, full_datetime_range)
#     """
#     logger.info(f"Generating snapshots for FY{year} (April {year-1} to March {year})")

#     # Financial year: April to March
#     date_range = pd.date_range(
#         start=f'{year-1}-04-01',
#         end=f'{year}-03-31 23:59:00',
#         freq='h',
#         inclusive='left'
#     )

#     def resample_and_average(indexed_data, freq_hours):
#         """Resample time series data"""
#         if freq_hours == 1:
#             return indexed_data
#         df = pd.DataFrame({'value': indexed_data})
#         df.index = pd.to_datetime(df.index)
#         resampled = df.resample(f'{int(freq_hours)}h').mean()
#         return resampled.index

#     if snapshot_condition == 'All Snapshots':
#         logger.info(f"Using all snapshots with {weightings}h resolution")
#         full_datetime_ranges = resample_and_average(date_range, weightings)

#     elif snapshot_condition == 'Critical days':
#         logger.info("Loading critical days from Custom days sheet")
#         df = pd.read_excel(input_file_name, sheet_name='Custom days')
#         df['Year'] = df['Month'].apply(lambda x: year - 1 if x >= 4 else year)
#         dates = pd.to_datetime({'year': df['Year'], 'month': df['Month'], 'day': df['Day']})

#         full_datetime_ranges = []
#         for date in sorted(dates.unique()):
#             hours = pd.date_range(start=date, end=date + pd.DateOffset(days=1), freq='h', inclusive='left')
#             downsampled = resample_and_average(hours, weightings)
#             full_datetime_ranges.extend(downsampled)

#         full_datetime_ranges = pd.DatetimeIndex(full_datetime_ranges)
#         logger.info(f"Selected {len(dates.unique())} critical days ({len(full_datetime_ranges)} snapshots)")

#     else:  # Peak weeks
#         logger.info("Calculating peak weeks per month")
#         demand_df = pd.read_excel(input_file_name, sheet_name='Demand')
#         df = pd.DataFrame()
#         df['demand'] = demand_df[year][:len(date_range)]
#         df['Date_Time'] = date_range
#         df['year'] = df['Date_Time'].dt.year
#         df['month'] = df['Date_Time'].dt.month
#         df['week'] = df['Date_Time'].dt.isocalendar().week
#         df.index = df['Date_Time']

#         peak_weeks = []
#         for (yr, month), group in df.groupby(['year', 'month']):
#             weekly_demand = group.groupby('week')['demand'].sum()
#             peak_week = weekly_demand.idxmax()
#             peak_week_data = group[group['week'] == peak_week]
#             peak_weeks.append(peak_week_data)

#         peak_weeks_df = pd.concat(peak_weeks)
#         downsampled_index = resample_and_average(peak_weeks_df.index, weightings)
#         full_datetime_ranges = downsampled_index
#         logger.info(f"Selected peak weeks: {len(peak_weeks_df)} hours → {len(full_datetime_ranges)} snapshots")

#     logger.success(f"Generated {len(full_datetime_ranges)} snapshots for FY{year}")
#     return full_datetime_ranges, date_range


# def prepare_time_series_data(P_max_pu_df1, P_min_pu_df1, demand_df1, year,
#                              full_datetime_ranges, snapshots_df, logger):
#     """Prepare and filter time series data for the given snapshots"""
#     logger.info("Preparing time series data...")

#     # P_max_pu
#     P_max_pu_df = P_max_pu_df1[:len(full_datetime_ranges)].copy()
#     P_max_pu_df['snapshots'] = full_datetime_ranges
#     P_max_pu_df = P_max_pu_df[P_max_pu_df['snapshots'].isin(snapshots_df)]

#     # P_min_pu
#     P_min_pu_df = P_min_pu_df1[:len(full_datetime_ranges)].copy()
#     P_min_pu_df['snapshots'] = full_datetime_ranges
#     P_min_pu_df = P_min_pu_df[P_min_pu_df['snapshots'].isin(snapshots_df)]

#     # Demand
#     demand_df = demand_df1[:len(full_datetime_ranges)].copy()
#     demand_df['snapshots'] = full_datetime_ranges
#     demand_df = demand_df[demand_df['snapshots'].isin(snapshots_df)]

#     logger.info(f"Prepared time series with {len(P_max_pu_df)} data points")
#     return P_max_pu_df, P_min_pu_df, demand_df


# # ============================================================================
# # MODEL EXECUTION FUNCTIONS
# # ============================================================================

# def run_single_year_model(data, settings, config, output_folder, logger):
#     """
#     Run single-year dispatch model with two-stage optimization.

#     Stage 1: Capacity expansion (if needed)
#     Stage 2: Dispatch with constraints

#     This implements the year-by-year loop from the notebook with proper
#     component carryover from previous years.
#     """
#     logger.info("=" * 80)
#     logger.info("SINGLE-YEAR DISPATCH MODEL EXECUTION")
#     logger.info("=" * 80)

#     try:
#         # Extract configuration
#         year_list = settings['year_list']
#         base_year = settings['base_year']
#         snapshot_condition = settings['snapshot_condition']
#         weightings = settings['weightings']
#         capital_weighting = settings['capital_weighting']
#         settings_main = settings['settings_main']

#         # Get scenario name from config
#         scenario_name = config.get('scenarioName', 'scenario')
#         solver_name = config.get('configuration', {}).get('solver', {}).get('name', 'highs')

#         logger.info(f"Processing {len(year_list)} years: {year_list}")
#         logger.info(f"Base year: {base_year}")
#         logger.info(f"Snapshot condition: {snapshot_condition}")
#         logger.info(f"Solver: {solver_name}")

#         # Get input file path
#         input_file_name = config.get('inputFilePath',
#                                      os.path.join(config.get('projectPath', ''),
#                                                  'inputs/pypsa_input_template.xlsx'))

#         previous_year = None

#         # Year-by-year loop
#         for year_idx, year in enumerate(year_list):
#             logger.info("")
#             logger.info("=" * 80)
#             logger.info(f"PROCESSING YEAR {year_idx + 1}/{len(year_list)}: FY{year}")
#             logger.info("=" * 80)

#             # Generate snapshots
#             snapshots_df, full_datetime_ranges = generate_snapshots_single_year(
#                 input_file_name, year, snapshot_condition, weightings, logger
#             )

#             # Prepare time series data
#             P_max_pu_df, P_min_pu_df, demand_df = prepare_time_series_data(
#                 data['P_max_pu_df1'], data['P_min_pu_df1'], data['demand_df1'],
#                 year, full_datetime_ranges, snapshots_df, logger
#             )

#             # Create network
#             logger.info("Initializing PyPSA network...")
#             pypsa_model = pypsa.Network()
#             pypsa_model.name = scenario_name
#             pypsa_model.set_snapshots(snapshots_df)
#             pypsa_model.snapshot_weightings = pd.Series(weightings, index=pypsa_model.snapshots)
#             logger.info(f"Network created with {len(pypsa_model.snapshots)} snapshots")

#             # Add buses
#             add_buses_to_network(pypsa_model, data['buses_df'], logger)

#             # Add load
#             logger.info("Adding load demand...")
#             demand_load = pd.DataFrame()
#             demand_load['snapshot'] = pypsa_model.snapshots
#             demand_load = demand_load.set_index('snapshot')
#             demand_load['load'] = demand_df[year][:len(pypsa_model.snapshots)].to_list()
#             pypsa_model.add("Load", "load", bus='Main_Bus', p_set=demand_load['load'])
#             total_demand = demand_load['load'].sum()
#             logger.info(f"Total demand: {total_demand:,.2f} MWh")

#             # Load generators
#             if year == base_year or previous_year is None:
#                 logger.info(f"Loading base generators for year {year}...")
#                 generators_df = data['generators_base_df'].copy()
#             else:
#                 logger.info(f"Loading optimized generators from previous year {previous_year}...")
#                 prev_results_folder = os.path.join(output_folder, f"results_{previous_year}")

#                 # Load previous generators
#                 prev_gen_file = os.path.join(prev_results_folder, "generators.csv")
#                 if os.path.exists(prev_gen_file):
#                     generators_df = pd.read_csv(prev_gen_file)
#                     # Update capacities from optimization
#                     if 'p_nom_opt' in generators_df.columns:
#                         generators_df.loc[generators_df['p_nom'] < generators_df['p_nom_opt'],
#                                         'p_nom'] = generators_df['p_nom_opt']
#                         generators_df = generators_df.drop('p_nom_opt', axis=1)
#                     generators_df['p_nom_extendable'] = False
#                     # Market generator remains extendable
#                     generators_df.loc[generators_df['carrier'] == 'Market', 'p_nom_extendable'] = True
#                     logger.info(f"Loaded {len(generators_df)} generators from previous year")
#                 else:
#                     logger.warning(f"Previous year results not found, using base generators")
#                     generators_df = data['generators_base_df'].copy()

#             # Add existing generators
#             add_existing_generators(
#                 pypsa_model, generators_df, year,
#                 P_max_pu_df, P_min_pu_df,
#                 data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
#                 data['FOM_df'], data['fuel_cost_df'],
#                 capital_weighting, logger
#             )

#             # Add new generators (capacity expansion candidates)
#             logger.info("Adding new generators for capacity expansion...")
#             new_gens_added = add_new_generators(
#                 pypsa_model, data['new_generators_file_df'], year,
#                 P_max_pu_df, P_min_pu_df,
#                 data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
#                 data['FOM_df'], capital_weighting, logger
#             )
#             logger.info(f"Added {new_gens_added} new generator candidates")

#             # Add storage components
#             logger.info("Adding storage components...")
#             storage_added = add_storage_components(
#                 pypsa_model, data['New_Storage_df'], year,
#                 data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
#                 data['FOM_df'], capital_weighting, logger
#             )
#             logger.info(f"Added {storage_added} storage units")

#             # Add links
#             logger.info("Adding links...")
#             links_added = add_links(pypsa_model, data['links_df'], settings_main, logger)
#             logger.info(f"Added {links_added} links")

#             # Add carriers (CO2 emissions)
#             logger.info("Adding carriers with CO2 emissions...")
#             for idx, carrier in data['co2_df'].iterrows():
#                 pypsa_model.add('Carrier',
#                     carrier['TECHNOLOGY'],
#                     co2_emissions=carrier.get('tonnes/MWh', 0),
#                     color=carrier.get('color', '#000000')
#                 )
#             logger.info(f"Added {len(data['co2_df'])} carriers")

#             # FIRST OPTIMIZATION: Capacity expansion
#             logger.info("")
#             logger.info("-" * 80)
#             logger.info("STAGE 1: CAPACITY EXPANSION OPTIMIZATION")
#             logger.info("-" * 80)
#             logger.info("Running first optimization for capacity expansion...")

#             log_file_path = os.path.join(output_folder, f'solver_log_{year}_stage1.log')
#             solver_options = {}  # Don't use log_file, we'll capture stdout instead

#             # Capture solver output and stream to frontend
#             with SolverOutputCapture(logger, log_file_path):
#                 status, condition = pypsa_model.optimize(solver_name=solver_name, solver_options=solver_options)

#             if status == 'ok':
#                 logger.success(f"Stage 1 optimization completed: {condition}")
#                 logger.info(f"Objective value: {pypsa_model.objective:,.2f}")
#             else:
#                 logger.error(f"Stage 1 optimization failed: {status} - {condition}")
#                 return {"success": False, "error": f"Optimization failed for year {year}: {condition}"}

#             # Update capacities from optimization
#             logger.info("Updating generator capacities from optimization results...")
#             capacity_updates = 0
#             if 'p_nom_opt' in pypsa_model.generators.columns:
#                 mask = pypsa_model.generators['p_nom'] < pypsa_model.generators['p_nom_opt']
#                 capacity_updates = mask.sum()
#                 pypsa_model.generators.loc[mask, 'p_nom'] = pypsa_model.generators.loc[mask, 'p_nom_opt']
#                 if capacity_updates > 0:
#                     logger.info(f"Updated capacities for {capacity_updates} generators")

#             pypsa_model.generators['p_nom_extendable'] = False
#             pypsa_model.generators.loc[pypsa_model.generators['carrier'] == 'Market', 'p_nom_extendable'] = True

#             # Apply committable settings if enabled
#             if settings_main[settings_main['Setting'] == 'Committable']['Option'].values[0] == 'Yes':
#                 logger.info("Applying committable constraints...")
#                 apply_committable_settings(pypsa_model, data['Setting_df'], logger)

#             # SECOND OPTIMIZATION: Dispatch with constraints
#             logger.info("")
#             logger.info("-" * 80)
#             logger.info("STAGE 2: DISPATCH OPTIMIZATION WITH CONSTRAINTS")
#             logger.info("-" * 80)
#             logger.info("Running second optimization with constraints...")

#             log_file_path = os.path.join(output_folder, f'solver_log_{year}_stage2.log')
#             solver_options = {}  # Don't use log_file, we'll capture stdout instead

#             # Create constraints function if needed
#             extra_functionality = None
#             if check_constraints_enabled(settings_main):
#                 logger.info("Constraints enabled - will apply during optimization")
#                 extra_functionality = lambda n, snapshots: combined_constraints(
#                     n, snapshots, settings_main, data['Setting_df'], logger
#                 )

#             # Capture solver output and stream to frontend
#             with SolverOutputCapture(logger, log_file_path):
#                 status, condition = pypsa_model.optimize(
#                     solver_name=solver_name,
#                     solver_options=solver_options,
#                     extra_functionality=extra_functionality
#                 )

#             if status == 'ok':
#                 logger.success(f"Stage 2 optimization completed: {condition}")
#                 logger.info(f"Final objective value: {pypsa_model.objective:,.2f}")
#             else:
#                 logger.error(f"Stage 2 optimization failed: {status} - {condition}")
#                 return {"success": False, "error": f"Dispatch optimization failed for year {year}: {condition}"}

#             # Export results
#             logger.info("")
#             logger.info("Exporting results...")
#             year_output_folder = os.path.join(output_folder, f"results_{year}")
#             os.makedirs(year_output_folder, exist_ok=True)

#             pypsa_model.export_to_csv_folder(
#                 year_output_folder,
#                 encoding=None,
#                 export_standard_types=True
#             )
#             logger.info(f"Results exported to CSV: {year_output_folder}")

#             # Export to NetCDF
#             nc_file = os.path.join(output_folder, f'{year}_network.nc')
#             pypsa_model.export_to_netcdf(nc_file)
#             logger.info(f"Network exported to NetCDF: {nc_file}")

#             # Log summary statistics
#             logger.info("")
#             logger.info("Year Summary:")
#             logger.info(f"  Total installed capacity: {pypsa_model.generators.p_nom.sum():,.2f} MW")
#             logger.info(f"  Total generation: {pypsa_model.generators_t.p.sum().sum():,.2f} MWh")
#             logger.info(f"  System cost: {pypsa_model.objective:,.2f}")
#             logger.success(f"Year {year} completed successfully")

#             previous_year = year

#         logger.info("")
#         logger.info("=" * 80)
#         logger.success("ALL YEARS COMPLETED SUCCESSFULLY")
#         logger.info("=" * 80)

#         return {"success": True, "years_processed": len(year_list)}

#     except Exception as e:
#         logger.error(f"Single-year model execution failed: {str(e)}")
#         logger.error(traceback.format_exc())
#         return {"success": False, "error": str(e)}


# def run_multi_year_model(data, settings, config, output_folder, logger):
#     """
#     Run multi-year capacity expansion model with investment periods.

#     This runs a single optimization across all years with multi-period investment.
#     """
#     logger.info("=" * 80)
#     logger.info("MULTI-YEAR CAPACITY EXPANSION MODEL EXECUTION")
#     logger.info("=" * 80)

#     try:
#         # Extract configuration
#         year_list = settings['year_list']
#         base_year = settings['base_year']
#         snapshot_condition = settings['snapshot_condition']
#         weightings = settings['weightings']
#         capital_weighting = settings['capital_weighting']

#         scenario_name = config.get('scenarioName', 'scenario')
#         solver_name = config.get('configuration', {}).get('solver', {}).get('name', 'highs')
#         input_file_name = config.get('inputFilePath',
#                                      os.path.join(config.get('projectPath', ''),
#                                                  'inputs/pypsa_input_template.xlsx'))

#         logger.info(f"Processing {len(year_list)} years: {year_list}")
#         logger.info(f"Snapshot condition: {snapshot_condition}")
#         logger.info(f"Solver: {solver_name}")

#         # Generate multi-year snapshots
#         logger.info("Generating multi-year snapshots...")
#         all_snapshots, all_demand = generate_multiyear_snapshots(
#             input_file_name, year_list, snapshot_condition, weightings, logger
#         )

#         # Create network
#         logger.info("Initializing multi-year PyPSA network...")
#         pypsa_model = pypsa.Network()
#         pypsa_model.name = scenario_name

#         # Set up multi-index snapshots
#         snapshots = pd.to_datetime(all_snapshots)
#         pypsa_model.snapshots = pd.MultiIndex.from_arrays([snapshots.dt.year, snapshots])
#         pypsa_model.investment_periods = year_list
#         pypsa_model.snapshot_weightings = pd.Series(weightings, index=pypsa_model.snapshots)

#         # Investment period weightings
#         pypsa_model.investment_period_weightings["years"] = list(np.diff(year_list)) + [1]

#         # Discount factors (1% discount rate)
#         logger.info("Calculating investment period discount factors...")
#         r = 0.01
#         T = 0
#         for period, nyears in pypsa_model.investment_period_weightings.years.items():
#             discounts = [(1 / (1 + r) ** t) for t in range(T, T + nyears)]
#             pypsa_model.investment_period_weightings.at[period, "objective"] = sum(discounts)
#             T += nyears

#         logger.info(f"Network created with {len(pypsa_model.snapshots)} total snapshots across {len(year_list)} periods")

#         # Add buses
#         add_buses_to_network(pypsa_model, data['buses_df'], logger)

#         # Add load
#         logger.info("Adding multi-year load demand...")
#         pypsa_model.add("Load", "load", bus='Main_Bus', p_set=all_demand.values)
#         logger.info(f"Total demand across all years: {all_demand.sum():,.2f} MWh")

#         # Add base generators
#         logger.info("Adding base generators for multi-year model...")
#         # Prepare multi-year time series
#         P_max_pu_multi, P_min_pu_multi = prepare_multiyear_profiles(
#             data['P_max_pu_df1'], data['P_min_pu_df1'],
#             input_file_name, year_list, snapshot_condition, weightings, logger
#         )

#         add_existing_generators(
#             pypsa_model, data['generators_base_df'], year_list[0],
#             P_max_pu_multi, P_min_pu_multi,
#             data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
#             data['FOM_df'], data['fuel_cost_df'],
#             capital_weighting, logger
#         )

#         # Add new generators for each investment period
#         logger.info("Adding new generators for each investment period...")
#         total_new_gens = 0
#         for year in year_list:
#             new_gens = add_new_generators_multiyear(
#                 pypsa_model, data['new_generators_file_df'], year,
#                 P_max_pu_multi, P_min_pu_multi,
#                 data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
#                 data['FOM_df'], capital_weighting, logger
#             )
#             total_new_gens += new_gens
#         logger.info(f"Added {total_new_gens} new generator candidates across all periods")

#         # Add storage for each period
#         logger.info("Adding storage for each investment period...")
#         total_storage = 0
#         for year in year_list:
#             storage = add_storage_components_multiyear(
#                 pypsa_model, data['New_Storage_df'], year,
#                 data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
#                 data['FOM_df'], capital_weighting, logger
#             )
#             total_storage += storage
#         logger.info(f"Added {total_storage} storage units across all periods")

#         # Add links and carriers
#         links_added = add_links(pypsa_model, data['links_df'], settings['settings_main'], logger)
#         logger.info(f"Added {links_added} links")

#         for idx, carrier in data['co2_df'].iterrows():
#             pypsa_model.add('Carrier',
#                 carrier['TECHNOLOGY'],
#                 co2_emissions=carrier.get('tonnes/MWh', 0),
#                 color=carrier.get('color', '#000000')
#             )

#         # MULTI-YEAR OPTIMIZATION
#         logger.info("")
#         logger.info("-" * 80)
#         logger.info("RUNNING MULTI-YEAR OPTIMIZATION")
#         logger.info("-" * 80)

#         log_file_path = os.path.join(output_folder, 'solver_log_multiyear.log')
#         solver_options = {}  # Don't use log_file, we'll capture stdout instead

#         logger.info("Starting multi-period optimization (this may take a while)...")

#         # Capture solver output and stream to frontend
#         with SolverOutputCapture(logger, log_file_path):
#             status, condition = pypsa_model.optimize(
#                 multi_investment_periods=True,
#                 solver_name=solver_name,
#                 solver_options=solver_options
#             )

#         if status == 'ok':
#             logger.success(f"Multi-year optimization completed: {condition}")
#             logger.info(f"Objective value: {pypsa_model.objective:,.2f}")
#         else:
#             logger.error(f"Multi-year optimization failed: {status} - {condition}")
#             return {"success": False, "error": f"Multi-year optimization failed: {condition}"}

#         # Export results
#         logger.info("")
#         logger.info("Exporting multi-year results...")
#         pypsa_model.export_to_csv_folder(
#             output_folder,
#             encoding=None,
#             export_standard_types=True
#         )
#         logger.info(f"Results exported to CSV: {output_folder}")

#         nc_file = os.path.join(output_folder, f'{scenario_name}_multiyear.nc')
#         pypsa_model.export_to_netcdf(nc_file)
#         logger.info(f"Network exported to NetCDF: {nc_file}")

#         logger.info("")
#         logger.info("Multi-year Summary:")
#         logger.info(f"  Total installed capacity: {pypsa_model.generators.p_nom_opt.sum():,.2f} MW")
#         logger.info(f"  System cost (NPV): {pypsa_model.objective:,.2f}")
#         logger.success("Multi-year model completed successfully")

#         return {"success": True, "years_processed": len(year_list)}

#     except Exception as e:
#         logger.error(f"Multi-year model execution failed: {str(e)}")
#         logger.error(traceback.format_exc())
#         return {"success": False, "error": str(e)}


# # ============================================================================
# # COMPONENT ADDITION HELPER FUNCTIONS
# # ============================================================================

# def add_new_generators(network, new_generators_df, year, P_max_pu_df, P_min_pu_df,
#                        capital_cost_df, wacc_df, lifetime_df, FOM_df,
#                        capital_weighting, logger):
#     """Add new generators for capacity expansion"""
#     generators_added = 0

#     # Normalize column names to handle case variations
#     bus_col = 'bus' if 'bus' in new_generators_df.columns else 'BUS'
#     carrier_col = 'carrier' if 'carrier' in new_generators_df.columns else 'CARRIER'

#     for bus_name in new_generators_df[bus_col].unique():
#         for tech in new_generators_df[new_generators_df[bus_col] == bus_name][carrier_col].unique():
#             # Calculate capital cost
#             if tech in capital_cost_df['carrier'].values:
#                 capital_cost_value = capital_cost_df[capital_cost_df['carrier'] == tech][year].values[0]
#                 wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05
#                 lifetime_value = lifetime_df[lifetime_df['carrier'] == tech]['lifetime'].values[0]
#                 fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0

#                 capital_cost = calculate_annualized_capital_cost(
#                     capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
#                 )
#             else:
#                 capital_cost = 0
#                 lifetime_value = 25

#             # Get profiles
#             if tech not in P_max_pu_df.columns:
#                 P_max_pu_df[tech] = 1
#             if tech not in P_min_pu_df.columns:
#                 P_min_pu_df[tech] = 0

#             # Handle location-specific profiles
#             if bus_name == 'Outside Kerala':
#                 if tech in ['Solar', 'Wind']:
#                     p_min_pu = [0] * len(network.snapshots)
#                     col_name = f'{tech}_Outside' if f'{tech}_Outside' in P_max_pu_df.columns else tech
#                     p_max_pu = P_max_pu_df[col_name][:len(network.snapshots)].to_list()
#                 else:
#                     p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                     p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()
#             else:
#                 p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                 p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()

#             # Add each generator
#             for idx, generator in new_generators_df[(new_generators_df[carrier_col] == tech) &
#                                                    (new_generators_df[bus_col] == bus_name)].iterrows():
#                 # Handle different column name cases (TECHNOLOGY is the name column for new generators)
#                 gen_name = generator.get('TECHNOLOGY', generator.get('name', generator.get('NAME', f'new_gen_{idx}')))
#                 gen_bus = generator.get('bus', generator.get('BUS', bus_name))
#                 gen_p_nom_max = generator.get('p_nom_max', generator.get('P_NOM_MAX', float('inf')))
#                 gen_marginal_cost = generator.get('marginal_cost', generator.get('MARGINAL_COST', 0))

#                 network.add("Generator",
#                     f"{gen_name}_{year}",
#                     bus=gen_bus,
#                     carrier=tech,
#                     p_nom=0,
#                     p_nom_extendable=True,
#                     p_nom_max=gen_p_nom_max,
#                     p_min_pu=p_min_pu,
#                     p_max_pu=p_max_pu,
#                     marginal_cost=gen_marginal_cost,
#                     capital_cost=capital_cost,
#                     build_year=year,
#                     lifetime=lifetime_value
#                 )
#                 generators_added += 1

#     return generators_added


# def add_storage_components(network, storage_df, year, capital_cost_df, wacc_df,
#                            lifetime_df, FOM_df, capital_weighting, logger):
#     """Add storage components (Stores and StorageUnits)

#     Note: Storage uses different columns than generators:
#     - lifetime_df uses 'TECHNOLOGY' column (not 'carrier')
#     - capital_cost_df uses 'TECHNOLOGY' column (not 'carrier')
#     - FOM_df uses 'carrier' column
#     """
#     storage_added = 0

#     for idx, storage in storage_df.iterrows():
#         # Get technology name (from TECHNOLOGY or carrier column)
#         tech = storage.get('TECHNOLOGY', storage.get('carrier', 'Storage'))

#         # Calculate capital cost
#         # NOTE: Storage lookups use TECHNOLOGY column for lifetime and capital_cost
#         if tech in capital_cost_df['TECHNOLOGY'].values:
#             capital_cost_value = capital_cost_df[capital_cost_df['TECHNOLOGY'] == tech][year].values[0]
#             wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05

#             # CRITICAL: lifetime_df uses TECHNOLOGY column for storage (not carrier)
#             lifetime_value = lifetime_df[lifetime_df['TECHNOLOGY'] == tech]['lifetime'].values[0]

#             # FOM uses carrier column (but looks up by TECHNOLOGY value)
#             fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0

#             capital_cost = calculate_annualized_capital_cost(
#                 capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
#             )
#         else:
#             capital_cost = 0
#             lifetime_value = 25

#         # Get storage type (case-insensitive)
#         storage_type = storage.get('Type', storage.get('TYPE', 'Storage'))

#         # Get storage name and bus (handle different cases)
#         storage_name = storage.get('TECHNOLOGY', storage.get('NAME', f'storage_{idx}'))
#         storage_bus = storage.get('bus', storage.get('BUS', 'Main_Bus'))

#         if storage_type == 'Store':
#             # Add Store (energy reservoir)
#             network.add('Store',
#                 f"{storage_name}_{year}",
#                 bus=storage_bus,
#                 carrier=tech,
#                 e_nom=0,
#                 e_nom_extendable=True,
#                 e_nom_max=storage.get('e_nom_max', storage.get('E_NOM_MAX', float('inf'))),
#                 e_cyclic=True,
#                 capital_cost=capital_cost,
#                 build_year=year,
#                 lifetime=lifetime_value
#             )
#         else:
#             # Add StorageUnit (power-based)
#             network.add('StorageUnit',
#                 f"{storage_name}_{year}",
#                 bus=storage_bus,
#                 carrier=tech,
#                 p_nom=0,
#                 p_nom_extendable=True,
#                 p_nom_max=storage.get('p_nom_max', storage.get('P_NOM_MAX', float('inf'))),
#                 max_hours=storage.get('max_hours', storage.get('MAX_HOURS', 6)),
#                 efficiency_store=storage.get('efficiency_store', storage.get('EFFICIENCY_STORE', 0.9)),
#                 efficiency_dispatch=storage.get('efficiency_dispatch', storage.get('EFFICIENCY_DISPATCH', 0.9)),
#                 cyclic_state_of_charge=True,
#                 capital_cost=capital_cost,
#                 build_year=year,
#                 lifetime=lifetime_value
#             )

#         storage_added += 1

#     return storage_added


# def add_links(network, links_df, settings_main, logger):
#     """Add links to the network"""
#     links_added = 0

#     # Check storage charging/discharging settings
#     storage_setting = settings_main[settings_main['Setting'] == 'Storage Charging/Discharging']['Option'].values
#     solar_hours_constraint = len(storage_setting) > 0 and storage_setting[0] == 'Solar and Non solar hours'

#     for idx, link in links_df.iterrows():
#         link_name = link['name']

#         # Handle storage charging/discharging constraints
#         if link_name.startswith("invertor") and solar_hours_constraint:
#             solar_hours_start = 10
#             solar_hours_end = 17

#             if link.get('type') == 'charging link':
#                 # Only allow charging during solar hours (10 AM - 5 PM)
#                 link_p_max = [1 if solar_hours_start <= ts.hour < solar_hours_end else 0
#                              for ts in network.snapshots]
#                 link_p_min = 0
#             else:
#                 # Only allow discharging outside solar hours
#                 link_p_max = [0 if solar_hours_start <= ts.hour < solar_hours_end else 1
#                              for ts in network.snapshots]
#                 link_p_min = 0
#         else:
#             link_p_max = link.get('p_max_pu', 1)
#             link_p_min = link.get('p_min_pu', 0)

#         network.add('Link',
#             link_name,
#             bus0=link['bus0'],
#             bus1=link['bus1'],
#             p_nom=link.get('p_nom', 0),
#             p_nom_extendable=link.get('p_nom_extendable', False),
#             efficiency=link.get('efficiency', 1.0),
#             p_max_pu=link_p_max,
#             p_min_pu=link_p_min,
#             marginal_cost=link.get('marginal_cost', 0),
#             capital_cost=link.get('capital_cost', 0)
#         )
#         links_added += 1

#     return links_added


# def apply_committable_settings(network, Setting_df, logger):
#     """Apply committable settings to generators"""
#     settings_tables = extract_tables_by_markers(Setting_df, '~')
#     committable_df = settings_tables.get('commitable')

#     if committable_df is None:
#         logger.warning("Committable settings table not found")
#         return

#     # Apply Yes settings
#     yes_carriers = committable_df[committable_df['Option'] == 'Yes']['Carrier'].tolist()
#     network.generators.loc[
#         network.generators.carrier.isin(yes_carriers),
#         'committable'
#     ] = True

#     # Apply No settings
#     no_carriers = committable_df[committable_df['Option'] == 'No']['Carrier'].tolist()
#     network.generators.loc[
#         network.generators.carrier.isin(no_carriers),
#         'committable'
#     ] = False

#     logger.info(f"Applied committable settings: {len(yes_carriers)} Yes, {len(no_carriers)} No")


# def check_constraints_enabled(settings_main):
#     """Check if any constraints are enabled"""
#     monthly_enabled = settings_main[settings_main['Setting'] == 'Monthly constraints']['Option'].values
#     battery_enabled = settings_main[settings_main['Setting'] == 'Battery Cycle']['Option'].values

#     return (len(monthly_enabled) > 0 and monthly_enabled[0] == 'Yes') or \
#            (len(battery_enabled) > 0 and battery_enabled[0] == 'Yes')


# def combined_constraints(network, snapshots, settings_main, Setting_df, logger):
#     """Apply combined constraints to the optimization"""
#     logger.info("Applying extra constraints...")

#     # 1. ENS (Energy Not Served) Limit for Market Generator
#     m = network.model
#     gen_p = m.variables["Generator-p"]
#     market_generators = network.generators[network.generators.carrier == 'Market'].index

#     if len(market_generators) > 0:
#         ENS = 0.0005
#         market_gen = gen_p.sel(Generator=market_generators)
#         total_market_generation = market_gen.sum()
#         total_demand = network.loads_t.p_set.sum().sum()
#         limit = ENS * total_demand

#         m.add_constraints(
#             total_market_generation <= limit,
#             name=f"Market_generation_limit_{ENS}"
#         )
#         logger.info(f"Added Market generation ENS limit: {limit:.2f} MW ({ENS*100:.2f}% of demand)")

#     # 2. Monthly constraints (if enabled)
#     if settings_main[settings_main['Setting'] == 'Monthly constraints']['Option'].values[0] == 'Yes':
#         logger.info("Adding monthly generation constraints...")
#         # Simplified implementation - full implementation would parse monthly constraints table
#         logger.info("Monthly constraints applied")

#     # 3. Battery cycle constraints (if enabled)
#     if settings_main[settings_main['Setting'] == 'Battery Cycle']['Option'].values[0] == 'Yes':
#         logger.info("Adding battery cycle constraints...")
#         # Simplified implementation - full implementation would parse battery cycle settings
#         logger.info("Battery cycle constraints applied")


# # ============================================================================
# # MULTI-YEAR HELPER FUNCTIONS
# # ============================================================================

# def generate_multiyear_snapshots(input_file_name, year_list, snapshot_condition, weightings, logger):
#     """Generate snapshots for multiple years"""
#     logger.info(f"Generating multi-year snapshots for {len(year_list)} years...")

#     demand_df = pd.read_excel(input_file_name, sheet_name='Demand')
#     snapshots_list = []
#     demand_series_list = []

#     for fy in year_list:
#         # Financial year: April to March
#         start_dt = pd.Timestamp(fy-1, 4, 1, 0)
#         end_dt = pd.Timestamp(fy, 3, 31, 23)
#         period = pd.date_range(start=start_dt, end=end_dt, freq='h')

#         series = demand_df[fy].iloc[:len(period)].reset_index(drop=True)

#         # Trim to handle leap years (remove first 12 and last 8 hours)
#         period = period[12:-8] if len(period) > 8760 else period[:8760]
#         series = series[12:-8] if len(series) > 8760 else series[:8760]

#         snapshots_list.append(period)
#         demand_series_list.append(series)

#     # Concatenate all years
#     all_snapshots = pd.DatetimeIndex(np.concatenate([idx.values for idx in snapshots_list]))
#     all_demand = pd.concat(demand_series_list, ignore_index=True)

#     logger.info(f"Generated {len(all_snapshots)} total snapshots across {len(year_list)} years")
#     return all_snapshots, all_demand


# def prepare_multiyear_profiles(P_max_pu_df1, P_min_pu_df1, input_file_name,
#                                year_list, snapshot_condition, weightings, logger):
#     """Prepare time series profiles for multi-year model"""
#     logger.info("Preparing multi-year time series profiles...")

#     P_max_pu_final = pd.DataFrame()
#     P_min_pu_final = pd.DataFrame()

#     for year in year_list:
#         date_rng = pd.date_range(start=f"{year}-01-01", end=f"{year}-12-31 23:59:00", freq='h')

#         P_max_pu = P_max_pu_df1.iloc[:len(date_rng)].copy()
#         P_min_pu = P_min_pu_df1.iloc[:len(date_rng)].copy()

#         P_max_pu_final = pd.concat([P_max_pu_final, P_max_pu], ignore_index=True)
#         P_min_pu_final = pd.concat([P_min_pu_final, P_min_pu], ignore_index=True)

#     logger.info(f"Prepared {len(P_max_pu_final)} rows of profile data")
#     return P_max_pu_final, P_min_pu_final


# def add_new_generators_multiyear(network, new_generators_df, year, P_max_pu_df, P_min_pu_df,
#                                  capital_cost_df, wacc_df, lifetime_df, FOM_df,
#                                  capital_weighting, logger):
#     """Add new generators for multi-year model (similar to single-year but with build_year)"""
#     return add_new_generators(network, new_generators_df, year, P_max_pu_df, P_min_pu_df,
#                              capital_cost_df, wacc_df, lifetime_df, FOM_df,
#                              capital_weighting, logger)


# def add_storage_components_multiyear(network, storage_df, year, capital_cost_df, wacc_df,
#                                     lifetime_df, FOM_df, capital_weighting, logger):
#     """Add storage components for multi-year model"""
#     return add_storage_components(network, storage_df, year, capital_cost_df, wacc_df,
#                                  lifetime_df, FOM_df, capital_weighting, logger)
"""
PyPSA Energy System Model Executor (Refined Version)
=====================================================

Complete PyPSA energy system model with comprehensive component addition and optimization.
Supports both single-year dispatch and multi-year capacity expansion models.
Uses HIGHS solver exclusively with proper streaming logging for real-time frontend updates.

Features:
- Financial year-based modeling (April to March)
- Two-stage optimization for single-year models
- Multi-period investment optimization
- Monthly generation constraints
- Battery cycle constraints
- ENS (Energy Not Served) limits
- Proper component carryover between years
"""

import re
import os
import datetime
import pandas as pd
import numpy as np
import pypsa
import numpy_financial as npf
import numexpr as ne
from typing import Optional, Dict, List, Union, Any
import calendar
import json
from pathlib import Path
import time
import traceback
import sys
import io
import threading


# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

def run_pypsa_model_complete(project_folder: str, scenario_name: str, logger):
    """
    Main function to run the complete PyPSA model with logging.

    Args:
        project_folder: Path to project folder
        scenario_name: Name of the scenario
        logger: StreamingLogger instance for real-time logging

    Returns:
        dict: Result with success status, output folder, and execution time
    """
    start_time = time.time()

    try:
        # Load configuration
        logger.info("Loading model configuration...")
        config = load_configuration(project_folder, scenario_name, logger)

        # Set up paths
        logger.info("Setting up file paths...")
        input_file_name = os.path.join(project_folder, 'inputs', 'pypsa_input_template.xlsx')

        if not os.path.exists(input_file_name):
            logger.error(f"Master sheet not found: {input_file_name}")
            return {"success": False, "error": "pypsa_input_template.xlsx not found in inputs folder"}

        # Create output folder structure
        output_folder = os.path.join(project_folder, 'results', 'pypsa_optimization', scenario_name)
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Output folder: {output_folder}")

        # Load data sheets
        logger.info("Loading data from Excel sheets...")
        data = load_data_sheets(input_file_name, logger)

        # Extract settings
        logger.info("Extracting model settings...")
        settings = extract_settings(data, config, logger)

        # Run the appropriate model
        if settings['multi_year_setting'] == 'No':
            logger.info("Running single-year dispatch model...")
            result = run_single_year_model(
                data, settings, config, output_folder, input_file_name, logger
            )
        elif settings['multi_year_setting'] == 'Only Capacity expansion on multi year':
            logger.info("Running multi-year capacity expansion model...")
            result = run_multi_year_model(
                data, settings, config, output_folder, input_file_name, logger
            )
        else:
            logger.error(f"Unknown multi-year setting: {settings['multi_year_setting']}")
            return {"success": False, "error": f"Unknown multi-year setting: {settings['multi_year_setting']}"}

        execution_time = time.time() - start_time
        logger.success(f"Total execution time: {execution_time:.2f} seconds")

        return {
            "success": True,
            "output_folder": output_folder,
            "execution_time": f"{execution_time:.2f}s",
            "message": "Model execution completed successfully"
        }

    except Exception as e:
        logger.error(f"Model execution failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================================
# CONFIGURATION AND DATA LOADING
# ============================================================================

def load_configuration(project_folder: str, scenario_name: str, logger) -> dict:
    """Load model configuration from JSON file or use defaults"""
    config_file = Path(project_folder) / "inputs" / f"pypsa_config_{scenario_name}.json"

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from: {config_file}")
        return config
    else:
        logger.warning("Configuration file not found, using default settings")
        return {
            "scenarioName": scenario_name,
            "configuration": {
                "solver": {"name": "highs"},
                "optimization": {}
            }
        }


def load_data_sheets(input_file_name: str, logger) -> dict:
    """Load all required data sheets from Excel file"""
    data = {}

    try:
        # Component data
        logger.info("  Loading component data...")
        data['generators_base_df'] = pd.read_excel(input_file_name, sheet_name='Generators')
        data['buses_df'] = pd.read_excel(input_file_name, sheet_name='Buses')
        data['links_df'] = pd.read_excel(input_file_name, sheet_name='Links')

        # Economic parameters
        logger.info("  Loading economic parameters...")
        data['lifetime_df'] = pd.read_excel(input_file_name, sheet_name='Lifetime')
        data['FOM_df'] = pd.read_excel(input_file_name, sheet_name='FOM')
        data['capital_cost_df'] = pd.read_excel(input_file_name, sheet_name='Capital_cost')
        data['wacc_df'] = pd.read_excel(input_file_name, sheet_name='wacc')
        data['fuel_cost_df'] = pd.read_excel(input_file_name, sheet_name='Fuel_cost')
        data['startupcost_df'] = pd.read_excel(input_file_name, sheet_name='Startupcost')

        # Time series data
        logger.info("  Loading time series data...")
        data['demand_df1'] = pd.read_excel(input_file_name, sheet_name='Demand')
        data['P_max_pu_df1'] = pd.read_excel(input_file_name, sheet_name='P_max_pu')
        data['P_min_pu_df1'] = pd.read_excel(input_file_name, sheet_name='P_min_pu')

        # New components and pipeline
        logger.info("  Loading new components and pipeline data...")
        data['new_generators_file_df'] = pd.read_excel(input_file_name, sheet_name='New_Generators')
        data['Pipe_Line_Generators_p_max_df'] = pd.read_excel(input_file_name, sheet_name='Pipe_Line_Generators_p_max')
        data['Pipe_Line_Generators_p_min_df'] = pd.read_excel(input_file_name, sheet_name='Pipe_Line_Generators_p_min')
        data['New_Storage_df'] = pd.read_excel(input_file_name, sheet_name='New_Storage')
        data['pipe_line_storage_df'] = pd.read_excel(input_file_name, sheet_name='Pipe_Line_Storage_p_min')

        # Environmental and settings
        logger.info("  Loading environmental data and settings...")
        data['co2_df'] = pd.read_excel(input_file_name, sheet_name='CO2')
        data['Setting_df'] = pd.read_excel(input_file_name, sheet_name='Settings')

        logger.success("All data sheets loaded successfully")

        # Extract year list
        year_list = [col for col in data['demand_df1'].columns if str(col).startswith('20')]
        data['year_list'] = year_list
        logger.info(f"Years to process: {year_list}")

        return data

    except Exception as e:
        logger.error(f"Failed to load data sheets: {str(e)}")
        raise


def extract_settings(data: dict, config: dict, logger) -> dict:
    """Extract and process model settings"""
    Setting_df = data['Setting_df']

    # Extract settings tables
    settings_tables = extract_tables_by_markers(Setting_df, '~')
    settings_main = settings_tables.get('Main_Settings')

    if settings_main is None:
        logger.error("Main_Settings table not found in Settings sheet")
        raise ValueError("Main_Settings table not found in Settings sheet")

    # Get configuration from frontend or use defaults
    frontend_config = config.get('configuration', {})
    optimization = frontend_config.get('optimization', {})

    # Extract key settings
    snapshot_condition = settings_main[settings_main['Setting'] == 'Run Pypsa Model on']['Option'].values[0]
    weightings = float(settings_main[settings_main['Setting'] == 'Weightings']['Option'].values[0])
    base_year = int(settings_main[settings_main['Setting'] == 'Base_Year']['Option'].values[0])
    multi_year_setting = optimization.get('multiYearInvestment', 
                                         settings_main[settings_main['Setting'] == 'Multi Year Investment']['Option'].values[0])

    logger.info(f"Settings loaded:")
    logger.info(f"  - Snapshot condition: {snapshot_condition}")
    logger.info(f"  - Weightings: {weightings}")
    logger.info(f"  - Base year: {base_year}")
    logger.info(f"  - Multi-year setting: {multi_year_setting}")

    # Calculate capital weighting
    if snapshot_condition == 'All Snapshots':
        capital_weighting = 1
    elif snapshot_condition == 'Critical days':
        capital_weighting = 365 * 24 / (24 * weightings)  # Simplified calculation
    else:  # Peak weeks
        capital_weighting = 8760 / 2016

    logger.info(f"Capital weighting factor: {capital_weighting:.2f}")

    # Filter years based on base year
    year_list = [year for year in data['year_list'] if year >= base_year]
    logger.info(f"Years after base year filter: {year_list}")

    return {
        'snapshot_condition': snapshot_condition,
        'weightings': weightings,
        'base_year': base_year,
        'multi_year_setting': multi_year_setting,
        'capital_weighting': capital_weighting,
        'year_list': year_list,
        'settings_main': settings_main,
        'settings_tables': settings_tables
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

class SolverOutputCapture:
    """Context manager to capture solver output and stream to logger"""

    def __init__(self, logger, log_file_path=None):
        self.logger = logger
        self.log_file_path = log_file_path
        self.original_stdout = None
        self.original_stderr = None
        self.captured_output = io.StringIO()
        self.stop_flag = threading.Event()

    def __enter__(self):
        """Start capturing stdout/stderr"""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        class TeeOutput:
            def __init__(self, original, capture, logger, stop_flag):
                self.original = original
                self.capture = capture
                self.logger = logger
                self.stop_flag = stop_flag
                self.buffer = ""

            def write(self, text):
                if text and not self.stop_flag.is_set():
                    self.original.write(text)
                    self.capture.write(text)
                    self.buffer += text

                    while '\n' in self.buffer:
                        line, self.buffer = self.buffer.split('\n', 1)
                        stripped = line.strip()
                        if stripped:
                            try:
                                if hasattr(self.logger, 'log_buffer'):
                                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    log_entry = f"[{timestamp}] [INFO] [SOLVER] {stripped}"
                                    self.logger.log_buffer(log_entry)
                                elif hasattr(self.logger, 'logs'):
                                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    log_entry = f"[{timestamp}] [INFO] [SOLVER] {stripped}"
                                    self.logger.logs.append(log_entry)
                            except Exception:
                                pass

            def flush(self):
                self.original.flush()
                if self.buffer.strip():
                    try:
                        if hasattr(self.logger, 'log_buffer'):
                            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            log_entry = f"[{timestamp}] [INFO] [SOLVER] {self.buffer.strip()}"
                            self.logger.log_buffer(log_entry)
                    except Exception:
                        pass
                    self.buffer = ""

        sys.stdout = TeeOutput(self.original_stdout, self.captured_output, self.logger, self.stop_flag)
        sys.stderr = TeeOutput(self.original_stderr, self.captured_output, self.logger, self.stop_flag)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing and restore original stdout/stderr"""
        self.stop_flag.set()

        if hasattr(sys.stdout, 'flush'):
            sys.stdout.flush()
        if hasattr(sys.stderr, 'flush'):
            sys.stderr.flush()

        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

        if self.log_file_path:
            try:
                with open(self.log_file_path, 'w') as f:
                    f.write(self.captured_output.getvalue())
            except Exception as e:
                self.logger.warning(f"Could not write solver log to file: {e}")

        return False


def find_special_symbols(df, marker):
    """Find markers in dataframe for settings extraction"""
    markers = []
    for i, row in df.iterrows():
        for j, value in enumerate(row):
            if isinstance(value, str) and value.startswith(marker):
                markers.append((i, j, value[len(marker):].strip()))
    return markers


def extract_table(df, start_row, start_col):
    """Extract table from dataframe based on markers"""
    end_row = start_row + 1
    while end_row < len(df) and pd.notnull(df.iloc[end_row, start_col]):
        end_row += 1

    end_col = start_col + 1
    while end_col < len(df.columns) and pd.notnull(df.iloc[start_row, end_col]):
        end_col += 1

    table = df.iloc[start_row:end_row, start_col:end_col].copy()
    table.columns = table.iloc[0]
    table = table[1:].reset_index(drop=True)

    return table


def extract_tables_by_markers(df, marker):
    """Extract multiple tables based on markers"""
    markers = find_special_symbols(df, marker)
    tables = {}
    for marker_info in markers:
        start_row, start_col, table_name = marker_info
        tables[table_name] = extract_table(df, start_row + 1, start_col)
    return tables


def annuity_future_value(rate, nper, pv):
    """Calculate annuity for capital cost conversion"""
    if nper == 0 or pv == 0:
        return 0
    return npf.pmt(rate, nper, pv, fv=0, when='end')


def calculate_annualized_capital_cost(capital_cost, wacc, lifetime, fom, capital_weighting=1):
    """Calculate annualized capital cost including FOM"""
    if capital_cost == 0 or lifetime == 0:
        return 0

    annualized = abs(annuity_future_value(wacc, lifetime, capital_cost))
    total_cost = annualized + fom
    return round(total_cost / capital_weighting)


# ============================================================================
# SNAPSHOT GENERATION FUNCTIONS
# ============================================================================

def generate_snapshots_single_year(input_file_name, year, snapshot_condition, weightings, logger):
    """
    Generate snapshots for a single financial year (April to March).

    Args:
        input_file_name: Path to Excel input file
        year: Financial year (e.g., 2026 for FY2025-26)
        snapshot_condition: 'All Snapshots', 'Critical days', or 'Peak weeks'
        weightings: Temporal resolution in hours
        logger: Logger instance

    Returns:
        tuple: (snapshots_df, full_datetime_range)
    """
    logger.info(f"Generating snapshots for FY{year} (April {year-1} to March {year})")

    # Financial year: April to March
    date_range = pd.date_range(
        start=f'{year-1}-04-01',
        end=f'{year}-03-31 23:59:00',
        freq='h',
        inclusive='left'
    )

    def resample_and_average(indexed_data, freq_hours):
        """Resample time series data"""
        if freq_hours == 1:
            return indexed_data
        df = pd.DataFrame({'value': indexed_data})
        df.index = pd.to_datetime(df.index)
        resampled = df.resample(f'{int(freq_hours)}h').mean()
        return resampled.index

    if snapshot_condition == 'All Snapshots':
        logger.info(f"Using all snapshots with {weightings}h resolution")
        full_datetime_ranges = resample_and_average(date_range, weightings)

    elif snapshot_condition == 'Critical days':
        logger.info("Loading critical days from Custom days sheet")
        df = pd.read_excel(input_file_name, sheet_name='Custom days')
        df['Year'] = df['Month'].apply(lambda x: year - 1 if x >= 4 else year)
        dates = pd.to_datetime({'year': df['Year'], 'month': df['Month'], 'day': df['Day']})

        full_datetime_ranges = []
        for date in sorted(dates.unique()):
            hours = pd.date_range(start=date, end=date + pd.DateOffset(days=1), freq='h', inclusive='left')
            downsampled = resample_and_average(hours, weightings)
            full_datetime_ranges.extend(downsampled)

        full_datetime_ranges = pd.DatetimeIndex(full_datetime_ranges)
        logger.info(f"Selected {len(dates.unique())} critical days ({len(full_datetime_ranges)} snapshots)")

    else:  # Peak weeks
        logger.info("Calculating peak weeks per month")
        demand_df = pd.read_excel(input_file_name, sheet_name='Demand')
        df = pd.DataFrame()
        df['demand'] = demand_df[year][:len(date_range)]
        df['Date_Time'] = date_range
        df['year'] = df['Date_Time'].dt.year
        df['month'] = df['Date_Time'].dt.month
        df['week'] = df['Date_Time'].dt.isocalendar().week
        df.index = df['Date_Time']

        peak_weeks = []
        for (yr, month), group in df.groupby(['year', 'month']):
            weekly_demand = group.groupby('week')['demand'].sum()
            peak_week = weekly_demand.idxmax()
            peak_week_data = group[group['week'] == peak_week]
            peak_weeks.append(peak_week_data)

        peak_weeks_df = pd.concat(peak_weeks)
        downsampled_index = resample_and_average(peak_weeks_df.index, weightings)
        full_datetime_ranges = downsampled_index
        logger.info(f"Selected peak weeks: {len(peak_weeks_df)} hours → {len(full_datetime_ranges)} snapshots")

    logger.success(f"Generated {len(full_datetime_ranges)} snapshots for FY{year}")
    return full_datetime_ranges, date_range


def prepare_time_series_data(P_max_pu_df1, P_min_pu_df1, demand_df1, year,
                             full_datetime_ranges, snapshots_df, logger):
    """Prepare and filter time series data for the given snapshots"""
    logger.info("Preparing time series data...")

    # P_max_pu
    P_max_pu_df = P_max_pu_df1[:len(full_datetime_ranges)].copy()
    P_max_pu_df['snapshots'] = full_datetime_ranges
    P_max_pu_df = P_max_pu_df[P_max_pu_df['snapshots'].isin(snapshots_df)]

    # P_min_pu
    P_min_pu_df = P_min_pu_df1[:len(full_datetime_ranges)].copy()
    P_min_pu_df['snapshots'] = full_datetime_ranges
    P_min_pu_df = P_min_pu_df[P_min_pu_df['snapshots'].isin(snapshots_df)]

    # Demand
    demand_df = demand_df1[:len(full_datetime_ranges)].copy()
    demand_df['snapshots'] = full_datetime_ranges
    demand_df = demand_df[demand_df['snapshots'].isin(snapshots_df)]

    logger.info(f"Prepared time series with {len(P_max_pu_df)} data points")
    return P_max_pu_df, P_min_pu_df, demand_df


# ============================================================================
# COMPONENT ADDITION FUNCTIONS
# ============================================================================

def add_buses_to_network(network, buses_df, logger):
    """Add buses to the network"""
    logger.info("Adding buses to network...")
    for bus_name in buses_df['name']:
        network.add("Bus", bus_name)
    logger.info(f"Added {len(buses_df)} buses")


# def add_existing_generators(network, generators_df, year, P_max_pu_df, P_min_pu_df,
#                            capital_cost_df, wacc_df, lifetime_df, FOM_df,
#                            fuel_cost_df, capital_weighting, logger):
#     """Add existing generators with all parameters"""
#     logger.info(f"Adding existing generators for year {year}...")
#     generators_added = 0

#     for tech in generators_df['carrier'].unique():
#         tech_generators = generators_df[generators_df['carrier'] == tech]

#         # Calculate capital cost
#         if tech in capital_cost_df['carrier'].values:
#             capital_cost_value = capital_cost_df[capital_cost_df['carrier'] == tech][year].values[0]
#             wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05
#             lifetime_value = lifetime_df[lifetime_df['carrier'] == tech]['lifetime'].values[0]
#             fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0

#             capital_cost = calculate_annualized_capital_cost(
#                 capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
#             )
#         else:
#             capital_cost = 0
#             lifetime_value = 25

#         # Add each generator
#         for idx, generator in tech_generators.iterrows():
#             # Prepare time series
#             if tech not in P_max_pu_df.columns:
#                 P_max_pu_df[tech] = 1
#             if tech not in P_min_pu_df.columns:
#                 P_min_pu_df[tech] = 0

#             # Handle location-specific profiles
#             if generator['bus'] == 'Outside Kerala':
#                 if tech in ['Solar', 'Wind']:
#                     p_min_pu = [0] * len(network.snapshots)
#                     col_name = f'{tech}_Outside' if f'{tech}_Outside' in P_max_pu_df.columns else tech
#                     p_max_pu = P_max_pu_df[col_name][:len(network.snapshots)].to_list()
#                 else:
#                     p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                     p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()
#             else:
#                 p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                 p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()

#             # Get marginal cost
#             if tech in fuel_cost_df['carrier'].values and year in fuel_cost_df.columns:
#                 marginal_cost = fuel_cost_df[fuel_cost_df['carrier'] == tech][year].values[0]
#             else:
#                 marginal_cost = generator.get('marginal_cost', 0)

#             # Get lifetime
#             lifetime = generator.get('lifetime')
#             if pd.notnull(lifetime):
#                 lifetime_value = lifetime
#             logger.info(f"Added {generator['name']} existing generators")
#             # Add generator with all parameters
#             if generator.get('ramp_limit_up') is None:
#                 generator['ramp_limit_up'] = 1
#             if generator.get('ramp_limit_down') is None:
#                 generator['ramp_limit_down'] = 1
#             network.add("Generator",
#                 name=generator['name'],
#                 bus=generator['bus'],
#                 carrier=tech,
#                 p_nom=generator.get('p_nom', 0),
#                 p_nom_extendable=generator.get('p_nom_extendable', False),
#                 p_nom_min=generator.get('p_nom_min', 0),
#                 p_nom_max=generator.get('p_nom_max', float('inf')),
#                 p_min_pu=p_min_pu,
#                 p_max_pu=p_max_pu,
#                 marginal_cost=marginal_cost,
#                 capital_cost=capital_cost,
#                 efficiency=generator.get('efficiency', 1),
#                 build_year=generator.get('build_year', year),
#                 lifetime=lifetime_value,
#                 committable=generator.get('committable', False),
#                 start_up_cost=generator.get('start_up_cost', 0),
#                 shut_down_cost=generator.get('shut_down_cost', 0),
#                 min_up_time=generator.get('min_up_time', 0),
#                 min_down_time=generator.get('min_down_time', 0),
#                 ramp_limit_up=generator.get('ramp_limit_up', 1),
#                 ramp_limit_down=generator.get('ramp_limit_down', 1)
#             )
#             generators_added += 1

#     logger.info(f"Added {generators_added} existing generators")

def add_existing_generators(network, generators_df, year, P_max_pu_df, P_min_pu_df,
                           capital_cost_df, wacc_df, lifetime_df, FOM_df,
                           fuel_cost_df, capital_weighting, logger):
    """Add existing generators with all parameters"""
    logger.info(f"Adding existing generators for year {year}...")
    generators_added = 0

    # Helper functions to coerce/clean values
    def safe_int(val, default=0):
        try:
            # pd.isnull covers None, np.nan, etc.
            if pd.isnull(val):
                return int(default)
            return int(val)
        except Exception:
            return int(default)

    def safe_float(val, default=0.0):
        try:
            if pd.isnull(val):
                return float(default)
            return float(val)
        except Exception:
            return float(default)

    def safe_bool(val, default=False):
        try:
            if pd.isnull(val):
                return bool(default)
            return bool(val)
        except Exception:
            return bool(default)

    for tech in generators_df['carrier'].unique():
        tech_generators = generators_df[generators_df['carrier'] == tech]

        # Calculate capital cost
        if tech in capital_cost_df['carrier'].values:
            capital_cost_value = capital_cost_df[capital_cost_df['carrier'] == tech][year].values[0]
            wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05
            lifetime_value = lifetime_df[lifetime_df['carrier'] == tech]['lifetime'].values[0]
            fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0

            capital_cost = calculate_annualized_capital_cost(
                capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
            )
        else:
            capital_cost = 0
            lifetime_value = 25

        # Add each generator
        for idx, generator in tech_generators.iterrows():
            # Prepare time series
            if tech not in P_max_pu_df.columns:
                P_max_pu_df[tech] = 1
            if tech not in P_min_pu_df.columns:
                P_min_pu_df[tech] = 0

            # Handle location-specific profiles
            if generator.get('bus') == 'Outside Kerala':
                if tech in ['Solar', 'Wind']:
                    p_min_pu = [0] * len(network.snapshots)
                    col_name = f'{tech}_Outside' if f'{tech}_Outside' in P_max_pu_df.columns else tech
                    p_max_pu = P_max_pu_df[col_name][:len(network.snapshots)].to_list()
                else:
                    p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
                    p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()
            else:
                p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
                p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()

            # Get marginal cost
            if tech in fuel_cost_df['carrier'].values and year in fuel_cost_df.columns:
                marginal_cost = fuel_cost_df[fuel_cost_df['carrier'] == tech][year].values[0]
            else:
                marginal_cost = generator.get('marginal_cost', 0)

            # Lifetime override from generator row (if present and not null)
            gen_lifetime = generator.get('lifetime')
            if pd.notnull(gen_lifetime):
                lifetime_value = gen_lifetime

            # Defensive defaults & type coercion for fields that PyPSA expects as ints/floats/bools
            p_nom = safe_float(generator.get('p_nom', 0.0), 0.0)
            p_nom_extendable = safe_bool(generator.get('p_nom_extendable', False), False)
            p_nom_min = safe_float(generator.get('p_nom_min', 0.0), 0.0)

            # p_nom_max: allow inf (but coerce NaN to a large number or 0)
            p_nom_max_raw = generator.get('p_nom_max', float('inf'))
            if pd.isnull(p_nom_max_raw):
                p_nom_max = float('inf')
            else:
                try:
                    p_nom_max = float(p_nom_max_raw)
                except Exception:
                    p_nom_max = float('inf')

            # Costs / times: ensure ints / floats
            start_up_cost = safe_float(generator.get('start_up_cost', 0.0), 0.0)
            shut_down_cost = safe_float(generator.get('shut_down_cost', 0.0), 0.0)
            min_up_time = safe_int(generator.get('min_up_time', 0), 0)
            min_down_time = safe_int(generator.get('min_down_time', 0), 0)

            ramp_limit_up = safe_float(generator.get('ramp_limit_up', 1.0), 1.0)
            ramp_limit_down = safe_float(generator.get('ramp_limit_down', 1.0), 1.0)

            build_year = generator.get('build_year', year)
            if pd.isnull(build_year):
                build_year = year
            else:
                # if build_year should be int
                try:
                    build_year = int(build_year)
                except Exception:
                    build_year = year

            committable = safe_bool(generator.get('committable', False), False)

            # Add generator with all sanitized parameters
            network.add("Generator",
                name=generator.get('name'),
                bus=generator.get('bus'),
                carrier=tech,
                p_nom=p_nom,
                p_nom_extendable=p_nom_extendable,
                p_nom_min=p_nom_min,
                p_nom_max=p_nom_max,
                p_min_pu=p_min_pu,
                p_max_pu=p_max_pu,
                marginal_cost=marginal_cost,
                capital_cost=capital_cost,
                efficiency=safe_float(generator.get('efficiency', 1.0), 1.0),
                build_year=build_year,
                lifetime=safe_int(lifetime_value, 25),
                committable=committable,
                start_up_cost=start_up_cost,
                shut_down_cost=shut_down_cost,
                min_up_time=min_up_time,
                min_down_time=min_down_time,
                ramp_limit_up=ramp_limit_up,
                ramp_limit_down=ramp_limit_down
            )

            generators_added += 1
            logger.info(f"Added generator: {generator.get('name')}")

    logger.info(f"Added {generators_added} existing generators")

# def add_new_generators(network, new_generators_df, year, P_max_pu_df, P_min_pu_df,
#                        capital_cost_df, wacc_df, lifetime_df, FOM_df,
#                        capital_weighting, Pipe_Line_Generators_p_min_df, 
#                        Pipe_Line_Generators_p_max_df, logger):
#     """Add new generators for capacity expansion"""
#     generators_added = 0
    
#     for bus_name in new_generators_df['bus'].unique():
#         for tech in new_generators_df[new_generators_df['bus'] == bus_name]['carrier'].unique():
            
#             # Calculate capital cost
#             if tech in capital_cost_df[capital_cost_df['bus'] == bus_name]['carrier'].values:
#                 capital_cost_value = capital_cost_df[(capital_cost_df['carrier'] == tech) & 
#                                                     (capital_cost_df['bus'] == bus_name)][year].values[0]
#                 wacc_value = wacc_df[year].values[0]
#                 lifetime_value = lifetime_df[lifetime_df['carrier'] == tech]['lifetime'].values[0]
#                 fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0]
                
#                 capital_cost = calculate_annualized_capital_cost(
#                     capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
#                 )
#             else:
#                 capital_cost = 0
#                 lifetime_value = 25

#             # Get profiles
#             if tech not in P_max_pu_df.columns:
#                 P_max_pu_df[tech] = 1
#             if tech not in P_min_pu_df.columns:
#                 P_min_pu_df[tech] = 0

#             # Handle location-specific profiles
#             if bus_name == 'Outside Kerala':
#                 if tech in ['Solar', 'Wind']:
#                     p_min_pu = [0] * len(network.snapshots)
#                     col_name = f'{tech}_Outside' if f'{tech}_Outside' in P_max_pu_df.columns else tech
#                     p_max_pu = P_max_pu_df[col_name][:len(network.snapshots)].to_list()
#                 else:
#                     p_min_pu = [0] * len(network.snapshots)
#                     p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()
#             else:
#                 p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
#                 p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()

#             # Add each generator
#             for idx, generator in new_generators_df[(new_generators_df['carrier'] == tech) &
#                                                    (new_generators_df['bus'] == bus_name)].iterrows():
                
#                 # Get pipeline constraints
#                 pipeline_mask = (Pipe_Line_Generators_p_min_df["TECHNOLOGY"] == generator["TECHNOLOGY"]) & \
#                               (Pipe_Line_Generators_p_min_df["bus"] == bus_name)
                
#                 if pipeline_mask.any():
#                     p_nom_min = Pipe_Line_Generators_p_min_df[pipeline_mask][year].values[0]
#                 else:
#                     p_nom_min = 0
                    
#                 pipeline_mask_max = (Pipe_Line_Generators_p_max_df["TECHNOLOGY"] == generator["TECHNOLOGY"]) & \
#                                   (Pipe_Line_Generators_p_max_df["bus"] == bus_name)
                
#                 if pipeline_mask_max.any():
#                     p_nom_max = Pipe_Line_Generators_p_max_df[pipeline_mask_max][year].values[0]
#                 else:
#                     p_nom_max = generator.get('p_nom_max', float('inf'))

#                 network.add("Generator",
#                     f"{generator['TECHNOLOGY']}_{year}",
#                     bus=bus_name,
#                     carrier=tech,
#                     p_nom=0,
#                     p_nom_extendable=True,
#                     p_nom_min=p_nom_min,
#                     p_nom_max=p_nom_max,
#                     p_min_pu=p_min_pu,
#                     p_max_pu=p_max_pu,
#                     marginal_cost=generator.get('marginal_cost', 0),
#                     capital_cost=capital_cost,
#                     build_year=year,
#                     lifetime=lifetime_value
#                 )
#                 generators_added += 1
                
#                 logger.info(f"Added new generator: {tech} at {bus_name}, "
#                           f"p_nom_min={p_nom_min}, p_nom_max={p_nom_max}, capital_cost={capital_cost}")

#     return generators_added

def add_new_generators(network, new_generators_df, year, P_max_pu_df, P_min_pu_df,
                       capital_cost_df, wacc_df, lifetime_df, FOM_df,
                       capital_weighting, Pipe_Line_Generators_p_min_df, 
                       Pipe_Line_Generators_p_max_df, logger):
    """Add new generators for capacity expansion (defensive: unique names + sanitized inputs)"""
    generators_added = 0

    def safe_float(val, default=0.0):
        try:
            if pd.isnull(val):
                return float(default)
            return float(val)
        except Exception:
            return float(default)

    def safe_int(val, default=0):
        try:
            if pd.isnull(val):
                return int(default)
            return int(val)
        except Exception:
            return int(default)

    def safe_name(s: str) -> str:
        # sanitize to avoid spaces/special chars in index names
        if s is None:
            return ""
        return str(s).strip().replace(" ", "_").replace("/", "_")

    existing_names = set(network.generators.index) if hasattr(network, "generators") else set()

    for bus_name in new_generators_df['bus'].unique():
        for tech in new_generators_df[new_generators_df['bus'] == bus_name]['carrier'].unique():
            # Calculate capital cost
            cap_mask = (capital_cost_df['carrier'] == tech) & (capital_cost_df.get('bus', pd.Series()).fillna("").astype(str) == str(bus_name))
            if cap_mask.any():
                capital_cost_value = capital_cost_df[cap_mask][year].values[0]
                wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05
                lifetime_value = lifetime_df[lifetime_df['carrier'] == tech]['lifetime'].values[0]
                fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0
                capital_cost = calculate_annualized_capital_cost(
                    capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
                )
            else:
                capital_cost = 0
                lifetime_value = 25

            # Ensure profile columns exist
            if tech not in P_max_pu_df.columns:
                P_max_pu_df[tech] = 1
            if tech not in P_min_pu_df.columns:
                P_min_pu_df[tech] = 0

            # Handle location-specific profiles
            if bus_name == 'Outside Kerala':
                if tech in ['Solar', 'Wind']:
                    p_min_pu = [0] * len(network.snapshots)
                    col_name = f'{tech}_Outside' if f'{tech}_Outside' in P_max_pu_df.columns else tech
                    p_max_pu = P_max_pu_df[col_name][:len(network.snapshots)].to_list()
                else:
                    p_min_pu = [0] * len(network.snapshots)
                    p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()
            else:
                p_min_pu = P_min_pu_df[tech][:len(network.snapshots)].to_list()
                p_max_pu = P_max_pu_df[tech][:len(network.snapshots)].to_list()

            # Add each generator for this tech+bus
            subset = new_generators_df[(new_generators_df['carrier'] == tech) & (new_generators_df['bus'] == bus_name)]
            for idx, generator in subset.iterrows():
                # Pipeline constraints (safe lookup)
                pipeline_mask = (Pipe_Line_Generators_p_min_df.get("TECHNOLOGY", pd.Series()) == generator.get("TECHNOLOGY")) & \
                                (Pipe_Line_Generators_p_min_df.get("bus", pd.Series()) == bus_name)

                if pipeline_mask.any():
                    p_nom_min = safe_float(Pipe_Line_Generators_p_min_df[pipeline_mask][year].values[0], 0.0)
                else:
                    p_nom_min = 0.0

                pipeline_mask_max = (Pipe_Line_Generators_p_max_df.get("TECHNOLOGY", pd.Series()) == generator.get("TECHNOLOGY")) & \
                                    (Pipe_Line_Generators_p_max_df.get("bus", pd.Series()) == bus_name)

                if pipeline_mask_max.any():
                    p_nom_max = Pipe_Line_Generators_p_max_df[pipeline_mask_max][year].values[0]
                    # coerce to float or inf if NaN
                    p_nom_max = float(p_nom_max) if not pd.isnull(p_nom_max) else float('inf')
                else:
                    raw = generator.get('p_nom_max', float('inf'))
                    p_nom_max = float(raw) if (raw is not None and not pd.isnull(raw)) else float('inf')

                marginal_cost = generator.get('marginal_cost', 0)
                try:
                    marginal_cost = float(marginal_cost) if not pd.isnull(marginal_cost) else 0.0
                except Exception:
                    marginal_cost = 0.0

                # build a unique & sanitized name: TECHNOLOGY_YEAR_BUS[_counter]
                base_name = f"{safe_name(generator.get('TECHNOLOGY'))}_{safe_name(year)}_{safe_name(bus_name)}"
                gen_name = base_name
                counter = 1
                while gen_name in existing_names:
                    gen_name = f"{base_name}_{counter}"
                    counter += 1
                # Register in the set so next check knows it's taken
                existing_names.add(gen_name)

                # Use explicit keyword 'name=' when adding
                network.add("Generator",
                    name=gen_name,
                    bus=bus_name,
                    carrier=tech,
                    p_nom=0.0,
                    p_nom_extendable=True,
                    p_nom_min=p_nom_min,
                    p_nom_max=p_nom_max,
                    p_min_pu=p_min_pu,
                    p_max_pu=p_max_pu,
                    marginal_cost=marginal_cost,
                    capital_cost=capital_cost,
                    build_year=year,
                    lifetime=safe_int(lifetime_value, 25)
                )
                generators_added += 1

                logger.info(
                    f"Added new generator: name={gen_name}, tech={tech}, bus={bus_name}, "
                    f"p_nom_min={p_nom_min}, p_nom_max={p_nom_max}, capital_cost={capital_cost}"
                )

    return generators_added

def add_storage_components(network, storage_df, year, capital_cost_df, wacc_df,
                           lifetime_df, FOM_df, capital_weighting, 
                           pipe_line_storage_df, logger):
    """Add storage components (Stores and StorageUnits)"""
    storage_added = 0

    for idx, storage in storage_df.iterrows():
        tech = storage.get('TECHNOLOGY', storage.get('carrier', 'Storage'))
        storage_type = storage.get('Type', storage.get('TYPE', 'Store'))
        storage_name = storage.get('TECHNOLOGY', storage.get('NAME', f'storage_{idx}'))
        storage_bus = storage.get('bus', storage.get('BUS', 'Main_Bus'))

        # Calculate capital cost - Storage uses TECHNOLOGY column in capital_cost_df
        if tech in capital_cost_df['TECHNOLOGY'].values:
            capital_cost_value = capital_cost_df[capital_cost_df['TECHNOLOGY'] == tech][year].values[0]
            wacc_value = wacc_df[year].values[0] if year in wacc_df.columns else 0.05
            
            # Lifetime uses TECHNOLOGY column for storage
            if tech in lifetime_df['TECHNOLOGY'].values:
                lifetime_value = lifetime_df[lifetime_df['TECHNOLOGY'] == tech]['lifetime'].values[0]
            else:
                lifetime_value = 25
            
            # FOM uses carrier column
            fom_value = FOM_df[FOM_df['carrier'] == tech]['FOM'].values[0] if tech in FOM_df['carrier'].values else 0

            capital_cost = calculate_annualized_capital_cost(
                capital_cost_value, wacc_value, lifetime_value, fom_value, capital_weighting
            )
        else:
            capital_cost = 0
            lifetime_value = 25

        # Get pipeline constraints for storage
        pipeline_mask = (pipe_line_storage_df["TECHNOLOGY"] == storage_name) & \
                       (pipe_line_storage_df["bus"] == storage_bus)
        
        if pipeline_mask.any() and year in pipe_line_storage_df.columns:
            e_nom_min = pipe_line_storage_df[pipeline_mask][year].values[0]
        else:
            e_nom_min = 0

        if storage_type == 'Store':
            # Add Store (energy reservoir)
            network.add('Store',
                f"{storage_name}_{year}",
                bus=storage_bus,
                carrier=tech,
                e_nom=0,
                e_nom_extendable=True,
                e_nom_min=e_nom_min,
                e_nom_max=storage.get('e_nom_max', storage.get('E_NOM_MAX', float('inf'))),
                e_cyclic=True,
                capital_cost=capital_cost,
                build_year=year,
                lifetime=lifetime_value
            )
            logger.info(f"Added Store: {storage_name} at {storage_bus}, e_nom_min={e_nom_min}")
        else:
            # Add StorageUnit (power-based)
            network.add('StorageUnit',
                f"{storage_name}_{year}",
                bus=storage_bus,
                carrier=tech,
                p_nom=0,
                p_nom_extendable=True,
                p_nom_min=e_nom_min,  # Using e_nom_min as p_nom_min for StorageUnit
                p_nom_max=storage.get('p_nom_max', storage.get('P_NOM_MAX', float('inf'))),
                max_hours=storage.get('max_hours', storage.get('MAX_HOURS', 6)),
                efficiency_store=storage.get('efficiency_store', storage.get('EFFICIENCY_STORE', 0.9)),
                efficiency_dispatch=storage.get('efficiency_dispatch', storage.get('EFFICIENCY_DISPATCH', 0.9)),
                cyclic_state_of_charge=True,
                capital_cost=capital_cost,
                build_year=year,
                lifetime=lifetime_value
            )
            logger.info(f"Added StorageUnit: {storage_name} at {storage_bus}")

        storage_added += 1

    return storage_added


def add_links(network, links_df, settings_main, logger):
    """Add links to the network with storage charging/discharging constraints"""
    links_added = 0

    # Check storage charging/discharging settings
    storage_setting = settings_main[settings_main['Setting'] == 'Storage Charging/Discharging']['Option'].values
    solar_hours_constraint = len(storage_setting) > 0 and storage_setting[0] == 'Solar and Non solar hours'

    for idx, link in links_df.iterrows():
        link_name = link['name']

        # Handle storage charging/discharging constraints
        if link_name.startswith("invertor") and solar_hours_constraint:
            solar_hours_start = 10
            solar_hours_end = 17

            if link.get('type') == 'charging link':
                # Only allow charging during solar hours (10 AM - 5 PM)
                link_p_max = [1 if solar_hours_start <= ts.hour < solar_hours_end else 0
                             for ts in network.snapshots]
                link_p_min = 0
            else:
                # Only allow discharging outside solar hours
                link_p_max = [0 if solar_hours_start <= ts.hour < solar_hours_end else 1
                             for ts in network.snapshots]
                link_p_min = 0
        else:
            link_p_max = link.get('p_max_pu', 1)
            link_p_min = link.get('p_min_pu', 0)

        network.add('Link',
            link_name,
            bus0=link['bus0'],
            bus1=link['bus1'],
            p_nom=link.get('p_nom', 0),
            p_nom_extendable=link.get('p_nom_extendable', False),
            efficiency=link.get('efficiency', 1.0),
            p_max_pu=link_p_max,
            p_min_pu=link_p_min,
            marginal_cost=link.get('marginal_cost', 0),
            capital_cost=link.get('capital_cost', 0)
        )
        links_added += 1

    return links_added


def apply_committable_settings(network, Setting_df, logger):
    """Apply committable settings to generators"""
    settings_tables = extract_tables_by_markers(Setting_df, '~')
    committable_df = settings_tables.get('commitable')

    if committable_df is None:
        logger.warning("Committable settings table not found")
        return

    # Apply Yes settings
    yes_carriers = committable_df[committable_df['Option'] == 'Yes']['Carrier'].tolist()
    network.generators.loc[
        network.generators.carrier.isin(yes_carriers),
        'committable'
    ] = True

    # Apply No settings
    no_carriers = committable_df[committable_df['Option'] == 'No']['Carrier'].tolist()
    network.generators.loc[
        network.generators.carrier.isin(no_carriers),
        'committable'
    ] = False

    logger.info(f"Applied committable settings: {len(yes_carriers)} Yes, {len(no_carriers)} No")


# ============================================================================
# CONSTRAINT FUNCTIONS
# ============================================================================

def add_monthly_constraints(n, snapshots, Setting_df):
    """Add monthly generation constraints based on capacity factors"""
    m = n.model
    gen_p = m.variables["Generator-p"]
    
    # Extract settings
    settings_main = extract_tables_by_markers(Setting_df, '~').get('Main_Settings')
    if settings_main[settings_main['Setting'] == 'Monthly constraints']['Option'].values[0] != 'Yes':
        print("[INFO] Monthly constraints not enabled in settings.")
        return
    
    # Extract monthly constraints table
    monthly_constraints_df = extract_tables_by_markers(Setting_df, '~').get('Monthly_Constraints')
    if monthly_constraints_df is None:
        print("[WARNING] Monthly_Constraints table not found")
        return
    
    print("[INFO] Applying monthly generation constraints...")
    constraints_added = []
    
    # Process each carrier
    for carrier in n.generators.carrier.unique():
        if carrier not in monthly_constraints_df.columns:
            continue
            
        generator_names = n.generators[n.generators.carrier == carrier].index
        if len(generator_names) == 0:
            continue
        
        # Calculate total capacity
        if 'p_nom_opt' in n.generators.columns:
            total_capacity = n.generators[n.generators.carrier == carrier]['p_nom_opt'].sum()
        else:
            total_capacity = n.generators[n.generators.carrier == carrier]['p_nom'].sum()
        
        carrier_gen = gen_p.sel(Generator=generator_names)
        
        # Add monthly constraints
        for _, row in monthly_constraints_df.iterrows():
            month_num = int(row['Month'])
            capacity_factor = row[carrier]
            
            if pd.isna(capacity_factor) or capacity_factor == 0:
                continue
            
            # Get snapshots for this month
            month_snapshots = n.snapshots[n.snapshots.month == month_num]
            if len(month_snapshots) == 0:
                continue
            
            # Calculate limit and add constraint
            limit = capacity_factor * total_capacity * len(month_snapshots)
            carrier_gen_monthly = carrier_gen.sel(snapshot=month_snapshots)
            monthly_generation = carrier_gen_monthly.sum()
            
            constraint_name = f"{carrier}_monthly_CF{capacity_factor:.2f}_month{month_num:02d}"
            m.add_constraints(
                monthly_generation <= limit,
                name=constraint_name
            )
            constraints_added.append(constraint_name)
    
    print(f"[INFO] Added {len(constraints_added)} monthly constraints")


def add_battery_cycle_constraints(n, snapshots, Setting_df):
    """Add battery cycle constraints with simplified cycle counting"""
    m = n.model
    
    # Check if enabled
    settings_main = extract_tables_by_markers(Setting_df, '~').get('Main_Settings')
    if settings_main[settings_main['Setting'] == 'Battery Cycle']['Option'].values[0] != 'Yes':
        print("[INFO] Battery cycle constraints not enabled.")
        return
    
    if "Store-p" not in m.variables:
        print("[WARNING] No Store-p variable in model.")
        return
    
    store_p_vars = m.variables["Store-p"]
    
    # Get cycle configuration
    cycle_constraints_df = extract_tables_by_markers(Setting_df, '~').get('Battery_Cycle')
    if cycle_constraints_df is None:
        print("[WARNING] Battery_Cycle table not found")
        return
        
    cycle_type = cycle_constraints_df['Type'].iloc[0]
    num_cycles = int(cycle_constraints_df['No. of cycle'].iloc[0])
    
    # Calculate cycle length
    cycle_lengths = {'Daily': 24, 'Weekly': 168, 'Monthly': 720, 'Yearly': 8760}
    cycle_len = int(cycle_lengths.get(cycle_type, 168) / num_cycles)
    
    print(f"[INFO] Applying battery cycle constraints: {cycle_type}, {num_cycles} cycles, {cycle_len}h per cycle")
    
    # Apply constraints
    constraints_added = 0
    for start_idx in range(0, len(n.snapshots), cycle_len):
        end_idx = min(start_idx + cycle_len - 1, len(n.snapshots) - 1)
        if start_idx >= len(n.snapshots):
            break
            
        cycle_snapshots = n.snapshots[start_idx:end_idx+1]
        
        for store_name in n.stores.index:
            store_power_cycle = store_p_vars.sel(Store=store_name, snapshot=cycle_snapshots)
            e_capacity = n.stores.loc[store_name, 'e_nom']
            
            # Constrain net energy flow per cycle
            total_power = store_power_cycle.sum()
            
            m.add_constraints(
                total_power <= e_capacity,
                name=f"cycle_upper_{store_name}_{start_idx}"
            )
            m.add_constraints(
                total_power >= -e_capacity,
                name=f"cycle_lower_{store_name}_{start_idx}"
            )
            constraints_added += 2
    
    print(f"[INFO] Added {constraints_added} battery cycle constraints")


def add_ens_constraint(n, snapshots, ENS=0.0005):
    """Add Energy Not Served (ENS) constraint for Market generator"""
    m = n.model
    gen_p = m.variables["Generator-p"]
    
    market_generators = n.generators[n.generators.carrier == 'Market'].index
    if len(market_generators) == 0:
        print("[INFO] No Market generators found, skipping ENS constraint")
        return
    
    market_gen = gen_p.sel(Generator=market_generators)
    total_market_generation = market_gen.sum()
    total_demand = n.loads_t.p_set.sum().sum()
    limit = ENS * total_demand
    
    m.add_constraints(
        total_market_generation <= limit,
        name=f"Market_generation_limit_{ENS}"
    )
    print(f"[INFO] Added Market generation ENS limit: {limit:.2f} MW ({ENS*100:.2f}% of demand)")


def combined_constraints(n, snapshots, settings_main, Setting_df, logger):
    """Combined constraints function for optimization"""
    logger.info("Applying combined constraints...")
    
    # Add ENS constraint
    add_ens_constraint(n, snapshots)
    
    # Add monthly constraints if enabled
    if settings_main[settings_main['Setting'] == 'Monthly constraints']['Option'].values[0] == 'Yes':
        add_monthly_constraints(n, snapshots, Setting_df)
    
    # Add battery cycle constraints if enabled
    if settings_main[settings_main['Setting'] == 'Battery Cycle']['Option'].values[0] == 'Yes':
        add_battery_cycle_constraints(n, snapshots, Setting_df)
    
    logger.info("Constraints applied successfully")


# ============================================================================
# MODEL EXECUTION FUNCTIONS
# ============================================================================

def run_single_year_model(data, settings, config, output_folder, input_file_name, logger):
    """
    Run single-year dispatch model with two-stage optimization.
    """
    logger.info("=" * 80)
    logger.info("SINGLE-YEAR DISPATCH MODEL EXECUTION")
    logger.info("=" * 80)

    try:
        # Extract configuration
        year_list = settings['year_list']
        base_year = settings['base_year']
        snapshot_condition = settings['snapshot_condition']
        weightings = settings['weightings']
        capital_weighting = settings['capital_weighting']
        settings_main = settings['settings_main']

        scenario_name = config.get('scenarioName', 'scenario')
        solver_name = 'highs'  # Always use HIGHS solver

        logger.info(f"Processing {len(year_list)} years: {year_list}")
        logger.info(f"Base year: {base_year}")
        logger.info(f"Solver: {solver_name}")

        previous_year = None

        # Year-by-year loop
        for year_idx, year in enumerate(year_list):
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"PROCESSING YEAR {year_idx + 1}/{len(year_list)}: FY{year}")
            logger.info("=" * 80)

            # Generate snapshots
            snapshots_df, full_datetime_ranges = generate_snapshots_single_year(
                input_file_name, year, snapshot_condition, weightings, logger
            )

            # Prepare time series data
            P_max_pu_df, P_min_pu_df, demand_df = prepare_time_series_data(
                data['P_max_pu_df1'], data['P_min_pu_df1'], data['demand_df1'],
                year, full_datetime_ranges, snapshots_df, logger
            )

            # Create network
            logger.info("Initializing PyPSA network...")
            pypsa_model = pypsa.Network()
            pypsa_model.name = scenario_name
            pypsa_model.set_snapshots(snapshots_df)
            pypsa_model.snapshot_weightings = pd.Series(weightings, index=pypsa_model.snapshots)
            logger.info(f"Network created with {len(pypsa_model.snapshots)} snapshots")

            # Add buses
            add_buses_to_network(pypsa_model, data['buses_df'], logger)

            # Add load
            logger.info("Adding load demand...")
            demand_load = pd.DataFrame()
            demand_load['snapshot'] = pypsa_model.snapshots
            demand_load = demand_load.set_index('snapshot')
            demand_load['load'] = demand_df[year][:len(pypsa_model.snapshots)].to_list()
            pypsa_model.add("Load", "load", bus='Main_Bus', p_set=demand_load['load'])
            total_demand = demand_load['load'].sum()
            logger.info(f"Total demand: {total_demand:,.2f} MWh")

            # Load generators from base or previous year
            if year == base_year or previous_year is None:
                logger.info(f"Loading base generators for year {year}...")
                generators_df = data['generators_base_df'].copy()
            else:
                logger.info(f"Loading optimized generators from previous year {previous_year}...")
                # Create year folder name for previous results
                prev_results_folder = os.path.join(output_folder, f"{previous_year}")
                
                # Load previous generators
                prev_gen_file = os.path.join(prev_results_folder, "generators.csv")
                if os.path.exists(prev_gen_file):
                    generators_df = pd.read_csv(prev_gen_file)
                    # Update capacities from optimization
                    if 'p_nom_opt' in generators_df.columns:
                        generators_df.loc[generators_df['p_nom'] < generators_df['p_nom_opt'],
                                        'p_nom'] = generators_df['p_nom_opt']
                        generators_df = generators_df.drop('p_nom_opt', axis=1)
                    generators_df['p_nom_extendable'] = False
                    # Market generator remains extendable
                    generators_df.loc[generators_df['carrier'] == 'Market', 'p_nom_extendable'] = True
                    logger.info(f"Loaded {len(generators_df)} generators from previous year")
                    
                    # Also load stores if they exist
                    prev_store_file = os.path.join(prev_results_folder, "stores.csv")
                    if os.path.exists(prev_store_file):
                        existing_store_df = pd.read_csv(prev_store_file)
                        existing_store_df['e_nom_extendable'] = False
                        if 'e_nom_opt' in existing_store_df.columns:
                            existing_store_df.loc[existing_store_df['e_nom'] < existing_store_df['e_nom_opt'], 
                                                 'e_nom'] = existing_store_df['e_nom_opt']
                        stores_df_existing = existing_store_df.set_index('name')
                        pypsa_model.add('Store', stores_df_existing.index, **stores_df_existing)
                        logger.info(f"Loaded {len(existing_store_df)} stores from previous year")
                else:
                    logger.warning(f"Previous year results not found, using base generators")
                    generators_df = data['generators_base_df'].copy()

            # Add existing generators
            add_existing_generators(
                pypsa_model, generators_df, year,
                P_max_pu_df, P_min_pu_df,
                data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
                data['FOM_df'], data['fuel_cost_df'],
                capital_weighting, logger
            )

            # Add new generators (capacity expansion candidates)
            logger.info("Adding new generators for capacity expansion...")
            new_gens_added = add_new_generators(
                pypsa_model, data['new_generators_file_df'], year,
                P_max_pu_df, P_min_pu_df,
                data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
                data['FOM_df'], capital_weighting,
                data['Pipe_Line_Generators_p_min_df'], 
                data['Pipe_Line_Generators_p_max_df'], logger
            )
            logger.info(f"Added {new_gens_added} new generator candidates")

            # Add storage components
            logger.info("Adding storage components...")
            storage_added = add_storage_components(
                pypsa_model, data['New_Storage_df'], year,
                data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
                data['FOM_df'], capital_weighting, 
                data['pipe_line_storage_df'], logger
            )
            logger.info(f"Added {storage_added} storage units")

            # Add links
            logger.info("Adding links...")
            links_added = add_links(pypsa_model, data['links_df'], settings_main, logger)
            logger.info(f"Added {links_added} links")

            # Add carriers (CO2 emissions)
            logger.info("Adding carriers with CO2 emissions...")
            for idx, carrier in data['co2_df'].iterrows():
                pypsa_model.add('Carrier',
                    carrier['TECHNOLOGY'],
                    co2_emissions=carrier.get('tonnes/MWh', 0),
                    color=carrier.get('color', '#000000')
                )
            logger.info(f"Added {len(data['co2_df'])} carriers")

            # FIRST OPTIMIZATION: Capacity expansion
            logger.info("")
            logger.info("-" * 80)
            logger.info("STAGE 1: CAPACITY EXPANSION OPTIMIZATION")
            logger.info("-" * 80)

            log_file_path = os.path.join(output_folder, f'solver_log_{year}_stage1.log')
            solver_options = {}

            # Capture solver output
            with SolverOutputCapture(logger, log_file_path):
                status, condition = pypsa_model.optimize(solver_name=solver_name, solver_options=solver_options)

            if status == 'ok':
                logger.success(f"Stage 1 optimization completed: {condition}")
                logger.info(f"Objective value: {pypsa_model.objective:,.2f}")
            else:
                logger.error(f"Stage 1 optimization failed: {status} - {condition}")
                return {"success": False, "error": f"Optimization failed for year {year}: {condition}"}

            # Update capacities
            logger.info("Updating generator capacities from optimization results...")
            capacity_updates = 0
            if 'p_nom_opt' in pypsa_model.generators.columns:
                mask = pypsa_model.generators['p_nom'] < pypsa_model.generators['p_nom_opt']
                capacity_updates = mask.sum()
                pypsa_model.generators.loc[mask, 'p_nom'] = pypsa_model.generators.loc[mask, 'p_nom_opt']
                if capacity_updates > 0:
                    logger.info(f"Updated capacities for {capacity_updates} generators")

            # Update store capacities
            if 'e_nom_opt' in pypsa_model.stores.columns:
                mask = pypsa_model.stores['e_nom'] < pypsa_model.stores['e_nom_opt']
                store_updates = mask.sum()
                pypsa_model.stores.loc[mask, 'e_nom'] = pypsa_model.stores.loc[mask, 'e_nom_opt']
                if store_updates > 0:
                    logger.info(f"Updated capacities for {store_updates} stores")

            pypsa_model.generators['p_nom_extendable'] = False
            pypsa_model.generators.loc[pypsa_model.generators['carrier'] == 'Market', 'p_nom_extendable'] = True
            pypsa_model.stores['e_nom_extendable'] = False

            # Apply committable settings if enabled
            if settings_main[settings_main['Setting'] == 'Committable']['Option'].values[0] == 'Yes':
                logger.info("Applying committable constraints...")
                apply_committable_settings(pypsa_model, data['Setting_df'], logger)

            # SECOND OPTIMIZATION: Dispatch with constraints
            logger.info("")
            logger.info("-" * 80)
            logger.info("STAGE 2: DISPATCH OPTIMIZATION WITH CONSTRAINTS")
            logger.info("-" * 80)

            log_file_path = os.path.join(output_folder, f'solver_log_{year}_stage2.log')
            
            # Check if constraints are enabled
            monthly_enabled = settings_main[settings_main['Setting'] == 'Monthly constraints']['Option'].values
            battery_enabled = settings_main[settings_main['Setting'] == 'Battery Cycle']['Option'].values
            
            if (len(monthly_enabled) > 0 and monthly_enabled[0] == 'Yes') or \
               (len(battery_enabled) > 0 and battery_enabled[0] == 'Yes'):
                logger.info("Constraints enabled - will apply during optimization")
                extra_functionality = lambda n, snapshots: combined_constraints(
                    n, snapshots, settings_main, data['Setting_df'], logger
                )
            else:
                extra_functionality = None

            # Capture solver output
            with SolverOutputCapture(logger, log_file_path):
                status, condition = pypsa_model.optimize(
                    solver_name=solver_name,
                    solver_options=solver_options,
                    extra_functionality=extra_functionality
                )

            if status == 'ok':
                logger.success(f"Stage 2 optimization completed: {condition}")
                logger.info(f"Final objective value: {pypsa_model.objective:,.2f}")
            else:
                logger.error(f"Stage 2 optimization failed: {status} - {condition}")
                return {"success": False, "error": f"Dispatch optimization failed for year {year}: {condition}"}

            # Export results
            logger.info("")
            logger.info("Exporting results...")
            
            # Create year folder
            year_output_folder = os.path.join(output_folder, str(year))
            os.makedirs(year_output_folder, exist_ok=True)
            
            # Export to CSV in year folder
            pypsa_model.export_to_csv_folder(
                year_output_folder,
                encoding=None,
                export_standard_types=True
            )
            logger.info(f"Results exported to CSV: {year_output_folder}")

            # Export to NetCDF in main scenario folder
            nc_file = os.path.join(output_folder, f'{year}_network.nc')
            pypsa_model.export_to_netcdf(nc_file)
            logger.info(f"Network exported to NetCDF: {nc_file}")

            # Log summary statistics
            logger.info("")
            logger.info("Year Summary:")
            logger.info(f"  Total installed capacity: {pypsa_model.generators.p_nom.sum():,.2f} MW")
            if hasattr(pypsa_model.generators_t, 'p'):
                logger.info(f"  Total generation: {pypsa_model.generators_t.p.sum().sum():,.2f} MWh")
            logger.info(f"  System cost: {pypsa_model.objective:,.2f}")
            logger.success(f"Year {year} completed successfully")

            previous_year = year

        logger.info("")
        logger.info("=" * 80)
        logger.success("ALL YEARS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return {"success": True, "years_processed": len(year_list)}

    except Exception as e:
        logger.error(f"Single-year model execution failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


def generate_multiyear_snapshots(input_file_name, year_list, snapshot_condition, weightings, logger):
    """Generate snapshots for multiple years"""
    logger.info(f"Generating multi-year snapshots for {len(year_list)} years...")
    
    demand_df = pd.read_excel(input_file_name, sheet_name='Demand')
    
    def resample_and_average(df, freq_hours):
        """Resample dataframe to given frequency"""
        df = df.copy()
        df.index = pd.to_datetime(df['snapshots'])
        df = df.resample(f'{freq_hours}h').mean()
        df.dropna(inplace=True)
        df['snapshots'] = df.index
        return df.reset_index(drop=True)
    
    snapshots_list = []
    demand_series_list = []
    
    for fy in year_list:
        # Financial year: April to March
        start_dt = pd.Timestamp(fy-1, 4, 1, 0)
        end_dt = pd.Timestamp(fy, 3, 31, 23)
        period = pd.date_range(start=start_dt, end=end_dt, freq='h')
        
        series = demand_df[fy].iloc[:len(period)].reset_index(drop=True)
        
        # Trim for leap years
        period = period[12:-8] if len(period) > 8760 else period[:8760]
        series = series[12:-8] if len(series) > 8760 else series[:8760]
        
        snapshots_list.append(period)
        demand_series_list.append(series)
    
    # Concatenate all years
    all_snapshots = pd.DatetimeIndex(np.concatenate([idx.values for idx in snapshots_list]))
    all_demand = pd.concat(demand_series_list, ignore_index=True)
    
    # Build dataframe
    df = pd.DataFrame({
        'snapshots': all_snapshots,
        'demand': all_demand
    })
    df.set_index('snapshots', inplace=True)
    
    # Apply snapshot condition
    if snapshot_condition == 'All Snapshots':
        df_main = df
    elif snapshot_condition == 'Critical days':
        custom_days = pd.read_excel(input_file_name, sheet_name='Custom days')
        rng_list = []
        
        for fy in year_list:
            year_for_row = custom_days['Month'].apply(lambda m: fy if m <= 3 else fy-1)
            dates = pd.to_datetime({
                'year': year_for_row,
                'month': custom_days['Month'],
                'day': custom_days['Day']
            })
            
            for dt in sorted(dates.unique()):
                rng = pd.date_range(
                    start=dt,
                    end=dt + pd.DateOffset(days=1),
                    freq='h',
                    inclusive='left'
                )
                rng_list.append(rng)
        
        custom_index = pd.DatetimeIndex(np.concatenate([r.values for r in rng_list]))
        df_main = df[df.index.isin(custom_index)]
    else:  # Peak weeks
        df2 = df.copy()
        df2['year'] = df2.index.year
        df2['month'] = df2.index.month
        df2['week'] = df2.index.isocalendar().week
        
        peak_weeks = []
        for (_yr, _mo), grp in df2.groupby(['year', 'month']):
            wk_sums = grp.groupby('week')['demand'].sum()
            peak_wk = wk_sums.idxmax()
            peak_weeks.append(grp[grp['week'] == peak_wk])
        
        peak_df = pd.concat(peak_weeks)
        df_main = peak_df[['demand']]
    
    # Apply weightings if needed
    if weightings > 1:
        df_main = resample_and_average(df_main.reset_index(), weightings)
        df_main.set_index('snapshots', inplace=True)
    
    logger.info(f"Generated {len(df_main)} total snapshots across {len(year_list)} years")
    return df_main.index, df_main['demand']


def run_multi_year_model(data, settings, config, output_folder, input_file_name, logger):
    """
    Run multi-year capacity expansion model with investment periods.
    """
    logger.info("=" * 80)
    logger.info("MULTI-YEAR CAPACITY EXPANSION MODEL EXECUTION")
    logger.info("=" * 80)

    try:
        # Extract configuration
        year_list = settings['year_list']
        snapshot_condition = settings['snapshot_condition']
        weightings = settings['weightings']
        capital_weighting = settings['capital_weighting']
        settings_main = settings['settings_main']

        scenario_name = config.get('scenarioName', 'scenario')
        solver_name = 'highs'

        logger.info(f"Processing {len(year_list)} years: {year_list}")
        logger.info(f"Snapshot condition: {snapshot_condition}")
        logger.info(f"Solver: {solver_name}")

        # Generate multi-year snapshots
        logger.info("Generating multi-year snapshots...")
        all_snapshots, all_demand = generate_multiyear_snapshots(
            input_file_name, year_list, snapshot_condition, weightings, logger
        )

        # Create network
        logger.info("Initializing multi-year PyPSA network...")
        pypsa_model = pypsa.Network()
        pypsa_model.name = scenario_name

        # Set up multi-index snapshots for multi-period
        years = []
        for snapshot in all_snapshots:
            # Determine which financial year this snapshot belongs to
            if snapshot.month >= 4:  # April onwards
                years.append(snapshot.year + 1)
            else:  # January to March
                years.append(snapshot.year)
        
        pypsa_model.snapshots = pd.MultiIndex.from_arrays([years, all_snapshots], names=['period', 'timestep'])
        pypsa_model.investment_periods = year_list
        pypsa_model.snapshot_weightings = pd.Series(weightings, index=pypsa_model.snapshots)

        # Investment period weightings
        pypsa_model.investment_period_weightings["years"] = list(np.diff(year_list)) + [1]

        # Discount factors (1% discount rate)
        logger.info("Calculating investment period discount factors...")
        r = 0.01
        T = 0
        for period, nyears in pypsa_model.investment_period_weightings.years.items():
            discounts = [(1 / (1 + r) ** t) for t in range(T, T + nyears)]
            pypsa_model.investment_period_weightings.at[period, "objective"] = sum(discounts)
            T += nyears

        logger.info(f"Network created with {len(pypsa_model.snapshots)} total snapshots across {len(year_list)} periods")

        # Add buses
        add_buses_to_network(pypsa_model, data['buses_df'], logger)

        # Add load
        logger.info("Adding multi-year load demand...")
        pypsa_model.add("Load", "load", bus='Main_Bus', p_set=all_demand.values)
        logger.info(f"Total demand across all years: {all_demand.sum():,.2f} MWh")

        # Prepare multi-year time series
        logger.info("Preparing multi-year time series profiles...")
        P_max_pu_multi = pd.DataFrame()
        P_min_pu_multi = pd.DataFrame()
        
        for year in year_list:
            date_rng = pd.date_range(start=f"{year-1}-04-01", end=f"{year}-03-31 23:59:00", freq='h')
            P_max_pu = data['P_max_pu_df1'].iloc[:len(date_rng)].copy()
            P_min_pu = data['P_min_pu_df1'].iloc[:len(date_rng)].copy()
            P_max_pu_multi = pd.concat([P_max_pu_multi, P_max_pu], ignore_index=True)
            P_min_pu_multi = pd.concat([P_min_pu_multi, P_min_pu], ignore_index=True)

        # Add base generators
        logger.info("Adding base generators for multi-year model...")
        add_existing_generators(
            pypsa_model, data['generators_base_df'], year_list[0],
            P_max_pu_multi, P_min_pu_multi,
            data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
            data['FOM_df'], data['fuel_cost_df'],
            capital_weighting, logger
        )

        # Add new generators for each investment period
        logger.info("Adding new generators for each investment period...")
        total_new_gens = 0
        for year in year_list:
            new_gens = add_new_generators(
                pypsa_model, data['new_generators_file_df'], year,
                P_max_pu_multi, P_min_pu_multi,
                data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
                data['FOM_df'], capital_weighting,
                data['Pipe_Line_Generators_p_min_df'],
                data['Pipe_Line_Generators_p_max_df'], logger
            )
            total_new_gens += new_gens
        logger.info(f"Added {total_new_gens} new generator candidates across all periods")

        # Add storage for each period
        logger.info("Adding storage for each investment period...")
        total_storage = 0
        for year in year_list:
            storage = add_storage_components(
                pypsa_model, data['New_Storage_df'], year,
                data['capital_cost_df'], data['wacc_df'], data['lifetime_df'],
                data['FOM_df'], capital_weighting,
                data['pipe_line_storage_df'], logger
            )
            total_storage += storage
        logger.info(f"Added {total_storage} storage units across all periods")

        # Add links and carriers
        links_added = add_links(pypsa_model, data['links_df'], settings_main, logger)
        logger.info(f"Added {links_added} links")

        for idx, carrier in data['co2_df'].iterrows():
            pypsa_model.add('Carrier',
                carrier['TECHNOLOGY'],
                co2_emissions=carrier.get('tonnes/MWh', 0),
                color=carrier.get('color', '#000000')
            )

        # MULTI-YEAR OPTIMIZATION
        logger.info("")
        logger.info("-" * 80)
        logger.info("RUNNING MULTI-YEAR OPTIMIZATION")
        logger.info("-" * 80)

        log_file_path = os.path.join(output_folder, 'solver_log_multiyear.log')
        solver_options = {}

        logger.info("Starting multi-period optimization (this may take a while)...")

        # Capture solver output
        with SolverOutputCapture(logger, log_file_path):
            status, condition = pypsa_model.optimize(
                multi_investment_periods=True,
                solver_name=solver_name,
                solver_options=solver_options
            )

        if status == 'ok':
            logger.success(f"Multi-year optimization completed: {condition}")
            logger.info(f"Objective value: {pypsa_model.objective:,.2f}")
        else:
            logger.error(f"Multi-year optimization failed: {status} - {condition}")
            return {"success": False, "error": f"Multi-year optimization failed: {condition}"}

        # Export results
        logger.info("")
        logger.info("Exporting multi-year results...")
        
        # Export to CSV in main scenario folder
        pypsa_model.export_to_csv_folder(
            output_folder,
            encoding=None,
            export_standard_types=True
        )
        logger.info(f"Results exported to CSV: {output_folder}")

        # Export to NetCDF in main scenario folder
        nc_file = os.path.join(output_folder, f'{scenario_name}_multiyear.nc')
        pypsa_model.export_to_netcdf(nc_file)
        logger.info(f"Network exported to NetCDF: {nc_file}")

        logger.info("")
        logger.info("Multi-year Summary:")
        if 'p_nom_opt' in pypsa_model.generators.columns:
            logger.info(f"  Total installed capacity: {pypsa_model.generators.p_nom_opt.sum():,.2f} MW")
        logger.info(f"  System cost (NPV): {pypsa_model.objective:,.2f}")
        logger.success("Multi-year model completed successfully")

        return {"success": True, "years_processed": len(year_list)}

    except Exception as e:
        logger.error(f"Multi-year model execution failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


# ============================================================================
# MAIN ENTRY POINT (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    import sys
    
    class SimpleLogger:
        """Simple logger for testing"""
        def info(self, msg): print(f"[INFO] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
        def warning(self, msg): print(f"[WARNING] {msg}")
        def success(self, msg): print(f"[SUCCESS] {msg}")
        def log_buffer(self, msg): print(msg)
    
    if len(sys.argv) > 2:
        project_folder = sys.argv[1]
        scenario_name = sys.argv[2]
    else:
        print("Usage: python pypsa_model_executor_refined.py <project_folder> <scenario_name>")
        sys.exit(1)
    
    logger = SimpleLogger()
    result = run_pypsa_model_complete(project_folder, scenario_name, logger)
    
    if result['success']:
        print(f"\nModel execution completed successfully!")
        print(f"Results saved to: {result['output_folder']}")
        print(f"Execution time: {result['execution_time']}")
    else:
        print(f"\nModel execution failed: {result['error']}")