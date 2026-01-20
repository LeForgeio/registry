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
  
  redis: {
    host: string;
    port: number;
    password: string | undefined;
    tls: boolean;
  };
  
  cors: {
    origins: string[];
    methods: string[];
  };
  
  crypto: {
    defaultHashAlgorithm: string;
    defaultEncryptionAlgorithm: string;
    bcryptRounds: number;
    argon2MemoryCost: number;
    argon2TimeCost: number;
    argon2Parallelism: number;
  };
  
  jwt: {
    secret: string | undefined;
    defaultExpiry: string;
    defaultAlgorithm: string;
    issuer: string;
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
    port: parseInt(process.env.PORT || '3001', 10),
    host: process.env.HOST || '0.0.0.0',
    env: process.env.NODE_ENV || 'development',
  },
  logLevel: process.env.LOG_LEVEL || 'info',
  serviceName: 'crypto-service',
  serviceVersion: process.env.SERVICE_VERSION || '1.0.0',
  
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    password: process.env.REDIS_PASSWORD || undefined,
    tls: process.env.REDIS_TLS === 'true',
  },
  
  cors: {
    origins: process.env.CORS_ORIGINS?.split(',') || ['*'],
    methods: ['GET', 'POST', 'OPTIONS'],
  },
  
  crypto: {
    defaultHashAlgorithm: process.env.CRYPTO_DEFAULT_HASH || 'sha256',
    defaultEncryptionAlgorithm: process.env.CRYPTO_DEFAULT_ENCRYPTION || 'aes-256-gcm',
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '12', 10),
    argon2MemoryCost: parseInt(process.env.ARGON2_MEMORY_COST || '65536', 10),
    argon2TimeCost: parseInt(process.env.ARGON2_TIME_COST || '3', 10),
    argon2Parallelism: parseInt(process.env.ARGON2_PARALLELISM || '4', 10),
  },
  
  jwt: {
    secret: process.env.JWT_SECRET,
    defaultExpiry: process.env.JWT_DEFAULT_EXPIRY || '1h',
    defaultAlgorithm: process.env.JWT_DEFAULT_ALGORITHM || 'HS256',
    issuer: process.env.JWT_ISSUER || 'flowforge-crypto-service',
  },
  
  rateLimit: {
    max: parseInt(process.env.RATE_LIMIT_MAX || '100', 10),
    timeWindow: process.env.RATE_LIMIT_WINDOW || '1 minute',
  },
  
  metrics: {
    enabled: process.env.METRICS_ENABLED !== 'false',
    endpoint: process.env.METRICS_ENDPOINT || '/metrics',
  },
};
