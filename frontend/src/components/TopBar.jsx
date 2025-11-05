

import React, { useState, useEffect, useRef } from 'react';
import { GoProject } from "react-icons/go";
import { FiBell, FiSettings } from 'react-icons/fi';
import { Loader2, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { useNotification } from '../contexts/NotificationContext'; 

const TopBar = ({ activeProject }) => {
    const { processes, showModal, getElapsedTime } = useNotification();
    const [isProgressPanelOpen, setIsProgressPanelOpen] = useState(false);
    const panelRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (panelRef.current && !panelRef.current.contains(event.target)) {
                setIsProgressPanelOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [panelRef]);

    // Check if any process is running
    const hasRunningProcesses = Object.values(processes).some(p => p.status === 'running');
    const runningProcesses = Object.values(processes).filter(p => p.status === 'running');
    const completedProcesses = Object.values(processes).filter(p => p.status === 'completed');
    const failedProcesses = Object.values(processes).filter(p => p.status === 'failed');

    // Calculate overall progress for the bell icon (average of all running processes)
    const overallProgress = runningProcesses.length > 0
        ? Math.round(runningProcesses.reduce((sum, p) => sum + (p.progress?.percentage || 0), 0) / runningProcesses.length)
        : 0;

    const getProcessIcon = (status) => {
        switch (status) {
            case 'running':
                return <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />;
            case 'completed':
                return <CheckCircle2 className="w-4 h-4 text-green-400" />;
            case 'failed':
                return <AlertTriangle className="w-4 h-4 text-red-400" />;
            case 'cancelled':
                return <XCircle className="w-4 h-4 text-orange-400" />;
            default:
                return null;
        }
    };

    const getStatusBadge = (status) => {
        const classes = {
            running: 'bg-indigo-600 text-white',
            completed: 'bg-green-600 text-white',
            failed: 'bg-red-600 text-white',
            cancelled: 'bg-orange-600 text-white',
        };
        return (
            <span className={`px-2 py-1 rounded text-xs font-bold ${classes[status] || 'bg-gray-600 text-white'}`}>
                {status.toUpperCase()}
            </span>
        );
    };

    const ProcessCard = ({ process, type }) => {
        const clampedPercentage = Math.min(100, Math.max(0, Math.round(process.progress?.percentage || 0)));
        const lastLog = process.logs && process.logs.length > 0
            ? process.logs[process.logs.length - 1]
            : null;

        return (
            <div className="border-b border-slate-700 bg-slate-750 hover:bg-slate-700 transition-colors">
                <div className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {getProcessIcon(process.status)}
                            <span className="font-bold text-white">{process.title}</span>
                        </div>
                        {getStatusBadge(process.status)}
                    </div>

                    {process.scenarioName && (
                        <div className="text-sm flex justify-between">
                            <span className="text-slate-400">Scenario:</span>
                            <span className="text-white font-semibold truncate max-w-[200px]">{process.scenarioName}</span>
                        </div>
                    )}

                    <div className="text-sm flex justify-between">
                        <span className="text-slate-400">Running Time:</span>
                        <span className="text-white font-semibold">{getElapsedTime(type)}</span>
                    </div>

                    {process.status === 'running' && (
                        <>
                            <div className="w-full bg-slate-700 rounded-full h-2">
                                <div
                                    className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${clampedPercentage}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-xs text-slate-400">
                                <span>{process.progress?.message || 'Processing...'}</span>
                                <span className="font-bold text-indigo-400">{clampedPercentage}%</span>
                            </div>

                            {process.taskProgress && process.taskProgress.total > 0 && (
                                <div className="text-xs text-slate-400">
                                    {process.taskProgress.current} / {process.taskProgress.total} {process.taskProgress.unit}
                                </div>
                            )}
                        </>
                    )}

                    {lastLog && process.status === 'running' && (
                        <div className="text-xs text-slate-400 bg-slate-800 rounded p-2 font-mono truncate">
                            {lastLog.text}
                        </div>
                    )}

                    <button
                        onClick={() => {
                            showModal(type);
                            setIsProgressPanelOpen(false);
                        }}
                        className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-semibold transition-colors text-sm"
                    >
                        View Full Logs
                    </button>
                </div>
            </div>
        );
    };

    const ProgressPanel = () => {
        if (!isProgressPanelOpen) return null;

        const hasAnyProcess = Object.keys(processes).length > 0;

        if (!hasAnyProcess) {
            return (
                <div ref={panelRef} className="absolute top-12 right-0 w-96 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl z-50 p-4 text-center text-slate-400">
                    No active processes.
                </div>
            );
        }

        return (
            <div
                ref={panelRef}
                className="absolute top-12 right-0 w-96 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl z-50 overflow-hidden text-slate-300 max-h-[600px] overflow-y-auto"
            >
                <div className="p-4 border-b border-slate-700 sticky top-0 bg-slate-800 z-10">
                    <h3 className="font-bold text-white text-lg">Active Processes</h3>
                    <div className="flex gap-2 mt-2 text-xs">
                        {runningProcesses.length > 0 && (
                            <span className="bg-indigo-600 text-white px-2 py-1 rounded">
                                {runningProcesses.length} Running
                            </span>
                        )}
                        {completedProcesses.length > 0 && (
                            <span className="bg-green-600 text-white px-2 py-1 rounded">
                                {completedProcesses.length} Completed
                            </span>
                        )}
                        {failedProcesses.length > 0 && (
                            <span className="bg-red-600 text-white px-2 py-1 rounded">
                                {failedProcesses.length} Failed
                            </span>
                        )}
                    </div>
                </div>

                {/* Render all processes */}
                {Object.entries(processes).map(([type, process]) => (
                    <ProcessCard key={type} process={process} type={type} />
                ))}
            </div>
        );
    };

    return (
        <header className="fixed top-0 left-0 right-0 bg-slate-800 border-b border-slate-700 h-16 flex items-center justify-between px-6 z-40">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center bg-slate-700 rounded-lg">
                    <GoProject size={20} className="text-blue-300" />
                </div>
                <div className="flex items-baseline gap-2">
                    <p className="text-sm font-bold text-indigo-400">Active Project:</p>
                    <h1 
                        className="text-base font-bold text-white tracking-tight truncate max-w-sm"
                        title={activeProject ? activeProject.name : 'No Project Loaded'}
                    >
                        {activeProject ? activeProject.name : 'No Project Loaded'}
                    </h1>
                </div>
            </div>

            <div className="flex items-center gap-5">
                <div className="relative">
                    <button
                        onClick={() => setIsProgressPanelOpen(prev => !prev)}
                        className="relative p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-700 transition-colors duration-200"
                    >
                        {hasRunningProcesses ? (
                            <div className="relative w-5 h-5 flex items-center justify-center">
                                <svg className="absolute w-full h-full" viewBox="0 0 36 36">
                                    <circle cx="18" cy="18" r="15.9155" className="stroke-current text-slate-600" strokeWidth="4" fill="transparent" />
                                    <circle cx="18" cy="18" r="15.9155" className="stroke-current text-indigo-500 transition-all duration-300" strokeWidth="4" fill="transparent"
                                        strokeDasharray={`${overallProgress}, 100`}
                                        transform="rotate(-90 18 18)"
                                    />
                                </svg>
                                <FiBell size={12} className="text-slate-400" />
                                {/* Process count badge */}
                                {runningProcesses.length > 0 && (
                                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                                        <span className="text-white text-xs font-bold">{runningProcesses.length}</span>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="relative">
                                <FiBell size={20} />
                                {/* Show badge for completed/failed processes */}
                                {(completedProcesses.length > 0 || failedProcesses.length > 0) && (
                                    <div className="absolute top-0 right-0 w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                )}
                            </div>
                        )}
                    </button>
                    <ProgressPanel />
                </div>
                
                <button className="p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-700 transition-colors duration-200">
                    <FiSettings size={20} />
                </button>
            </div>
        </header>
    );
};

export default TopBar;