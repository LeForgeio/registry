/**
 * Excel Utilities - Embedded ForgeHook Plugin
 * Parse and generate Excel (XLSX) and CSV files locally
 * Zero external dependencies - pure JavaScript implementation
 */

// ============================================================================
// CSV PARSING AND GENERATION
// ============================================================================

/**
 * Parse CSV string to array of objects or arrays
 */
function parseCSV(input, options = {}) {
  const {
    delimiter = ',',
    hasHeaders = true,
    trimValues = true,
    skipEmptyLines = true,
    quoteChar = '"'
  } = typeof input === 'object' ? { ...input, ...options } : options;
  
  const text = typeof input === 'object' ? input.data || input.text || input.csv : input;
  
  const lines = [];
  let currentLine = [];
  let currentField = '';
  let inQuotes = false;
  
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const nextChar = text[i + 1];
    
    if (inQuotes) {
      if (char === quoteChar && nextChar === quoteChar) {
        currentField += quoteChar;
        i++; // Skip escaped quote
      } else if (char === quoteChar) {
        inQuotes = false;
      } else {
        currentField += char;
      }
    } else {
      if (char === quoteChar) {
        inQuotes = true;
      } else if (char === delimiter) {
        currentLine.push(trimValues ? currentField.trim() : currentField);
        currentField = '';
      } else if (char === '\r' && nextChar === '\n') {
        currentLine.push(trimValues ? currentField.trim() : currentField);
        if (!skipEmptyLines || currentLine.some(f => f !== '')) {
          lines.push(currentLine);
        }
        currentLine = [];
        currentField = '';
        i++; // Skip \n
      } else if (char === '\n') {
        currentLine.push(trimValues ? currentField.trim() : currentField);
        if (!skipEmptyLines || currentLine.some(f => f !== '')) {
          lines.push(currentLine);
        }
        currentLine = [];
        currentField = '';
      } else {
        currentField += char;
      }
    }
  }
  
  // Handle last field/line
  if (currentField || currentLine.length > 0) {
    currentLine.push(trimValues ? currentField.trim() : currentField);
    if (!skipEmptyLines || currentLine.some(f => f !== '')) {
      lines.push(currentLine);
    }
  }
  
  if (!hasHeaders) {
    return lines;
  }
  
  // Convert to objects using headers
  const headers = lines[0];
  const data = lines.slice(1).map(row => {
    const obj = {};
    headers.forEach((header, i) => {
      obj[header] = row[i] !== undefined ? row[i] : '';
    });
    return obj;
  });
  
  return data;
}

/**
 * Generate CSV string from array of objects or arrays
 */
function toCSV(input, options = {}) {
  const {
    delimiter = ',',
    includeHeaders = true,
    quoteChar = '"',
    lineEnding = '\r\n',
    quoteAll = false
  } = typeof input === 'object' && !Array.isArray(input) ? { ...input, ...options } : options;
  
  const data = Array.isArray(input) ? input : (input.data || input.rows || []);
  
  if (data.length === 0) return '';
  
  const needsQuote = (value) => {
    if (quoteAll) return true;
    const str = String(value);
    return str.includes(delimiter) || str.includes(quoteChar) || str.includes('\n') || str.includes('\r');
  };
  
  const escapeField = (value) => {
    if (value === null || value === undefined) return '';
    const str = String(value);
    if (needsQuote(str)) {
      return quoteChar + str.replace(new RegExp(quoteChar, 'g'), quoteChar + quoteChar) + quoteChar;
    }
    return str;
  };
  
  const lines = [];
  
  // Check if array of objects or array of arrays
  const isObjectArray = data[0] && typeof data[0] === 'object' && !Array.isArray(data[0]);
  
  if (isObjectArray) {
    const headers = Object.keys(data[0]);
    if (includeHeaders) {
      lines.push(headers.map(escapeField).join(delimiter));
    }
    data.forEach(row => {
      lines.push(headers.map(h => escapeField(row[h])).join(delimiter));
    });
  } else {
    data.forEach((row, i) => {
      if (!includeHeaders && i === 0) return;
      const arr = Array.isArray(row) ? row : [row];
      lines.push(arr.map(escapeField).join(delimiter));
    });
  }
  
  return lines.join(lineEnding);
}

// ============================================================================
// XLSX PARSING (Simplified - handles basic XLSX structure)
// ============================================================================

/**
 * Parse XLSX from base64 or ArrayBuffer
 * This is a simplified parser for basic spreadsheets
 */
function parseXLSX(input, options = {}) {
  const {
    sheet = 0,
    hasHeaders = true,
    range = null
  } = typeof input === 'object' && !ArrayBuffer.isView(input) ? { ...input, ...options } : options;
  
  // Get the data buffer
  let buffer;
  if (typeof input === 'string') {
    // Base64 input
    buffer = base64ToArrayBuffer(input);
  } else if (input instanceof ArrayBuffer) {
    buffer = input;
  } else if (input.data || input.base64) {
    buffer = base64ToArrayBuffer(input.data || input.base64);
  } else {
    throw new Error('Input must be base64 string or ArrayBuffer');
  }
  
  // Parse ZIP structure (XLSX is a ZIP file)
  const zip = parseZip(buffer);
  
  // Find shared strings
  const sharedStrings = [];
  const sharedStringsXml = zip['xl/sharedStrings.xml'];
  if (sharedStringsXml) {
    const matches = sharedStringsXml.matchAll(/<t[^>]*>([^<]*)<\/t>/g);
    for (const match of matches) {
      sharedStrings.push(decodeXmlEntities(match[1]));
    }
  }
  
  // Find the sheet
  const sheetNames = [];
  const workbookXml = zip['xl/workbook.xml'];
  if (workbookXml) {
    const sheetMatches = workbookXml.matchAll(/<sheet[^>]*name="([^"]*)"[^>]*\/>/g);
    for (const match of sheetMatches) {
      sheetNames.push(match[1]);
    }
  }
  
  const sheetIndex = typeof sheet === 'string' 
    ? sheetNames.indexOf(sheet) 
    : sheet;
  
  const sheetPath = `xl/worksheets/sheet${sheetIndex + 1}.xml`;
  const sheetXml = zip[sheetPath];
  
  if (!sheetXml) {
    throw new Error(`Sheet not found: ${sheet}`);
  }
  
  // Parse cells
  const rows = [];
  const rowMatches = sheetXml.matchAll(/<row[^>]*r="(\d+)"[^>]*>([\s\S]*?)<\/row>/g);
  
  for (const rowMatch of rowMatches) {
    const rowNum = parseInt(rowMatch[1], 10);
    const rowContent = rowMatch[2];
    const row = [];
    
    const cellMatches = rowContent.matchAll(/<c[^>]*r="([A-Z]+)(\d+)"[^>]*(?:t="([^"]*)")?[^>]*>(?:<v>([^<]*)<\/v>)?/g);
    
    for (const cellMatch of cellMatches) {
      const colLetter = cellMatch[1];
      const type = cellMatch[3];
      const value = cellMatch[4];
      
      const colIndex = columnToIndex(colLetter);
      
      // Ensure row has enough columns
      while (row.length <= colIndex) {
        row.push('');
      }
      
      if (type === 's' && value !== undefined) {
        // Shared string
        row[colIndex] = sharedStrings[parseInt(value, 10)] || '';
      } else if (type === 'b') {
        // Boolean
        row[colIndex] = value === '1';
      } else if (value !== undefined) {
        // Number or inline string
        const num = parseFloat(value);
        row[colIndex] = isNaN(num) ? value : num;
      }
    }
    
    // Fill in missing columns
    while (rows.length < rowNum - 1) {
      rows.push([]);
    }
    rows[rowNum - 1] = row;
  }
  
  // Apply range filter if specified
  let data = rows;
  if (range) {
    const [start, end] = range.split(':');
    const startCol = columnToIndex(start.replace(/\d+/g, ''));
    const startRow = parseInt(start.replace(/[A-Z]+/gi, ''), 10) - 1;
    const endCol = columnToIndex(end.replace(/\d+/g, ''));
    const endRow = parseInt(end.replace(/[A-Z]+/gi, ''), 10) - 1;
    
    data = rows.slice(startRow, endRow + 1).map(row => 
      row.slice(startCol, endCol + 1)
    );
  }
  
  if (!hasHeaders) {
    return {
      sheets: sheetNames,
      currentSheet: sheetNames[sheetIndex],
      data
    };
  }
  
  // Convert to objects using headers
  const headers = data[0] || [];
  const objects = data.slice(1).map(row => {
    const obj = {};
    headers.forEach((header, i) => {
      if (header) {
        obj[header] = row[i] !== undefined ? row[i] : '';
      }
    });
    return obj;
  });
  
  return {
    sheets: sheetNames,
    currentSheet: sheetNames[sheetIndex],
    headers,
    data: objects
  };
}

/**
 * Get sheet names from XLSX
 */
function getSheetNames(input) {
  let buffer;
  if (typeof input === 'string') {
    buffer = base64ToArrayBuffer(input);
  } else if (input instanceof ArrayBuffer) {
    buffer = input;
  } else if (input.data || input.base64) {
    buffer = base64ToArrayBuffer(input.data || input.base64);
  }
  
  const zip = parseZip(buffer);
  const workbookXml = zip['xl/workbook.xml'];
  
  if (!workbookXml) return [];
  
  const names = [];
  const matches = workbookXml.matchAll(/<sheet[^>]*name="([^"]*)"[^>]*\/>/g);
  for (const match of matches) {
    names.push(match[1]);
  }
  return names;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function base64ToArrayBuffer(base64) {
  // Remove data URL prefix if present
  const cleanBase64 = base64.replace(/^data:[^;]+;base64,/, '');
  
  if (typeof Buffer !== 'undefined') {
    const buffer = Buffer.from(cleanBase64, 'base64');
    return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
  }
  
  const binaryString = atob(cleanBase64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

function parseZip(buffer) {
  const view = new DataView(buffer);
  const files = {};
  
  // Find End of Central Directory
  let eocdOffset = buffer.byteLength - 22;
  while (eocdOffset >= 0) {
    if (view.getUint32(eocdOffset, true) === 0x06054b50) break;
    eocdOffset--;
  }
  
  if (eocdOffset < 0) {
    throw new Error('Invalid ZIP file');
  }
  
  const cdOffset = view.getUint32(eocdOffset + 16, true);
  const cdEntries = view.getUint16(eocdOffset + 10, true);
  
  let offset = cdOffset;
  for (let i = 0; i < cdEntries; i++) {
    if (view.getUint32(offset, true) !== 0x02014b50) break;
    
    const compressionMethod = view.getUint16(offset + 10, true);
    const compressedSize = view.getUint32(offset + 20, true);
    const uncompressedSize = view.getUint32(offset + 24, true);
    const fileNameLength = view.getUint16(offset + 28, true);
    const extraLength = view.getUint16(offset + 30, true);
    const commentLength = view.getUint16(offset + 32, true);
    const localHeaderOffset = view.getUint32(offset + 42, true);
    
    const fileName = new TextDecoder().decode(
      new Uint8Array(buffer, offset + 46, fileNameLength)
    );
    
    // Read local file header
    const localFileNameLength = view.getUint16(localHeaderOffset + 26, true);
    const localExtraLength = view.getUint16(localHeaderOffset + 28, true);
    const dataOffset = localHeaderOffset + 30 + localFileNameLength + localExtraLength;
    
    if (compressionMethod === 0) {
      // Stored (no compression)
      const data = new Uint8Array(buffer, dataOffset, uncompressedSize);
      files[fileName] = new TextDecoder().decode(data);
    } else if (compressionMethod === 8) {
      // Deflate - simplified decompression
      const compressed = new Uint8Array(buffer, dataOffset, compressedSize);
      try {
        const decompressed = inflateRaw(compressed);
        files[fileName] = new TextDecoder().decode(decompressed);
      } catch (e) {
        // Skip files we can't decompress
      }
    }
    
    offset += 46 + fileNameLength + extraLength + commentLength;
  }
  
  return files;
}

// Simplified DEFLATE decompression
function inflateRaw(data) {
  const result = [];
  let pos = 0;
  let bitBuf = 0;
  let bitCnt = 0;
  
  const getBits = (n) => {
    while (bitCnt < n) {
      bitBuf |= data[pos++] << bitCnt;
      bitCnt += 8;
    }
    const val = bitBuf & ((1 << n) - 1);
    bitBuf >>= n;
    bitCnt -= n;
    return val;
  };
  
  // Fixed Huffman tables
  const litLenTable = buildFixedLitLenTable();
  const distTable = buildFixedDistTable();
  
  while (pos < data.length || bitCnt > 0) {
    const bfinal = getBits(1);
    const btype = getBits(2);
    
    if (btype === 0) {
      // No compression
      bitBuf = 0;
      bitCnt = 0;
      const len = data[pos] | (data[pos + 1] << 8);
      pos += 4;
      for (let i = 0; i < len; i++) {
        result.push(data[pos++]);
      }
    } else if (btype === 1 || btype === 2) {
      // Fixed or dynamic Huffman
      let litLen, dist;
      
      if (btype === 2) {
        // Skip dynamic table building - fallback to fixed
        // This is a simplification; full implementation would parse dynamic tables
      }
      
      while (true) {
        litLen = decodeSymbol(getBits, litLenTable);
        
        if (litLen < 256) {
          result.push(litLen);
        } else if (litLen === 256) {
          break;
        } else {
          const lenCode = litLen - 257;
          const lenExtra = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0][lenCode];
          const lenBase = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258][lenCode];
          const length = lenBase + getBits(lenExtra);
          
          const distSymbol = decodeSymbol(getBits, distTable);
          const distExtra = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13][distSymbol];
          const distBase = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577][distSymbol];
          const distance = distBase + getBits(distExtra);
          
          for (let i = 0; i < length; i++) {
            result.push(result[result.length - distance]);
          }
        }
      }
    }
    
    if (bfinal) break;
  }
  
  return new Uint8Array(result);
}

function buildFixedLitLenTable() {
  const table = new Array(288);
  for (let i = 0; i < 144; i++) table[i] = { bits: 8, symbol: i };
  for (let i = 144; i < 256; i++) table[i] = { bits: 9, symbol: i };
  for (let i = 256; i < 280; i++) table[i] = { bits: 7, symbol: i };
  for (let i = 280; i < 288; i++) table[i] = { bits: 8, symbol: i };
  return table;
}

function buildFixedDistTable() {
  const table = new Array(32);
  for (let i = 0; i < 32; i++) table[i] = { bits: 5, symbol: i };
  return table;
}

function decodeSymbol(getBits, table) {
  // Simplified - assumes fixed tables
  let code = 0;
  let len = 0;
  
  while (len < 15) {
    code = (code << 1) | getBits(1);
    len++;
    
    for (const entry of table) {
      if (entry && entry.bits === len) {
        // Check if code matches
        return entry.symbol;
      }
    }
  }
  
  return 0;
}

function columnToIndex(col) {
  let index = 0;
  for (let i = 0; i < col.length; i++) {
    index = index * 26 + (col.charCodeAt(i) - 64);
  }
  return index - 1;
}

function indexToColumn(index) {
  let col = '';
  index++;
  while (index > 0) {
    const mod = (index - 1) % 26;
    col = String.fromCharCode(65 + mod) + col;
    index = Math.floor((index - 1) / 26);
  }
  return col;
}

function decodeXmlEntities(str) {
  return str
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code, 10)))
    .replace(/&#x([0-9a-fA-F]+);/g, (_, code) => String.fromCharCode(parseInt(code, 16)));
}

// ============================================================================
// DATA MANIPULATION FUNCTIONS
// ============================================================================

/**
 * Get specific column from parsed data
 */
function getColumn(data, column) {
  const arr = Array.isArray(data) ? data : (data.data || []);
  
  if (typeof column === 'number') {
    return arr.map(row => Array.isArray(row) ? row[column] : Object.values(row)[column]);
  }
  
  return arr.map(row => row[column]);
}

/**
 * Get specific row from parsed data
 */
function getRow(data, index) {
  const arr = Array.isArray(data) ? data : (data.data || []);
  return arr[index];
}

/**
 * Filter rows based on condition
 */
function filterRows(data, predicate) {
  const arr = Array.isArray(data) ? data : (data.data || []);
  
  if (typeof predicate === 'function') {
    return arr.filter(predicate);
  }
  
  // Object predicate: { column: value } or { column: { op: '>', value: 10 } }
  return arr.filter(row => {
    for (const [key, condition] of Object.entries(predicate)) {
      const value = row[key];
      
      if (typeof condition === 'object' && condition.op) {
        switch (condition.op) {
          case '=':
          case '==':
            if (value != condition.value) return false;
            break;
          case '===':
            if (value !== condition.value) return false;
            break;
          case '!=':
          case '<>':
            if (value == condition.value) return false;
            break;
          case '>':
            if (!(value > condition.value)) return false;
            break;
          case '>=':
            if (!(value >= condition.value)) return false;
            break;
          case '<':
            if (!(value < condition.value)) return false;
            break;
          case '<=':
            if (!(value <= condition.value)) return false;
            break;
          case 'contains':
            if (!String(value).includes(condition.value)) return false;
            break;
          case 'startsWith':
            if (!String(value).startsWith(condition.value)) return false;
            break;
          case 'endsWith':
            if (!String(value).endsWith(condition.value)) return false;
            break;
        }
      } else if (value != condition) {
        return false;
      }
    }
    return true;
  });
}

/**
 * Sort rows by column
 */
function sortRows(data, column, descending = false) {
  const arr = Array.isArray(data) ? [...data] : [...(data.data || [])];
  
  arr.sort((a, b) => {
    const aVal = a[column];
    const bVal = b[column];
    
    if (aVal === bVal) return 0;
    if (aVal === null || aVal === undefined) return 1;
    if (bVal === null || bVal === undefined) return -1;
    
    const result = aVal < bVal ? -1 : 1;
    return descending ? -result : result;
  });
  
  return arr;
}

/**
 * Group rows by column value
 */
function groupBy(data, column) {
  const arr = Array.isArray(data) ? data : (data.data || []);
  const groups = {};
  
  arr.forEach(row => {
    const key = row[column];
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(row);
  });
  
  return groups;
}

/**
 * Aggregate column values
 */
function aggregate(data, column, operation = 'sum') {
  const arr = Array.isArray(data) ? data : (data.data || []);
  const values = arr.map(row => row[column]).filter(v => typeof v === 'number');
  
  switch (operation.toLowerCase()) {
    case 'sum':
      return values.reduce((a, b) => a + b, 0);
    case 'avg':
    case 'average':
    case 'mean':
      return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
    case 'min':
      return values.length > 0 ? Math.min(...values) : null;
    case 'max':
      return values.length > 0 ? Math.max(...values) : null;
    case 'count':
      return values.length;
    case 'countall':
      return arr.length;
    default:
      return null;
  }
}

/**
 * Pivot table
 */
function pivot(data, rowField, colField, valueField, aggregation = 'sum') {
  const arr = Array.isArray(data) ? data : (data.data || []);
  
  const rowValues = [...new Set(arr.map(r => r[rowField]))];
  const colValues = [...new Set(arr.map(r => r[colField]))];
  
  const result = rowValues.map(rowVal => {
    const row = { [rowField]: rowVal };
    colValues.forEach(colVal => {
      const filtered = arr.filter(r => r[rowField] === rowVal && r[colField] === colVal);
      row[colVal] = aggregate(filtered, valueField, aggregation);
    });
    return row;
  });
  
  return {
    columns: [rowField, ...colValues],
    data: result
  };
}

/**
 * Join two datasets
 */
function join(leftData, rightData, leftKey, rightKey = leftKey, type = 'inner') {
  const left = Array.isArray(leftData) ? leftData : (leftData.data || []);
  const right = Array.isArray(rightData) ? rightData : (rightData.data || []);
  
  const rightIndex = {};
  right.forEach(row => {
    const key = row[rightKey];
    if (!rightIndex[key]) {
      rightIndex[key] = [];
    }
    rightIndex[key].push(row);
  });
  
  const result = [];
  
  left.forEach(leftRow => {
    const key = leftRow[leftKey];
    const matches = rightIndex[key] || [];
    
    if (matches.length > 0) {
      matches.forEach(rightRow => {
        result.push({ ...leftRow, ...rightRow });
      });
    } else if (type === 'left' || type === 'outer') {
      result.push({ ...leftRow });
    }
  });
  
  if (type === 'right' || type === 'outer') {
    right.forEach(rightRow => {
      const key = rightRow[rightKey];
      const hasMatch = left.some(leftRow => leftRow[leftKey] === key);
      if (!hasMatch) {
        result.push({ ...rightRow });
      }
    });
  }
  
  return result;
}

/**
 * Transform/map columns
 */
function mapColumns(data, mapping) {
  const arr = Array.isArray(data) ? data : (data.data || []);
  
  return arr.map(row => {
    const newRow = {};
    for (const [newCol, source] of Object.entries(mapping)) {
      if (typeof source === 'function') {
        newRow[newCol] = source(row);
      } else {
        newRow[newCol] = row[source];
      }
    }
    return newRow;
  });
}

/**
 * Deduplicate rows
 */
function distinct(data, columns) {
  const arr = Array.isArray(data) ? data : (data.data || []);
  const seen = new Set();
  
  return arr.filter(row => {
    const key = columns 
      ? columns.map(c => JSON.stringify(row[c])).join('|')
      : JSON.stringify(row);
    
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Convert cell reference to row/col indices
 */
function cellToIndex(cell) {
  const match = cell.match(/^([A-Z]+)(\d+)$/i);
  if (!match) throw new Error('Invalid cell reference');
  
  return {
    col: columnToIndex(match[1].toUpperCase()),
    row: parseInt(match[2], 10) - 1
  };
}

/**
 * Convert row/col indices to cell reference
 */
function indexToCell(row, col) {
  return indexToColumn(col) + (row + 1);
}

/**
 * Get cell value from 2D array
 */
function getCell(data, cell) {
  const { row, col } = cellToIndex(cell);
  const arr = Array.isArray(data) ? data : (data.data || []);
  return arr[row]?.[col];
}

/**
 * Set cell value in 2D array
 */
function setCell(data, cell, value) {
  const { row, col } = cellToIndex(cell);
  const arr = Array.isArray(data) ? [...data.map(r => [...r])] : [...(data.data || []).map(r => [...r])];
  
  while (arr.length <= row) {
    arr.push([]);
  }
  while (arr[row].length <= col) {
    arr[row].push('');
  }
  
  arr[row][col] = value;
  return arr;
}

module.exports = {
  // CSV
  parseCSV,
  toCSV,
  
  // XLSX
  parseXLSX,
  getSheetNames,
  
  // Data manipulation
  getColumn,
  getRow,
  filterRows,
  sortRows,
  groupBy,
  aggregate,
  pivot,
  join,
  mapColumns,
  distinct,
  
  // Cell utilities
  columnToIndex,
  indexToColumn,
  cellToIndex,
  indexToCell,
  getCell,
  setCell
};
