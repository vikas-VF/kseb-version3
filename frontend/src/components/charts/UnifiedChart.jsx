/**
 * UnifiedChart - Universal Chart Wrapper
 * ========================================
 *
 * This component provides a unified interface for all chart types used
 * in the PyPSA analysis views. It delegates to existing specialized
 * chart components to avoid code duplication.
 *
 * Supported Chart Types:
 * - line, area, bar, stacked-area, stacked-bar (via ChartTypeAdapter)
 * - pie, donut (via ReactApexChart)
 * - table (via DataTableView)
 * - heatmap, treemap (placeholder for future implementation)
 *
 * Usage:
 *   <UnifiedChart
 *     data={chartData}
 *     type="bar"
 *     config={visualizationConfig}
 *     height={400}
 *   />
 */

import React, { useMemo } from 'react';
import ReactApexChart from 'react-apexcharts';
import { AlertCircle } from 'lucide-react';

// Import existing chart components
import ChartTypeAdapter from '../pypsa/ChartTypeAdapter';
import DataTableView from '../pypsa/DataTableView';

// Re-export DataTableView as TableView for compatibility
export { default as TableView } from '../pypsa/DataTableView';

const UnifiedChart = ({
  data,
  type = 'bar',
  config = {},
  height = 400,
  loading = false,
  error = null
}) => {
  // ====== LOADING STATE ======
  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-slate-50 rounded-lg border border-slate-200"
        style={{ height: `${height}px` }}
      >
        <div className="text-slate-500 text-sm">Loading chart...</div>
      </div>
    );
  }

  // ====== ERROR STATE ======
  if (error) {
    return (
      <div
        className="flex items-center justify-center bg-red-50 rounded-lg border border-red-200 p-6"
        style={{ minHeight: `${height}px` }}
      >
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-3" />
          <p className="text-red-700 text-sm font-medium">Error loading chart</p>
          <p className="text-red-600 text-xs mt-1">{error}</p>
        </div>
      </div>
    );
  }

  // ====== NO DATA STATE ======
  if (!data || (Array.isArray(data) && data.length === 0)) {
    return (
      <div
        className="flex items-center justify-center bg-slate-50 rounded-lg border border-slate-200"
        style={{ height: `${height}px` }}
      >
        <div className="text-center text-slate-500">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">No data available for visualization</p>
        </div>
      </div>
    );
  }

  // ====== RECHARTS-BASED CHARTS ======
  // These use ChartTypeAdapter which uses Recharts library
  if (['line', 'area', 'bar', 'stacked-area', 'stacked-bar'].includes(type)) {
    return (
      <ChartTypeAdapter
        data={data}
        chartType={type}
        dataKeys={config.dataKeys || []}
        colors={config.colors || {}}
        title={config.title}
        xAxisKey={config.xAxisKey || 'name'}
        yAxisLabel={config.yAxisLabel || 'Value'}
        showLoad={config.showLoad || false}
        height={height}
      />
    );
  }

  // ====== PIE CHART (APEXCHARTS) ======
  if (type === 'pie') {
    return <PieChart data={data} config={config} height={height} />;
  }

  // ====== DONUT CHART (APEXCHARTS) ======
  if (type === 'donut') {
    return <DonutChart data={data} config={config} height={height} />;
  }

  // ====== TABLE VIEW ======
  if (type === 'table') {
    return (
      <DataTableView
        data={data}
        columns={config.columns || []}
        title={config.title || 'Data Table'}
        sortable={config.sortable !== false}
        onExport={true}
      />
    );
  }

  // ====== HEATMAP (PLACEHOLDER) ======
  if (type === 'heatmap') {
    return <PlaceholderChart type="Heatmap" height={height} />;
  }

  // ====== TREEMAP (PLACEHOLDER) ======
  if (type === 'treemap') {
    return <PlaceholderChart type="Treemap" height={height} />;
  }

  // ====== UNKNOWN CHART TYPE ======
  return (
    <div
      className="flex items-center justify-center bg-yellow-50 rounded-lg border border-yellow-200 p-6"
      style={{ height: `${height}px` }}
    >
      <div className="text-center">
        <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-3" />
        <p className="text-yellow-700 text-sm font-medium">
          Unsupported chart type: <code className="font-mono">{type}</code>
        </p>
        <p className="text-yellow-600 text-xs mt-1">
          Supported types: line, area, bar, stacked-area, stacked-bar, pie, donut, table
        </p>
      </div>
    </div>
  );
};

// ============================================================================
// SPECIALIZED CHART IMPLEMENTATIONS
// ============================================================================

/**
 * Pie Chart using ApexCharts
 */
const PieChart = ({ data, config, height }) => {
  const chartConfig = useMemo(() => {
    // Handle array of objects with label/value pairs
    if (Array.isArray(data)) {
      const labels = data.map(d => d.label || d.name || d.carrier || d.technology || 'Unknown');
      const values = data.map(d => d.value || d.count || d.capacity || 0);
      const colors = config.colors || generateColors(labels.length);

      return {
        series: values,
        options: {
          chart: { type: 'pie' },
          labels: labels,
          colors: colors,
          legend: {
            position: 'right',
            fontSize: '14px'
          },
          dataLabels: {
            enabled: true,
            formatter: (val) => (typeof val === 'number' ? val.toFixed(1) : '0') + '%'
          },
          responsive: [{
            breakpoint: 768,
            options: {
              legend: { position: 'bottom' }
            }
          }]
        }
      };
    }

    // Handle object with key-value pairs
    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = config.colors || generateColors(labels.length);

    return {
      series: values,
      options: {
        chart: { type: 'pie' },
        labels: labels,
        colors: colors,
        legend: {
          position: 'right',
          fontSize: '14px'
        },
        dataLabels: {
          enabled: true,
          formatter: (val) => (typeof val === 'number' ? val.toFixed(1) : '0') + '%'
        }
      }
    };
  }, [data, config]);

  return (
    <div className="w-full">
      <ReactApexChart
        options={chartConfig.options}
        series={chartConfig.series}
        type="pie"
        height={height}
      />
    </div>
  );
};

/**
 * Donut Chart using ApexCharts
 */
const DonutChart = ({ data, config, height }) => {
  const chartConfig = useMemo(() => {
    // Handle array of objects
    if (Array.isArray(data)) {
      const labels = data.map(d => d.label || d.name || d.carrier || d.technology || 'Unknown');
      const values = data.map(d => d.value || d.count || d.capacity || 0);
      const colors = config.colors || generateColors(labels.length);
      const total = values.reduce((sum, v) => sum + v, 0);

      return {
        series: values,
        options: {
          chart: { type: 'donut' },
          labels: labels,
          colors: colors,
          legend: {
            position: 'right',
            fontSize: '14px'
          },
          dataLabels: {
            enabled: true,
            formatter: (val) => (typeof val === 'number' ? val.toFixed(1) : '0') + '%'
          },
          plotOptions: {
            pie: {
              donut: {
                size: '65%',
                labels: {
                  show: true,
                  total: {
                    show: true,
                    label: config.totalLabel || 'Total',
                    formatter: () => formatNumber(total)
                  }
                }
              }
            }
          },
          responsive: [{
            breakpoint: 768,
            options: {
              legend: { position: 'bottom' }
            }
          }]
        }
      };
    }

    // Handle object
    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = config.colors || generateColors(labels.length);
    const total = values.reduce((sum, v) => sum + v, 0);

    return {
      series: values,
      options: {
        chart: { type: 'donut' },
        labels: labels,
        colors: colors,
        legend: {
          position: 'right',
          fontSize: '14px'
        },
        dataLabels: {
          enabled: true,
          formatter: (val) => (typeof val === 'number' ? val.toFixed(1) : '0') + '%'
        },
        plotOptions: {
          pie: {
            donut: {
              size: '65%',
              labels: {
                show: true,
                total: {
                  show: true,
                  label: config.totalLabel || 'Total',
                  formatter: () => formatNumber(total)
                }
              }
            }
          }
        }
      }
    };
  }, [data, config]);

  return (
    <div className="w-full">
      <ReactApexChart
        options={chartConfig.options}
        series={chartConfig.series}
        type="donut"
        height={height}
      />
    </div>
  );
};

/**
 * Placeholder for unimplemented chart types
 */
const PlaceholderChart = ({ type, height }) => (
  <div
    className="flex items-center justify-center bg-blue-50 rounded-lg border-2 border-dashed border-blue-300"
    style={{ height: `${height}px` }}
  >
    <div className="text-center text-blue-600">
      <div className="text-4xl mb-2">📊</div>
      <p className="font-medium">{type} Chart</p>
      <p className="text-sm text-blue-500 mt-1">Coming soon...</p>
    </div>
  </div>
);

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Generate an array of distinct colors
 */
function generateColors(count) {
  const colors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#6366f1',
    '#84cc16', '#f43f5e', '#0ea5e9', '#d946ef', '#eab308'
  ];

  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  return result;
}

/**
 * Format numbers with appropriate units
 */
function formatNumber(value) {
  if (typeof value !== 'number' || isNaN(value)) return '0';
  if (value >= 1e9) return (value / 1e9).toFixed(1) + 'B';
  if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M';
  if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K';
  return value.toFixed(0);
}

export default UnifiedChart;
