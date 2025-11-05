import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};

/**
 * Unified Notification Context for Managing All Long-Running Processes
 *
 * Supports:
 * - Demand Projection/Forecasting
 * - Load Profile Generation
 * - PyPSA Model Execution
 *
 * Features:
 * - Multiple concurrent processes (one per type)
 * - Modal visibility control (hide/show)
 * - Real-time SSE log streaming
 * - Copy-to-clipboard functionality
 * - Progress tracking
 */
export const NotificationProvider = ({ children }) => {
  // Process types: 'demand', 'loadProfile', 'pypsa'
  const [processes, setProcesses] = useState({});

  // Active modal (only one modal visible at a time)
  const [activeModal, setActiveModal] = useState(null);

  // Store EventSource references for cleanup
  const eventSourcesRef = useRef({});

  /**
   * Start a new process
   * @param {string} type - Process type ('demand', 'loadProfile', 'pypsa')
   * @param {object} config - Process configuration
   */
  const startProcess = useCallback((type, config) => {
    const processId = `${type}_${Date.now()}`;

    setProcesses(prev => ({
      ...prev,
      [type]: {
        id: processId,
        type,
        status: 'running',
        title: config.title || 'Processing...',
        scenarioName: config.scenarioName || '',
        startTime: new Date(),
        logs: [],
        progress: {
          percentage: 0,
          message: 'Initializing...',
        },
        taskProgress: {
          current: 0,
          total: 0,
          unit: config.unit || 'items',
        },
        metadata: config.metadata || {},
      }
    }));

    // Show modal immediately when process starts
    setActiveModal(type);

    return processId;
  }, []);

  /**
   * Update process logs
   */
  const updateLogs = useCallback((type, newLog) => {
    setProcesses(prev => {
      if (!prev[type]) return prev;

      const timestamp = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });

      return {
        ...prev,
        [type]: {
          ...prev[type],
          logs: [
            ...prev[type].logs,
            {
              timestamp,
              type: newLog.type || 'info',
              text: newLog.text || newLog,
            }
          ],
        }
      };
    });
  }, []);

  /**
   * Update process progress
   */
  const updateProgress = useCallback((type, progressData) => {
    setProcesses(prev => {
      if (!prev[type]) return prev;

      return {
        ...prev,
        [type]: {
          ...prev[type],
          progress: {
            ...prev[type].progress,
            ...progressData,
          },
        }
      };
    });
  }, []);

  /**
   * Update task progress (e.g., 5/10 years processed)
   */
  const updateTaskProgress = useCallback((type, taskData) => {
    setProcesses(prev => {
      if (!prev[type]) return prev;

      return {
        ...prev,
        [type]: {
          ...prev[type],
          taskProgress: {
            ...prev[type].taskProgress,
            ...taskData,
          },
        }
      };
    });
  }, []);

  /**
   * Update process status
   */
  const updateStatus = useCallback((type, status, error = null) => {
    setProcesses(prev => {
      if (!prev[type]) return prev;

      return {
        ...prev,
        [type]: {
          ...prev[type],
          status,
          error,
          endTime: (status === 'completed' || status === 'failed' || status === 'cancelled')
            ? new Date()
            : prev[type].endTime,
        }
      };
    });

    // Close EventSource if process ended
    if (['completed', 'failed', 'cancelled'].includes(status)) {
      if (eventSourcesRef.current[type]) {
        eventSourcesRef.current[type].forEach(es => es.close());
        delete eventSourcesRef.current[type];
      }
    }
  }, []);

  /**
   * Stop/cancel a running process
   */
  const stopProcess = useCallback((type, stopEndpoint) => {
    return new Promise(async (resolve, reject) => {
      try {
        if (stopEndpoint) {
          await fetch(stopEndpoint, { method: 'POST' });
        }

        updateStatus(type, 'cancelled');
        updateLogs(type, {
          type: 'warning',
          text: 'Process cancelled by user'
        });

        resolve();
      } catch (error) {
        console.error(`Error stopping ${type} process:`, error);
        reject(error);
      }
    });
  }, [updateStatus, updateLogs]);

  /**
   * Reset and clear a process
   */
  const resetProcess = useCallback((type) => {
    setProcesses(prev => {
      const newProcesses = { ...prev };
      delete newProcesses[type];
      return newProcesses;
    });

    // Close modal if it was for this process
    if (activeModal === type) {
      setActiveModal(null);
    }

    // Clean up EventSources
    if (eventSourcesRef.current[type]) {
      eventSourcesRef.current[type].forEach(es => es.close());
      delete eventSourcesRef.current[type];
    }
  }, [activeModal]);

  /**
   * Show modal for a specific process
   */
  const showModal = useCallback((type) => {
    setActiveModal(type);
  }, []);

  /**
   * Hide the current modal (but keep process running)
   */
  const hideModal = useCallback(() => {
    setActiveModal(null);
  }, []);

  /**
   * Register an EventSource for cleanup
   */
  const registerEventSource = useCallback((type, eventSource) => {
    if (!eventSourcesRef.current[type]) {
      eventSourcesRef.current[type] = [];
    }
    eventSourcesRef.current[type].push(eventSource);
  }, []);

  /**
   * Get elapsed time for a process
   */
  const getElapsedTime = useCallback((type) => {
    const process = processes[type];
    if (!process || !process.startTime) return '0m';

    const endTime = process.endTime || new Date();
    const elapsed = Math.floor((endTime - process.startTime) / 1000);

    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }, [processes]);

  /**
   * Copy logs to clipboard
   */
  const copyLogsToClipboard = useCallback((type) => {
    const process = processes[type];
    if (!process || !process.logs.length) return false;

    const logsText = process.logs
      .map(log => `[${log.timestamp}] [${log.type.toUpperCase()}] ${log.text}`)
      .join('\n');

    navigator.clipboard.writeText(logsText).then(
      () => console.log('Logs copied to clipboard'),
      (err) => console.error('Failed to copy logs:', err)
    );

    return true;
  }, [processes]);

  /**
   * Get all running processes
   */
  const getRunningProcesses = useCallback(() => {
    return Object.keys(processes).filter(
      type => processes[type].status === 'running'
    );
  }, [processes]);

  /**
   * Check if a specific process type is running
   */
  const isProcessRunning = useCallback((type) => {
    return processes[type]?.status === 'running';
  }, [processes]);

  const value = {
    processes,
    activeModal,
    startProcess,
    updateLogs,
    updateProgress,
    updateTaskProgress,
    updateStatus,
    stopProcess,
    resetProcess,
    showModal,
    hideModal,
    registerEventSource,
    getElapsedTime,
    copyLogsToClipboard,
    getRunningProcesses,
    isProcessRunning,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
