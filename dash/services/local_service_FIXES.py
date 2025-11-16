"""
CRITICAL FIXES FOR local_service.py
====================================

This file contains the fixed methods to replace in local_service.py

FIXES INCLUDED:
1. Process cancellation implementation
2. Process tracking with timeout
3. Better error handling
4. State cleanup
5. User-friendly error messages

USAGE:
Copy these methods and replace the corresponding methods in local_service.py
"""

import os
import json
import subprocess
import threading
import queue
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# ERROR MESSAGE CATALOG
# =============================================================================

ERROR_MESSAGES = {
    'project_not_found': {
        'message': 'Project folder not found',
        'hint': 'Please check the project path and try again. Ensure the folder exists and you have permission to access it.'
    },
    'excel_file_missing': {
        'message': 'Required Excel file not found',
        'hint': 'Make sure input_demand_file.xlsx exists in the inputs/ folder.'
    },
    'forecast_failed': {
        'message': 'Forecasting process failed',
        'hint': 'Check the data quality and try again. Ensure all required columns are present.'
    },
    'insufficient_data': {
        'message': 'Not enough data for forecasting',
        'hint': 'At least 5 years of historical data are required for reliable forecasting.'
    },
    'pypsa_network_error': {
        'message': 'PyPSA network file could not be loaded',
        'hint': 'The .nc file may be corrupted. Try running the optimization again.'
    },
    'process_timeout': {
        'message': 'Process exceeded maximum runtime',
        'hint': 'The operation took too long and was terminated. Try reducing the data size or simplifying the configuration.'
    },
    'process_not_found': {
        'message': 'Process not found',
        'hint': 'The process may have already completed or been cancelled.'
    },
    'cancellation_failed': {
        'message': 'Failed to cancel process',
        'hint': 'The process may have already completed. Please check the results.'
    }
}

def format_error(error_key: str, technical_details: str = None) -> Dict:
    """
    Format user-friendly error message

    Args:
        error_key: Key from ERROR_MESSAGES dict
        technical_details: Optional technical error details

    Returns:
        Dict with success=False, error message, hint, and optional technical details
    """
    error_info = ERROR_MESSAGES.get(error_key, {
        'message': 'An error occurred',
        'hint': 'Please try again. If the problem persists, contact support.'
    })

    return {
        'success': False,
        'error': error_info['message'],
        'hint': error_info['hint'],
        'technical': technical_details if logger.isEnabledFor(logging.DEBUG) else None
    }


# =============================================================================
# PROCESS TRACKING GLOBALS (ADD TO TOP OF LOCAL_SERVICE.PY)
# =============================================================================

# These replace the existing simple dicts
forecast_processes = {}  # {process_id: {'process': Popen, 'timer': Timer, 'start_time': datetime, 'config': Dict}}
profile_processes = {}   # Same structure
pypsa_processes = {}     # Same structure

# Existing queues (keep as is)
forecast_sse_queue = queue.Queue()
pypsa_solver_sse_queue = queue.Queue()


# =============================================================================
# FIXED METHOD #1: cancel_forecast
# =============================================================================

def cancel_forecast(self, process_id: str) -> Dict:
    """
    Cancel forecasting process (FIXED VERSION)

    Args:
        process_id: Process identifier

    Returns:
        Dict with success status and message
    """
    global forecast_processes

    if process_id not in forecast_processes:
        return format_error('process_not_found', f'Process ID: {process_id}')

    proc_info = forecast_processes[process_id]
    process = proc_info['process']

    try:
        # Check if already finished
        if process.poll() is not None:
            # Already finished
            cleanup_process(process_id, 'forecast')
            return {
                'success': True,
                'message': 'Process already completed'
            }

        logger.info(f"Cancelling forecast process: {process_id}")

        # Try graceful termination first
        process.terminate()

        # Wait up to 5 seconds for graceful shutdown
        try:
            process.wait(timeout=5)
            logger.info(f"Process {process_id} terminated gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if not terminated
            logger.warning(f"Process {process_id} did not terminate gracefully, forcing kill")
            process.kill()
            process.wait()
            logger.info(f"Process {process_id} killed")

        # Send cancellation event to SSE queue
        forecast_sse_queue.put({
            'type': 'end',
            'status': 'cancelled',
            'message': 'Forecasting cancelled by user',
            'timestamp': datetime.now().isoformat()
        })

        # Cleanup
        cleanup_process(process_id, 'forecast')

        return {
            'success': True,
            'message': 'Forecasting cancelled successfully'
        }

    except Exception as e:
        logger.error(f"Error cancelling forecast: {e}")
        return format_error('cancellation_failed', str(e))


# =============================================================================
# FIXED METHOD #2: cancel_profile_generation
# =============================================================================

def cancel_profile_generation(self, process_id: str) -> Dict:
    """
    Cancel load profile generation process (NEW METHOD)

    Args:
        process_id: Process identifier

    Returns:
        Dict with success status and message
    """
    global profile_processes

    if process_id not in profile_processes:
        return format_error('process_not_found', f'Process ID: {process_id}')

    proc_info = profile_processes[process_id]
    process = proc_info['process']

    try:
        # Check if already finished
        if process.poll() is not None:
            cleanup_process(process_id, 'profile')
            return {
                'success': True,
                'message': 'Process already completed'
            }

        logger.info(f"Cancelling profile generation process: {process_id}")

        # Try graceful termination
        process.terminate()

        try:
            process.wait(timeout=5)
            logger.info(f"Process {process_id} terminated gracefully")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            logger.info(f"Process {process_id} killed")

        # Cleanup
        cleanup_process(process_id, 'profile')

        return {
            'success': True,
            'message': 'Profile generation cancelled successfully'
        }

    except Exception as e:
        logger.error(f"Error cancelling profile generation: {e}")
        return format_error('cancellation_failed', str(e))


# =============================================================================
# FIXED METHOD #3: cancel_pypsa_model
# =============================================================================

def cancel_pypsa_model(self, process_id: str) -> Dict:
    """
    Cancel PyPSA optimization process (NEW METHOD)

    Args:
        process_id: Process identifier

    Returns:
        Dict with success status and message
    """
    global pypsa_processes

    if process_id not in pypsa_processes:
        return format_error('process_not_found', f'Process ID: {process_id}')

    proc_info = pypsa_processes[process_id]
    process = proc_info['process']

    try:
        # Check if already finished
        if process.poll() is not None:
            cleanup_process(process_id, 'pypsa')
            return {
                'success': True,
                'message': 'Process already completed'
            }

        logger.info(f"Cancelling PyPSA optimization process: {process_id}")

        # Try graceful termination
        process.terminate()

        try:
            process.wait(timeout=5)
            logger.info(f"Process {process_id} terminated gracefully")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            logger.info(f"Process {process_id} killed")

        # Send cancellation event to SSE queue
        pypsa_solver_sse_queue.put({
            'type': 'end',
            'status': 'cancelled',
            'message': 'PyPSA optimization cancelled by user',
            'timestamp': datetime.now().isoformat()
        })

        # Cleanup
        cleanup_process(process_id, 'pypsa')

        return {
            'success': True,
            'message': 'PyPSA optimization cancelled successfully'
        }

    except Exception as e:
        logger.error(f"Error cancelling PyPSA model: {e}")
        return format_error('cancellation_failed', str(e))


# =============================================================================
# NEW METHOD #4: cleanup_process
# =============================================================================

def cleanup_process(process_id: str, process_type: str):
    """
    Clean up process state after completion/error/cancellation

    Args:
        process_id: Process identifier
        process_type: Type of process ('forecast', 'profile', 'pypsa')
    """
    global forecast_processes, profile_processes, pypsa_processes

    try:
        if process_type == 'forecast':
            if process_id in forecast_processes:
                proc_info = forecast_processes[process_id]

                # Cancel watchdog timer if exists
                if 'timer' in proc_info and proc_info['timer']:
                    proc_info['timer'].cancel()

                # Remove from tracking
                del forecast_processes[process_id]
                logger.info(f"Cleaned up forecast process: {process_id}")

        elif process_type == 'profile':
            if process_id in profile_processes:
                proc_info = profile_processes[process_id]

                # Cancel watchdog timer if exists
                if 'timer' in proc_info and proc_info['timer']:
                    proc_info['timer'].cancel()

                del profile_processes[process_id]
                logger.info(f"Cleaned up profile process: {process_id}")

        elif process_type == 'pypsa':
            if process_id in pypsa_processes:
                proc_info = pypsa_processes[process_id]

                # Cancel watchdog timer if exists
                if 'timer' in proc_info and proc_info['timer']:
                    proc_info['timer'].cancel()

                del pypsa_processes[process_id]
                logger.info(f"Cleaned up PyPSA process: {process_id}")

    except Exception as e:
        logger.error(f"Error during cleanup of {process_type} process {process_id}: {e}")


# =============================================================================
# NEW METHOD #5: create_process_with_timeout
# =============================================================================

def create_process_with_timeout(cmd: list, process_id: str, process_type: str,
                                config: Dict, timeout_seconds: int = 3600) -> subprocess.Popen:
    """
    Create subprocess with watchdog timeout

    Args:
        cmd: Command list for Popen
        process_id: Unique process identifier
        process_type: 'forecast', 'profile', or 'pypsa'
        config: Process configuration dict
        timeout_seconds: Maximum runtime (default 3600 = 1 hour)

    Returns:
        subprocess.Popen object
    """
    global forecast_processes, profile_processes, pypsa_processes

    # Start subprocess
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )

    # Create watchdog timer
    def timeout_handler():
        """Handler called if process exceeds timeout"""
        if process.poll() is None:  # Still running
            logger.warning(f"Process {process_id} ({process_type}) timed out after {timeout_seconds}s, terminating...")

            try:
                process.kill()

                # Send timeout error to appropriate queue
                error_event = {
                    'type': 'error',
                    'status': 'timeout',
                    'message': f'Process exceeded timeout of {timeout_seconds} seconds and was terminated',
                    'timestamp': datetime.now().isoformat()
                }

                if process_type == 'forecast':
                    forecast_sse_queue.put(error_event)
                elif process_type == 'pypsa':
                    pypsa_solver_sse_queue.put(error_event)

            except Exception as e:
                logger.error(f"Error in timeout handler: {e}")

    timer = threading.Timer(timeout_seconds, timeout_handler)
    timer.start()

    # Store process info
    proc_info = {
        'process': process,
        'timer': timer,
        'start_time': datetime.now(),
        'config': config,
        'timeout': timeout_seconds
    }

    if process_type == 'forecast':
        forecast_processes[process_id] = proc_info
    elif process_type == 'profile':
        profile_processes[process_id] = proc_info
    elif process_type == 'pypsa':
        pypsa_processes[process_id] = proc_info

    return process


# =============================================================================
# EXAMPLE: How to use in run_forecast method
# =============================================================================

def example_run_forecast(self, config: Dict) -> Dict:
    """
    Example of how to modify existing run_forecast method to use new features

    REPLACE YOUR EXISTING run_forecast WITH THIS PATTERN
    """
    try:
        # Generate unique process ID
        process_id = f"forecast_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Prepare command
        models_path = os.path.join(os.path.dirname(__file__), '..', 'models')
        forecasting_script = os.path.join(models_path, 'forecasting.py')

        cmd = [
            'python',
            forecasting_script,
            '--config', json.dumps(config)
        ]

        # Create process with timeout (1 hour = 3600 seconds)
        process = create_process_with_timeout(
            cmd=cmd,
            process_id=process_id,
            process_type='forecast',
            config=config,
            timeout_seconds=3600
        )

        # Start monitoring thread
        def monitor_process():
            """Monitor process output and send to SSE queue"""
            try:
                for line in process.stdout:
                    if line.startswith('PROGRESS:'):
                        try:
                            progress_data = json.loads(line[9:])
                            forecast_sse_queue.put(progress_data)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid progress JSON: {line}")

                # Wait for process to complete
                return_code = process.wait()

                # Send completion event
                if return_code == 0:
                    forecast_sse_queue.put({
                        'type': 'end',
                        'status': 'completed',
                        'message': 'Forecasting completed successfully'
                    })
                else:
                    forecast_sse_queue.put({
                        'type': 'error',
                        'status': 'failed',
                        'message': f'Forecasting failed with return code {return_code}'
                    })

                # Cleanup
                cleanup_process(process_id, 'forecast')

            except Exception as e:
                logger.error(f"Error in monitoring thread: {e}")
                forecast_sse_queue.put({
                    'type': 'error',
                    'status': 'error',
                    'message': f'Monitoring error: {str(e)}'
                })
                cleanup_process(process_id, 'forecast')

        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()

        return {
            'success': True,
            'process_id': process_id,
            'message': 'Forecasting started'
        }

    except Exception as e:
        logger.error(f"Error starting forecast: {e}")
        return format_error('forecast_failed', str(e))


# =============================================================================
# SUMMARY OF CHANGES NEEDED IN local_service.py
# =============================================================================

"""
STEP 1: Add ERROR_MESSAGES dict and format_error() function to the top

STEP 2: Replace global process tracking dicts with enhanced versions

STEP 3: Add these new methods to LocalService class:
   - cleanup_process()
   - create_process_with_timeout()
   - cancel_forecast() [REPLACE existing]
   - cancel_profile_generation() [NEW]
   - cancel_pypsa_model() [NEW]

STEP 4: Modify existing process execution methods to use:
   - create_process_with_timeout() instead of subprocess.Popen()
   - cleanup_process() on completion/error
   - format_error() for all error returns

STEP 5: Add process monitoring with proper cleanup in all execution methods
"""
