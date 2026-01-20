// Encryption Types
export type EncryptionAlgorithm = 'aes-256-gcm' | 'aes-256-cbc' | 'aes-128-gcm' | 'aes-128-cbc';

export interface EncryptRequest {
  data: string;
  algorithm?: EncryptionAlgorithm;
  key?: string;
}

export interface EncryptResponse {
  encrypted: string;
  iv: string;
  tag?: string;
  algorithm: EncryptionAlgorithm;
}

export interface DecryptRequest {
  encrypted: string;
  iv: string;
  tag?: string;
  algorithm?: EncryptionAlgorithm;
  key?: string;
}

export interface DecryptResponse {
  decrypted: string;
  algorithm: EncryptionAlgorithm;
}

// Hash Types
export type HashAlgorithm = 'sha256' | 'sha512' | 'sha384' | 'sha1' | 'md5' | 'bcrypt' | 'argon2';
export type HashEncoding = 'hex' | 'base64';

export interface HashRequest {
  data: string;
  algorithm?: HashAlgorithm;
  encoding?: HashEncoding;
  options?: {
    rounds?: number;       // bcrypt
    memoryCost?: number;   // argon2
    timeCost?: number;     // argon2
    parallelism?: number;  // argon2
  };
}

export interface HashResponse {
  hash: string;
  algorithm: HashAlgorithm;
  encoding: HashEncoding | 'encoded';
}

export interface HashVerifyRequest {
  data: string;
  hash: string;
  algorithm?: 'bcrypt' | 'argon2';
}

export interface HashVerifyResponse {
  valid: boolean;
  algorithm: string;
}

// HMAC Types
export interface HmacSignRequest {
  data: string;
  key: string;
  algorithm?: 'sha256' | 'sha512' | 'sha384' | 'sha1';
  encoding?: HashEncoding;
}

export interface HmacSignResponse {
  signature: string;
  algorithm: string;
  encoding: HashEncoding;
}

export interface HmacVerifyRequest {
  data: string;
  key: string;
  signature: string;
  algorithm?: 'sha256' | 'sha512' | 'sha384' | 'sha1';
  encoding?: HashEncoding;
}

export interface HmacVerifyResponse {
  valid: boolean;
  algorithm: string;
}

// JWT Types
export type JwtAlgorithm = 'HS256' | 'HS384' | 'HS512' | 'RS256' | 'RS384' | 'RS512';

export interface JwtGenerateRequest {
  payload: Record<string, unknown>;
  expiresIn?: string | number;
  algorithm?: JwtAlgorithm;
  secret?: string;
  issuer?: string;
  audience?: string;
  subject?: string;
}

export interface JwtGenerateResponse {
  token: string;
  expiresAt: string | null;
  issuedAt: string | null;
  algorithm: JwtAlgorithm;
}

export interface JwtVerifyRequest {
  token: string;
  secret?: string;
  algorithms?: JwtAlgorithm[];
  issuer?: string;
  audience?: string;
  ignoreExpiration?: boolean;
  clockTolerance?: number;
}

export interface JwtVerifyResponse {
  valid: boolean;
  payload?: Record<string, unknown>;
  expiresAt?: string | null;
  issuedAt?: string | null;
  error?: string;
  message?: string;
}

export interface JwtDecodeRequest {
  token: string;
  complete?: boolean;
}

export interface JwtDecodeResponse {
  header?: {
    alg: string;
    typ: string;
  };
  payload: Record<string, unknown>;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  requestId: string;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{
    field: string;
    message: string;
  }>;
}

// Health Check Types
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  uptime: number;
  timestamp: string;
  checks?: {
    [key: string]: {
      status: 'pass' | 'fail';
      message?: string;
    };
  };
}

// Key Generation Types
export interface GenerateKeyRequest {
  length?: number;
  encoding?: 'hex' | 'base64';
  type?: 'random' | 'uuid';
  count?: number;
}

export interface GenerateKeyResponse {
  key?: string;
  keys?: string[];
  length: number;
  encoding: string;
}
