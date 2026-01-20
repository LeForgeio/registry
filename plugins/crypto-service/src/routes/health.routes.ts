import { FastifyPluginAsync } from 'fastify';
import os from 'os';
import { config } from '../config';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime: number;
  checks: {
    name: string;
    status: 'pass' | 'fail';
    duration?: number;
    message?: string;
  }[];
}

interface ReadinessStatus {
  ready: boolean;
  timestamp: string;
  checks: {
    name: string;
    ready: boolean;
    message?: string;
  }[];
}

interface MetricsResponse {
  timestamp: string;
  service: string;
  version: string;
  uptime: number;
  memory: {
    heapUsed: number;
    heapTotal: number;
    rss: number;
    external: number;
    arrayBuffers: number;
  };
  cpu: {
    user: number;
    system: number;
  };
  system: {
    loadAvg: number[];
    totalMemory: number;
    freeMemory: number;
    cpus: number;
    platform: string;
    arch: string;
  };
}

const startTime = Date.now();
const serviceVersion = process.env.npm_package_version || '1.0.0';

export const healthRoutes: FastifyPluginAsync = async (fastify) => {
  // GET /health - Liveness probe
  fastify.get<{ Reply: HealthStatus }>(
    '/health',
    {
      schema: {
        description: 'Health check endpoint (liveness probe)',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              status: { type: 'string', enum: ['healthy', 'degraded', 'unhealthy'] },
              timestamp: { type: 'string' },
              version: { type: 'string' },
              uptime: { type: 'number' },
              checks: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    status: { type: 'string', enum: ['pass', 'fail'] },
                    duration: { type: 'number' },
                    message: { type: 'string' },
                  },
                },
              },
            },
          },
        },
      },
    },
    async (_request, reply) => {
      const checks: HealthStatus['checks'] = [];
      let overallStatus: HealthStatus['status'] = 'healthy';

      // Memory check
      const memUsage = process.memoryUsage();
      const heapUsedPercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
      const memoryCheck = {
        name: 'memory',
        status: heapUsedPercent < 90 ? ('pass' as const) : ('fail' as const),
        message: `Heap usage: ${heapUsedPercent.toFixed(1)}%`,
      };
      checks.push(memoryCheck);

      if (memoryCheck.status === 'fail') {
        overallStatus = 'degraded';
      }

      // Event loop check (simple)
      const eventLoopStart = Date.now();
      await new Promise((resolve) => setImmediate(resolve));
      const eventLoopLag = Date.now() - eventLoopStart;
      const eventLoopCheck = {
        name: 'event_loop',
        status: eventLoopLag < 100 ? ('pass' as const) : ('fail' as const),
        duration: eventLoopLag,
        message: `Event loop lag: ${eventLoopLag}ms`,
      };
      checks.push(eventLoopCheck);

      if (eventLoopCheck.status === 'fail') {
        overallStatus = 'degraded';
      }

      // Crypto module check
      try {
        const crypto = await import('crypto');
        crypto.randomBytes(16);
        checks.push({
          name: 'crypto_module',
          status: 'pass',
          message: 'Crypto module operational',
        });
      } catch (err) {
        checks.push({
          name: 'crypto_module',
          status: 'fail',
          message: err instanceof Error ? err.message : 'Crypto module failed',
        });
        overallStatus = 'unhealthy';
      }

      const response: HealthStatus = {
        status: overallStatus,
        timestamp: new Date().toISOString(),
        version: serviceVersion,
        uptime: Math.floor((Date.now() - startTime) / 1000),
        checks,
      };

      const statusCode = overallStatus === 'unhealthy' ? 503 : 200;
      return reply.status(statusCode).send(response);
    }
  );

  // GET /health/ready - Readiness probe
  fastify.get<{ Reply: ReadinessStatus }>(
    '/health/ready',
    {
      schema: {
        description: 'Readiness check endpoint',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              ready: { type: 'boolean' },
              timestamp: { type: 'string' },
              checks: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    ready: { type: 'boolean' },
                    message: { type: 'string' },
                  },
                },
              },
            },
          },
        },
      },
    },
    async (_request, reply) => {
      const checks: ReadinessStatus['checks'] = [];
      let ready = true;

      // Check if crypto operations work
      try {
        const crypto = await import('crypto');
        const testKey = crypto.randomBytes(32);
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-cbc', testKey, iv);
        cipher.update('test', 'utf8', 'base64');
        cipher.final('base64');
        checks.push({ name: 'crypto_operations', ready: true });
      } catch (err) {
        checks.push({
          name: 'crypto_operations',
          ready: false,
          message: err instanceof Error ? err.message : 'Crypto test failed',
        });
        ready = false;
      }

      // Check environment config
      const configCheck = {
        name: 'configuration',
        ready: !!config.server.port,
        message: config.server.port ? undefined : 'Missing required configuration',
      };
      checks.push(configCheck);
      if (!configCheck.ready) ready = false;

      const response: ReadinessStatus = {
        ready,
        timestamp: new Date().toISOString(),
        checks,
      };

      return reply.status(ready ? 200 : 503).send(response);
    }
  );

  // GET /health/live - Simple liveness probe for K8s
  fastify.get(
    '/health/live',
    {
      schema: {
        description: 'Simple liveness check',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              alive: { type: 'boolean' },
              timestamp: { type: 'string' },
            },
          },
        },
      },
    },
    async (_request, reply) => {
      return reply.send({
        alive: true,
        timestamp: new Date().toISOString(),
      });
    }
  );

  // GET /metrics - Prometheus-style metrics
  fastify.get<{ Reply: MetricsResponse }>(
    '/metrics',
    {
      schema: {
        description: 'Service metrics endpoint',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              timestamp: { type: 'string' },
              service: { type: 'string' },
              version: { type: 'string' },
              uptime: { type: 'number' },
              memory: { type: 'object' },
              cpu: { type: 'object' },
              system: { type: 'object' },
            },
          },
        },
      },
    },
    async (_request, reply) => {
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();

      const response: MetricsResponse = {
        timestamp: new Date().toISOString(),
        service: 'crypto-service',
        version: serviceVersion,
        uptime: Math.floor((Date.now() - startTime) / 1000),
        memory: {
          heapUsed: memUsage.heapUsed,
          heapTotal: memUsage.heapTotal,
          rss: memUsage.rss,
          external: memUsage.external,
          arrayBuffers: memUsage.arrayBuffers,
        },
        cpu: {
          user: cpuUsage.user,
          system: cpuUsage.system,
        },
        system: {
          loadAvg: os.loadavg(),
          totalMemory: os.totalmem(),
          freeMemory: os.freemem(),
          cpus: os.cpus().length,
          platform: os.platform(),
          arch: os.arch(),
        },
      };

      return reply.send(response);
    }
  );
};
