import React, { useRef, useEffect } from 'react';
import {
  X,
  Minimize2,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
} from 'lucide-react';
import { toast } from 'react-hot-toast';

/**
 * Unified Process Modal Component
 *
 * Used by:
 * - Demand Projection
 * - Load Profile Generation
 * - PyPSA Model Execution
 *
 * Features:
 * - Real-time log streaming
 * - Progress tracking
 * - Minimize/Maximize
 * - Copy logs to clipboard
 * - Stop/Cancel button
 */
const ProcessModal = ({
  process,
  onClose,
  onMinimize,
  onStop,
  children, // Custom content area (e.g., dual log tabs for PyPSA)
}) => {
  const logContainerRef = useRef(null);
  const [copied, setCopied] = React.useState(false);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [process.logs]);

  const handleCopyLogs = () => {
    const logsText = process.logs
      .map(log => `[${log.timestamp}] [${log.type.toUpperCase()}] ${log.text}`)
      .join('\n');

    navigator.clipboard.writeText(logsText).then(
      () => {
        setCopied(true);
        toast.success('Logs copied to clipboard!');
        setTimeout(() => setCopied(false), 2000);
      },
      (err) => {
        console.error('Failed to copy logs:', err);
        toast.error('Failed to copy logs');
      }
    );
  };

  const getStatusIcon = () => {
    switch (process.status) {
      case 'running':
        return <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-6 h-6 text-green-600" />;
      case 'failed':
        return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'cancelled':
        return <XCircle className="w-6 h-6 text-orange-600" />;
      default:
        return null;
    }
  };

  const getStatusTitle = () => {
    switch (process.status) {
      case 'running':
        return `${process.title} in Progress`;
      case 'completed':
        return `${process.title} Completed`;
      case 'failed':
        return `${process.title} Failed`;
      case 'cancelled':
        return `${process.title} Cancelled`;
      default:
        return process.title;
    }
  };

  const getStatusSubtitle = () => {
    switch (process.status) {
      case 'running':
        return 'Please wait while the process runs...';
      case 'completed':
        return 'Process completed successfully!';
      case 'failed':
        return 'An error occurred during execution';
      case 'cancelled':
        return 'Process was cancelled by user';
      default:
        return '';
    }
  };

  const isRunning = process.status === 'running';
  const isFinished = ['completed', 'failed', 'cancelled'].includes(process.status);

  const clampedPercentage = Math.min(100, Math.max(0, Math.round(process.progress?.percentage || 0)));

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[85vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-indigo-50 to-purple-50">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h2 className="text-xl font-bold text-slate-800">{getStatusTitle()}</h2>
              <p className="text-sm text-slate-600">{getStatusSubtitle()}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Minimize Button */}
            {isRunning && (
              <button
                onClick={onMinimize}
                className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                title="Minimize (continue running in background)"
              >
                <Minimize2 size={18} className="text-slate-600" />
              </button>
            )}

            {/* Copy Logs Button */}
            {process.logs && process.logs.length > 0 && (
              <button
                onClick={handleCopyLogs}
                className="flex items-center gap-2 px-3 py-2 hover:bg-slate-200 rounded-lg transition-colors"
                title="Copy logs to clipboard"
              >
                {copied ? (
                  <Check size={18} className="text-green-600" />
                ) : (
                  <Copy size={18} className="text-slate-600" />
                )}
              </button>
            )}

            {/* Stop Button */}
            {isRunning && onStop && (
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to stop this process? This action cannot be undone.')) {
                    onStop();
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-semibold"
              >
                <XCircle className="w-5 h-5" />
                Stop Process
              </button>
            )}

            {/* Close Button */}
            {isFinished && (
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <X size={20} className="text-slate-600" />
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-slate-700">
              {process.progress?.message || 'Processing...'}
            </span>
            <span className="text-sm font-bold text-indigo-600">
              {clampedPercentage}%
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${clampedPercentage}%` }}
            ></div>
          </div>

          {/* Task Progress (e.g., 5/10 years) */}
          {process.taskProgress && process.taskProgress.total > 0 && (
            <div className="flex justify-between items-center mt-2 text-xs text-slate-600">
              <span>
                {process.taskProgress.unit}: {process.taskProgress.current} / {process.taskProgress.total}
              </span>
              {process.scenarioName && (
                <span className="font-semibold">Scenario: {process.scenarioName}</span>
              )}
            </div>
          )}
        </div>

        {/* Custom Content Area (for special cases like PyPSA dual tabs) */}
        {children ? (
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        ) : (
          /* Default Log Display */
          <div className="flex-1 overflow-y-auto p-6 bg-slate-900 font-mono text-sm">
            {process.logs.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Loader2 className="w-12 h-12 text-indigo-400 animate-spin mx-auto mb-4" />
                  <p className="text-slate-400">Initializing process...</p>
                </div>
              </div>
            ) : (
              <div ref={logContainerRef} className="space-y-1">
                {process.logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <span className="text-slate-500 text-xs flex-shrink-0">
                      {log.timestamp}
                    </span>
                    <span
                      className={`text-xs font-semibold flex-shrink-0 ${
                        log.type === 'error' ? 'text-red-400' :
                        log.type === 'success' ? 'text-green-400' :
                        log.type === 'warning' ? 'text-yellow-400' :
                        log.type === 'progress' ? 'text-cyan-400' :
                        'text-slate-400'
                      }`}
                    >
                      [{log.type.toUpperCase()}]
                    </span>
                    <p
                      className={`flex-1 break-words ${
                        log.type === 'error' ? 'text-red-300' :
                        log.type === 'success' ? 'text-green-300' :
                        log.type === 'warning' ? 'text-yellow-300' :
                        'text-slate-300'
                      }`}
                    >
                      {log.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-slate-600">
              {isRunning && (
                <span className="flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin text-indigo-600" />
                  Process is running... Please do not close this window
                </span>
              )}
              {process.status === 'completed' && (
                <span className="text-green-600 font-semibold">
                  ✓ Process completed successfully!
                </span>
              )}
              {process.status === 'failed' && (
                <span className="text-red-600 font-semibold">
                  ✗ Process failed. {process.error ? `Error: ${process.error}` : 'Please check the logs above.'}
                </span>
              )}
              {process.status === 'cancelled' && (
                <span className="text-orange-600 font-semibold">
                  ⚠ Process was cancelled by user
                </span>
              )}
            </div>

            {isFinished && (
              <button
                onClick={onClose}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold transition-all"
              >
                Close
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessModal;
