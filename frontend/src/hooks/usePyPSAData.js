/**
 * Optimized PyPSA Data Hook - Version 2.0
 * ========================================
 *
 * Enhanced custom hook for fetching PyPSA analysis data with intelligent
 * network type detection and optimized data fetching strategies.
 *
 * Features:
 * - Automatic network type detection (single/multi-period/multi-file)
 * - Intelligent request queuing with priority support
 * - Response size optimization with smart defaults
 * - Multi-level caching (memory + HTTP)
 * - Performance metrics tracking
 * - Retry logic with exponential backoff
 * - Request deduplication
 * - Automatic request abortion on unmount
 * - Period-specific data fetching for multi-period networks
 *
 * Supports:
 * - Single network analysis
 * - Multi-period networks (single file, multiple investment periods)
 * - Multi-file networks (multiple year files)
 *
 * @version 2.0
 * @date 2025-01-03
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import axios from 'axios';

// ============================================================================
// CONSTANTS & CONFIGURATION
// ============================================================================

const CONFIG = {
  MAX_CONCURRENT_REQUESTS: 1,        // Only 1 request at a time to prevent flooding
  REQUEST_DELAY: 300,                // Delay between requests (300ms)
  RETRY_ATTEMPTS: 0,                 // No retries to avoid request multiplication
  RETRY_DELAY: 1000,                 // Initial retry delay (ms)
  CACHE_DURATION: 300000,            // 5 minutes in milliseconds
  REQUEST_TIMEOUT: 30000,            // 30 seconds timeout
  DEDUP_WINDOW: 5000,                // 5 second deduplication window
};

// Priority levels for request queuing
const PRIORITY = {
  HIGH: 1,    // Critical data (overview, availability checks)
  NORMAL: 2,  // Regular analysis data
  LOW: 3,     // Large datasets, visualizations
};

// Network type detection cache
const networkTypeCache = new Map();

// Request deduplication cache
const requestCache = new Map();

// ============================================================================
// GLOBAL REQUEST QUEUE (Priority-based)
// ============================================================================

class PriorityRequestQueue {
  constructor() {
    this.queue = [];
    this.activeRequests = 0;
    this.maxConcurrent = CONFIG.MAX_CONCURRENT_REQUESTS;
    this.requestDelay = CONFIG.REQUEST_DELAY;
    this.processing = false;
  }

  async enqueue(requestFn, priority = PRIORITY.NORMAL) {
    return new Promise((resolve, reject) => {
      this.queue.push({ requestFn, resolve, reject, priority, timestamp: Date.now() });
      // Sort queue by priority
      this.queue.sort((a, b) => a.priority - b.priority);
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.processing) return;
    this.processing = true;

    while (this.queue.length > 0 && this.activeRequests < this.maxConcurrent) {
      const item = this.queue.shift();
      if (!item) break;

      this.activeRequests++;

      // Execute request
      (async () => {
        try {
          const result = await item.requestFn();
          item.resolve(result);
        } catch (error) {
          item.reject(error);
        } finally {
          this.activeRequests--;
          // Add delay before processing next if queue has items
          if (this.queue.length > 0) {
            setTimeout(() => this.processQueue(), this.requestDelay);
          }
        }
      })();
    }

    this.processing = false;
  }

  clear() {
    this.queue = [];
  }
}

const requestQueue = new PriorityRequestQueue();

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Generate unique request key for deduplication
 */
const generateRequestKey = (endpoint, params) => {
  const sortedParams = Object.keys(params || {})
    .sort()
    .map(key => `${key}=${params[key]}`)
    .join('&');
  return `${endpoint}?${sortedParams}`;
};

/**
 * Check if network type is cached
 */
const getCachedNetworkType = (projectPath, scenarioName, networkFile) => {
  const key = `${projectPath}/${scenarioName}/${networkFile}`;
  return networkTypeCache.get(key);
};

/**
 * Cache network type
 */
const cacheNetworkType = (projectPath, scenarioName, networkFile, type) => {
  const key = `${projectPath}/${scenarioName}/${networkFile}`;
  networkTypeCache.set(key, type);
};

/**
 * Detect network type (single, multi-period, or multi-file)
 */
const detectNetworkType = async (projectPath, scenarioName, networkFile) => {
  // Check cache first
  const cached = getCachedNetworkType(projectPath, scenarioName, networkFile);
  if (cached) return cached;

  try {
    const response = await axios.get('/project/pypsa/detect-network-type', {
      params: { projectPath, scenarioName, networkFile },
      timeout: 5000,
    });

    if (response.data.success) {
      const type = {
        isSinglePeriod: response.data.isSinglePeriod,
        isMultiPeriod: response.data.isMultiPeriod,
        isMultiFile: response.data.isMultiFile,
        periods: response.data.periods || [],
        files: response.data.files || [],
      };

      cacheNetworkType(projectPath, scenarioName, networkFile, type);
      return type;
    }
  } catch (error) {
    console.warn('Network type detection failed, assuming single period:', error.message);
  }

  // Default to single period if detection fails
  return {
    isSinglePeriod: true,
    isMultiPeriod: false,
    isMultiFile: false,
    periods: [],
    files: [],
  };
};

/**
 * Retry logic with exponential backoff
 */
const retryWithBackoff = async (fn, maxRetries = CONFIG.RETRY_ATTEMPTS) => {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx)
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;
      }

      // Don't retry on abort
      if (error.name === 'CanceledError' || error.message === 'canceled') {
        throw error;
      }

      // Last attempt failed
      if (attempt === maxRetries) {
        throw error;
      }

      // Wait before retrying with exponential backoff
      const delay = CONFIG.RETRY_DELAY * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));

      console.log(`Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`);
    }
  }

  throw lastError;
};

// ============================================================================
// MAIN HOOK
// ============================================================================

/**
 * Optimized hook for fetching PyPSA data
 *
 * @param {string} endpoint - API endpoint (without /project prefix)
 * @param {object} params - Query parameters
 * @param {boolean} enabled - Whether to fetch data (default: true)
 * @param {object} options - Additional options:
 *   - includeTimeseries: Include large timeseries data (default: auto-detect)
 *   - useCache: Respect cache headers (default: true)
 *   - priority: Request priority (HIGH, NORMAL, LOW)
 *   - period: Specific period for multi-period networks
 *   - onProgress: Callback for performance metrics
 *   - onNetworkTypeDetected: Callback when network type is detected
 * @returns {object} Data, loading state, error, refetch, networkType, and metrics
 */
const usePyPSAData = (endpoint, params = null, enabled = true, options = {}) => {
  const {
    includeTimeseries = null,       // null = auto-detect based on endpoint
    useCache = true,
    priority = PRIORITY.NORMAL,
    period = null,                  // Specific period for multi-period networks
    onProgress = null,
    onNetworkTypeDetected = null,
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [networkType, setNetworkType] = useState(null);

  const abortControllerRef = useRef(null);
  const lastRequestKeyRef = useRef(null);
  const isLoadingRef = useRef(false);  // Guard against concurrent requests
  const isMountedRef = useRef(true);   // Track if component is mounted

  // Auto-detect if timeseries should be included based on endpoint
  const shouldIncludeTimeseries = useMemo(() => {
    if (includeTimeseries !== null) return includeTimeseries;

    // Safety check: if endpoint is null or undefined, default to false
    if (!endpoint) return false;

    // Endpoints that typically need timeseries data
    const timeseriesEndpoints = [
      '/pypsa/dispatch-analysis',
      '/pypsa/storage',
      '/pypsa/prices',
      '/pypsa/loads',
    ];

    return timeseriesEndpoints.some(ep => endpoint.includes(ep));
  }, [endpoint, includeTimeseries]);

  // Detect network type on mount or when params change
  useEffect(() => {
    if (!enabled || !params) return;

    const { projectPath, scenarioName, networkFile } = params;
    if (!projectPath || !scenarioName || !networkFile) return;

    const detect = async () => {
      const type = await detectNetworkType(projectPath, scenarioName, networkFile);
      setNetworkType(type);

      if (onNetworkTypeDetected && typeof onNetworkTypeDetected === 'function') {
        onNetworkTypeDetected(type);
      }
    };

    detect();
  }, [params, enabled, onNetworkTypeDetected]);

  const fetchData = useCallback(async () => {
    // Don't fetch if component is unmounted
    if (!isMountedRef.current) {
      return;
    }

    // Don't fetch if disabled or params are null
    if (!enabled || params === null) {
      setData(null);
      setLoading(false);
      return;
    }

    // Validate required params
    const { projectPath, scenarioName, networkFile } = params;
    if (!projectPath || !scenarioName || !networkFile) {
      setData(null);
      setLoading(false);
      return;
    }

    // AGGRESSIVE: Check if already loading using ref
    if (isLoadingRef.current) {
      console.log('[PyPSA] Request already in progress, skipping:', endpoint);
      return;
    }

    // Generate request key for deduplication
    const requestKey = generateRequestKey(endpoint, {
      ...params,
      period,
      includeTimeseries: shouldIncludeTimeseries,
    });

    // Check if same request is already in flight (using ref to avoid dependency loop)
    if (requestKey === lastRequestKeyRef.current) {
      console.log('[PyPSA] Skipping duplicate request (in flight):', endpoint);
      return;
    }

    // Check request cache for recent identical requests
    const now = Date.now();
    const cachedRequest = requestCache.get(requestKey);
    if (cachedRequest && (now - cachedRequest.timestamp) < CONFIG.DEDUP_WINDOW) {
      console.log('[PyPSA] Using deduplicated request result');
      setData(cachedRequest.data.data ?? cachedRequest.data);
      setPerformanceMetrics(cachedRequest.metrics);
      return;
    }

    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();
    lastRequestKeyRef.current = requestKey;
    isLoadingRef.current = true;  // Set loading guard

    setLoading(true);
    setError(null);

    const requestStartTime = performance.now();

    try {
      // Enqueue request with priority
      const result = await requestQueue.enqueue(async () => {
        return await retryWithBackoff(async () => {
          // Extract date range parameters if present
          const { startDate, endDate, ...otherParams } = params || {};

          return await axios.get(`/project${endpoint}`, {
            params: {
              projectPath,
              scenarioName,
              networkFile,
              period,                       // Pass period for multi-period networks
              includeTimeseries: shouldIncludeTimeseries,
              ...(startDate && { start_date: startDate }),  // Pass date range if provided
              ...(endDate && { end_date: endDate }),
              ...otherParams
            },
            headers: useCache ? {
              'Cache-Control': `max-age=${CONFIG.CACHE_DURATION / 1000}`,
            } : {
              'Cache-Control': 'no-cache',
            },
            signal: abortControllerRef.current.signal,
            timeout: CONFIG.REQUEST_TIMEOUT,
          });
        });
      }, priority);

      // Extract performance metrics
      const requestEndTime = performance.now();
      const metrics = {
        clientTime: Math.round(requestEndTime - requestStartTime),
        serverTime: result.headers['x-analysis-time']
          ? parseFloat(result.headers['x-analysis-time']) * 1000
          : null,
        responseSize: result.headers['content-length']
          ? parseInt(result.headers['content-length'])
          : JSON.stringify(result.data).length,
        cached: result.headers['x-cache'] === 'HIT',
        timestamp: new Date().toISOString(),
        endpoint,
        networkType: networkType?.isMultiPeriod ? 'multi-period' :
                     networkType?.isMultiFile ? 'multi-file' : 'single',
      };

      setPerformanceMetrics(metrics);

      // Call progress callback
      if (onProgress && typeof onProgress === 'function') {
        onProgress(metrics);
      }

      // Log performance in development
      if (import.meta.env.DEV) {
        console.log(`[PyPSA API] ${endpoint}:`, {
          clientTime: `${metrics.clientTime}ms`,
          serverTime: metrics.serverTime ? `${metrics.serverTime}ms` : 'N/A',
          size: `${(metrics.responseSize / 1024).toFixed(2)} KB`,
          cached: metrics.cached ? 'YES' : 'NO',
          networkType: metrics.networkType,
          period: period || 'all',
          includeTimeseries: shouldIncludeTimeseries,
        });
      }

      // Handle response
      if (result.data.success) {
        setData(result.data.data ?? result.data);

        // Cache request result
        requestCache.set(requestKey, {
          data: result.data,
          metrics,
          timestamp: now,
        });

        // Clean old cache entries (keep last 50)
        if (requestCache.size > 50) {
          const keys = Array.from(requestCache.keys());
          keys.slice(0, requestCache.size - 50).forEach(key => {
            requestCache.delete(key);
          });
        }
      } else {
        setError(result.data.message || 'Failed to fetch data');
        setData(null);
      }
    } catch (err) {
      // Ignore abort errors
      if (err.name === 'CanceledError' || err.message === 'canceled') {
        console.log('[PyPSA] Request aborted');
        return;
      }

      console.error(`[PyPSA] Error fetching ${endpoint}:`, err);

      const errorMessage = err.response?.data?.detail ||
                          err.response?.data?.message ||
                          err.message ||
                          'Failed to fetch data';

      setError(errorMessage);
      setData(null);
    } finally {
      setLoading(false);
      lastRequestKeyRef.current = null;
      isLoadingRef.current = false;  // Clear loading guard
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    endpoint,
    params,
    enabled,
    shouldIncludeTimeseries,
    useCache,
    priority,
    period
    // NOTE: onProgress and networkType intentionally excluded to prevent infinite loop
    // They are captured in the closure but don't need to trigger refetch
  ]);

  // Fetch on mount and when dependencies change
  useEffect(() => {
    isMountedRef.current = true;  // Mark as mounted
    fetchData();

    // Cleanup: abort request on unmount
    return () => {
      isMountedRef.current = false;  // Mark as unmounted
      isLoadingRef.current = false;  // Clear loading guard
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    networkType,                    // Network type information
    performanceMetrics,
    refetch: fetchData,
  };
};

// ============================================================================
// HELPER HOOKS
// ============================================================================

/**
 * Hook for fetching data with high priority (overview, availability checks)
 */
export const usePyPSADataHighPriority = (endpoint, params, enabled, options = {}) => {
  return usePyPSAData(endpoint, params, enabled, {
    ...options,
    priority: PRIORITY.HIGH,
  });
};

/**
 * Hook for fetching large datasets with low priority
 */
export const usePyPSADataLowPriority = (endpoint, params, enabled, options = {}) => {
  return usePyPSAData(endpoint, params, enabled, {
    ...options,
    priority: PRIORITY.LOW,
  });
};

/**
 * Hook for fetching period-specific data in multi-period networks
 */
export const usePyPSADataPeriod = (endpoint, params, period, enabled, options = {}) => {
  return usePyPSAData(endpoint, params, enabled, {
    ...options,
    period,
  });
};

// ============================================================================
// UTILITY EXPORTS
// ============================================================================

/**
 * Clear all request caches
 */
export const clearPyPSACache = () => {
  requestCache.clear();
  networkTypeCache.clear();
  requestQueue.clear();
  console.log('[PyPSA] All caches cleared');
};

/**
 * Get cache statistics
 */
export const getPyPSACacheStats = () => {
  return {
    requestCacheSize: requestCache.size,
    networkTypeCacheSize: networkTypeCache.size,
    queueLength: requestQueue.queue.length,
    activeRequests: requestQueue.activeRequests,
  };
};

export default usePyPSAData;
