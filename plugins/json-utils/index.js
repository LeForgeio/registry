/**
 * JSON Utilities - Embedded ForgeHook Plugin
 * JSON manipulation, querying, and validation
 */

// JSONPath query (simplified implementation)
function query(data, path) {
  if (!path || path === '$') return data;
  
  const tokens = tokenizePath(path);
  let results = [data];
  
  for (const token of tokens) {
    const newResults = [];
    for (const item of results) {
      if (item == null) continue;
      
      if (token.type === 'property') {
        if (token.value === '*') {
          if (Array.isArray(item)) {
            newResults.push(...item);
          } else if (typeof item === 'object') {
            newResults.push(...Object.values(item));
          }
        } else {
          const val = item[token.value];
          if (val !== undefined) newResults.push(val);
        }
      } else if (token.type === 'index') {
        if (Array.isArray(item)) {
          const idx = token.value < 0 ? item.length + token.value : token.value;
          if (item[idx] !== undefined) newResults.push(item[idx]);
        }
      } else if (token.type === 'slice') {
        if (Array.isArray(item)) {
          newResults.push(...item.slice(token.start, token.end));
        }
      } else if (token.type === 'filter') {
        if (Array.isArray(item)) {
          newResults.push(...item.filter(el => evaluateFilter(el, token.expression)));
        }
      } else if (token.type === 'recursive') {
        newResults.push(...findRecursive(item, token.value));
      }
    }
    results = newResults;
  }
  
  return results.length === 1 ? results[0] : results;
}

function tokenizePath(path) {
  const tokens = [];
  const regex = /\.\.(\w+)|\[([^\]]+)\]|\.(\w+)|(\*)/g;
  let match;
  
  // Skip leading $
  const normalized = path.startsWith('$') ? path.slice(1) : path;
  
  while ((match = regex.exec(normalized)) !== null) {
    if (match[1]) {
      tokens.push({ type: 'recursive', value: match[1] });
    } else if (match[2]) {
      const inner = match[2];
      if (/^-?\d+$/.test(inner)) {
        tokens.push({ type: 'index', value: parseInt(inner, 10) });
      } else if (inner.includes(':')) {
        const [start, end] = inner.split(':').map(s => s ? parseInt(s, 10) : undefined);
        tokens.push({ type: 'slice', start, end });
      } else if (inner.startsWith('?')) {
        tokens.push({ type: 'filter', expression: inner.slice(1) });
      } else if (inner.startsWith("'") || inner.startsWith('"')) {
        tokens.push({ type: 'property', value: inner.slice(1, -1) });
      } else {
        tokens.push({ type: 'property', value: inner });
      }
    } else if (match[3]) {
      tokens.push({ type: 'property', value: match[3] });
    } else if (match[4]) {
      tokens.push({ type: 'property', value: '*' });
    }
  }
  
  return tokens;
}

function findRecursive(obj, key) {
  const results = [];
  
  function search(current) {
    if (current == null || typeof current !== 'object') return;
    
    if (key in current) {
      results.push(current[key]);
    }
    
    for (const value of Object.values(current)) {
      if (typeof value === 'object') {
        search(value);
      }
    }
  }
  
  search(obj);
  return results;
}

function evaluateFilter(item, expression) {
  // Simple filter: @.property > value
  const match = expression.match(/@\.(\w+)\s*(==|!=|>|<|>=|<=)\s*(.+)/);
  if (!match) return true;
  
  const [, prop, op, rawValue] = match;
  const itemValue = item[prop];
  const value = JSON.parse(rawValue);
  
  switch (op) {
    case '==': return itemValue == value;
    case '!=': return itemValue != value;
    case '>': return itemValue > value;
    case '<': return itemValue < value;
    case '>=': return itemValue >= value;
    case '<=': return itemValue <= value;
    default: return true;
  }
}

// Get value at path (dot notation)
function get(obj, path, defaultValue = undefined) {
  if (!path) return obj;
  
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.');
  let result = obj;
  
  for (const key of keys) {
    if (result == null || typeof result !== 'object') {
      return defaultValue;
    }
    result = result[key];
  }
  
  return result === undefined ? defaultValue : result;
}

// Set value at path
function set(obj, path, value) {
  if (!path) return value;
  
  const result = clone(obj);
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.');
  let current = result;
  
  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    const nextKey = keys[i + 1];
    
    if (current[key] == null) {
      current[key] = /^\d+$/.test(nextKey) ? [] : {};
    }
    current = current[key];
  }
  
  current[keys[keys.length - 1]] = value;
  return result;
}

// Check if path exists
function has(obj, path) {
  return get(obj, path, Symbol('NOT_FOUND')) !== Symbol('NOT_FOUND');
}

// Remove value at path
function remove(obj, path) {
  const result = clone(obj);
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.');
  let current = result;
  
  for (let i = 0; i < keys.length - 1; i++) {
    if (current[keys[i]] == null) return result;
    current = current[keys[i]];
  }
  
  const lastKey = keys[keys.length - 1];
  if (Array.isArray(current)) {
    current.splice(parseInt(lastKey, 10), 1);
  } else {
    delete current[lastKey];
  }
  
  return result;
}

// Flatten nested object
function flatten(obj, options = {}) {
  const {
    delimiter = '.',
    maxDepth = 100,
    arrayNotation = 'bracket'
  } = options;
  
  const result = {};
  
  function recurse(current, prefix, depth) {
    if (depth > maxDepth) return;
    
    if (Array.isArray(current)) {
      current.forEach((item, index) => {
        const key = arrayNotation === 'bracket' 
          ? `${prefix}[${index}]`
          : `${prefix}${delimiter}${index}`;
        
        if (typeof item === 'object' && item !== null) {
          recurse(item, key, depth + 1);
        } else {
          result[key] = item;
        }
      });
    } else if (typeof current === 'object' && current !== null) {
      for (const [key, value] of Object.entries(current)) {
        const newKey = prefix ? `${prefix}${delimiter}${key}` : key;
        
        if (typeof value === 'object' && value !== null) {
          recurse(value, newKey, depth + 1);
        } else {
          result[newKey] = value;
        }
      }
    } else {
      result[prefix] = current;
    }
  }
  
  recurse(obj, '', 0);
  return result;
}

// Unflatten object
function unflatten(obj, options = {}) {
  const { delimiter = '.' } = options;
  const result = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const keys = key.replace(/\[(\d+)\]/g, `${delimiter}$1`).split(delimiter);
    let current = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      const nextKey = keys[i + 1];
      
      if (current[k] == null) {
        current[k] = /^\d+$/.test(nextKey) ? [] : {};
      }
      current = current[k];
    }
    
    current[keys[keys.length - 1]] = value;
  }
  
  return result;
}

// Deep merge objects
function deepMerge(...objects) {
  const result = {};
  
  for (const obj of objects) {
    if (obj == null) continue;
    
    for (const [key, value] of Object.entries(obj)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        result[key] = deepMerge(result[key] || {}, value);
      } else {
        result[key] = value;
      }
    }
  }
  
  return result;
}

// Shallow merge
function merge(...objects) {
  return Object.assign({}, ...objects);
}

// Deep clone
function clone(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (Array.isArray(obj)) return obj.map(clone);
  
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    result[key] = clone(value);
  }
  return result;
}

// Deep equality check
function equals(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a !== typeof b) return false;
  
  if (typeof a !== 'object') return false;
  
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  
  if (keysA.length !== keysB.length) return false;
  
  for (const key of keysA) {
    if (!equals(a[key], b[key])) return false;
  }
  
  return true;
}

// Diff two objects
function diff(a, b, options = {}) {
  const { includeEqual = false } = options;
  const changes = [];
  
  function compare(pathA, pathB, path) {
    const keysA = pathA != null ? Object.keys(pathA) : [];
    const keysB = pathB != null ? Object.keys(pathB) : [];
    const allKeys = new Set([...keysA, ...keysB]);
    
    for (const key of allKeys) {
      const currentPath = path ? `${path}.${key}` : key;
      const valA = pathA?.[key];
      const valB = pathB?.[key];
      
      if (valA === undefined) {
        changes.push({ type: 'added', path: currentPath, value: valB });
      } else if (valB === undefined) {
        changes.push({ type: 'removed', path: currentPath, value: valA });
      } else if (typeof valA === 'object' && typeof valB === 'object' && valA !== null && valB !== null) {
        compare(valA, valB, currentPath);
      } else if (valA !== valB) {
        changes.push({ type: 'changed', path: currentPath, oldValue: valA, newValue: valB });
      } else if (includeEqual) {
        changes.push({ type: 'equal', path: currentPath, value: valA });
      }
    }
  }
  
  compare(a, b, '');
  return changes;
}

// Apply diff patch
function patch(obj, changes) {
  let result = clone(obj);
  
  for (const change of changes) {
    switch (change.type) {
      case 'added':
      case 'changed':
        result = set(result, change.path, change.newValue ?? change.value);
        break;
      case 'removed':
        result = remove(result, change.path);
        break;
    }
  }
  
  return result;
}

// JSON Schema validation (simplified)
function validate(data, schema) {
  const errors = [];
  
  function check(value, schemaNode, path) {
    if (schemaNode.type) {
      const actualType = Array.isArray(value) ? 'array' : typeof value;
      if (actualType !== schemaNode.type && !(value === null && schemaNode.nullable)) {
        errors.push({ path, message: `Expected ${schemaNode.type}, got ${actualType}` });
      }
    }
    
    if (schemaNode.required && schemaNode.type === 'object') {
      for (const req of schemaNode.required) {
        if (value[req] === undefined) {
          errors.push({ path: `${path}.${req}`, message: 'Required property missing' });
        }
      }
    }
    
    if (schemaNode.properties && typeof value === 'object') {
      for (const [key, propSchema] of Object.entries(schemaNode.properties)) {
        if (value[key] !== undefined) {
          check(value[key], propSchema, `${path}.${key}`);
        }
      }
    }
    
    if (schemaNode.items && Array.isArray(value)) {
      value.forEach((item, index) => {
        check(item, schemaNode.items, `${path}[${index}]`);
      });
    }
    
    if (schemaNode.minimum !== undefined && typeof value === 'number') {
      if (value < schemaNode.minimum) {
        errors.push({ path, message: `Value must be >= ${schemaNode.minimum}` });
      }
    }
    
    if (schemaNode.maximum !== undefined && typeof value === 'number') {
      if (value > schemaNode.maximum) {
        errors.push({ path, message: `Value must be <= ${schemaNode.maximum}` });
      }
    }
    
    if (schemaNode.minLength !== undefined && typeof value === 'string') {
      if (value.length < schemaNode.minLength) {
        errors.push({ path, message: `String must be >= ${schemaNode.minLength} chars` });
      }
    }
    
    if (schemaNode.maxLength !== undefined && typeof value === 'string') {
      if (value.length > schemaNode.maxLength) {
        errors.push({ path, message: `String must be <= ${schemaNode.maxLength} chars` });
      }
    }
    
    if (schemaNode.pattern && typeof value === 'string') {
      if (!new RegExp(schemaNode.pattern).test(value)) {
        errors.push({ path, message: `String must match pattern ${schemaNode.pattern}` });
      }
    }
    
    if (schemaNode.enum && !schemaNode.enum.includes(value)) {
      errors.push({ path, message: `Value must be one of: ${schemaNode.enum.join(', ')}` });
    }
  }
  
  check(data, schema, '$');
  
  return {
    valid: errors.length === 0,
    errors
  };
}

// Safe JSON parse
function safeParse(input, defaultValue = null) {
  try {
    return JSON.parse(input);
  } catch {
    return defaultValue;
  }
}

// Stringify with options
function stringify(obj, options = {}) {
  const { indent = 0, replacer = null } = options;
  return JSON.stringify(obj, replacer, indent);
}

// Pretty format
function format(obj, indent = 2) {
  return JSON.stringify(obj, null, indent);
}

// Minify
function minify(obj) {
  return JSON.stringify(obj);
}

// Sort keys alphabetically
function sortKeys(obj, options = {}) {
  const { deep = true } = options;
  
  if (Array.isArray(obj)) {
    return deep ? obj.map(item => sortKeys(item, options)) : obj;
  }
  
  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }
  
  const sorted = {};
  const keys = Object.keys(obj).sort();
  
  for (const key of keys) {
    sorted[key] = deep ? sortKeys(obj[key], options) : obj[key];
  }
  
  return sorted;
}

// Pick specific keys
function pick(obj, keys) {
  const result = {};
  for (const key of keys) {
    if (key in obj) {
      result[key] = obj[key];
    }
  }
  return result;
}

// Omit specific keys
function omit(obj, keys) {
  const keySet = new Set(keys);
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    if (!keySet.has(key)) {
      result[key] = value;
    }
  }
  return result;
}

// Transform with mapping
function transform(obj, mapping) {
  const result = {};
  
  for (const [targetKey, sourceKey] of Object.entries(mapping)) {
    const value = typeof sourceKey === 'function' 
      ? sourceKey(obj)
      : get(obj, sourceKey);
    
    if (value !== undefined) {
      set(result, targetKey, value);
    }
  }
  
  return unflatten(result);
}

// Array helpers
function filter(arr, predicate) {
  if (typeof predicate === 'function') {
    return arr.filter(predicate);
  }
  // Object predicate
  return arr.filter(item => {
    for (const [key, value] of Object.entries(predicate)) {
      if (get(item, key) !== value) return false;
    }
    return true;
  });
}

function mapArray(arr, iteratee) {
  if (typeof iteratee === 'function') {
    return arr.map(iteratee);
  }
  // String path
  return arr.map(item => get(item, iteratee));
}

function find(arr, predicate) {
  return filter(arr, predicate)[0];
}

function findAll(arr, predicate) {
  return filter(arr, predicate);
}

function count(arr, predicate) {
  if (!predicate) return arr.length;
  return filter(arr, predicate).length;
}

function sum(arr, key) {
  return arr.reduce((acc, item) => {
    const value = key ? get(item, key) : item;
    return acc + (typeof value === 'number' ? value : 0);
  }, 0);
}

function groupBy(arr, key) {
  const result = {};
  for (const item of arr) {
    const groupKey = typeof key === 'function' ? key(item) : get(item, key);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
  }
  return result;
}

function keyBy(arr, key) {
  const result = {};
  for (const item of arr) {
    const itemKey = typeof key === 'function' ? key(item) : get(item, key);
    result[itemKey] = item;
  }
  return result;
}

module.exports = {
  query,
  get,
  set,
  has,
  remove,
  flatten,
  unflatten,
  merge,
  deepMerge,
  diff,
  patch,
  clone,
  equals,
  validate,
  safeParse,
  stringify,
  format,
  minify,
  sortKeys,
  pick,
  omit,
  transform,
  filter,
  map: mapArray,
  find,
  findAll,
  count,
  sum,
  groupBy,
  keyBy
};
