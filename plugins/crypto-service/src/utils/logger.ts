import pino, { Logger } from 'pino';
import { config } from '../config';

const transport = config.server.env === 'development' 
  ? {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'SYS:standard',
        ignore: 'pid,hostname',
      },
    }
  : undefined;

export const logger: Logger = pino({
  level: config.logLevel,
  transport,
  base: {
    service: config.serviceName,
    version: config.serviceVersion,
    env: config.server.env,
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  formatters: {
    level: (label) => ({ level: label }),
  },
  serializers: {
    err: pino.stdSerializers.err,
    req: (req) => ({
      method: req.method,
      url: req.url,
      headers: {
        'user-agent': req.headers['user-agent'],
        'content-type': req.headers['content-type'],
        'x-request-id': req.headers['x-request-id'],
      },
    }),
    res: (res) => ({
      statusCode: res.statusCode,
    }),
  },
});

export const createChildLogger = (bindings: Record<string, unknown>): Logger => {
  return logger.child(bindings);
};
