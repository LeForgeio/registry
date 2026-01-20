import { FastifyInstance } from 'fastify';
import * as fs from 'fs/promises';
import { config } from '../config';
import { generatorService } from '../services';
import { HealthResponseSchema } from '../schemas';

const startTime = Date.now();

export async function healthRoutes(fastify: FastifyInstance): Promise<void> {
  /**
   * Simple health check
   */
  fastify.get(
    '/health',
    {
      schema: {
        description: 'Simple health check endpoint',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              status: { type: 'string' },
              timestamp: { type: 'string' },
            },
          },
        },
      },
    },
    async () => {
      return {
        status: 'ok',
        timestamp: new Date().toISOString(),
      };
    }
  );

  /**
   * Detailed health check with component status
   */
  fastify.get(
    '/health/detailed',
    {
      schema: {
        description: 'Detailed health check with all component statuses',
        tags: ['Health'],
        response: {
          200: HealthResponseSchema,
        },
      },
    },
    async () => {
      const checks = {
        puppeteer: await checkPuppeteer(),
        tempDirectory: await checkTempDirectory(),
        memory: checkMemory(),
      };

      // Determine overall status
      const allHealthy = Object.values(checks).every(c => c.status === 'healthy');
      const anyUnhealthy = Object.values(checks).some(c => c.status === 'unhealthy');
      
      let status: 'healthy' | 'unhealthy' | 'degraded';
      if (allHealthy) {
        status = 'healthy';
      } else if (anyUnhealthy) {
        // Puppeteer being unhealthy is critical
        status = checks.puppeteer.status === 'unhealthy' ? 'unhealthy' : 'degraded';
      } else {
        status = 'degraded';
      }

      return {
        status,
        timestamp: new Date().toISOString(),
        uptime: Date.now() - startTime,
        version: config.serviceVersion,
        checks,
      };
    }
  );

  /**
   * Readiness probe (for Kubernetes)
   */
  fastify.get(
    '/ready',
    {
      schema: {
        description: 'Readiness probe for container orchestration',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              ready: { type: 'boolean' },
            },
          },
          503: {
            type: 'object',
            properties: {
              ready: { type: 'boolean' },
              reason: { type: 'string' },
            },
          },
        },
      },
    },
    async (request, reply) => {
      // Check if Puppeteer browser is ready
      const isReady = await generatorService.isReady();
      
      if (isReady) {
        return { ready: true };
      }

      return reply.status(503).send({
        ready: false,
        reason: 'Puppeteer browser not ready',
      });
    }
  );

  /**
   * Liveness probe (for Kubernetes)
   */
  fastify.get(
    '/live',
    {
      schema: {
        description: 'Liveness probe for container orchestration',
        tags: ['Health'],
        response: {
          200: {
            type: 'object',
            properties: {
              alive: { type: 'boolean' },
            },
          },
        },
      },
    },
    async () => {
      return { alive: true };
    }
  );
}

async function checkPuppeteer(): Promise<{ status: 'healthy' | 'unhealthy'; message?: string; latency?: number }> {
  const start = Date.now();
  try {
    const info = await generatorService.getHealthInfo();
    return {
      status: info.ready ? 'healthy' : 'unhealthy',
      message: info.ready ? `Browser version: ${info.version}` : 'Browser not connected',
      latency: Date.now() - start,
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      message: error instanceof Error ? error.message : 'Unknown error',
      latency: Date.now() - start,
    };
  }
}

async function checkTempDirectory(): Promise<{ status: 'healthy' | 'unhealthy'; message?: string }> {
  try {
    // Check if temp directory exists and is writable
    await fs.access(config.pdf.tempDir, fs.constants.W_OK);
    
    // Try to get directory stats
    const stats = await fs.stat(config.pdf.tempDir);
    if (!stats.isDirectory()) {
      return {
        status: 'unhealthy',
        message: 'Temp path is not a directory',
      };
    }

    return {
      status: 'healthy',
      message: `Temp directory: ${config.pdf.tempDir}`,
    };
  } catch (error) {
    // Try to create it
    try {
      await fs.mkdir(config.pdf.tempDir, { recursive: true });
      return {
        status: 'healthy',
        message: 'Temp directory created',
      };
    } catch {
      return {
        status: 'unhealthy',
        message: 'Cannot access or create temp directory',
      };
    }
  }
}

function checkMemory(): { status: 'healthy' | 'unhealthy'; message?: string } {
  const used = process.memoryUsage();
  const heapUsedMB = Math.round(used.heapUsed / 1024 / 1024);
  const heapTotalMB = Math.round(used.heapTotal / 1024 / 1024);
  const rssMB = Math.round(used.rss / 1024 / 1024);

  // Consider unhealthy if using more than 90% of heap
  const heapPercent = (used.heapUsed / used.heapTotal) * 100;
  const status = heapPercent > 90 ? 'unhealthy' : 'healthy';

  return {
    status,
    message: `Heap: ${heapUsedMB}/${heapTotalMB}MB (${heapPercent.toFixed(1)}%), RSS: ${rssMB}MB`,
  };
}
