import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import { FastifyInstance } from 'fastify';
import { buildApp } from '../src/app';

describe('Crypto Service API Tests', () => {
  let app: FastifyInstance;

  beforeAll(async () => {
    app = await buildApp();
    await app.ready();
  });

  afterAll(async () => {
    await app.close();
  });

  // ===========================================================================
  // Health Endpoints
  // ===========================================================================
  describe('Health Endpoints', () => {
    it('GET /health should return health status', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/health',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      // Health can be 'healthy' or 'degraded' (e.g., event loop lag during tests)
      // The important thing is that critical crypto module check passes
      expect(['healthy', 'degraded']).toContain(body.status);
      expect(body).toHaveProperty('timestamp');
      expect(body).toHaveProperty('version');
      expect(body).toHaveProperty('uptime');
      expect(body).toHaveProperty('checks');
      expect(Array.isArray(body.checks)).toBe(true);
      // Ensure crypto module check passes
      const cryptoCheck = body.checks.find((c: { name: string }) => c.name === 'crypto_module');
      expect(cryptoCheck).toBeDefined();
      expect(cryptoCheck.status).toBe('pass');
    });

    it('GET /health/ready should return readiness status', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/health/ready',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.ready).toBe(true);
      expect(body).toHaveProperty('checks');
    });

    it('GET /health/live should return liveness status', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/health/live',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.alive).toBe(true);
    });

    it('GET /metrics should return service metrics', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/metrics',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.service).toBe('crypto-service');
      expect(body).toHaveProperty('memory');
      expect(body).toHaveProperty('cpu');
      expect(body).toHaveProperty('system');
    });
  });

  // ===========================================================================
  // Encryption Endpoints
  // ===========================================================================
  describe('Encryption Endpoints', () => {
    it('POST /api/v1/encrypt should encrypt data with AES-256-GCM', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/encrypt',
        payload: {
          data: 'Hello, World!',
          key: 'test-encryption-key-12345',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty('encrypted');
      expect(body.data).toHaveProperty('iv');
      expect(body.data).toHaveProperty('tag');
      expect(body.data.algorithm).toBe('aes-256-gcm');
    });

    it('POST /api/v1/encrypt should encrypt data with AES-256-CBC', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/encrypt',
        payload: {
          data: 'Hello, World!',
          algorithm: 'aes-256-cbc',
          key: 'test-encryption-key-12345',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.algorithm).toBe('aes-256-cbc');
      expect(body.data).not.toHaveProperty('tag'); // CBC doesn't have auth tag
    });

    it('POST /api/v1/decrypt should decrypt data', async () => {
      // First encrypt
      const encryptResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/encrypt',
        payload: {
          data: 'Sensitive data',
          key: 'my-secret-key-12345',
        },
      });

      const encryptBody = JSON.parse(encryptResponse.payload);

      // Then decrypt
      const decryptResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/decrypt',
        payload: {
          encrypted: encryptBody.data.encrypted,
          iv: encryptBody.data.iv,
          tag: encryptBody.data.tag,
          key: 'my-secret-key-12345',
        },
      });

      expect(decryptResponse.statusCode).toBe(200);
      const decryptBody = JSON.parse(decryptResponse.payload);
      expect(decryptBody.success).toBe(true);
      expect(decryptBody.data.decrypted).toBe('Sensitive data');
    });

    it('POST /api/v1/encrypt should fail with empty data', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/encrypt',
        payload: {
          data: '',
        },
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(false);
      expect(body.error.code).toBe('VALIDATION_ERROR');
    });
  });

  // ===========================================================================
  // Hash Endpoints
  // ===========================================================================
  describe('Hash Endpoints', () => {
    it('POST /api/v1/hash should create SHA-256 hash', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/hash',
        payload: {
          data: 'Hello, World!',
          algorithm: 'sha256',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.algorithm).toBe('sha256');
      expect(body.data.hash).toBe(
        'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
      );
    });

    it('POST /api/v1/hash should create bcrypt hash', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/hash',
        payload: {
          data: 'password123',
          algorithm: 'bcrypt',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.algorithm).toBe('bcrypt');
      expect(body.data.hash).toMatch(/^\$2[aby]\$\d{2}\$/);
    });

    it('POST /api/v1/hash should create argon2 hash', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/hash',
        payload: {
          data: 'password123',
          algorithm: 'argon2',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.algorithm).toBe('argon2');
      expect(body.data.hash).toMatch(/^\$argon2/);
    });

    it('POST /api/v1/hash/verify should verify bcrypt hash', async () => {
      // First create hash
      const hashResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hash',
        payload: {
          data: 'mypassword',
          algorithm: 'bcrypt',
        },
      });

      const hashBody = JSON.parse(hashResponse.payload);

      // Then verify
      const verifyResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hash/verify',
        payload: {
          data: 'mypassword',
          hash: hashBody.data.hash,
        },
      });

      expect(verifyResponse.statusCode).toBe(200);
      const verifyBody = JSON.parse(verifyResponse.payload);
      expect(verifyBody.success).toBe(true);
      expect(verifyBody.data.valid).toBe(true);
    });

    it('POST /api/v1/hash/verify should reject wrong password', async () => {
      // First create hash
      const hashResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hash',
        payload: {
          data: 'correctpassword',
          algorithm: 'bcrypt',
        },
      });

      const hashBody = JSON.parse(hashResponse.payload);

      // Then verify with wrong password
      const verifyResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hash/verify',
        payload: {
          data: 'wrongpassword',
          hash: hashBody.data.hash,
        },
      });

      expect(verifyResponse.statusCode).toBe(200);
      const verifyBody = JSON.parse(verifyResponse.payload);
      expect(verifyBody.success).toBe(true);
      expect(verifyBody.data.valid).toBe(false);
    });
  });

  // ===========================================================================
  // JWT Endpoints
  // ===========================================================================
  describe('JWT Endpoints', () => {
    // Use the same secret for all JWT operations in tests
    const testSecret = process.env.JWT_SECRET || 'test-secret-key-for-testing-at-least-32-chars';

    it('POST /api/v1/jwt/generate should create a JWT', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/jwt/generate',
        payload: {
          payload: { userId: '123', role: 'admin' },
          secret: testSecret,
          expiresIn: '1h',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty('token');
      expect(body.data.token.split('.')).toHaveLength(3);
      expect(body.data).toHaveProperty('expiresAt');
    });

    it('POST /api/v1/jwt/verify should verify a valid JWT', async () => {
      // First generate
      const generateResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/jwt/generate',
        payload: {
          payload: { userId: '456' },
          secret: testSecret,
          expiresIn: '1h',
        },
      });

      const generateBody = JSON.parse(generateResponse.payload);

      // Then verify with the same secret
      const verifyResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/jwt/verify',
        payload: {
          token: generateBody.data.token,
          secret: testSecret,
        },
      });

      expect(verifyResponse.statusCode).toBe(200);
      const verifyBody = JSON.parse(verifyResponse.payload);
      expect(verifyBody.success).toBe(true);
      expect(verifyBody.data.valid).toBe(true);
      expect(verifyBody.data.payload).toHaveProperty('userId');
      expect(verifyBody.data.payload.userId).toBe('456');
    });

    it('POST /api/v1/jwt/verify should reject invalid JWT', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/jwt/verify',
        payload: {
          token: 'invalid.jwt.token',
          secret: testSecret,
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.valid).toBe(false);
    });

    it('POST /api/v1/jwt/decode should decode JWT without verification', async () => {
      // First generate
      const generateResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/jwt/generate',
        payload: {
          payload: { data: 'test' },
          secret: testSecret,
        },
      });

      const generateBody = JSON.parse(generateResponse.payload);

      // Then decode
      const decodeResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/jwt/decode',
        payload: {
          token: generateBody.data.token,
          complete: true,
        },
      });

      expect(decodeResponse.statusCode).toBe(200);
      const decodeBody = JSON.parse(decodeResponse.payload);
      expect(decodeBody.success).toBe(true);
      expect(decodeBody.data).toHaveProperty('header');
      expect(decodeBody.data).toHaveProperty('payload');
      expect(decodeBody.data.header).toHaveProperty('alg');
      expect(decodeBody.data.header.alg).toBe('HS256');
    });
  });

  // ===========================================================================
  // HMAC Endpoints
  // ===========================================================================
  describe('HMAC Endpoints', () => {
    const testKey = 'hmac-secret-key';

    it('POST /api/v1/hmac/sign should create HMAC signature', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/hmac/sign',
        payload: {
          data: 'message to sign',
          key: testKey,
          algorithm: 'sha256',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty('signature');
      expect(body.data.algorithm).toBe('sha256');
    });

    it('POST /api/v1/hmac/verify should verify valid signature', async () => {
      // First sign
      const signResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hmac/sign',
        payload: {
          data: 'important message',
          key: testKey,
        },
      });

      const signBody = JSON.parse(signResponse.payload);

      // Then verify
      const verifyResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hmac/verify',
        payload: {
          data: 'important message',
          signature: signBody.data.signature,
          key: testKey,
        },
      });

      expect(verifyResponse.statusCode).toBe(200);
      const verifyBody = JSON.parse(verifyResponse.payload);
      expect(verifyBody.success).toBe(true);
      expect(verifyBody.data.valid).toBe(true);
    });

    it('POST /api/v1/hmac/verify should reject tampered message', async () => {
      // First sign
      const signResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hmac/sign',
        payload: {
          data: 'original message',
          key: testKey,
        },
      });

      const signBody = JSON.parse(signResponse.payload);

      // Then verify with different message
      const verifyResponse = await app.inject({
        method: 'POST',
        url: '/api/v1/hmac/verify',
        payload: {
          data: 'tampered message',
          signature: signBody.data.signature,
          key: testKey,
        },
      });

      expect(verifyResponse.statusCode).toBe(200);
      const verifyBody = JSON.parse(verifyResponse.payload);
      expect(verifyBody.success).toBe(true);
      expect(verifyBody.data.valid).toBe(false);
    });
  });

  // ===========================================================================
  // Key Generation Endpoints
  // ===========================================================================
  describe('Key Generation Endpoints', () => {
    it('POST /api/v1/keys/generate should generate random key', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/keys/generate',
        payload: {
          length: 32,
          encoding: 'hex',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty('key');
      expect(body.data.key).toHaveLength(64); // 32 bytes = 64 hex chars
      expect(body.data.length).toBe(32);
      expect(body.data.encoding).toBe('hex');
    });

    it('POST /api/v1/keys/generate should generate base64 key', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/keys/generate',
        payload: {
          length: 16,
          encoding: 'base64',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.encoding).toBe('base64');
    });

    it('POST /api/v1/keys/generate should use default values', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/keys/generate',
        payload: {},
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(true);
      expect(body.data.length).toBe(32); // default
      expect(body.data.encoding).toBe('hex'); // default
    });
  });

  // ===========================================================================
  // Error Handling
  // ===========================================================================
  describe('Error Handling', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/nonexistent',
      });

      expect(response.statusCode).toBe(404);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(false);
      expect(body.error.code).toBe('NOT_FOUND');
    });

    it('should include request ID in all responses', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/encrypt',
        payload: {
          data: 'test',
          key: 'test-key-12345',
        },
      });

      expect(response.headers['x-request-id']).toBeDefined();
      const body = JSON.parse(response.payload);
      expect(body).toHaveProperty('requestId');
    });

    it('should validate required fields', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/hash',
        payload: {},
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.payload);
      expect(body.success).toBe(false);
      expect(body.error.code).toBe('VALIDATION_ERROR');
    });
  });

  // ===========================================================================
  // Documentation Endpoints
  // ===========================================================================
  describe('Documentation', () => {
    it('GET / should return service info', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.payload);
      expect(body.service).toBe('crypto-service');
      expect(body).toHaveProperty('endpoints');
    });

    it('GET /docs should return Swagger UI', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/docs',
      });

      // Swagger UI redirects or returns HTML
      expect([200, 302]).toContain(response.statusCode);
    });
  });
});
