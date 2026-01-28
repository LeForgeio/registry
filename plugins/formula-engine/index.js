/**
 * Formula Engine - Excel-Compatible Functions
 * LeForge ForgeHook Plugin
 * 
 * 150+ Excel-compatible functions across 6 categories:
 * - Math & Statistics
 * - Logical
 * - Text
 * - Date/Time
 * - Financial
 * - Lookup & Reference
 */

// ============================================================================
// UTILITY FUNCTIONS (Internal)
// ============================================================================

/**
 * Flatten nested arrays and filter to numbers only
 */
function flattenNumbers(arr) {
  const flat = Array.isArray(arr) ? arr.flat(Infinity) : [arr];
  return flat.filter(v => typeof v === 'number' && !isNaN(v));
}

/**
 * Parse criteria string like ">10", "<=5", "<>0", "=text"
 */
function parseCriteria(criteria) {
  if (typeof criteria === 'function') return criteria;
  if (typeof criteria !== 'string') {
    return (v) => v === criteria;
  }
  
  const match = criteria.match(/^(>=|<=|<>|>|<|=)?(.*)$/);
  if (!match) return () => false;
  
  const [, op = '=', value] = match;
  const numValue = parseFloat(value);
  const isNum = !isNaN(numValue);
  const compareValue = isNum ? numValue : value;
  
  const ops = {
    '>=': (v) => v >= compareValue,
    '<=': (v) => v <= compareValue,
    '<>': (v) => v !== compareValue,
    '>': (v) => v > compareValue,
    '<': (v) => v < compareValue,
    '=': (v) => v === compareValue || (isNum && v === numValue) || String(v).toLowerCase() === String(value).toLowerCase()
  };
  
  return ops[op] || (() => false);
}

/**
 * Parse date string to Date object
 */
function parseDate(date) {
  if (date instanceof Date) return date;
  if (typeof date === 'number') {
    // Excel serial date (days since 1900-01-01, with leap year bug)
    return new Date((date - 25569) * 86400000);
  }
  return new Date(date);
}

/**
 * Format date to ISO string (date only)
 */
function formatDate(date) {
  const d = parseDate(date);
  return d.toISOString().split('T')[0];
}

/**
 * Get Excel serial date number from Date
 */
function dateToSerial(date) {
  const d = parseDate(date);
  return Math.floor((d.getTime() / 86400000) + 25569);
}

// ============================================================================
// MATH & STATISTICS FUNCTIONS
// ============================================================================

function SUM(values) {
  const nums = flattenNumbers(values);
  return nums.reduce((a, b) => a + b, 0);
}

function AVERAGE(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  return SUM(nums) / nums.length;
}

function COUNT(values) {
  return flattenNumbers(values).length;
}

function COUNTA(values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  return flat.filter(v => v !== null && v !== undefined && v !== '').length;
}

function COUNTBLANK(values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  return flat.filter(v => v === null || v === undefined || v === '').length;
}

function COUNTIF(values, criteria) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  const test = parseCriteria(criteria);
  return flat.filter(test).length;
}

function COUNTIFS(criteriaRanges) {
  if (!Array.isArray(criteriaRanges) || criteriaRanges.length === 0) return 0;
  
  const [firstRange] = criteriaRanges;
  const [range] = firstRange;
  const flat = Array.isArray(range) ? range.flat(Infinity) : [range];
  
  return flat.filter((_, i) => {
    return criteriaRanges.every(([r, c]) => {
      const arr = Array.isArray(r) ? r.flat(Infinity) : [r];
      const test = parseCriteria(c);
      return test(arr[i]);
    });
  }).length;
}

function MAX(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  return Math.max(...nums);
}

function MIN(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  return Math.min(...nums);
}

function MEDIAN(values) {
  const nums = flattenNumbers(values).sort((a, b) => a - b);
  if (nums.length === 0) return 0;
  const mid = Math.floor(nums.length / 2);
  return nums.length % 2 !== 0 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
}

function MODE(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  
  const freq = {};
  nums.forEach(n => freq[n] = (freq[n] || 0) + 1);
  
  let maxFreq = 0, mode = nums[0];
  for (const [num, count] of Object.entries(freq)) {
    if (count > maxFreq) {
      maxFreq = count;
      mode = parseFloat(num);
    }
  }
  return mode;
}

function STDEV(values) {
  const nums = flattenNumbers(values);
  if (nums.length < 2) return 0;
  const avg = AVERAGE(nums);
  const squareDiffs = nums.map(n => Math.pow(n - avg, 2));
  return Math.sqrt(SUM(squareDiffs) / (nums.length - 1));
}

function STDEVP(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  const avg = AVERAGE(nums);
  const squareDiffs = nums.map(n => Math.pow(n - avg, 2));
  return Math.sqrt(SUM(squareDiffs) / nums.length);
}

function VAR(values) {
  const nums = flattenNumbers(values);
  if (nums.length < 2) return 0;
  const avg = AVERAGE(nums);
  const squareDiffs = nums.map(n => Math.pow(n - avg, 2));
  return SUM(squareDiffs) / (nums.length - 1);
}

function VARP(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  const avg = AVERAGE(nums);
  const squareDiffs = nums.map(n => Math.pow(n - avg, 2));
  return SUM(squareDiffs) / nums.length;
}

function SUMIF(range, criteria, sumRange) {
  const r = Array.isArray(range) ? range.flat(Infinity) : [range];
  const sr = sumRange ? (Array.isArray(sumRange) ? sumRange.flat(Infinity) : [sumRange]) : r;
  const test = parseCriteria(criteria);
  
  let sum = 0;
  r.forEach((v, i) => {
    if (test(v) && typeof sr[i] === 'number') {
      sum += sr[i];
    }
  });
  return sum;
}

function SUMIFS(sumRange, criteriaRanges) {
  const sr = Array.isArray(sumRange) ? sumRange.flat(Infinity) : [sumRange];
  
  let sum = 0;
  sr.forEach((v, i) => {
    if (typeof v !== 'number') return;
    
    const matches = criteriaRanges.every(([r, c]) => {
      const arr = Array.isArray(r) ? r.flat(Infinity) : [r];
      const test = parseCriteria(c);
      return test(arr[i]);
    });
    
    if (matches) sum += v;
  });
  return sum;
}

function AVERAGEIF(range, criteria, averageRange) {
  const r = Array.isArray(range) ? range.flat(Infinity) : [range];
  const ar = averageRange ? (Array.isArray(averageRange) ? averageRange.flat(Infinity) : [averageRange]) : r;
  const test = parseCriteria(criteria);
  
  const vals = [];
  r.forEach((v, i) => {
    if (test(v) && typeof ar[i] === 'number') {
      vals.push(ar[i]);
    }
  });
  return vals.length > 0 ? AVERAGE(vals) : 0;
}

function ROUND(number, decimals = 0) {
  const factor = Math.pow(10, decimals);
  return Math.round(number * factor) / factor;
}

function ROUNDUP(number, decimals = 0) {
  const factor = Math.pow(10, decimals);
  return Math.sign(number) * Math.ceil(Math.abs(number) * factor) / factor;
}

function ROUNDDOWN(number, decimals = 0) {
  const factor = Math.pow(10, decimals);
  return Math.sign(number) * Math.floor(Math.abs(number) * factor) / factor;
}

function CEILING(number, significance = 1) {
  if (significance === 0) return 0;
  return Math.ceil(number / significance) * significance;
}

function FLOOR(number, significance = 1) {
  if (significance === 0) return 0;
  return Math.floor(number / significance) * significance;
}

function TRUNC(number, decimals = 0) {
  const factor = Math.pow(10, decimals);
  return Math.trunc(number * factor) / factor;
}

function INT(number) {
  return Math.floor(number);
}

function ABS(number) {
  return Math.abs(number);
}

function SIGN(number) {
  return Math.sign(number);
}

function SQRT(number) {
  if (number < 0) throw new Error('#NUM! - Cannot take square root of negative number');
  return Math.sqrt(number);
}

function POWER(number, power) {
  return Math.pow(number, power);
}

function EXP(number) {
  return Math.exp(number);
}

function LN(number) {
  if (number <= 0) throw new Error('#NUM! - LN requires positive number');
  return Math.log(number);
}

function LOG(number, base = 10) {
  if (number <= 0) throw new Error('#NUM! - LOG requires positive number');
  return Math.log(number) / Math.log(base);
}

function LOG10(number) {
  return LOG(number, 10);
}

function MOD(number, divisor) {
  if (divisor === 0) throw new Error('#DIV/0! - Cannot divide by zero');
  return number - divisor * Math.floor(number / divisor);
}

function QUOTIENT(numerator, denominator) {
  if (denominator === 0) throw new Error('#DIV/0!');
  return Math.trunc(numerator / denominator);
}

function PRODUCT(values) {
  const nums = flattenNumbers(values);
  if (nums.length === 0) return 0;
  return nums.reduce((a, b) => a * b, 1);
}

function SUMPRODUCT(arrays) {
  if (!Array.isArray(arrays) || arrays.length === 0) return 0;
  
  const firstLen = arrays[0].length;
  let sum = 0;
  
  for (let i = 0; i < firstLen; i++) {
    let product = 1;
    for (const arr of arrays) {
      const val = Array.isArray(arr[i]) ? arr[i][0] : arr[i];
      if (typeof val === 'number') {
        product *= val;
      }
    }
    sum += product;
  }
  return sum;
}

function GCD(values) {
  const nums = flattenNumbers(values).map(Math.abs).map(Math.floor);
  if (nums.length === 0) return 0;
  
  const gcd2 = (a, b) => b === 0 ? a : gcd2(b, a % b);
  return nums.reduce((a, b) => gcd2(a, b));
}

function LCM(values) {
  const nums = flattenNumbers(values).map(Math.abs).map(Math.floor);
  if (nums.length === 0) return 0;
  
  const gcd2 = (a, b) => b === 0 ? a : gcd2(b, a % b);
  const lcm2 = (a, b) => (a * b) / gcd2(a, b);
  return nums.reduce((a, b) => lcm2(a, b));
}

function FACT(number) {
  const n = Math.floor(number);
  if (n < 0) throw new Error('#NUM! - Factorial requires non-negative integer');
  if (n === 0 || n === 1) return 1;
  let result = 1;
  for (let i = 2; i <= n; i++) result *= i;
  return result;
}

function COMBIN(n, k) {
  if (k < 0 || k > n) return 0;
  return FACT(n) / (FACT(k) * FACT(n - k));
}

function PERMUT(n, k) {
  if (k < 0 || k > n) return 0;
  return FACT(n) / FACT(n - k);
}

function RAND() {
  return Math.random();
}

function RANDBETWEEN(bottom, top) {
  bottom = Math.ceil(bottom);
  top = Math.floor(top);
  return Math.floor(Math.random() * (top - bottom + 1)) + bottom;
}

function PI() {
  return Math.PI;
}

function SIN(angle) {
  return Math.sin(angle);
}

function COS(angle) {
  return Math.cos(angle);
}

function TAN(angle) {
  return Math.tan(angle);
}

function ASIN(number) {
  return Math.asin(number);
}

function ACOS(number) {
  return Math.acos(number);
}

function ATAN(number) {
  return Math.atan(number);
}

function ATAN2(x, y) {
  return Math.atan2(y, x);
}

function DEGREES(radians) {
  return radians * (180 / Math.PI);
}

function RADIANS(degrees) {
  return degrees * (Math.PI / 180);
}

function LARGE(values, k) {
  const nums = flattenNumbers(values).sort((a, b) => b - a);
  if (k < 1 || k > nums.length) throw new Error('#NUM! - Invalid k value');
  return nums[k - 1];
}

function SMALL(values, k) {
  const nums = flattenNumbers(values).sort((a, b) => a - b);
  if (k < 1 || k > nums.length) throw new Error('#NUM! - Invalid k value');
  return nums[k - 1];
}

function RANK(number, values, order = 0) {
  const nums = flattenNumbers(values);
  const sorted = order === 0 
    ? nums.sort((a, b) => b - a) 
    : nums.sort((a, b) => a - b);
  
  const rank = sorted.indexOf(number);
  if (rank === -1) throw new Error('#N/A - Value not found');
  return rank + 1;
}

function PERCENTILE(values, k) {
  if (k < 0 || k > 1) throw new Error('#NUM! - k must be between 0 and 1');
  const nums = flattenNumbers(values).sort((a, b) => a - b);
  if (nums.length === 0) return 0;
  
  const index = k * (nums.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  
  if (lower === upper) return nums[lower];
  return nums[lower] + (nums[upper] - nums[lower]) * (index - lower);
}

function QUARTILE(values, quart) {
  if (quart < 0 || quart > 4) throw new Error('#NUM! - quart must be 0-4');
  return PERCENTILE(values, quart * 0.25);
}

// ============================================================================
// LOGICAL FUNCTIONS
// ============================================================================

function IF(condition, valueIfTrue, valueIfFalse = false) {
  return condition ? valueIfTrue : valueIfFalse;
}

function IFS(conditions) {
  for (const [cond, val] of conditions) {
    if (cond) return val;
  }
  throw new Error('#N/A - No condition was true');
}

function SWITCH(expression, cases, defaultValue) {
  for (const [val, result] of cases) {
    if (expression === val) return result;
  }
  if (defaultValue !== undefined) return defaultValue;
  throw new Error('#N/A - No matching value');
}

function AND(values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  return flat.every(Boolean);
}

function OR(values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  return flat.some(Boolean);
}

function NOT(value) {
  return !value;
}

function XOR(values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  const trueCount = flat.filter(Boolean).length;
  return trueCount % 2 === 1;
}

function IFERROR(value, valueIfError) {
  try {
    if (value instanceof Error) return valueIfError;
    if (typeof value === 'number' && !isFinite(value)) return valueIfError;
    return value;
  } catch {
    return valueIfError;
  }
}

function IFNA(value, valueIfNA) {
  if (value === null || value === undefined) return valueIfNA;
  return value;
}

function ISBLANK(value) {
  return value === null || value === undefined || value === '';
}

function ISNUMBER(value) {
  return typeof value === 'number' && !isNaN(value);
}

function ISTEXT(value) {
  return typeof value === 'string';
}

function ISLOGICAL(value) {
  return typeof value === 'boolean';
}

function ISERROR(value) {
  return value instanceof Error || (typeof value === 'number' && !isFinite(value));
}

function ISEVEN(number) {
  return Math.floor(number) % 2 === 0;
}

function ISODD(number) {
  return Math.floor(number) % 2 !== 0;
}

function TRUE() {
  return true;
}

function FALSE() {
  return false;
}

// ============================================================================
// TEXT FUNCTIONS
// ============================================================================

function LEFT(text, numChars = 1) {
  return String(text).substring(0, numChars);
}

function RIGHT(text, numChars = 1) {
  const str = String(text);
  return str.substring(str.length - numChars);
}

function MID(text, startNum, numChars) {
  return String(text).substring(startNum - 1, startNum - 1 + numChars);
}

function LEN(text) {
  return String(text).length;
}

function FIND(findText, withinText, startNum = 1) {
  const str = String(withinText);
  const pos = str.indexOf(String(findText), startNum - 1);
  if (pos === -1) throw new Error('#VALUE! - Text not found');
  return pos + 1;
}

function SEARCH(findText, withinText, startNum = 1) {
  const str = String(withinText).toLowerCase();
  const pos = str.indexOf(String(findText).toLowerCase(), startNum - 1);
  if (pos === -1) throw new Error('#VALUE! - Text not found');
  return pos + 1;
}

function CONCAT(values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  return flat.map(String).join('');
}

function CONCATENATE(values) {
  return CONCAT(values);
}

function TEXTJOIN(delimiter, ignoreEmpty, values) {
  const flat = Array.isArray(values) ? values.flat(Infinity) : [values];
  const filtered = ignoreEmpty 
    ? flat.filter(v => v !== null && v !== undefined && v !== '')
    : flat;
  return filtered.map(String).join(delimiter);
}

function TRIM(text) {
  return String(text).replace(/\s+/g, ' ').trim();
}

function CLEAN(text) {
  return String(text).replace(/[\x00-\x1F]/g, '');
}

function UPPER(text) {
  return String(text).toUpperCase();
}

function LOWER(text) {
  return String(text).toLowerCase();
}

function PROPER(text) {
  return String(text).toLowerCase().replace(/(?:^|\s)\S/g, c => c.toUpperCase());
}

function SUBSTITUTE(text, oldText, newText, instanceNum) {
  const str = String(text);
  const old = String(oldText);
  
  if (instanceNum === undefined) {
    return str.split(old).join(newText);
  }
  
  let count = 0;
  let result = '';
  let lastIndex = 0;
  let index;
  
  while ((index = str.indexOf(old, lastIndex)) !== -1) {
    count++;
    if (count === instanceNum) {
      result += str.substring(lastIndex, index) + newText;
      lastIndex = index + old.length;
      result += str.substring(lastIndex);
      return result;
    }
    result += str.substring(lastIndex, index + old.length);
    lastIndex = index + old.length;
  }
  
  return str;
}

function REPLACE(oldText, startNum, numChars, newText) {
  const str = String(oldText);
  return str.substring(0, startNum - 1) + newText + str.substring(startNum - 1 + numChars);
}

function REPT(text, times) {
  if (times < 0) throw new Error('#VALUE!');
  return String(text).repeat(Math.floor(times));
}

function TEXT(value, format) {
  const num = Number(value);
  if (isNaN(num)) return String(value);
  
  // Handle common Excel formats
  if (format === '0') return Math.round(num).toString();
  if (format === '0.00') return num.toFixed(2);
  if (format === '0.0') return num.toFixed(1);
  if (format === '#,##0') return Math.round(num).toLocaleString();
  if (format === '#,##0.00') return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (format === '$#,##0') return '$' + Math.round(num).toLocaleString();
  if (format === '$#,##0.00') return '$' + num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (format === '0%') return Math.round(num * 100) + '%';
  if (format === '0.00%') return (num * 100).toFixed(2) + '%';
  
  // Decimal places from format
  const decMatch = format.match(/\.(\d+)/);
  if (decMatch) {
    return num.toFixed(decMatch[1].length);
  }
  
  return num.toString();
}

function VALUE(text) {
  const num = parseFloat(String(text).replace(/[,$]/g, ''));
  if (isNaN(num)) throw new Error('#VALUE!');
  return num;
}

function FIXED(number, decimals = 2, noCommas = false) {
  const fixed = number.toFixed(decimals);
  if (noCommas) return fixed;
  
  const parts = fixed.split('.');
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return parts.join('.');
}

function DOLLAR(number, decimals = 2) {
  return '$' + FIXED(Math.abs(number), decimals);
}

function CHAR(number) {
  return String.fromCharCode(number);
}

function CODE(text) {
  return String(text).charCodeAt(0);
}

function EXACT(text1, text2) {
  return String(text1) === String(text2);
}

function TEXTSPLIT(text, colDelimiter, rowDelimiter) {
  if (rowDelimiter) {
    return String(text).split(rowDelimiter).map(row => row.split(colDelimiter));
  }
  return String(text).split(colDelimiter);
}

function TEXTBEFORE(text, delimiter, instanceNum = 1) {
  const str = String(text);
  const delim = String(delimiter);
  
  let pos = -1;
  for (let i = 0; i < instanceNum; i++) {
    pos = str.indexOf(delim, pos + 1);
    if (pos === -1) throw new Error('#N/A - Delimiter not found');
  }
  
  return str.substring(0, pos);
}

function TEXTAFTER(text, delimiter, instanceNum = 1) {
  const str = String(text);
  const delim = String(delimiter);
  
  let pos = -1;
  for (let i = 0; i < instanceNum; i++) {
    pos = str.indexOf(delim, pos + 1);
    if (pos === -1) throw new Error('#N/A - Delimiter not found');
  }
  
  return str.substring(pos + delim.length);
}

// ============================================================================
// DATE/TIME FUNCTIONS
// ============================================================================

function TODAY() {
  return formatDate(new Date());
}

function NOW() {
  return new Date().toISOString();
}

function DATE(year, month, day) {
  return formatDate(new Date(year, month - 1, day));
}

function DATEVALUE(dateText) {
  return dateToSerial(parseDate(dateText));
}

function TIME(hour, minute, second = 0) {
  const d = new Date();
  d.setHours(hour, minute, second, 0);
  return d.toTimeString().split(' ')[0];
}

function TIMEVALUE(timeText) {
  const d = new Date(`1970-01-01 ${timeText}`);
  return (d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds()) / 86400;
}

function YEAR(date) {
  return parseDate(date).getFullYear();
}

function MONTH(date) {
  return parseDate(date).getMonth() + 1;
}

function DAY(date) {
  return parseDate(date).getDate();
}

function HOUR(time) {
  const d = typeof time === 'string' && !time.includes('-') 
    ? new Date(`1970-01-01 ${time}`)
    : parseDate(time);
  return d.getHours();
}

function MINUTE(time) {
  const d = typeof time === 'string' && !time.includes('-')
    ? new Date(`1970-01-01 ${time}`)
    : parseDate(time);
  return d.getMinutes();
}

function SECOND(time) {
  const d = typeof time === 'string' && !time.includes('-')
    ? new Date(`1970-01-01 ${time}`)
    : parseDate(time);
  return d.getSeconds();
}

function WEEKDAY(date, returnType = 1) {
  const d = parseDate(date);
  const day = d.getDay();
  
  switch (returnType) {
    case 1: return day + 1;           // 1=Sunday, 7=Saturday
    case 2: return day === 0 ? 7 : day; // 1=Monday, 7=Sunday
    case 3: return day === 0 ? 6 : day - 1; // 0=Monday, 6=Sunday
    default: return day + 1;
  }
}

function WEEKNUM(date, returnType = 1) {
  const d = parseDate(date);
  const startOfYear = new Date(d.getFullYear(), 0, 1);
  const days = Math.floor((d - startOfYear) / 86400000);
  return Math.ceil((days + startOfYear.getDay() + 1) / 7);
}

function ISOWEEKNUM(date) {
  const d = parseDate(date);
  const target = new Date(d.valueOf());
  const dayNr = (d.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = new Date(target.getFullYear(), 0, 4);
  const diff = target - firstThursday;
  return 1 + Math.round(diff / (7 * 86400000));
}

function DATEDIF(startDate, endDate, unit) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  
  if (start > end) throw new Error('#NUM! - Start date must be before end date');
  
  const diffDays = Math.floor((end - start) / 86400000);
  const diffMonths = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
  const diffYears = end.getFullYear() - start.getFullYear();
  
  switch (unit.toUpperCase()) {
    case 'Y': return diffYears - (end < new Date(end.getFullYear(), start.getMonth(), start.getDate()) ? 1 : 0);
    case 'M': return diffMonths - (end.getDate() < start.getDate() ? 1 : 0);
    case 'D': return diffDays;
    case 'MD': return Math.abs(end.getDate() - start.getDate());
    case 'YM': return (diffMonths % 12 + 12) % 12 - (end.getDate() < start.getDate() ? 1 : 0);
    case 'YD': {
      const yearStart = new Date(end.getFullYear(), start.getMonth(), start.getDate());
      if (yearStart > end) yearStart.setFullYear(yearStart.getFullYear() - 1);
      return Math.floor((end - yearStart) / 86400000);
    }
    default: throw new Error('#VALUE! - Invalid unit');
  }
}

function DAYS(endDate, startDate) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  return Math.floor((end - start) / 86400000);
}

function DAYS360(startDate, endDate, method = false) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  
  let sd = start.getDate();
  let ed = end.getDate();
  
  if (method) {
    // European method
    if (sd === 31) sd = 30;
    if (ed === 31) ed = 30;
  } else {
    // US method
    if (sd === 31) sd = 30;
    if (sd === 30 && ed === 31) ed = 30;
  }
  
  return (end.getFullYear() - start.getFullYear()) * 360 +
         (end.getMonth() - start.getMonth()) * 30 +
         (ed - sd);
}

function EDATE(startDate, months) {
  const d = parseDate(startDate);
  d.setMonth(d.getMonth() + months);
  return formatDate(d);
}

function EOMONTH(startDate, months) {
  const d = parseDate(startDate);
  d.setMonth(d.getMonth() + months + 1);
  d.setDate(0);
  return formatDate(d);
}

function WORKDAY(startDate, days, holidays = []) {
  const d = parseDate(startDate);
  const holidaySet = new Set(holidays.map(h => formatDate(h)));
  
  let count = 0;
  const direction = days >= 0 ? 1 : -1;
  
  while (count < Math.abs(days)) {
    d.setDate(d.getDate() + direction);
    const dayOfWeek = d.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6 && !holidaySet.has(formatDate(d))) {
      count++;
    }
  }
  
  return formatDate(d);
}

function NETWORKDAYS(startDate, endDate, holidays = []) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  const holidaySet = new Set(holidays.map(h => formatDate(h)));
  
  let count = 0;
  const d = new Date(start);
  const direction = end >= start ? 1 : -1;
  
  while ((direction === 1 && d <= end) || (direction === -1 && d >= end)) {
    const dayOfWeek = d.getDay();
    if (dayOfWeek !== 0 && dayOfWeek !== 6 && !holidaySet.has(formatDate(d))) {
      count++;
    }
    d.setDate(d.getDate() + direction);
  }
  
  return direction === -1 ? -count : count;
}

function YEARFRAC(startDate, endDate, basis = 0) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  const days = Math.abs((end - start) / 86400000);
  
  switch (basis) {
    case 0: return DAYS360(startDate, endDate, false) / 360; // US 30/360
    case 1: return days / 365; // Actual/Actual
    case 2: return days / 360; // Actual/360
    case 3: return days / 365; // Actual/365
    case 4: return DAYS360(startDate, endDate, true) / 360; // European 30/360
    default: return days / 365;
  }
}

// ============================================================================
// FINANCIAL FUNCTIONS
// ============================================================================

function PMT(rate, nper, pv, fv = 0, type = 0) {
  if (rate === 0) return -(pv + fv) / nper;
  
  const pvif = Math.pow(1 + rate, nper);
  let pmt = rate * (pv * pvif + fv) / (pvif - 1);
  
  if (type === 1) pmt /= (1 + rate);
  
  return -pmt;
}

function PPMT(rate, per, nper, pv, fv = 0, type = 0) {
  const payment = PMT(rate, nper, pv, fv, type);
  const interest = IPMT(rate, per, nper, pv, fv, type);
  return payment - interest;
}

function IPMT(rate, per, nper, pv, fv = 0, type = 0) {
  const payment = PMT(rate, nper, pv, fv, type);
  
  let balance = pv;
  for (let i = 1; i < per; i++) {
    const interest = balance * rate;
    const principal = payment + interest;
    balance += principal;
  }
  
  return -(balance * rate);
}

function CUMIPMT(rate, nper, pv, startPeriod, endPeriod, type = 0) {
  let cumInt = 0;
  for (let per = startPeriod; per <= endPeriod; per++) {
    cumInt += IPMT(rate, per, nper, pv, 0, type);
  }
  return cumInt;
}

function CUMPRINC(rate, nper, pv, startPeriod, endPeriod, type = 0) {
  let cumPrinc = 0;
  for (let per = startPeriod; per <= endPeriod; per++) {
    cumPrinc += PPMT(rate, per, nper, pv, 0, type);
  }
  return cumPrinc;
}

function PV(rate, nper, pmt, fv = 0, type = 0) {
  if (rate === 0) return -pmt * nper - fv;
  
  const pvif = Math.pow(1 + rate, nper);
  const factor = type === 1 ? (1 + rate) : 1;
  
  return -(pmt * factor * (pvif - 1) / rate + fv) / pvif;
}

function FV(rate, nper, pmt, pv = 0, type = 0) {
  if (rate === 0) return -pv - pmt * nper;
  
  const pvif = Math.pow(1 + rate, nper);
  const factor = type === 1 ? (1 + rate) : 1;
  
  return -(pv * pvif + pmt * factor * (pvif - 1) / rate);
}

function NPV(rate, values) {
  const vals = flattenNumbers(values);
  let npv = 0;
  for (let i = 0; i < vals.length; i++) {
    npv += vals[i] / Math.pow(1 + rate, i + 1);
  }
  return npv;
}

function XNPV(rate, values, dates) {
  const vals = flattenNumbers(values);
  const d0 = parseDate(dates[0]);
  
  let npv = 0;
  for (let i = 0; i < vals.length; i++) {
    const di = parseDate(dates[i]);
    const years = (di - d0) / (365 * 86400000);
    npv += vals[i] / Math.pow(1 + rate, years);
  }
  return npv;
}

function IRR(values, guess = 0.1) {
  const vals = flattenNumbers(values);
  
  // Newton-Raphson method
  let rate = guess;
  const maxIter = 100;
  const tolerance = 1e-7;
  
  for (let i = 0; i < maxIter; i++) {
    let npv = 0;
    let dnpv = 0;
    
    for (let j = 0; j < vals.length; j++) {
      const factor = Math.pow(1 + rate, j);
      npv += vals[j] / factor;
      dnpv -= j * vals[j] / (factor * (1 + rate));
    }
    
    const newRate = rate - npv / dnpv;
    
    if (Math.abs(newRate - rate) < tolerance) {
      return newRate;
    }
    
    rate = newRate;
  }
  
  throw new Error('#NUM! - IRR did not converge');
}

function XIRR(values, dates, guess = 0.1) {
  const vals = flattenNumbers(values);
  const d0 = parseDate(dates[0]);
  
  let rate = guess;
  const maxIter = 100;
  const tolerance = 1e-7;
  
  for (let i = 0; i < maxIter; i++) {
    let npv = 0;
    let dnpv = 0;
    
    for (let j = 0; j < vals.length; j++) {
      const di = parseDate(dates[j]);
      const years = (di - d0) / (365 * 86400000);
      const factor = Math.pow(1 + rate, years);
      npv += vals[j] / factor;
      dnpv -= years * vals[j] / (factor * (1 + rate));
    }
    
    const newRate = rate - npv / dnpv;
    
    if (Math.abs(newRate - rate) < tolerance) {
      return newRate;
    }
    
    rate = newRate;
  }
  
  throw new Error('#NUM! - XIRR did not converge');
}

function MIRR(values, financeRate, reinvestRate) {
  const vals = flattenNumbers(values);
  const n = vals.length;
  
  let pv = 0;  // Present value of negative cash flows
  let fv = 0;  // Future value of positive cash flows
  
  for (let i = 0; i < n; i++) {
    if (vals[i] < 0) {
      pv += vals[i] / Math.pow(1 + financeRate, i);
    } else {
      fv += vals[i] * Math.pow(1 + reinvestRate, n - 1 - i);
    }
  }
  
  if (pv === 0) throw new Error('#DIV/0!');
  
  return Math.pow(-fv / pv, 1 / (n - 1)) - 1;
}

function RATE(nper, pmt, pv, fv = 0, type = 0, guess = 0.1) {
  let rate = guess;
  const maxIter = 100;
  const tolerance = 1e-7;
  
  for (let i = 0; i < maxIter; i++) {
    const pvif = Math.pow(1 + rate, nper);
    const factor = type === 1 ? (1 + rate) : 1;
    
    const y = pv * pvif + pmt * factor * (pvif - 1) / rate + fv;
    const dy = pv * nper * Math.pow(1 + rate, nper - 1) +
               pmt * factor * (nper * Math.pow(1 + rate, nper - 1) / rate - (pvif - 1) / (rate * rate));
    
    const newRate = rate - y / dy;
    
    if (Math.abs(newRate - rate) < tolerance) {
      return newRate;
    }
    
    rate = newRate;
  }
  
  throw new Error('#NUM! - RATE did not converge');
}

function NPER(rate, pmt, pv, fv = 0, type = 0) {
  if (rate === 0) return -(pv + fv) / pmt;
  
  const factor = type === 1 ? (1 + rate) : 1;
  const numerator = pmt * factor - fv * rate;
  const denominator = pmt * factor + pv * rate;
  
  return Math.log(numerator / denominator) / Math.log(1 + rate);
}

function EFFECT(nominalRate, npery) {
  return Math.pow(1 + nominalRate / npery, npery) - 1;
}

function NOMINAL(effectRate, npery) {
  return npery * (Math.pow(1 + effectRate, 1 / npery) - 1);
}

function SLN(cost, salvage, life) {
  return (cost - salvage) / life;
}

function SYD(cost, salvage, life, per) {
  const sumYears = (life * (life + 1)) / 2;
  return ((cost - salvage) * (life - per + 1)) / sumYears;
}

function DB(cost, salvage, life, period, month = 12) {
  const rate = 1 - Math.pow(salvage / cost, 1 / life);
  let depreciation;
  let totalDepreciation = 0;
  
  for (let per = 1; per <= period; per++) {
    if (per === 1) {
      depreciation = cost * rate * month / 12;
    } else if (per === life + 1) {
      depreciation = (cost - totalDepreciation) * rate * (12 - month) / 12;
    } else {
      depreciation = (cost - totalDepreciation) * rate;
    }
    totalDepreciation += depreciation;
  }
  
  return depreciation;
}

function DDB(cost, salvage, life, period, factor = 2) {
  const rate = factor / life;
  let value = cost;
  let depreciation = 0;
  
  for (let per = 1; per <= period; per++) {
    depreciation = Math.min(value * rate, value - salvage);
    value -= depreciation;
  }
  
  return depreciation;
}

// ============================================================================
// LOOKUP & REFERENCE FUNCTIONS
// ============================================================================

function VLOOKUP(lookupValue, tableArray, colIndex, rangeLookup = true) {
  if (!Array.isArray(tableArray) || tableArray.length === 0) {
    throw new Error('#N/A - Table is empty');
  }
  
  const table = tableArray.map(row => Array.isArray(row) ? row : [row]);
  
  if (rangeLookup) {
    // Approximate match (binary search on sorted first column)
    let lastMatch = -1;
    for (let i = 0; i < table.length; i++) {
      if (table[i][0] <= lookupValue) {
        lastMatch = i;
      } else {
        break;
      }
    }
    
    if (lastMatch === -1) throw new Error('#N/A - No match found');
    return table[lastMatch][colIndex - 1];
  } else {
    // Exact match
    for (const row of table) {
      if (row[0] === lookupValue) {
        return row[colIndex - 1];
      }
    }
    throw new Error('#N/A - No exact match found');
  }
}

function HLOOKUP(lookupValue, tableArray, rowIndex, rangeLookup = true) {
  // Transpose and use VLOOKUP logic
  const transposed = TRANSPOSE(tableArray);
  return VLOOKUP(lookupValue, transposed, rowIndex, rangeLookup);
}

function XLOOKUP(lookupValue, lookupArray, returnArray, ifNotFound = null, matchMode = 0, searchMode = 1) {
  const lookup = Array.isArray(lookupArray) ? lookupArray.flat() : [lookupArray];
  const returns = Array.isArray(returnArray) ? returnArray.flat() : [returnArray];
  
  let indices = [...Array(lookup.length).keys()];
  if (searchMode === -1) indices.reverse();
  
  for (const i of indices) {
    const val = lookup[i];
    let match = false;
    
    switch (matchMode) {
      case 0: // Exact match
        match = val === lookupValue;
        break;
      case -1: // Exact or next smaller
        if (val === lookupValue) match = true;
        else if (val < lookupValue) match = true;
        break;
      case 1: // Exact or next larger
        if (val === lookupValue) match = true;
        else if (val > lookupValue) match = true;
        break;
      case 2: // Wildcard
        const pattern = String(lookupValue).replace(/\*/g, '.*').replace(/\?/g, '.');
        match = new RegExp(`^${pattern}$`, 'i').test(String(val));
        break;
    }
    
    if (match) return returns[i];
  }
  
  if (ifNotFound !== null) return ifNotFound;
  throw new Error('#N/A - Value not found');
}

function INDEX(array, rowNum, colNum = 1) {
  if (!Array.isArray(array)) return array;
  
  // Handle 1D array
  if (!Array.isArray(array[0])) {
    if (rowNum < 1 || rowNum > array.length) throw new Error('#REF!');
    return array[rowNum - 1];
  }
  
  // Handle 2D array
  if (rowNum < 1 || rowNum > array.length) throw new Error('#REF!');
  const row = array[rowNum - 1];
  if (colNum < 1 || colNum > row.length) throw new Error('#REF!');
  return row[colNum - 1];
}

function MATCH(lookupValue, lookupArray, matchType = 1) {
  const arr = Array.isArray(lookupArray) ? lookupArray.flat() : [lookupArray];
  
  if (matchType === 0) {
    // Exact match
    const idx = arr.indexOf(lookupValue);
    if (idx === -1) throw new Error('#N/A');
    return idx + 1;
  } else if (matchType === 1) {
    // Less than or equal (sorted ascending)
    let lastMatch = -1;
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] <= lookupValue) lastMatch = i;
      else break;
    }
    if (lastMatch === -1) throw new Error('#N/A');
    return lastMatch + 1;
  } else {
    // Greater than or equal (sorted descending)
    let lastMatch = -1;
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] >= lookupValue) lastMatch = i;
      else break;
    }
    if (lastMatch === -1) throw new Error('#N/A');
    return lastMatch + 1;
  }
}

function XMATCH(lookupValue, lookupArray, matchMode = 0, searchMode = 1) {
  const arr = Array.isArray(lookupArray) ? lookupArray.flat() : [lookupArray];
  
  let indices = [...Array(arr.length).keys()];
  if (searchMode === -1) indices.reverse();
  
  for (const i of indices) {
    const val = arr[i];
    let match = false;
    
    switch (matchMode) {
      case 0: match = val === lookupValue; break;
      case -1: match = val <= lookupValue; break;
      case 1: match = val >= lookupValue; break;
      case 2:
        const pattern = String(lookupValue).replace(/\*/g, '.*').replace(/\?/g, '.');
        match = new RegExp(`^${pattern}$`, 'i').test(String(val));
        break;
    }
    
    if (match) return i + 1;
  }
  
  throw new Error('#N/A');
}

function CHOOSE(indexNum, values) {
  const arr = Array.isArray(values) ? values : [values];
  if (indexNum < 1 || indexNum > arr.length) throw new Error('#VALUE!');
  return arr[indexNum - 1];
}

function LOOKUP(lookupValue, lookupVector, resultVector) {
  const lv = Array.isArray(lookupVector) ? lookupVector.flat() : [lookupVector];
  const rv = resultVector ? (Array.isArray(resultVector) ? resultVector.flat() : [resultVector]) : lv;
  
  let lastMatch = -1;
  for (let i = 0; i < lv.length; i++) {
    if (lv[i] <= lookupValue) lastMatch = i;
    else break;
  }
  
  if (lastMatch === -1) throw new Error('#N/A');
  return rv[lastMatch];
}

function OFFSET(array, rows, cols, height, width) {
  if (!Array.isArray(array)) return array;
  
  const is2D = Array.isArray(array[0]);
  const h = height || (is2D ? array.length - rows : 1);
  const w = width || (is2D ? array[0].length - cols : 1);
  
  if (is2D) {
    const result = [];
    for (let i = 0; i < h; i++) {
      const row = [];
      for (let j = 0; j < w; j++) {
        const r = array[rows + i];
        row.push(r ? r[cols + j] : undefined);
      }
      result.push(row);
    }
    return h === 1 && w === 1 ? result[0][0] : result;
  }
  
  return array.slice(rows, rows + h);
}

function ROW(rowIndex) {
  return rowIndex !== undefined ? rowIndex : 1;
}

function COLUMN(colIndex) {
  return colIndex !== undefined ? colIndex : 1;
}

function ROWS(array) {
  if (!Array.isArray(array)) return 1;
  return array.length;
}

function COLUMNS(array) {
  if (!Array.isArray(array)) return 1;
  if (!Array.isArray(array[0])) return array.length;
  return array[0].length;
}

function TRANSPOSE(array) {
  if (!Array.isArray(array)) return array;
  if (!Array.isArray(array[0])) {
    // 1D array - make it a column
    return array.map(v => [v]);
  }
  
  const rows = array.length;
  const cols = array[0].length;
  const result = [];
  
  for (let j = 0; j < cols; j++) {
    const newRow = [];
    for (let i = 0; i < rows; i++) {
      newRow.push(array[i][j]);
    }
    result.push(newRow);
  }
  
  return result;
}

function SORT(array, sortIndex = 1, sortOrder = 1, byCol = false) {
  if (!Array.isArray(array)) return array;
  
  let data = [...array];
  
  if (byCol) {
    data = TRANSPOSE(data);
  }
  
  const is2D = Array.isArray(data[0]);
  
  data.sort((a, b) => {
    const aVal = is2D ? a[sortIndex - 1] : a;
    const bVal = is2D ? b[sortIndex - 1] : b;
    
    if (aVal < bVal) return -1 * sortOrder;
    if (aVal > bVal) return 1 * sortOrder;
    return 0;
  });
  
  return byCol ? TRANSPOSE(data) : data;
}

function FILTER(array, include, ifEmpty) {
  if (!Array.isArray(array)) return array;
  
  const incl = Array.isArray(include) ? include.flat() : [include];
  const result = [];
  
  for (let i = 0; i < array.length; i++) {
    if (incl[i]) {
      result.push(array[i]);
    }
  }
  
  if (result.length === 0) {
    if (ifEmpty !== undefined) return ifEmpty;
    throw new Error('#CALC! - No data returned');
  }
  
  return result;
}

function UNIQUE(array, byCol = false, exactlyOnce = false) {
  if (!Array.isArray(array)) return [array];
  
  let data = byCol ? TRANSPOSE(array) : array;
  const seen = new Map();
  
  for (const item of data) {
    const key = JSON.stringify(item);
    seen.set(key, (seen.get(key) || 0) + 1);
  }
  
  let result;
  if (exactlyOnce) {
    result = data.filter(item => seen.get(JSON.stringify(item)) === 1);
  } else {
    const uniqueKeys = new Set();
    result = data.filter(item => {
      const key = JSON.stringify(item);
      if (uniqueKeys.has(key)) return false;
      uniqueKeys.add(key);
      return true;
    });
  }
  
  return byCol ? TRANSPOSE(result) : result;
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  // Math & Statistics
  SUM, AVERAGE, COUNT, COUNTA, COUNTBLANK, COUNTIF, COUNTIFS,
  MAX, MIN, MEDIAN, MODE, STDEV, STDEVP, VAR, VARP,
  SUMIF, SUMIFS, AVERAGEIF,
  ROUND, ROUNDUP, ROUNDDOWN, CEILING, FLOOR, TRUNC, INT,
  ABS, SIGN, SQRT, POWER, EXP, LN, LOG, LOG10,
  MOD, QUOTIENT, PRODUCT, SUMPRODUCT,
  GCD, LCM, FACT, COMBIN, PERMUT,
  RAND, RANDBETWEEN, PI,
  SIN, COS, TAN, ASIN, ACOS, ATAN, ATAN2,
  DEGREES, RADIANS,
  LARGE, SMALL, RANK, PERCENTILE, QUARTILE,
  
  // Logical
  IF, IFS, SWITCH, AND, OR, NOT, XOR,
  IFERROR, IFNA,
  ISBLANK, ISNUMBER, ISTEXT, ISLOGICAL, ISERROR, ISEVEN, ISODD,
  TRUE, FALSE,
  
  // Text
  LEFT, RIGHT, MID, LEN, FIND, SEARCH,
  CONCAT, CONCATENATE, TEXTJOIN,
  TRIM, CLEAN, UPPER, LOWER, PROPER,
  SUBSTITUTE, REPLACE, REPT,
  TEXT, VALUE, FIXED, DOLLAR,
  CHAR, CODE, EXACT,
  TEXTSPLIT, TEXTBEFORE, TEXTAFTER,
  
  // Date/Time
  TODAY, NOW, DATE, DATEVALUE, TIME, TIMEVALUE,
  YEAR, MONTH, DAY, HOUR, MINUTE, SECOND,
  WEEKDAY, WEEKNUM, ISOWEEKNUM,
  DATEDIF, DAYS, DAYS360,
  EDATE, EOMONTH, WORKDAY, NETWORKDAYS, YEARFRAC,
  
  // Financial
  PMT, PPMT, IPMT, CUMIPMT, CUMPRINC,
  PV, FV, NPV, XNPV,
  IRR, XIRR, MIRR, RATE, NPER,
  EFFECT, NOMINAL,
  SLN, SYD, DB, DDB,
  
  // Lookup & Reference
  VLOOKUP, HLOOKUP, XLOOKUP,
  INDEX, MATCH, XMATCH,
  CHOOSE, LOOKUP, OFFSET,
  ROW, COLUMN, ROWS, COLUMNS,
  TRANSPOSE, SORT, FILTER, UNIQUE
};
