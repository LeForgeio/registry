import crypto from 'crypto';
import bcrypt from 'bcryptjs';
import argon2 from 'argon2';
import jwt, { JwtPayload, SignOptions, VerifyOptions, Algorithm } from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { config } from '../config';
import {
  EncryptionAlgorithm,
  EncryptResponse,
  DecryptResponse,
  HashAlgorithm,
  HashEncoding,
  HashResponse,
  HmacSignResponse,
  JwtAlgorithm,
  JwtGenerateResponse,
  JwtVerifyResponse,
} from '../types';

// ============================================================================
// Encryption Services
// ============================================================================

const deriveKey = (key: string, algorithm: EncryptionAlgorithm): Buffer => {
  const keyLength = algorithm.includes('128') ? 16 : 32;
  return crypto.createHash('sha256').update(key).digest().subarray(0, keyLength);
};

const getDefaultKey = (): string => {
  if (!config.jwt.secret) {
    throw new Error('No encryption key configured. Set JWT_SECRET environment variable.');
  }
  return config.jwt.secret;
};

export const encrypt = (
  data: string,
  algorithm: EncryptionAlgorithm = 'aes-256-gcm',
  userKey?: string
): EncryptResponse => {
  const key = userKey || getDefaultKey();
  const keyBuffer = deriveKey(key, algorithm);
  const ivLength = algorithm.includes('gcm') ? 12 : 16;
  const iv = crypto.randomBytes(ivLength);

  const cipher = crypto.createCipheriv(algorithm as crypto.CipherGCMTypes, keyBuffer, iv);

  let encrypted = cipher.update(data, 'utf8', 'base64');
  encrypted += cipher.final('base64');

  const response: EncryptResponse = {
    encrypted,
    iv: iv.toString('base64'),
    algorithm,
  };

  if (algorithm.includes('gcm')) {
    response.tag = (cipher as crypto.CipherGCM).getAuthTag().toString('base64');
  }

  return response;
};

export const decrypt = (
  encrypted: string,
  iv: string,
  algorithm: EncryptionAlgorithm = 'aes-256-gcm',
  tag?: string,
  userKey?: string
): DecryptResponse => {
  const key = userKey || getDefaultKey();
  const keyBuffer = deriveKey(key, algorithm);
  const ivBuffer = Buffer.from(iv, 'base64');

  const decipher = crypto.createDecipheriv(
    algorithm as crypto.CipherGCMTypes,
    keyBuffer,
    ivBuffer
  );

  if (algorithm.includes('gcm') && tag) {
    (decipher as crypto.DecipherGCM).setAuthTag(Buffer.from(tag, 'base64'));
  }

  let decrypted = decipher.update(encrypted, 'base64', 'utf8');
  decrypted += decipher.final('utf8');

  return {
    decrypted,
    algorithm,
  };
};

// ============================================================================
// Hash Services
// ============================================================================

export const hash = async (
  data: string,
  algorithm: HashAlgorithm = 'sha256',
  encoding: HashEncoding = 'hex',
  options?: {
    rounds?: number;
    memoryCost?: number;
    timeCost?: number;
    parallelism?: number;
  }
): Promise<HashResponse> => {
  let hashResult: string;
  let resultEncoding: HashEncoding | 'encoded' = encoding;

  switch (algorithm) {
    case 'bcrypt':
      hashResult = await bcrypt.hash(data, options?.rounds || config.crypto.bcryptRounds);
      resultEncoding = 'encoded';
      break;

    case 'argon2':
      hashResult = await argon2.hash(data, {
        memoryCost: options?.memoryCost || config.crypto.argon2MemoryCost,
        timeCost: options?.timeCost || config.crypto.argon2TimeCost,
        parallelism: options?.parallelism || config.crypto.argon2Parallelism,
        type: argon2.argon2id,
      });
      resultEncoding = 'encoded';
      break;

    default:
      hashResult = crypto
        .createHash(algorithm)
        .update(data)
        .digest(encoding as crypto.BinaryToTextEncoding);
      break;
  }

  return {
    hash: hashResult,
    algorithm,
    encoding: resultEncoding,
  };
};

export const verifyHash = async (
  data: string,
  hashValue: string,
  algorithm?: 'bcrypt' | 'argon2'
): Promise<boolean> => {
  // Auto-detect algorithm from hash format
  const detectedAlgorithm =
    algorithm ||
    (hashValue.startsWith('$2') ? 'bcrypt' : hashValue.startsWith('$argon2') ? 'argon2' : null);

  if (!detectedAlgorithm) {
    throw new Error('Could not detect hash algorithm. Please specify algorithm.');
  }

  switch (detectedAlgorithm) {
    case 'bcrypt':
      return bcrypt.compare(data, hashValue);
    case 'argon2':
      return argon2.verify(hashValue, data);
    default:
      throw new Error(`Unsupported hash verification algorithm: ${detectedAlgorithm}`);
  }
};

// ============================================================================
// HMAC Services
// ============================================================================

export const hmacSign = (
  data: string,
  key: string,
  algorithm: string = 'sha256',
  encoding: HashEncoding = 'hex'
): HmacSignResponse => {
  const signature = crypto
    .createHmac(algorithm, key)
    .update(data)
    .digest(encoding as crypto.BinaryToTextEncoding);

  return {
    signature,
    algorithm,
    encoding,
  };
};

export const hmacVerify = (
  data: string,
  key: string,
  signature: string,
  algorithm: string = 'sha256',
  encoding: HashEncoding = 'hex'
): boolean => {
  const expectedSignature = crypto
    .createHmac(algorithm, key)
    .update(data)
    .digest(encoding as crypto.BinaryToTextEncoding);

  // Use timing-safe comparison to prevent timing attacks
  try {
    const sigBuffer = Buffer.from(signature, encoding);
    const expectedBuffer = Buffer.from(expectedSignature, encoding);
    
    if (sigBuffer.length !== expectedBuffer.length) {
      return false;
    }
    
    return crypto.timingSafeEqual(sigBuffer, expectedBuffer);
  } catch {
    return false;
  }
};

// ============================================================================
// JWT Services
// ============================================================================

const getJwtSecret = (userSecret?: string): string => {
  const secret = userSecret || config.jwt.secret;
  if (!secret) {
    throw new Error('JWT secret is required. Set JWT_SECRET environment variable or provide secret.');
  }
  return secret;
};

export const generateJWT = (options: {
  payload: Record<string, unknown>;
  expiresIn?: string | number;
  algorithm?: JwtAlgorithm;
  secret?: string;
  issuer?: string;
  audience?: string;
  subject?: string;
  jwtid?: string;
}): JwtGenerateResponse => {
  const {
    payload,
    expiresIn = config.jwt.defaultExpiry,
    algorithm = config.jwt.defaultAlgorithm as JwtAlgorithm,
    secret: userSecret,
    issuer,
    audience,
    subject,
    jwtid,
  } = options;

  const secret = getJwtSecret(userSecret);

  const signOptions: SignOptions = {
    algorithm: algorithm as Algorithm,
    issuer: issuer || config.jwt.issuer,
  };

  // Handle expiresIn - can be number (seconds) or string (e.g. '1h', '2d')
  if (expiresIn !== undefined) {
    (signOptions as Record<string, unknown>).expiresIn = expiresIn;
  }

  if (audience) signOptions.audience = audience;
  if (subject) signOptions.subject = subject;
  if (jwtid) signOptions.jwtid = jwtid;

  const token = jwt.sign(payload, secret, signOptions);

  const decoded = jwt.decode(token, { complete: true }) as {
    header: { alg: string; typ: string };
    payload: JwtPayload;
  };

  return {
    token,
    expiresAt: decoded.payload.exp
      ? new Date(decoded.payload.exp * 1000).toISOString()
      : null,
    issuedAt: decoded.payload.iat
      ? new Date(decoded.payload.iat * 1000).toISOString()
      : null,
    algorithm,
  };
};

export const verifyJWT = (options: {
  token: string;
  secret?: string;
  algorithms?: JwtAlgorithm[];
  issuer?: string;
  audience?: string;
  ignoreExpiration?: boolean;
  clockTolerance?: number;
}): JwtVerifyResponse => {
  const {
    token,
    secret: userSecret,
    algorithms,
    issuer,
    audience,
    ignoreExpiration,
    clockTolerance,
  } = options;

  const secret = getJwtSecret(userSecret);

  const verifyOptions: VerifyOptions = {
    algorithms: (algorithms || ['HS256']) as Algorithm[],
    ignoreExpiration: ignoreExpiration || false,
    clockTolerance: clockTolerance || 0,
  };

  if (issuer) verifyOptions.issuer = issuer;
  if (audience) verifyOptions.audience = audience;

  try {
    const decoded = jwt.verify(token, secret, verifyOptions) as JwtPayload;

    return {
      valid: true,
      payload: decoded as Record<string, unknown>,
      expiresAt: decoded.exp ? new Date(decoded.exp * 1000).toISOString() : null,
      issuedAt: decoded.iat ? new Date(decoded.iat * 1000).toISOString() : null,
    };
  } catch (error) {
    const err = error as Error & { expiredAt?: Date };
    
    const errorMap: Record<string, { code: string; message: string }> = {
      TokenExpiredError: { code: 'JWT_EXPIRED', message: 'Token has expired' },
      JsonWebTokenError: { code: 'JWT_INVALID', message: 'Invalid token' },
      NotBeforeError: { code: 'JWT_NOT_ACTIVE', message: 'Token not yet active' },
    };

    const errorInfo = errorMap[err.name] || {
      code: 'JWT_VERIFICATION_FAILED',
      message: 'Token verification failed',
    };

    return {
      valid: false,
      error: errorInfo.code,
      message: errorInfo.message,
    };
  }
};

export const decodeJWT = (
  token: string,
  complete: boolean = false
): { header?: { alg: string; typ: string }; payload: Record<string, unknown> } => {
  const decoded = jwt.decode(token, { complete });

  if (!decoded) {
    throw new Error('Invalid JWT format');
  }

  if (complete) {
    const fullDecoded = decoded as { header: { alg: string; typ: string }; payload: JwtPayload };
    return {
      header: fullDecoded.header,
      payload: fullDecoded.payload as Record<string, unknown>,
    };
  }

  return { payload: decoded as Record<string, unknown> };
};

// ============================================================================
// Key Generation Services
// ============================================================================

export const generateKey = (
  length: number = 32,
  encoding: 'hex' | 'base64' | 'utf8' = 'hex'
): { key: string; length: number; encoding: string } => {
  const key = crypto.randomBytes(length).toString(encoding === 'utf8' ? 'base64' : encoding);
  return { key, length, encoding };
};

export const generateRandomKey = (
  length: number = 32,
  encoding: 'hex' | 'base64' = 'hex'
): string => {
  return crypto.randomBytes(length).toString(encoding);
};

export const generateUuid = (): string => {
  return uuidv4();
};

export const generateMultipleKeys = (
  count: number,
  length: number,
  encoding: 'hex' | 'base64',
  type: 'random' | 'uuid'
): string[] => {
  const keys: string[] = [];
  for (let i = 0; i < count; i++) {
    keys.push(type === 'uuid' ? generateUuid() : generateRandomKey(length, encoding));
  }
  return keys;
};
