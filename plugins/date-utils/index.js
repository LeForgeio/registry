/**
 * Date Utilities - Embedded ForgeHook Plugin
 * Lightweight date manipulation and formatting utilities
 */

// Parse input to Date object
function parseDate(input) {
  if (input instanceof Date) return input;
  if (typeof input === 'number') return new Date(input);
  if (typeof input === 'string') return new Date(input);
  if (typeof input === 'object') {
    const value = input.date || input.value || input.timestamp;
    if (value) return parseDate(value);
  }
  return new Date();
}

// Get current date/time
function now(input, config = {}) {
  const format = (typeof input === 'object' ? input.format : input) || 'iso';
  const date = new Date();
  
  if (format === 'unix') return Math.floor(date.getTime() / 1000);
  if (format === 'ms' || format === 'milliseconds') return date.getTime();
  return date.toISOString();
}

// Format date with pattern
function format(input, config = {}) {
  let date, pattern;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    pattern = input.format || input.pattern || 'YYYY-MM-DD';
  } else {
    date = parseDate(input);
    pattern = config.format || 'YYYY-MM-DD';
  }
  
  if (!isValid({ date })) return 'Invalid Date';
  
  const pad = (n, width = 2) => String(n).padStart(width, '0');
  
  const tokens = {
    'YYYY': date.getFullYear(),
    'YY': String(date.getFullYear()).slice(-2),
    'MM': pad(date.getMonth() + 1),
    'M': date.getMonth() + 1,
    'DD': pad(date.getDate()),
    'D': date.getDate(),
    'HH': pad(date.getHours()),
    'H': date.getHours(),
    'hh': pad(date.getHours() % 12 || 12),
    'h': date.getHours() % 12 || 12,
    'mm': pad(date.getMinutes()),
    'm': date.getMinutes(),
    'ss': pad(date.getSeconds()),
    's': date.getSeconds(),
    'SSS': pad(date.getMilliseconds(), 3),
    'A': date.getHours() < 12 ? 'AM' : 'PM',
    'a': date.getHours() < 12 ? 'am' : 'pm',
    'ddd': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()],
    'dddd': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][date.getDay()],
    'MMM': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][date.getMonth()],
    'MMMM': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][date.getMonth()]
  };
  
  // Sort by length descending to match longer tokens first
  const sortedTokens = Object.keys(tokens).sort((a, b) => b.length - a.length);
  let result = pattern;
  
  for (const token of sortedTokens) {
    result = result.replace(new RegExp(token, 'g'), tokens[token]);
  }
  
  return result;
}

// Parse date from string with format
function parse(input, config = {}) {
  let dateStr, pattern;
  
  if (typeof input === 'object') {
    dateStr = input.date || input.value || input.text;
    pattern = input.format || input.pattern;
  } else {
    dateStr = input;
    pattern = config.format;
  }
  
  // If no pattern, try native Date parsing
  if (!pattern) {
    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? null : date.toISOString();
  }
  
  // Simple pattern-based parsing
  const patternMap = {
    YYYY: { regex: '(\\d{4})', setter: 'setFullYear' },
    MM: { regex: '(\\d{2})', setter: 'setMonth', offset: -1 },
    DD: { regex: '(\\d{2})', setter: 'setDate' },
    HH: { regex: '(\\d{2})', setter: 'setHours' },
    mm: { regex: '(\\d{2})', setter: 'setMinutes' },
    ss: { regex: '(\\d{2})', setter: 'setSeconds' }
  };
  
  let regexStr = pattern;
  const setters = [];
  
  for (const [token, info] of Object.entries(patternMap)) {
    if (pattern.includes(token)) {
      regexStr = regexStr.replace(token, info.regex);
      setters.push({ ...info, token });
    }
  }
  
  const match = dateStr.match(new RegExp(`^${regexStr}$`));
  if (!match) return null;
  
  const date = new Date(0);
  date.setFullYear(1970, 0, 1);
  date.setHours(0, 0, 0, 0);
  
  let i = 1;
  for (const setter of setters) {
    const value = parseInt(match[i++], 10) + (setter.offset || 0);
    date[setter.setter](value);
  }
  
  return date.toISOString();
}

// Convert to ISO string
function toISO(input) {
  const date = parseDate(input);
  return isValid({ date }) ? date.toISOString() : 'Invalid Date';
}

// Convert to Unix timestamp (seconds)
function toUnix(input) {
  const date = parseDate(input);
  return isValid({ date }) ? Math.floor(date.getTime() / 1000) : null;
}

// Create date from Unix timestamp
function fromUnix(input) {
  const timestamp = typeof input === 'object' ? input.timestamp || input.value : input;
  const date = new Date(timestamp * 1000);
  return isValid({ date }) ? date.toISOString() : 'Invalid Date';
}

// Get relative time string
function relativeTime(input, config = {}) {
  let date, baseDate;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    baseDate = input.base ? parseDate(input.base) : new Date();
  } else {
    date = parseDate(input);
    baseDate = new Date();
  }
  
  if (!isValid({ date })) return 'Invalid Date';
  
  const diffMs = date.getTime() - baseDate.getTime();
  const absDiff = Math.abs(diffMs);
  const isPast = diffMs < 0;
  
  const intervals = [
    { unit: 'year', ms: 365 * 24 * 60 * 60 * 1000 },
    { unit: 'month', ms: 30 * 24 * 60 * 60 * 1000 },
    { unit: 'week', ms: 7 * 24 * 60 * 60 * 1000 },
    { unit: 'day', ms: 24 * 60 * 60 * 1000 },
    { unit: 'hour', ms: 60 * 60 * 1000 },
    { unit: 'minute', ms: 60 * 1000 },
    { unit: 'second', ms: 1000 }
  ];
  
  for (const interval of intervals) {
    const count = Math.floor(absDiff / interval.ms);
    if (count >= 1) {
      const plural = count === 1 ? '' : 's';
      return isPast 
        ? `${count} ${interval.unit}${plural} ago`
        : `in ${count} ${interval.unit}${plural}`;
    }
  }
  
  return 'just now';
}

// Add days to date
function addDays(input, config = {}) {
  let date, days;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    days = input.days || input.amount || 0;
  } else {
    date = parseDate(input);
    days = config.days || 0;
  }
  
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result.toISOString();
}

// Add hours to date
function addHours(input, config = {}) {
  let date, hours;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    hours = input.hours || input.amount || 0;
  } else {
    date = parseDate(input);
    hours = config.hours || 0;
  }
  
  const result = new Date(date);
  result.setHours(result.getHours() + hours);
  return result.toISOString();
}

// Add minutes to date
function addMinutes(input, config = {}) {
  let date, minutes;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    minutes = input.minutes || input.amount || 0;
  } else {
    date = parseDate(input);
    minutes = config.minutes || 0;
  }
  
  const result = new Date(date);
  result.setMinutes(result.getMinutes() + minutes);
  return result.toISOString();
}

// Add months to date
function addMonths(input, config = {}) {
  let date, months;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    months = input.months || input.amount || 0;
  } else {
    date = parseDate(input);
    months = config.months || 0;
  }
  
  const result = new Date(date);
  result.setMonth(result.getMonth() + months);
  return result.toISOString();
}

// Add years to date
function addYears(input, config = {}) {
  let date, years;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    years = input.years || input.amount || 0;
  } else {
    date = parseDate(input);
    years = config.years || 0;
  }
  
  const result = new Date(date);
  result.setFullYear(result.getFullYear() + years);
  return result.toISOString();
}

// Calculate difference between dates
function diff(input, config = {}) {
  let date1, date2, unit;
  
  if (typeof input === 'object') {
    date1 = parseDate(input.date1 || input.from || input.start);
    date2 = parseDate(input.date2 || input.to || input.end || new Date());
    unit = input.unit || 'days';
  } else {
    date1 = parseDate(input);
    date2 = new Date();
    unit = config.unit || 'days';
  }
  
  const diffMs = date2.getTime() - date1.getTime();
  
  const conversions = {
    milliseconds: 1,
    seconds: 1000,
    minutes: 60 * 1000,
    hours: 60 * 60 * 1000,
    days: 24 * 60 * 60 * 1000,
    weeks: 7 * 24 * 60 * 60 * 1000,
    months: 30 * 24 * 60 * 60 * 1000,
    years: 365 * 24 * 60 * 60 * 1000
  };
  
  const divisor = conversions[unit] || conversions.days;
  return Math.floor(diffMs / divisor);
}

// Get start of period
function startOf(input, config = {}) {
  let date, unit;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    unit = input.unit || 'day';
  } else {
    date = parseDate(input);
    unit = config.unit || 'day';
  }
  
  const result = new Date(date);
  
  switch (unit) {
    case 'year':
      result.setMonth(0, 1);
      result.setHours(0, 0, 0, 0);
      break;
    case 'month':
      result.setDate(1);
      result.setHours(0, 0, 0, 0);
      break;
    case 'week':
      const day = result.getDay();
      result.setDate(result.getDate() - day);
      result.setHours(0, 0, 0, 0);
      break;
    case 'day':
      result.setHours(0, 0, 0, 0);
      break;
    case 'hour':
      result.setMinutes(0, 0, 0);
      break;
    case 'minute':
      result.setSeconds(0, 0);
      break;
  }
  
  return result.toISOString();
}

// Get end of period
function endOf(input, config = {}) {
  let date, unit;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    unit = input.unit || 'day';
  } else {
    date = parseDate(input);
    unit = config.unit || 'day';
  }
  
  const result = new Date(date);
  
  switch (unit) {
    case 'year':
      result.setMonth(11, 31);
      result.setHours(23, 59, 59, 999);
      break;
    case 'month':
      result.setMonth(result.getMonth() + 1, 0);
      result.setHours(23, 59, 59, 999);
      break;
    case 'week':
      const day = result.getDay();
      result.setDate(result.getDate() + (6 - day));
      result.setHours(23, 59, 59, 999);
      break;
    case 'day':
      result.setHours(23, 59, 59, 999);
      break;
    case 'hour':
      result.setMinutes(59, 59, 999);
      break;
    case 'minute':
      result.setSeconds(59, 999);
      break;
  }
  
  return result.toISOString();
}

// Check if date is valid
function isValid(input) {
  const date = parseDate(input);
  return date instanceof Date && !isNaN(date.getTime());
}

// Check if date1 is before date2
function isBefore(input, config = {}) {
  let date1, date2;
  
  if (typeof input === 'object') {
    date1 = parseDate(input.date || input.date1 || input.value);
    date2 = parseDate(input.compare || input.date2 || config.compare);
  } else {
    date1 = parseDate(input);
    date2 = parseDate(config.compare);
  }
  
  return date1.getTime() < date2.getTime();
}

// Check if date1 is after date2
function isAfter(input, config = {}) {
  let date1, date2;
  
  if (typeof input === 'object') {
    date1 = parseDate(input.date || input.date1 || input.value);
    date2 = parseDate(input.compare || input.date2 || config.compare);
  } else {
    date1 = parseDate(input);
    date2 = parseDate(config.compare);
  }
  
  return date1.getTime() > date2.getTime();
}

// Check if date is between two dates
function isBetween(input, config = {}) {
  let date, start, end;
  
  if (typeof input === 'object') {
    date = parseDate(input.date || input.value);
    start = parseDate(input.start);
    end = parseDate(input.end);
  } else {
    date = parseDate(input);
    start = parseDate(config.start);
    end = parseDate(config.end);
  }
  
  const time = date.getTime();
  return time >= start.getTime() && time <= end.getTime();
}

// Get day of week (0 = Sunday, 6 = Saturday)
function getWeekday(input, config = {}) {
  let date, format;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    date = parseDate(input.date || input.value);
    format = input.format || 'number';
  } else {
    date = parseDate(input);
    format = config.format || 'number';
  }
  
  const day = date.getDay();
  
  if (format === 'short') {
    return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day];
  }
  if (format === 'long') {
    return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][day];
  }
  
  return day;
}

// Get number of days in month
function getDaysInMonth(input) {
  let date;
  
  if (typeof input === 'object' && !(input instanceof Date)) {
    if (input.year !== undefined && input.month !== undefined) {
      date = new Date(input.year, input.month, 0);
      return date.getDate();
    }
    date = parseDate(input.date || input.value);
  } else {
    date = parseDate(input);
  }
  
  // Get last day of the month
  const result = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  return result.getDate();
}

module.exports = {
  format,
  parse,
  now,
  toISO,
  toUnix,
  fromUnix,
  relativeTime,
  addDays,
  addHours,
  addMinutes,
  addMonths,
  addYears,
  diff,
  startOf,
  endOf,
  isValid,
  isBefore,
  isAfter,
  isBetween,
  getWeekday,
  getDaysInMonth
};
