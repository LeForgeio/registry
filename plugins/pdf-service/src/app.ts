import Fastify, { FastifyInstance } from 'fastify';
import cors from '@fastify/cors';
import multipart from '@fastify/multipart';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import { config } from './config';
import {
  generateRoutes,
  mergeRoutes,
  extractRoutes,
  formRoutes,
  healthRoutes,
} from './routes';

export async function buildApp(): Promise<FastifyInstance> {
  const app = Fastify({
    logger: {
      level: config.logLevel,
      transport:
        config.server.env === 'development'
          ? {
              target: 'pino-pretty',
              options: {
                translateTime: 'HH:MM:ss Z',
                ignore: 'pid,hostname',
              },
            }
          : undefined,
    },
    bodyLimit: config.pdf.maxFileSize * 2, // Allow for base64 overhead
    trustProxy: true,
  });

  // Register CORS
  await app.register(cors, {
    origin: config.cors.origins,
    methods: config.cors.methods,
    credentials: true,
  });

  // Register multipart for file uploads
  await app.register(multipart, {
    limits: {
      fileSize: config.pdf.maxFileSize,
      files: config.pdf.maxMergeFiles,
    },
  });

  // Register Swagger documentation
  await app.register(swagger, {
    openapi: {
      info: {
        title: 'PDF Service API',
        description: 'API for PDF generation, manipulation, and text extraction',
        version: config.serviceVersion,
        contact: {
          name: 'FlowForge',
          url: 'https://flowforge.dev',
        },
        license: {
          name: 'MIT',
          url: 'https://opensource.org/licenses/MIT',
        },
      },
      servers: [
        {
          url: `http://localhost:${config.server.port}`,
          description: 'Development server',
        },
      ],
      tags: [
        { name: 'Generate', description: 'PDF generation from HTML and templates' },
        { name: 'Merge', description: 'PDF merging operations' },
        { name: 'Extract', description: 'Text extraction from PDFs' },
        { name: 'Form', description: 'PDF form operations' },
        { name: 'Health', description: 'Health check endpoints' },
      ],
      components: {
        securitySchemes: {
          apiKey: {
            type: 'apiKey',
            name: 'X-API-Key',
            in: 'header',
          },
        },
      },
    },
  });

  await app.register(swaggerUi, {
    routePrefix: '/docs',
    uiConfig: {
      docExpansion: 'list',
      deepLinking: true,
    },
    staticCSP: true,
  });

  // Request ID middleware
  app.addHook('onRequest', async (request) => {
    request.id = request.headers['x-request-id'] as string || request.id;
  });

  // Error handler
  app.setErrorHandler(async (error, request, reply) => {
    request.log.error({ error }, 'Request error');

    // Handle validation errors
    if (error.validation) {
      return reply.status(400).send({
        success: false,
        error: 'Validation error',
        code: 'VALIDATION_ERROR',
        details: error.validation,
      });
    }

    // Handle file size errors
    if (error.code === 'FST_REQ_FILE_TOO_LARGE') {
      return reply.status(413).send({
        success: false,
        error: 'File too large',
        code: 'FILE_TOO_LARGE',
      });
    }

    // Generic error response
    const statusCode = error.statusCode || 500;
    return reply.status(statusCode).send({
      success: false,
      error: statusCode >= 500 ? 'Internal server error' : error.message,
      code: error.code || 'INTERNAL_ERROR',
    });
  });

  // Register routes
  await app.register(healthRoutes, { prefix: '/api/v1' });
  await app.register(generateRoutes, { prefix: '/api/v1/generate' });
  await app.register(mergeRoutes, { prefix: '/api/v1/merge' });
  await app.register(extractRoutes, { prefix: '/api/v1/extract' });
  await app.register(formRoutes, { prefix: '/api/v1/form' });

  // Root endpoint
  app.get('/', async () => {
    return {
      service: config.serviceName,
      version: config.serviceVersion,
      documentation: '/docs',
      health: '/api/v1/health',
    };
  });

  return app;
}
