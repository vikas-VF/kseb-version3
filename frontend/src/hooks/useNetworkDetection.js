/**
 * Network Type Detection Hook
 * ============================
 *
 * Detects PyPSA network type using filename-based logic:
 * 1. Single .nc file WITH year → single-period
 * 2. Single .nc file WITHOUT year → check MultiIndex for multi-period
 * 3. Multiple .nc files with years → multi-file
 *
 * Returns:
 * - workflow_type: "single-period" | "multi-period" | "multi-file"
 * - periods: array of period IDs (for multi-period)
 * - years: array of years (for multi-file)
 * - ui_tabs: configuration for which tabs to show
 *
 * Usage:
 *   const { detection, loading, error } =
 *     useNetworkDetection(projectPath, scenario, network);
 */

import { useState, useEffect } from 'react';
import axios from 'axios';

const useNetworkDetection = (projectPath, scenarioName, networkFile) => {
  const [detection, setDetection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!projectPath || !scenarioName || !networkFile) {
      console.log('[useNetworkDetection] Missing required params, skipping detection');
      setDetection(null);
      return;
    }

    const detectNetworkType = async () => {
      console.log('[useNetworkDetection] Detecting network type for:', {
        projectPath,
        scenarioName,
        networkFile
      });

      setLoading(true);
      setError(null);

      try {
        const response = await axios.get('/project/pypsa/detect-network-type', {
          params: {
            projectPath,
            scenarioName,
            networkFile
          },
          timeout: 60000, // Increase to 60 seconds for large networks
          headers: {
            'Cache-Control': 'max-age=300' // Cache for 5 minutes
          }
        });

        console.log('[useNetworkDetection] Detection result:', response.data);

        if (response.data.success) {
          // Backend returns detection data directly in response.data, not nested under .detection
          setDetection(response.data);
        } else {
          const errorMsg = response.data.message || 'Failed to detect network type';
          console.error('[useNetworkDetection] Request failed:', errorMsg);
          setError(errorMsg);
        }
      } catch (err) {
        console.error('[useNetworkDetection] Error detecting network type:', err);

        let errorMsg = 'Failed to detect network type';

        if (err.response) {
          errorMsg = err.response.data?.detail || err.response.data?.message || errorMsg;
          console.error('[useNetworkDetection] Server error:', err.response.status, errorMsg);
        } else if (err.request) {
          errorMsg = 'No response from server. Please check if backend is running.';
          console.error('[useNetworkDetection] No response from server');
        } else if (err.code === 'ECONNABORTED') {
          errorMsg = 'Network detection timeout - assuming single period network';
          console.warn('[useNetworkDetection] Timeout error, assuming single period');
        } else {
          errorMsg = err.message || errorMsg;
          console.error('[useNetworkDetection] Request setup error:', err.message);
        }

        // Graceful fallback: assume single-period network if detection fails
        console.warn('[useNetworkDetection] Falling back to single-period assumption');
        setDetection({
          success: true,
          workflow_type: 'single-period',
          isSinglePeriod: true,
          isMultiPeriod: false,
          isMultiFile: false,
          message: 'Assumed single period (detection failed)',
          ui_tabs: ['Dispatch & Load', 'Capacity', 'Metrics', 'Storage', 'Emissions', 'Prices', 'Network Flow']
        });
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    detectNetworkType();
  }, [projectPath, scenarioName, networkFile]);

  return {
    detection,
    loading,
    error
  };
};

export default useNetworkDetection;
