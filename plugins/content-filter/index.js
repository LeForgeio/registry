/**
 * Content Filter - Embedded ForgeHook Plugin
 * Profanity filtering and content moderation locally
 * No external API calls - uses local word lists
 */

// ============================================================================
// DEFAULT WORD LISTS
// ============================================================================

// Common profanity words (obfuscated in source, will match variations)
const DEFAULT_PROFANITY = [
  'fuck', 'shit', 'ass', 'damn', 'hell', 'bitch', 'bastard', 'crap',
  'dick', 'cock', 'pussy', 'cunt', 'whore', 'slut', 'piss', 'fag',
  'nigger', 'nigga', 'retard', 'twat', 'wank', 'bollocks', 'arse',
  'asshole', 'motherfucker', 'bullshit', 'horseshit', 'dumbass',
  'jackass', 'dipshit', 'shithead', 'fuckhead', 'dickhead', 'asswipe'
];

// Slurs and hate speech terms
const DEFAULT_SLURS = [
  'nigger', 'nigga', 'chink', 'spic', 'wetback', 'kike', 'gook',
  'jap', 'beaner', 'cracker', 'honky', 'gringo', 'fag', 'faggot',
  'dyke', 'tranny', 'retard', 'cripple', 'midget'
];

// Common leetspeak substitutions
const LEET_MAP = {
  '4': 'a', '@': 'a', '8': 'b', '3': 'e', '1': 'i', '!': 'i',
  '0': 'o', '5': 's', '$': 's', '7': 't', '+': 't', '2': 'z'
};

// ============================================================================
// FILTER CONFIGURATION
// ============================================================================

let customWordList = [];
let customWhitelist = [];
let configOptions = {
  filterProfanity: true,
  filterSlurs: true,
  detectLeetspeak: true,
  detectPartialMatch: false,
  caseSensitive: false,
  replacement: '*',
  preserveLength: true
};

/**
 * Configure the content filter
 */
function configure(options = {}) {
  configOptions = { ...configOptions, ...options };
  
  if (options.customWords) {
    customWordList = Array.isArray(options.customWords) ? options.customWords : [];
  }
  if (options.whitelist) {
    customWhitelist = Array.isArray(options.whitelist) ? options.whitelist : [];
  }
  
  return configOptions;
}

/**
 * Add words to the custom filter list
 */
function addWords(words) {
  const toAdd = Array.isArray(words) ? words : [words];
  customWordList = [...new Set([...customWordList, ...toAdd])];
  return customWordList.length;
}

/**
 * Remove words from the custom filter list
 */
function removeWords(words) {
  const toRemove = new Set(Array.isArray(words) ? words : [words]);
  customWordList = customWordList.filter(w => !toRemove.has(w));
  return customWordList.length;
}

/**
 * Add words to whitelist (will never be filtered)
 */
function addToWhitelist(words) {
  const toAdd = Array.isArray(words) ? words : [words];
  customWhitelist = [...new Set([...customWhitelist, ...toAdd])];
  return customWhitelist.length;
}

/**
 * Get current word lists
 */
function getWordLists() {
  return {
    profanity: DEFAULT_PROFANITY.length,
    slurs: DEFAULT_SLURS.length,
    custom: customWordList.length,
    whitelist: customWhitelist.length
  };
}

// ============================================================================
// CORE FILTERING FUNCTIONS
// ============================================================================

/**
 * Get all words to filter based on current config
 */
function getFilterWords(options = {}) {
  const opts = { ...configOptions, ...options };
  let words = [...customWordList];
  
  if (opts.filterProfanity) {
    words = [...words, ...DEFAULT_PROFANITY];
  }
  if (opts.filterSlurs) {
    words = [...words, ...DEFAULT_SLURS];
  }
  
  return [...new Set(words)];
}

/**
 * Normalize text for matching (handle leetspeak, case, etc.)
 */
function normalizeText(text, options = {}) {
  const opts = { ...configOptions, ...options };
  let normalized = text;
  
  if (!opts.caseSensitive) {
    normalized = normalized.toLowerCase();
  }
  
  if (opts.detectLeetspeak) {
    normalized = normalized.split('').map(c => LEET_MAP[c] || c).join('');
  }
  
  return normalized;
}

/**
 * Check if text contains profanity
 */
function containsProfanity(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  const opts = { ...configOptions, ...options };
  
  // Check whitelist first
  const normalizedText = normalizeText(text, opts);
  const words = getFilterWords(opts);
  
  for (const word of words) {
    const normalizedWord = normalizeText(word, opts);
    
    if (opts.detectPartialMatch) {
      if (normalizedText.includes(normalizedWord)) {
        // Check it's not whitelisted
        if (!isWhitelisted(word, opts)) {
          return true;
        }
      }
    } else {
      // Word boundary match
      const regex = new RegExp(`\\b${escapeRegex(normalizedWord)}\\b`, opts.caseSensitive ? '' : 'i');
      if (regex.test(normalizedText)) {
        if (!isWhitelisted(word, opts)) {
          return true;
        }
      }
    }
  }
  
  return false;
}

/**
 * Check if a word is whitelisted
 */
function isWhitelisted(word, options = {}) {
  const opts = { ...configOptions, ...options };
  const normalizedWord = opts.caseSensitive ? word : word.toLowerCase();
  
  return customWhitelist.some(w => {
    const normalizedWhitelist = opts.caseSensitive ? w : w.toLowerCase();
    return normalizedWord === normalizedWhitelist;
  });
}

/**
 * Find all profanity in text
 */
function findProfanity(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  const opts = { ...configOptions, ...options };
  
  const found = [];
  const words = getFilterWords(opts);
  const normalizedText = normalizeText(text, opts);
  
  for (const word of words) {
    const normalizedWord = normalizeText(word, opts);
    
    if (opts.detectPartialMatch) {
      let index = normalizedText.indexOf(normalizedWord);
      while (index !== -1) {
        if (!isWhitelisted(word, opts)) {
          const original = text.slice(index, index + word.length);
          found.push({
            word: normalizedWord,
            original,
            index,
            category: categorizeWord(word)
          });
        }
        index = normalizedText.indexOf(normalizedWord, index + 1);
      }
    } else {
      const regex = new RegExp(`\\b(${escapeRegex(normalizedWord)})\\b`, 'gi');
      let match;
      while ((match = regex.exec(normalizedText)) !== null) {
        if (!isWhitelisted(word, opts)) {
          found.push({
            word: normalizedWord,
            original: text.slice(match.index, match.index + match[0].length),
            index: match.index,
            category: categorizeWord(word)
          });
        }
      }
    }
  }
  
  // Remove duplicates and sort by index
  const unique = [];
  const seen = new Set();
  for (const item of found.sort((a, b) => a.index - b.index)) {
    const key = `${item.index}-${item.word}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(item);
    }
  }
  
  return unique;
}

/**
 * Categorize a word
 */
function categorizeWord(word) {
  const lower = word.toLowerCase();
  if (DEFAULT_SLURS.includes(lower)) return 'slur';
  if (DEFAULT_PROFANITY.includes(lower)) return 'profanity';
  return 'custom';
}

/**
 * Filter/censor profanity in text
 */
function filterProfanity(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  const opts = { ...configOptions, ...options };
  
  const found = findProfanity(text, opts);
  
  if (found.length === 0) {
    return {
      filtered: text,
      changed: false,
      count: 0,
      found: []
    };
  }
  
  let result = text;
  let offset = 0;
  
  // Sort by index descending to replace from end first
  const sorted = [...found].sort((a, b) => b.index - a.index);
  
  for (const item of sorted) {
    const replacement = opts.preserveLength 
      ? opts.replacement.repeat(item.original.length)
      : opts.replacement;
    
    result = result.slice(0, item.index) + replacement + result.slice(item.index + item.original.length);
  }
  
  return {
    filtered: result,
    changed: true,
    count: found.length,
    found: found.map(f => f.original)
  };
}

/**
 * Clean text (alias for filterProfanity)
 */
function clean(input, options = {}) {
  return filterProfanity(input, options).filtered;
}

/**
 * Check text and return detailed analysis
 */
function analyze(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  const opts = { ...configOptions, ...options };
  
  const found = findProfanity(text, opts);
  
  const categories = {
    profanity: 0,
    slur: 0,
    custom: 0
  };
  
  found.forEach(f => {
    categories[f.category]++;
  });
  
  const severity = found.some(f => f.category === 'slur') ? 'high' 
    : found.length > 3 ? 'medium' 
    : found.length > 0 ? 'low' 
    : 'none';
  
  return {
    clean: found.length === 0,
    severity,
    totalFound: found.length,
    categories,
    matches: found,
    wordCount: text.split(/\s+/).length,
    characterCount: text.length
  };
}

/**
 * Rate content safety (0-100)
 */
function rateSafety(input, options = {}) {
  const analysis = analyze(input, options);
  
  let score = 100;
  
  // Deduct for each profanity found
  score -= analysis.categories.profanity * 5;
  
  // Deduct more for slurs
  score -= analysis.categories.slur * 20;
  
  // Deduct for custom words
  score -= analysis.categories.custom * 5;
  
  return {
    score: Math.max(0, Math.min(100, score)),
    rating: score >= 90 ? 'safe' : score >= 70 ? 'mild' : score >= 50 ? 'moderate' : 'unsafe',
    analysis
  };
}

// ============================================================================
// ADDITIONAL CONTENT CHECKS
// ============================================================================

/**
 * Check for personal information patterns
 */
function detectPII(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  
  const patterns = {
    email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
    phone: /\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
    ssn: /\b\d{3}[-]?\d{2}[-]?\d{4}\b/g,
    creditCard: /\b(?:\d{4}[-\s]?){3}\d{4}\b/g,
    ipAddress: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g
  };
  
  const found = {};
  let totalCount = 0;
  
  for (const [type, pattern] of Object.entries(patterns)) {
    const matches = text.match(pattern) || [];
    if (matches.length > 0) {
      found[type] = matches;
      totalCount += matches.length;
    }
  }
  
  return {
    hasPII: totalCount > 0,
    count: totalCount,
    found
  };
}

/**
 * Check for spam patterns
 */
function detectSpam(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  
  const indicators = [];
  let spamScore = 0;
  
  // Check for excessive caps
  const capsRatio = (text.match(/[A-Z]/g) || []).length / text.length;
  if (capsRatio > 0.5 && text.length > 20) {
    indicators.push('excessive_caps');
    spamScore += 20;
  }
  
  // Check for repeated characters
  if (/(.)\1{4,}/.test(text)) {
    indicators.push('repeated_characters');
    spamScore += 15;
  }
  
  // Check for multiple exclamation/question marks
  if (/[!?]{3,}/.test(text)) {
    indicators.push('excessive_punctuation');
    spamScore += 10;
  }
  
  // Check for common spam words
  const spamWords = ['free', 'winner', 'congratulations', 'prize', 'click here', 
    'limited time', 'act now', 'urgent', 'buy now', 'order now', 'subscribe',
    'unsubscribe', 'click below', 'special offer', 'exclusive deal'];
  
  const lowerText = text.toLowerCase();
  const foundSpamWords = spamWords.filter(w => lowerText.includes(w));
  if (foundSpamWords.length > 0) {
    indicators.push('spam_keywords');
    spamScore += foundSpamWords.length * 5;
  }
  
  // Check for URLs
  const urls = text.match(/https?:\/\/[^\s]+/g) || [];
  if (urls.length > 2) {
    indicators.push('multiple_urls');
    spamScore += 15;
  }
  
  return {
    isSpam: spamScore >= 40,
    score: Math.min(100, spamScore),
    indicators,
    urlCount: urls.length
  };
}

/**
 * Sanitize text (remove PII, filter profanity)
 */
function sanitize(input, options = {}) {
  const text = typeof input === 'object' ? (input.text || input.content || input.data) : input;
  const opts = {
    filterProfanity: true,
    removePII: true,
    ...options
  };
  
  let result = text;
  const changes = [];
  
  // Remove PII
  if (opts.removePII) {
    const pii = detectPII(result);
    for (const [type, matches] of Object.entries(pii.found)) {
      for (const match of matches) {
        const replacement = `[${type.toUpperCase()}_REMOVED]`;
        result = result.replace(match, replacement);
        changes.push({ type: 'pii', original: match, replacement });
      }
    }
  }
  
  // Filter profanity
  if (opts.filterProfanity) {
    const filtered = filterProfanity(result, opts);
    if (filtered.changed) {
      result = filtered.filtered;
      filtered.found.forEach(word => {
        changes.push({ type: 'profanity', original: word });
      });
    }
  }
  
  return {
    sanitized: result,
    changes,
    changeCount: changes.length
  };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Test a specific word against the filter
 */
function testWord(word, options = {}) {
  return containsProfanity(word, options);
}

/**
 * Get replacement string for a word
 */
function censorWord(word, options = {}) {
  const opts = { ...configOptions, ...options };
  return opts.preserveLength 
    ? opts.replacement.repeat(word.length)
    : opts.replacement;
}

module.exports = {
  // Configuration
  configure,
  addWords,
  removeWords,
  addToWhitelist,
  getWordLists,
  
  // Core filtering
  containsProfanity,
  findProfanity,
  filterProfanity,
  clean,
  
  // Analysis
  analyze,
  rateSafety,
  
  // Additional checks
  detectPII,
  detectSpam,
  sanitize,
  
  // Utilities
  testWord,
  censorWord
};
