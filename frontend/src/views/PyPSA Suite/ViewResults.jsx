/**
 * View Results - Updated to Use Unified Network View
 * ===================================================
 * 
 * Main container for viewing PyPSA optimization results.
 * Now uses the UnifiedNetworkView component instead of multiple specialized views.
 * 
 * Features:
 * - Toggle between Excel results and Network analysis
 * - Network selector for scenarios and files
 * - Seamless integration with UnifiedNetworkView
 * - No more jarring component switches!
 * 
 * Changes from original:
 * - Removed: MultiYearNetworkView
 * - Removed: SingleNetworkView
 * - Removed: Multi-year detection logic
 * - Added: Direct use of UnifiedNetworkView
 * - Benefit: Cleaner, simpler, more maintainable
 */

import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Loader2, 
  AreaChart as AreaIcon, 
  BarChart3 as BarIcon, 
  FileSpreadsheet, 
  Network,
  AlertCircle
} from 'lucide-react';

// Chart components for Excel view
import AreaChartComponent from '../../components/charts/AreaChartComponent';
import StackedBarChartComponent from '../../components/charts/StackedBarChartComponent';

// PyPSA Components
import NetworkSelector from '../../components/pypsa/NetworkSelector';
import UnifiedNetworkView from './UnifiedNetworkView';

const ViewResults = ({ activeProject: activeProjectProp }) => {
  // ====== PROJECT STATE ======
  const [activeProject, setActiveProject] = useState(activeProjectProp);
  
  // Initialize active project from storage if not provided as prop
  useEffect(() => {
    if (!activeProjectProp) {
      const projectString = 
        sessionStorage.getItem('activeProject') ||
        sessionStorage.getItem('currentProject') ||
        localStorage.getItem('activeProject') ||
        localStorage.getItem('currentProject');
      
      if (projectString) {
        try {
          const project = JSON.parse(projectString);
          setActiveProject(project);
        } catch (error) {
          console.error('[ViewResults] Error parsing project from storage:', error);
        }
      }
    } else {
      setActiveProject(activeProjectProp);
    }
  }, [activeProjectProp]);
  
  // ====== VIEW MODE STATE ======
  const [viewMode, setViewMode] = useState('network'); // 'excel' or 'network'
  
  // ====== EXCEL RESULTS STATE ======
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [sheets, setSheets] = useState([]);
  const [selectedSheet, setSelectedSheet] = useState('');
  const [sheetData, setSheetData] = useState([]);
  const [chartType, setChartType] = useState('Area');
  
  // ====== NETWORK ANALYSIS STATE ======
  const [selectedScenario, setSelectedScenario] = useState('');
  const [selectedNetwork, setSelectedNetwork] = useState('');
  const [selectedNetworks, setSelectedNetworks] = useState([]);
  
  // ====== LOADING STATES ======
  const [loadingFolders, setLoadingFolders] = useState(false);
  const [loadingSheets, setLoadingSheets] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [folderError, setFolderError] = useState(null);
  const [sheetError, setSheetError] = useState(null);
  const [dataError, setDataError] = useState(null);
  
  // ====== EXCEL DATA FETCHING ======
  
  // Fetch folders
  useEffect(() => {
    if (activeProject?.path && viewMode === 'excel') {
      setLoadingFolders(true);
      setFolderError(null);
      
      axios.get('/project/optimization-folders', { 
        params: { projectPath: activeProject.path } 
      })
        .then(res => {
          setFolders(res.data.folders);
          if (res.data.folders.length > 0) {
            setSelectedFolder(res.data.folders[0]);
          }
        })
        .catch(err => {
          console.error("Error fetching folders:", err);
          setFolderError(err.response?.data?.detail || err.message || "Failed to load folders");
        })
        .finally(() => setLoadingFolders(false));
    }
  }, [activeProject, viewMode]);
  
  // Fetch sheets
  useEffect(() => {
    if (selectedFolder && activeProject?.path && viewMode === 'excel') {
      setLoadingSheets(true);
      setSheetError(null);
      setSheets([]);
      setSelectedSheet('');
      setSheetData([]);
      
      axios.get('/project/optimization-sheets', { 
        params: { 
          projectPath: activeProject.path, 
          folderName: selectedFolder 
        } 
      })
        .then(res => {
          setSheets(res.data.sheets);
          if (res.data.sheets.length > 0) {
            setSelectedSheet(res.data.sheets[0]);
          }
        })
        .catch(err => {
          console.error("Error fetching sheets:", err);
          setSheetError(err.response?.data?.detail || err.message || "Failed to load sheets");
        })
        .finally(() => setLoadingSheets(false));
    }
  }, [selectedFolder, activeProject, viewMode]);
  
  // Fetch sheet data
  useEffect(() => {
    if (selectedSheet && selectedFolder && activeProject?.path && viewMode === 'excel') {
      setLoadingData(true);
      setDataError(null);
      setSheetData([]);
      
      axios.get('/project/optimization-sheet-data', { 
        params: { 
          projectPath: activeProject.path, 
          folderName: selectedFolder, 
          sheetName: selectedSheet 
        } 
      })
        .then(res => {
          setSheetData(res.data.data);
        })
        .catch(err => {
          console.error("Error fetching sheet data:", err);
          setDataError(err.response?.data?.detail || err.message || "Failed to load sheet data");
        })
        .finally(() => setLoadingData(false));
    }
  }, [selectedSheet, selectedFolder, activeProject, viewMode]);
  
  // Extract data keys for Excel charts
  const dataKeys = useMemo(() =>
    sheetData.length > 0 
      ? Object.keys(sheetData[0]).filter(key => key.toLowerCase() !== 'year') 
      : [],
    [sheetData]
  );
  
  // ====== NETWORK SELECTION HANDLER ======
  const handleNetworkSelect = (scenario, networksOrNetwork) => {
    setSelectedScenario(scenario);

    // Handle both single network and array of networks
    if (Array.isArray(networksOrNetwork)) {
      setSelectedNetworks(networksOrNetwork);
      setSelectedNetwork(networksOrNetwork[0] || ''); // Use first network for UnifiedNetworkView
    } else {
      setSelectedNetwork(networksOrNetwork);
      setSelectedNetworks([networksOrNetwork]);
    }
  };
  
  // ====== PROJECT PATH ======
  const projectPath = activeProject?.path;
  
  // ====== RENDER ======
  
  if (!activeProject) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <AlertCircle className="w-16 h-16 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Project Loaded</h3>
          <p className="text-sm">Please load or create a project to view results.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="view-results h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">View Results</h1>
            <p className="text-sm text-gray-600 mt-1">
              {activeProject.name} - Analysis and Visualization
            </p>
          </div>
          
          {/* View Mode Selector */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('excel')}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                ${viewMode === 'excel'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'}
              `}
            >
              <FileSpreadsheet className="w-4 h-4" />
              Excel Results
            </button>
            <button
              onClick={() => setViewMode('network')}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                ${viewMode === 'network'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'}
              `}
            >
              <Network className="w-4 h-4" />
              Network Analysis
            </button>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'excel' ? (
          /* Excel View */
          <div className="h-full p-6 overflow-y-auto">
            <div className="max-w-7xl mx-auto space-y-6">
              {/* Folder Selection */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Optimization Folder
                </label>
                {loadingFolders ? (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Loading folders...</span>
                  </div>
                ) : folderError ? (
                  <div className="text-sm text-red-600">{folderError}</div>
                ) : (
                  <select
                    value={selectedFolder}
                    onChange={(e) => setSelectedFolder(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Select Folder --</option>
                    {folders.map(folder => (
                      <option key={folder} value={folder}>{folder}</option>
                    ))}
                  </select>
                )}
              </div>
              
              {/* Sheet Selection */}
              {selectedFolder && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Sheet
                  </label>
                  {loadingSheets ? (
                    <div className="flex items-center gap-2 text-gray-600">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Loading sheets...</span>
                    </div>
                  ) : sheetError ? (
                    <div className="text-sm text-red-600">{sheetError}</div>
                  ) : (
                    <select
                      value={selectedSheet}
                      onChange={(e) => setSelectedSheet(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">-- Select Sheet --</option>
                      {sheets.map(sheet => (
                        <option key={sheet} value={sheet}>{sheet}</option>
                      ))}
                    </select>
                  )}
                </div>
              )}
              
              {/* Chart Type Selection */}
              {selectedSheet && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chart Type
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setChartType('Area')}
                      className={`
                        flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                        ${chartType === 'Area'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
                      `}
                    >
                      <AreaIcon className="w-4 h-4" />
                      Area Chart
                    </button>
                    <button
                      onClick={() => setChartType('StackedBar')}
                      className={`
                        flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                        ${chartType === 'StackedBar'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
                      `}
                    >
                      <BarIcon className="w-4 h-4" />
                      Stacked Bar
                    </button>
                  </div>
                </div>
              )}
              
              {/* Chart Display */}
              {selectedSheet && sheetData.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  {loadingData ? (
                    <div className="flex items-center justify-center py-16">
                      <div className="flex flex-col items-center gap-4">
                        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
                        <span className="text-sm font-medium text-gray-600">Loading data...</span>
                      </div>
                    </div>
                  ) : dataError ? (
                    <div className="text-center text-red-600 py-8">{dataError}</div>
                  ) : chartType === 'Area' ? (
                    <AreaChartComponent data={sheetData} dataKeys={dataKeys} />
                  ) : (
                    <StackedBarChartComponent data={sheetData} dataKeys={dataKeys} />
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Network View */
          <div className="h-full flex flex-col">
            {/* Network Selector */}
            <div className="bg-white border-b border-gray-200 p-6">
              <NetworkSelector
                projectPath={projectPath}
                onSelect={handleNetworkSelect}
                selectedScenario={selectedScenario}
                selectedNetwork={selectedNetwork}
                selectedNetworks={selectedNetworks}
                multiSelect={true}
              />
            </div>
            
            {/* Unified Network View */}
            <div className="flex-1 overflow-hidden">
              {selectedScenario && selectedNetwork ? (
                <>
                  {/* Show multi-network indicator if multiple files selected */}
                  {selectedNetworks.length > 1 && (
                    <div className="bg-blue-50 border-b border-blue-200 px-6 py-3">
                      <div className="flex items-center gap-2 text-sm text-blue-800">
                        <AlertCircle className="w-4 h-4" />
                        <span>
                          <strong>{selectedNetworks.length} networks selected:</strong> {selectedNetworks.join(', ')}
                        </span>
                      </div>
                      <p className="text-xs text-blue-600 mt-1">
                        Currently analyzing: <strong>{selectedNetwork}</strong>
                      </p>
                    </div>
                  )}
                  <UnifiedNetworkView
                    projectPath={projectPath}
                    selectedScenario={selectedScenario}
                    selectedNetwork={selectedNetwork}
                  />
                </>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <Network className="w-16 h-16 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Select a Network</h3>
                    <p className="text-sm">Choose a scenario and network file(s) to begin analysis</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViewResults;