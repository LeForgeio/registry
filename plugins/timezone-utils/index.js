/**
 * Timezone Utilities - Embedded ForgeHook Plugin
 * Convert times across multiple timezones
 */

// Common timezone offsets (IANA timezone -> offset in minutes from UTC)
// Note: These are standard offsets. DST is handled separately.
const TIMEZONE_DATA = {
  // Americas
  'America/New_York': { offset: -300, name: 'Eastern Time', abbr: 'ET' },
  'America/Chicago': { offset: -360, name: 'Central Time', abbr: 'CT' },
  'America/Denver': { offset: -420, name: 'Mountain Time', abbr: 'MT' },
  'America/Los_Angeles': { offset: -480, name: 'Pacific Time', abbr: 'PT' },
  'America/Anchorage': { offset: -540, name: 'Alaska Time', abbr: 'AKT' },
  'America/Phoenix': { offset: -420, name: 'Arizona Time', abbr: 'MST' },
  'America/Toronto': { offset: -300, name: 'Eastern Time', abbr: 'ET' },
  'America/Vancouver': { offset: -480, name: 'Pacific Time', abbr: 'PT' },
  'America/Mexico_City': { offset: -360, name: 'Central Time', abbr: 'CST' },
  'America/Sao_Paulo': { offset: -180, name: 'Brasilia Time', abbr: 'BRT' },
  'America/Buenos_Aires': { offset: -180, name: 'Argentina Time', abbr: 'ART' },
  
  // Europe
  'Europe/London': { offset: 0, name: 'Greenwich Mean Time', abbr: 'GMT' },
  'Europe/Paris': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Berlin': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Rome': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Madrid': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Amsterdam': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Brussels': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Zurich': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Vienna': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Stockholm': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Oslo': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Copenhagen': { offset: 60, name: 'Central European Time', abbr: 'CET' },
  'Europe/Helsinki': { offset: 120, name: 'Eastern European Time', abbr: 'EET' },
  'Europe/Athens': { offset: 120, name: 'Eastern European Time', abbr: 'EET' },
  'Europe/Moscow': { offset: 180, name: 'Moscow Time', abbr: 'MSK' },
  'Europe/Istanbul': { offset: 180, name: 'Turkey Time', abbr: 'TRT' },
  
  // Asia
  'Asia/Dubai': { offset: 240, name: 'Gulf Standard Time', abbr: 'GST' },
  'Asia/Kolkata': { offset: 330, name: 'India Standard Time', abbr: 'IST' },
  'Asia/Mumbai': { offset: 330, name: 'India Standard Time', abbr: 'IST' },
  'Asia/Bangkok': { offset: 420, name: 'Indochina Time', abbr: 'ICT' },
  'Asia/Singapore': { offset: 480, name: 'Singapore Time', abbr: 'SGT' },
  'Asia/Hong_Kong': { offset: 480, name: 'Hong Kong Time', abbr: 'HKT' },
  'Asia/Shanghai': { offset: 480, name: 'China Standard Time', abbr: 'CST' },
  'Asia/Tokyo': { offset: 540, name: 'Japan Standard Time', abbr: 'JST' },
  'Asia/Seoul': { offset: 540, name: 'Korea Standard Time', abbr: 'KST' },
  'Asia/Jakarta': { offset: 420, name: 'Western Indonesia Time', abbr: 'WIB' },
  'Asia/Manila': { offset: 480, name: 'Philippine Time', abbr: 'PHT' },
  'Asia/Taipei': { offset: 480, name: 'Taipei Time', abbr: 'CST' },
  'Asia/Kuala_Lumpur': { offset: 480, name: 'Malaysia Time', abbr: 'MYT' },
  'Asia/Jerusalem': { offset: 120, name: 'Israel Standard Time', abbr: 'IST' },
  'Asia/Riyadh': { offset: 180, name: 'Arabia Standard Time', abbr: 'AST' },
  
  // Pacific / Oceania
  'Pacific/Auckland': { offset: 720, name: 'New Zealand Time', abbr: 'NZST' },
  'Pacific/Fiji': { offset: 720, name: 'Fiji Time', abbr: 'FJT' },
  'Pacific/Honolulu': { offset: -600, name: 'Hawaii Time', abbr: 'HST' },
  'Australia/Sydney': { offset: 600, name: 'Australian Eastern Time', abbr: 'AEST' },
  'Australia/Melbourne': { offset: 600, name: 'Australian Eastern Time', abbr: 'AEST' },
  'Australia/Brisbane': { offset: 600, name: 'Australian Eastern Time', abbr: 'AEST' },
  'Australia/Perth': { offset: 480, name: 'Australian Western Time', abbr: 'AWST' },
  'Australia/Adelaide': { offset: 570, name: 'Australian Central Time', abbr: 'ACST' },
  
  // Africa
  'Africa/Cairo': { offset: 120, name: 'Eastern European Time', abbr: 'EET' },
  'Africa/Johannesburg': { offset: 120, name: 'South Africa Time', abbr: 'SAST' },
  'Africa/Lagos': { offset: 60, name: 'West Africa Time', abbr: 'WAT' },
  'Africa/Nairobi': { offset: 180, name: 'East Africa Time', abbr: 'EAT' },
  
  // UTC
  'UTC': { offset: 0, name: 'Coordinated Universal Time', abbr: 'UTC' },
};

// City aliases to IANA timezones
const CITY_ALIASES = {
  // Major cities
  'new york': 'America/New_York',
  'nyc': 'America/New_York',
  'los angeles': 'America/Los_Angeles',
  'la': 'America/Los_Angeles',
  'chicago': 'America/Chicago',
  'seattle': 'America/Los_Angeles',
  'san francisco': 'America/Los_Angeles',
  'sf': 'America/Los_Angeles',
  'boston': 'America/New_York',
  'miami': 'America/New_York',
  'denver': 'America/Denver',
  'phoenix': 'America/Phoenix',
  'dallas': 'America/Chicago',
  'houston': 'America/Chicago',
  'atlanta': 'America/New_York',
  
  'london': 'Europe/London',
  'paris': 'Europe/Paris',
  'berlin': 'Europe/Berlin',
  'rome': 'Europe/Rome',
  'madrid': 'Europe/Madrid',
  'amsterdam': 'Europe/Amsterdam',
  'brussels': 'Europe/Brussels',
  'zurich': 'Europe/Zurich',
  'vienna': 'Europe/Vienna',
  'stockholm': 'Europe/Stockholm',
  'oslo': 'Europe/Oslo',
  'copenhagen': 'Europe/Copenhagen',
  'helsinki': 'Europe/Helsinki',
  'athens': 'Europe/Athens',
  'moscow': 'Europe/Moscow',
  'istanbul': 'Europe/Istanbul',
  
  'dubai': 'Asia/Dubai',
  'mumbai': 'Asia/Mumbai',
  'delhi': 'Asia/Kolkata',
  'bangalore': 'Asia/Kolkata',
  'bangkok': 'Asia/Bangkok',
  'singapore': 'Asia/Singapore',
  'hong kong': 'Asia/Hong_Kong',
  'shanghai': 'Asia/Shanghai',
  'beijing': 'Asia/Shanghai',
  'tokyo': 'Asia/Tokyo',
  'seoul': 'Asia/Seoul',
  'jakarta': 'Asia/Jakarta',
  'manila': 'Asia/Manila',
  'taipei': 'Asia/Taipei',
  'kuala lumpur': 'Asia/Kuala_Lumpur',
  'jerusalem': 'Asia/Jerusalem',
  'tel aviv': 'Asia/Jerusalem',
  'riyadh': 'Asia/Riyadh',
  
  'sydney': 'Australia/Sydney',
  'melbourne': 'Australia/Melbourne',
  'brisbane': 'Australia/Brisbane',
  'perth': 'Australia/Perth',
  'adelaide': 'Australia/Adelaide',
  'auckland': 'Pacific/Auckland',
  'honolulu': 'Pacific/Honolulu',
  'hawaii': 'Pacific/Honolulu',
  
  'cairo': 'Africa/Cairo',
  'johannesburg': 'Africa/Johannesburg',
  'lagos': 'Africa/Lagos',
  'nairobi': 'Africa/Nairobi',
  
  'toronto': 'America/Toronto',
  'vancouver': 'America/Vancouver',
  'mexico city': 'America/Mexico_City',
  'sao paulo': 'America/Sao_Paulo',
  'buenos aires': 'America/Buenos_Aires',
};

// Resolve timezone from various input formats
function resolveTimezone(tz) {
  if (!tz) return null;
  
  const normalized = tz.trim();
  
  // Direct IANA match
  if (TIMEZONE_DATA[normalized]) {
    return normalized;
  }
  
  // City alias (case insensitive)
  const lower = normalized.toLowerCase();
  if (CITY_ALIASES[lower]) {
    return CITY_ALIASES[lower];
  }
  
  // Try matching partial IANA (e.g., "Sydney" -> "Australia/Sydney")
  for (const tzName of Object.keys(TIMEZONE_DATA)) {
    if (tzName.toLowerCase().includes(lower)) {
      return tzName;
    }
  }
  
  return null;
}

// Parse time input (can be Date, ISO string, time string like "2pm", "14:30", etc.)
function parseTimeInput(input, sourceTimezone) {
  if (!input) return new Date();
  
  if (input instanceof Date) return input;
  
  if (typeof input === 'number') {
    return new Date(input);
  }
  
  if (typeof input === 'string') {
    // Try ISO format first
    const isoDate = new Date(input);
    if (!isNaN(isoDate.getTime()) && input.includes('-')) {
      return isoDate;
    }
    
    // Parse time-only formats like "2pm", "14:30", "2:30pm"
    const timeMatch = input.match(/^(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)?$/i);
    if (timeMatch) {
      let hours = parseInt(timeMatch[1], 10);
      const minutes = parseInt(timeMatch[2] || '0', 10);
      const seconds = parseInt(timeMatch[3] || '0', 10);
      const meridiem = timeMatch[4]?.toLowerCase();
      
      if (meridiem === 'pm' && hours < 12) hours += 12;
      if (meridiem === 'am' && hours === 12) hours = 0;
      
      const now = new Date();
      const result = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes, seconds);
      
      // Adjust for source timezone if provided
      if (sourceTimezone) {
        const tzData = TIMEZONE_DATA[sourceTimezone];
        if (tzData) {
          const localOffset = now.getTimezoneOffset();
          const diff = tzData.offset + localOffset;
          result.setMinutes(result.getMinutes() - diff);
        }
      }
      
      return result;
    }
    
    // Try parsing as regular date string
    const parsed = new Date(input);
    if (!isNaN(parsed.getTime())) {
      return parsed;
    }
  }
  
  return new Date();
}

// Format time for display
function formatTime(date, options = {}) {
  const { format = '12h', includeSeconds = false, includeDate = false } = options;
  
  const hours24 = date.getUTCHours();
  const hours12 = hours24 % 12 || 12;
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  const seconds = String(date.getUTCSeconds()).padStart(2, '0');
  const meridiem = hours24 < 12 ? 'AM' : 'PM';
  
  let timeStr = format === '24h' 
    ? `${String(hours24).padStart(2, '0')}:${minutes}`
    : `${hours12}:${minutes} ${meridiem}`;
  
  if (includeSeconds) {
    timeStr = format === '24h'
      ? `${String(hours24).padStart(2, '0')}:${minutes}:${seconds}`
      : `${hours12}:${minutes}:${seconds} ${meridiem}`;
  }
  
  if (includeDate) {
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    timeStr = `${year}-${month}-${day} ${timeStr}`;
  }
  
  return timeStr;
}

// Convert time to a specific timezone
function convertToTimezone(date, timezone) {
  const tzData = TIMEZONE_DATA[timezone];
  if (!tzData) return null;
  
  // Create a new date adjusted for the target timezone
  const utcTime = date.getTime();
  const targetTime = new Date(utcTime + tzData.offset * 60 * 1000);
  
  return {
    timezone,
    name: tzData.name,
    abbr: tzData.abbr,
    offset: tzData.offset,
    offsetString: formatOffset(tzData.offset),
    iso: targetTime.toISOString(),
    time: formatTime(targetTime),
    time24h: formatTime(targetTime, { format: '24h' }),
    dateTime: formatTime(targetTime, { includeDate: true }),
    dateTime24h: formatTime(targetTime, { format: '24h', includeDate: true }),
  };
}

// Format offset as string like "+05:30" or "-08:00"
function formatOffset(minutes) {
  const sign = minutes >= 0 ? '+' : '-';
  const absMinutes = Math.abs(minutes);
  const hours = Math.floor(absMinutes / 60);
  const mins = absMinutes % 60;
  return `${sign}${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
}

// =============================================================================
// Public API Functions
// =============================================================================

/**
 * Convert a time to multiple timezones
 * @param {Object} input - { time, from, to: string[] }
 * @returns {Object} - Array of converted times
 */
function convert(input, config = {}) {
  let time, fromTz, toTzList;
  
  if (typeof input === 'object') {
    time = input.time || input.dateTime || input.value;
    fromTz = input.from || input.fromTimezone || input.source;
    toTzList = input.to || input.toTimezones || input.targets || config.to;
  } else {
    time = input;
    fromTz = config.from;
    toTzList = config.to;
  }
  
  // Resolve source timezone
  const sourceTimezone = fromTz ? resolveTimezone(fromTz) : null;
  
  // Parse the input time
  const date = parseTimeInput(time, sourceTimezone);
  
  // If we have a source timezone, adjust to UTC first
  let utcDate = date;
  if (sourceTimezone) {
    const tzData = TIMEZONE_DATA[sourceTimezone];
    if (tzData) {
      utcDate = new Date(date.getTime() - tzData.offset * 60 * 1000);
    }
  }
  
  // Handle single timezone or array
  const timezones = Array.isArray(toTzList) ? toTzList : [toTzList].filter(Boolean);
  
  if (timezones.length === 0) {
    // Default to common business timezones
    timezones.push('America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo');
  }
  
  const results = [];
  for (const tz of timezones) {
    const resolved = resolveTimezone(tz);
    if (resolved) {
      const converted = convertToTimezone(utcDate, resolved);
      if (converted) {
        results.push(converted);
      }
    }
  }
  
  return {
    input: {
      time: time || 'now',
      from: sourceTimezone || 'local',
    },
    conversions: results,
  };
}

/**
 * Convert a single time to one timezone
 * @param {Object} input - { time, from, to }
 */
function convertSingle(input, config = {}) {
  let time, fromTz, toTz;
  
  if (typeof input === 'object') {
    time = input.time || input.dateTime || input.value;
    fromTz = input.from || input.fromTimezone || input.source;
    toTz = input.to || input.toTimezone || input.target || config.to;
  } else {
    time = input;
    fromTz = config.from;
    toTz = config.to;
  }
  
  const sourceTimezone = fromTz ? resolveTimezone(fromTz) : null;
  const targetTimezone = toTz ? resolveTimezone(toTz) : 'UTC';
  
  if (!targetTimezone) {
    return { error: `Unknown timezone: ${toTz}` };
  }
  
  const date = parseTimeInput(time, sourceTimezone);
  
  let utcDate = date;
  if (sourceTimezone) {
    const tzData = TIMEZONE_DATA[sourceTimezone];
    if (tzData) {
      utcDate = new Date(date.getTime() - tzData.offset * 60 * 1000);
    }
  }
  
  const result = convertToTimezone(utcDate, targetTimezone);
  return {
    input: {
      time: time || 'now',
      from: sourceTimezone || 'local',
    },
    result,
  };
}

/**
 * Get current time in multiple timezones
 */
function now(input, config = {}) {
  let timezones;
  
  if (typeof input === 'object') {
    timezones = input.timezones || input.zones || input.to;
  } else if (typeof input === 'string') {
    timezones = [input];
  } else {
    timezones = config.timezones;
  }
  
  const zones = Array.isArray(timezones) ? timezones : timezones ? [timezones] : [];
  
  if (zones.length === 0) {
    // Default timezones for "now"
    zones.push('UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney');
  }
  
  const utcNow = new Date();
  const results = [];
  
  for (const tz of zones) {
    const resolved = resolveTimezone(tz);
    if (resolved) {
      const converted = convertToTimezone(utcNow, resolved);
      if (converted) {
        results.push(converted);
      }
    }
  }
  
  return {
    utc: utcNow.toISOString(),
    timezones: results,
  };
}

/**
 * List all available timezones
 */
function listTimezones(input, config = {}) {
  let filter, region;
  
  if (typeof input === 'object') {
    filter = input.filter || input.search;
    region = input.region;
  } else if (typeof input === 'string') {
    filter = input;
  }
  
  let timezones = Object.entries(TIMEZONE_DATA).map(([id, data]) => ({
    id,
    name: data.name,
    abbr: data.abbr,
    offset: data.offset,
    offsetString: formatOffset(data.offset),
  }));
  
  // Filter by region
  if (region) {
    const regionLower = region.toLowerCase();
    timezones = timezones.filter(tz => tz.id.toLowerCase().startsWith(regionLower));
  }
  
  // Filter by search term
  if (filter) {
    const filterLower = filter.toLowerCase();
    timezones = timezones.filter(tz => 
      tz.id.toLowerCase().includes(filterLower) ||
      tz.name.toLowerCase().includes(filterLower) ||
      tz.abbr.toLowerCase().includes(filterLower)
    );
  }
  
  // Sort by offset
  timezones.sort((a, b) => a.offset - b.offset);
  
  return {
    total: timezones.length,
    timezones,
  };
}

/**
 * Get timezone info
 */
function getTimezoneInfo(input, config = {}) {
  let timezone;
  
  if (typeof input === 'object') {
    timezone = input.timezone || input.zone || input.tz;
  } else {
    timezone = input;
  }
  
  const resolved = resolveTimezone(timezone);
  if (!resolved) {
    return { error: `Unknown timezone: ${timezone}` };
  }
  
  const tzData = TIMEZONE_DATA[resolved];
  const now = new Date();
  const converted = convertToTimezone(now, resolved);
  
  return {
    id: resolved,
    name: tzData.name,
    abbr: tzData.abbr,
    offset: tzData.offset,
    offsetString: formatOffset(tzData.offset),
    currentTime: converted.time,
    currentTime24h: converted.time24h,
    currentDateTime: converted.dateTime,
  };
}

/**
 * Calculate time difference between two timezones
 */
function timeDifference(input, config = {}) {
  let tz1, tz2;
  
  if (typeof input === 'object') {
    tz1 = input.from || input.timezone1 || input.tz1;
    tz2 = input.to || input.timezone2 || input.tz2;
  } else {
    tz1 = input;
    tz2 = config.to;
  }
  
  const resolved1 = resolveTimezone(tz1);
  const resolved2 = resolveTimezone(tz2);
  
  if (!resolved1) return { error: `Unknown timezone: ${tz1}` };
  if (!resolved2) return { error: `Unknown timezone: ${tz2}` };
  
  const data1 = TIMEZONE_DATA[resolved1];
  const data2 = TIMEZONE_DATA[resolved2];
  
  const diffMinutes = data2.offset - data1.offset;
  const diffHours = diffMinutes / 60;
  
  const sign = diffMinutes >= 0 ? '+' : '';
  const hoursStr = diffHours === Math.floor(diffHours) 
    ? `${sign}${diffHours}` 
    : `${sign}${diffHours.toFixed(1)}`;
  
  return {
    from: {
      id: resolved1,
      name: data1.name,
      offset: data1.offset,
    },
    to: {
      id: resolved2,
      name: data2.name,
      offset: data2.offset,
    },
    difference: {
      minutes: diffMinutes,
      hours: diffHours,
      description: `${hoursStr} hours`,
    },
  };
}

/**
 * Find meeting time across timezones
 * Given a preferred time range in one timezone, find the local times in other timezones
 */
function findMeetingTime(input, config = {}) {
  let sourceTimezone, targetTimezones, preferredHour, preferredEndHour;
  
  if (typeof input === 'object') {
    sourceTimezone = input.from || input.source || input.timezone;
    targetTimezones = input.to || input.targets || input.timezones;
    preferredHour = input.hour || input.startHour || 9;
    preferredEndHour = input.endHour || preferredHour + 1;
  }
  
  const resolved = sourceTimezone ? resolveTimezone(sourceTimezone) : 'UTC';
  if (!resolved) return { error: `Unknown timezone: ${sourceTimezone}` };
  
  const targets = Array.isArray(targetTimezones) ? targetTimezones : [targetTimezones].filter(Boolean);
  
  if (targets.length === 0) {
    targets.push('America/New_York', 'Europe/London', 'Asia/Tokyo');
  }
  
  const sourceData = TIMEZONE_DATA[resolved];
  const results = [];
  
  for (const tz of targets) {
    const targetResolved = resolveTimezone(tz);
    if (!targetResolved) continue;
    
    const targetData = TIMEZONE_DATA[targetResolved];
    const diffMinutes = targetData.offset - sourceData.offset;
    const diffHours = diffMinutes / 60;
    
    const localStartHour = preferredHour + diffHours;
    const localEndHour = preferredEndHour + diffHours;
    
    // Normalize hours
    const normalizeHour = (h) => {
      while (h < 0) h += 24;
      while (h >= 24) h -= 24;
      return h;
    };
    
    const formatHour = (h) => {
      const hour = Math.floor(h);
      const mins = Math.round((h - hour) * 60);
      const h12 = hour % 12 || 12;
      const meridiem = hour < 12 ? 'AM' : 'PM';
      return mins > 0 ? `${h12}:${String(mins).padStart(2, '0')} ${meridiem}` : `${h12}:00 ${meridiem}`;
    };
    
    const startNorm = normalizeHour(localStartHour);
    const endNorm = normalizeHour(localEndHour);
    
    // Determine if time is during business hours
    const isBusinessHours = startNorm >= 9 && startNorm <= 17 && endNorm >= 9 && endNorm <= 18;
    
    results.push({
      timezone: targetResolved,
      name: targetData.name,
      abbr: targetData.abbr,
      localStartTime: formatHour(startNorm),
      localEndTime: formatHour(endNorm),
      isBusinessHours,
      note: isBusinessHours ? 'Within business hours' : 'Outside business hours',
    });
  }
  
  return {
    source: {
      timezone: resolved,
      name: sourceData.name,
      proposedTime: `${preferredHour}:00 - ${preferredEndHour}:00`,
    },
    participants: results,
  };
}

module.exports = {
  convert,
  convertSingle,
  now,
  listTimezones,
  getTimezoneInfo,
  timeDifference,
  findMeetingTime,
};
