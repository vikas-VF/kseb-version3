import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Check, ArrowRight, ArrowLeft, Rocket, FileText, FileSpreadsheet, Activity, Database, SlidersHorizontal, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useNotification } from '../../contexts/NotificationContext';
import ProcessModal from '../../components/ProcessModal';
import FloatingProcessIndicator from '../../components/FloatingProcessIndicator';


const GenerateProfiles = ({ activeProject, setSelected }) => {
    // Unified notification system
    const {
        processes,
        activeModal,
        startProcess,
        updateLogs,
        updateProgress,
        updateTaskProgress,
        updateStatus,
        resetProcess,
        showModal,
        hideModal,
        registerEventSource,
    } = useNotification();

    const profileProcess = processes['loadProfile'];
    const isModalVisible = activeModal === 'loadProfile';
    const status = profileProcess?.status || 'idle';

    const getInitialState = () => {
        const savedState = sessionStorage.getItem('generateProfiles_wizardState');
        try {
            const parsed = JSON.parse(savedState);
            if (parsed && typeof parsed === 'object' && parsed.currentStep) {
                return parsed;
            }
        } catch (e) { }

        return {
            currentStep: 1,
            profileName: '',
            startYear: '',
            endYear: '',
            selectedMethod: null,
            baseYear: '',
            demandSource: null,
            projectionScenario: '',
            monthlyConstraint: null,
            profileNameError: '',
        };
    };

    const [state, setState] = useState(getInitialState);
    const [availableBaseYears, setAvailableBaseYears] = useState([]);
    const [isLoadingYears, setIsLoadingYears] = useState(false);
    const [availableScenarios, setAvailableScenarios] = useState([]);
    const [isLoadingScenarios, setIsLoadingScenarios] = useState(false);

    const updateState = (updates) => setState(prevState => ({ ...prevState, ...updates }));

    const resetAndClearState = () => {
        sessionStorage.removeItem('generateProfiles_wizardState');
        setState(getInitialState());
        setAvailableBaseYears([]);
        setAvailableScenarios([]);
        resetProcess('loadProfile');
    };

    const handleNavigateToAnalysis = () => {
        sessionStorage.removeItem('generateProfiles_wizardState');
        resetProcess('loadProfile');
        setSelected('Analyze Profiles');
    };

    useEffect(() => {
        sessionStorage.setItem('generateProfiles_wizardState', JSON.stringify(state));
    }, [state]);


    useEffect(() => {
        if (state.selectedMethod !== 'base' || !activeProject?.path) return;
        const fetchBaseYears = async () => {
            setIsLoadingYears(true);
            try {
                const response = await axios.get(`/project/available-base-years?projectPath=${encodeURIComponent(activeProject.path)}`);
                if (response.data?.success) {
                    const years = response.data.years;
                    setAvailableBaseYears(years);
                    if (years.length > 0 && !state.baseYear) {
                        updateState({ baseYear: years[years.length - 1] });
                    }
                }
            } catch (error) { console.error("Failed to fetch base years:", error); }
            finally { setIsLoadingYears(false); }
        };
        fetchBaseYears();
    }, [state.selectedMethod, activeProject]);

    useEffect(() => {
        if (state.demandSource !== 'projection' || !activeProject?.path) return;
        const fetchScenarios = async () => {
            setIsLoadingScenarios(true);
            try {
                const response = await axios.get(`/project/available-scenarios`, { params: { projectPath: activeProject.path } });
                if (response.data?.scenarios) {
                    const scenarios = response.data.scenarios;
                    setAvailableScenarios(scenarios);
                    if (scenarios.length > 0 && !state.projectionScenario) {
                        updateState({ projectionScenario: scenarios[0] });
                    }
                }
            } catch (error) { console.error("Failed to fetch scenarios:", error); }
            finally { setIsLoadingScenarios(false); }
        };
        fetchScenarios();
    }, [state.demandSource, activeProject]);

    useEffect(() => {
        if (!state.profileName) {
            updateState({ profileNameError: '' });
            return;
        }
        const checkProfileName = async () => {
            if (!activeProject?.path) return;
            try {
                const response = await axios.get(`/project/check-profile-exists?projectPath=${encodeURIComponent(activeProject.path)}&profileName=${encodeURIComponent(state.profileName)}`);
                updateState({ profileNameError: response.data.exists ? 'This profile name already exists.' : '' });
            } catch (error) {
                updateState({ profileNameError: 'Failed to validate profile name.' });
            }
        };
        const debounceCheck = setTimeout(checkProfileName, 500);
        return () => clearTimeout(debounceCheck);
    }, [state.profileName, activeProject]);

    // --- Validation Logic ---
    const isStep1Valid = state.profileName && !state.profileNameError && state.startYear && state.endYear && state.selectedMethod && (state.selectedMethod === 'base' ? state.baseYear : true);
    const isStep2Valid = state.demandSource && (state.demandSource === 'projection' ? state.projectionScenario : true);
    const isStep3Valid = !!state.monthlyConstraint;

    // --- Process Handling ---
    const handleGenerateClick = async () => {
        if (!activeProject?.path) {
            toast.error('Active project path not found!');
            return;
        }
        if (state.profileNameError || !state.profileName) {
            toast.error('Please fix the profile name error.');
            return;
        }

        const finalPayload = {
            projectPath: activeProject.path,
            profileConfiguration: {
                general: { profile_name: state.profileName, start_year: state.startYear, end_year: state.endYear },
                generation_method: { type: state.selectedMethod, base_year: state.selectedMethod === 'base' ? state.baseYear : null },
                data_source: { type: state.demandSource, scenario_name: state.demandSource === 'projection' ? state.projectionScenario : null },
                constraints: { monthly_method: state.monthlyConstraint }
            }
        };

        try {
            // Start process in unified notification system
            startProcess('loadProfile', {
                title: 'Load Profile Generation',
                scenarioName: state.profileName,
                unit: 'Years',
                metadata: finalPayload,
            });

            // Send API request to start generation
            await axios.post('/project/generate-profile', finalPayload);

            // Connect to SSE for progress updates
            const eventSource = new EventSource('/project/generation-status');
            registerEventSource('loadProfile', eventSource);

            eventSource.onmessage = (event) => {
                try {
                    const log = event.data;

                    // Clean up the log text by removing STDERR/STDOUT prefixes and timestamps
                    let cleanLog = log;

                    // Remove backend timestamp and log level prefix (e.g., "2025-11-05 13:03:58,528 - ERROR - [Profile Generation STDERR]: ")
                    cleanLog = cleanLog.replace(/^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3}\s+-\s+\w+\s+-\s+\[Profile Generation (STDERR|STDOUT)\]:\s+/, '');

                    // Skip empty logs or just separators
                    if (!cleanLog.trim() || cleanLog.trim() === '=' || /^=+$/.test(cleanLog.trim())) {
                        return;
                    }

                    // Parse log for progress information
                    let calculatedPercentage;

                    if (log.includes('PROGRESS:')) {
                        try {
                            const jsonStart = log.indexOf('{');
                            if (jsonStart !== -1) {
                                const p = JSON.parse(log.substring(jsonStart));
                                updateProgress('loadProfile', {
                                    message: p.message || 'Processing...',
                                    percentage: p.percentage || undefined
                                });
                                updateLogs('loadProfile', {
                                    type: 'progress',
                                    text: p.message || cleanLog
                                });
                            }
                        } catch (e) {
                            updateLogs('loadProfile', { type: 'info', text: cleanLog });
                        }
                    } else if (log.includes('YEAR_PROGRESS:')) {
                        const match = log.match(/Processing FY(\d+) \((\d+)\/(\d+)\)/);
                        if (match) {
                            const year = match[1];
                            const current = parseInt(match[2], 10);
                            const total = parseInt(match[3], 10);
                            if (total > 0) {
                                const basePercentage = 5;
                                const workRange = 94;
                                calculatedPercentage = basePercentage + (current / total) * workRange;
                                updateProgress('loadProfile', {
                                    percentage: Math.min(99, calculatedPercentage),
                                    message: `Processing FY${year} (${current}/${total})`
                                });
                                updateTaskProgress('loadProfile', {
                                    current,
                                    total
                                });
                            }
                            updateLogs('loadProfile', {
                                type: 'progress',
                                text: `Processing FY${year} (${current}/${total} years)`
                            });
                        }
                    } else if (log.includes('GENERATION COMPLETE') || log.includes('Generation completed successfully')) {
                        updateStatus('loadProfile', 'completed');
                        updateProgress('loadProfile', {
                            percentage: 100,
                            message: 'Profile generation completed!'
                        });
                        updateLogs('loadProfile', {
                            type: 'success',
                            text: '✅ Load profile generation completed successfully!'
                        });
                        toast.success('Load profile generated successfully!');
                        eventSource.close();
                    } else if (log.includes('FAILED') || log.includes('Error:') || log.includes('ERROR:')) {
                        // Check if it's actually a failure or just an informational error log
                        if (log.includes('FAILED') && !log.includes('profile generation')) {
                            updateStatus('loadProfile', 'failed');
                            updateLogs('loadProfile', {
                                type: 'error',
                                text: '❌ Profile generation failed'
                            });
                            toast.error('Load profile generation failed');
                            eventSource.close();
                        } else {
                            // Just log it as info (backend uses ERROR level for all stderr output)
                            updateLogs('loadProfile', { type: 'info', text: cleanLog });
                        }
                    } else {
                        // Determine log type based on content
                        let logType = 'info';
                        if (cleanLog.includes('✓') || cleanLog.includes('✅') || cleanLog.includes('successfully') || cleanLog.includes('completed')) {
                            logType = 'success';
                        } else if (cleanLog.includes('Processing') || cleanLog.includes('Generating') || cleanLog.includes('Loading') || cleanLog.includes('Extracting')) {
                            logType = 'progress';
                        } else if (cleanLog.includes('Warning') || cleanLog.includes('Note:')) {
                            logType = 'warning';
                        }

                        updateLogs('loadProfile', { type: logType, text: cleanLog });
                    }
                } catch (parseError) {
                    console.error('Error parsing SSE data:', parseError);
                }
            };

            eventSource.onerror = () => {
                updateStatus('loadProfile', 'failed', 'Connection error');
                updateLogs('loadProfile', {
                    type: 'error',
                    text: 'Connection to server lost'
                });
                toast.error('Connection error during generation');
                eventSource.close();
            };

        } catch (error) {
            console.error('Error starting profile generation:', error);
            toast.error('Failed to start profile generation');
        }
    };

    return (
        <>
            <div className="w-full h-full p-4 bg-slate-50 font-sans flex flex-col">
                <div className="w-full flex-grow max-w-7xl mx-auto bg-white rounded-xl shadow-lg border border-slate-200 flex flex-col">
                    <header className="flex-shrink-0 p-5 border-b border-slate-200">
                        <Stepper currentStep={state.currentStep} />
                    </header>

                    <main className="flex-grow p-6 overflow-y-auto">
                        {state.currentStep === 1 && <Step1 state={state} updateState={updateState} isLoading={isLoadingYears} years={availableBaseYears} />}
                        {state.currentStep === 2 && <Step2 state={state} updateState={updateState} isLoading={isLoadingScenarios} scenarios={availableScenarios} />}
                        {state.currentStep === 3 && <Step3 state={state} updateState={updateState} />}
                        {state.currentStep === 4 && <Step4 state={state} />}
                    </main>

                    <footer className="flex-shrink-0 flex justify-between items-center p-4 bg-slate-50/70 border-t border-slate-200">
                        <button
                            onClick={() => updateState({ currentStep: state.currentStep - 1 })}
                            className="flex items-center gap-2 text-sm font-semibold text-slate-700 bg-slate-200 hover:bg-slate-300 rounded-lg px-5 py-2.5 transition-all disabled:opacity-0 disabled:pointer-events-none"
                            disabled={state.currentStep === 1}
                        >
                            <ArrowLeft size={16} /> Back
                        </button>
                        {state.currentStep < 4 && (
                            <button
                                onClick={() => updateState({ currentStep: state.currentStep + 1 })}
                                disabled={(state.currentStep === 1 && !isStep1Valid) || (state.currentStep === 2 && !isStep2Valid) || (state.currentStep === 3 && !isStep3Valid)}
                                className="flex items-center gap-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg px-5 py-2.5 transition-all disabled:bg-slate-300 disabled:cursor-not-allowed"
                            >
                                Next <ArrowRight size={16} />
                            </button>
                        )}
                        {state.currentStep === 4 && (
                            <button
                                onClick={handleGenerateClick}
                                disabled={status === 'running'}
                                className="flex items-center gap-2 text-sm font-semibold text-white bg-green-600 hover:bg-green-700 rounded-lg px-5 py-2.5 transition-all shadow-lg shadow-green-500/20 disabled:bg-slate-300 disabled:cursor-not-allowed"
                            >
                                <Rocket size={16} /> Generate Profile
                            </button>
                        )}
                    </footer>
                </div>
            </div>

            {/* Process Modal with unified notification system */}
            {isModalVisible && profileProcess && (
                <ProcessModal
                    process={profileProcess}
                    onClose={() => {
                        resetProcess('loadProfile');
                        if (profileProcess.status === 'completed') {
                            handleNavigateToAnalysis();
                        } else {
                            resetAndClearState();
                        }
                    }}
                    onMinimize={hideModal}
                    onStop={null} // No stop endpoint for profile generation
                />
            )}

            {/* Floating Indicator when minimized */}
            {!isModalVisible && profileProcess?.status === 'running' && (
                <FloatingProcessIndicator
                    process={profileProcess}
                    onClick={() => showModal('loadProfile')}
                    onStop={null}
                />
            )}
        </>
    );
};


const Stepper = ({ currentStep }) => { const steps = [{ number: 1, title: "Method & Timeframe", icon: <Activity size={18} /> }, { number: 2, title: "Data Source", icon: <Database size={18} /> }, { number: 3, title: "Constraints", icon: <SlidersHorizontal size={18} /> }, { number: 4, title: "Review & Generate", icon: <FileText size={18} /> }]; return (<nav className="flex items-center justify-center" aria-label="Progress"> {steps.map((step, index) => (<React.Fragment key={step.number}> <div className="flex items-center gap-3"> <div className={`w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center transition-colors duration-300 ${currentStep >= step.number ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-500'}`}> {currentStep > step.number ? <Check size={20} /> : step.icon} </div> <div> <p className="text-xs text-slate-500">Step {step.number}</p> <p className={`font-semibold text-sm ${currentStep === step.number ? 'text-indigo-600' : 'text-slate-700'}`}>{step.title}</p> </div> </div> {index < steps.length - 1 && <div className="flex-1 h-0.5 mx-4 bg-slate-200" />} </React.Fragment>))} </nav>); };
const inputStyle = "w-full p-2 mt-1 bg-white border rounded-md text-xs text-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/20 outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed";
const cardStyle = "relative p-4 bg-white rounded-lg cursor-pointer border-2 transition-all duration-200 flex flex-col justify-center";
const selectedCardStyle = "border-indigo-600 shadow-sm";
const unselectedCardStyle = "border-slate-200 hover:border-indigo-400";
const MethodCard = ({ icon, title, description, isSelected, onClick, children }) => (<div onClick={onClick} className={`${cardStyle} ${isSelected ? selectedCardStyle : unselectedCardStyle}`}> {isSelected && <div className="absolute top-2 right-2 w-5 h-5 bg-indigo-600 text-white rounded-full flex items-center justify-center"><Check size={14} /></div>} <div className="flex items-center text-slate-600 mb-2">{icon}<h3 className="font-semibold text-slate-800 text-sm ml-2">{title}</h3></div> {description && <p className="text-xs text-slate-500">{description}</p>} <div className={`transition-all duration-500 ease-in-out overflow-hidden ${isSelected && children ? 'max-h-40 mt-2 pt-2 border-t border-slate-200' : 'max-h-0'}`}> {children} </div> </div>);


const Step1 = ({ state, updateState, isLoading, years }) => (
    <div className="space-y-6 animate-fade-in-up">
        <header><h1 className="text-2xl font-bold text-slate-900">Method & Timeframe</h1><p className="text-sm text-slate-500 mt-1">Choose the core method and define the profile's timeframe.</p></header>
        <section>
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Profile Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label htmlFor="profileName" className="text-xs text-slate-600 font-medium">Profile Name</label>
                    <input id="profileName" placeholder="Project_Profile_V1" type="text" value={state.profileName} onChange={(e) => updateState({ profileName: e.target.value })} className={`${inputStyle} ${state.profileNameError ? 'border-red-500' : 'border-slate-300'}`} />
                    {state.profileNameError && <p className="text-red-600 text-xs mt-1">{state.profileNameError}</p>}
                </div>
                <div><label htmlFor="startYear" className="text-xs text-slate-600 font-medium">Start Year</label><input id="startYear" type="number" value={state.startYear} onChange={(e) => updateState({ startYear: e.target.value })} className={`${inputStyle} border-slate-300`} /></div>
                <div><label htmlFor="endYear" className="text-xs text-slate-600 font-medium">End Year</label><input id="endYear" type="number" value={state.endYear} onChange={(e) => updateState({ endYear: e.target.value })} className={`${inputStyle} border-slate-300`} /></div>
            </div>
        </section>
        <section>
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Select Method</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <MethodCard
                    title="Base Profile Method"
                    description="Extrapolates a profile based on a single historical reference year."
                    isSelected={state.selectedMethod === 'base'}
                    onClick={() => updateState({ selectedMethod: 'base' })}
                >
                    <div>
                        <label htmlFor="baseYear" className="text-xs text-slate-600 font-medium">Base Year</label>
                        <select id="baseYear" value={state.baseYear} onChange={(e) => updateState({ baseYear: e.target.value })} className={`${inputStyle} border-slate-300`} onClick={(e) => e.stopPropagation()} disabled={isLoading || years.length === 0}>
                            {isLoading ? (<option>Loading...</option>) : years.length > 0 ? (years.map(year => (<option key={year} value={year}>{year}</option>))) : (<option value="">No historical data</option>)}
                        </select>
                    </div>
                </MethodCard>
                <MethodCard
                    title="STL Decomposition"
                    description="Advanced seasonal-trend analysis for better accuracy."
                    isSelected={state.selectedMethod === 'stl'}
                    onClick={() => updateState({ selectedMethod: 'stl' })}
                />
            </div>
        </section>
    </div>
);
const Step2 = ({ state, updateState, isLoading, scenarios }) => (<div className="flex flex-col justify-center animate-fade-in-up h-full"> <header className="mb-6 text-center"><h1 className="text-2xl font-bold text-slate-900">Total Demand Source</h1><p className="text-sm text-slate-500 mt-1">Choose where to pull annual demand targets from.</p></header> <div className="space-y-3 max-w-xl mx-auto w-full"> <MethodCard icon={<FileSpreadsheet size={18} />} title="Use 'Total Demand' sheet" description="Requires a 'Total_Demand' sheet in your input Excel file." isSelected={state.demandSource === 'template'} onClick={() => updateState({ demandSource: 'template' })} /> <MethodCard icon={<CheckCircle size={18} />} title="Use demand projection scenario" description="Uses the consolidated results from a previously run forecast." isSelected={state.demandSource === 'projection'} onClick={() => updateState({ demandSource: 'projection' })}> <div> <label htmlFor="projectionScenario" className="text-xs text-slate-600 font-medium">Select Projection Scenario</label> <select id="projectionScenario" value={state.projectionScenario} onChange={(e) => updateState({ projectionScenario: e.target.value })} className={`${inputStyle} border-slate-300`} onClick={(e) => e.stopPropagation()} disabled={isLoading || scenarios.length === 0}> {isLoading ? (<option>Loading scenarios...</option>) : scenarios.length > 0 ? (scenarios.map(s => (<option key={s} value={s}>{s}</option>))) : (<option value="">No scenarios found</option>)} </select> </div> </MethodCard> </div> </div>);
const Step3 = ({ state, updateState }) => (<div className="flex flex-col justify-center animate-fade-in-up h-full"> <header className="mb-6 text-center"><h1 className="text-2xl font-bold text-slate-900">Monthly Constraints</h1><p className="text-sm text-slate-500 mt-1">Choose how to apply monthly peak/min constraints to shape the profile.</p></header> <div className="space-y-3 max-w-xl mx-auto w-full"> {[{ value: 'auto', title: 'Auto-calculate from base year', desc: 'Automatically derive constraints from the selected base year data.' }, { value: 'excel', title: 'Use constraints from Excel file', desc: 'Read peak and minimum constraints from the input Excel template.' }, { value: 'none', title: 'No monthly constraints', desc: 'Generate the profile without applying any monthly constraints.' },].map(opt => (<label key={opt.value} className={`${cardStyle.replace('flex-grow', '')} flex items-start ${state.monthlyConstraint === opt.value ? selectedCardStyle : unselectedCardStyle}`}> <input type="radio" name="constraint" value={opt.value} checked={state.monthlyConstraint === opt.value} onChange={(e) => updateState({ monthlyConstraint: e.target.value })} className="h-4 w-4 mt-1 text-indigo-600 focus:ring-indigo-500 border-slate-300" /> <div className="ml-3"> <span className="text-sm font-bold text-slate-800">{opt.title}</span> <p className="text-xs text-slate-500">{opt.desc}</p> </div> </label>))} </div> </div>);
const Step4 = ({ state }) => { const SummaryItem = ({ label, value }) => value ? (<div><dt className="text-xs font-medium text-slate-500">{label}</dt><dd className="mt-1 text-sm font-semibold text-slate-900">{value}</dd></div>) : null; return (<div className="animate-fade-in-up"> <header className="mb-6"><h1 className="text-2xl font-bold text-slate-900">Review & Generate</h1><p className="text-sm text-slate-500 mt-1">Confirm the settings below before starting the generation process.</p></header> <div className="space-y-4 p-4 bg-slate-50/80 rounded-lg border border-slate-200"> <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4"> <SummaryItem label="Profile Name" value={state.profileName} /> <SummaryItem label="Timeframe" value={`${state.startYear} to ${state.endYear}`} /> <SummaryItem label="Generation Method" value={state.selectedMethod === 'base' ? 'Base Profile' : 'STL Decomposition'} /> <SummaryItem label="Base Profile Year" value={state.selectedMethod === 'base' ? state.baseYear : 'N/A'} /> <SummaryItem label="Total Demand Source" value={state.demandSource === 'template' ? 'Template Sheet' : 'Projection Scenario'} /> <SummaryItem label="Projection Scenario" value={state.demandSource === 'projection' ? state.projectionScenario : 'N/A'} /> <SummaryItem label="Monthly Constraints" value={state.monthlyConstraint ? state.monthlyConstraint.charAt(0).toUpperCase() + state.monthlyConstraint.slice(1) : ''} /> </dl> </div> </div>); };


export default GenerateProfiles;