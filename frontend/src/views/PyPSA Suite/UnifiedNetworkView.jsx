/**
 * PyPSA Unified Network Visualization - Professional Desktop Version
 * ==================================================================
 *
 * Modern, professional implementation with:
 * - Desktop-optimized design (minimum 1280px width)
 * - Support for single and multi-period/multi-year NC files
 * - Specialized visualization panels for each analysis type
 * - Enhanced data handling with comprehensive transformers
 * - Professional color scheme and typography
 * - Robust error handling and loading states
 *
 * @version 3.0
 * @date 2025-01-05
 */

import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import {
  Activity, BarChart3, TrendingUp, Battery,
  CloudOff, DollarSign, Network, AlertCircle,
  CheckCircle, Loader2, Download, Info, Zap
} from 'lucide-react';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';
import usePyPSAData from '../../hooks/usePyPSAData';
import useNetworkDetection from '../../hooks/useNetworkDetection';
import {
  transformCapacityData,
  transformDispatchData,
  transformRenewableShareData,
  transformStorageData,
  transformEmissionsData,
  transformSystemCostsData,
  transformLinesData,
  PYPSA_COLORS
} from '../../utils/pypsaDataTransformer';

// =============================================================================
// CONSTANTS & CONFIGURATION
// =============================================================================

const TABS = [
  {
    id: 'dispatch',
    label: 'Dispatch & Load',
    icon: Activity,
    endpoint: '/pypsa/dispatch',
    description: 'Power generation and load dispatch over time'
  },
  {
    id: 'capacity',
    label: 'Capacity',
    icon: BarChart3,
    endpoint: '/pypsa/total-capacities',
    description: 'Installed capacity by technology and year'
  },
  {
    id: 'metrics',
    label: 'Metrics',
    icon: TrendingUp,
    endpoint: '/pypsa/renewable-share',
    description: 'System performance metrics and renewable share'
  },
  {
    id: 'storage',
    label: 'Storage',
    icon: Battery,
    endpoint: '/pypsa/storage-units',
    description: 'Energy storage systems and stores'
  },
  {
    id: 'emissions',
    label: 'Emissions',
    icon: CloudOff,
    endpoint: '/pypsa/emissions',
    description: 'CO2 emissions tracking and intensity'
  },
  {
    id: 'costs',
    label: 'Costs',
    icon: DollarSign,
    endpoint: '/pypsa/system-costs',
    description: 'System cost breakdown by carrier'
  },
  {
    id: 'network',
    label: 'Network',
    icon: Network,
    endpoint: '/pypsa/lines',
    description: 'Transmission network lines'
  }
];

const RESOLUTIONS = [
  { value: '1H', label: '1 Hour' },
  { value: '3H', label: '3 Hours' },
  { value: '6H', label: '6 Hours' },
  { value: '12H', label: '12 Hours' },
  { value: '1D', label: '1 Day' },
  { value: '1W', label: '1 Week' }
];

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  if (value >= 1e9) return (value / 1e9).toFixed(decimals) + ' B';
  if (value >= 1e6) return (value / 1e6).toFixed(decimals) + ' M';
  if (value >= 1e3) return (value / 1e3).toFixed(decimals) + ' K';
  return value.toFixed(decimals);
};

const formatPercentage = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '-';
  return value.toFixed(2) + '%';
};

// =============================================================================
// COMMON COMPONENTS
// =============================================================================

const LoadingState = ({ message = 'Loading data...' }) => (
  <div className="flex flex-col items-center justify-center py-20">
    <Loader2 className="w-16 h-16 text-blue-600 animate-spin mb-4" />
    <p className="text-gray-600 text-lg font-medium">{message}</p>
  </div>
);

const ErrorState = ({ error, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-20">
    <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8 max-w-2xl">
      <div className="flex items-start gap-4">
        <AlertCircle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="text-red-900 font-bold text-xl mb-3">Error Loading Data</h3>
          <p className="text-red-700 mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium shadow-md hover:shadow-lg"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
);

const EmptyState = ({ message = 'No data available for this analysis' }) => (
  <div className="flex flex-col items-center justify-center py-20">
    <div className="bg-gray-100 rounded-full p-8 mb-4">
      <BarChart3 className="w-16 h-16 text-gray-400" />
    </div>
    <p className="text-gray-600 text-lg">{message}</p>
  </div>
);

const InfoCard = ({ title, value, subtitle, icon: Icon, color = 'blue' }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    orange: 'bg-orange-50 border-orange-200 text-orange-900',
    purple: 'bg-purple-50 border-purple-200 text-purple-900',
    red: 'bg-red-50 border-red-200 text-red-900'
  };

  const iconColorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    orange: 'text-orange-600',
    purple: 'text-purple-600',
    red: 'text-red-600'
  };

  return (
    <div className={`${colorClasses[color]} border-2 rounded-xl p-6 shadow-sm`}>
      <div className="flex items-start justify-between mb-3">
        <h4 className="text-sm font-semibold uppercase tracking-wide opacity-80">{title}</h4>
        {Icon && <Icon className={`w-6 h-6 ${iconColorClasses[color]}`} />}
      </div>
      <p className="text-3xl font-bold mb-1">{value}</p>
      {subtitle && <p className="text-sm opacity-70">{subtitle}</p>}
    </div>
  );
};

// =============================================================================
// DISPATCH & LOAD PANEL
// =============================================================================

// const DispatchPanel = ({ data, loading, error }) => {
//   if (loading) return <LoadingState message="Loading dispatch data..." />;
//   if (error) return <ErrorState error={error} />;
//   if (!data || data.length === 0) return <EmptyState />;

//   // Extract data keys (carriers)
//   const dataKeys = Object.keys(data[0]).filter(key =>
//     key !== 'timestamp' && key !== 'Load'
//   );

//   return (
//     <div className="space-y-6">
//       <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
//         <h3 className="text-lg font-bold text-gray-900 mb-4">Generation Dispatch</h3>
//         <ResponsiveContainer width="100%" height={600}>
//           <AreaChart data={data} margin={{ top: 10, right: 30, left: 60, bottom: 60 }}>
//             <defs>
//               {dataKeys.map((key) => (
//                 <linearGradient key={key} id={`color${key}`} x1="0" y1="0" x2="0" y2="1">
//                   <stop offset="5%" stopColor={PYPSA_COLORS[key] || '#3b82f6'} stopOpacity={0.8} />
//                   <stop offset="95%" stopColor={PYPSA_COLORS[key] || '#3b82f6'} stopOpacity={0.3} />
//                 </linearGradient>
//               ))}
//             </defs>
//             <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
//             <XAxis
//               dataKey="timestamp"
//               stroke="#6b7280"
//               tick={{ fontSize: 12 }}
//               angle={-45}
//               textAnchor="end"
//               height={80}
//               tickFormatter={(value) => {
//                 const date = new Date(value);
//                 return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
//               }}
//             />
//             <YAxis
//   stroke="#6b7280"
//   label={{ value: 'Power (MW)', angle: -90, position: 'insideLeft' }}
//   domain={['auto', 'auto']} // ✅ allows both positive & negative dynamically
// />


//             <Tooltip
//               contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
//               labelFormatter={(value) => new Date(value).toLocaleString()}
//               formatter={(value) => formatNumber(value) + ' MW'}
//             />
//             <Legend wrapperStyle={{ paddingTop: '20px' }} />
//             {dataKeys.map((key) => (
//               <Area
//                 key={key}
//                 type="monotone"
//                 dataKey={key}
//                 stackId="1"
//                 stroke={PYPSA_COLORS[key] || '#3b82f6'}
//                 fill={`url(#color${key})`}
//                 strokeWidth={1.5}
//               />
//             ))}
//             {data[0]?.Load !== undefined && (
//               <Line
//                 type="monotone"
//                 dataKey="Load"
//                 stroke="#000000"
//                 strokeWidth={3}
//                 strokeDasharray="5 5"
//                 dot={false}
//                 name="Load"
//               />
//             )}
//           </AreaChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// };

const DispatchPanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading dispatch data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data || data.length === 0) return <EmptyState />;

  const dataKeys = Object.keys(data[0]).filter(k => k !== 'timestamp' && k !== 'Load');

  // Helper to coerce values to numbers safely
  const toNum = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };

  // Compute global min/max across all keys (including Load)
  let globalMin = Infinity;
  let globalMax = -Infinity;
  data.forEach(row => {
    // check load
    if (row.Load !== undefined) {
      const n = toNum(row.Load);
      if (n < globalMin) globalMin = n;
      if (n > globalMax) globalMax = n;
    }
    // check each area key
    dataKeys.forEach(k => {
      const n = toNum(row[k]);
      if (n < globalMin) globalMin = n;
      if (n > globalMax) globalMax = n;
    });
  });

  // Fallbacks if no finite values found
  if (!isFinite(globalMin)) globalMin = 0;
  if (!isFinite(globalMax)) globalMax = 0;

  // Add small padding so the chart isn't flush to the edges
  const padding = Math.max(10, Math.abs(globalMax - globalMin) * 0.05);
  const domainMin = Math.floor(globalMin - padding);
  const domainMax = Math.ceil(globalMax + padding);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Generation Dispatch</h3>
        <ResponsiveContainer width="100%" height={600}>
          <AreaChart
            data={data}
            margin={{ top: 10, right: 30, left: 60, bottom: 60 }}
            stackOffset="sign" // <-- handle negative & positive stacking correctly
          >
            <defs>
              {dataKeys.map((key) => (
                <linearGradient key={key} id={`color${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={PYPSA_COLORS[key] || '#3b82f6'} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={PYPSA_COLORS[key] || '#3b82f6'} stopOpacity={0.3} />
                </linearGradient>
              ))}
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="timestamp"
              stroke="#6b7280"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
              }}
            />
            <YAxis
              stroke="#6b7280"
              label={{ value: 'Power (MW)', angle: -90, position: 'insideLeft' }}
              domain={[domainMin, domainMax]}   // explicit domain computed from data
              allowDataOverflow={true}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              labelFormatter={(value) => new Date(value).toLocaleString()}
              formatter={(value) => formatNumber(value) + ' MW'}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />

            {dataKeys.map((key) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stackId="1"
                stroke={PYPSA_COLORS[key] || '#3b82f6'}
                fill={`url(#color${key})`}
                strokeWidth={1.5}
                isAnimationActive={false}
              />
            ))}

            {data[0]?.Load !== undefined && (
              <Line
                type="monotone"
                dataKey="Load"
                stroke="#000000"
                strokeWidth={3}
                strokeDasharray="5 5"
                dot={false}
                name="Load"
                isAnimationActive={false}
              />
            )}

            {/* Draw zero baseline so negative/positive split is clear */}
            <ReferenceLine y={0} stroke="#000000" strokeDasharray="3 3" ifOverflow="extendDomain" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// =============================================================================
// CAPACITY PANEL
// =============================================================================

const CapacityPanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading capacity data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data) return <EmptyState />;

  const { generators, storage_units, stores, totals, aggregates, isMultiPeriod } = data;

  if (isMultiPeriod && aggregates) {
    // Multi-period view with stacked bar charts by year
    const generatorData = aggregates.generators_by_carrier || [];
    const years = generatorData.length > 0 ? Object.keys(generatorData[0]).filter(k => !isNaN(parseInt(k))) : [];

    // Transform for stacked bar chart
    const chartData = years.map(year => {
      const dataPoint = { year };
      generatorData.forEach(item => {
        dataPoint[item.Carrier] = item[year] || 0;
      });
      return dataPoint;
    });

    const carriers = generatorData.map(item => item.Carrier);

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-3 gap-4">
          {years.map(year => (
            <InfoCard
              key={year}
              title={`Total Capacity ${year}`}
              value={formatNumber(totals?.generation_capacity_mw?.[year] || 0) + ' MW'}
              subtitle="Generation"
              icon={Zap}
              color="blue"
            />
          ))}
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Generator Capacities by Year</h3>
          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="year" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: 'Capacity (MW)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value) => formatNumber(value) + ' MW'}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              {carriers.map(carrier => (
                <Bar
                  key={carrier}
                  dataKey={carrier}
                  stackId="capacity"
                  fill={PYPSA_COLORS[carrier] || '#3b82f6'}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {aggregates.storage_energy_by_carrier && aggregates.storage_energy_by_carrier.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Storage Energy Capacity by Year</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={years.map(year => ({
                  year,
                  ...aggregates.storage_energy_by_carrier.reduce((acc, item) => {
                    acc[item.Carrier] = item[year] || 0;
                    return acc;
                  }, {})
                }))}
                margin={{ top: 20, right: 30, left: 60, bottom: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" stroke="#6b7280" />
                <YAxis stroke="#6b7280" label={{ value: 'Energy (MWh)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => formatNumber(value) + ' MWh'}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                {aggregates.storage_energy_by_carrier.map(item => (
                  <Bar
                    key={item.Carrier}
                    dataKey={item.Carrier}
                    stackId="storage"
                    fill={PYPSA_COLORS[item.Carrier] || '#9333ea'}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    );
  }

  // Single period view
  const generatorChartData = generators.map(gen => ({
    name: gen.carrier,
    value: gen.value
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <InfoCard
          title="Total Generation"
          value={formatNumber(totals?.generation_capacity_mw || 0) + ' MW'}
          subtitle="Installed capacity"
          icon={Zap}
          color="blue"
        />
        <InfoCard
          title="Storage Power"
          value={formatNumber(totals?.storage_power_capacity_mw || 0) + ' MW'}
          subtitle="Storage capacity"
          icon={Battery}
          color="purple"
        />
        <InfoCard
          title="Storage Energy"
          value={formatNumber(totals?.storage_energy_capacity_mwh || 0) + ' MWh'}
          subtitle="Energy storage"
          icon={Battery}
          color="green"
        />
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Generator Capacities</h3>
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={generatorChartData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="name"
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis stroke="#6b7280" label={{ value: 'Capacity (MW)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              formatter={(value) => formatNumber(value) + ' MW'}
            />
            <Bar dataKey="value">
              {generatorChartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={PYPSA_COLORS[entry.name] || '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// =============================================================================
// METRICS PANEL
// =============================================================================

const MetricsPanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading metrics data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data || !data.summary) return <EmptyState />;

  const { breakdown, summary, isMultiPeriod } = data;

  if (isMultiPeriod) {
    const years = Object.keys(summary.renewable_share_percent || {});

    // Prepare chart data for renewable share by year
    const renewableShareChart = years.map(year => ({
      year,
      renewable: summary.renewable_share_percent[year] || 0,
      non_renewable: 100 - (summary.renewable_share_percent[year] || 0)
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-3 gap-4">
          {years.map(year => (
            <InfoCard
              key={year}
              title={`Renewable Share ${year}`}
              value={formatPercentage(summary.renewable_share_percent[year])}
              subtitle={formatNumber(summary.renewable_energy_mwh[year]) + ' MWh'}
              icon={TrendingUp}
              color="green"
            />
          ))}
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Renewable Share by Year</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={renewableShareChart} margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="year" stroke="#6b7280" />
              <YAxis stroke="#6b7280" label={{ value: 'Share (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value) => formatPercentage(value)}
              />
              <Legend />
              <Bar dataKey="renewable" stackId="share" fill="#10b981" name="Renewable" />
              <Bar dataKey="non_renewable" stackId="share" fill="#ef4444" name="Non-Renewable" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {breakdown && breakdown.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Renewable Breakdown by Carrier</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                    {years.map(year => (
                      <th key={year} className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">{year} (MWh)</th>
                    ))}
                    {years.map(year => (
                      <th key={`share-${year}`} className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">{year} (%)</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {breakdown.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.Carrier}</td>
                      {years.map(year => (
                        <td key={year} className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                          {formatNumber(item.Renewable_Energy_MWh?.[year] || 0)}
                        </td>
                      ))}
                      {years.map(year => (
                        <td key={`share-${year}`} className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                          {formatPercentage(item['Share_%']?.[year] || 0)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Multi-period CUF Data */}
        {data.capacity_factors && data.capacity_factors.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Capacity Utilization Factors (CUF) by Year</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                    {years.map(year => (
                      <th key={year} className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">{year} (%)</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.capacity_factors.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.Carrier}</td>
                      {years.map(year => (
                        <td key={year} className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                          {formatPercentage(item[year] || 0)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Multi-period Curtailment Data */}
        {data.curtailment && data.curtailment.length > 0 && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Renewable Curtailment by Year</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                    {years.map(year => (
                      <th key={year} className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">{year} (MWh)</th>
                    ))}
                    {years.map(year => (
                      <th key={`curtail-${year}`} className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">{year} (%)</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.curtailment.map((item, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.Carrier}</td>
                      {years.map(year => (
                        <td key={year} className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                          {formatNumber(item.Curtailment_MWh?.[year] || 0)}
                        </td>
                      ))}
                      {years.map(year => (
                        <td key={`curtail-${year}`} className="px-6 py-4 whitespace-nowrap text-right text-orange-700 font-semibold">
                          {formatPercentage(item['Curtailment_%']?.[year] || 0)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Single period view
  const renewableData = [
    { name: 'Renewable', value: summary.renewable_share_percent, color: '#10b981' },
    { name: 'Non-Renewable', value: 100 - summary.renewable_share_percent, color: '#ef4444' }
  ];

  const breakdownChart = breakdown.map(item => ({
    name: item.carrier,
    value: item.renewable_energy_mwh,
    share: item.share_percent
  }));

  const { capacity_factors = [], curtailment = [] } = data;

  // Aggregate curtailment by carrier
  const curtailmentByCarrier = curtailment.reduce((acc, item) => {
    const carrier = item.carrier;
    if (!acc[carrier]) {
      acc[carrier] = {
        carrier,
        total_curtailment_mwh: 0,
        total_potential_mwh: 0,
        generators: []
      };
    }
    acc[carrier].total_curtailment_mwh += item.curtailment_mwh || 0;
    acc[carrier].total_potential_mwh += item.potential_generation || 0;
    acc[carrier].generators.push(item);
    return acc;
  }, {});

  const curtailmentData = Object.values(curtailmentByCarrier).map(item => ({
    ...item,
    curtailment_percent: item.total_potential_mwh > 0
      ? (item.total_curtailment_mwh / item.total_potential_mwh) * 100
      : 0
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <InfoCard
          title="Renewable Share"
          value={formatPercentage(summary.renewable_share_percent)}
          subtitle="Of total energy"
          icon={TrendingUp}
          color="green"
        />
        <InfoCard
          title="Renewable Energy"
          value={formatNumber(summary.renewable_energy_mwh) + ' MWh'}
          subtitle="Total renewable generation"
          icon={Zap}
          color="blue"
        />
        <InfoCard
          title="Total Energy"
          value={formatNumber(summary.total_energy_mwh) + ' MWh'}
          subtitle="System total"
          icon={Activity}
          color="purple"
        />
        <InfoCard
          title="Total Curtailment"
          value={formatNumber(summary.total_curtailed_mwh || 0) + ' MWh'}
          subtitle={formatPercentage(summary.curtailment_rate_percent || 0) + ' rate'}
          icon={AlertCircle}
          color="orange"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Renewable vs Non-Renewable</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={renewableData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${formatPercentage(entry.value)}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {renewableData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatPercentage(value)} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Renewable Breakdown by Carrier</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={breakdownChart}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {breakdownChart.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PYPSA_COLORS[entry.name] || '#3b82f6'} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatNumber(value) + ' MWh'} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Capacity Utilization Factors (CUF) */}
      {capacity_factors.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Capacity Utilization Factors (CUF)</h3>
          <div className="overflow-x-auto mb-6">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Capacity Factor</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Utilization (%)</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {capacity_factors.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.carrier}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.capacity_factor, 4)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${Math.min(100, item.utilization_percent)}%` }}
                          ></div>
                        </div>
                        <span className="font-semibold">{formatPercentage(item.utilization_percent)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={capacity_factors} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="carrier"
                stroke="#6b7280"
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis stroke="#6b7280" label={{ value: 'Utilization (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value) => formatPercentage(value)}
              />
              <Bar dataKey="utilization_percent" fill="#3b82f6" name="Utilization (%)">
                {capacity_factors.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PYPSA_COLORS[entry.carrier] || '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Curtailment Analysis */}
      {curtailmentData.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Renewable Curtailment Analysis</h3>
          <div className="overflow-x-auto mb-6">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Curtailed (MWh)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Potential (MWh)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Curtailment (%)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase"># Generators</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {curtailmentData.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.carrier}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.total_curtailment_mwh)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.total_potential_mwh)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-orange-700 font-semibold">{formatPercentage(item.curtailment_percent)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{item.generators.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={curtailmentData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="carrier"
                stroke="#6b7280"
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis stroke="#6b7280" label={{ value: 'Curtailment (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                formatter={(value) => formatPercentage(value)}
              />
              <Bar dataKey="curtailment_percent" fill="#f97316" name="Curtailment (%)">
                {curtailmentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PYPSA_COLORS[entry.carrier] || '#f97316'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// STORAGE PANEL
// =============================================================================

const StoragePanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading storage data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data) return <EmptyState />;

  const { storage_units, stores } = data;

  const storageChartData = storage_units.map(unit => ({
    name: unit.carrier,
    power: unit.power_capacity_mw,
    energy: unit.energy_capacity_mwh
  }));

  const storesChartData = stores.map(store => ({
    name: store.carrier,
    energy: store.energy_capacity_mwh,
    max_hours: store.max_hours
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <InfoCard
          title="Storage Units"
          value={storage_units.length.toString()}
          subtitle="Total count"
          icon={Battery}
          color="purple"
        />
        <InfoCard
          title="Stores"
          value={stores.length.toString()}
          subtitle="Total count"
          icon={Battery}
          color="blue"
        />
      </div>

      {storage_units.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Storage Units Capacity</h3>
          <div className="overflow-x-auto mb-6">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Power (MW)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Energy (MWh)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Max Hours</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {storage_units.map((unit, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{unit.carrier}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(unit.power_capacity_mw)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(unit.energy_capacity_mwh)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                      {unit.power_capacity_mw > 0 ? formatNumber(unit.energy_capacity_mwh / unit.power_capacity_mw) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {storageChartData.length > 0 && (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={storageChartData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="name"
                  stroke="#6b7280"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis stroke="#6b7280" label={{ value: 'Capacity', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => formatNumber(value)}
                />
                <Legend />
                <Bar dataKey="power" fill="#9333ea" name="Power (MW)" />
                <Bar dataKey="energy" fill="#3b82f6" name="Energy (MWh)" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {stores.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Stores Capacity</h3>
          <div className="overflow-x-auto mb-6">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Energy (MWh)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Max Dispatch (MW)</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Max Hours</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stores.map((store, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{store.carrier}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(store.energy_capacity_mwh)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(store.max_dispatch_mw)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">
                      {store.max_dispatch_mw > 0 ? formatNumber(store.energy_capacity_mwh / store.max_dispatch_mw) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {storesChartData.length > 0 && (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={storesChartData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="name"
                  stroke="#6b7280"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis stroke="#6b7280" label={{ value: 'Energy (MWh)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                  formatter={(value) => formatNumber(value)}
                />
                <Bar dataKey="energy" fill="#10b981" name="Energy Capacity (MWh)">
                  {storesChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PYPSA_COLORS[entry.name] || '#10b981'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      )}
    </div>
  );
};

// =============================================================================
// EMISSIONS PANEL
// =============================================================================

const EmissionsPanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading emissions data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data || !data.summary) return <EmptyState />;

  const { emissions, summary } = data;

  const chartData = emissions.map(item => ({
    name: item.carrier,
    emissions: item.co2_emissions_tco2,
    energy: item.energy_mwh,
    factor: item.emission_factor
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <InfoCard
          title="Total Emissions"
          value={formatNumber(summary.total_emissions_tco2) + ' tCO₂'}
          subtitle="System total"
          icon={CloudOff}
          color="red"
        />
        <InfoCard
          title="Emission Intensity"
          value={formatNumber(summary.emission_intensity_tco2_per_mwh, 4) + ' tCO₂/MWh'}
          subtitle="Average intensity"
          icon={TrendingUp}
          color="orange"
        />
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Emissions by Carrier</h3>
        <div className="overflow-x-auto mb-6">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">CO₂ Emissions (tCO₂)</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Energy (MWh)</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Factor (tCO₂/MWh)</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {emissions.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.carrier}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.co2_emissions_tco2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.energy_mwh)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.emission_factor, 4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="name"
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis stroke="#6b7280" label={{ value: 'CO₂ Emissions (tCO₂)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              formatter={(value) => formatNumber(value)}
            />
            <Bar dataKey="emissions" fill="#ef4444" name="CO₂ Emissions (tCO₂)">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={PYPSA_COLORS[entry.name] || '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// =============================================================================
// COSTS PANEL
// =============================================================================

const CostsPanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading costs data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data || !data.costs) return <EmptyState />;

  const { costs, totals } = data;

  const chartData = costs.map(item => ({
    name: item.carrier,
    capital: item.capital_cost,
    marginal: item.marginal_cost,
    total: item.total_cost
  }));

  return (
    <div className="space-y-6">
      {totals && (
        <div className="grid grid-cols-3 gap-4">
          <InfoCard
            title="Total CAPEX"
            value={formatNumber(totals.total_capex)}
            subtitle="Capital expenditure"
            icon={DollarSign}
            color="blue"
          />
          <InfoCard
            title="Total OPEX"
            value={formatNumber(totals.total_opex)}
            subtitle="Operating expenditure"
            icon={DollarSign}
            color="green"
          />
          <InfoCard
            title="Total System Cost"
            value={formatNumber(totals.total_system_cost)}
            subtitle="CAPEX + OPEX"
            icon={DollarSign}
            color="purple"
          />
        </div>
      )}

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Costs by Carrier</h3>
        <div className="overflow-x-auto mb-6">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Carrier</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Capital Cost</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Marginal Cost</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Total Cost</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {costs.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{item.carrier}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.capital_cost)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(item.marginal_cost)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700 font-semibold">{formatNumber(item.total_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ResponsiveContainer width="100%" height={500}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 60, bottom: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="name"
              stroke="#6b7280"
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis stroke="#6b7280" label={{ value: 'Cost', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              formatter={(value) => formatNumber(value)}
            />
            <Legend />
            <Bar dataKey="capital" fill="#3b82f6" name="Capital Cost" />
            <Bar dataKey="marginal" fill="#10b981" name="Marginal Cost" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// =============================================================================
// NETWORK PANEL
// =============================================================================

const NetworkPanel = ({ data, loading, error }) => {
  if (loading) return <LoadingState message="Loading network data..." />;
  if (error) return <ErrorState error={error} />;
  if (!data || data.length === 0) return <EmptyState />;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Transmission Lines</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Line</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">From</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">To</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Capacity (MW)</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Utilization (%)</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((line, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{line.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-700">{line.from}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-700">{line.to}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatNumber(line.capacity)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-700">{formatPercentage(line.utilization)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

const UnifiedNetworkView = ({ projectPath, selectedScenario, selectedNetwork }) => {
  // State management
  const [activeTab, setActiveTab] = useState('dispatch');
  const [resolution, setResolution] = useState('1H');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const metadataFetchedRef = useRef(false);

  // Network detection
  const { detection, loading: detectionLoading, error: detectionError } = useNetworkDetection(
    projectPath,
    selectedScenario,
    selectedNetwork
  );

  // Get active tab config
  const activeTabConfig = useMemo(() =>
    TABS.find(t => t.id === activeTab),
    [activeTab]
  );

  // Build data parameters
  const dataParams = useMemo(() => {
    const params = {
      projectPath,
      scenarioName: selectedScenario,
      networkFile: selectedNetwork
    };

    if (activeTab === 'dispatch') {
      params.resolution = resolution;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
    }

    return params;
  }, [projectPath, selectedScenario, selectedNetwork, activeTab, resolution, startDate, endDate]);

  // Fetch metadata for dispatch tab
  const shouldFetchMetadata = activeTab === 'dispatch' && !metadataFetchedRef.current;

  const { data: metadataData } = usePyPSAData(
    '/pypsa/network-metadata',
    { projectPath, scenarioName: selectedScenario, networkFile: selectedNetwork },
    shouldFetchMetadata
  );

  // Auto-populate dates from metadata
  useEffect(() => {
    if (metadataData && metadataData.start_date && metadataData.end_date && !metadataFetchedRef.current) {
      setStartDate(metadataData.start_date.split('T')[0]);
      setEndDate(metadataData.end_date.split('T')[0]);
      metadataFetchedRef.current = true;
    }
  }, [metadataData]);

  // Reset metadata flag on network change
  useEffect(() => {
    metadataFetchedRef.current = false;
  }, [selectedNetwork]);

  // Fetch main data
  const {
    data: rawData,
    loading: dataLoading,
    error: dataError,
    refetch
  } = usePyPSAData(
    activeTabConfig?.endpoint,
    dataParams,
    !!activeTabConfig && !!detection
  );

  // Transform data based on active tab
  const transformedData = useMemo(() => {
    if (!rawData) return null;

    switch (activeTab) {
      case 'capacity':
        return transformCapacityData(rawData);
      case 'dispatch':
        return transformDispatchData(rawData);
      case 'metrics':
        return transformRenewableShareData(rawData);
      case 'storage':
        return transformStorageData(rawData);
      case 'emissions':
        return transformEmissionsData(rawData);
      case 'costs':
        return transformSystemCostsData(rawData);
      case 'network':
        return transformLinesData(rawData);
      default:
        return rawData;
    }
  }, [rawData, activeTab]);

  // Export to CSV
  const exportToCSV = useCallback(() => {
    if (!transformedData) return;

    let csvContent = '';
    let filename = `${activeTab}_${new Date().toISOString().split('T')[0]}.csv`;

    // Handle different data structures
    if (Array.isArray(transformedData)) {
      if (transformedData.length === 0) return;
      const headers = Object.keys(transformedData[0]);
      csvContent = [
        headers.join(','),
        ...transformedData.map(row => headers.map(h => row[h] || '').join(','))
      ].join('\n');
    } else {
      // Handle object structure
      csvContent = JSON.stringify(transformedData, null, 2);
      filename = filename.replace('.csv', '.json');
    }

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }, [transformedData, activeTab]);

  // Render loading state during detection
  if (detectionLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
        <LoadingState message="Detecting network type..." />
      </div>
    );
  }

  // Render detection error
  if (detectionError && !detection) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
        <ErrorState error={detectionError} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 p-8" style={{ minWidth: '1280px' }}>
      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-md border-2 border-gray-200 p-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                PyPSA Network Analysis
              </h1>
              <p className="text-lg text-gray-600">
                {selectedNetwork} • {selectedScenario}
              </p>
            </div>
            {detection && (
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <div>
                    <p className="text-sm font-bold text-gray-900">Network Loaded</p>
                    <p className="text-xs text-gray-600">
                      {detection.workflow_type === 'single-period' && `Single period • ${detection.snapshot_count || 0} snapshots`}
                      {detection.workflow_type === 'multi-period' && `Multi-period • ${detection.periods?.length || 0} periods`}
                      {detection.workflow_type === 'multi-file' && `Multi-file • ${detection.years?.length || 0} years`}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-2xl shadow-md border-2 border-gray-200 p-3">
          <div className="grid grid-cols-7 gap-3">
            {TABS.map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex flex-col items-center gap-3 p-5 rounded-xl transition-all duration-200 font-medium
                    ${isActive
                      ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-xl scale-105'
                      : 'bg-gray-50 text-gray-700 hover:bg-gray-100 hover:shadow-lg hover:scale-102'
                    }
                  `}
                  title={tab.description}
                >
                  <Icon className="w-7 h-7" />
                  <span className="text-sm text-center leading-tight">
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Controls Bar */}
        {activeTab === 'dispatch' && (
          <div className="bg-white rounded-2xl shadow-md border-2 border-gray-200 p-5">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-3">
                <label className="text-sm font-bold text-gray-700">Resolution:</label>
                <select
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  className="px-4 py-2 border-2 border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {RESOLUTIONS.map(res => (
                    <option key={res.value} value={res.value}>
                      {res.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-3">
                <label className="text-sm font-bold text-gray-700">From:</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-4 py-2 border-2 border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-3">
                <label className="text-sm font-bold text-gray-700">To:</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-4 py-2 border-2 border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex-1"></div>

              {transformedData && (
                <button
                  onClick={exportToCSV}
                  className="flex items-center gap-2 px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-md hover:shadow-lg font-medium"
                >
                  <Download className="w-5 h-5" />
                  Export
                </button>
              )}
            </div>
          </div>
        )}

        {/* Data Visualization Panel */}
        <div className="bg-white rounded-2xl shadow-md border-2 border-gray-200 p-8">
          <div className="mb-6">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              {activeTabConfig?.label}
            </h2>
            <p className="text-gray-600">
              {activeTabConfig?.description}
            </p>
          </div>

          {/* Render appropriate panel based on active tab */}
          {activeTab === 'dispatch' && (
            <DispatchPanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
          {activeTab === 'capacity' && (
            <CapacityPanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
          {activeTab === 'metrics' && (
            <MetricsPanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
          {activeTab === 'storage' && (
            <StoragePanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
          {activeTab === 'emissions' && (
            <EmissionsPanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
          {activeTab === 'costs' && (
            <CostsPanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
          {activeTab === 'network' && (
            <NetworkPanel
              data={transformedData}
              loading={dataLoading}
              error={dataError}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default UnifiedNetworkView;
