import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

/**
 * Adapter component to render the same data in different chart types
 * Supports: line, area, stacked-area, bar, stacked-bar
 */
const ChartTypeAdapter = ({
  data,
  chartType = 'line',
  dataKeys = [],
  colors = {},
  // title is reserved for future use
  // eslint-disable-next-line no-unused-vars
  title,
  xAxisKey = 'name',
  yAxisLabel = 'Value',
  showLoad = false, // Special flag to show load line overlay (for dispatch)
  height = 400
}) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-slate-50 rounded-lg border border-slate-200">
        <p className="text-slate-500">No data available</p>
      </div>
    );
  }

  // Auto-detect data keys if not provided
  const keys = dataKeys.length > 0 ? dataKeys : Object.keys(data[0]).filter(k => k !== xAxisKey);
  
  // Default colors for data series
  const defaultColors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#14b8a6', '#f97316', '#6366f1'
  ];

  const getColor = (key, index) => colors[key] || defaultColors[index % defaultColors.length];

  const commonProps = {
    data,
    margin: { top: 5, right: 30, left: 0, bottom: 5 }
  };

  const tooltipContent = (props) => {
    const { active, payload } = props;
    if (!active || !payload) return null;

    return (
      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-lg">
        <p className="font-medium text-slate-800 mb-2">{payload[0]?.payload[xAxisKey]}</p>
        <div className="space-y-1">
          {payload.map((entry, idx) => (
            <div key={idx} className="text-sm">
              <span style={{ color: entry.color }} className="font-medium">
                {entry.name}:
              </span>
              <span className="ml-2 font-mono">{entry.value?.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  switch (chartType) {
    case 'area':
      return (
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart {...commonProps}>
            <defs>
              {keys.map((key, idx) => (
                <linearGradient key={key} id={`color${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={getColor(key, idx)} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={getColor(key, idx)} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={xAxisKey} stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip content={tooltipContent} />
            <Legend />
            {keys.map((key, idx) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={getColor(key, idx)}
                fillOpacity={1}
                fill={`url(#color${key})`}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      );

    case 'stacked-area':
      // Separate keys into positive and negative groups based on data
      const positiveKeys = [];
      const negativeKeys = [];

      keys.forEach(key => {
        if (key === 'Load') return; // Skip Load, it's rendered separately

        // Check if this key has predominantly negative values
        const hasNegativeValues = data.some(d => d[key] < -0.001);
        if (hasNegativeValues || key.includes('Charge')) {
          negativeKeys.push(key);
        } else {
          positiveKeys.push(key);
        }
      });

      return (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart {...commonProps}>
            <defs>
              {keys.map((key, idx) => (
                <linearGradient key={key} id={`stackedColor${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={getColor(key, idx)} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={getColor(key, idx)} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey={xAxisKey}
              stroke="#94a3b8"
              tick={{ fontSize: 11 }}
              tickFormatter={(value) => {
                // Format timestamp for better readability
                if (xAxisKey === 'timestamp') {
                  try {
                    const date = new Date(value);
                    return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:00`;
                  } catch {
                    return value;
                  }
                }
                return value;
              }}
            />
            <YAxis stroke="#94a3b8" label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip content={tooltipContent} />
            <Legend />

            {/* Render positive stack (generation and discharge) */}
            {positiveKeys.map((key, idx) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={getColor(key, keys.indexOf(key))}
                fill={getColor(key, keys.indexOf(key))}
                stackId="positive"
                fillOpacity={0.8}
              />
            ))}

            {/* Render negative stack (storage charge) below x-axis */}
            {negativeKeys.map((key, idx) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={getColor(key, keys.indexOf(key))}
                fill={getColor(key, keys.indexOf(key))}
                stackId="negative"
                fillOpacity={0.8}
              />
            ))}

            {/* Add Load line overlay if showLoad is true */}
            {showLoad && data[0]?.Load !== undefined && (
              <Line
                type="monotone"
                dataKey="Load"
                stroke="#000000"
                strokeWidth={2.5}
                strokeDasharray="5 5"
                dot={false}
                name="Load"
                isAnimationActive={false}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      );

    case 'bar':
      return (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={xAxisKey} stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip content={tooltipContent} />
            <Legend />
            {keys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                opacity={0.8}
              >
                {/* Apply colors per data point based on xAxisKey (carrier name) */}
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry[xAxisKey], index)} />
                ))}
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      );

    case 'stacked-bar':
      return (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={xAxisKey} stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip content={tooltipContent} />
            <Legend />
            {keys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                fill={getColor(key, idx)}
                stackId="stack"
                opacity={0.8}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      );

    case 'line':
    default:
      return (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={xAxisKey} stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip content={tooltipContent} />
            <Legend />
            {keys.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={getColor(key, idx)}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      );
  }
};

export default ChartTypeAdapter;