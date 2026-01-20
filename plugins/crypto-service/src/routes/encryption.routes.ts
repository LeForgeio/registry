import { FastifyPluginAsync } from 'fastify';
import { encryptSchema, decryptSchema } from '../schemas';
import { encrypt, decrypt } from '../services';
import { EncryptRequest, DecryptRequest } from '../types';

export const encryptionRoutes: FastifyPluginAsync = async (fastify) => {
  // POST /api/v1/encrypt
  fastify.post<{ Body: EncryptRequest }>(
    '/encrypt',
    {
      schema: {
        description: 'Encrypt data using AES encryption',
        tags: ['Encryption'],
        body: {
          type: 'object',
          required: ['data'],
          properties: {
            data: { type: 'string', description: 'Data to encrypt' },
            algorithm: {
              type: 'string',
              enum: ['aes-256-gcm', 'aes-256-cbc', 'aes-128-gcm', 'aes-128-cbc'],
              default: 'aes-256-gcm',
              description: 'Encryption algorithm',
            },
            key: { type: 'string', description: 'Optional encryption key (min 8 chars)' },
          },
        },
        response: {
          200: {
            type: 'object',
            properties: {
              success: { type: 'boolean' },
              data: {
                type: 'object',
                properties: {
                  encrypted: { type: 'string' },
                  iv: { type: 'string' },
                  tag: { type: 'string' },
                  algorithm: { type: 'string' },
                },
              },
              requestId: { type: 'string' },
              timestamp: { type: 'string' },
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { error, value } = encryptSchema.validate(request.body, {
        abortEarly: false,
        stripUnknown: true,
      });

      if (error) {
        return reply.status(400).send({
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input data',
            details: error.details.map((d) => ({
              field: d.path.join('.'),
              message: d.message,
            })),
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }

      try {
        const { data, algorithm, key } = value;
        const result = encrypt(data, algorithm, key);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'Encryption failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'ENCRYPTION_ERROR',
            message: err instanceof Error ? err.message : 'Encryption failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );

  // POST /api/v1/decrypt
  fastify.post<{ Body: DecryptRequest }>(
    '/decrypt',
    {
      schema: {
        description: 'Decrypt data encrypted with AES encryption',
        tags: ['Encryption'],
        body: {
          type: 'object',
          required: ['encrypted', 'iv'],
          properties: {
            encrypted: { type: 'string', description: 'Base64 encoded encrypted data' },
            iv: { type: 'string', description: 'Base64 encoded initialization vector' },
            tag: { type: 'string', description: 'Base64 encoded auth tag (required for GCM)' },
            algorithm: {
              type: 'string',
              enum: ['aes-256-gcm', 'aes-256-cbc', 'aes-128-gcm', 'aes-128-cbc'],
              default: 'aes-256-gcm',
            },
            key: { type: 'string', description: 'Decryption key' },
          },
        },
        response: {
          200: {
            type: 'object',
            properties: {
              success: { type: 'boolean' },
              data: {
                type: 'object',
                properties: {
                  decrypted: { type: 'string' },
                  algorithm: { type: 'string' },
                },
              },
              requestId: { type: 'string' },
              timestamp: { type: 'string' },
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { error, value } = decryptSchema.validate(request.body, {
        abortEarly: false,
        stripUnknown: true,
      });

      if (error) {
        return reply.status(400).send({
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input data',
            details: error.details.map((d) => ({
              field: d.path.join('.'),
              message: d.message,
            })),
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }

      try {
        const { encrypted, iv, tag, algorithm, key } = value;
        const result = decrypt(encrypted, iv, algorithm, tag, key);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Decryption failed';
        const isAuthError = errorMessage.includes('authenticate') || errorMessage.includes('auth');

        request.log.error({ err }, 'Decryption failed');
        return reply.status(isAuthError ? 400 : 500).send({
          success: false,
          error: {
            code: isAuthError ? 'DECRYPTION_AUTH_ERROR' : 'DECRYPTION_ERROR',
            message: isAuthError
              ? 'Decryption failed: Invalid key, IV, or authentication tag'
              : errorMessage,
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );
};
