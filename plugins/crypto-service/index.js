/**
 * Crypto Service - Embedded ForgeHook
 * 
 * Comprehensive cryptographic operations using Node.js built-in crypto module.
 * Zero external dependencies for maximum compatibility and security.
 * 
 * @version 1.0.0
 * @license MIT
 */

const crypto = require('crypto');

// ============================================================================
// HASHING FUNCTIONS
// ============================================================================

/**
 * Hash data using SHA-1, SHA-256, SHA-512, or MD5
 * @param {string} data - Data to hash
 * @param {string} algorithm - Hash algorithm (sha1, sha256, sha512, md5)
 * @param {string} encoding - Output encoding (hex, base64)
 * @returns {string} Hash digest
 */
function hash(data, algorithm = 'sha256', encoding = 'hex') {
  const validAlgorithms = ['sha1', 'sha256', 'sha512', 'md5', 'sha384', 'sha3-256', 'sha3-512'];
  if (!validAlgorithms.includes(algorithm)) {
    throw new Error(`Invalid algorithm. Supported: ${validAlgorithms.join(', ')}`);
  }
  return crypto.createHash(algorithm).update(String(data)).digest(encoding);
}

/**
 * Calculate hash/checksum of file data (base64 encoded)
 * @param {string} fileData - Base64 encoded file data
 * @param {string} algorithm - Hash algorithm
 * @returns {string} File hash
 */
function hashFile(fileData, algorithm = 'sha256') {
  const buffer = Buffer.from(fileData, 'base64');
  return crypto.createHash(algorithm).update(buffer).digest('hex');
}

// ============================================================================
// ENCRYPTION FUNCTIONS
// ============================================================================

/**
 * Derive a key from a password/passphrase
 * @private
 */
function _deriveKeyInternal(key, algorithm) {
  const keyLength = algorithm.includes('128') ? 16 : 32;
  return crypto.createHash('sha256').update(String(key)).digest().subarray(0, keyLength);
}

/**
 * Encrypt data using AES (GCM or CBC mode)
 * @param {string} data - Data to encrypt
 * @param {string} key - Encryption key
 * @param {string} algorithm - Algorithm (aes-256-gcm, aes-256-cbc, aes-128-gcm, aes-128-cbc)
 * @returns {object} { encrypted, iv, tag?, algorithm }
 */
function encrypt(data, key, algorithm = 'aes-256-gcm') {
  if (!data) throw new Error('Data is required');
  if (!key) throw new Error('Key is required');
  
  const validAlgorithms = ['aes-256-gcm', 'aes-256-cbc', 'aes-128-gcm', 'aes-128-cbc'];
  if (!validAlgorithms.includes(algorithm)) {
    throw new Error(`Invalid algorithm. Supported: ${validAlgorithms.join(', ')}`);
  }
  
  const keyBuffer = _deriveKeyInternal(key, algorithm);
  const ivLength = algorithm.includes('gcm') ? 12 : 16;
  const iv = crypto.randomBytes(ivLength);
  
  const cipher = crypto.createCipheriv(algorithm, keyBuffer, iv);
  
  let encrypted = cipher.update(String(data), 'utf8', 'base64');
  encrypted += cipher.final('base64');
  
  const result = {
    encrypted,
    iv: iv.toString('base64'),
    algorithm
  };
  
  if (algorithm.includes('gcm')) {
    result.tag = cipher.getAuthTag().toString('base64');
  }
  
  return result;
}

/**
 * Decrypt AES encrypted data
 * @param {string} encrypted - Base64 encrypted data
 * @param {string} key - Encryption key
 * @param {string} iv - Base64 initialization vector
 * @param {string} tag - Base64 auth tag (required for GCM)
 * @param {string} algorithm - Algorithm
 * @returns {string} Decrypted plaintext
 */
function decrypt(encrypted, key, iv, tag = null, algorithm = 'aes-256-gcm') {
  if (!encrypted) throw new Error('Encrypted data is required');
  if (!key) throw new Error('Key is required');
  if (!iv) throw new Error('IV is required');
  
  const keyBuffer = _deriveKeyInternal(key, algorithm);
  const ivBuffer = Buffer.from(iv, 'base64');
  
  const decipher = crypto.createDecipheriv(algorithm, keyBuffer, ivBuffer);
  
  if (algorithm.includes('gcm')) {
    if (!tag) throw new Error('Auth tag is required for GCM mode');
    decipher.setAuthTag(Buffer.from(tag, 'base64'));
  }
  
  let decrypted = decipher.update(encrypted, 'base64', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}

// ============================================================================
// JWT FUNCTIONS
// ============================================================================

/**
 * Base64URL encode
 * @private
 */
function _base64UrlEncode(data) {
  const base64 = Buffer.from(data).toString('base64');
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

/**
 * Base64URL decode
 * @private
 */
function _base64UrlDecode(data) {
  let base64 = data.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4) base64 += '=';
  return Buffer.from(base64, 'base64').toString('utf8');
}

/**
 * Parse duration string to seconds
 * @private
 */
function _parseDuration(duration) {
  if (typeof duration === 'number') return duration;
  
  const match = String(duration).match(/^(\d+)(s|m|h|d|w)$/);
  if (!match) throw new Error(`Invalid duration format: ${duration}`);
  
  const value = parseInt(match[1], 10);
  const unit = match[2];
  
  const multipliers = { s: 1, m: 60, h: 3600, d: 86400, w: 604800 };
  return value * multipliers[unit];
}

/**
 * Generate a JWT token
 * @param {object} payload - JWT payload/claims
 * @param {string} secret - Signing secret
 * @param {string} expiresIn - Expiration time (e.g., '1h', '7d')
 * @param {string} algorithm - Algorithm (HS256, HS384, HS512)
 * @param {string} issuer - Token issuer
 * @param {string} audience - Token audience
 * @param {string} subject - Token subject
 * @returns {object} { token, expiresAt, issuedAt }
 */
function jwtSign(payload, secret, expiresIn = '1h', algorithm = 'HS256', issuer = null, audience = null, subject = null) {
  if (!payload || typeof payload !== 'object') throw new Error('Payload must be an object');
  if (!secret) throw new Error('Secret is required');
  
  const algMap = {
    'HS256': 'sha256',
    'HS384': 'sha384',
    'HS512': 'sha512'
  };
  
  if (!algMap[algorithm]) {
    throw new Error(`Invalid algorithm. Supported: ${Object.keys(algMap).join(', ')}`);
  }
  
  const now = Math.floor(Date.now() / 1000);
  const exp = now + _parseDuration(expiresIn);
  
  const header = { alg: algorithm, typ: 'JWT' };
  
  const claims = {
    ...payload,
    iat: now,
    exp: exp
  };
  
  if (issuer) claims.iss = issuer;
  if (audience) claims.aud = audience;
  if (subject) claims.sub = subject;
  
  const headerEncoded = _base64UrlEncode(JSON.stringify(header));
  const payloadEncoded = _base64UrlEncode(JSON.stringify(claims));
  
  const signatureInput = `${headerEncoded}.${payloadEncoded}`;
  const signature = crypto
    .createHmac(algMap[algorithm], secret)
    .update(signatureInput)
    .digest('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
  
  return {
    token: `${signatureInput}.${signature}`,
    expiresAt: new Date(exp * 1000).toISOString(),
    issuedAt: new Date(now * 1000).toISOString()
  };
}

/**
 * Verify and decode a JWT token
 * @param {string} token - JWT token
 * @param {string} secret - Signing secret
 * @param {string[]} algorithms - Allowed algorithms
 * @param {string} issuer - Expected issuer
 * @param {string} audience - Expected audience
 * @returns {object} { valid, payload?, error?, message? }
 */
function jwtVerify(token, secret, algorithms = ['HS256'], issuer = null, audience = null) {
  if (!token) throw new Error('Token is required');
  if (!secret) throw new Error('Secret is required');
  
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return { valid: false, error: 'JWT_MALFORMED', message: 'Token must have 3 parts' };
    }
    
    const [headerEncoded, payloadEncoded, signatureEncoded] = parts;
    
    const header = JSON.parse(_base64UrlDecode(headerEncoded));
    const payload = JSON.parse(_base64UrlDecode(payloadEncoded));
    
    // Check algorithm
    if (!algorithms.includes(header.alg)) {
      return { valid: false, error: 'JWT_INVALID_ALGORITHM', message: `Algorithm ${header.alg} not allowed` };
    }
    
    const algMap = { 'HS256': 'sha256', 'HS384': 'sha384', 'HS512': 'sha512' };
    
    // Verify signature
    const signatureInput = `${headerEncoded}.${payloadEncoded}`;
    const expectedSignature = crypto
      .createHmac(algMap[header.alg], secret)
      .update(signatureInput)
      .digest('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
    
    if (signatureEncoded !== expectedSignature) {
      return { valid: false, error: 'JWT_INVALID_SIGNATURE', message: 'Signature verification failed' };
    }
    
    // Check expiration
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      return { valid: false, error: 'JWT_EXPIRED', message: 'Token has expired' };
    }
    
    // Check not before
    if (payload.nbf && payload.nbf > now) {
      return { valid: false, error: 'JWT_NOT_ACTIVE', message: 'Token not yet active' };
    }
    
    // Check issuer
    if (issuer && payload.iss !== issuer) {
      return { valid: false, error: 'JWT_INVALID_ISSUER', message: 'Invalid issuer' };
    }
    
    // Check audience
    if (audience) {
      const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
      if (!aud.includes(audience)) {
        return { valid: false, error: 'JWT_INVALID_AUDIENCE', message: 'Invalid audience' };
      }
    }
    
    return {
      valid: true,
      payload,
      expiresAt: payload.exp ? new Date(payload.exp * 1000).toISOString() : null,
      issuedAt: payload.iat ? new Date(payload.iat * 1000).toISOString() : null
    };
    
  } catch (e) {
    return { valid: false, error: 'JWT_PARSE_ERROR', message: e.message };
  }
}

/**
 * Decode a JWT without verification
 * @param {string} token - JWT token
 * @returns {object} { header, payload }
 */
function jwtDecode(token) {
  if (!token) throw new Error('Token is required');
  
  const parts = token.split('.');
  if (parts.length !== 3) {
    throw new Error('Invalid JWT format');
  }
  
  return {
    header: JSON.parse(_base64UrlDecode(parts[0])),
    payload: JSON.parse(_base64UrlDecode(parts[1]))
  };
}

// ============================================================================
// HMAC FUNCTIONS
// ============================================================================

/**
 * Create HMAC signature
 * @param {string} data - Data to sign
 * @param {string} key - HMAC key
 * @param {string} algorithm - Hash algorithm
 * @param {string} encoding - Output encoding (hex, base64)
 * @returns {string} HMAC signature
 */
function hmacSign(data, key, algorithm = 'sha256', encoding = 'hex') {
  if (!data) throw new Error('Data is required');
  if (!key) throw new Error('Key is required');
  
  return crypto.createHmac(algorithm, key).update(String(data)).digest(encoding);
}

/**
 * Verify HMAC signature (timing-safe comparison)
 * @param {string} data - Original data
 * @param {string} signature - Signature to verify
 * @param {string} key - HMAC key
 * @param {string} algorithm - Hash algorithm
 * @param {string} encoding - Signature encoding
 * @returns {boolean} True if signature is valid
 */
function hmacVerify(data, signature, key, algorithm = 'sha256', encoding = 'hex') {
  if (!data || !signature || !key) return false;
  
  try {
    const expectedSignature = crypto.createHmac(algorithm, key).update(String(data)).digest(encoding);
    
    const sigBuffer = Buffer.from(signature, encoding);
    const expectedBuffer = Buffer.from(expectedSignature, encoding);
    
    if (sigBuffer.length !== expectedBuffer.length) return false;
    
    return crypto.timingSafeEqual(sigBuffer, expectedBuffer);
  } catch {
    return false;
  }
}

// ============================================================================
// RANDOM & KEY GENERATION
// ============================================================================

/**
 * Generate cryptographically secure random bytes
 * @param {number} length - Number of bytes
 * @param {string} encoding - Output encoding (hex, base64)
 * @returns {string} Random bytes
 */
function randomBytes(length = 32, encoding = 'hex') {
  return crypto.randomBytes(length).toString(encoding);
}

/**
 * Generate a UUID v4
 * @returns {string} UUID v4 string
 */
function uuid() {
  // Use crypto.randomUUID() if available (Node 14.17+), otherwise manual generation
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  const bytes = crypto.randomBytes(16);
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // Version 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant
  
  const hex = bytes.toString('hex');
  return [
    hex.slice(0, 8),
    hex.slice(8, 12),
    hex.slice(12, 16),
    hex.slice(16, 20),
    hex.slice(20, 32)
  ].join('-');
}

/**
 * Derive encryption key from password using PBKDF2
 * @param {string} password - Password
 * @param {string} salt - Salt (generated if not provided)
 * @param {number} iterations - Iterations
 * @param {number} keyLength - Key length in bytes
 * @param {string} digest - Hash algorithm
 * @returns {object} { key, salt }
 */
function deriveKey(password, salt = null, iterations = 100000, keyLength = 32, digest = 'sha256') {
  if (!password) throw new Error('Password is required');
  
  const saltBuffer = salt ? Buffer.from(salt, 'hex') : crypto.randomBytes(16);
  const key = crypto.pbkdf2Sync(password, saltBuffer, iterations, keyLength, digest);
  
  return {
    key: key.toString('hex'),
    salt: saltBuffer.toString('hex')
  };
}

/**
 * Generate a secure random password
 * @param {number} length - Password length
 * @param {object} options - { uppercase, lowercase, numbers, symbols }
 * @returns {string} Generated password
 */
function generatePassword(length = 16, options = {}) {
  const {
    uppercase = true,
    lowercase = true,
    numbers = true,
    symbols = true
  } = options;
  
  let chars = '';
  if (uppercase) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  if (lowercase) chars += 'abcdefghijklmnopqrstuvwxyz';
  if (numbers) chars += '0123456789';
  if (symbols) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';
  
  if (!chars) throw new Error('At least one character type must be enabled');
  
  const bytes = crypto.randomBytes(length);
  let password = '';
  
  for (let i = 0; i < length; i++) {
    password += chars[bytes[i] % chars.length];
  }
  
  return password;
}

// ============================================================================
// ENCODING FUNCTIONS
// ============================================================================

/**
 * Encode string to Base64
 * @param {string} data - Data to encode
 * @param {boolean} urlSafe - Use URL-safe Base64
 * @returns {string} Base64 encoded string
 */
function base64Encode(data, urlSafe = false) {
  let encoded = Buffer.from(String(data)).toString('base64');
  if (urlSafe) {
    encoded = encoded.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  }
  return encoded;
}

/**
 * Decode Base64 string
 * @param {string} data - Base64 data
 * @param {boolean} urlSafe - Is URL-safe Base64
 * @returns {string} Decoded string
 */
function base64Decode(data, urlSafe = false) {
  let base64 = data;
  if (urlSafe) {
    base64 = data.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) base64 += '=';
  }
  return Buffer.from(base64, 'base64').toString('utf8');
}

/**
 * Encode string to hexadecimal
 * @param {string} data - Data to encode
 * @returns {string} Hex encoded string
 */
function hexEncode(data) {
  return Buffer.from(String(data)).toString('hex');
}

/**
 * Decode hexadecimal string
 * @param {string} data - Hex data
 * @returns {string} Decoded string
 */
function hexDecode(data) {
  return Buffer.from(data, 'hex').toString('utf8');
}

/**
 * Timing-safe string comparison
 * @param {string} a - First string
 * @param {string} b - Second string
 * @returns {boolean} True if strings are equal
 */
function compareStrings(a, b) {
  try {
    const bufA = Buffer.from(String(a));
    const bufB = Buffer.from(String(b));
    
    if (bufA.length !== bufB.length) return false;
    
    return crypto.timingSafeEqual(bufA, bufB);
  } catch {
    return false;
  }
}

// ============================================================================
// KEY PAIR GENERATION & ASYMMETRIC CRYPTO
// ============================================================================

/**
 * Generate RSA, ECDSA, or Ed25519 key pair
 * @param {string} type - Key type: 'rsa', 'ec', 'ed25519'
 * @param {object} options - { modulusLength (RSA), namedCurve (EC), passphrase }
 * @returns {object} { publicKey, privateKey }
 */
function generateKeyPair(type = 'rsa', options = {}) {
  const {
    modulusLength = 2048,
    namedCurve = 'prime256v1',
    passphrase = null,
    format = 'pem'
  } = options;
  
  let keyOptions;
  
  switch (type.toLowerCase()) {
    case 'rsa':
      keyOptions = {
        modulusLength,
        publicKeyEncoding: { type: 'spki', format },
        privateKeyEncoding: { 
          type: 'pkcs8', 
          format,
          ...(passphrase && { cipher: 'aes-256-cbc', passphrase })
        }
      };
      return crypto.generateKeyPairSync('rsa', keyOptions);
      
    case 'ec':
    case 'ecdsa':
      keyOptions = {
        namedCurve,
        publicKeyEncoding: { type: 'spki', format },
        privateKeyEncoding: { 
          type: 'pkcs8', 
          format,
          ...(passphrase && { cipher: 'aes-256-cbc', passphrase })
        }
      };
      return crypto.generateKeyPairSync('ec', keyOptions);
      
    case 'ed25519':
      keyOptions = {
        publicKeyEncoding: { type: 'spki', format },
        privateKeyEncoding: { 
          type: 'pkcs8', 
          format,
          ...(passphrase && { cipher: 'aes-256-cbc', passphrase })
        }
      };
      return crypto.generateKeyPairSync('ed25519', keyOptions);
      
    default:
      throw new Error(`Unsupported key type: ${type}. Use 'rsa', 'ec', or 'ed25519'`);
  }
}

/**
 * Encrypt data using RSA public key
 * @param {string} data - Data to encrypt
 * @param {string} publicKey - PEM-formatted public key
 * @param {string} padding - Padding scheme: 'oaep' or 'pkcs1'
 * @returns {string} Base64 encrypted data
 */
function rsaEncrypt(data, publicKey, padding = 'oaep') {
  if (!data) throw new Error('Data is required');
  if (!publicKey) throw new Error('Public key is required');
  
  const paddingScheme = padding === 'pkcs1' 
    ? crypto.constants.RSA_PKCS1_PADDING 
    : crypto.constants.RSA_PKCS1_OAEP_PADDING;
  
  const encrypted = crypto.publicEncrypt(
    { key: publicKey, padding: paddingScheme },
    Buffer.from(data)
  );
  
  return encrypted.toString('base64');
}

/**
 * Decrypt data using RSA private key
 * @param {string} encrypted - Base64 encrypted data
 * @param {string} privateKey - PEM-formatted private key
 * @param {string} padding - Padding scheme: 'oaep' or 'pkcs1'
 * @param {string} passphrase - Private key passphrase (if encrypted)
 * @returns {string} Decrypted plaintext
 */
function rsaDecrypt(encrypted, privateKey, padding = 'oaep', passphrase = null) {
  if (!encrypted) throw new Error('Encrypted data is required');
  if (!privateKey) throw new Error('Private key is required');
  
  const paddingScheme = padding === 'pkcs1' 
    ? crypto.constants.RSA_PKCS1_PADDING 
    : crypto.constants.RSA_PKCS1_OAEP_PADDING;
  
  const keyOptions = { key: privateKey, padding: paddingScheme };
  if (passphrase) keyOptions.passphrase = passphrase;
  
  const decrypted = crypto.privateDecrypt(keyOptions, Buffer.from(encrypted, 'base64'));
  
  return decrypted.toString('utf8');
}

/**
 * Create digital signature
 * @param {string} data - Data to sign
 * @param {string} privateKey - PEM-formatted private key
 * @param {string} algorithm - Signature algorithm (sha256, sha384, sha512)
 * @param {string} passphrase - Private key passphrase
 * @returns {string} Base64 signature
 */
function sign(data, privateKey, algorithm = 'sha256', passphrase = null) {
  if (!data) throw new Error('Data is required');
  if (!privateKey) throw new Error('Private key is required');
  
  const signer = crypto.createSign(algorithm);
  signer.update(data);
  
  const keyOptions = passphrase ? { key: privateKey, passphrase } : privateKey;
  
  return signer.sign(keyOptions, 'base64');
}

/**
 * Verify digital signature
 * @param {string} data - Original data
 * @param {string} signature - Base64 signature
 * @param {string} publicKey - PEM-formatted public key
 * @param {string} algorithm - Signature algorithm
 * @returns {boolean} True if signature is valid
 */
function verify(data, signature, publicKey, algorithm = 'sha256') {
  if (!data || !signature || !publicKey) return false;
  
  try {
    const verifier = crypto.createVerify(algorithm);
    verifier.update(data);
    return verifier.verify(publicKey, signature, 'base64');
  } catch {
    return false;
  }
}

// ============================================================================
// TOTP/HOTP (Two-Factor Authentication)
// ============================================================================

/**
 * Generate TOTP secret for 2FA
 * @param {number} length - Secret length in bytes
 * @returns {object} { secret, base32, otpauthUrl }
 */
function totpGenerateSecret(length = 20, options = {}) {
  const { issuer = 'LeForge', accountName = 'user' } = options;
  
  const secret = crypto.randomBytes(length);
  const base32Secret = _base32Encode(secret);
  
  const otpauthUrl = `otpauth://totp/${encodeURIComponent(issuer)}:${encodeURIComponent(accountName)}?secret=${base32Secret}&issuer=${encodeURIComponent(issuer)}&algorithm=SHA1&digits=6&period=30`;
  
  return {
    secret: secret.toString('hex'),
    base32: base32Secret,
    otpauthUrl
  };
}

/**
 * Generate TOTP code
 * @param {string} secret - Hex or base32 secret
 * @param {object} options - { digits, period, algorithm, timestamp }
 * @returns {string} TOTP code
 */
function totp(secret, options = {}) {
  const {
    digits = 6,
    period = 30,
    algorithm = 'sha1',
    timestamp = Date.now()
  } = options;
  
  const counter = Math.floor(timestamp / 1000 / period);
  return _generateOTP(secret, counter, digits, algorithm);
}

/**
 * Verify TOTP code
 * @param {string} token - TOTP code to verify
 * @param {string} secret - Secret key
 * @param {object} options - { window, digits, period, algorithm }
 * @returns {object} { valid, delta }
 */
function totpVerify(token, secret, options = {}) {
  const {
    window = 1,
    digits = 6,
    period = 30,
    algorithm = 'sha1',
    timestamp = Date.now()
  } = options;
  
  const counter = Math.floor(timestamp / 1000 / period);
  
  for (let i = -window; i <= window; i++) {
    const expectedToken = _generateOTP(secret, counter + i, digits, algorithm);
    if (compareStrings(token, expectedToken)) {
      return { valid: true, delta: i };
    }
  }
  
  return { valid: false, delta: null };
}

/**
 * Generate HOTP code
 * @param {string} secret - Secret key
 * @param {number} counter - Counter value
 * @param {object} options - { digits, algorithm }
 * @returns {string} HOTP code
 */
function hotp(secret, counter, options = {}) {
  const { digits = 6, algorithm = 'sha1' } = options;
  return _generateOTP(secret, counter, digits, algorithm);
}

/**
 * Internal OTP generation
 * @private
 */
function _generateOTP(secret, counter, digits, algorithm) {
  // Convert secret from hex or base32
  let secretBuffer;
  if (/^[A-Z2-7]+=*$/i.test(secret)) {
    secretBuffer = _base32Decode(secret);
  } else {
    secretBuffer = Buffer.from(secret, 'hex');
  }
  
  // Convert counter to 8-byte buffer (big-endian)
  const counterBuffer = Buffer.alloc(8);
  counterBuffer.writeBigInt64BE(BigInt(counter));
  
  // Generate HMAC
  const hmac = crypto.createHmac(algorithm, secretBuffer);
  hmac.update(counterBuffer);
  const hmacResult = hmac.digest();
  
  // Dynamic truncation
  const offset = hmacResult[hmacResult.length - 1] & 0x0f;
  const binary = (
    ((hmacResult[offset] & 0x7f) << 24) |
    ((hmacResult[offset + 1] & 0xff) << 16) |
    ((hmacResult[offset + 2] & 0xff) << 8) |
    (hmacResult[offset + 3] & 0xff)
  );
  
  const otp = binary % Math.pow(10, digits);
  return otp.toString().padStart(digits, '0');
}

/**
 * Base32 encode
 * @private
 */
function _base32Encode(buffer) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let result = '';
  let bits = 0;
  let value = 0;
  
  for (const byte of buffer) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      bits -= 5;
      result += alphabet[(value >> bits) & 0x1f];
    }
  }
  
  if (bits > 0) {
    result += alphabet[(value << (5 - bits)) & 0x1f];
  }
  
  return result;
}

/**
 * Base32 decode
 * @private
 */
function _base32Decode(str) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  str = str.toUpperCase().replace(/=+$/, '');
  
  let bits = 0;
  let value = 0;
  const output = [];
  
  for (const char of str) {
    const index = alphabet.indexOf(char);
    if (index === -1) continue;
    
    value = (value << 5) | index;
    bits += 5;
    
    if (bits >= 8) {
      bits -= 8;
      output.push((value >> bits) & 0xff);
    }
  }
  
  return Buffer.from(output);
}

// ============================================================================
// SCRYPT KEY DERIVATION
// ============================================================================

/**
 * Derive key using scrypt (memory-hard)
 * @param {string} password - Password
 * @param {string} salt - Salt (generated if not provided)
 * @param {object} options - { N, r, p, keyLength }
 * @returns {object} { key, salt }
 */
function scryptDerive(password, salt = null, options = {}) {
  if (!password) throw new Error('Password is required');
  
  const {
    N = 16384,      // CPU/memory cost parameter (power of 2)
    r = 8,          // Block size
    p = 1,          // Parallelization
    keyLength = 32
  } = options;
  
  const saltBuffer = salt ? Buffer.from(salt, 'hex') : crypto.randomBytes(16);
  const key = crypto.scryptSync(password, saltBuffer, keyLength, { N, r, p });
  
  return {
    key: key.toString('hex'),
    salt: saltBuffer.toString('hex'),
    params: { N, r, p, keyLength }
  };
}

// ============================================================================
// HIGH-LEVEL PASSWORD FUNCTIONS
// ============================================================================

/**
 * Hash a password with auto-generated salt (for storage)
 * Uses scrypt with secure defaults
 * @param {string} password - Password to hash
 * @returns {string} Encoded hash string (contains salt and params)
 */
function hashPassword(password) {
  if (!password) throw new Error('Password is required');
  
  const salt = crypto.randomBytes(16);
  const N = 16384;
  const r = 8;
  const p = 1;
  const keyLength = 32;
  
  const hash = crypto.scryptSync(password, salt, keyLength, { N, r, p });
  
  // Format: $scrypt$N$r$p$salt$hash
  return `$scrypt$${N}$${r}$${p}$${salt.toString('base64')}$${hash.toString('base64')}`;
}

/**
 * Verify a password against a hash
 * @param {string} password - Password to verify
 * @param {string} hashString - Encoded hash string
 * @returns {boolean} True if password matches
 */
function verifyPassword(password, hashString) {
  if (!password || !hashString) return false;
  
  try {
    const parts = hashString.split('$');
    if (parts[1] !== 'scrypt') return false;
    
    const N = parseInt(parts[2]);
    const r = parseInt(parts[3]);
    const p = parseInt(parts[4]);
    const salt = Buffer.from(parts[5], 'base64');
    const expectedHash = Buffer.from(parts[6], 'base64');
    
    const hash = crypto.scryptSync(password, salt, expectedHash.length, { N, r, p });
    
    return crypto.timingSafeEqual(hash, expectedHash);
  } catch {
    return false;
  }
}

// ============================================================================
// OBJECT ENCRYPTION
// ============================================================================

/**
 * Encrypt a JSON object
 * @param {object} obj - Object to encrypt
 * @param {string} key - Encryption key
 * @returns {string} Encrypted string (contains all needed data for decryption)
 */
function encryptObject(obj, key) {
  if (!obj || typeof obj !== 'object') throw new Error('Object is required');
  if (!key) throw new Error('Key is required');
  
  const jsonStr = JSON.stringify(obj);
  const result = encrypt(jsonStr, key, 'aes-256-gcm');
  
  // Combine into single string for easy storage/transmission
  return `${result.iv}:${result.tag}:${result.encrypted}`;
}

/**
 * Decrypt a JSON object
 * @param {string} encryptedStr - Encrypted string from encryptObject
 * @param {string} key - Encryption key
 * @returns {object} Decrypted object
 */
function decryptObject(encryptedStr, key) {
  if (!encryptedStr) throw new Error('Encrypted string is required');
  if (!key) throw new Error('Key is required');
  
  const [iv, tag, encrypted] = encryptedStr.split(':');
  if (!iv || !tag || !encrypted) throw new Error('Invalid encrypted string format');
  
  const decrypted = decrypt(encrypted, key, iv, tag, 'aes-256-gcm');
  return JSON.parse(decrypted);
}

// ============================================================================
// CHECKSUM FUNCTIONS
// ============================================================================

/**
 * Calculate CRC32 checksum
 * @param {string|Buffer} data - Data to checksum
 * @returns {string} CRC32 as hex string
 */
function crc32(data) {
  const buffer = Buffer.isBuffer(data) ? data : Buffer.from(data);
  
  // CRC32 lookup table
  const table = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let j = 0; j < 8; j++) {
      c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    }
    table[i] = c;
  }
  
  let crc = 0xFFFFFFFF;
  for (const byte of buffer) {
    crc = table[(crc ^ byte) & 0xFF] ^ (crc >>> 8);
  }
  
  return ((crc ^ 0xFFFFFFFF) >>> 0).toString(16).padStart(8, '0');
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  // Hashing
  hash,
  hashFile,
  crc32,
  
  // Symmetric Encryption
  encrypt,
  decrypt,
  encryptObject,
  decryptObject,
  
  // Asymmetric Crypto
  generateKeyPair,
  rsaEncrypt,
  rsaDecrypt,
  sign,
  verify,
  
  // JWT
  jwtSign,
  jwtVerify,
  jwtDecode,
  
  // HMAC
  hmacSign,
  hmacVerify,
  
  // TOTP/HOTP (2FA)
  totpGenerateSecret,
  totp,
  totpVerify,
  hotp,
  
  // Key Derivation
  deriveKey,
  scryptDerive,
  hashPassword,
  verifyPassword,
  
  // Random
  randomBytes,
  uuid,
  generatePassword,
  
  // Encoding
  base64Encode,
  base64Decode,
  hexEncode,
  hexDecode,
  compareStrings
};
