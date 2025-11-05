/**
 * Enhanced PyPSA Availability Hook
 * =================================
 *
 * Fetches network availability and capabilities with improved detection.
 * Provides helper functions for checking what analyses are available.
 *
 * CRITICAL: This hook fetches data from `/project/pypsa/availability` endpoint
 * which returns BOTH flat boolean flags (for frontend requirements checking)
 * AND nested detailed structures (for backward compatibility).
 *
 * Backend Returns (after fix):
 * {
 *   // Flat flags (used by frontend for analysis availability)
 *   has_generators: bool,
 *   has_storage_units: bool,
 *   has_stores: bool,
 *   has_loads: bool,
 *   has_lines: bool,
 *   has_buses: bool,
 *   has_carriers: bool,
 *   is_solved: bool,
 *   has_emissions_data: bool,
 *
 *   // Flat arrays (used for filters)
 *   carriers: [],
 *   technologies: [],
 *   regions: [],
 *   zones: [],
 *   buses: [],
 *   sectors: [],
 *   years: [],
 *
 *   // Nested structures (detailed info)
 *   basic_info: {...},
 *   components: {...},
 *   time_series: {...},
 *   spatial_info: {...},
 *   available_analyses: [...],
 *   available_visualizations: {...}
 * }
 *
 * Usage:
 *   const { availability, loading, error, canAnalyze, getDynamicFilters } =
 *     usePyPSAAvailability(projectPath, scenario, network);
 */

import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

const usePyPSAAvailability = (projectPath, scenarioName, networkFile) => {
  const [availability, setAvailability] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!projectPath || !scenarioName || !networkFile) {
      console.log('[usePyPSAAvailability] Missing required params, skipping fetch');
      setAvailability(null);
      return;
    }

    const fetchAvailability = async () => {
      console.log('[usePyPSAAvailability] Fetching availability for:', {
        projectPath,
        scenarioName,
        networkFile
      });

      setLoading(true);
      setError(null);

      try {
        const response = await axios.get('/project/pypsa/availability', {
          params: {
            projectPath,
            scenarioName,
            networkFile
          },
          timeout: 30000 // 30 second timeout for large networks
        });

        console.log('[usePyPSAAvailability] Response received:', response.data);

        if (response.data.success) {
          const availabilityData = response.data.availability;

          // Validate that required fields exist
          const requiredFields = [
            'has_generators', 'has_storage_units', 'has_stores', 'has_loads',
            'has_lines', 'has_buses', 'is_solved', 'carriers'
          ];

          const missingFields = requiredFields.filter(field => !(field in availabilityData));
          if (missingFields.length > 0) {
            console.warn('[usePyPSAAvailability] Missing fields in availability response:', missingFields);
          }

          // Log key availability flags for debugging
          console.log('[usePyPSAAvailability] Availability flags:', {
            has_generators: availabilityData.has_generators,
            has_storage_units: availabilityData.has_storage_units,
            has_stores: availabilityData.has_stores,
            has_loads: availabilityData.has_loads,
            has_lines: availabilityData.has_lines,
            has_buses: availabilityData.has_buses,
            is_solved: availabilityData.is_solved,
            has_emissions_data: availabilityData.has_emissions_data,
            carriers_count: availabilityData.carriers?.length || 0,
            available_analyses_count: availabilityData.available_analyses?.length || 0
          });

          setAvailability(availabilityData);
        } else {
          const errorMsg = response.data.message || 'Failed to fetch availability';
          console.error('[usePyPSAAvailability] Request failed:', errorMsg);
          setError(errorMsg);
        }
      } catch (err) {
        console.error('[usePyPSAAvailability] Error fetching availability:', err);

        // Provide detailed error message
        let errorMsg = 'Failed to fetch network availability';

        if (err.response) {
          // Server responded with error
          errorMsg = err.response.data?.detail || err.response.data?.message || errorMsg;
          console.error('[usePyPSAAvailability] Server error:', err.response.status, errorMsg);
        } else if (err.request) {
          // No response received
          errorMsg = 'No response from server. Please check if backend is running.';
          console.error('[usePyPSAAvailability] No response from server');
        } else {
          // Request setup error
          errorMsg = err.message || errorMsg;
          console.error('[usePyPSAAvailability] Request setup error:', err.message);
        }

        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    fetchAvailability();
  }, [projectPath, scenarioName, networkFile]);
  
  /**
   * Check if specific analysis can be performed
   */
  const canAnalyze = useMemo(() => {
    return (analysisType) => {
      if (!availability) return false;
      
      switch (analysisType) {
        case 'total_capacities':
        case 'capacity':
          return availability.has_generators;
          
        case 'energy_mix':
          return availability.has_generators && availability.is_solved;
          
        case 'capacity_factors':
        case 'cuf':
          return availability.has_generators && availability.is_solved;
          
        case 'renewable_share':
          return availability.has_generators;
          
        case 'emissions':
          return availability.has_generators && availability.has_emissions_data;
          
        case 'system_costs':
        case 'costs':
          return availability.has_generators;
          
        case 'storage_units':
          return availability.has_storage_units;
          
        case 'stores':
        case 'bess':
          return availability.has_stores;
          
        case 'lines':
        case 'transmission':
          return availability.has_lines;
          
        case 'loads':
        case 'demand':
          return availability.has_loads;
          
        case 'buses':
          return availability.has_buses;
          
        case 'carriers':
          return availability.has_carriers;
          
        case 'utilization':
          return availability.has_generators && availability.is_solved;
          
        default:
          return true; // Unknown analysis, assume available
      }
    };
  }, [availability]);
  
  /**
   * Check if component can be shown
   */
  const canShow = useMemo(() => {
    return (componentType) => {
      if (!availability) return false;
      
      switch (componentType) {
        case 'generators':
          return availability.has_generators;
        case 'storage':
          return availability.has_storage_units || availability.has_stores;
        case 'transmission':
          return availability.has_lines;
        case 'loads':
          return availability.has_loads;
        case 'buses':
          return availability.has_buses;
        default:
          return true;
      }
    };
  }, [availability]);
  
  /**
   * Get dynamic filter options from availability
   */
  const getDynamicFilters = useMemo(() => {
    return () => {
      if (!availability) {
        return {
          carriers: [],
          technologies: [],
          regions: [],
          zones: [],
          sectors: []
        };
      }
      
      return {
        carriers: availability.carriers || [],
        technologies: availability.technologies || [],
        regions: availability.regions || [],
        zones: availability.zones || [],
        sectors: availability.sectors || [],
        buses: availability.buses || [],
        years: availability.years || []
      };
    };
  }, [availability]);
  
  /**
   * Get network type information
   */
  const networkType = useMemo(() => {
    if (!availability) return null;
    
    return {
      isMultiPeriod: availability.is_multi_period || false,
      isMultiFile: availability.is_multi_file || false,
      isSinglePeriod: !availability.is_multi_period && !availability.is_multi_file,
      periods: availability.periods || [],
      files: availability.files || []
    };
  }, [availability]);
  
  return {
    availability,
    loading,
    error,
    canAnalyze,
    canShow,
    getDynamicFilters,
    networkType
  };
};

export default usePyPSAAvailability;