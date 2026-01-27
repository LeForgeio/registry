/**
 * Validation Utilities - Embedded ForgeHook Plugin
 * All validations run locally with no external API calls
 */

// Email validation (RFC 5322 compliant)
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
const EMAIL_STRICT_REGEX = /^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$/i;

function isEmail(value, options = {}) {
  if (typeof value !== 'string') return false;
  const regex = options.strict ? EMAIL_STRICT_REGEX : EMAIL_REGEX;
  return regex.test(value.trim());
}

// Phone validation (international formats)
const PHONE_REGEX = /^[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]*$/;
function isPhone(value, options = {}) {
  if (typeof value !== 'string') return false;
  const cleaned = value.replace(/[\s\-\.\(\)]/g, '');
  if (cleaned.length < 7 || cleaned.length > 15) return false;
  return PHONE_REGEX.test(value);
}

// URL validation
function isURL(value, options = {}) {
  if (typeof value !== 'string') return false;
  try {
    const url = new URL(value);
    const allowedProtocols = options.protocols || ['http:', 'https:'];
    return allowedProtocols.includes(url.protocol);
  } catch {
    return false;
  }
}

// UUID validation (v1-v5)
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
function isUUID(value, version) {
  if (typeof value !== 'string') return false;
  if (!UUID_REGEX.test(value)) return false;
  if (version) {
    return value.charAt(14) === String(version);
  }
  return true;
}

// IBAN validation with checksum
function isIBAN(value) {
  if (typeof value !== 'string') return false;
  const iban = value.replace(/\s/g, '').toUpperCase();
  if (!/^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,30}$/.test(iban)) return false;
  
  // Move first 4 chars to end and convert letters to numbers
  const rearranged = iban.slice(4) + iban.slice(0, 4);
  const numeric = rearranged.replace(/[A-Z]/g, (char) => (char.charCodeAt(0) - 55).toString());
  
  // Mod 97 check
  let remainder = numeric;
  while (remainder.length > 2) {
    const block = remainder.slice(0, 9);
    remainder = (parseInt(block, 10) % 97).toString() + remainder.slice(block.length);
  }
  return parseInt(remainder, 10) % 97 === 1;
}

// EU VAT number validation (format only, no VIES check)
const VAT_PATTERNS = {
  AT: /^ATU[0-9]{8}$/,
  BE: /^BE[01][0-9]{9}$/,
  BG: /^BG[0-9]{9,10}$/,
  CY: /^CY[0-9]{8}[A-Z]$/,
  CZ: /^CZ[0-9]{8,10}$/,
  DE: /^DE[0-9]{9}$/,
  DK: /^DK[0-9]{8}$/,
  EE: /^EE[0-9]{9}$/,
  EL: /^EL[0-9]{9}$/,
  ES: /^ES[A-Z0-9][0-9]{7}[A-Z0-9]$/,
  FI: /^FI[0-9]{8}$/,
  FR: /^FR[A-Z0-9]{2}[0-9]{9}$/,
  GB: /^GB([0-9]{9}|[0-9]{12}|(GD|HA)[0-9]{3})$/,
  HR: /^HR[0-9]{11}$/,
  HU: /^HU[0-9]{8}$/,
  IE: /^IE([0-9]{7}[A-Z]{1,2}|[0-9][A-Z][0-9]{5}[A-Z])$/,
  IT: /^IT[0-9]{11}$/,
  LT: /^LT([0-9]{9}|[0-9]{12})$/,
  LU: /^LU[0-9]{8}$/,
  LV: /^LV[0-9]{11}$/,
  MT: /^MT[0-9]{8}$/,
  NL: /^NL[0-9]{9}B[0-9]{2}$/,
  PL: /^PL[0-9]{10}$/,
  PT: /^PT[0-9]{9}$/,
  RO: /^RO[0-9]{2,10}$/,
  SE: /^SE[0-9]{12}$/,
  SI: /^SI[0-9]{8}$/,
  SK: /^SK[0-9]{10}$/
};

function isVATNumber(value) {
  if (typeof value !== 'string') return false;
  const vat = value.replace(/[\s\-\.]/g, '').toUpperCase();
  const countryCode = vat.slice(0, 2);
  const pattern = VAT_PATTERNS[countryCode];
  return pattern ? pattern.test(vat) : false;
}

// Credit card validation (Luhn algorithm)
function isCreditCard(value) {
  if (typeof value !== 'string') return false;
  const card = value.replace(/[\s\-]/g, '');
  if (!/^[0-9]{13,19}$/.test(card)) return false;
  
  // Luhn algorithm
  let sum = 0;
  let isEven = false;
  for (let i = card.length - 1; i >= 0; i--) {
    let digit = parseInt(card[i], 10);
    if (isEven) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    isEven = !isEven;
  }
  return sum % 10 === 0;
}

function getCreditCardType(value) {
  if (typeof value !== 'string') return null;
  const card = value.replace(/[\s\-]/g, '');
  
  const patterns = {
    visa: /^4[0-9]{12}(?:[0-9]{3})?$/,
    mastercard: /^5[1-5][0-9]{14}$|^2[2-7][0-9]{14}$/,
    amex: /^3[47][0-9]{13}$/,
    discover: /^6(?:011|5[0-9]{2})[0-9]{12}$/,
    diners: /^3(?:0[0-5]|[68][0-9])[0-9]{11}$/,
    jcb: /^(?:2131|1800|35\d{3})\d{11}$/
  };
  
  for (const [type, pattern] of Object.entries(patterns)) {
    if (pattern.test(card)) return type;
  }
  return null;
}

// Postal code validation by country
const POSTAL_PATTERNS = {
  US: /^[0-9]{5}(?:-[0-9]{4})?$/,
  CA: /^[A-Z][0-9][A-Z]\s?[0-9][A-Z][0-9]$/i,
  UK: /^[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}$/i,
  GB: /^[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}$/i,
  DE: /^[0-9]{5}$/,
  FR: /^[0-9]{5}$/,
  IT: /^[0-9]{5}$/,
  ES: /^[0-9]{5}$/,
  NL: /^[0-9]{4}\s?[A-Z]{2}$/i,
  BE: /^[0-9]{4}$/,
  AU: /^[0-9]{4}$/,
  JP: /^[0-9]{3}-?[0-9]{4}$/,
  CN: /^[0-9]{6}$/,
  IN: /^[0-9]{6}$/,
  BR: /^[0-9]{5}-?[0-9]{3}$/
};

function isPostalCode(value, country = 'US') {
  if (typeof value !== 'string') return false;
  const pattern = POSTAL_PATTERNS[country.toUpperCase()];
  return pattern ? pattern.test(value.trim()) : false;
}

// IP address validation
function isIPv4(value) {
  if (typeof value !== 'string') return false;
  const parts = value.split('.');
  if (parts.length !== 4) return false;
  return parts.every(part => {
    const num = parseInt(part, 10);
    return !isNaN(num) && num >= 0 && num <= 255 && String(num) === part;
  });
}

function isIPv6(value) {
  if (typeof value !== 'string') return false;
  const ipv6Regex = /^(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+|::(?:ffff(?::0{1,4})?:)?(?:(?:25[0-5]|(?:2[0-4]|1?[0-9])?[0-9])\.){3}(?:25[0-5]|(?:2[0-4]|1?[0-9])?[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1?[0-9])?[0-9])\.){3}(?:25[0-5]|(?:2[0-4]|1?[0-9])?[0-9]))$/;
  return ipv6Regex.test(value);
}

// MAC address validation
function isMACAddress(value, options = {}) {
  if (typeof value !== 'string') return false;
  const separator = options.separator || ':';
  const pattern = separator === ':' 
    ? /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/
    : /^([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}$/;
  return pattern.test(value);
}

// Hex color validation
function isHexColor(value) {
  if (typeof value !== 'string') return false;
  return /^#?([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$/.test(value);
}

// JSON validation
function isJSON(value) {
  if (typeof value !== 'string') return false;
  try {
    JSON.parse(value);
    return true;
  } catch {
    return false;
  }
}

// Base64 validation
function isBase64(value) {
  if (typeof value !== 'string') return false;
  if (value.length % 4 !== 0) return false;
  return /^[A-Za-z0-9+/]*={0,2}$/.test(value);
}

// Character type validation
function isAlpha(value, locale = 'en-US') {
  if (typeof value !== 'string') return false;
  return /^[a-zA-Z]+$/.test(value);
}

function isAlphanumeric(value) {
  if (typeof value !== 'string') return false;
  return /^[a-zA-Z0-9]+$/.test(value);
}

function isNumeric(value) {
  if (typeof value !== 'string') return false;
  return /^-?[0-9]+(\.[0-9]+)?$/.test(value);
}

function isSlug(value) {
  if (typeof value !== 'string') return false;
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
}

function isEmpty(value) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

function isLength(value, options = {}) {
  if (typeof value !== 'string') return false;
  const len = value.length;
  if (options.min !== undefined && len < options.min) return false;
  if (options.max !== undefined && len > options.max) return false;
  if (options.exact !== undefined && len !== options.exact) return false;
  return true;
}

function matches(value, pattern) {
  if (typeof value !== 'string') return false;
  const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
  return regex.test(value);
}

// Batch validation
function validateAll(data, rules) {
  const results = {};
  const errors = [];
  
  for (const [field, fieldRules] of Object.entries(rules)) {
    const value = data[field];
    results[field] = { valid: true, errors: [] };
    
    for (const rule of fieldRules) {
      let valid = false;
      const ruleName = typeof rule === 'string' ? rule : rule.type;
      const options = typeof rule === 'object' ? rule : {};
      
      switch (ruleName) {
        case 'required': valid = !isEmpty(value); break;
        case 'email': valid = isEmpty(value) || isEmail(value, options); break;
        case 'phone': valid = isEmpty(value) || isPhone(value, options); break;
        case 'url': valid = isEmpty(value) || isURL(value, options); break;
        case 'uuid': valid = isEmpty(value) || isUUID(value, options.version); break;
        case 'iban': valid = isEmpty(value) || isIBAN(value); break;
        case 'vat': valid = isEmpty(value) || isVATNumber(value); break;
        case 'creditCard': valid = isEmpty(value) || isCreditCard(value); break;
        case 'postalCode': valid = isEmpty(value) || isPostalCode(value, options.country); break;
        case 'ipv4': valid = isEmpty(value) || isIPv4(value); break;
        case 'ipv6': valid = isEmpty(value) || isIPv6(value); break;
        case 'length': valid = isEmpty(value) || isLength(value, options); break;
        case 'pattern': valid = isEmpty(value) || matches(value, options.pattern); break;
        default: valid = true;
      }
      
      if (!valid) {
        results[field].valid = false;
        results[field].errors.push(options.message || `Failed ${ruleName} validation`);
        errors.push({ field, rule: ruleName, message: options.message || `Failed ${ruleName} validation` });
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    results,
    errors
  };
}

module.exports = {
  isEmail,
  isPhone,
  isURL,
  isUUID,
  isIBAN,
  isVATNumber,
  isCreditCard,
  getCreditCardType,
  isPostalCode,
  isIPv4,
  isIPv6,
  isMACAddress,
  isHexColor,
  isJSON,
  isBase64,
  isAlpha,
  isAlphanumeric,
  isNumeric,
  isSlug,
  isEmpty,
  isLength,
  matches,
  validateAll
};
