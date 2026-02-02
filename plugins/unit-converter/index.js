/**
 * Unit Converter - Embedded ForgeHook Plugin
 * Convert between units of length, weight, volume, temperature, and more
 */

// =============================================================================
// Conversion Tables
// =============================================================================

// Length conversions (base unit: meters)
const LENGTH_UNITS = {
  // Metric
  kilometer: { toBase: 1000, abbr: 'km', system: 'metric' },
  meter: { toBase: 1, abbr: 'm', system: 'metric' },
  centimeter: { toBase: 0.01, abbr: 'cm', system: 'metric' },
  millimeter: { toBase: 0.001, abbr: 'mm', system: 'metric' },
  micrometer: { toBase: 0.000001, abbr: 'µm', system: 'metric' },
  nanometer: { toBase: 0.000000001, abbr: 'nm', system: 'metric' },
  
  // Imperial/US
  mile: { toBase: 1609.344, abbr: 'mi', system: 'imperial' },
  yard: { toBase: 0.9144, abbr: 'yd', system: 'imperial' },
  foot: { toBase: 0.3048, abbr: 'ft', system: 'imperial' },
  inch: { toBase: 0.0254, abbr: 'in', system: 'imperial' },
  
  // Nautical
  nauticalMile: { toBase: 1852, abbr: 'nmi', system: 'nautical' },
  fathom: { toBase: 1.8288, abbr: 'ftm', system: 'nautical' },
};

// Weight/Mass conversions (base unit: kilograms)
const WEIGHT_UNITS = {
  // Metric
  tonne: { toBase: 1000, abbr: 't', system: 'metric' },
  kilogram: { toBase: 1, abbr: 'kg', system: 'metric' },
  gram: { toBase: 0.001, abbr: 'g', system: 'metric' },
  milligram: { toBase: 0.000001, abbr: 'mg', system: 'metric' },
  microgram: { toBase: 0.000000001, abbr: 'µg', system: 'metric' },
  
  // Imperial/US
  ton: { toBase: 907.18474, abbr: 'ton', system: 'imperial' }, // US ton (short ton)
  longTon: { toBase: 1016.0469088, abbr: 'long ton', system: 'imperial' }, // UK ton
  pound: { toBase: 0.45359237, abbr: 'lb', system: 'imperial' },
  ounce: { toBase: 0.028349523125, abbr: 'oz', system: 'imperial' },
  stone: { toBase: 6.35029318, abbr: 'st', system: 'imperial' },
  
  // Troy (precious metals)
  troyOunce: { toBase: 0.0311034768, abbr: 'oz t', system: 'troy' },
};

// Volume conversions (base unit: liters)
const VOLUME_UNITS = {
  // Metric
  cubicMeter: { toBase: 1000, abbr: 'm³', system: 'metric' },
  liter: { toBase: 1, abbr: 'L', system: 'metric' },
  milliliter: { toBase: 0.001, abbr: 'mL', system: 'metric' },
  cubicCentimeter: { toBase: 0.001, abbr: 'cm³', system: 'metric' },
  
  // Imperial
  gallon: { toBase: 3.785411784, abbr: 'gal', system: 'imperial' }, // US gallon
  quart: { toBase: 0.946352946, abbr: 'qt', system: 'imperial' }, // US quart
  pint: { toBase: 0.473176473, abbr: 'pt', system: 'imperial' }, // US pint
  cup: { toBase: 0.2365882365, abbr: 'cup', system: 'imperial' }, // US cup
  fluidOunce: { toBase: 0.0295735295625, abbr: 'fl oz', system: 'imperial' }, // US fl oz
  tablespoon: { toBase: 0.01478676478125, abbr: 'tbsp', system: 'imperial' },
  teaspoon: { toBase: 0.00492892159375, abbr: 'tsp', system: 'imperial' },
  
  // Imperial (UK)
  imperialGallon: { toBase: 4.54609, abbr: 'imp gal', system: 'imperial-uk' },
  imperialQuart: { toBase: 1.1365225, abbr: 'imp qt', system: 'imperial-uk' },
  imperialPint: { toBase: 0.56826125, abbr: 'imp pt', system: 'imperial-uk' },
  
  // Other
  cubicFoot: { toBase: 28.316846592, abbr: 'ft³', system: 'imperial' },
  cubicInch: { toBase: 0.016387064, abbr: 'in³', system: 'imperial' },
};

// Temperature conversions (special handling needed)
const TEMPERATURE_UNITS = {
  celsius: { abbr: '°C', system: 'metric' },
  fahrenheit: { abbr: '°F', system: 'imperial' },
  kelvin: { abbr: 'K', system: 'si' },
};

// Area conversions (base unit: square meters)
const AREA_UNITS = {
  squareKilometer: { toBase: 1000000, abbr: 'km²', system: 'metric' },
  hectare: { toBase: 10000, abbr: 'ha', system: 'metric' },
  squareMeter: { toBase: 1, abbr: 'm²', system: 'metric' },
  squareCentimeter: { toBase: 0.0001, abbr: 'cm²', system: 'metric' },
  
  squareMile: { toBase: 2589988.110336, abbr: 'mi²', system: 'imperial' },
  acre: { toBase: 4046.8564224, abbr: 'ac', system: 'imperial' },
  squareYard: { toBase: 0.83612736, abbr: 'yd²', system: 'imperial' },
  squareFoot: { toBase: 0.09290304, abbr: 'ft²', system: 'imperial' },
  squareInch: { toBase: 0.00064516, abbr: 'in²', system: 'imperial' },
};

// Speed conversions (base unit: meters per second)
const SPEED_UNITS = {
  meterPerSecond: { toBase: 1, abbr: 'm/s', system: 'si' },
  kilometerPerHour: { toBase: 0.277777778, abbr: 'km/h', system: 'metric' },
  milePerHour: { toBase: 0.44704, abbr: 'mph', system: 'imperial' },
  footPerSecond: { toBase: 0.3048, abbr: 'ft/s', system: 'imperial' },
  knot: { toBase: 0.514444444, abbr: 'kn', system: 'nautical' },
};

// Data storage conversions (base unit: bytes)
const DATA_UNITS = {
  byte: { toBase: 1, abbr: 'B', system: 'binary' },
  kilobyte: { toBase: 1024, abbr: 'KB', system: 'binary' },
  megabyte: { toBase: 1048576, abbr: 'MB', system: 'binary' },
  gigabyte: { toBase: 1073741824, abbr: 'GB', system: 'binary' },
  terabyte: { toBase: 1099511627776, abbr: 'TB', system: 'binary' },
  petabyte: { toBase: 1125899906842624, abbr: 'PB', system: 'binary' },
  
  // SI units (decimal)
  kilobyteSI: { toBase: 1000, abbr: 'kB', system: 'decimal' },
  megabyteSI: { toBase: 1000000, abbr: 'MB', system: 'decimal' },
  gigabyteSI: { toBase: 1000000000, abbr: 'GB', system: 'decimal' },
  terabyteSI: { toBase: 1000000000000, abbr: 'TB', system: 'decimal' },
  
  bit: { toBase: 0.125, abbr: 'b', system: 'binary' },
  kilobit: { toBase: 128, abbr: 'Kb', system: 'binary' },
  megabit: { toBase: 131072, abbr: 'Mb', system: 'binary' },
  gigabit: { toBase: 134217728, abbr: 'Gb', system: 'binary' },
};

// Time conversions (base unit: seconds)
const TIME_UNITS = {
  year: { toBase: 31536000, abbr: 'yr', system: 'common' }, // 365 days
  month: { toBase: 2592000, abbr: 'mo', system: 'common' }, // 30 days
  week: { toBase: 604800, abbr: 'wk', system: 'common' },
  day: { toBase: 86400, abbr: 'd', system: 'common' },
  hour: { toBase: 3600, abbr: 'hr', system: 'common' },
  minute: { toBase: 60, abbr: 'min', system: 'common' },
  second: { toBase: 1, abbr: 's', system: 'si' },
  millisecond: { toBase: 0.001, abbr: 'ms', system: 'si' },
  microsecond: { toBase: 0.000001, abbr: 'µs', system: 'si' },
  nanosecond: { toBase: 0.000000001, abbr: 'ns', system: 'si' },
};

// Unit category mapping
const UNIT_CATEGORIES = {
  length: LENGTH_UNITS,
  weight: WEIGHT_UNITS,
  mass: WEIGHT_UNITS,
  volume: VOLUME_UNITS,
  temperature: TEMPERATURE_UNITS,
  area: AREA_UNITS,
  speed: SPEED_UNITS,
  data: DATA_UNITS,
  time: TIME_UNITS,
};

// Unit name aliases
const UNIT_ALIASES = {
  // Length
  km: 'kilometer',
  m: 'meter',
  cm: 'centimeter',
  mm: 'millimeter',
  mi: 'mile',
  yd: 'yard',
  ft: 'foot',
  feet: 'foot',
  in: 'inch',
  inches: 'inch',
  nmi: 'nauticalMile',
  'nautical mile': 'nauticalMile',
  
  // Weight
  t: 'tonne',
  kg: 'kilogram',
  g: 'gram',
  mg: 'milligram',
  lb: 'pound',
  lbs: 'pound',
  oz: 'ounce',
  st: 'stone',
  
  // Volume
  l: 'liter',
  L: 'liter',
  ml: 'milliliter',
  mL: 'milliliter',
  gal: 'gallon',
  qt: 'quart',
  pt: 'pint',
  'fl oz': 'fluidOunce',
  tbsp: 'tablespoon',
  tsp: 'teaspoon',
  
  // Temperature
  c: 'celsius',
  C: 'celsius',
  f: 'fahrenheit',
  F: 'fahrenheit',
  k: 'kelvin',
  K: 'kelvin',
  
  // Speed
  'km/h': 'kilometerPerHour',
  kph: 'kilometerPerHour',
  mph: 'milePerHour',
  'm/s': 'meterPerSecond',
  kn: 'knot',
  knots: 'knot',
  
  // Data
  B: 'byte',
  KB: 'kilobyte',
  MB: 'megabyte',
  GB: 'gigabyte',
  TB: 'terabyte',
  PB: 'petabyte',
  
  // Time
  yr: 'year',
  years: 'year',
  mo: 'month',
  months: 'month',
  wk: 'week',
  weeks: 'week',
  d: 'day',
  days: 'day',
  hr: 'hour',
  hours: 'hour',
  min: 'minute',
  minutes: 'minute',
  s: 'second',
  sec: 'second',
  seconds: 'second',
  ms: 'millisecond',
};

// =============================================================================
// Helper Functions
// =============================================================================

// Resolve unit name from aliases
function resolveUnit(unitName) {
  if (!unitName) return null;
  const normalized = unitName.trim().toLowerCase();
  
  // Check aliases first
  if (UNIT_ALIASES[unitName]) return UNIT_ALIASES[unitName];
  if (UNIT_ALIASES[normalized]) return UNIT_ALIASES[normalized];
  
  // Try to find in unit categories
  for (const units of Object.values(UNIT_CATEGORIES)) {
    if (units[unitName]) return unitName;
    if (units[normalized]) return normalized;
    
    // Try case-insensitive match
    for (const key of Object.keys(units)) {
      if (key.toLowerCase() === normalized) return key;
    }
  }
  
  return null;
}

// Find category for a unit
function findCategory(unitName) {
  const resolved = resolveUnit(unitName);
  if (!resolved) return null;
  
  for (const [category, units] of Object.entries(UNIT_CATEGORIES)) {
    if (units[resolved]) return category;
  }
  return null;
}

// Temperature conversion helpers
function convertTemperature(value, fromUnit, toUnit) {
  // Convert to Celsius first
  let celsius;
  if (fromUnit === 'celsius') {
    celsius = value;
  } else if (fromUnit === 'fahrenheit') {
    celsius = (value - 32) * 5 / 9;
  } else if (fromUnit === 'kelvin') {
    celsius = value - 273.15;
  }
  
  // Convert from Celsius to target
  if (toUnit === 'celsius') {
    return celsius;
  } else if (toUnit === 'fahrenheit') {
    return celsius * 9 / 5 + 32;
  } else if (toUnit === 'kelvin') {
    return celsius + 273.15;
  }
  
  return null;
}

// Generic conversion using base unit
function convertValue(value, fromUnit, toUnit, unitTable) {
  const from = unitTable[fromUnit];
  const to = unitTable[toUnit];
  
  if (!from || !to) return null;
  
  // Convert to base unit, then to target
  const baseValue = value * from.toBase;
  return baseValue / to.toBase;
}

// Format number with appropriate precision
function formatNumber(num, precision = 6) {
  if (Math.abs(num) < 0.0001 || Math.abs(num) >= 1000000) {
    return num.toExponential(precision);
  }
  
  // Remove trailing zeros
  const fixed = num.toFixed(precision);
  return parseFloat(fixed).toString();
}

// =============================================================================
// Public API Functions
// =============================================================================

/**
 * Convert a value from one unit to another
 * @param {Object} input - { value, from, to }
 */
function convert(input, config = {}) {
  let value, fromUnit, toUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.source;
    toUnit = input.to || input.toUnit || input.target;
  } else {
    value = parseFloat(input);
    fromUnit = config.from;
    toUnit = config.to;
  }
  
  if (isNaN(value)) return { error: 'Invalid value' };
  
  const resolvedFrom = resolveUnit(fromUnit);
  const resolvedTo = resolveUnit(toUnit);
  
  if (!resolvedFrom) return { error: `Unknown unit: ${fromUnit}` };
  if (!resolvedTo) return { error: `Unknown unit: ${toUnit}` };
  
  const fromCategory = findCategory(resolvedFrom);
  const toCategory = findCategory(resolvedTo);
  
  if (fromCategory !== toCategory) {
    return { error: `Cannot convert between ${fromCategory} and ${toCategory}` };
  }
  
  let result;
  if (fromCategory === 'temperature') {
    result = convertTemperature(value, resolvedFrom, resolvedTo);
  } else {
    const unitTable = UNIT_CATEGORIES[fromCategory];
    result = convertValue(value, resolvedFrom, resolvedTo, unitTable);
  }
  
  if (result === null) {
    return { error: 'Conversion failed' };
  }
  
  const unitTable = UNIT_CATEGORIES[fromCategory];
  
  return {
    input: {
      value,
      unit: resolvedFrom,
      abbr: unitTable[resolvedFrom]?.abbr || resolvedFrom,
    },
    result: {
      value: result,
      formatted: formatNumber(result),
      unit: resolvedTo,
      abbr: unitTable[resolvedTo]?.abbr || resolvedTo,
    },
    category: fromCategory,
  };
}

/**
 * Convert a value to multiple units
 * @param {Object} input - { value, from, to: string[] }
 */
function convertMultiple(input, config = {}) {
  let value, fromUnit, toUnits;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.source;
    toUnits = input.to || input.toUnits || input.targets;
  } else {
    value = parseFloat(input);
    fromUnit = config.from;
    toUnits = config.to;
  }
  
  if (isNaN(value)) return { error: 'Invalid value' };
  
  const resolvedFrom = resolveUnit(fromUnit);
  if (!resolvedFrom) return { error: `Unknown unit: ${fromUnit}` };
  
  const fromCategory = findCategory(resolvedFrom);
  const unitTable = UNIT_CATEGORIES[fromCategory];
  
  const targets = Array.isArray(toUnits) ? toUnits : [toUnits].filter(Boolean);
  const results = [];
  
  for (const target of targets) {
    const result = convert({ value, from: fromUnit, to: target });
    if (!result.error) {
      results.push(result.result);
    }
  }
  
  return {
    input: {
      value,
      unit: resolvedFrom,
      abbr: unitTable[resolvedFrom]?.abbr || resolvedFrom,
    },
    category: fromCategory,
    conversions: results,
  };
}

/**
 * Convert a length to common units
 * @param {Object} input - { value, from }
 */
function convertLength(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'meter';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'meter';
  }
  
  const targets = ['kilometer', 'meter', 'centimeter', 'millimeter', 'mile', 'yard', 'foot', 'inch'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * Convert a weight to common units
 * @param {Object} input - { value, from }
 */
function convertWeight(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'kilogram';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'kilogram';
  }
  
  const targets = ['tonne', 'kilogram', 'gram', 'milligram', 'pound', 'ounce', 'stone'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * Convert a volume to common units
 * @param {Object} input - { value, from }
 */
function convertVolume(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'liter';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'liter';
  }
  
  const targets = ['liter', 'milliliter', 'gallon', 'quart', 'pint', 'cup', 'fluidOunce'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * Convert a temperature to other scales
 * @param {Object} input - { value, from }
 */
function convertTemperatureAll(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'celsius';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'celsius';
  }
  
  const targets = ['celsius', 'fahrenheit', 'kelvin'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * Convert a speed to common units
 * @param {Object} input - { value, from }
 */
function convertSpeed(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'kilometerPerHour';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'kilometerPerHour';
  }
  
  const targets = ['kilometerPerHour', 'milePerHour', 'meterPerSecond', 'knot'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * Convert data size to common units
 * @param {Object} input - { value, from }
 */
function convertData(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'megabyte';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'megabyte';
  }
  
  const targets = ['byte', 'kilobyte', 'megabyte', 'gigabyte', 'terabyte'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * Convert area to common units
 * @param {Object} input - { value, from }
 */
function convertArea(input, config = {}) {
  let value, fromUnit;
  
  if (typeof input === 'object') {
    value = input.value || input.amount || input.number;
    fromUnit = input.from || input.fromUnit || input.unit || 'squareMeter';
  } else {
    value = parseFloat(input);
    fromUnit = config.from || 'squareMeter';
  }
  
  const targets = ['squareKilometer', 'hectare', 'squareMeter', 'squareMile', 'acre', 'squareFoot'];
  return convertMultiple({ value, from: fromUnit, to: targets });
}

/**
 * List all available units for a category
 * @param {Object} input - { category }
 */
function listUnits(input, config = {}) {
  let category;
  
  if (typeof input === 'object') {
    category = input.category || input.type;
  } else if (typeof input === 'string') {
    category = input;
  }
  
  if (category) {
    const normalized = category.toLowerCase();
    const unitTable = UNIT_CATEGORIES[normalized];
    
    if (!unitTable) {
      return { 
        error: `Unknown category: ${category}`,
        availableCategories: Object.keys(UNIT_CATEGORIES),
      };
    }
    
    const units = Object.entries(unitTable).map(([name, data]) => ({
      name,
      abbr: data.abbr,
      system: data.system,
    }));
    
    return {
      category: normalized,
      units,
    };
  }
  
  // List all categories and their unit counts
  const categories = Object.entries(UNIT_CATEGORIES).map(([name, units]) => ({
    name,
    unitCount: Object.keys(units).length,
  }));
  
  return { categories };
}

/**
 * Parse a unit string like "5 miles" or "100kg"
 * @param {string} input - String containing value and unit
 */
function parseUnit(input, config = {}) {
  let str;
  
  if (typeof input === 'object') {
    str = input.text || input.value || input.input;
  } else {
    str = String(input);
  }
  
  // Try to match patterns like "5 miles", "100kg", "3.14 m", etc.
  const match = str.match(/^([\d.,]+)\s*(.+)$/);
  
  if (!match) {
    return { error: 'Could not parse input. Expected format: "5 miles" or "100kg"' };
  }
  
  const value = parseFloat(match[1].replace(',', ''));
  const unitStr = match[2].trim();
  const resolved = resolveUnit(unitStr);
  
  if (isNaN(value)) {
    return { error: `Invalid number: ${match[1]}` };
  }
  
  if (!resolved) {
    return { error: `Unknown unit: ${unitStr}` };
  }
  
  const category = findCategory(resolved);
  const unitTable = UNIT_CATEGORIES[category];
  
  return {
    value,
    unit: resolved,
    abbr: unitTable[resolved]?.abbr || resolved,
    category,
  };
}

module.exports = {
  convert,
  convertMultiple,
  convertLength,
  convertWeight,
  convertVolume,
  convertTemperature: convertTemperatureAll,
  convertSpeed,
  convertData,
  convertArea,
  listUnits,
  parseUnit,
};
