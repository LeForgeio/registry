import { FastifyPluginAsync } from 'fastify';
import { generateKeySchema } from '../schemas';
import { generateKey } from '../services';

export const keyRoutes: FastifyPluginAsync = async (fastify) => {
  // POST /api/v1/keys/generate
  fastify.post<{
    Body: { length?: number; encoding?: 'hex' | 'base64' | 'utf8' };
  }>(
    '/keys/generate',
    {
      schema: {
        description: 'Generate a cryptographically secure random key',
        tags: ['Keys'],
        body: {
          type: 'object',
          properties: {
            length: {
              type: 'integer',
              minimum: 8,
              maximum: 256,
              default: 32,
              description: 'Key length in bytes',
            },
            encoding: {
              type: 'string',
              enum: ['hex', 'base64', 'utf8'],
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
                  key: { type: 'string' },
                  length: { type: 'integer' },
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
      const { error, value } = generateKeySchema.validate(request.body, {
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
        const { length, encoding } = value;
        const result = generateKey(length, encoding);

        return reply.send({
          success: true,
          data: result,
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      } catch (err) {
        request.log.error({ err }, 'Key generation failed');
        return reply.status(500).send({
          success: false,
          error: {
            code: 'KEY_GENERATE_ERROR',
            message: err instanceof Error ? err.message : 'Key generation failed',
          },
          requestId: request.id,
          timestamp: new Date().toISOString(),
        });
      }
    }
  );
};
