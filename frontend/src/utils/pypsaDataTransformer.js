/**
 * PyPSA Data Transformer
 * ======================
 *
 * Transforms backend API responses into chart-ready data formats.
 *
 * Backend returns nested structures like:
 * {
 *   success: true,
 *   data: {
 *     capacities: { generators: [...], storage_units: [...] },
 *     totals: {...},
 *     aggregates: {...}
 *   }
 * }
 *
 * Charts need simple arrays like:
 * [
 *   { name: 'Solar', value: 1000 },
 *   { name: 'Wind', value: 2000 }
 * ]
 */

/**
 * Transform total capacities data for charts - Enhanced for multi-period support
 */
export const transformCapacityData = (backendData) => {
  console.log('[transformCapacityData] Input:', backendData);

  if (!backendData) {
    console.warn('[transformCapacityData] No data provided');
    return { generators: [], storage_units: [], stores: [], totals: null, isMultiPeriod: false };
  }

  // Handle different response structures
  const dataSource = backendData.data || backendData;
  const capacities = dataSource.capacities || dataSource;

  // Check if this is multi-period data (years as columns)
  const isMultiPeriod = capacities.generators &&
    Array.isArray(capacities.generators) &&
    capacities.generators.length > 0 &&
    Object.keys(capacities.generators[0]).some(key => !isNaN(parseInt(key)));

  const result = {
    generators: [],
    storage_units: [],
    stores: [],
    totals: dataSource.totals || null,
    aggregates: dataSource.aggregates || null,
    isMultiPeriod
  };

  // Generators
  if (capacities.generators && Array.isArray(capacities.generators)) {
    result.generators = capacities.generators.map(gen => {
      const baseData = {
        carrier: gen.Carrier || gen.carrier || 'Unknown',
        technology: gen.Technology || gen.technology || ''
      };

      if (isMultiPeriod) {
        // Multi-period: years as properties
        Object.keys(gen).forEach(key => {
          if (!isNaN(parseInt(key))) {
            baseData[key] = gen[key];
          }
        });
      } else {
        // Single period: value property
        baseData.value = gen.Capacity_MW || gen.capacity_mw || gen.Capacity_MW_value || 0;
      }

      return baseData;
    });
  }

  // Storage Units
  if (capacities.storage_units && Array.isArray(capacities.storage_units)) {
    result.storage_units = capacities.storage_units.map(unit => {
      const baseData = {
        carrier: unit.Carrier || unit.carrier || 'Unknown',
        technology: unit.Technology || unit.technology || ''
      };

      if (isMultiPeriod) {
        Object.keys(unit).forEach(key => {
          if (!isNaN(parseInt(key))) {
            baseData[key] = unit[key];
          }
        });
      } else {
        baseData.value = unit.Power_Capacity_MW || unit.power_capacity_mw || unit.Power_Capacity_MW_value || 0;
      }

      return baseData;
    });
  }

  // Stores
  if (capacities.stores && Array.isArray(capacities.stores)) {
    result.stores = capacities.stores.map(store => {
      const baseData = {
        carrier: store.Carrier || store.carrier || 'Unknown',
        technology: store.Technology || store.technology || ''
      };

      if (isMultiPeriod) {
        Object.keys(store).forEach(key => {
          if (!isNaN(parseInt(key))) {
            baseData[key] = store[key];
          }
        });
      } else {
        baseData.value = store.Energy_Capacity_MWh || store.energy_capacity_mwh || store.Energy_Capacity_MWh_value || 0;
      }

      return baseData;
    });
  }

  console.log('[transformCapacityData] Output:', {
    generatorCount: result.generators.length,
    storageUnitCount: result.storage_units.length,
    storeCount: result.stores.length,
    isMultiPeriod
  });

  return result;
};

/**
 * Transform dispatch time-series data for stacked area chart
 */
export const transformDispatchData = (backendData) => {
  console.log('[transformDispatchData] Input:', backendData);

  // Handle null/undefined
  if (!backendData) {
    console.warn('[transformDispatchData] No data provided');
    return [];
  }

  // Extract timestamps - handle different possible structures
  const timestamps = backendData.timestamps || [];

  if (timestamps.length === 0) {
    console.warn('[transformDispatchData] No timestamps found');
    return [];
  }

  const { generation = {}, storage_discharge = {}, storage_charge = {}, load = [] } = backendData;

  console.log('[transformDispatchData] Processing:', {
    timestampCount: timestamps.length,
    generationCarriers: Object.keys(generation),
    storageDischarge: Object.keys(storage_discharge),
    storageCharge: Object.keys(storage_charge),
    loadLength: load.length
  });

  // Create array of objects where each object represents a timestamp
  const chartData = timestamps.map((timestamp, index) => {
    const dataPoint = { timestamp: new Date(timestamp).toISOString() };

    // Add generation data
    Object.entries(generation).forEach(([carrier, values]) => {
      if (Array.isArray(values) && values.length > index) {
        dataPoint[carrier] = values[index] || 0;
      }
    });

    // Add storage discharge data
    Object.entries(storage_discharge).forEach(([carrier, values]) => {
      if (Array.isArray(values) && values.length > index) {
        dataPoint[carrier] = values[index] || 0;
      }
    });

    // Add storage charge data (negative values)
    Object.entries(storage_charge).forEach(([carrier, values]) => {
      if (Array.isArray(values) && values.length > index) {
        dataPoint[carrier] = values[index] || 0;
      }
    });

    // Add load as a separate line
    if (Array.isArray(load) && load.length > index) {
      dataPoint.Load = load[index] || 0;
    }

    return dataPoint;
  });

  console.log('[transformDispatchData] Output:', {
    dataPoints: chartData.length,
    sampleDataPoint: chartData[0],
    dataKeys: chartData.length > 0 ? Object.keys(chartData[0]) : []
  });

  return chartData;
};

/**
 * Transform daily profile data for charts (average by hour of day)
 */
export const transformDailyProfileData = (backendData) => {
  if (!backendData || !backendData.by_hour) {
    return [];
  }

  const { by_hour } = backendData;

  // Convert by_hour object to array format
  const chartData = [];
  for (let hour = 0; hour < 24; hour++) {
    const dataPoint = { hour: hour };

    if (by_hour[hour]) {
      Object.entries(by_hour[hour]).forEach(([carrier, value]) => {
        dataPoint[carrier] = value || 0;
      });
    }

    chartData.push(dataPoint);
  }

  return chartData;
};

/**
 * Transform duration curve data for charts
 */
export const transformDurationCurveData = (backendData) => {
  if (!backendData || !backendData.duration_curves) {
    return [];
  }

  const { duration_curves } = backendData;

  // Group by type (generation, load)
  const loadData = duration_curves.filter(d => d.type === 'load');
  const genData = duration_curves.filter(d => d.type === 'generation');

  // Transform to percentage-based x-axis (0-100%)
  const transformToPercent = (data) => {
    const totalPoints = data.length;
    return data.map((point, index) => ({
      duration_percent: (index / totalPoints) * 100,
      power_mw: point.power_mw
    }));
  };

  return {
    load: transformToPercent(loadData),
    generation: transformToPercent(genData)
  };
};

/**
 * Transform energy mix data for charts
 */
export const transformEnergyMixData = (backendData) => {
  if (!backendData || !backendData.energy_mix) {
    return [];
  }

  return backendData.energy_mix.map(item => ({
    name: item.Carrier || item.carrier || 'Unknown',
    value: item.Energy_MWh || item.energy_mwh || 0,
    percentage: item['Share_%'] || item.share_percent || 0
  }));
};

/**
 * Transform renewable share data for charts - Enhanced for single and multi-period with CUF and curtailment
 */
export const transformRenewableShareData = (backendData) => {
  if (!backendData) {
    return { breakdown: [], summary: null, isMultiPeriod: false, capacity_factors: [], curtailment: [] };
  }

  // Check if this is multi-period data
  const dataSource = backendData.data || backendData;
  const isMultiPeriod = dataSource.renewable_share_percent && typeof dataSource.renewable_share_percent === 'object';

  const result = {
    breakdown: [],
    summary: null,
    isMultiPeriod,
    capacity_factors: [],
    curtailment: []
  };

  if (isMultiPeriod) {
    // Multi-period data with years
    result.summary = {
      renewable_share_percent: dataSource.renewable_share_percent || {},
      renewable_energy_mwh: dataSource.renewable_energy_mwh || {},
      total_energy_mwh: dataSource.total_energy_mwh || {},
      renewable_carriers: dataSource.renewable_carriers || [],
      years: dataSource.years || []
    };

    // Transform breakdown data
    if (dataSource.breakdown && Array.isArray(dataSource.breakdown)) {
      result.breakdown = dataSource.breakdown;
    }

    // Transform capacity factors (CUF) data for multi-period
    // Format: [{"Carrier": "Solar", "2025": 23.5, "2026": 24.1}]
    if (dataSource.capacity_factors && Array.isArray(dataSource.capacity_factors)) {
      result.capacity_factors = dataSource.capacity_factors;
    }

    // Transform curtailment data for multi-period
    // Format: [{"Carrier": "Solar", "Curtailment_MWh": {"2025": 1500, "2026": 1600}, "Curtailment_%": {...}}]
    if (dataSource.curtailment && Array.isArray(dataSource.curtailment)) {
      result.curtailment = dataSource.curtailment;
    }
  } else {
    // Single period data
    result.summary = {
      renewable_share_percent: dataSource.renewable_share_percent || backendData.renewable_share_percent || 0,
      renewable_energy_mwh: dataSource.renewable_energy_mwh || backendData.renewable_energy_mwh || 0,
      total_energy_mwh: dataSource.total_energy_mwh || backendData.total_energy_mwh || 0,
      renewable_carriers: dataSource.renewable_carriers || backendData.renewable_carriers || [],
      total_curtailed_mwh: dataSource.total_curtailed_mwh || backendData.total_curtailed_mwh || 0,
      curtailment_rate_percent: dataSource.curtailment_rate_percent || backendData.curtailment_rate_percent || 0
    };

    // Transform breakdown data
    if (dataSource.breakdown && Array.isArray(dataSource.breakdown)) {
      result.breakdown = dataSource.breakdown.map(item => ({
        carrier: item.Carrier || item.carrier || 'Unknown',
        renewable_energy_mwh: item.Renewable_Energy_MWh || item.renewable_energy_mwh || 0,
        share_percent: item['Share_%'] || item.share_percent || 0
      }));
    } else if (backendData.breakdown && Array.isArray(backendData.breakdown)) {
      result.breakdown = backendData.breakdown.map(item => ({
        carrier: item.Carrier || item.carrier || 'Unknown',
        renewable_energy_mwh: item.Renewable_Energy_MWh || item.renewable_energy_mwh || 0,
        share_percent: item['Share_%'] || item.share_percent || 0
      }));
    }

    // Transform capacity factors (CUF) data
    if (dataSource.capacity_factors && Array.isArray(dataSource.capacity_factors)) {
      result.capacity_factors = dataSource.capacity_factors.map(item => ({
        carrier: item.Carrier || item.carrier || 'Unknown',
        utilization_percent: item['Utilization_%'] || item.utilization_percent || 0,
        capacity_factor: item.Capacity_Factor || item.capacity_factor || 0
      }));
    } else if (backendData.capacity_factors && Array.isArray(backendData.capacity_factors)) {
      result.capacity_factors = backendData.capacity_factors.map(item => ({
        carrier: item.Carrier || item.carrier || 'Unknown',
        utilization_percent: item['Utilization_%'] || item.utilization_percent || 0,
        capacity_factor: item.Capacity_Factor || item.capacity_factor || 0
      }));
    }

    // Transform curtailment data
    if (dataSource.curtailment && Array.isArray(dataSource.curtailment)) {
      result.curtailment = dataSource.curtailment.map(item => ({
        carrier: item.carrier || 'Unknown',
        generator: item.generator || '',
        curtailment_mwh: item.curtailment_mwh || 0,
        curtailment_percent: item.curtailment_percent || 0,
        actual_generation: item.actual_generation || 0,
        potential_generation: item.potential_generation || 0
      }));
    } else if (backendData.curtailment && Array.isArray(backendData.curtailment)) {
      result.curtailment = backendData.curtailment.map(item => ({
        carrier: item.carrier || 'Unknown',
        generator: item.generator || '',
        curtailment_mwh: item.curtailment_mwh || 0,
        curtailment_percent: item.curtailment_percent || 0,
        actual_generation: item.actual_generation || 0,
        potential_generation: item.potential_generation || 0
      }));
    }
  }

  return result;
};

/**
 * Transform storage units and stores data for charts - Enhanced
 */
export const transformStorageData = (backendData) => {
  if (!backendData) {
    return { storage_units: [], stores: [] };
  }

  const dataSource = backendData.data || backendData;
  const result = {
    storage_units: [],
    stores: []
  };

  // Storage Units (power capacity in MW)
  if (dataSource.storage_units && Array.isArray(dataSource.storage_units)) {
    result.storage_units = dataSource.storage_units.map(unit => ({
      name: unit.Carrier || unit.carrier || unit.name || 'Unknown',
      carrier: unit.Carrier || unit.carrier || 'Unknown',
      power_capacity_mw: unit.Power_Capacity_MW || unit.power_capacity_mw || 0,
      energy_capacity_mwh: unit.Energy_Capacity_MWh || unit.energy_capacity_mwh || 0,
      max_hours: unit.max_hours || 0,
      soc_mwh: unit.SOC_MWh || unit.soc_mwh || 0
    }));
  }

  // Stores (energy capacity in MWh)
  if (dataSource.stores && Array.isArray(dataSource.stores)) {
    result.stores = dataSource.stores.map(store => ({
      name: store.Carrier || store.carrier || store.name || 'Unknown',
      carrier: store.Carrier || store.carrier || 'Unknown',
      energy_capacity_mwh: store.Energy_Capacity_MWh || store.energy_capacity_mwh || 0,
      max_hours: store.max_hours || 0,
      max_dispatch_mw: store.max_dispatch_mw || 0
    }));
  }

  return result;
};

/**
 * Transform emissions data for charts - Enhanced for new data structure
 */
export const transformEmissionsData = (backendData) => {
  if (!backendData) {
    return { emissions: [], summary: null };
  }

  // Handle nested data structure
  const dataSource = backendData.data || backendData;

  const result = {
    emissions: [],
    summary: {
      total_emissions_tco2: dataSource.total_emissions_tco2 || 0,
      emission_intensity_tco2_per_mwh: dataSource.emission_intensity_tco2_per_mwh || 0
    }
  };

  // Process emissions array
  if (dataSource.emissions && Array.isArray(dataSource.emissions)) {
    result.emissions = dataSource.emissions.map(item => ({
      carrier: item.Carrier || item.carrier || 'Unknown',
      co2_emissions_tco2: item.CO2_Emissions_tCO2 || item.co2_emissions || 0,
      energy_mwh: item.Energy_MWh || item.energy_mwh || 0,
      emission_factor: item.Emission_Factor_tCO2_per_MWh || item.emission_factor || 0
    }));
  }

  // Legacy format support
  if (backendData.emissions && Array.isArray(backendData.emissions)) {
    result.emissions = backendData.emissions.map(item => ({
      carrier: item.Carrier || item.carrier || 'Unknown',
      co2_emissions_tco2: item.Emissions_tonnes || item.emissions || 0,
      energy_mwh: 0,
      emission_factor: 0
    }));
  }

  return result;
};

/**
 * Transform system costs data for charts - Enhanced for new data structure
 */
export const transformSystemCostsData = (backendData) => {
  if (!backendData) {
    return { costs: [], totals: null };
  }

  // Handle nested data structure
  const dataSource = backendData.data || backendData;

  const result = {
    costs: [],
    totals: dataSource.total_costs || null
  };

  // Process costs array
  if (dataSource.costs && Array.isArray(dataSource.costs)) {
    result.costs = dataSource.costs.map(item => ({
      carrier: item.Carrier || item.carrier || 'Unknown',
      capital_cost: item.Capital_Cost || item.capital_cost || 0,
      marginal_cost: item.Marginal_Cost || item.marginal_cost || 0,
      total_cost: item.Total_Cost || item.total_cost || 0
    }));
  }

  // Legacy format support
  if (backendData.by_carrier && typeof backendData.by_carrier === 'object') {
    result.costs = Object.entries(backendData.by_carrier).map(([carrier, value]) => ({
      carrier,
      capital_cost: 0,
      marginal_cost: 0,
      total_cost: value || 0
    }));
  }

  return result;
};

/**
 * Transform lines data for charts
 */
export const transformLinesData = (backendData) => {
  if (!backendData || !backendData.lines) {
    return [];
  }

  if (Array.isArray(backendData.lines)) {
    return backendData.lines.map(line => ({
      name: line.name || line.line_id || 'Unknown',
      capacity: line.s_nom || line.capacity || 0,
      utilization: line.loading || line.utilization || 0,
      from: line.bus0 || line.from_bus || '',
      to: line.bus1 || line.to_bus || ''
    }));
  }

  return [];
};

/**
 * Transform capacity factors (CUF) data for charts
 */
export const transformCapacityFactorData = (backendData) => {
  if (!backendData) {
    return [];
  }

  const data = [];

  // Handle by_carrier object
  if (backendData.by_carrier && typeof backendData.by_carrier === 'object') {
    Object.entries(backendData.by_carrier).forEach(([carrier, cuf]) => {
      data.push({
        name: carrier,
        cuf: typeof cuf === 'number' ? cuf * 100 : 0, // Convert to percentage
        value: typeof cuf === 'number' ? cuf * 100 : 0
      });
    });
  }

  // Handle capacity_factors array
  if (backendData.capacity_factors && Array.isArray(backendData.capacity_factors)) {
    return backendData.capacity_factors.map(item => ({
      name: item.Carrier || item.carrier || 'Unknown',
      cuf: (item.CUF || item.cuf || 0) * 100,
      value: (item.CUF || item.cuf || 0) * 100
    }));
  }

  return data;
};

/**
 * Transform curtailment data for charts
 */
export const transformCurtailmentData = (backendData) => {
  if (!backendData) {
    return [];
  }

  const data = [];

  // Handle by_carrier object
  if (backendData.by_carrier && typeof backendData.by_carrier === 'object') {
    Object.entries(backendData.by_carrier).forEach(([carrier, curtailment]) => {
      data.push({
        name: carrier,
        curtailment_mwh: curtailment.curtailment_mwh || 0,
        curtailment_percent: curtailment.curtailment_percent || 0,
        value: curtailment.curtailment_mwh || 0
      });
    });
  }

  // Handle curtailment array
  if (backendData.curtailment && Array.isArray(backendData.curtailment)) {
    return backendData.curtailment.map(item => ({
      name: item.Carrier || item.carrier || 'Unknown',
      curtailment_mwh: item.Curtailment_MWh || item.curtailment_mwh || 0,
      curtailment_percent: item['Curtailment_%'] || item.curtailment_percent || 0,
      value: item.Curtailment_MWh || item.curtailment_mwh || 0
    }));
  }

  return data;
};

/**
 * Transform storage state of charge data for time-series chart
 */
export const transformStorageSOCData = (backendData) => {
  if (!backendData || !backendData.timestamps || backendData.timestamps.length === 0) {
    return [];
  }

  const { timestamps, soc } = backendData;

  // Create array of objects where each object represents a timestamp
  const chartData = timestamps.map((timestamp, index) => {
    const dataPoint = { timestamp: new Date(timestamp).toISOString() };

    // Add SOC data for each storage unit/store
    Object.entries(soc || {}).forEach(([storage, values]) => {
      dataPoint[storage] = values[index] || 0;
    });

    return dataPoint;
  });

  return chartData;
};

/**
 * Main transformer function - routes to appropriate transformer
 */
export const transformPyPSAData = (data, analysisType) => {
  if (!data) {
    console.warn('[PyPSA Transformer] No data provided');
    return [];
  }

  console.log('[PyPSA Transformer] Transforming data for:', analysisType, data);

  // Handle case where data is already in simple array format
  if (Array.isArray(data)) {
    console.log('[PyPSA Transformer] Data is already array, returning as-is');
    return data;
  }

  // Route to appropriate transformer based on analysis type
  let transformed = [];

  switch (analysisType) {
    case 'capacity':
      transformed = transformCapacityData(data);
      break;

    case 'dispatch':
      transformed = transformDispatchData(data);
      break;

    case 'metrics':
      transformed = transformRenewableShareData(data);
      break;

    case 'storage':
      transformed = transformStorageData(data);
      break;

    case 'emissions':
      transformed = transformEmissionsData(data);
      break;

    case 'prices':
      transformed = transformSystemCostsData(data);
      break;

    case 'network_flow':
      transformed = transformLinesData(data);
      break;

    case 'daily_profile':
      transformed = transformDailyProfileData(data);
      break;

    case 'duration_curve':
      transformed = transformDurationCurveData(data);
      break;

    case 'capacity_factor':
    case 'cuf':
      transformed = transformCapacityFactorData(data);
      break;

    case 'curtailment':
      transformed = transformCurtailmentData(data);
      break;

    case 'storage_soc':
    case 'soc':
      transformed = transformStorageSOCData(data);
      break;

    default:
      console.warn('[PyPSA Transformer] Unknown analysis type:', analysisType);

      // If data has a common array property, use it
      if (data.data && Array.isArray(data.data)) {
        transformed = data.data;
      }
      // Try to extract first array found
      else {
        const firstArray = Object.values(data).find(v => Array.isArray(v));
        if (firstArray) {
          transformed = firstArray;
        }
        // Convert object to array of key-value pairs
        else {
          transformed = Object.entries(data).map(([key, value]) => ({
            name: key,
            value: typeof value === 'number' ? value : 0
          }));
        }
      }
  }

  console.log('[PyPSA Transformer] Transformed result:', transformed);
  return transformed;
};

/**
 * Get chart configuration based on analysis type
 */
/**
 * Helper to extract data keys from dispatch data
 */
export const getDispatchDataKeys = (data) => {
  if (!data || data.length === 0) return [];
  const keys = Object.keys(data[0]).filter(key => key !== 'timestamp' && key !== 'Load');
  return keys;
};

// PyPSA Color Scheme - Matching Streamlit colors
export const PYPSA_COLORS = {
  // Generation carriers
  'Coal': '#8B4513',
  'Lignite': '#A0522D',
  'Nuclear': '#FF1493',
  'Hydro': '#4169E1',
  'Hydro RoR': '#1E90FF',
  'Hydro Storage': '#00BFFF',
  'Solar': '#FFD700',
  'Wind': '#87CEEB',
  'Wind Onshore': '#87CEEB',
  'Wind Offshore': '#4682B4',
  'LFO': '#DC143C',
  'Co-Gen': '#FF6347',
  'Market': '#708090',
  'Gas': '#FF8C00',
  'CCGT': '#FFA500',
  'OCGT': '#FF7F50',
  'Biomass': '#228B22',
  'Geothermal': '#CD853F',

  // Storage
  'PSP': '#9370DB',
  'Battery Storage': '#BA55D3',
  'Planned Battery Storage': '#DDA0DD',
  'Planned PSP': '#E6A8F7',
  'Battery': '#BA55D3',
  'H2': '#ADD8E6',

  // Other
  'Load': '#000000',
  'Storage Discharge': '#FFA500',
  'Storage Charge': '#FFA500',
  'Other': '#D3D3D3',
  'Curtailment': '#FF4500'
};

export const getChartConfig = (analysisType) => {
  const configs = {
    capacity: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['value'],
      yAxisLabel: 'Capacity (MW)',
      title: 'Installed Capacity by Technology',
      colors: PYPSA_COLORS,
      supportsPie: true // This analysis type can also be shown as pie chart
    },
    dispatch: {
      type: 'stacked-area',
      xAxisKey: 'timestamp',
      dataKeys: [], // Will be populated dynamically from data
      yAxisLabel: 'Power (MW)',
      title: 'Power Dispatch',
      showLoad: true, // Special flag to show load line
      colors: PYPSA_COLORS
    },
    metrics: {
      type: 'donut',
      labelKey: 'name',
      valueKey: 'percentage',
      title: 'Renewable Share',
      colors: {
        'Renewable': '#10b981',
        'Non-Renewable': '#ef4444',
        ...PYPSA_COLORS
      }
    },
    storage: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['power_capacity', 'energy_capacity'],
      yAxisLabel: 'Capacity',
      title: 'Storage Capacity',
      colors: PYPSA_COLORS,
      supportsPie: true
    },
    emissions: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['value'],
      yAxisLabel: 'Emissions (tonnes CO2)',
      title: 'CO2 Emissions by Carrier',
      colors: PYPSA_COLORS,
      supportsPie: true
    },
    prices: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['value'],
      yAxisLabel: 'Cost',
      title: 'System Costs',
      colors: PYPSA_COLORS
    },
    network_flow: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['capacity', 'utilization'],
      yAxisLabel: 'MW / %',
      title: 'Network Lines',
      colors: PYPSA_COLORS
    },
    daily_profile: {
      type: 'stacked-area',
      xAxisKey: 'hour',
      dataKeys: [], // Will be populated dynamically
      yAxisLabel: 'Average Power (MW)',
      title: 'Average Daily Profile',
      colors: PYPSA_COLORS
    },
    duration_curve: {
      type: 'area',
      xAxisKey: 'duration_percent',
      dataKeys: ['power_mw'],
      yAxisLabel: 'Power (MW)',
      title: 'Load Duration Curve',
      colors: { 'power_mw': '#3b82f6' }
    },
    capacity_factor: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['cuf'],
      yAxisLabel: 'Capacity Utilization Factor',
      title: 'Capacity Utilization Factor by Technology',
      colors: PYPSA_COLORS
    },
    curtailment: {
      type: 'bar',
      xAxisKey: 'name',
      dataKeys: ['curtailment_mwh', 'curtailment_percent'],
      yAxisLabel: 'Curtailment',
      title: 'Renewable Curtailment',
      colors: PYPSA_COLORS
    },
    storage_soc: {
      type: 'area',
      xAxisKey: 'timestamp',
      dataKeys: [], // Will be populated dynamically
      yAxisLabel: 'State of Charge (MWh)',
      title: 'Storage State of Charge',
      colors: PYPSA_COLORS
    }
  };

  return configs[analysisType] || {
    type: 'bar',
    xAxisKey: 'name',
    dataKeys: ['value'],
    yAxisLabel: 'Value',
    title: 'Analysis',
    colors: PYPSA_COLORS
  };
};
