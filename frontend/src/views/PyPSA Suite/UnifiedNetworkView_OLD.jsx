/**
 * Unified Network View - Streamlit-Style PyPSA Visualization
 * ===========================================================
 *
 * Matches Streamlit UI exactly:
 * - Single-period: Show tabs (Dispatch & Load, Capacity, etc.)
 * - Multi-period: Show period selector + tabs + cross-period comparison
 * - Multi-file: Show year selector + tabs + year-to-year comparison
 *
 * NO categorization, NO complex filtering - simple and clean like Streamlit
 */

import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import {
  Activity,
  BarChart3,
  TrendingUp,
  Battery,
  CloudOff,
  DollarSign,
  Network,
  Loader2,
  AlertCircle,
  RefreshCw,
  Table as TableIcon
} from 'lucide-react';

// Hooks
import usePyPSAData from '../../hooks/usePyPSAData';
import usePyPSAAvailability from '../../hooks/usePyPSAAvailability';
import useNetworkDetection from '../../hooks/useNetworkDetection';

// Components
import UnifiedChart from '../../components/charts/UnifiedChart';

// Utils
import { transformPyPSAData, getChartConfig } from '../../utils/pypsaDataTransformer';

// ============================================================================
// TAB DEFINITIONS (matching Streamlit)
// ============================================================================

const SINGLE_PERIOD_TABS = [
  { id: 'dispatch', label: 'Dispatch & Load', icon: Activity, endpoint: '/pypsa/dispatch' },
  { id: 'capacity', label: 'Capacity', icon: BarChart3, endpoint: '/pypsa/total-capacities' },
  { id: 'metrics', label: 'Metrics', icon: TrendingUp, endpoint: '/pypsa/renewable-share' },
  { id: 'storage', label: 'Storage', icon: Battery, endpoint: '/pypsa/storage-units' },
  { id: 'emissions', label: 'Emissions', icon: CloudOff, endpoint: '/pypsa/emissions' },
  { id: 'prices', label: 'Prices', icon: DollarSign, endpoint: '/pypsa/system-costs' },
  { id: 'network_flow', label: 'Network Flow', icon: Network, endpoint: '/pypsa/lines' }
];

const RESOLUTION_OPTIONS = [
  { value: '1H', label: '1 Hour' },
  { value: '3H', label: '3 Hours' },
  { value: '6H', label: '6 Hours' },
  { value: '12H', label: '12 Hours' },
  { value: '1D', label: '1 Day' },
  { value: '1W', label: '1 Week' }
];

const COMPARISON_TYPES = [
  { id: 'capacity', label: 'Capacity Comparison' },
  { id: 'generation', label: 'Generation Comparison' },
  { id: 'metrics', label: 'Metrics Comparison' },
  { id: 'emissions', label: 'Emissions Comparison' }
];

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * Loading Spinner
 */
const LoadingSpinner = ({ message = "Loading..." }) => (
  <div className="flex items-center justify-center py-16">
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
      <span className="text-sm font-medium text-gray-600">{message}</span>
    </div>
  </div>
);

/**
 * Error Message
 */
const ErrorMessage = ({ error, onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
    <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
    <h3 className="text-lg font-semibold text-red-900 mb-2">Error Loading Data</h3>
    <p className="text-sm text-red-700 mb-4">{error}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Retry
      </button>
    )}
  </div>
);

/**
 * Simple Tab Sidebar - Matches Streamlit
 */
const TabSidebar = ({ tabs, activeTab, onTabChange, title }) => (
  <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
    <div className="p-4 border-b border-gray-200">
      <h3 className="font-semibold text-gray-900">{title}</h3>
    </div>

    <div className="p-2">
      {tabs.map(tab => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              w-full flex items-center gap-3 px-4 py-3 text-sm rounded-lg transition-all mb-1
              ${isActive
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-700 hover:bg-gray-100'}
            `}
          >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{tab.label}</span>
          </button>
        );
      })}
    </div>
  </div>
);

/**
 * Network Type Header - Shows detection result
 */
const NetworkTypeHeader = ({ detection }) => {
  if (!detection) return null;

  const { workflow_type, periods, years } = detection;

  let message = '';
  let color = 'blue';

  if (workflow_type === 'single-period') {
    message = detection.year
      ? `Single period network (Year ${detection.year})`
      : 'Single period network detected';
    color = 'green';
  } else if (workflow_type === 'multi-period') {
    message = `Multi-period network detected with ${periods?.length || 0} periods`;
    color = 'purple';
  } else if (workflow_type === 'multi-file') {
    message = `Multiple files detected (year_XXXX.nc format) - ${years?.length || 0} years available`;
    color = 'orange';
  }

  return (
    <div className={`bg-${color}-50 border border-${color}-200 rounded-lg p-3 mb-4`}>
      <p className={`text-sm font-medium text-${color}-900`}>{message}</p>
    </div>
  );
};

/**
 * Period Selector for Multi-Period Networks
 */
const PeriodSelector = ({ periods, selectedPeriod, onChange }) => {
  if (!periods || periods.length === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select period for analysis:
      </label>
      <select
        value={selectedPeriod}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {periods.map(period => (
          <option key={period} value={period}>
            Period {period}
          </option>
        ))}
      </select>
    </div>
  );
};

/**
 * Year Selector for Multi-File Networks
 */
const YearSelector = ({ years, selectedYear, onChange }) => {
  if (!years || years.length === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Select year for detailed analysis:
      </label>
      <select
        value={selectedYear}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {years.map(year => (
          <option key={year} value={year}>
            Year {year}
          </option>
        ))}
      </select>
    </div>
  );
};

/**
 * Date Range Selector for Dispatch & Load
 */
const DateRangeSelector = ({ startDate, endDate, onStartChange, onEndChange, onClear, show }) => {
  if (!show) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <label className="block text-sm font-medium text-gray-700">
          Filter by Date Range (Optional):
        </label>
        {(startDate || endDate) && (
          <button
            onClick={onClear}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear Filter
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate || ''}
            onChange={(e) => onStartChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-1">End Date</label>
          <input
            type="date"
            value={endDate || ''}
            onChange={(e) => onEndChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      {startDate && endDate && startDate > endDate && (
        <p className="text-xs text-red-600 mt-2">Start date must be before end date</p>
      )}
    </div>
  );
};

/**
 * Resolution Selector for Dispatch & Load
 */
const ResolutionSelector = ({ resolution, onChange, options, show }) => {
  if (!show) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Time Resolution:
      </label>
      <select
        value={resolution}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
};

/**
 * Comparison Section for Multi-Period/Multi-File
 */
const ComparisonSection = ({ type, items, selectedItems, onItemsChange, comparisonTypes, activeComparison, onComparisonChange }) => {
  const itemLabel = type === 'period' ? 'Period' : 'Year';
  const sectionTitle = type === 'period' ? 'Cross-Period Comparison' : 'Year-to-Year Comparison';

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <h4 className="font-semibold text-gray-900 mb-3">{sectionTitle}</h4>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select {itemLabel.toLowerCase()}s to compare:
        </label>
        <div className="flex flex-wrap gap-2">
          {items.map(item => {
            const isSelected = selectedItems.includes(item);
            return (
              <button
                key={item}
                onClick={() => {
                  if (isSelected) {
                    onItemsChange(selectedItems.filter(i => i !== item));
                  } else {
                    onItemsChange([...selectedItems, item]);
                  }
                }}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${isSelected
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}
                `}
              >
                {itemLabel} {item}
              </button>
            );
          })}
        </div>
      </div>

      {selectedItems.length >= 2 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Comparison type:
          </label>
          <div className="grid grid-cols-2 gap-2">
            {comparisonTypes.map(comp => {
              const isActive = activeComparison === comp.id;
              return (
                <button
                  key={comp.id}
                  onClick={() => onComparisonChange(comp.id)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${isActive
                      ? 'bg-purple-600 text-white shadow-md'
                      : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'}
                  `}
                >
                  {comp.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// MULTI-YEAR STACKED VISUALIZATIONS WITH EXPORT
// ============================================================================

/**
 * Multi-Year Comparison View with Stacked Bar Charts and Export
 */
const MultiYearStackedView = ({ projectPath, scenarioName }) => {
  const [activeView, setActiveView] = useState('capacity');

  // Fetch stacked capacity evolution
  const { data: capacityData, loading: capacityLoading } = usePyPSAData(
    '/pypsa/multi-year/stacked-capacity-evolution',
    { projectPath, scenarioName },
    activeView === 'capacity'
  );

  // Fetch new capacity additions
  const { data: additionsData, loading: additionsLoading } = usePyPSAData(
    '/pypsa/multi-year/new-capacity-additions',
    { projectPath, scenarioName },
    activeView === 'additions'
  );

  // Fetch emissions evolution
  const { data: emissionsData, loading: emissionsLoading } = usePyPSAData(
    '/pypsa/multi-year/stacked-emissions-evolution',
    { projectPath, scenarioName },
    activeView === 'emissions'
  );

  // Fetch cost evolution
  const { data: costData, loading: costLoading } = usePyPSAData(
    '/pypsa/multi-year/total-cost-evolution',
    { projectPath, scenarioName },
    activeView === 'cost'
  );

  // Export to CSV
  const exportToCSV = (data, filename) => {
    if (!data || data.length === 0) return;

    // Convert data to CSV
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(h => row[h] || 0).join(','))
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Export to PNG (using html2canvas)
  const exportToPNG = async (elementId, filename) => {
    try {
      const element = document.getElementById(elementId);
      if (!element) return;

      // Dynamic import of html2canvas
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(element, {
        backgroundColor: '#ffffff',
        scale: 2
      });

      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
        link.click();
        URL.revokeObjectURL(url);
      });
    } catch (error) {
      console.error('Error exporting to PNG:', error);
      alert('Export to PNG failed. Make sure html2canvas is installed.');
    }
  };

  const views = [
    { id: 'capacity', label: 'Total Capacity Evolution', data: capacityData, loading: capacityLoading },
    { id: 'additions', label: 'New Capacity Additions', data: additionsData, loading: additionsLoading },
    { id: 'emissions', label: 'Emissions Evolution', data: emissionsData, loading: emissionsLoading },
    { id: 'cost', label: 'Cost Evolution', data: costData, loading: costLoading }
  ];

  const currentView = views.find(v => v.id === activeView);
  const chartData = currentView?.data?.data || [];
  const dataKeys = currentView?.data?.carriers || currentView?.data?.cost_types || [];

  return (
    <div className="mt-6 space-y-4">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Multi-Year Comparison</h3>

          {/* Export Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => exportToCSV(chartData, `${activeView}_evolution`)}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              disabled={!chartData || chartData.length === 0}
            >
              📊 Export CSV
            </button>
            <button
              onClick={() => exportToPNG('multi-year-chart', `${activeView}_evolution`)}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              disabled={!chartData || chartData.length === 0}
            >
              🖼️ Export PNG
            </button>
          </div>
        </div>

        {/* View Selector */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {views.map(view => (
            <button
              key={view.id}
              onClick={() => setActiveView(view.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeView === view.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {view.label}
            </button>
          ))}
        </div>

        {/* Chart Display */}
        <div id="multi-year-chart">
          {currentView?.loading ? (
            <LoadingSpinner message={`Loading ${currentView.label}...`} />
          ) : chartData && chartData.length > 0 ? (
            <UnifiedChart
              data={chartData}
              type="stacked-bar"
              config={{
                type: 'stacked-bar',
                xAxisKey: 'year',
                dataKeys: dataKeys,
                yAxisLabel: activeView === 'capacity' ? 'Capacity (MW)' :
                           activeView === 'emissions' ? 'Emissions (tonnes CO2)' :
                           activeView === 'cost' ? 'Cost (currency)' : 'Value',
                title: currentView.label,
                colors: {}  // Will use PYPSA_COLORS from config
              }}
              height={500}
            />
          ) : (
            <div className="text-center py-12 text-gray-500">
              No multi-year data available. Need at least 2 year network files.
            </div>
          )}
        </div>

        {/* Data Summary */}
        {chartData && chartData.length > 0 && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Years Analyzed</p>
                <p className="font-semibold">{chartData.length}</p>
              </div>
              <div>
                <p className="text-gray-600">Categories</p>
                <p className="font-semibold">{dataKeys.length}</p>
              </div>
              <div>
                <p className="text-gray-600">First Year</p>
                <p className="font-semibold">{chartData[0]?.year}</p>
              </div>
              <div>
                <p className="text-gray-600">Last Year</p>
                <p className="font-semibold">{chartData[chartData.length - 1]?.year}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// ADDITIONAL COMPONENTS - Metrics Analysis
// ============================================================================

/**
 * Metrics Additional Analysis - CUF & Curtailment
 */
const MetricsAdditionalAnalysis = ({ projectPath, scenarioName, networkFile, period }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  const { data: cufData, loading: cufLoading } = usePyPSAData(
    '/pypsa/capacity-factors',
    { projectPath, scenarioName, networkFile, period },
    expandedSection === 'cuf'
  );

  const { data: curtailmentData, loading: curtailmentLoading } = usePyPSAData(
    '/pypsa/curtailment',
    { projectPath, scenarioName, networkFile, period },
    expandedSection === 'curtailment'
  );

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const cufTransformed = useMemo(() => {
    if (!cufData) return null;
    return transformPyPSAData(cufData, 'capacity_factor');
  }, [cufData]);

  const curtailmentTransformed = useMemo(() => {
    if (!curtailmentData) return null;
    return transformPyPSAData(curtailmentData, 'curtailment');
  }, [curtailmentData]);

  const cufConfig = getChartConfig('capacity_factor');
  const curtailmentConfig = getChartConfig('curtailment');

  return (
    <div className="mt-4 space-y-4">
      {/* CUF Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <button
          onClick={() => toggleSection('cuf')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <h4 className="text-md font-semibold text-gray-900">
            Capacity Utilization Factors (CUF)
          </h4>
          <span className={`transform transition-transform ${expandedSection === 'cuf' ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>

        {expandedSection === 'cuf' && (
          <div className="px-6 pb-6 pt-4">
            {cufLoading ? (
              <LoadingSpinner message="Loading CUF data..." />
            ) : cufTransformed && cufTransformed.length > 0 ? (
              <UnifiedChart
                data={cufTransformed}
                type={cufConfig.type}
                config={cufConfig}
                height={400}
              />
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                No CUF data available
              </div>
            )}
          </div>
        )}
      </div>

      {/* Curtailment Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <button
          onClick={() => toggleSection('curtailment')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <h4 className="text-md font-semibold text-gray-900">
            Renewable Curtailment
          </h4>
          <span className={`transform transition-transform ${expandedSection === 'curtailment' ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>

        {expandedSection === 'curtailment' && (
          <div className="px-6 pb-6 pt-4">
            {curtailmentLoading ? (
              <LoadingSpinner message="Loading curtailment data..." />
            ) : curtailmentTransformed && curtailmentTransformed.length > 0 ? (
              <UnifiedChart
                data={curtailmentTransformed}
                type={curtailmentConfig.type}
                config={curtailmentConfig}
                height={400}
              />
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                No curtailment data available
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// ADDITIONAL COMPONENTS - Storage Analysis
// ============================================================================

/**
 * Storage Additional Analysis - State of Charge Time-Series
 */
const StorageAdditionalAnalysis = ({ projectPath, scenarioName, networkFile, period }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  const { data: socData, loading: socLoading } = usePyPSAData(
    '/pypsa/storage-operation',
    { projectPath, scenarioName, networkFile, period },
    expandedSection === 'soc'
  );

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const socTransformed = useMemo(() => {
    if (!socData) return null;
    return transformPyPSAData(socData, 'storage_soc');
  }, [socData]);

  const socConfig = useMemo(() => {
    const config = getChartConfig('storage_soc');
    if (socTransformed && socTransformed.length > 0) {
      config.dataKeys = Object.keys(socTransformed[0]).filter(key => key !== 'timestamp');
    }
    return config;
  }, [socTransformed]);

  return (
    <div className="mt-4 space-y-4">
      {/* SOC Time-Series Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <button
          onClick={() => toggleSection('soc')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <h4 className="text-md font-semibold text-gray-900">
            Storage State of Charge (Time-Series)
          </h4>
          <span className={`transform transition-transform ${expandedSection === 'soc' ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>

        {expandedSection === 'soc' && (
          <div className="px-6 pb-6 pt-4">
            {socLoading ? (
              <LoadingSpinner message="Loading SOC data..." />
            ) : socTransformed && socTransformed.length > 0 ? (
              <UnifiedChart
                data={socTransformed}
                type={socConfig.type}
                config={socConfig}
                height={400}
              />
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm">
                No SOC data available
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// ADDITIONAL COMPONENTS - Dispatch Analysis
// ============================================================================

/**
 * Dispatch Additional Analysis - Daily Profile & Load Duration Curve
 */
const DispatchAdditionalAnalysis = ({ projectPath, scenarioName, networkFile, period }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  const { data: dailyProfileData, loading: dailyLoading } = usePyPSAData(
    '/pypsa/daily-profiles',
    { projectPath, scenarioName, networkFile, period },
    expandedSection === 'additional'
  );

  const { data: durationData, loading: durationLoading } = usePyPSAData(
    '/pypsa/duration-curves',
    { projectPath, scenarioName, networkFile, period },
    expandedSection === 'additional'
  );

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const dailyProfileTransformed = useMemo(() => {
    if (!dailyProfileData) return null;
    return transformPyPSAData(dailyProfileData, 'daily_profile');
  }, [dailyProfileData]);

  const durationCurveTransformed = useMemo(() => {
    if (!durationData) return null;
    const transformed = transformPyPSAData(durationData, 'duration_curve');
    return transformed.load || []; // Get load duration curve
  }, [durationData]);

  const dailyProfileConfig = useMemo(() => {
    const config = getChartConfig('daily_profile');
    if (dailyProfileTransformed && dailyProfileTransformed.length > 0) {
      config.dataKeys = Object.keys(dailyProfileTransformed[0]).filter(key => key !== 'hour');
    }
    return config;
  }, [dailyProfileTransformed]);

  const durationCurveConfig = getChartConfig('duration_curve');

  return (
    <div className="mt-4 space-y-4">
      {/* Daily Profile & Load Duration Curve Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <button
          onClick={() => toggleSection('additional')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <h4 className="text-md font-semibold text-gray-900">
            Daily Profiles & Load Duration Curve
          </h4>
          <span className={`transform transition-transform ${expandedSection === 'additional' ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>

        {expandedSection === 'additional' && (
          <div className="px-6 pb-6 grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            {/* Daily Profile */}
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-3">Average Daily Profile</h5>
              {dailyLoading ? (
                <LoadingSpinner message="Loading daily profile..." />
              ) : dailyProfileTransformed && dailyProfileTransformed.length > 0 ? (
                <UnifiedChart
                  data={dailyProfileTransformed}
                  type={dailyProfileConfig.type}
                  config={dailyProfileConfig}
                  height={350}
                />
              ) : (
                <div className="text-center py-8 text-gray-500 text-sm">
                  No daily profile data available
                </div>
              )}
            </div>

            {/* Load Duration Curve */}
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-3">Load Duration Curve</h5>
              {durationLoading ? (
                <LoadingSpinner message="Loading duration curve..." />
              ) : durationCurveTransformed && durationCurveTransformed.length > 0 ? (
                <UnifiedChart
                  data={durationCurveTransformed}
                  type={durationCurveConfig.type}
                  config={durationCurveConfig}
                  height={350}
                />
              ) : (
                <div className="text-center py-8 text-gray-500 text-sm">
                  No duration curve data available
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Summary Statistics Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <button
          onClick={() => toggleSection('summary')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <h4 className="text-md font-semibold text-gray-900">
            Dispatch Summary Statistics
          </h4>
          <span className={`transform transition-transform ${expandedSection === 'summary' ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>

        {expandedSection === 'summary' && (
          <div className="px-6 pb-6 pt-4">
            <div className="text-center py-8 text-gray-500 text-sm">
              Summary statistics coming soon
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const UnifiedNetworkView = ({
  projectPath,
  selectedScenario,
  selectedNetwork
}) => {
  // ====== STATE MANAGEMENT ======
  const [activeTab, setActiveTab] = useState('dispatch');
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [selectedYear, setSelectedYear] = useState(null);
  const [viewMode, setViewMode] = useState('single'); // 'single' or 'comparison'

  // Comparison state
  const [selectedPeriods, setSelectedPeriods] = useState([]);
  const [selectedYears, setSelectedYears] = useState([]);
  const [activeComparison, setActiveComparison] = useState('capacity');

  // Date range state (for Dispatch & Load filtering)
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Resolution state (for Dispatch plots)
  const [resolution, setResolution] = useState('1H');

  // View mode state (chart or table)
  const [dataViewMode, setDataViewMode] = useState('chart'); // 'chart' or 'table'

  // Chart type override (for views that support multiple chart types)
  const [chartTypeOverride, setChartTypeOverride] = useState(null);

  // Track if dates have been auto-populated (to prevent infinite loops)
  const datesAutoPopulatedRef = useRef(false);

  // ====== NETWORK TYPE DETECTION ======
  const {
    detection,
    loading: detectionLoading,
    error: detectionError
  } = useNetworkDetection(projectPath, selectedScenario, selectedNetwork);

  // ====== NETWORK CAPABILITIES ======
  const {
    loading: capabilitiesLoading,
    error: capabilitiesError
  } = usePyPSAAvailability(projectPath, selectedScenario, selectedNetwork);

  // Auto-select first period/year when detection completes
  useEffect(() => {
    if (detection) {
      if (detection.workflow_type === 'multi-period' && detection.periods?.length > 0) {
        setSelectedPeriod(detection.periods[0]);
      }
      if (detection.workflow_type === 'multi-file' && detection.years?.length > 0) {
        setSelectedYear(detection.years[0]);
      }
    }
  }, [detection]);

  // Fetch network metadata to get date range from snapshots
  // ONLY fetch when on dispatch tab to avoid unnecessary API calls
  const shouldFetchMetadata = activeTab === 'dispatch' && !!projectPath && !!selectedScenario && !!selectedNetwork && !datesAutoPopulatedRef.current;

  const { data: metadataData } = usePyPSAData(
    '/pypsa/network-metadata',
    { projectPath, scenarioName: selectedScenario, networkFile: selectedNetwork },
    shouldFetchMetadata
  );

  // Auto-populate date range from metadata when available (ONCE only)
  useEffect(() => {
    if (metadataData && metadataData.start_date && metadataData.end_date && !datesAutoPopulatedRef.current) {
      // Set default to show full range
      setStartDate(metadataData.start_date.split('T')[0]);
      setEndDate(metadataData.end_date.split('T')[0]);

      // Mark as populated to prevent re-fetching
      datesAutoPopulatedRef.current = true;

      console.log('[UnifiedNetworkView] Auto-populated dates:', {
        start: metadataData.start_date.split('T')[0],
        end: metadataData.end_date.split('T')[0]
      });
    }
  }, [metadataData]);

  // Reset dates populated flag when network changes
  useEffect(() => {
    datesAutoPopulatedRef.current = false;
  }, [selectedNetwork, selectedScenario]);

  // ====== ENDPOINT SELECTION ======
  const endpoint = useMemo(() => {
    if (!detection) return null;

    const tab = SINGLE_PERIOD_TABS.find(t => t.id === activeTab);
    if (!tab) return null;

    // Comparison mode
    if (viewMode === 'comparison') {
      if (detection.workflow_type === 'multi-period' && selectedPeriods.length >= 2) {
        return '/pypsa/analysis/cross-period-comparison';
      }
      if (detection.workflow_type === 'multi-file' && selectedYears.length >= 2) {
        return '/pypsa/analysis/year-to-year-comparison';
      }
      return null;
    }

    // Single analysis mode
    if (detection.workflow_type === 'multi-period' && selectedPeriod !== null) {
      return `/pypsa/analysis/period/${selectedPeriod}`;
    }
    if (detection.workflow_type === 'multi-file' && selectedYear !== null) {
      return `/pypsa/analysis/year/${selectedYear}`;
    }

    // Single-period: use regular endpoints
    return tab.endpoint;
  }, [detection, activeTab, viewMode, selectedPeriod, selectedYear, selectedPeriods, selectedYears]);

  // ====== DATA FETCHING ======
  const dataParams = useMemo(() => {
    const params = {
      projectPath,
      scenarioName: selectedScenario,
      networkFile: selectedNetwork
    };

    if (viewMode === 'comparison') {
      if (detection?.workflow_type === 'multi-period') {
        params.periods = selectedPeriods;
        params.comparisonType = activeComparison;
      } else if (detection?.workflow_type === 'multi-file') {
        params.years = selectedYears;
        params.comparisonType = activeComparison;
      }
    } else {
      params.analysisType = activeTab;

      if (detection?.workflow_type === 'multi-period' && selectedPeriod !== null) {
        params.period = selectedPeriod;
      }
      if (detection?.workflow_type === 'multi-file' && selectedYear !== null) {
        params.year = selectedYear;
      }

      // Add date range and resolution for dispatch tab
      if (activeTab === 'dispatch') {
        params.resolution = resolution;
        if (startDate) params.startDate = startDate;
        if (endDate) params.endDate = endDate;
      }
    }

    return params;
  }, [projectPath, selectedScenario, selectedNetwork, viewMode, activeTab, selectedPeriod, selectedYear, selectedPeriods, selectedYears, activeComparison, detection, startDate, endDate, resolution]);

  const {
    data,
    loading: dataLoading,
    error: dataError,
    refetch
  } = usePyPSAData(
    endpoint,
    dataParams,
    !!endpoint && !!projectPath && !!selectedScenario && !!selectedNetwork
  );

  // ====== DATA TRANSFORMATION ======
  const transformedData = useMemo(() => {
    if (!data) return null;
    return transformPyPSAData(data, activeTab);
  }, [data, activeTab]);

  const chartConfig = useMemo(() => {
    const config = getChartConfig(activeTab);

    // For dispatch charts, dynamically populate dataKeys from the data
    if (activeTab === 'dispatch' && transformedData && transformedData.length > 0) {
      const dataKeys = Object.keys(transformedData[0]).filter(key => key !== 'timestamp' && key !== 'Load');
      config.dataKeys = dataKeys;
    }

    // Apply chart type override if set
    if (chartTypeOverride && config.supportsPie) {
      config.type = chartTypeOverride;
    }

    return config;
  }, [activeTab, transformedData, chartTypeOverride]);

  // ====== HANDLERS ======
  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
    setViewMode('single');
    setChartTypeOverride(null); // Reset chart type override when switching tabs
  }, []);

  const handleComparisonChange = useCallback((comparisonId) => {
    setActiveComparison(comparisonId);
    setViewMode('comparison');
  }, []);

  const handleClearDateRange = useCallback(() => {
    setStartDate('');
    setEndDate('');
  }, []);

  // ====== RENDER ======

  // Loading
  if (detectionLoading || capabilitiesLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner message="Detecting network type..." />
      </div>
    );
  }

  // Error
  if (detectionError || capabilitiesError) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <ErrorMessage error={detectionError || capabilitiesError} />
      </div>
    );
  }

  // No detection result
  if (!detection) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <ErrorMessage error="Unable to detect network type" />
      </div>
    );
  }

  const { workflow_type, periods, years } = detection;

  return (
    <div className="h-full flex">
      {/* Sidebar with Tabs */}
      <TabSidebar
        tabs={SINGLE_PERIOD_TABS}
        activeTab={activeTab}
        onTabChange={handleTabChange}
        title="Analysis"
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-gray-50">
        <div className="p-6 overflow-y-auto">
          {/* Network Type Header */}
          <NetworkTypeHeader detection={detection} />

          {/* Resolution Selector (for Dispatch & Load tab only) */}
          <ResolutionSelector
            resolution={resolution}
            onChange={setResolution}
            options={RESOLUTION_OPTIONS}
            show={activeTab === 'dispatch' && viewMode === 'single'}
          />

          {/* Date Range Selector (for Dispatch & Load tab only) */}
          <DateRangeSelector
            startDate={startDate}
            endDate={endDate}
            onStartChange={setStartDate}
            onEndChange={setEndDate}
            onClear={handleClearDateRange}
            show={activeTab === 'dispatch' && viewMode === 'single'}
          />

          {/* Multi-Period: Period Selector + Comparison */}
          {workflow_type === 'multi-period' && (
            <>
              <PeriodSelector
                periods={periods}
                selectedPeriod={selectedPeriod}
                onChange={setSelectedPeriod}
              />

              <ComparisonSection
                type="period"
                items={periods || []}
                selectedItems={selectedPeriods}
                onItemsChange={setSelectedPeriods}
                comparisonTypes={COMPARISON_TYPES}
                activeComparison={activeComparison}
                onComparisonChange={handleComparisonChange}
              />
            </>
          )}

          {/* Multi-File: Year Selector + Comparison */}
          {workflow_type === 'multi-file' && (
            <>
              <YearSelector
                years={years}
                selectedYear={selectedYear}
                onChange={setSelectedYear}
              />

              <ComparisonSection
                type="year"
                items={years || []}
                selectedItems={selectedYears}
                onItemsChange={setSelectedYears}
                comparisonTypes={COMPARISON_TYPES}
                activeComparison={activeComparison}
                onComparisonChange={handleComparisonChange}
              />
            </>
          )}

          {/* Data Visualization */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {viewMode === 'comparison'
                  ? COMPARISON_TYPES.find(c => c.id === activeComparison)?.label
                  : SINGLE_PERIOD_TABS.find(t => t.id === activeTab)?.label
                }
              </h3>

              <div className="flex items-center gap-2">
                {/* Chart Type Toggle (for views that support it) */}
                {dataViewMode === 'chart' && chartConfig.supportsPie && (
                  <div className="flex bg-blue-50 border border-blue-200 rounded-lg p-1 mr-2">
                    <button
                      onClick={() => {
                        const currentType = chartConfig.type;
                        const newType = currentType === 'pie' || currentType === 'donut' ? 'bar' : 'pie';
                        setChartTypeOverride(newType);
                      }}
                      className="px-3 py-1.5 text-xs font-medium text-blue-700 hover:text-blue-900 rounded transition-colors"
                      title={`Switch to ${chartConfig.type === 'pie' || chartConfig.type === 'donut' ? 'Bar' : 'Pie'} Chart`}
                    >
                      {chartConfig.type === 'pie' || chartConfig.type === 'donut' ? '📊 Bar' : '🥧 Pie'}
                    </button>
                  </div>
                )}

                {/* View Mode Toggle */}
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setDataViewMode('chart')}
                    className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                      dataViewMode === 'chart'
                        ? 'bg-white text-gray-900 shadow'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="Chart View"
                  >
                    <BarChart3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setDataViewMode('table')}
                    className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                      dataViewMode === 'table'
                        ? 'bg-white text-gray-900 shadow'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="Table View"
                  >
                    <TableIcon className="w-4 h-4" />
                  </button>
                </div>

                {/* Refresh Button */}
                <button
                  onClick={refetch}
                  className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Refresh data"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>

            {dataLoading && <LoadingSpinner />}

            {dataError && <ErrorMessage error={dataError} onRetry={refetch} />}

            {!dataLoading && !dataError && transformedData && transformedData.length > 0 && (
              <>
                {dataViewMode === 'chart' ? (
                  <UnifiedChart
                    data={transformedData}
                    type={chartConfig.type}
                    config={chartConfig}
                    height={500}
                  />
                ) : (
                  <div className="overflow-auto max-h-[500px]">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          {Object.keys(transformedData[0] || {}).map(key => (
                            <th
                              key={key}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {transformedData.map((row, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            {Object.values(row).map((value, colIdx) => (
                              <td key={colIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {typeof value === 'number' ? value.toFixed(2) : value}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}

            {!dataLoading && !dataError && (!transformedData || transformedData.length === 0) && (
              <div className="text-center py-8 text-gray-500">
                No data available for this analysis
              </div>
            )}
          </div>

          {/* Additional Dispatch Analysis (Daily Profile & Load Duration) */}
          {activeTab === 'dispatch' && viewMode === 'single' && !dataLoading && !dataError && transformedData && transformedData.length > 0 && (
            <DispatchAdditionalAnalysis
              projectPath={projectPath}
              scenarioName={selectedScenario}
              networkFile={selectedNetwork}
              period={selectedPeriod}
            />
          )}

          {/* Additional Metrics Analysis (CUF & Curtailment) */}
          {activeTab === 'metrics' && viewMode === 'single' && !dataLoading && !dataError && (
            <MetricsAdditionalAnalysis
              projectPath={projectPath}
              scenarioName={selectedScenario}
              networkFile={selectedNetwork}
              period={selectedPeriod}
            />
          )}

          {/* Additional Storage Analysis (SOC Time-Series) */}
          {activeTab === 'storage' && viewMode === 'single' && !dataLoading && !dataError && (
            <StorageAdditionalAnalysis
              projectPath={projectPath}
              scenarioName={selectedScenario}
              networkFile={selectedNetwork}
              period={selectedPeriod}
            />
          )}

          {/* Multi-Year Stacked Visualizations (for multi-file networks) */}
          {detection?.workflow_type === 'multi-file' && (
            <MultiYearStackedView
              projectPath={projectPath}
              scenarioName={selectedScenario}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default UnifiedNetworkView;
