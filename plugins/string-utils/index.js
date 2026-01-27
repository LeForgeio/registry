/**
 * String Utilities - Embedded ForgeHook Plugin
 * Lightweight string manipulation utilities
 */

// Convert string to URL-friendly slug
function slugify(input, config = {}) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  const separator = config.separator || '-';
  
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove non-word chars
    .replace(/[\s_-]+/g, separator) // Replace spaces/underscores with separator
    .replace(new RegExp(`^${separator}+|${separator}+$`, 'g'), ''); // Trim separators
}

// Convert string to camelCase
function camelCase(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((word, index) => 
      index === 0 ? word : word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join('');
}

// Convert string to PascalCase
function pascalCase(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
}

// Convert string to snake_case
function snakeCase(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str
    .replace(/([a-z])([A-Z])/g, '$1_$2') // Handle camelCase
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .trim()
    .replace(/[\s-]+/g, '_');
}

// Convert string to kebab-case
function kebabCase(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2') // Handle camelCase
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ')
    .trim()
    .replace(/[\s_]+/g, '-');
}

// Truncate string to specified length
function truncate(input, config = {}) {
  let str, length, suffix;
  
  if (typeof input === 'object') {
    str = input.text || input.value || '';
    length = input.length || config.defaultTruncateLength || 100;
    suffix = input.suffix || config.truncateSuffix || '...';
  } else {
    str = String(input);
    length = config.defaultTruncateLength || 100;
    suffix = config.truncateSuffix || '...';
  }
  
  if (str.length <= length) return str;
  
  return str.slice(0, length - suffix.length).trim() + suffix;
}

// Remove HTML tags from string
function sanitizeHtml(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove scripts
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '') // Remove styles
    .replace(/<[^>]+>/g, '') // Remove all HTML tags
    .replace(/&nbsp;/g, ' ')
    .trim();
}

// Escape HTML special characters
function escapeHtml(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  const escapeMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
  };
  
  return str.replace(/[&<>"'`=/]/g, char => escapeMap[char]);
}

// Unescape HTML entities
function unescapeHtml(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  const unescapeMap = {
    '&amp;': '&',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&#39;': "'",
    '&#x27;': "'",
    '&#x2F;': '/',
    '&#x60;': '`',
    '&#x3D;': '=',
    '&nbsp;': ' '
  };
  
  return str.replace(/&(?:amp|lt|gt|quot|#39|#x27|#x2F|#x60|#x3D|nbsp);/g, 
    entity => unescapeMap[entity] || entity);
}

// Capitalize first letter
function capitalize(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

// Convert to Title Case
function titleCase(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  // Words that should not be capitalized (unless first word)
  const minorWords = new Set([
    'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 
    'to', 'from', 'by', 'of', 'in', 'with', 'as', 'is', 'vs'
  ]);
  
  return str
    .toLowerCase()
    .split(/\s+/)
    .map((word, index) => {
      if (index === 0 || !minorWords.has(word)) {
        return word.charAt(0).toUpperCase() + word.slice(1);
      }
      return word;
    })
    .join(' ');
}

// Count words in string
function wordCount(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  if (!str.trim()) return 0;
  
  return str
    .trim()
    .split(/\s+/)
    .filter(word => word.length > 0)
    .length;
}

// Reverse string
function reverse(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  // Handle Unicode properly using Array.from
  return Array.from(str).reverse().join('');
}

// Pad string on the left
function padLeft(input, config = {}) {
  let str, length, char;
  
  if (typeof input === 'object') {
    str = String(input.text || input.value || '');
    length = input.length || 0;
    char = input.char || input.padChar || ' ';
  } else {
    str = String(input);
    length = config.length || 0;
    char = config.char || ' ';
  }
  
  if (str.length >= length) return str;
  
  const padding = char.repeat(Math.ceil((length - str.length) / char.length));
  return (padding + str).slice(-length);
}

// Pad string on the right
function padRight(input, config = {}) {
  let str, length, char;
  
  if (typeof input === 'object') {
    str = String(input.text || input.value || '');
    length = input.length || 0;
    char = input.char || input.padChar || ' ';
  } else {
    str = String(input);
    length = config.length || 0;
    char = config.char || ' ';
  }
  
  if (str.length >= length) return str;
  
  const padding = char.repeat(Math.ceil((length - str.length) / char.length));
  return (str + padding).slice(0, length);
}

// Remove all whitespace
function removeWhitespace(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str.replace(/\s+/g, '');
}

// Normalize whitespace (collapse multiple spaces to single)
function normalizeWhitespace(input) {
  const str = typeof input === 'object' ? input.text || input.value || '' : String(input);
  
  return str
    .replace(/\s+/g, ' ')
    .trim();
}

module.exports = {
  slugify,
  camelCase,
  pascalCase,
  snakeCase,
  kebabCase,
  truncate,
  sanitizeHtml,
  escapeHtml,
  unescapeHtml,
  capitalize,
  titleCase,
  wordCount,
  reverse,
  padLeft,
  padRight,
  removeWhitespace,
  normalizeWhitespace
};
