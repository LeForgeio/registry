import { FastifyPluginAsync } from 'fastify';
import { hmacSignSchema, hmacVerifySchema } from '../schemas';
import { hmacSign, hmacVerify } from '../services';
import { HmacSignRequest, HmacVerifyRequest } from '../types';

export const hmacRoutes: FastifyPluginAsync = async (fastify) => {
  // POST /api/v1/hmac/sign
  fastify.post<{ Body: HmacSignRequest }>(
    '/hmac/sign',
    {
      schema: {
        description: 'Create an HMAC signature for data',
        tags: ['HMAC'],
        body: {
          type: 'object',
          required: ['data', 'key'],
          properties: {
            data: { type: 'string', description: 'Data to sign' },
            key: { type: 'string', description: 'HMAC secret key' },
            algorithm: {
              type: 'string',
              enum: ['sha256', 'sha384', 'sha512'],
              default: 'sha256',
              description: 'HMAC algorithm',
            },
            encoding: {
              type: 'string',
              enum: ['hex', 'base64'],
              default: 'hex',
              description: 'Output encoding',
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
                  signature: { type: 'string' },
                  algorithm: { type: 'string' },
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
      const { error, value } = hmacSignSchema.validate(request.body, {
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
        const { data, key, algorithm, encoding } = value;
        const result = hmacSign(data, key, algorithm, encoding);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'HMAC signing failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'HMAC_SIGN_ERROR',
            message: err instanceof Error ? err.message : 'HMAC signing failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );

  // POST /api/v1/hmac/verify
  fastify.post<{ Body: HmacVerifyRequest }>(
    '/hmac/verify',
    {
      schema: {
        description: 'Verify an HMAC signature',
        tags: ['HMAC'],
        body: {
          type: 'object',
          required: ['data', 'signature', 'key'],
          properties: {
            data: { type: 'string', description: 'Original data' },
            signature: { type: 'string', description: 'HMAC signature to verify' },
            key: { type: 'string', description: 'HMAC secret key' },
            algorithm: {
              type: 'string',
              enum: ['sha256', 'sha384', 'sha512'],
              default: 'sha256',
            },
            encoding: {
              type: 'string',
              enum: ['hex', 'base64'],
              default: 'hex',
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
      const { error, value } = hmacVerifySchema.validate(request.body, {
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
        const { data, signature, key, algorithm, encoding } = value;
        const valid = hmacVerify(data, key, signature, algorithm, encoding);

        return reply.send({
          success: true,
          data: { valid, algorithm },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'HMAC verification failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'HMAC_VERIFY_ERROR',
            message: err instanceof Error ? err.message : 'HMAC verification failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );
};
