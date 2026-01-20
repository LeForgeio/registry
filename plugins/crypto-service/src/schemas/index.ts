import Joi from 'joi';

// Encryption Schemas
export const encryptSchema = Joi.object({
  data: Joi.string().required().max(10_000_000).messages({
    'string.empty': 'Data is required',
    'string.max': 'Data exceeds maximum length of 10MB',
    'any.required': 'Data is required',
  }),
  algorithm: Joi.string()
    .valid('aes-256-gcm', 'aes-256-cbc', 'aes-128-gcm', 'aes-128-cbc')
    .default('aes-256-gcm'),
  key: Joi.string().min(8).max(256).optional().messages({
    'string.min': 'Key must be at least 8 characters',
    'string.max': 'Key exceeds maximum length of 256 characters',
  }),
});

export const decryptSchema = Joi.object({
  encrypted: Joi.string().required().messages({
    'string.empty': 'Encrypted data is required',
    'any.required': 'Encrypted data is required',
  }),
  iv: Joi.string().required().messages({
    'string.empty': 'IV is required',
    'any.required': 'IV is required',
  }),
  tag: Joi.string().when('algorithm', {
    is: Joi.string().pattern(/gcm/),
    then: Joi.required(),
    otherwise: Joi.optional(),
  }),
  algorithm: Joi.string()
    .valid('aes-256-gcm', 'aes-256-cbc', 'aes-128-gcm', 'aes-128-cbc')
    .default('aes-256-gcm'),
  key: Joi.string().min(8).max(256).optional(),
});

// Hash Schemas
export const hashSchema = Joi.object({
  data: Joi.string().required().max(10_000_000).messages({
    'string.empty': 'Data is required',
    'string.max': 'Data exceeds maximum length of 10MB',
    'any.required': 'Data is required',
  }),
  algorithm: Joi.string()
    .valid('sha256', 'sha512', 'sha384', 'sha1', 'md5', 'bcrypt', 'argon2')
    .default('sha256'),
  encoding: Joi.string().valid('hex', 'base64').default('hex'),
  options: Joi.object({
    rounds: Joi.number().integer().min(4).max(16).default(12),
    memoryCost: Joi.number().integer().min(1024).max(1048576).default(65536),
    timeCost: Joi.number().integer().min(1).max(10).default(3),
    parallelism: Joi.number().integer().min(1).max(16).default(4),
  }).default({}),
});

export const hashVerifySchema = Joi.object({
  data: Joi.string().required().max(10_000_000).messages({
    'string.empty': 'Data is required',
    'any.required': 'Data is required',
  }),
  hash: Joi.string().required().messages({
    'string.empty': 'Hash is required',
    'any.required': 'Hash is required',
  }),
  algorithm: Joi.string().valid('bcrypt', 'argon2').optional(),
});

// HMAC Schemas
export const hmacSignSchema = Joi.object({
  data: Joi.string().required().max(10_000_000).messages({
    'string.empty': 'Data is required',
    'any.required': 'Data is required',
  }),
  key: Joi.string().required().min(1).messages({
    'string.empty': 'Key is required',
    'any.required': 'Key is required',
  }),
  algorithm: Joi.string().valid('sha256', 'sha512', 'sha384', 'sha1').default('sha256'),
  encoding: Joi.string().valid('hex', 'base64').default('hex'),
});

export const hmacVerifySchema = Joi.object({
  data: Joi.string().required().max(10_000_000).messages({
    'string.empty': 'Data is required',
    'any.required': 'Data is required',
  }),
  key: Joi.string().required().min(1).messages({
    'string.empty': 'Key is required',
    'any.required': 'Key is required',
  }),
  signature: Joi.string().required().messages({
    'string.empty': 'Signature is required',
    'any.required': 'Signature is required',
  }),
  algorithm: Joi.string().valid('sha256', 'sha512', 'sha384', 'sha1').default('sha256'),
  encoding: Joi.string().valid('hex', 'base64').default('hex'),
});

// JWT Schemas
export const jwtGenerateSchema = Joi.object({
  payload: Joi.object().required().messages({
    'object.base': 'Payload must be an object',
    'any.required': 'Payload is required',
  }),
  expiresIn: Joi.alternatives()
    .try(
      Joi.string().pattern(/^\d+[smhdwMy]?$/),
      Joi.number().integer().positive()
    )
    .default('1h'),
  algorithm: Joi.string()
    .valid('HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512')
    .default('HS256'),
  secret: Joi.string().min(32).optional().messages({
    'string.min': 'Secret must be at least 32 characters for security',
  }),
  issuer: Joi.string().optional(),
  audience: Joi.string().optional(),
  subject: Joi.string().optional(),
});

export const jwtVerifySchema = Joi.object({
  token: Joi.string().required().messages({
    'string.empty': 'Token is required',
    'any.required': 'Token is required',
  }),
  secret: Joi.string().min(32).optional(),
  algorithms: Joi.array()
    .items(Joi.string().valid('HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512'))
    .default(['HS256']),
  issuer: Joi.string().optional(),
  audience: Joi.string().optional(),
  ignoreExpiration: Joi.boolean().default(false),
  clockTolerance: Joi.number().integer().min(0).max(300).default(0),
});

export const jwtDecodeSchema = Joi.object({
  token: Joi.string().required().messages({
    'string.empty': 'Token is required',
    'any.required': 'Token is required',
  }),
  complete: Joi.boolean().default(false),
});

// Key Generation Schema
export const generateKeySchema = Joi.object({
  length: Joi.number().integer().min(8).max(512).default(32),
  encoding: Joi.string().valid('hex', 'base64').default('hex'),
  type: Joi.string().valid('random', 'uuid').default('random'),
  count: Joi.number().integer().min(1).max(100).default(1),
});
