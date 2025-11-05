"""
PyPSA Visualization Routes - Consolidated
==========================================

Complete API endpoints for PyPSA network visualization and plotting.

Consolidates:
- pypsa_plot_routes.py (Plot generation with filters)

Features:
- Interactive Plotly-based visualizations
- Multiple plot types (dispatch, capacity, storage, transmission, prices)
- Customizable filters (resolution, date range, carriers)
- Export in multiple formats (HTML, PNG, PDF)
- Dynamic plot availability detection
- Memory-efficient rendering

Supported Plot Types:
- dispatch: Power system dispatch with generation and storage
- capacity: Installed capacity analysis by technology
- storage: Storage operation and state of charge
- transmission: Transmission line flows and utilization
- prices: Nodal electricity prices
- duration_curve: Load and generation duration curves
- daily_profile: Typical daily generation profiles
- dashboard: Comprehensive system overview

Version: 3.0 (Consolidated)
Date: 2025
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import tempfile
import pandas as pd

# Import models
import sys
sys.path.append(str(Path(__file__).parent.parent / "models"))

from models.pypsa_visualizer import PyPSAVisualizer
from models.pypsa_analyzer import load_network_cached

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST MODELS
# =============================================================================

class PlotFilters(BaseModel):
    """Filters for plot customization."""
    resolution: Optional[str] = Field("1H", description="Time resolution: 1H, 1D, 1W, 1M")
    start_date: Optional[str] = Field(None, description="Start date for filtering (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for filtering (YYYY-MM-DD)")
    carriers: Optional[List[str]] = Field(None, description="List of carriers to include")
    capacity_type: Optional[str] = Field("optimal", description="Capacity type: optimal, installed, both")
    plot_style: Optional[str] = Field("bar", description="Plot style: bar, pie, treemap")
    flow_type: Optional[str] = Field("heatmap", description="Flow visualization: heatmap, line, sankey")
    price_plot_type: Optional[str] = Field("line", description="Price plot type: line, heatmap, duration_curve")
    buses: Optional[List[str]] = Field(None, description="Specific buses for price plots")
    by_zone: bool = Field(False, description="Group by zone/region")
    stacked: bool = Field(True, description="Stack areas in dispatch plot")
    show_storage: bool = Field(True, description="Include storage in dispatch plot")
    show_load: bool = Field(True, description="Show load line in dispatch plot")
    period: Optional[int] = Field(None, description="Specific period for multi-period networks")
    year: Optional[int] = Field(None, description="Specific year for multi-period dispatch plots")


class PlotRequest(BaseModel):
    """Request model for plot generation using direct network path."""
    network_path: str = Field(..., description="Full path to network file")
    plot_type: str = Field(..., description="Type of plot to generate")
    filters: PlotFilters = Field(default_factory=PlotFilters, description="Plot filters")
    output_format: str = Field("html", description="Output format: html, png, pdf")


class NetworkPlotRequest(BaseModel):
    """Request model for plot generation using project path components."""
    projectPath: str = Field(..., description="Project root path")
    scenarioName: str = Field(..., description="Scenario name")
    networkFile: str = Field(..., description="Network filename")
    plot_type: str = Field(..., description="Type of plot to generate")
    filters: PlotFilters = Field(default_factory=PlotFilters, description="Plot filters")
    output_format: str = Field("html", description="Output format: html, png, pdf")


# =============================================================================
# PLOT GENERATION ENDPOINTS
# =============================================================================

@router.post("/pypsa/plot/generate")
async def generate_plot(request: PlotRequest):
    """
    Generate interactive PyPSA visualization plot.

    Supported plot types:
    - dispatch: Power system dispatch with storage and load
    - capacity: Installed capacity analysis
    - storage: Storage operation visualization
    - transmission: Transmission flow analysis
    - prices: Nodal price analysis
    - duration_curve: Load/price duration curves
    - daily_profile: Typical daily profiles

    Args:
        request: PlotRequest with network path, plot type, filters, and format

    Returns:
        dict: Response with plot content (HTML) or file path (PNG/PDF)
    """
    try:
        # Validate network file
        network_path = Path(request.network_path)
        if not network_path.exists():
            raise HTTPException(status_code=404, detail=f"Network file not found: {request.network_path}")
        
        if network_path.suffix != '.nc':
            raise HTTPException(status_code=400, detail="Only .nc files are supported")
        
        # Load network with caching
        logger.info(f"Loading network for plot generation: {network_path}")
        network = load_network_cached(str(network_path))
        
        # Create visualizer
        visualizer = PyPSAVisualizer(network)
        
        # Generate plot based on type
        logger.info(f"Generating {request.plot_type} plot")
        fig = _generate_plot_by_type(visualizer, request.plot_type, request.filters)
        
        if fig is None:
            raise HTTPException(status_code=500, detail="Failed to generate plot")
        
        # Export based on format
        if request.output_format == "html":
            html_content = fig.to_html(
                include_plotlyjs='cdn',
                config={'responsive': True, 'displayModeBar': True}
            )
            
            return {
                "success": True,
                "plot_type": request.plot_type,
                "format": "html",
                "content": html_content
            }
        
        elif request.output_format in ["png", "pdf"]:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.output_format}") as tmp:
                fig.write_image(tmp.name)
                
                return {
                    "success": True,
                    "plot_type": request.plot_type,
                    "format": request.output_format,
                    "file_path": tmp.name
                }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported output format: {request.output_format}")
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error generating plot: {error}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/pypsa/plot/available-years")
async def get_available_years(
    projectPath: str = Query(..., description="Project root path"),
    scenarioName: str = Query(..., description="Scenario name"),
    networkFile: str = Query(..., description="Network filename")
):
    """
    Get available years for multi-period dispatch plots.

    Args:
        projectPath: Project root directory
        scenarioName: Scenario folder name
        networkFile: Network filename

    Returns:
        dict: List of available years for multi-period networks
    """
    try:
        network_path = Path(projectPath) / "results" / "pypsa_optimization" / scenarioName / networkFile
        
        if not network_path.exists():
            raise HTTPException(status_code=404, detail=f"Network file not found: {networkFile}")
        
        network = load_network_cached(str(network_path))
        visualizer = PyPSAVisualizer(network)
        
        years = visualizer._get_available_years() if visualizer.is_multi_period else []
        
        return {
            "success": True,
            "is_multi_period": visualizer.is_multi_period,
            "available_years": years,
            "current_year": years[0] if years else None
        }
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error getting available years: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/pypsa/plot/dispatch-by-year")
async def generate_dispatch_by_year(request: NetworkPlotRequest):
    """
    Generate dispatch plot for multi-period networks with year selection.

    Filters dispatch plot to a specific year in multi-period networks.

    Args:
        request: NetworkPlotRequest with network details and filters
        
    Returns:
        dict: Response with plot content (HTML) or file path (PNG/PDF)
    """
    try:
        network_path = Path(request.projectPath) / "results" / "pypsa_optimization" / request.scenarioName / request.networkFile
        
        if not network_path.exists():
            raise HTTPException(status_code=404, detail=f"Network file not found: {network_path}")
        
        network = load_network_cached(str(network_path))
        visualizer = PyPSAVisualizer(network)
        
        logger.info(f"Generating dispatch plot by year for {request.scenarioName}")
        
        year = request.filters.year
        fig = visualizer.plot_dispatch_by_year(
            year=year,
            resolution=request.filters.resolution,
            start_date=request.filters.start_date,
            end_date=request.filters.end_date,
            carriers=request.filters.carriers,
            stacked=request.filters.stacked,
            show_storage=request.filters.show_storage,
            show_load=request.filters.show_load
        )
        
        if fig is None:
            raise HTTPException(status_code=500, detail="Failed to generate plot")
        
        if request.output_format == "html":
            html_content = fig.to_html(
                include_plotlyjs='cdn',
                config={'responsive': True, 'displayModeBar': True}
            )
            
            return {
                "success": True,
                "plot_type": "dispatch_by_year",
                "year": year,
                "format": "html",
                "content": html_content
            }
        
        elif request.output_format in ["png", "pdf"]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.output_format}") as tmp:
                fig.write_image(tmp.name)
                
                return {
                    "success": True,
                    "plot_type": "dispatch_by_year",
                    "year": year,
                    "format": request.output_format,
                    "file_path": tmp.name
                }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported output format: {request.output_format}")
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error generating dispatch plot by year: {error}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/pypsa/plot/generate-from-project")
async def generate_plot_from_project(request: NetworkPlotRequest):
    """
    Generate plot using project path and scenario/network names.

    Convenience endpoint that constructs the full network path from project components.

    Args:
        request: NetworkPlotRequest with project path, scenario, network file, plot type, and filters

    Returns:
        dict: Response with plot content (HTML) or file path (PNG/PDF)
    """
    try:
        # Construct network path
        network_path = Path(request.projectPath) / "results" / "pypsa_optimization" / request.scenarioName / request.networkFile
        
        if not network_path.exists():
            raise HTTPException(status_code=404, detail=f"Network file not found: {network_path}")
        
        # Create standard plot request
        plot_request = PlotRequest(
            network_path=str(network_path),
            plot_type=request.plot_type,
            filters=request.filters,
            output_format=request.output_format
        )
        
        # Use the standard plot generation endpoint
        return await generate_plot(plot_request)
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error generating plot from project: {error}")
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/pypsa/plot/availability")
async def get_plot_availability(
    projectPath: str = Query(..., description="Project root path"),
    scenarioName: str = Query(..., description="Scenario name"),
    networkFile: str = Query(..., description="Network filename")
):
    """
    Get available plot types for a network file.

    Inspects the network and returns which plot types can be generated
    based on available data.

    Args:
        projectPath: Project root directory
        scenarioName: Scenario folder name
        networkFile: Network filename

    Returns:
        dict: Available plot types with metadata, filters, and available carriers/buses
    """
    try:
        # Construct network path
        network_path = Path(projectPath) / "results" / "pypsa_optimization" / scenarioName / networkFile
        
        if not network_path.exists():
            raise HTTPException(status_code=404, detail=f"Network file not found: {networkFile}")
        
        # Load network
        network = load_network_cached(str(network_path))
        
        # Determine available plots
        availability = {
            "dispatch": {
                "available": _check_dispatch_availability(network),
                "description": "Power system dispatch with generation and storage",
                "filters": ["resolution", "carriers", "start_date", "end_date", "stacked", "show_storage", "show_load", "period"]
            },
            "capacity": {
                "available": _check_capacity_availability(network),
                "description": "Installed capacity by technology",
                "filters": ["capacity_type", "plot_style", "by_zone"]
            },
            "storage": {
                "available": _check_storage_availability(network),
                "description": "Storage operation and state of charge",
                "filters": ["resolution", "period"]
            },
            "transmission": {
                "available": _check_transmission_availability(network),
                "description": "Transmission line flows and utilization",
                "filters": ["resolution", "flow_type", "period"]
            },
            "prices": {
                "available": _check_prices_availability(network),
                "description": "Nodal electricity prices",
                "filters": ["resolution", "buses", "price_plot_type", "period"]
            },
            "duration_curve": {
                "available": _check_dispatch_availability(network),
                "description": "Load and generation duration curves",
                "filters": ["carriers"]
            },
            "daily_profile": {
                "available": _check_dispatch_availability(network),
                "description": "Typical daily generation and load profiles",
                "filters": ["carriers"]
            },
            "dashboard": {
                "available": _check_capacity_availability(network),
                "description": "Comprehensive system overview dashboard",
                "filters": []
            }
        }
        
        # Get available carriers for filtering
        carriers = []
        if hasattr(network, 'generators') and 'carrier' in network.generators.columns:
            carriers = sorted(network.generators.carrier.unique().tolist())
        
        # Get available buses for price filtering
        buses = []
        if hasattr(network, 'buses'):
            buses = network.buses.index.tolist()
        
        # Check if multi-period
        is_multi_period = isinstance(network.snapshots, pd.MultiIndex) if hasattr(network, 'snapshots') else False
        
        return {
            "success": True,
            "scenario": scenarioName,
            "network_file": networkFile,
            "plots": availability,
            "available_carriers": carriers,
            "available_buses": buses[:20],  # Limit to first 20 buses for performance
            "has_time_series": hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'),
            "is_multi_period": is_multi_period
        }
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error checking plot availability: {error}")
        raise HTTPException(status_code=500, detail=str(error))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _generate_plot_by_type(visualizer: PyPSAVisualizer, plot_type: str, filters: PlotFilters):
    """Generate plot based on type and filters."""
    
    if plot_type == "dispatch":
        return visualizer.plot_dispatch(
            resolution=filters.resolution,
            start_date=filters.start_date,
            end_date=filters.end_date,
            carriers=filters.carriers,
            stacked=filters.stacked,
            show_storage=filters.show_storage,
            show_load=filters.show_load,
            period=filters.period
        )
    
    elif plot_type == "capacity":
        # Map to visualizer method based on plot_style
        if filters.plot_style == "bar":
            return visualizer.plot_capacity_bar_chart(
                capacity_type=filters.capacity_type,
                carriers=filters.carriers
            )
        elif filters.plot_style == "pie":
            return visualizer.plot_capacity_pie_chart(
                capacity_type=filters.capacity_type,
                carriers=filters.carriers
            )
        else:
            raise ValueError(f"Unsupported capacity plot style: {filters.plot_style}")
    
    elif plot_type == "storage":
        return visualizer.plot_storage_operation(
            resolution=filters.resolution,
            period=filters.period
        )
    
    elif plot_type == "transmission":
        return visualizer.plot_transmission_flows(
            resolution=filters.resolution,
            period=filters.period
        )
    
    elif plot_type == "prices":
        return visualizer.plot_price_analysis(
            resolution=filters.resolution,
            buses=filters.buses,
            period=filters.period
        )
    
    elif plot_type == "duration_curve":
        return visualizer.plot_duration_curve(
            carriers=filters.carriers
        )
    
    elif plot_type == "daily_profile":
        return visualizer.plot_daily_profile(
            carriers=filters.carriers
        )
    
    elif plot_type == "dashboard":
        return visualizer.create_dashboard()
    
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")


def _check_dispatch_availability(network) -> bool:
    """Check if dispatch plot can be generated."""
    return (hasattr(network, 'generators_t') and
            hasattr(network.generators_t, 'p') and
            not network.generators_t.p.empty)


def _check_capacity_availability(network) -> bool:
    """Check if capacity plot can be generated."""
    if hasattr(network, 'generators') and not network.generators.empty:
        has_capacity = 'p_nom' in network.generators.columns or 'p_nom_opt' in network.generators.columns
        return has_capacity
    return False


def _check_storage_availability(network) -> bool:
    """Check if storage plot can be generated."""
    has_storage_units = (hasattr(network, 'storage_units') and
                        not network.storage_units.empty)
    has_stores = (hasattr(network, 'stores') and
                 not network.stores.empty)
    return has_storage_units or has_stores


def _check_transmission_availability(network) -> bool:
    """Check if transmission plot can be generated."""
    has_lines = (hasattr(network, 'lines_t') and
                hasattr(network.lines_t, 'p0') and
                not network.lines_t.p0.empty)
    has_links = (hasattr(network, 'links_t') and
                hasattr(network.links_t, 'p0') and
                not network.links_t.p0.empty)
    return has_lines or has_links


def _check_prices_availability(network) -> bool:
    """Check if price plot can be generated."""
    return (hasattr(network, 'buses_t') and
            hasattr(network.buses_t, 'marginal_price') and
            not network.buses_t.marginal_price.empty)


# =============================================================================
# DOWNLOAD ENDPOINTS
# =============================================================================

@router.get("/pypsa/plot/download/{filename}")
async def download_plot_file(filename: str):
    """
    Download a generated plot file.

    Args:
        filename: Temporary filename to download

    Returns:
        FileResponse: File for download
    """
    try:
        file_path = Path(tempfile.gettempdir()) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found or expired")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error downloading file: {error}")
        raise HTTPException(status_code=500, detail=str(error))


# =============================================================================
# BATCH PLOT GENERATION
# =============================================================================

@router.post("/pypsa/plot/generate-batch")
async def generate_batch_plots(
    projectPath: str = Body(...),
    scenarioName: str = Body(...),
    networkFile: str = Body(...),
    plot_types: List[str] = Body(..., description="List of plot types to generate"),
    filters: PlotFilters = Body(default_factory=PlotFilters),
    output_format: str = Body("html")
):
    """
    Generate multiple plots at once.

    Useful for creating a complete set of visualizations efficiently.

    Args:
        projectPath: Project root path
        scenarioName: Scenario name
        networkFile: Network filename
        plot_types: List of plot types to generate
        filters: Common filters for all plots
        output_format: Output format for all plots

    Returns:
        dict: Results for each plot type
    """
    try:
        # Construct network path
        network_path = Path(projectPath) / "results" / "pypsa_optimization" / scenarioName / networkFile
        
        if not network_path.exists():
            raise HTTPException(status_code=404, detail=f"Network file not found: {networkFile}")
        
        # Load network once
        network = load_network_cached(str(network_path))
        visualizer = PyPSAVisualizer(network)
        
        # Generate all plots
        results = {}
        for plot_type in plot_types:
            try:
                logger.info(f"Generating {plot_type} plot")
                fig = _generate_plot_by_type(visualizer, plot_type, filters)
                
                if fig is None:
                    results[plot_type] = {
                        "success": False,
                        "error": "Failed to generate plot"
                    }
                    continue
                
                # Export based on format
                if output_format == "html":
                    html_content = fig.to_html(
                        include_plotlyjs='cdn',
                        config={'responsive': True, 'displayModeBar': True}
                    )
                    results[plot_type] = {
                        "success": True,
                        "format": "html",
                        "content": html_content
                    }
                
                elif output_format in ["png", "pdf"]:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as tmp:
                        fig.write_image(tmp.name)
                        results[plot_type] = {
                            "success": True,
                            "format": output_format,
                            "file_path": tmp.name
                        }
            
            except Exception as plot_error:
                logger.error(f"Error generating {plot_type}: {plot_error}")
                results[plot_type] = {
                    "success": False,
                    "error": str(plot_error)
                }
        
        return {
            "success": True,
            "scenario": scenarioName,
            "network_file": networkFile,
            "plots_generated": len([r for r in results.values() if r.get("success")]),
            "plots_failed": len([r for r in results.values() if not r.get("success")]),
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error in batch plot generation: {error}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(error))