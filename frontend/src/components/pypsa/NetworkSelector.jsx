import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Folder, FileText, RefreshCw, Loader2, AlertCircle } from 'lucide-react';

const NetworkSelector = ({
  projectPath,
  onSelect,
  selectedScenario,
  selectedNetwork,
  selectedNetworks = [],
  multiSelect = false
}) => {
  const [scenarios, setScenarios] = useState([]);
  const [networks, setNetworks] = useState([]);
  const [loadingScenarios, setLoadingScenarios] = useState(false);
  const [loadingNetworks, setLoadingNetworks] = useState(false);
  const [error, setError] = useState(null);
  const [pendingScenario, setPendingScenario] = useState(selectedScenario || '');
  const [pendingNetwork, setPendingNetwork] = useState(() => {
    if (multiSelect) {
      if (selectedNetworks && selectedNetworks.length) {
        return selectedNetworks;
      }
      if (selectedNetwork) {
        return [selectedNetwork];
      }
      return [];
    }
    return selectedNetwork || '';
  });

  const isMultiSelect = multiSelect;

  const areArraysEqual = (a, b) => {
    if (!Array.isArray(a) || !Array.isArray(b)) {
      return false;
    }
    if (a.length !== b.length) {
      return false;
    }
    const sortedA = [...a].sort();
    const sortedB = [...b].sort();
    for (let i = 0; i < sortedA.length; i += 1) {
      if (sortedA[i] !== sortedB[i]) {
        return false;
      }
    }
    return true;
  };

  const pendingNetworksArray = isMultiSelect ? (Array.isArray(pendingNetwork) ? pendingNetwork : []) : [];
  const selectedNetworksArray = isMultiSelect ? (Array.isArray(selectedNetworks) ? selectedNetworks : []) : [];
  const isPendingEmpty = isMultiSelect ? pendingNetworksArray.length === 0 : !pendingNetwork;
  const isSameSelection = selectedScenario === pendingScenario && (
    isMultiSelect ? areArraysEqual(selectedNetworksArray, pendingNetworksArray) : selectedNetwork === pendingNetwork
  );
  // Reserved for future use - may be used to disable apply button
  // eslint-disable-next-line no-unused-vars
  const isApplyDisabled = !pendingScenario || isPendingEmpty || loadingScenarios || loadingNetworks || isSameSelection;
  const pendingNetworkDisplay = isMultiSelect
    ? (pendingNetworksArray.length ? pendingNetworksArray.join(', ') : '—')
    : (pendingNetwork || '—');
  const activeNetworkDisplay = isMultiSelect
    ? (selectedNetworksArray.length ? selectedNetworksArray.join(', ') : '—')
    : (selectedNetwork || '—');

  useEffect(() => {
    if (projectPath) {
      fetchScenarios();
    } else {
      setScenarios([]);
      setNetworks([]);
      setPendingScenario('');
      setPendingNetwork(isMultiSelect ? [] : '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectPath, isMultiSelect]);

  useEffect(() => {
    if (selectedScenario) {
      setPendingScenario(selectedScenario);
    } else {
      setPendingScenario('');
    }
  }, [selectedScenario]);

  useEffect(() => {
    if (isMultiSelect) {
      if (selectedNetworks && selectedNetworks.length) {
        setPendingNetwork(selectedNetworks);
      } else if (selectedNetwork) {
        setPendingNetwork([selectedNetwork]);
      } else {
        setPendingNetwork([]);
      }
    } else if (selectedNetwork) {
      setPendingNetwork(selectedNetwork);
    } else {
      setPendingNetwork('');
    }
  }, [selectedNetwork, selectedNetworks, isMultiSelect]);

  useEffect(() => {
    if (projectPath && pendingScenario) {
      fetchNetworks(pendingScenario);
    } else {
      setNetworks([]);
      setPendingNetwork(isMultiSelect ? [] : '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectPath, pendingScenario, isMultiSelect]);

  const fetchScenarios = async () => {
    setLoadingScenarios(true);
    setError(null);

    try {
      const response = await axios.get('/project/pypsa/scenarios', {
        params: { projectPath }
      });

      if (response.data.success) {
        const scenarioList = response.data.scenarios || [];
        setScenarios(scenarioList);
        setPendingScenario(prev => {
          if (prev && scenarioList.includes(prev)) {
            return prev;
          }
          if (selectedScenario && scenarioList.includes(selectedScenario)) {
            return selectedScenario;
          }
          return '';
        });
        if (scenarioList.length === 0) {
          setPendingNetwork(isMultiSelect ? [] : '');
          setNetworks([]);
        }
      } else {
        setError(response.data.message || 'Failed to load scenarios');
      }
    } catch (err) {
      console.error('Error fetching scenarios:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          err.message || 
                          'Failed to load scenarios. Please check your project path.';
      setError(errorMessage);
    } finally {
      setLoadingScenarios(false);
    }
  };

  const fetchNetworks = async (scenario) => {
    setLoadingNetworks(true);
    setError(null);

    try {
      const response = await axios.get('/project/pypsa/networks', {
        params: {
          projectPath,
          scenarioName: scenario
        }
      });

      if (response.data.success) {
        const networkList = response.data.networks || [];
        setNetworks(networkList);

        if (isMultiSelect) {
          const allNames = networkList.map(item => item.name);
          let nextSelection = [];

          if (pendingNetworksArray.length && pendingNetworksArray.every(name => allNames.includes(name))) {
            nextSelection = pendingNetworksArray;
          } else if (selectedScenario === scenario && selectedNetworksArray.length) {
            const valid = selectedNetworksArray.filter(name => allNames.includes(name));
            if (valid.length) {
              nextSelection = valid;
            }
          } else if (selectedScenario === scenario && selectedNetwork && allNames.includes(selectedNetwork)) {
            nextSelection = [selectedNetwork];
          }

          if (!nextSelection.length) {
            nextSelection = allNames;
          }

          setPendingNetwork(nextSelection);
        } else {
          setPendingNetwork(prev => {
            if (prev && networkList.some(item => item.name === prev)) {
              return prev;
            }
            if (selectedScenario === scenario && selectedNetwork && networkList.some(item => item.name === selectedNetwork)) {
              return selectedNetwork;
            }
            return '';
          });
        }
      } else {
        setError(response.data.message || 'Failed to load network files');
      }
    } catch (err) {
      console.error('Error fetching networks:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.message || 
                          err.message || 
                          'Failed to load network files for this scenario.';
      setError(errorMessage);
    } finally {
      setLoadingNetworks(false);
    }
  };

  const handleScenarioChange = (e) => {
    const scenario = e.target.value;
    setPendingScenario(scenario);
    setPendingNetwork(isMultiSelect ? [] : '');
  };

  const handleNetworkChange = (e) => {
    if (isMultiSelect) {
      const selected = Array.from(e.target.selectedOptions, option => option.value);
      setPendingNetwork(selected);
    } else {
      const network = e.target.value;
      setPendingNetwork(network);
    }
  };

  const handleRefresh = () => {
    fetchScenarios();
    if (pendingScenario) {
      fetchNetworks(pendingScenario);
    }
  };

  const handleSubmit = () => {
    if (!pendingScenario || isPendingEmpty) {
      return;
    }
    if (isMultiSelect) {
      onSelect(pendingScenario, pendingNetworksArray);
    } else {
      onSelect(pendingScenario, pendingNetwork);
    }
  };

  if (!projectPath) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-yellow-600" />
        <p className="text-sm text-yellow-800">No active project. Please load or create a project first.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Folder className="w-5 h-5 text-blue-600" />
          Network Selection
        </h3>
        <button
          onClick={handleRefresh}
          disabled={loadingScenarios || loadingNetworks}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${(loadingScenarios || loadingNetworks) ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className={`grid grid-cols-1 ${networks.length === 1 ? '' : 'md:grid-cols-2'} gap-4`}>
        {/* Scenario Selector */}
        <div>
          <label htmlFor="scenario-select" className="block text-sm font-medium text-slate-700 mb-2">
            Scenario
          </label>
          <div className="relative">
            <select
              id="scenario-select"
              value={pendingScenario}
              onChange={handleScenarioChange}
              disabled={loadingScenarios || scenarios.length === 0}
              className="w-full p-2.5 pr-10 border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-50 disabled:cursor-not-allowed"
            >
              <option value="">
                {loadingScenarios ? 'Loading scenarios...' :
                  scenarios.length === 0 ? 'No scenarios found' :
                    'Select a scenario'}
              </option>
              {scenarios.map((scenario) => (
                <option key={scenario} value={scenario}>
                  {scenario}
                </option>
              ))}
            </select>
            {loadingScenarios && (
              <Loader2 className="absolute right-3 top-3 w-5 h-5 animate-spin text-blue-600" />
            )}
          </div>
          {scenarios.length > 0 && (
            <p className="mt-1 text-xs text-slate-500">{scenarios.length} scenario(s) available</p>
          )}
        </div>

        {/* Single Network File Indicator */}
        {networks.length === 1 && pendingScenario && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Network File
            </label>
            <div className="p-2.5 border border-green-300 bg-green-50 rounded-md shadow-sm">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800 font-medium">
                  {networks[0].name} ({networks[0].size_mb.toFixed(1)} MB)
                </span>
              </div>
            </div>
            <p className="mt-1 text-xs text-green-600">
              ✓ Single file auto-selected
            </p>
          </div>
        )}

        {/* Network File Selector - Hide if only 1 file */}
        {networks.length !== 1 && (
          <div>
            <label htmlFor="network-select" className="block text-sm font-medium text-slate-700 mb-2">
              Network File{isMultiSelect ? 's' : ''}
            </label>
            <div className="relative">
              <select
                id="network-select"
                value={pendingNetwork}
                onChange={handleNetworkChange}
                multiple={isMultiSelect}
                disabled={!pendingScenario || loadingNetworks || networks.length === 0}
                className={`w-full p-2.5 ${isMultiSelect ? 'pr-4 min-h-[120px]' : 'pr-10'} border border-slate-300 rounded-md shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-slate-50 disabled:cursor-not-allowed`}
                size={isMultiSelect ? Math.min(Math.max(networks.length, 3), 10) : undefined}
              >
                {!isMultiSelect && (
                  <option value="">
                    {!pendingScenario ? 'Select scenario first' :
                      loadingNetworks ? 'Loading networks...' :
                        networks.length === 0 ? 'No network files found' :
                          'Select a network file'}
                  </option>
                )}
                {networks.map((network) => (
                  <option key={network.name} value={network.name}>
                    {network.name} ({network.size_mb.toFixed(1)} MB)
                  </option>
                ))}
              </select>
              {loadingNetworks && (
                <Loader2 className="absolute right-3 top-3 w-5 h-5 animate-spin text-blue-600" />
              )}
            </div>
            {networks.length > 0 && (
              <p className="mt-1 text-xs text-slate-500">
                {isMultiSelect ? 'All network files selected by default. Hold Ctrl/Cmd to modify selection.' : `${networks.length} network file(s) available`}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Pending Selection Display */}
      <div className="mt-4 space-y-2">
        <div className="bg-slate-50 border border-slate-200 rounded-md p-3 text-sm text-slate-700">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-500" />
            <span className="font-medium">Pending Selection:</span>
            <span className="font-mono">
              {pendingScenario || '—'} / {pendingNetworkDisplay}
            </span>
          </div>
        </div>
        {selectedScenario && (selectedNetwork || (selectedNetworksArray.length > 0)) && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm text-blue-800">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span className="font-medium">Active Selection:</span>
              <span className="font-mono">{selectedScenario} / {activeNetworkDisplay}</span>
            </div>
          </div>
        )}
        <button
          onClick={handleSubmit}
          disabled={!pendingScenario || !pendingNetwork || loadingScenarios || loadingNetworks || (selectedScenario === pendingScenario && selectedNetwork === pendingNetwork)}
          className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-md font-medium text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Apply Selection
        </button>
      </div>
    </div>
  );
};

export default NetworkSelector;
