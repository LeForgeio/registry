/**
 * UUID Utilities - Embedded ForgeHook Plugin
 * Generate unique identifiers locally with cryptographically secure randomness
 */

// Crypto for secure random bytes
const crypto = typeof window !== 'undefined' ? window.crypto : require('crypto');

function getRandomBytes(length) {
  if (crypto.randomBytes) {
    return crypto.randomBytes(length);
  }
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return bytes;
}

function bytesToHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

// UUID v4 (random)
function uuidv4() {
  const bytes = getRandomBytes(16);
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // Version 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 1
  
  const hex = bytesToHex(bytes);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// UUID v1 (timestamp-based)
let _clockseq = null;
let _lastMSecs = 0;
let _lastNSecs = 0;

function uuidv1(options = {}) {
  const msecs = Date.now();
  let nsecs = _lastNSecs + 1;
  const dt = msecs - _lastMSecs + (nsecs - _lastNSecs) / 10000;
  
  if (dt < 0 || msecs > _lastMSecs) {
    nsecs = 0;
  }
  if (nsecs >= 10000) {
    throw new Error('uuid.v1(): Can\'t create more than 10M uuids/sec');
  }
  
  _lastMSecs = msecs;
  _lastNSecs = nsecs;
  
  if (_clockseq === null) {
    const rb = getRandomBytes(2);
    _clockseq = ((rb[0] << 8) | rb[1]) & 0x3fff;
  }
  
  // UUID epoch (Oct 15, 1582)
  const epoch = msecs + 12219292800000;
  const tl = ((epoch & 0xfffffff) * 10000 + nsecs) % 0x100000000;
  const tmh = ((epoch / 0x100000000) * 10000) & 0xfffffff;
  const tm = tmh & 0xffff;
  const thAndVersion = (tmh >> 16) | 0x1000;
  
  const node = getRandomBytes(6);
  node[0] |= 0x01; // Multicast bit
  
  const clockSeqHi = (_clockseq >> 8) | 0x80;
  const clockSeqLo = _clockseq & 0xff;
  
  const bytes = [
    (tl >> 24) & 0xff, (tl >> 16) & 0xff, (tl >> 8) & 0xff, tl & 0xff,
    (tm >> 8) & 0xff, tm & 0xff,
    (thAndVersion >> 8) & 0xff, thAndVersion & 0xff,
    clockSeqHi, clockSeqLo,
    ...node
  ];
  
  const hex = bytesToHex(bytes);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// UUID v5 (SHA-1 namespace)
function sha1(message) {
  if (crypto.createHash) {
    return crypto.createHash('sha1').update(message).digest();
  }
  // Simplified SHA-1 for browser (use SubtleCrypto in real impl)
  throw new Error('SHA-1 not available in this environment');
}

const DNS_NAMESPACE = '6ba7b810-9dad-11d1-80b4-00c04fd430c8';
const URL_NAMESPACE = '6ba7b811-9dad-11d1-80b4-00c04fd430c8';

function uuidv5(name, namespace = DNS_NAMESPACE) {
  const nsBytes = parseUUID(namespace);
  const nameBytes = Buffer.from(name, 'utf8');
  const bytes = sha1(Buffer.concat([nsBytes, nameBytes]));
  
  bytes[6] = (bytes[6] & 0x0f) | 0x50; // Version 5
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 1
  
  const hex = bytesToHex(bytes.slice(0, 16));
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// UUID v7 (sortable timestamp, draft RFC)
function uuidv7() {
  const timestamp = Date.now();
  const bytes = getRandomBytes(16);
  
  // 48-bit timestamp (ms)
  bytes[0] = (timestamp >> 40) & 0xff;
  bytes[1] = (timestamp >> 32) & 0xff;
  bytes[2] = (timestamp >> 24) & 0xff;
  bytes[3] = (timestamp >> 16) & 0xff;
  bytes[4] = (timestamp >> 8) & 0xff;
  bytes[5] = timestamp & 0xff;
  
  bytes[6] = (bytes[6] & 0x0f) | 0x70; // Version 7
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 1
  
  const hex = bytesToHex(bytes);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

// ULID (Universally Unique Lexicographically Sortable Identifier)
const ULID_CHARS = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

function ulid(seedTime = Date.now()) {
  let result = '';
  
  // Timestamp (10 chars, Crockford Base32)
  let time = seedTime;
  for (let i = 0; i < 10; i++) {
    result = ULID_CHARS[time % 32] + result;
    time = Math.floor(time / 32);
  }
  
  // Randomness (16 chars)
  const randomBytes = getRandomBytes(10);
  for (let i = 0; i < 16; i++) {
    const idx = Math.floor(i / 2);
    const shift = (i % 2) * 4;
    result += ULID_CHARS[(randomBytes[idx] >> shift) & 0x1f];
  }
  
  return result;
}

// NanoID
const NANOID_ALPHABET = 'useandom-26T198340PX75pxJACKVERYMINDBUSHWOLF_GQZbfghjklqvwyzrict';

function nanoid(size = 21, alphabet = NANOID_ALPHABET) {
  const bytes = getRandomBytes(size);
  let result = '';
  for (let i = 0; i < size; i++) {
    result += alphabet[bytes[i] % alphabet.length];
  }
  return result;
}

// CUID2 (Collision-resistant unique identifier)
function cuid2(length = 24) {
  const timestamp = Date.now().toString(36);
  const random = nanoid(length - timestamp.length - 1, 'abcdefghijklmnopqrstuvwxyz0123456789');
  return timestamp[0] + random + timestamp.slice(1);
}

// Snowflake ID (Twitter-style)
let _lastSnowflake = 0n;
let _snowflakeSeq = 0n;

function snowflake(options = {}) {
  const epoch = BigInt(options.epoch || 1609459200000);
  const machineId = BigInt(options.machineId || 1);
  const datacenterId = BigInt(options.datacenterId || 1);
  
  const timestamp = BigInt(Date.now()) - epoch;
  
  if (timestamp === _lastSnowflake) {
    _snowflakeSeq = (_snowflakeSeq + 1n) & 4095n;
    if (_snowflakeSeq === 0n) {
      // Wait for next millisecond
      while (BigInt(Date.now()) - epoch === timestamp) {}
    }
  } else {
    _snowflakeSeq = 0n;
  }
  _lastSnowflake = timestamp;
  
  const id = (timestamp << 22n) | ((datacenterId & 31n) << 17n) | ((machineId & 31n) << 12n) | _snowflakeSeq;
  return id.toString();
}

// Random string generators
function randomString(length = 16, options = {}) {
  const chars = options.alphabet || 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const bytes = getRandomBytes(length);
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars[bytes[i] % chars.length];
  }
  return result;
}

function randomHex(length = 32) {
  return bytesToHex(getRandomBytes(Math.ceil(length / 2))).slice(0, length);
}

function randomBase64(length = 32) {
  const bytes = getRandomBytes(Math.ceil(length * 0.75));
  if (Buffer) {
    return Buffer.from(bytes).toString('base64').slice(0, length);
  }
  return btoa(String.fromCharCode(...bytes)).slice(0, length);
}

function shortId(length = 8) {
  return randomString(length, { alphabet: '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz' });
}

// Validation and parsing
function isValidUUID(value) {
  if (typeof value !== 'string') return false;
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-7][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function isValidULID(value) {
  if (typeof value !== 'string') return false;
  return /^[0-9A-HJKMNP-TV-Z]{26}$/i.test(value);
}

function parseUUID(uuid) {
  const hex = uuid.replace(/-/g, '');
  if (hex.length !== 32) throw new Error('Invalid UUID');
  const bytes = new Uint8Array(16);
  for (let i = 0; i < 16; i++) {
    bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

function parseULID(ulid) {
  if (!isValidULID(ulid)) throw new Error('Invalid ULID');
  
  // Decode timestamp
  let timestamp = 0;
  for (let i = 0; i < 10; i++) {
    timestamp = timestamp * 32 + ULID_CHARS.indexOf(ulid[i].toUpperCase());
  }
  
  return {
    timestamp,
    date: new Date(timestamp),
    randomness: ulid.slice(10)
  };
}

// Nil UUID
const nil = '00000000-0000-0000-0000-000000000000';

// Alias
const uuid = uuidv4;

module.exports = {
  uuid,
  uuidv1,
  uuidv4,
  uuidv5,
  uuidv7,
  ulid,
  nanoid,
  cuid: cuid2,
  cuid2,
  snowflake,
  randomString,
  randomHex,
  randomBase64,
  shortId,
  isValidUUID,
  isValidULID,
  parseUUID,
  parseULID,
  nil,
  DNS_NAMESPACE,
  URL_NAMESPACE
};
