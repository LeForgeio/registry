import { FastifyPluginAsync } from 'fastify';
import { hashSchema, hashVerifySchema } from '../schemas';
import { hash, verifyHash } from '../services';
import { HashRequest, HashVerifyRequest } from '../types';

export const hashRoutes: FastifyPluginAsync = async (fastify) => {
  // POST /api/v1/hash
  fastify.post<{ Body: HashRequest }>(
    '/hash',
    {
      schema: {
        description: 'Create a hash of the input data',
        tags: ['Hashing'],
        body: {
          type: 'object',
          required: ['data'],
          properties: {
            data: { type: 'string', description: 'Data to hash' },
            algorithm: {
              type: 'string',
              enum: ['sha256', 'sha384', 'sha512', 'bcrypt', 'argon2'],
              default: 'sha256',
              description: 'Hashing algorithm',
            },
            salt: { type: 'string', description: 'Optional salt for SHA hashes' },
            rounds: {
              type: 'integer',
              minimum: 4,
              maximum: 31,
              default: 12,
              description: 'Rounds for bcrypt (4-31)',
            },
            encoding: {
              type: 'string',
              enum: ['hex', 'base64'],
              default: 'hex',
              description: 'Output encoding for SHA hashes',
            },
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
                  hash: { type: 'string' },
                  algorithm: { type: 'string' },
                  salt: { type: 'string' },
                  encoding: { type: 'string' },
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
      const { error, value } = hashSchema.validate(request.body, {
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
        const { data, algorithm, encoding, options } = value;
        const result = await hash(data, algorithm, encoding, options);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'Hashing failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'HASH_ERROR',
            message: err instanceof Error ? err.message : 'Hashing failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );

  // POST /api/v1/hash/verify
  fastify.post<{ Body: HashVerifyRequest }>(
    '/hash/verify',
    {
      schema: {
        description: 'Verify data against a hash',
        tags: ['Hashing'],
        body: {
          type: 'object',
          required: ['data', 'hash'],
          properties: {
            data: { type: 'string', description: 'Original data to verify' },
            hash: { type: 'string', description: 'Hash to verify against' },
            algorithm: {
              type: 'string',
              enum: ['bcrypt', 'argon2'],
            },
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
                  valid: { type: 'boolean' },
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
      const { error, value } = hashVerifySchema.validate(request.body, {
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
        const { data, hash: hashValue, algorithm } = value;
        const valid = await verifyHash(data, hashValue, algorithm);

        return reply.send({
          success: true,
          data: { valid, algorithm: algorithm || 'auto-detected' },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'Hash verification failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'HASH_VERIFY_ERROR',
            message: err instanceof Error ? err.message : 'Hash verification failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );
};
