/**
 * Encoding Utilities - Embedded ForgeHook Plugin
 * Data encoding and decoding operations, all running locally
 */

// Base64 encoding/decoding
function base64Encode(input, encoding = 'utf-8') {
  if (typeof input === 'string') {
    if (typeof Buffer !== 'undefined') {
      return Buffer.from(input, encoding).toString('base64');
    }
    return btoa(unescape(encodeURIComponent(input)));
  }
  if (input instanceof Uint8Array || Buffer.isBuffer(input)) {
    return Buffer.from(input).toString('base64');
  }
  throw new Error('Input must be string or buffer');
}

function base64Decode(input, toBuffer = false) {
  if (typeof Buffer !== 'undefined') {
    const buffer = Buffer.from(input, 'base64');
    return toBuffer ? buffer : buffer.toString('utf-8');
  }
  const decoded = decodeURIComponent(escape(atob(input)));
  return toBuffer ? new TextEncoder().encode(decoded) : decoded;
}

// Base64URL (URL-safe Base64)
function base64UrlEncode(input) {
  return base64Encode(input)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

function base64UrlDecode(input, toBuffer = false) {
  let base64 = input
    .replace(/-/g, '+')
    .replace(/_/g, '/');
  
  // Add padding
  const padding = base64.length % 4;
  if (padding) {
    base64 += '='.repeat(4 - padding);
  }
  
  return base64Decode(base64, toBuffer);
}

// Hexadecimal encoding/decoding
function hexEncode(input) {
  if (typeof input === 'string') {
    if (typeof Buffer !== 'undefined') {
      return Buffer.from(input, 'utf-8').toString('hex');
    }
    return Array.from(new TextEncoder().encode(input))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }
  if (input instanceof Uint8Array || Buffer.isBuffer(input)) {
    return Array.from(input)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }
  throw new Error('Input must be string or buffer');
}

function hexDecode(input, toBuffer = false) {
  const hex = input.replace(/\s/g, '');
  if (!/^[0-9a-fA-F]*$/.test(hex)) {
    throw new Error('Invalid hexadecimal string');
  }
  
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  
  if (toBuffer) {
    return typeof Buffer !== 'undefined' ? Buffer.from(bytes) : bytes;
  }
  return new TextDecoder().decode(bytes);
}

// URL encoding/decoding
function urlEncode(input, options = {}) {
  if (options.component) {
    return encodeURIComponent(input);
  }
  return encodeURI(input);
}

function urlDecode(input, options = {}) {
  if (options.component) {
    return decodeURIComponent(input);
  }
  return decodeURI(input);
}

// HTML entity encoding/decoding
const HTML_ENTITIES = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '`': '&#96;',
  '/': '&#47;'
};

const HTML_DECODE_MAP = {
  '&amp;': '&',
  '&lt;': '<',
  '&gt;': '>',
  '&quot;': '"',
  '&#39;': "'",
  '&apos;': "'",
  '&#96;': '`',
  '&#47;': '/',
  '&nbsp;': ' ',
  '&copy;': '©',
  '&reg;': '®',
  '&trade;': '™',
  '&bull;': '•',
  '&mdash;': '—',
  '&ndash;': '–',
  '&hellip;': '…'
};

function htmlEncode(input, options = {}) {
  const chars = options.full 
    ? /[&<>"'`\/]/g 
    : /[&<>"]/g;
  
  return input.replace(chars, char => HTML_ENTITIES[char] || char);
}

function htmlDecode(input) {
  // Decode named entities
  let result = input;
  for (const [entity, char] of Object.entries(HTML_DECODE_MAP)) {
    result = result.replace(new RegExp(entity, 'g'), char);
  }
  
  // Decode numeric entities (&#123; or &#x7B;)
  result = result.replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code, 10)));
  result = result.replace(/&#x([0-9a-fA-F]+);/g, (_, code) => String.fromCharCode(parseInt(code, 16)));
  
  return result;
}

// Unicode encoding/decoding
function unicodeEncode(input) {
  return input.split('').map(char => {
    const code = char.charCodeAt(0);
    if (code > 127) {
      return '\\u' + code.toString(16).padStart(4, '0');
    }
    return char;
  }).join('');
}

function unicodeDecode(input) {
  return input.replace(/\\u([0-9a-fA-F]{4})/g, (_, code) => 
    String.fromCharCode(parseInt(code, 16))
  );
}

// JWT decoding (WITHOUT verification - read-only)
function jwtDecode(token) {
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT format');
  }
  
  return {
    header: JSON.parse(base64UrlDecode(parts[0])),
    payload: JSON.parse(base64UrlDecode(parts[1])),
    signature: parts[2]
  };
}

function jwtHeader(token) {
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT format');
  }
  return JSON.parse(base64UrlDecode(parts[0]));
}

function jwtPayload(token) {
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT format');
  }
  const payload = JSON.parse(base64UrlDecode(parts[1]));
  
  // Add human-readable dates
  if (payload.iat) payload.issuedAt = new Date(payload.iat * 1000).toISOString();
  if (payload.exp) payload.expiresAt = new Date(payload.exp * 1000).toISOString();
  if (payload.nbf) payload.notBefore = new Date(payload.nbf * 1000).toISOString();
  
  // Check expiration
  if (payload.exp) {
    payload.isExpired = Date.now() > payload.exp * 1000;
  }
  
  return payload;
}

// String to bytes conversion
function stringToBytes(input, encoding = 'utf-8') {
  if (typeof Buffer !== 'undefined') {
    return Array.from(Buffer.from(input, encoding));
  }
  return Array.from(new TextEncoder().encode(input));
}

function bytesToString(bytes, encoding = 'utf-8') {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  if (typeof Buffer !== 'undefined') {
    return Buffer.from(arr).toString(encoding);
  }
  return new TextDecoder(encoding).decode(arr);
}

function utf8ToBytes(input) {
  return stringToBytes(input, 'utf-8');
}

function bytesToUtf8(bytes) {
  return bytesToString(bytes, 'utf-8');
}

// Simple ciphers (for obfuscation, NOT security)
function rot13(input) {
  return input.replace(/[a-zA-Z]/g, char => {
    const code = char.charCodeAt(0);
    const base = code < 97 ? 65 : 97;
    return String.fromCharCode(((code - base + 13) % 26) + base);
  });
}

function caesar(input, shift = 3, decrypt = false) {
  const actualShift = decrypt ? 26 - (shift % 26) : shift % 26;
  return input.replace(/[a-zA-Z]/g, char => {
    const code = char.charCodeAt(0);
    const base = code < 97 ? 65 : 97;
    return String.fromCharCode(((code - base + actualShift) % 26) + base);
  });
}

// Browser-compatible atob/btoa
const _atob = typeof atob !== 'undefined' ? atob : (s) => Buffer.from(s, 'base64').toString('binary');
const _btoa = typeof btoa !== 'undefined' ? btoa : (s) => Buffer.from(s, 'binary').toString('base64');

module.exports = {
  base64Encode,
  base64Decode,
  base64UrlEncode,
  base64UrlDecode,
  hexEncode,
  hexDecode,
  urlEncode,
  urlDecode,
  htmlEncode,
  htmlDecode,
  unicodeEncode,
  unicodeDecode,
  jwtDecode,
  jwtHeader,
  jwtPayload,
  stringToBytes,
  bytesToString,
  utf8ToBytes,
  bytesToUtf8,
  rot13,
  caesar,
  atob: _atob,
  btoa: _btoa
};
