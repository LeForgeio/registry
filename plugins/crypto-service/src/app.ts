import Fastify, { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import cors from '@fastify/cors';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import { randomUUID } from 'crypto';
import { config } from './config';
import {
  encryptionRoutes,
  hashRoutes,
  jwtRoutes,
  hmacRoutes,
  keyRoutes,
  healthRoutes,
} from './routes';

export async function buildApp(): Promise<FastifyInstance> {
  const app = Fastify({
    logger: config.server.env === 'test' 
      ? false 
      : {
          level: config.logLevel,
          transport: config.server.env === 'development'
            ? {
                target: 'pino-pretty',
                options: {
                  colorize: true,
                  translateTime: 'SYS:standard',
                  ignore: 'pid,hostname',
                },
              }
            : undefined,
        },
    genReqId: () => randomUUID(),
    trustProxy: true,
    bodyLimit: 10 * 1024 * 1024, // 10MB
    requestTimeout: 30000,
    keepAliveTimeout: 5000,
  });

  // Register CORS
  await app.register(cors, {
    origin: config.cors.origins,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID', 'X-API-Key'],
    exposedHeaders: ['X-Request-ID'],
    credentials: true,
    maxAge: 86400,
  });

  // Register Swagger documentation
  await app.register(swagger, {
    openapi: {
      openapi: '3.0.3',
      info: {
        title: 'FlowForge Crypto Service API',
        description: `
Production-ready cryptographic operations service providing:
- **Encryption/Decryption**: AES-256-GCM, AES-256-CBC, AES-128-GCM, AES-128-CBC
- **Hashing**: SHA-256/384/512, bcrypt, Argon2
- **JWT**: Generate, verify, and decode JSON Web Tokens
- **HMAC**: Sign and verify message authentication codes
- **Key Generation**: Cryptographically secure random keys

All endpoints return consistent JSON responses with request tracking.
        `.trim(),
        version: '1.0.0',
        contact: {
          name: 'FlowForge Team',
          email: 'support@flowforge.io',
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
        {
          url: 'https://api.flowforge.io/crypto',
          description: 'Production server',
        },
      ],
      tags: [
        { name: 'Health', description: 'Service health and metrics endpoints' },
        { name: 'Encryption', description: 'Symmetric encryption operations' },
        { name: 'Hashing', description: 'Cryptographic hash functions' },
        { name: 'JWT', description: 'JSON Web Token operations' },
        { name: 'HMAC', description: 'Hash-based message authentication' },
        { name: 'Keys', description: 'Key generation utilities' },
      ],
      components: {
        securitySchemes: {
          ApiKeyAuth: {
            type: 'apiKey',
            in: 'header',
            name: 'X-API-Key',
          },
        },
      },
    },
  });

  // Register Swagger UI
  await app.register(swaggerUi, {
    routePrefix: '/docs',
    uiConfig: {
      docExpansion: 'list',
      deepLinking: true,
      displayRequestDuration: true,
      filter: true,
      showExtensions: true,
      tryItOutEnabled: true,
    },
    staticCSP: true,
    transformStaticCSP: (header) => header,
  });

  // Add request ID header to responses
  app.addHook('onRequest', async (request: FastifyRequest, reply: FastifyReply) => {
    reply.header('X-Request-ID', request.id);
  });

  // Log request completion
  app.addHook('onResponse', async (request: FastifyRequest, reply: FastifyReply) => {
    request.log.info(
      {
        method: request.method,
        url: request.url,
        statusCode: reply.statusCode,
        responseTime: reply.elapsedTime,
      },
      'Request completed'
    );
  });

  // Global error handler
  app.setErrorHandler(async (error, request, reply) => {
    request.log.error(
      {
        err: error,
        method: request.method,
        url: request.url,
      },
      'Request error'
    );

    // Handle validation errors
    if (error.validation) {
      return reply.status(400).send({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: error.validation.map((v) => ({
            field: v.instancePath || 'body',
            message: v.message,
          })),
        },
        requestId: request.id,
        timestamp: new Date().toISOString(),
      });
    }

    // Handle 404 errors
    if (error.statusCode === 404) {
      return reply.status(404).send({
        success: false,
        error: {
          code: 'NOT_FOUND',
          message: `Route ${request.method} ${request.url} not found`,
        },
        requestId: request.id,
        timestamp: new Date().toISOString(),
      });
    }

    // Handle rate limiting
    if (error.statusCode === 429) {
      return reply.status(429).send({
        success: false,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests, please try again later',
        },
        requestId: request.id,
        timestamp: new Date().toISOString(),
      });
    }

    // Default error response
    const statusCode = error.statusCode || 500;
    return reply.status(statusCode).send({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message:
          config.server.env === 'production'
            ? 'An internal error occurred'
            : error.message,
      },
      requestId: request.id,
      timestamp: new Date().toISOString(),
    });
  });

  // Handle 404 for undefined routes
  app.setNotFoundHandler(async (request, reply) => {
    return reply.status(404).send({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: `Route ${request.method} ${request.url} not found`,
      },
      requestId: request.id,
      timestamp: new Date().toISOString(),
    });
  });

  // Register health routes at root level
  await app.register(healthRoutes);

  // Register API routes under /api/v1 prefix
  await app.register(
    async (api) => {
      await api.register(encryptionRoutes);
      await api.register(hashRoutes);
      await api.register(jwtRoutes);
      await api.register(hmacRoutes);
      await api.register(keyRoutes);
    },
    { prefix: '/api/v1' }
  );

  // Root endpoint
  app.get('/', async (_request, reply) => {
    return reply.send({
      service: 'crypto-service',
      version: '1.0.0',
      documentation: '/docs',
      health: '/health',
      api: '/api/v1',
      endpoints: {
        encrypt: 'POST /api/v1/encrypt',
        decrypt: 'POST /api/v1/decrypt',
        hash: 'POST /api/v1/hash',
        hashVerify: 'POST /api/v1/hash/verify',
        jwtGenerate: 'POST /api/v1/jwt/generate',
        jwtVerify: 'POST /api/v1/jwt/verify',
        jwtDecode: 'POST /api/v1/jwt/decode',
        hmacSign: 'POST /api/v1/hmac/sign',
        hmacVerify: 'POST /api/v1/hmac/verify',
        keysGenerate: 'POST /api/v1/keys/generate',
      },
    });
  });

  return app;
}
