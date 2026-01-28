/**
 * QR Code Utilities - Embedded ForgeHook Plugin
 * Generate QR codes and barcodes locally without external APIs
 * Pure JavaScript implementation
 */

// ============================================================================
// QR CODE GENERATION
// ============================================================================

// QR Code error correction levels
const EC_LEVELS = { L: 0, M: 1, Q: 2, H: 3 };

// QR Code version capacities (for alphanumeric mode, EC level M)
const QR_CAPACITIES = [
  0, 25, 47, 77, 114, 154, 195, 224, 279, 335, 395,
  458, 523, 586, 644, 718, 792, 858, 929, 1003, 1091
];

// Mode indicators
const MODE = {
  NUMERIC: 0b0001,
  ALPHANUMERIC: 0b0010,
  BYTE: 0b0100,
  KANJI: 0b1000,
  ECI: 0b0111
};

// Alphanumeric character set
const ALPHANUM = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:';

/**
 * Generate QR code as 2D array of modules (true = black, false = white)
 */
function generateQRMatrix(input, options = {}) {
  const {
    errorCorrection = 'M',
    version = 'auto',
    mask = 'auto'
  } = typeof input === 'object' ? { ...input, ...options } : options;
  
  const data = typeof input === 'object' ? (input.data || input.text || input.content) : input;
  
  if (!data) {
    throw new Error('No data provided for QR code');
  }
  
  // Determine best mode
  const mode = detectMode(data);
  
  // Determine version (size)
  const ecLevel = EC_LEVELS[errorCorrection.toUpperCase()] ?? EC_LEVELS.M;
  const ver = version === 'auto' ? findVersion(data, mode, ecLevel) : version;
  
  if (ver > 40) {
    throw new Error('Data too large for QR code');
  }
  
  // Encode data
  const encoded = encodeData(data, mode, ver, ecLevel);
  
  // Create matrix
  const size = ver * 4 + 17;
  const matrix = createMatrix(size);
  
  // Place patterns
  placeFunctionPatterns(matrix, ver);
  
  // Place data
  placeData(matrix, encoded);
  
  // Apply mask
  const bestMask = mask === 'auto' ? findBestMask(matrix) : mask;
  applyMask(matrix, bestMask);
  
  // Place format info
  placeFormatInfo(matrix, ecLevel, bestMask);
  
  if (ver >= 7) {
    placeVersionInfo(matrix, ver);
  }
  
  return {
    matrix: matrix.map(row => row.map(cell => cell === 1)),
    version: ver,
    size,
    errorCorrection: Object.keys(EC_LEVELS)[ecLevel]
  };
}

/**
 * Generate QR code as SVG string
 */
function generateQRSvg(input, options = {}) {
  const {
    size = 200,
    margin = 4,
    darkColor = '#000000',
    lightColor = '#ffffff',
    errorCorrection = 'M'
  } = typeof input === 'object' ? { ...input, ...options } : options;
  
  const data = typeof input === 'object' ? (input.data || input.text || input.content) : input;
  const qr = generateQRMatrix(data, { errorCorrection });
  
  const moduleCount = qr.size;
  const moduleSize = size / (moduleCount + margin * 2);
  const offset = margin * moduleSize;
  
  let paths = '';
  
  for (let y = 0; y < moduleCount; y++) {
    for (let x = 0; x < moduleCount; x++) {
      if (qr.matrix[y][x]) {
        paths += `M${offset + x * moduleSize},${offset + y * moduleSize}h${moduleSize}v${moduleSize}h-${moduleSize}z`;
      }
    }
  }
  
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}">
  <rect width="100%" height="100%" fill="${lightColor}"/>
  <path d="${paths}" fill="${darkColor}"/>
</svg>`;
}

/**
 * Generate QR code as Data URL (PNG via canvas or SVG base64)
 */
function generateQRDataUrl(input, options = {}) {
  const svg = generateQRSvg(input, options);
  const base64 = typeof Buffer !== 'undefined' 
    ? Buffer.from(svg).toString('base64')
    : btoa(unescape(encodeURIComponent(svg)));
  return `data:image/svg+xml;base64,${base64}`;
}

/**
 * Generate QR code as ASCII art
 */
function generateQRAscii(input, options = {}) {
  const {
    darkChar = '██',
    lightChar = '  ',
    errorCorrection = 'M'
  } = typeof input === 'object' ? { ...input, ...options } : options;
  
  const data = typeof input === 'object' ? (input.data || input.text || input.content) : input;
  const qr = generateQRMatrix(data, { errorCorrection });
  
  return qr.matrix.map(row => 
    row.map(cell => cell ? darkChar : lightChar).join('')
  ).join('\n');
}

// ============================================================================
// BARCODE GENERATION (Code 128, Code 39, EAN-13, UPC-A)
// ============================================================================

// Code 128 character sets
const CODE128_B = {
  ' ': 0, '!': 1, '"': 2, '#': 3, '$': 4, '%': 5, '&': 6, "'": 7,
  '(': 8, ')': 9, '*': 10, '+': 11, ',': 12, '-': 13, '.': 14, '/': 15,
  '0': 16, '1': 17, '2': 18, '3': 19, '4': 20, '5': 21, '6': 22, '7': 23,
  '8': 24, '9': 25, ':': 26, ';': 27, '<': 28, '=': 29, '>': 30, '?': 31,
  '@': 32, 'A': 33, 'B': 34, 'C': 35, 'D': 36, 'E': 37, 'F': 38, 'G': 39,
  'H': 40, 'I': 41, 'J': 42, 'K': 43, 'L': 44, 'M': 45, 'N': 46, 'O': 47,
  'P': 48, 'Q': 49, 'R': 50, 'S': 51, 'T': 52, 'U': 53, 'V': 54, 'W': 55,
  'X': 56, 'Y': 57, 'Z': 58, '[': 59, '\\': 60, ']': 61, '^': 62, '_': 63,
  '`': 64, 'a': 65, 'b': 66, 'c': 67, 'd': 68, 'e': 69, 'f': 70, 'g': 71,
  'h': 72, 'i': 73, 'j': 74, 'k': 75, 'l': 76, 'm': 77, 'n': 78, 'o': 79,
  'p': 80, 'q': 81, 'r': 82, 's': 83, 't': 84, 'u': 85, 'v': 86, 'w': 87,
  'x': 88, 'y': 89, 'z': 90, '{': 91, '|': 92, '}': 93, '~': 94
};

const CODE128_PATTERNS = [
  '11011001100', '11001101100', '11001100110', '10010011000', '10010001100',
  '10001001100', '10011001000', '10011000100', '10001100100', '11001001000',
  '11001000100', '11000100100', '10110011100', '10011011100', '10011001110',
  '10111001100', '10011101100', '10011100110', '11001110010', '11001011100',
  '11001001110', '11011100100', '11001110100', '11101101110', '11101001100',
  '11100101100', '11100100110', '11101100100', '11100110100', '11100110010',
  '11011011000', '11011000110', '11000110110', '10100011000', '10001011000',
  '10001000110', '10110001000', '10001101000', '10001100010', '11010001000',
  '11000101000', '11000100010', '10110111000', '10110001110', '10001101110',
  '10111011000', '10111000110', '10001110110', '11101110110', '11010001110',
  '11000101110', '11011101000', '11011100010', '11011101110', '11101011000',
  '11101000110', '11100010110', '11101101000', '11101100010', '11100011010',
  '11101111010', '11001000010', '11110001010', '10100110000', '10100001100',
  '10010110000', '10010000110', '10000101100', '10000100110', '10110010000',
  '10110000100', '10011010000', '10011000010', '10000110100', '10000110010',
  '11000010010', '11001010000', '11110111010', '11000010100', '10001111010',
  '10100111100', '10010111100', '10010011110', '10111100100', '10011110100',
  '10011110010', '11110100100', '11110010100', '11110010010', '11011011110',
  '11011110110', '11110110110', '10101111000', '10100011110', '10001011110',
  '10111101000', '10111100010', '11110101000', '11110100010', '10111011110',
  '10111101110', '11101011110', '11110101110', '11010000100', '11010010000',
  '11010011100', '11000111010'
];

/**
 * Generate Code 128 barcode as array of bar widths
 */
function generateCode128(input, options = {}) {
  const data = typeof input === 'object' ? (input.data || input.text || input.code) : input;
  
  // Start with Code B
  const codes = [104]; // Start B
  let checksum = 104;
  
  for (let i = 0; i < data.length; i++) {
    const char = data[i];
    const code = CODE128_B[char];
    if (code === undefined) {
      throw new Error(`Invalid character for Code 128: ${char}`);
    }
    codes.push(code);
    checksum += code * (i + 1);
  }
  
  checksum = checksum % 103;
  codes.push(checksum);
  codes.push(106); // Stop
  
  const pattern = codes.map(c => CODE128_PATTERNS[c]).join('');
  
  return {
    pattern,
    codes,
    data,
    type: 'Code128'
  };
}

// Code 39 patterns
const CODE39_PATTERNS = {
  '0': '101001101101', '1': '110100101011', '2': '101100101011', '3': '110110010101',
  '4': '101001101011', '5': '110100110101', '6': '101100110101', '7': '101001011011',
  '8': '110100101101', '9': '101100101101', 'A': '110101001011', 'B': '101101001011',
  'C': '110110100101', 'D': '101011001011', 'E': '110101100101', 'F': '101101100101',
  'G': '101010011011', 'H': '110101001101', 'I': '101101001101', 'J': '101011001101',
  'K': '110101010011', 'L': '101101010011', 'M': '110110101001', 'N': '101011010011',
  'O': '110101101001', 'P': '101101101001', 'Q': '101010110011', 'R': '110101011001',
  'S': '101101011001', 'T': '101011011001', 'U': '110010101011', 'V': '100110101011',
  'W': '110011010101', 'X': '100101101011', 'Y': '110010110101', 'Z': '100110110101',
  '-': '100101011011', '.': '110010101101', ' ': '100110101101', '$': '100100100101',
  '/': '100100101001', '+': '100101001001', '%': '101001001001', '*': '100101101101'
};

/**
 * Generate Code 39 barcode
 */
function generateCode39(input, options = {}) {
  const data = typeof input === 'object' ? (input.data || input.text || input.code) : input;
  const upperData = data.toUpperCase();
  
  // Validate characters
  for (const char of upperData) {
    if (!CODE39_PATTERNS[char]) {
      throw new Error(`Invalid character for Code 39: ${char}`);
    }
  }
  
  // Add start/stop characters
  const fullData = '*' + upperData + '*';
  const pattern = fullData.split('').map(c => CODE39_PATTERNS[c]).join('0');
  
  return {
    pattern,
    data: upperData,
    type: 'Code39'
  };
}

// EAN/UPC patterns
const EAN_L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011'];
const EAN_G = ['0100111', '0110011', '0011011', '0100001', '0011101', '0111001', '0000101', '0010001', '0001001', '0010111'];
const EAN_R = ['1110010', '1100110', '1101100', '1000010', '1011100', '1001110', '1010000', '1000100', '1001000', '1110100'];
const EAN_PARITY = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL'];

/**
 * Generate EAN-13 barcode
 */
function generateEAN13(input, options = {}) {
  let data = typeof input === 'object' ? (input.data || input.code || input.ean) : input;
  data = data.replace(/\D/g, '');
  
  if (data.length === 12) {
    // Calculate check digit
    let sum = 0;
    for (let i = 0; i < 12; i++) {
      sum += parseInt(data[i], 10) * (i % 2 === 0 ? 1 : 3);
    }
    data += (10 - (sum % 10)) % 10;
  }
  
  if (data.length !== 13) {
    throw new Error('EAN-13 must be 12 or 13 digits');
  }
  
  const parityPattern = EAN_PARITY[parseInt(data[0], 10)];
  let pattern = '101'; // Start
  
  // Left side (6 digits, variable parity)
  for (let i = 0; i < 6; i++) {
    const digit = parseInt(data[i + 1], 10);
    pattern += parityPattern[i] === 'L' ? EAN_L[digit] : EAN_G[digit];
  }
  
  pattern += '01010'; // Center
  
  // Right side (6 digits, R encoding)
  for (let i = 0; i < 6; i++) {
    const digit = parseInt(data[i + 7], 10);
    pattern += EAN_R[digit];
  }
  
  pattern += '101'; // End
  
  return {
    pattern,
    data,
    type: 'EAN-13'
  };
}

/**
 * Generate UPC-A barcode
 */
function generateUPCA(input, options = {}) {
  let data = typeof input === 'object' ? (input.data || input.code || input.upc) : input;
  data = data.replace(/\D/g, '');
  
  if (data.length === 11) {
    // Calculate check digit
    let sum = 0;
    for (let i = 0; i < 11; i++) {
      sum += parseInt(data[i], 10) * (i % 2 === 0 ? 3 : 1);
    }
    data += (10 - (sum % 10)) % 10;
  }
  
  if (data.length !== 12) {
    throw new Error('UPC-A must be 11 or 12 digits');
  }
  
  // UPC-A is essentially EAN-13 with leading 0
  return generateEAN13('0' + data, options);
}

/**
 * Generate barcode as SVG
 */
function generateBarcodeSvg(input, options = {}) {
  const {
    type = 'Code128',
    width = 200,
    height = 80,
    barWidth = 2,
    showText = true,
    fontSize = 12,
    textMargin = 5
  } = typeof input === 'object' ? { ...input, ...options } : options;
  
  const data = typeof input === 'object' ? (input.data || input.text || input.code) : input;
  
  let barcode;
  switch (type.toLowerCase()) {
    case 'code128':
      barcode = generateCode128(data);
      break;
    case 'code39':
      barcode = generateCode39(data);
      break;
    case 'ean13':
    case 'ean-13':
      barcode = generateEAN13(data);
      break;
    case 'upca':
    case 'upc-a':
      barcode = generateUPCA(data);
      break;
    default:
      throw new Error(`Unknown barcode type: ${type}`);
  }
  
  const pattern = barcode.pattern;
  const totalWidth = pattern.length * barWidth;
  const textHeight = showText ? fontSize + textMargin : 0;
  const barcodeHeight = height - textHeight;
  
  let bars = '';
  let x = 0;
  
  for (const bit of pattern) {
    if (bit === '1') {
      bars += `<rect x="${x}" y="0" width="${barWidth}" height="${barcodeHeight}" fill="black"/>`;
    }
    x += barWidth;
  }
  
  let textElement = '';
  if (showText) {
    textElement = `<text x="${totalWidth / 2}" y="${height - 2}" text-anchor="middle" font-family="monospace" font-size="${fontSize}">${barcode.data}</text>`;
  }
  
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${totalWidth} ${height}" width="${width}" height="${height}">
  <rect width="100%" height="100%" fill="white"/>
  ${bars}
  ${textElement}
</svg>`;
}

/**
 * Generate barcode as Data URL
 */
function generateBarcodeDataUrl(input, options = {}) {
  const svg = generateBarcodeSvg(input, options);
  const base64 = typeof Buffer !== 'undefined'
    ? Buffer.from(svg).toString('base64')
    : btoa(unescape(encodeURIComponent(svg)));
  return `data:image/svg+xml;base64,${base64}`;
}

// ============================================================================
// QR CODE HELPER FUNCTIONS
// ============================================================================

function detectMode(data) {
  if (/^\d+$/.test(data)) return MODE.NUMERIC;
  if (/^[0-9A-Z $%*+\-./:]+$/.test(data.toUpperCase())) return MODE.ALPHANUMERIC;
  return MODE.BYTE;
}

function findVersion(data, mode, ecLevel) {
  const len = data.length;
  for (let v = 1; v <= 40; v++) {
    const capacity = getCapacity(v, mode, ecLevel);
    if (capacity >= len) return v;
  }
  return 41; // Too large
}

function getCapacity(version, mode, ecLevel) {
  // Simplified capacity calculation
  const baseCapacity = QR_CAPACITIES[version] || 0;
  const ecMultiplier = [1, 0.8, 0.6, 0.4][ecLevel];
  const modeMultiplier = mode === MODE.NUMERIC ? 1.6 : mode === MODE.ALPHANUMERIC ? 1 : 0.6;
  return Math.floor(baseCapacity * ecMultiplier * modeMultiplier);
}

function createMatrix(size) {
  return Array(size).fill(null).map(() => Array(size).fill(-1));
}

function placeFunctionPatterns(matrix, version) {
  const size = matrix.length;
  
  // Finder patterns (7x7)
  placeFinder(matrix, 0, 0);
  placeFinder(matrix, 0, size - 7);
  placeFinder(matrix, size - 7, 0);
  
  // Timing patterns
  for (let i = 8; i < size - 8; i++) {
    matrix[6][i] = i % 2 === 0 ? 1 : 0;
    matrix[i][6] = i % 2 === 0 ? 1 : 0;
  }
  
  // Alignment patterns (for version >= 2)
  if (version >= 2) {
    const positions = getAlignmentPositions(version);
    for (const row of positions) {
      for (const col of positions) {
        if (matrix[row][col] === -1) {
          placeAlignment(matrix, row, col);
        }
      }
    }
  }
  
  // Dark module
  matrix[size - 8][8] = 1;
}

function placeFinder(matrix, row, col) {
  for (let r = -1; r <= 7; r++) {
    for (let c = -1; c <= 7; c++) {
      const tr = row + r;
      const tc = col + c;
      if (tr >= 0 && tr < matrix.length && tc >= 0 && tc < matrix.length) {
        if (r === -1 || r === 7 || c === -1 || c === 7) {
          matrix[tr][tc] = 0; // White border
        } else if (r === 0 || r === 6 || c === 0 || c === 6 ||
                   (r >= 2 && r <= 4 && c >= 2 && c <= 4)) {
          matrix[tr][tc] = 1; // Black
        } else {
          matrix[tr][tc] = 0; // White
        }
      }
    }
  }
}

function placeAlignment(matrix, row, col) {
  for (let r = -2; r <= 2; r++) {
    for (let c = -2; c <= 2; c++) {
      const val = (Math.abs(r) === 2 || Math.abs(c) === 2 || (r === 0 && c === 0)) ? 1 : 0;
      matrix[row + r][col + c] = val;
    }
  }
}

function getAlignmentPositions(version) {
  if (version === 1) return [];
  const positions = [6];
  const last = version * 4 + 10;
  const count = Math.floor(version / 7) + 2;
  const step = Math.ceil((last - 6) / (count - 1));
  
  for (let i = 1; i < count; i++) {
    positions.push(6 + i * step);
  }
  positions[positions.length - 1] = last;
  return positions;
}

function encodeData(data, mode, version, ecLevel) {
  // Simplified encoding - returns bit pattern
  const bits = [];
  
  // Mode indicator (4 bits)
  for (let i = 3; i >= 0; i--) {
    bits.push((mode >> i) & 1);
  }
  
  // Character count indicator
  const countBits = getCountBits(version, mode);
  for (let i = countBits - 1; i >= 0; i--) {
    bits.push((data.length >> i) & 1);
  }
  
  // Data encoding
  if (mode === MODE.BYTE) {
    for (const char of data) {
      const code = char.charCodeAt(0);
      for (let i = 7; i >= 0; i--) {
        bits.push((code >> i) & 1);
      }
    }
  } else if (mode === MODE.ALPHANUMERIC) {
    const upper = data.toUpperCase();
    for (let i = 0; i < upper.length; i += 2) {
      if (i + 1 < upper.length) {
        const val = ALPHANUM.indexOf(upper[i]) * 45 + ALPHANUM.indexOf(upper[i + 1]);
        for (let j = 10; j >= 0; j--) {
          bits.push((val >> j) & 1);
        }
      } else {
        const val = ALPHANUM.indexOf(upper[i]);
        for (let j = 5; j >= 0; j--) {
          bits.push((val >> j) & 1);
        }
      }
    }
  } else if (mode === MODE.NUMERIC) {
    for (let i = 0; i < data.length; i += 3) {
      const chunk = data.slice(i, i + 3);
      const val = parseInt(chunk, 10);
      const numBits = chunk.length === 3 ? 10 : chunk.length === 2 ? 7 : 4;
      for (let j = numBits - 1; j >= 0; j--) {
        bits.push((val >> j) & 1);
      }
    }
  }
  
  // Terminator
  const capacity = getDataCapacity(version, ecLevel);
  while (bits.length < capacity && bits.length < capacity + 4) {
    bits.push(0);
  }
  
  // Pad to byte boundary
  while (bits.length % 8 !== 0) {
    bits.push(0);
  }
  
  // Pad bytes
  const padBytes = [0b11101100, 0b00010001];
  let padIndex = 0;
  while (bits.length < capacity) {
    for (let i = 7; i >= 0; i--) {
      bits.push((padBytes[padIndex] >> i) & 1);
    }
    padIndex = (padIndex + 1) % 2;
  }
  
  return bits;
}

function getCountBits(version, mode) {
  if (version <= 9) {
    return mode === MODE.NUMERIC ? 10 : mode === MODE.ALPHANUMERIC ? 9 : 8;
  } else if (version <= 26) {
    return mode === MODE.NUMERIC ? 12 : mode === MODE.ALPHANUMERIC ? 11 : 16;
  } else {
    return mode === MODE.NUMERIC ? 14 : mode === MODE.ALPHANUMERIC ? 13 : 16;
  }
}

function getDataCapacity(version, ecLevel) {
  // Simplified - returns approximate bit capacity
  const totalCodewords = Math.pow(version * 4 + 17, 2) - 225;
  const ecRatio = [0.07, 0.15, 0.25, 0.3][ecLevel];
  return Math.floor(totalCodewords * (1 - ecRatio) * 8 / 10);
}

function placeData(matrix, bits) {
  const size = matrix.length;
  let bitIndex = 0;
  let up = true;
  
  for (let col = size - 1; col >= 0; col -= 2) {
    if (col === 6) col--;
    
    for (let i = 0; i < size; i++) {
      const row = up ? size - 1 - i : i;
      
      for (let j = 0; j < 2; j++) {
        const c = col - j;
        if (matrix[row][c] === -1) {
          matrix[row][c] = bitIndex < bits.length ? bits[bitIndex++] : 0;
        }
      }
    }
    up = !up;
  }
}

function findBestMask(matrix) {
  // Simplified - just return mask 0
  return 0;
}

function applyMask(matrix, maskPattern) {
  const size = matrix.length;
  const maskFn = getMaskFunction(maskPattern);
  
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      if (isDataModule(matrix, row, col)) {
        if (maskFn(row, col)) {
          matrix[row][col] ^= 1;
        }
      }
    }
  }
}

function getMaskFunction(pattern) {
  const masks = [
    (r, c) => (r + c) % 2 === 0,
    (r, c) => r % 2 === 0,
    (r, c) => c % 3 === 0,
    (r, c) => (r + c) % 3 === 0,
    (r, c) => (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0,
    (r, c) => (r * c) % 2 + (r * c) % 3 === 0,
    (r, c) => ((r * c) % 2 + (r * c) % 3) % 2 === 0,
    (r, c) => ((r + c) % 2 + (r * c) % 3) % 2 === 0
  ];
  return masks[pattern] || masks[0];
}

function isDataModule(matrix, row, col) {
  const size = matrix.length;
  // Skip finder patterns, timing, etc.
  if (row < 9 && col < 9) return false;
  if (row < 9 && col >= size - 8) return false;
  if (row >= size - 8 && col < 9) return false;
  if (row === 6 || col === 6) return false;
  return true;
}

function placeFormatInfo(matrix, ecLevel, mask) {
  const size = matrix.length;
  const format = (ecLevel << 3) | mask;
  // Simplified - place format bits
  const bits = formatToBits(format);
  
  // Top-left
  for (let i = 0; i < 6; i++) {
    matrix[8][i] = bits[i];
  }
  matrix[8][7] = bits[6];
  matrix[8][8] = bits[7];
  matrix[7][8] = bits[8];
  for (let i = 0; i < 6; i++) {
    matrix[5 - i][8] = bits[9 + i];
  }
  
  // Top-right and bottom-left
  for (let i = 0; i < 8; i++) {
    matrix[8][size - 1 - i] = bits[i];
  }
  for (let i = 0; i < 7; i++) {
    matrix[size - 7 + i][8] = bits[8 + i];
  }
}

function formatToBits(format) {
  // BCH error correction for format info
  let data = format << 10;
  const gen = 0b10100110111;
  
  for (let i = 4; i >= 0; i--) {
    if (data & (1 << (i + 10))) {
      data ^= gen << i;
    }
  }
  
  const encoded = (format << 10) | data;
  const masked = encoded ^ 0b101010000010010;
  
  const bits = [];
  for (let i = 14; i >= 0; i--) {
    bits.push((masked >> i) & 1);
  }
  return bits;
}

function placeVersionInfo(matrix, version) {
  // Version info for version 7+
  const size = matrix.length;
  const bits = versionToBits(version);
  
  for (let i = 0; i < 18; i++) {
    const bit = bits[i];
    const row = Math.floor(i / 3);
    const col = i % 3;
    
    matrix[row][size - 11 + col] = bit;
    matrix[size - 11 + col][row] = bit;
  }
}

function versionToBits(version) {
  // BCH error correction for version info
  let data = version << 12;
  const gen = 0b1111100100101;
  
  for (let i = 5; i >= 0; i--) {
    if (data & (1 << (i + 12))) {
      data ^= gen << i;
    }
  }
  
  const encoded = (version << 12) | data;
  const bits = [];
  for (let i = 17; i >= 0; i--) {
    bits.push((encoded >> i) & 1);
  }
  return bits;
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  // QR Code
  generateQRMatrix,
  generateQRSvg,
  generateQRDataUrl,
  generateQRAscii,
  
  // Barcodes
  generateCode128,
  generateCode39,
  generateEAN13,
  generateUPCA,
  generateBarcodeSvg,
  generateBarcodeDataUrl
};
