import { buildApp } from './app';
import { config } from './config';
import { generatorService, pdfService } from './services';

async function main(): Promise<void> {
  const app = await buildApp();

  // Graceful shutdown handling
  const shutdown = async (signal: string) => {
    app.log.info(`Received ${signal}, shutting down gracefully...`);
    
    try {
      // Close Puppeteer browser
      await generatorService.close();
      
      // Close Fastify server
      await app.close();
      
      // Cleanup temp files
      const cleaned = await pdfService.cleanupOldTempFiles(0); // Clean all
      app.log.info(`Cleaned up ${cleaned} temporary files`);
      
      process.exit(0);
    } catch (error) {
      app.log.error({ error }, 'Error during shutdown');
      process.exit(1);
    }
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  // Handle uncaught exceptions
  process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    shutdown('uncaughtException');
  });

  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  });

  try {
    // Start the server
    await app.listen({
      port: config.server.port,
      host: config.server.host,
    });

    app.log.info(
      `${config.serviceName} v${config.serviceVersion} started on port ${config.server.port}`
    );
    app.log.info(`Documentation available at http://localhost:${config.server.port}/docs`);

    // Start periodic temp file cleanup (every hour)
    setInterval(async () => {
      try {
        const cleaned = await pdfService.cleanupOldTempFiles();
        if (cleaned > 0) {
          app.log.info(`Cleaned up ${cleaned} old temporary files`);
        }
      } catch (error) {
        app.log.warn({ error }, 'Failed to cleanup temp files');
      }
    }, 3600000); // 1 hour

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

main();

