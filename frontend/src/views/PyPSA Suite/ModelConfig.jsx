import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Settings,
  AlertTriangle,
  Play,
  FileText,
  Wrench,
  FolderOpen,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { useNotification } from '../../contexts/NotificationContext';
import ProcessModal from '../../components/ProcessModal';
import FloatingProcessIndicator from '../../components/FloatingProcessIndicator';

const DEFAULT_SCENARIO_NAME = 'PyPSA_Scenario_V1';
const SOLVER_OPTIONS = [
  { value: 'highs', label: 'Highs', description: 'Fast and reliable open-source solver (Default)' },
];

const ModelConfig = () => {
  const [scenarioName, setScenarioName] = useState(DEFAULT_SCENARIO_NAME);
  const [selectedSolver, setSelectedSolver] = useState('highs');
  const [existingScenarios, setExistingScenarios] = useState([]);
  const [error, setError] = useState('');
  const [projectPath, setProjectPath] = useState('');

  // Reference to solver stream for cleanup
  const solverStreamRef = useRef(null);

  // Unified notification system
  const {
    processes,
    activeModal,
    startProcess,
    updateLogs,
    updateProgress,
    updateStatus,
    stopProcess,
    resetProcess,
    showModal,
    hideModal,
    registerEventSource,
  } = useNotification();

  const pypsaProcess = processes['pypsa'];
  const isModalVisible = activeModal === 'pypsa';
  const isRunningModel = pypsaProcess?.status === 'running';

  // Check for duplicate scenario name
  const isNameDuplicate = useMemo(
    () =>
      existingScenarios.some(
        (existingName) =>
          existingName.toLowerCase() ===
          (scenarioName.trim() || DEFAULT_SCENARIO_NAME).toLowerCase()
      ),
    [scenarioName, existingScenarios]
  );

  useEffect(() => {
    // Try multiple possible keys for active project
    let currentProjectString = sessionStorage.getItem('activeProject') ||
                                sessionStorage.getItem('currentProject') ||
                                localStorage.getItem('activeProject') ||
                                localStorage.getItem('currentProject');

    console.log('[ModelConfig] Checking for active project...');

    if (!currentProjectString) {
      console.warn('[ModelConfig] No active project found in storage');
      setError('No active project found. Please load a project first.');
      return;
    }

    try {
      const currentProject = JSON.parse(currentProjectString);
      console.log('[ModelConfig] Parsed project:', currentProject);

      if (!currentProject?.path) {
        console.warn('[ModelConfig] Project has no path');
        setError('Active project has no path configured.');
        return;
      }

      console.log('[ModelConfig] Setting project path:', currentProject.path);
      setProjectPath(currentProject.path);

      // Fetch existing PyPSA scenarios
      axios
        .get('/project/pypsa/scenarios', { params: { projectPath: currentProject.path } })
        .then((res) => {
          console.log('[ModelConfig] Scenarios fetched:', res.data.scenarios);
          setExistingScenarios(res.data.scenarios || []);
        })
        .catch((err) => {
          console.error('[ModelConfig] Could not fetch existing PyPSA scenarios', err);
        });

      // Pre-fill default solver
      setSelectedSolver('highs');

      // Clear any previous errors
      setError('');
    } catch (parseError) {
      console.error('[ModelConfig] Error parsing project data:', parseError);
      setError('Invalid project data. Please reload the project.');
    }
  }, []);

  const handleApplyConfiguration = async () => {
    if (!projectPath) {
      setError('No active project found. Please load a project first.');
      return;
    }

    // Check if PyPSA model is already running
    if (isRunningModel) {
      toast.error('A PyPSA model is already running. Please wait for it to complete or stop it first.');
      return;
    }

    setError('');

    // Use default name if input is empty
    const finalScenarioName = scenarioName.trim() || DEFAULT_SCENARIO_NAME;

    // Simplified payload - only projectPath and scenarioName
    const configPayload = {
      projectPath: projectPath,
      scenarioName: finalScenarioName,
    };

    try {
      // Step 1: Apply configuration (create scenario folder)
      await axios.post('/project/pypsa/apply-configuration', configPayload);
      console.log('[ModelConfig] Configuration applied successfully');

      // Step 2: Start process in unified notification system
      startProcess('pypsa', {
        title: 'PyPSA Model Execution',
        scenarioName: finalScenarioName,
        unit: 'years',
        metadata: {
          projectPath: projectPath,
          solver: selectedSolver,
        },
      });

      // Solver logs will be streamed into unified logs

      // Step 3: Start model execution on backend
      const runResponse = await axios.post('/project/run-pypsa-model', {
        projectPath: projectPath,
        scenarioName: finalScenarioName
      });

      console.log('[ModelConfig] Model execution started:', runResponse.data);

      // Step 4: Connect to SSE for progress updates
      connectToProgressStream();

      // Step 5: Connect to solver log stream
      connectToSolverLogs(finalScenarioName);

    } catch (err) {
      console.error('Error applying PyPSA configuration or starting model:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Failed to apply the configuration or start model execution.';
      setError(errorMsg);
      toast.error(errorMsg);

      // Update process status to failed if it was started
      if (pypsaProcess) {
        updateStatus('pypsa', 'failed', errorMsg);
      }
    }
  };

  const connectToProgressStream = () => {
    console.log('[ModelConfig] Connecting to progress stream...');
    const eventSource = new EventSource('/project/pypsa-model-progress');

    // Register for cleanup
    registerEventSource('pypsa', eventSource);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[ModelConfig] Progress event:', data);

        if (data.type === 'progress') {
          // Add new logs to unified system
          updateLogs('pypsa', {
            type: 'info',
            text: data.log
          });
        } else if (data.type === 'end') {
          // Model execution finished
          if (data.status === 'completed') {
            updateStatus('pypsa', 'completed');
            updateLogs('pypsa', {
              type: 'success',
              text: '✅ Model execution completed successfully!'
            });
            toast.success('PyPSA model completed successfully!');
          } else if (data.status === 'failed') {
            updateStatus('pypsa', 'failed', data.error || 'Unknown error');
            updateLogs('pypsa', {
              type: 'error',
              text: `❌ Model execution failed: ${data.error || 'Unknown error'}`
            });
            toast.error('PyPSA model execution failed');
          }
          eventSource.close();
          // Close solver stream if open
          if (solverStreamRef.current) {
            solverStreamRef.current.close();
          }
        } else if (data.type === 'error') {
          updateStatus('pypsa', 'failed', data.message);
          updateLogs('pypsa', {
            type: 'error',
            text: `❌ Error: ${data.message}`
          });
          toast.error('PyPSA model error');
          eventSource.close();
          // Close solver stream if open
          if (solverStreamRef.current) {
            solverStreamRef.current.close();
          }
        }
      } catch (parseError) {
        console.error('[ModelConfig] Error parsing SSE data:', parseError);
      }
    };

    eventSource.onerror = (error) => {
      console.error('[ModelConfig] SSE error:', error);
      if (pypsaProcess?.status === 'running') {
        updateStatus('pypsa', 'failed', 'Connection to progress stream lost');
        updateLogs('pypsa', {
          type: 'error',
          text: '❌ Connection to progress stream lost'
        });
      }
      eventSource.close();
      // Close solver stream if open
      if (solverStreamRef.current) {
        solverStreamRef.current.close();
      }
    };
  };

  const connectToSolverLogs = (finalScenarioName) => {
    console.log('[ModelConfig] Connecting to solver log stream...');

    const eventSource = new EventSource(
      `/project/pypsa-solver-logs?projectPath=${encodeURIComponent(projectPath)}&scenarioName=${encodeURIComponent(finalScenarioName)}`
    );

    solverStreamRef.current = eventSource;
    registerEventSource('pypsa', eventSource);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'log') {
          // Push solver logs to unified notification system
          updateLogs('pypsa', {
            type: 'info',
            text: data.content
          });
        } else if (data.type === 'end') {
          console.log('[ModelConfig] Solver log stream ended');
          eventSource.close();
        }
      } catch (parseError) {
        console.error('[ModelConfig] Error parsing solver SSE data:', parseError);
      }
    };

    eventSource.onerror = (error) => {
      console.error('[ModelConfig] Solver SSE error:', error);
      eventSource.close();
    };
  };

  const handleStopModel = async () => {
    try {
      toast.loading('Stopping model...', { id: 'stop-model' });

      await axios.post('/project/stop-pypsa-model');

      updateLogs('pypsa', {
        type: 'warning',
        text: '⚠️  Model cancellation requested...'
      });

      await stopProcess('pypsa', '/project/stop-pypsa-model');

      toast.success('Model stopped successfully', { id: 'stop-model' });

    } catch (error) {
      console.error('[ModelConfig] Error stopping model:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to stop model';
      toast.error(errorMsg, { id: 'stop-model' });

      if (error.response?.status === 404) {
        updateLogs('pypsa', {
          type: 'error',
          text: '❌ No model is currently running'
        });
      }
    }
  };

  const handleCloseModal = () => {
    resetProcess('pypsa');

    // Reset form after successful completion
    if (pypsaProcess?.status === 'completed') {
      setScenarioName(DEFAULT_SCENARIO_NAME);
      setSelectedSolver('highs');
    }
  };

  return (
    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 overflow-hidden p-6">
      <div className="bg-white w-full max-w-6xl rounded-xl shadow-2xl border border-slate-300 flex flex-col max-h-[90vh]">
        {/* Header */}
        <header className="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <Settings className="w-7 h-7 text-indigo-600" />
          <div>
            <h1 className="text-xl font-bold text-slate-800">PyPSA Model Configuration</h1>
            <p className="text-sm text-slate-600">
              Configure scenario and solver settings for grid optimization
            </p>
          </div>
        </header>

        {/* Main Content */}
        <main className="p-6 space-y-5 overflow-y-auto flex-grow">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg flex items-start gap-3 text-sm">
              <AlertTriangle className="w-5 h-5 mt-0.5 text-red-600 flex-shrink-0" />
              <div>
                <p className="font-bold">Configuration Error</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Basic Configuration */}
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-800">Basic Configuration</h3>

            <div className="grid grid-cols-2 gap-4">
              {/* Scenario Name Input */}
              <div className="space-y-2">
                <label className="block text-sm font-bold text-slate-700">
                  Scenario Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  placeholder={DEFAULT_SCENARIO_NAME}
                  className="w-full text-base px-4 py-2.5 bg-white border-2 border-slate-300 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                />
                <p className="text-xs text-slate-500">
                  Enter a unique name for your scenario
                </p>
                {isNameDuplicate && scenarioName && (
                  <div className="bg-amber-100 border border-amber-400 rounded-lg p-3 mt-2">
                    <p className="text-sm text-amber-900 font-medium flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Warning: This scenario name already exists
                    </p>
                    <p className="text-xs text-amber-800 mt-1">
                      Running this configuration will overwrite the old scenario results with new results.
                    </p>
                  </div>
                )}
              </div>

              {/* Solver Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-bold text-slate-700">
                  Optimization Solver <span className="text-red-500">*</span>
                </label>
                <select
                  value={selectedSolver}
                  onChange={(e) => setSelectedSolver(e.target.value)}
                  className="w-full text-base px-4 py-2.5 bg-white border-2 border-slate-300 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all cursor-pointer"
                >
                  {SOLVER_OPTIONS.map((solver) => (
                    <option key={solver.value} value={solver.value}>
                      {solver.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500">
                  {SOLVER_OPTIONS.find((s) => s.value === selectedSolver)?.description}
                </p>
              </div>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex gap-3">
              <div className="flex-shrink-0">
                <svg
                  className="w-5 h-5 text-blue-600 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">About PyPSA Optimization</p>
                <p>
                  PyPSA (Python for Power System Analysis) performs optimal power flow and capacity
                  expansion planning. The selected solver will be used to optimize the power system
                  network based on your input data.
                </p>
                <p className="mt-1.5">
                  <span className="font-medium">Recommended:</span> Highs solver offers the best
                  balance of speed and reliability for most use cases.
                </p>
              </div>
            </div>
          </div>

          {/* Configuration Summary */}
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-5">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-800">Configuration Summary</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between bg-white rounded-lg px-4 py-3 shadow-sm">
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <span className="text-sm font-medium text-slate-600">Scenario Name</span>
                </div>
                <span className="text-sm font-bold text-slate-800">
                  {scenarioName || DEFAULT_SCENARIO_NAME}
                </span>
              </div>
              <div className="flex items-center justify-between bg-white rounded-lg px-4 py-3 shadow-sm">
                <div className="flex items-center gap-3">
                  <Wrench className="w-4 h-4 text-indigo-600" />
                  <span className="text-sm font-medium text-slate-600">Solver</span>
                </div>
                <span className="text-sm font-bold text-slate-800">
                  {SOLVER_OPTIONS.find((s) => s.value === selectedSolver)?.label || selectedSolver}
                </span>
              </div>
              <div className="flex items-center justify-between bg-white rounded-lg px-4 py-3 shadow-sm">
                <div className="flex items-center gap-3">
                  <FolderOpen className="w-4 h-4 text-indigo-600" />
                  <span className="text-sm font-medium text-slate-600">Project Path</span>
                </div>
                <span
                  className="text-xs font-medium text-slate-700 truncate max-w-sm"
                  title={projectPath}
                >
                  {projectPath || '(no project loaded)'}
                </span>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="flex justify-end gap-3 px-6 py-4 bg-slate-50 border-t border-slate-200">
          <button
            onClick={handleApplyConfiguration}
            disabled={isRunningModel}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-semibold transition-all shadow-md hover:shadow-lg ${
              isRunningModel
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            {isRunningModel ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Running Model...
              </>
            ) : (
              <>
                <Play size={18} />
                Apply Configuration & Run Model
              </>
            )}
          </button>
        </footer>
      </div>

      {/* Process Modal with Unified Logs */}
      {isModalVisible && pypsaProcess && (
        <ProcessModal
          process={pypsaProcess}
          onClose={handleCloseModal}
          onMinimize={hideModal}
          onStop={isRunningModel ? handleStopModel : null}
        />
      )}

      {/* Floating Indicator when minimized */}
      {!isModalVisible && pypsaProcess?.status === 'running' && (
        <FloatingProcessIndicator
          process={pypsaProcess}
          onClick={() => showModal('pypsa')}
          onStop={handleStopModel}
        />
      )}
    </div>
  );
};

export default ModelConfig;
