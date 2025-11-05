import React, { useState, useMemo } from 'react';
import { Download, ChevronUp, ChevronDown } from 'lucide-react';

const DataTableView = ({ 
  data, 
  columns = [], 
  title = 'Data Table',
  sortable = true,
  onExport 
}) => {
  const [sortConfig, setSortConfig] = useState({ column: null, direction: 'asc' });

  // Automatically detect columns if not provided
  const detectedColumns = useMemo(() => {
    if (columns.length > 0) return columns;
    
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    
    return Object.keys(data[0]).map(key => ({
      key,
      label: formatColumnName(key),
      sortable: true
    }));
  }, [data, columns]);

  const sortedData = useMemo(() => {
    if (!sortable || !sortConfig.column || !data) return data;

    const sorted = [...data].sort((a, b) => {
      const aVal = a[sortConfig.column];
      const bVal = b[sortConfig.column];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return sorted;
  }, [data, sortConfig, sortable]);

  const handleSort = (columnKey) => {
    if (!sortable) return;
    
    setSortConfig(prev => ({
      column: columnKey,
      direction: prev.column === columnKey && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleExport = () => {
    if (!onExport) return;
    
    const csv = [
      detectedColumns.map(col => col.label).join(','),
      ...sortedData.map(row =>
        detectedColumns.map(col => 
          JSON.stringify(row[col.key] ?? '').replace(/"/g, '""')
        ).join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="w-full p-8 bg-white rounded-lg border border-slate-200 text-center">
        <p className="text-slate-500 text-sm">No data available</p>
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-lg border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm font-medium transition-all"
        >
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 border-b border-slate-200 sticky top-0">
            <tr>
              {detectedColumns.map(col => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`
                    px-4 py-3 text-left font-semibold text-slate-700
                    ${sortable && col.sortable ? 'cursor-pointer hover:bg-slate-200' : ''}
                  `}
                >
                  <div className="flex items-center gap-2">
                    <span>{col.label}</span>
                    {sortable && col.sortable && sortConfig.column === col.key && (
                      <span className="text-xs">
                        {sortConfig.direction === 'asc' ? (
                          <ChevronUp size={14} className="inline" />
                        ) : (
                          <ChevronDown size={14} className="inline" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {sortedData.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50 transition-colors">
                {detectedColumns.map(col => (
                  <td key={`${idx}-${col.key}`} className="px-4 py-3 text-slate-700">
                    {formatCellValue(row[col.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 text-xs text-slate-600 text-right">
        Showing {sortedData.length} row{sortedData.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
};

// Helper Functions
function formatColumnName(name) {
  return name
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatCellValue(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') return value.toFixed(2);
  if (typeof value === 'boolean') return value ? '✓' : '✗';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export default DataTableView;