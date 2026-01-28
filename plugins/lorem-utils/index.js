/**
 * Lorem Utilities - Embedded ForgeHook Plugin
 * Generate placeholder text, fake data, and sample content locally
 * No external API calls - all generated deterministically or with local randomness
 */

// ============================================================================
// LOREM IPSUM TEXT
// ============================================================================

const LOREM_WORDS = [
  'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
  'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
  'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
  'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
  'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
  'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
  'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
  'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum', 'perspiciatis', 'unde',
  'omnis', 'iste', 'natus', 'error', 'voluptatem', 'accusantium', 'doloremque',
  'laudantium', 'totam', 'rem', 'aperiam', 'eaque', 'ipsa', 'quae', 'ab', 'illo',
  'inventore', 'veritatis', 'quasi', 'architecto', 'beatae', 'vitae', 'dicta',
  'explicabo', 'nemo', 'ipsam', 'quia', 'voluptas', 'aspernatur', 'aut', 'odit',
  'fugit', 'consequuntur', 'magni', 'dolores', 'eos', 'ratione', 'sequi',
  'nesciunt', 'neque', 'porro', 'quisquam', 'dolorem', 'adipisci', 'numquam',
  'eius', 'modi', 'tempora', 'incidunt', 'magnam', 'aliquam', 'quaerat'
];

const CLASSIC_LOREM = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.';

// ============================================================================
// FUNNY/THEMED PLACEHOLDER TEXT
// ============================================================================

const BACON_WORDS = [
  'bacon', 'ipsum', 'dolor', 'amet', 'ribeye', 'pork', 'belly', 'ham', 'hock',
  'hamburger', 'sirloin', 'tenderloin', 'fatback', 'pig', 'shank', 'flank',
  'pancetta', 'drumstick', 'capicola', 'sausage', 'turkey', 'kielbasa',
  'chicken', 'beef', 'ribs', 'ground', 'round', 'filet', 'mignon', 'strip',
  'steak', 'brisket', 'chuck', 'short', 'loin', 'tri-tip', 'ball', 'tip',
  'prosciutto', 'andouille', 'corned', 'jerky', 'pastrami', 'salami', 'spare',
  'venison', 'buffalo', 'bresaola', 'meatball', 'meatloaf', 'tongue', 'alcatra',
  'boudin', 'burgdoggen', 'chislic', 'cupim', 'doner', 'frankfurter', 'jowl',
  'kevin', 'landjaeger', 'leberkas', 'picanha', 'porchetta', 'rump', 'shankle',
  'swine', 't-bone', 'turducken'
];

const HIPSTER_WORDS = [
  'artisan', 'craft', 'beer', 'vinyl', 'record', 'fixie', 'bicycle', 'kombucha',
  'avocado', 'toast', 'matcha', 'oat', 'milk', 'sustainable', 'ethical',
  'locally', 'sourced', 'farm', 'table', 'vintage', 'retro', 'aesthetic',
  'minimalist', 'curated', 'bespoke', 'authentic', 'artisanal', 'handcrafted',
  'organic', 'gluten-free', 'vegan', 'plant-based', 'cold-brew', 'pour-over',
  'single-origin', 'fair-trade', 'biodegradable', 'upcycled', 'reclaimed',
  'mid-century', 'modern', 'hygge', 'kinfolk', 'brooklyn', 'portland',
  'mustache', 'beard', 'flannel', 'denim', 'leather', 'canvas', 'tote',
  'typewriter', 'polaroid', 'film', 'analog', 'podcast', 'zine', 'letterpress'
];

const CORPORATE_WORDS = [
  'synergy', 'leverage', 'paradigm', 'shift', 'bandwidth', 'circle', 'back',
  'deep', 'dive', 'helicopter', 'view', 'move', 'needle', 'low-hanging', 'fruit',
  'value', 'add', 'core', 'competency', 'best', 'practice', 'stakeholder',
  'engagement', 'actionable', 'insights', 'deliverables', 'milestones', 'kpi',
  'roi', 'vertical', 'integration', 'horizontal', 'scalable', 'solution',
  'innovative', 'disruptive', 'bleeding', 'edge', 'cutting', 'proactive',
  'holistic', 'approach', 'ecosystem', 'touchpoint', 'alignment', 'optimize',
  'streamline', 'agile', 'methodology', 'sprint', 'scrum', 'standup', 'retro',
  'pivot', 'iterate', 'fail', 'fast', 'lean', 'startup', 'unicorn', 'runway'
];

const TECH_WORDS = [
  'cloud', 'native', 'serverless', 'microservices', 'kubernetes', 'docker',
  'container', 'devops', 'ci/cd', 'pipeline', 'api', 'graphql', 'rest',
  'webhook', 'oauth', 'jwt', 'encryption', 'blockchain', 'machine', 'learning',
  'artificial', 'intelligence', 'neural', 'network', 'deep', 'algorithm',
  'data', 'science', 'big', 'analytics', 'visualization', 'dashboard',
  'database', 'sql', 'nosql', 'mongodb', 'postgres', 'redis', 'cache',
  'cdn', 'edge', 'compute', 'lambda', 'function', 'event', 'driven',
  'architecture', 'monolith', 'distributed', 'system', 'fault', 'tolerant',
  'high', 'availability', 'load', 'balancer', 'auto', 'scaling'
];

const PIRATE_WORDS = [
  'ahoy', 'matey', 'avast', 'ye', 'landlubber', 'scallywag', 'buccaneer',
  'plunder', 'booty', 'treasure', 'doubloons', 'pieces', 'eight', 'jolly',
  'roger', 'skull', 'crossbones', 'walk', 'plank', 'shiver', 'timbers',
  'blimey', 'hornswaggle', 'seadog', 'swashbuckler', 'cutlass', 'cannon',
  'galleon', 'ship', 'captain', 'crew', 'deck', 'anchor', 'sail', 'mast',
  'port', 'starboard', 'bow', 'stern', 'rum', 'grog', 'parrot', 'eyepatch',
  'pegleg', 'hook', 'hand', 'buried', 'island', 'map', 'seven', 'seas'
];

// ============================================================================
// NAME DATA
// ============================================================================

const FIRST_NAMES = [
  'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
  'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph',
  'Jessica', 'Thomas', 'Sarah', 'Christopher', 'Karen', 'Charles', 'Nancy',
  'Daniel', 'Lisa', 'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra',
  'Emma', 'Olivia', 'Ava', 'Isabella', 'Sophia', 'Mia', 'Charlotte', 'Amelia',
  'Liam', 'Noah', 'Oliver', 'Elijah', 'Lucas', 'Mason', 'Logan', 'Alexander'
];

const LAST_NAMES = [
  'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
  'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
  'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
  'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores'
];

const COMPANY_SUFFIXES = ['Inc', 'LLC', 'Corp', 'Co', 'Ltd', 'Group', 'Solutions', 'Industries', 'Technologies', 'Systems'];
const COMPANY_PREFIXES = ['Global', 'Advanced', 'Dynamic', 'Innovative', 'Premier', 'Elite', 'Strategic', 'Unified'];
const COMPANY_CORES = ['Tech', 'Data', 'Cloud', 'Digital', 'Cyber', 'Net', 'Web', 'Soft', 'Logic', 'Core'];

const STREET_TYPES = ['Street', 'Avenue', 'Boulevard', 'Drive', 'Lane', 'Road', 'Way', 'Court', 'Place', 'Circle'];
const STREET_NAMES = ['Main', 'Oak', 'Maple', 'Cedar', 'Pine', 'Elm', 'Washington', 'Lincoln', 'Park', 'Lake', 'Hill', 'River'];

const CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'];
const STATES = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI'];

// ============================================================================
// SEEDED RANDOM NUMBER GENERATOR
// ============================================================================

class SeededRandom {
  constructor(seed = Date.now()) {
    this.seed = seed;
  }
  
  next() {
    this.seed = (this.seed * 1103515245 + 12345) & 0x7fffffff;
    return this.seed / 0x7fffffff;
  }
  
  nextInt(min, max) {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }
  
  pick(array) {
    return array[this.nextInt(0, array.length - 1)];
  }
  
  shuffle(array) {
    const result = [...array];
    for (let i = result.length - 1; i > 0; i--) {
      const j = this.nextInt(0, i);
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }
}

let rng = new SeededRandom();

/**
 * Set seed for reproducible output
 */
function setSeed(seed) {
  rng = new SeededRandom(seed);
}

/**
 * Reset to random seed
 */
function resetSeed() {
  rng = new SeededRandom();
}

// ============================================================================
// TEXT GENERATION FUNCTIONS
// ============================================================================

/**
 * Generate lorem ipsum words
 */
function words(input, options = {}) {
  const count = typeof input === 'number' ? input : (input?.count || input?.words || 10);
  const { startWithLorem = false, theme = 'lorem' } = typeof input === 'object' ? input : options;
  
  const wordList = getWordList(theme);
  const result = [];
  
  if (startWithLorem && theme === 'lorem') {
    result.push('Lorem', 'ipsum', 'dolor', 'sit', 'amet');
  }
  
  while (result.length < count) {
    result.push(rng.pick(wordList));
  }
  
  return result.slice(0, count).join(' ');
}

/**
 * Generate lorem ipsum sentences
 */
function sentences(input, options = {}) {
  const count = typeof input === 'number' ? input : (input?.count || input?.sentences || 3);
  const { theme = 'lorem', minWords = 8, maxWords = 15 } = typeof input === 'object' ? input : options;
  
  const result = [];
  const wordList = getWordList(theme);
  
  for (let i = 0; i < count; i++) {
    const wordCount = rng.nextInt(minWords, maxWords);
    const sentenceWords = [];
    
    for (let j = 0; j < wordCount; j++) {
      sentenceWords.push(rng.pick(wordList));
    }
    
    // Capitalize first letter
    sentenceWords[0] = sentenceWords[0].charAt(0).toUpperCase() + sentenceWords[0].slice(1);
    
    // Add comma occasionally
    if (wordCount > 6 && rng.next() > 0.6) {
      const commaPos = rng.nextInt(3, wordCount - 3);
      sentenceWords[commaPos] += ',';
    }
    
    result.push(sentenceWords.join(' ') + '.');
  }
  
  return result.join(' ');
}

/**
 * Generate lorem ipsum paragraphs
 */
function paragraphs(input, options = {}) {
  const count = typeof input === 'number' ? input : (input?.count || input?.paragraphs || 3);
  const { theme = 'lorem', minSentences = 4, maxSentences = 8, startWithLorem = true } = typeof input === 'object' ? input : options;
  
  const result = [];
  
  for (let i = 0; i < count; i++) {
    const sentenceCount = rng.nextInt(minSentences, maxSentences);
    let para = sentences({ count: sentenceCount, theme });
    
    // First paragraph starts with classic lorem
    if (i === 0 && startWithLorem && theme === 'lorem') {
      para = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' + para;
    }
    
    result.push(para);
  }
  
  return result.join('\n\n');
}

/**
 * Generate text of approximately N characters
 */
function characters(input, options = {}) {
  const count = typeof input === 'number' ? input : (input?.count || input?.characters || 100);
  const { theme = 'lorem' } = typeof input === 'object' ? input : options;
  
  let text = '';
  while (text.length < count) {
    text += sentences({ count: 1, theme }) + ' ';
  }
  
  return text.slice(0, count).trim();
}

/**
 * Get the classic Lorem Ipsum text
 */
function classic() {
  return CLASSIC_LOREM;
}

// ============================================================================
// FAKE DATA GENERATION
// ============================================================================

/**
 * Generate a random full name
 */
function name(input, options = {}) {
  const { gender, includeMiddle = false } = typeof input === 'object' ? input : options;
  
  const first = rng.pick(FIRST_NAMES);
  const last = rng.pick(LAST_NAMES);
  
  if (includeMiddle) {
    const middle = rng.pick(FIRST_NAMES);
    return `${first} ${middle} ${last}`;
  }
  
  return `${first} ${last}`;
}

/**
 * Generate a random first name
 */
function firstName() {
  return rng.pick(FIRST_NAMES);
}

/**
 * Generate a random last name
 */
function lastName() {
  return rng.pick(LAST_NAMES);
}

/**
 * Generate a random email
 */
function email(input, options = {}) {
  const { domain } = typeof input === 'object' ? input : options;
  
  const domains = domain ? [domain] : ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'example.com'];
  const first = rng.pick(FIRST_NAMES).toLowerCase();
  const last = rng.pick(LAST_NAMES).toLowerCase();
  const num = rng.nextInt(1, 99);
  
  const formats = [
    `${first}.${last}`,
    `${first}${last}`,
    `${first}_${last}`,
    `${first[0]}${last}`,
    `${first}${num}`,
    `${first}.${last}${num}`
  ];
  
  return `${rng.pick(formats)}@${rng.pick(domains)}`;
}

/**
 * Generate a random phone number
 */
function phone(input, options = {}) {
  const { format = '(###) ###-####', countryCode = false } = typeof input === 'object' ? input : options;
  
  let result = format.replace(/#/g, () => rng.nextInt(0, 9).toString());
  
  if (countryCode) {
    result = '+1 ' + result;
  }
  
  return result;
}

/**
 * Generate a random company name
 */
function company() {
  const style = rng.nextInt(1, 3);
  
  switch (style) {
    case 1:
      return `${rng.pick(LAST_NAMES)} ${rng.pick(COMPANY_SUFFIXES)}`;
    case 2:
      return `${rng.pick(COMPANY_PREFIXES)} ${rng.pick(COMPANY_CORES)} ${rng.pick(COMPANY_SUFFIXES)}`;
    default:
      return `${rng.pick(LAST_NAMES)} & ${rng.pick(LAST_NAMES)}`;
  }
}

/**
 * Generate a random street address
 */
function address() {
  const num = rng.nextInt(100, 9999);
  const street = rng.pick(STREET_NAMES);
  const type = rng.pick(STREET_TYPES);
  
  return `${num} ${street} ${type}`;
}

/**
 * Generate a random city
 */
function city() {
  return rng.pick(CITIES);
}

/**
 * Generate a random state abbreviation
 */
function state() {
  return rng.pick(STATES);
}

/**
 * Generate a random zip code
 */
function zipCode() {
  return rng.nextInt(10000, 99999).toString();
}

/**
 * Generate a full address
 */
function fullAddress() {
  return `${address()}, ${city()}, ${state()} ${zipCode()}`;
}

/**
 * Generate a random number
 */
function number(input, options = {}) {
  const { min = 0, max = 100, decimals = 0 } = typeof input === 'object' ? input : options;
  
  const num = rng.next() * (max - min) + min;
  return decimals > 0 ? parseFloat(num.toFixed(decimals)) : Math.floor(num);
}

/**
 * Generate a random boolean
 */
function boolean(input, options = {}) {
  const { likelihood = 0.5 } = typeof input === 'object' ? input : options;
  return rng.next() < likelihood;
}

/**
 * Generate a random date
 */
function date(input, options = {}) {
  const {
    from = new Date(2020, 0, 1),
    to = new Date(),
    format = 'iso'
  } = typeof input === 'object' ? input : options;
  
  const fromTime = new Date(from).getTime();
  const toTime = new Date(to).getTime();
  const randomTime = fromTime + rng.next() * (toTime - fromTime);
  const d = new Date(randomTime);
  
  switch (format) {
    case 'iso':
      return d.toISOString();
    case 'date':
      return d.toISOString().split('T')[0];
    case 'time':
      return d.toISOString().split('T')[1].split('.')[0];
    case 'unix':
      return Math.floor(d.getTime() / 1000);
    default:
      return d.toISOString();
  }
}

/**
 * Generate a random UUID
 */
function uuid() {
  const hex = () => rng.nextInt(0, 15).toString(16);
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = parseInt(hex(), 16);
    return c === 'x' ? hex() : ((r & 0x3) | 0x8).toString(16);
  });
}

/**
 * Generate a random color
 */
function color(input, options = {}) {
  const { format = 'hex' } = typeof input === 'object' ? input : options;
  
  const r = rng.nextInt(0, 255);
  const g = rng.nextInt(0, 255);
  const b = rng.nextInt(0, 255);
  
  switch (format) {
    case 'hex':
      return '#' + [r, g, b].map(c => c.toString(16).padStart(2, '0')).join('');
    case 'rgb':
      return `rgb(${r}, ${g}, ${b})`;
    case 'hsl':
      const max = Math.max(r, g, b) / 255;
      const min = Math.min(r, g, b) / 255;
      const l = (max + min) / 2;
      let h = 0, s = 0;
      
      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        
        if (max === r/255) h = ((g - b) / 255 / d + (g < b ? 6 : 0)) / 6;
        else if (max === g/255) h = ((b - r) / 255 / d + 2) / 6;
        else h = ((r - g) / 255 / d + 4) / 6;
      }
      
      return `hsl(${Math.round(h * 360)}, ${Math.round(s * 100)}%, ${Math.round(l * 100)}%)`;
    default:
      return '#' + [r, g, b].map(c => c.toString(16).padStart(2, '0')).join('');
  }
}

/**
 * Pick a random item from an array
 */
function pick(array) {
  if (!Array.isArray(array) || array.length === 0) {
    return null;
  }
  return rng.pick(array);
}

/**
 * Pick multiple random items from an array
 */
function pickMultiple(input, options = {}) {
  const array = Array.isArray(input) ? input : (input?.items || input?.array || []);
  const count = typeof input === 'object' ? (input.count || options.count || 1) : (options.count || 1);
  const unique = typeof input === 'object' ? (input.unique ?? true) : (options.unique ?? true);
  
  if (unique) {
    const shuffled = rng.shuffle(array);
    return shuffled.slice(0, Math.min(count, array.length));
  }
  
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(rng.pick(array));
  }
  return result;
}

/**
 * Generate an array of random items
 */
function generateArray(input, options = {}) {
  const { count = 10, generator = 'name' } = typeof input === 'object' ? input : options;
  
  const generators = {
    name, firstName, lastName, email, phone, company, address, city, state, zipCode,
    fullAddress, number, boolean, date, uuid, color
  };
  
  const gen = typeof generator === 'function' ? generator : generators[generator];
  
  if (!gen) {
    throw new Error(`Unknown generator: ${generator}`);
  }
  
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(gen(options));
  }
  return result;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getWordList(theme) {
  switch (theme?.toLowerCase()) {
    case 'bacon':
      return BACON_WORDS;
    case 'hipster':
      return HIPSTER_WORDS;
    case 'corporate':
    case 'business':
      return CORPORATE_WORDS;
    case 'tech':
    case 'technology':
      return TECH_WORDS;
    case 'pirate':
      return PIRATE_WORDS;
    default:
      return LOREM_WORDS;
  }
}

/**
 * Generate themed placeholder text
 */
function themed(theme, input, options = {}) {
  const count = typeof input === 'number' ? input : (input?.count || 3);
  const unit = typeof input === 'object' ? (input.unit || 'paragraphs') : 'paragraphs';
  
  const opts = { theme, ...options };
  
  switch (unit) {
    case 'words':
      return words({ count, ...opts });
    case 'sentences':
      return sentences({ count, ...opts });
    case 'paragraphs':
    default:
      return paragraphs({ count, ...opts });
  }
}

// Convenience theme functions
const bacon = (count, options) => themed('bacon', count, options);
const hipster = (count, options) => themed('hipster', count, options);
const corporate = (count, options) => themed('corporate', count, options);
const tech = (count, options) => themed('tech', count, options);
const pirate = (count, options) => themed('pirate', count, options);

module.exports = {
  // Seed control
  setSeed,
  resetSeed,
  
  // Text generation
  words,
  sentences,
  paragraphs,
  characters,
  classic,
  themed,
  
  // Themed shortcuts
  bacon,
  hipster,
  corporate,
  tech,
  pirate,
  
  // Fake data
  name,
  firstName,
  lastName,
  email,
  phone,
  company,
  address,
  city,
  state,
  zipCode,
  fullAddress,
  number,
  boolean,
  date,
  uuid,
  color,
  
  // Array utilities
  pick,
  pickMultiple,
  generateArray
};
