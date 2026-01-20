import dotenv from 'dotenv';

dotenv.config();

export interface Config {
  server: {
    port: number;
    host: string;
    env: string;
  };
  logLevel: string;
  serviceName: string;
  serviceVersion: string;

  cors: {
    origins: string[];
    methods: string[];
  };

  pdf: {
    maxFileSize: number; // bytes
    maxMergeFiles: number;
    tempDir: string;
    defaultFormat: 'A4' | 'Letter' | 'Legal';
    defaultMargin: {
      top: string;
      right: string;
      bottom: string;
      left: string;
    };
    puppeteerTimeout: number;
  };

  rateLimit: {
    max: number;
    timeWindow: string;
  };

  metrics: {
    enabled: boolean;
    endpoint: string;
  };
}

export const config: Config = {
  server: {
    port: parseInt(process.env.PORT || '3003', 10),
    host: process.env.HOST || '0.0.0.0',
    env: process.env.NODE_ENV || 'development',
  },
  logLevel: process.env.LOG_LEVEL || 'info',
  serviceName: 'pdf-service',
  serviceVersion: process.env.SERVICE_VERSION || '1.0.0',

  cors: {
    origins: process.env.CORS_ORIGINS?.split(',') || ['*'],
    methods: ['GET', 'POST', 'OPTIONS'],
  },

  pdf: {
    maxFileSize: parseInt(process.env.PDF_MAX_FILE_SIZE || String(50 * 1024 * 1024), 10), // 50MB default
    maxMergeFiles: parseInt(process.env.PDF_MAX_MERGE_FILES || '20', 10),
    tempDir: process.env.PDF_TEMP_DIR || '/tmp/pdf-service',
    defaultFormat: (process.env.PDF_DEFAULT_FORMAT as 'A4' | 'Letter' | 'Legal') || 'A4',
    defaultMargin: {
      top: process.env.PDF_MARGIN_TOP || '20mm',
      right: process.env.PDF_MARGIN_RIGHT || '20mm',
      bottom: process.env.PDF_MARGIN_BOTTOM || '20mm',
      left: process.env.PDF_MARGIN_LEFT || '20mm',
    },
    puppeteerTimeout: parseInt(process.env.PDF_PUPPETEER_TIMEOUT || '30000', 10),
  },

  rateLimit: {
    max: parseInt(process.env.RATE_LIMIT_MAX || '50', 10),
    timeWindow: process.env.RATE_LIMIT_WINDOW || '1 minute',
  },

  metrics: {
    enabled: process.env.METRICS_ENABLED !== 'false',
    endpoint: process.env.METRICS_ENDPOINT || '/metrics',
  },
};
