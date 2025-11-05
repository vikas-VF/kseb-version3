import React from 'react';
import { Loader2, XCircle, CheckCircle2, AlertTriangle } from 'lucide-react';

/**
 * Floating Process Indicator
 *
 * Displays when a process modal is minimized.
 * Shows:
 * - Process status icon
 * - Process title and scenario
 * - Last log entry
 * - Progress bar
 * - Quick stop button
 *
 * Click to restore the modal
 */
const FloatingProcessIndicator = ({ process, onClick, onStop }) => {
  if (!process) return null;

  const getStatusIcon = () => {
    switch (process.status) {
      case 'running':
        return <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />;
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 flex-shrink-0" />;
      case 'failed':
        return <AlertTriangle className="w-5 h-5 flex-shrink-0" />;
      default:
        return <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />;
    }
  };

  const getBackgroundClass = () => {
    switch (process.status) {
      case 'running':
        return 'bg-gradient-to-r from-indigo-600 to-purple-600';
      case 'completed':
        return 'bg-gradient-to-r from-green-600 to-emerald-600';
      case 'failed':
        return 'bg-gradient-to-r from-red-600 to-rose-600';
      default:
        return 'bg-gradient-to-r from-indigo-600 to-purple-600';
    }
  };

  const clampedPercentage = Math.min(100, Math.max(0, Math.round(process.progress?.percentage || 0)));
  const lastLog = process.logs && process.logs.length > 0
    ? process.logs[process.logs.length - 1]
    : null;

  const isRunning = process.status === 'running';

  return (
    <div
      className={`fixed bottom-6 right-6 ${getBackgroundClass()} text-white rounded-lg shadow-2xl p-4 cursor-pointer hover:shadow-3xl transition-all z-50 max-w-sm ${isRunning ? 'animate-pulse-subtle' : ''}`}
      onClick={onClick}
    >
      <div className="space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <p className="font-bold text-sm">{process.title}</p>
              {process.scenarioName && (
                <p className="text-xs opacity-90">{process.scenarioName}</p>
              )}
            </div>
          </div>

          {/* Stop Button */}
          {isRunning && onStop && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm('Stop this process?')) {
                  onStop();
                }
              }}
              className="p-1.5 hover:bg-white/20 rounded transition-colors"
              title="Stop Process"
            >
              <XCircle size={18} />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-white/20 rounded-full h-1.5">
          <div
            className="bg-white h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${clampedPercentage}%` }}
          ></div>
        </div>

        {/* Last Log Entry */}
        {lastLog && (
          <p className="text-xs opacity-80 truncate font-mono">
            {lastLog.text}
          </p>
        )}

        {/* Task Progress */}
        {process.taskProgress && process.taskProgress.total > 0 && (
          <div className="flex justify-between text-xs opacity-75">
            <span>
              {process.taskProgress.current} / {process.taskProgress.total} {process.taskProgress.unit}
            </span>
            <span>{clampedPercentage}%</span>
          </div>
        )}

        {/* Click hint */}
        <p className="text-xs text-center opacity-75 italic mt-2">
          Click to view full logs
        </p>
      </div>
    </div>
  );
};

export default FloatingProcessIndicator;
