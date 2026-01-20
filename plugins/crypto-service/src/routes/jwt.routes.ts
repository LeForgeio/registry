import { FastifyPluginAsync } from 'fastify';
import { jwtGenerateSchema, jwtVerifySchema, jwtDecodeSchema } from '../schemas';
import { generateJWT, verifyJWT, decodeJWT } from '../services';
import {
  JwtGenerateRequest,
  JwtVerifyRequest,
  JwtDecodeRequest,
} from '../types';

export const jwtRoutes: FastifyPluginAsync = async (fastify) => {
  // POST /api/v1/jwt/generate
  fastify.post<{ Body: JwtGenerateRequest }>(
    '/jwt/generate',
    {
      schema: {
        description: 'Generate a JSON Web Token',
        tags: ['JWT'],
        body: {
          type: 'object',
          required: ['payload'],
          properties: {
            payload: {
              type: 'object',
              additionalProperties: true,
              description: 'JWT payload (claims)',
            },
            secret: { type: 'string', description: 'Signing secret (min 8 chars)' },
            algorithm: {
              type: 'string',
              enum: ['HS256', 'HS384', 'HS512'],
              default: 'HS256',
            },
            expiresIn: {
              type: 'string',
              description: 'Expiration time (e.g., "1h", "7d", "30m")',
            },
            issuer: { type: 'string', description: 'Token issuer' },
            audience: { type: 'string', description: 'Token audience' },
            subject: { type: 'string', description: 'Token subject' },
            jwtid: { type: 'string', description: 'Unique token identifier' },
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
                  token: { type: 'string' },
                  expiresAt: { type: 'string' },
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
      const { error, value } = jwtGenerateSchema.validate(request.body, {
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
        const result = generateJWT(value);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'JWT generation failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'JWT_GENERATE_ERROR',
            message: err instanceof Error ? err.message : 'JWT generation failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );

  // POST /api/v1/jwt/verify
  fastify.post<{ Body: JwtVerifyRequest }>(
    '/jwt/verify',
    {
      schema: {
        description: 'Verify a JSON Web Token',
        tags: ['JWT'],
        body: {
          type: 'object',
          required: ['token'],
          properties: {
            token: { type: 'string', description: 'JWT token to verify' },
            secret: { type: 'string', description: 'Signing secret' },
            algorithms: {
              type: 'array',
              items: { type: 'string', enum: ['HS256', 'HS384', 'HS512'] },
              description: 'Allowed algorithms',
            },
            issuer: { type: 'string', description: 'Expected issuer' },
            audience: { type: 'string', description: 'Expected audience' },
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
                  payload: { type: 'object', additionalProperties: true },
                  expired: { type: 'boolean' },
                  expiresAt: { type: 'string' },
                  issuedAt: { type: 'string' },
                  error: { type: 'string' },
                  message: { type: 'string' },
                },
                additionalProperties: true,
              },
              requestId: { type: 'string' },
              timestamp: { type: 'string' },
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { error, value } = jwtVerifySchema.validate(request.body, {
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
        const result = verifyJWT(value);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        // Token validation failures should still return success: true with valid: false
        request.log.warn({ err }, 'JWT verification failed');
        return reply.send({
          success: true,
          data: {
            valid: false,
            error: err instanceof Error ? err.message : 'Token verification failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );

  // POST /api/v1/jwt/decode
  fastify.post<{ Body: JwtDecodeRequest }>(
    '/jwt/decode',
    {
      schema: {
        description: 'Decode a JWT without verification',
        tags: ['JWT'],
        body: {
          type: 'object',
          required: ['token'],
          properties: {
            token: { type: 'string', description: 'JWT token to decode' },
            complete: {
              type: 'boolean',
              default: false,
              description: 'Include header in response',
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
                  header: { type: 'object', additionalProperties: true },
                  payload: { type: 'object', additionalProperties: true },
                  signature: { type: 'string' },
                },
                additionalProperties: true,
              },
              requestId: { type: 'string' },
              timestamp: { type: 'string' },
            },
          },
        },
      },
    },
    async (request, reply) => {
      const { error, value } = jwtDecodeSchema.validate(request.body, {
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
        const result = decodeJWT(value.token, value.complete);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'JWT decode failed');
        return reply.status(400).send({
          success: false,
          error: {
            code: 'JWT_DECODE_ERROR',
            message: err instanceof Error ? err.message : 'Invalid JWT format',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );
};
