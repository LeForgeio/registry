/**
 * On-Premises Connector - Full Implementation
 * 
 * Container-based ForgeHook plugin for secure access to on-premises resources.
 * Runs as a Docker container with native database drivers.
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');

// Database drivers
const mssql = require('mssql');
const { Pool: PgPool } = require('pg');
const mysql = require('mysql2/promise');
const oracledb = require('oracledb');

// LDAP
const ldap = require('ldapjs');

// Initialize Express
const app = express();
app.use(cors());
app.use(helmet());
app.use(express.json({ limit: '50mb' }));

// Connection store (in production, use encrypted storage)
const connectionStore = new Map();

// Encryption key for credentials (should come from env)
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || crypto.randomBytes(32).toString('hex');

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function encrypt(text) {
  const iv = crypto.randomBytes(16);
  const key = Buffer.from(ENCRYPTION_KEY.slice(0, 32).padEnd(32, '0'));
  const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return iv.toString('hex') + ':' + encrypted;
}

function decrypt(text) {
  const parts = text.split(':');
  const iv = Buffer.from(parts[0], 'hex');
  const key = Buffer.from(ENCRYPTION_KEY.slice(0, 32).padEnd(32, '0'));
  const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
  let decrypted = decipher.update(parts[1], 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

function sanitizeSqlIdentifier(identifier) {
  // Only allow alphanumeric, underscore, and dot (for schema.table)
  return identifier.replace(/[^a-zA-Z0-9_.]/g, '');
}

// Standard response format
function successResponse(data, meta = {}) {
  return {
    success: true,
    data,
    ...meta,
    timestamp: new Date().toISOString()
  };
}

function errorResponse(message, code = 'ERROR', details = null) {
  return {
    success: false,
    error: {
      code,
      message,
      details
    },
    timestamp: new Date().toISOString()
  };
}

// ============================================================================
// CONNECTION MANAGEMENT
// ============================================================================

/**
 * Store a connection configuration
 */
app.post('/connections', async (req, res) => {
  try {
    const { id, name, type, config, credentials } = req.body;
    
    if (!id || !type || !config) {
      return res.status(400).json(errorResponse('Missing required fields: id, type, config', 'VALIDATION_ERROR'));
    }
    
    // Encrypt sensitive credentials
    const encryptedCredentials = credentials ? {
      ...credentials,
      password: credentials.password ? encrypt(credentials.password) : undefined,
      secret: credentials.secret ? encrypt(credentials.secret) : undefined
    } : null;
    
    const connection = {
      id,
      name: name || id,
      type,
      config,
      credentials: encryptedCredentials,
      createdAt: new Date().toISOString(),
      lastTested: null,
      status: 'untested'
    };
    
    connectionStore.set(id, connection);
    
    // Persist to disk
    await saveConnections();
    
    res.json(successResponse({ id, name: connection.name, type }, { message: 'Connection saved' }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'INTERNAL_ERROR'));
  }
});

/**
 * List all connections
 */
app.get('/connections', async (req, res) => {
  try {
    const connections = Array.from(connectionStore.values()).map(c => ({
      id: c.id,
      name: c.name,
      type: c.type,
      status: c.status,
      lastTested: c.lastTested,
      createdAt: c.createdAt
    }));
    
    res.json(successResponse(connections));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'INTERNAL_ERROR'));
  }
});

/**
 * Delete a connection
 */
app.delete('/connections/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    if (!connectionStore.has(id)) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    connectionStore.delete(id);
    await saveConnections();
    
    res.json(successResponse({ id }, { message: 'Connection deleted' }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'INTERNAL_ERROR'));
  }
});

/**
 * Test a connection
 */
app.post('/connections/:id/test', async (req, res) => {
  try {
    const { id } = req.params;
    const connection = connectionStore.get(id);
    
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    const startTime = Date.now();
    let testResult;
    
    switch (connection.type) {
      case 'mssql':
      case 'postgresql':
      case 'mysql':
      case 'oracle':
        testResult = await testDatabaseConnection(connection);
        break;
      case 'api':
        testResult = await testApiConnection(connection);
        break;
      case 'fileshare':
        testResult = await testFileShareConnection(connection);
        break;
      case 'ldap':
        testResult = await testLdapConnection(connection);
        break;
      default:
        return res.status(400).json(errorResponse(`Unknown connection type: ${connection.type}`, 'VALIDATION_ERROR'));
    }
    
    const latency = Date.now() - startTime;
    
    // Update connection status
    connection.lastTested = new Date().toISOString();
    connection.status = testResult.success ? 'connected' : 'failed';
    connectionStore.set(id, connection);
    await saveConnections();
    
    res.json(successResponse({
      success: testResult.success,
      message: testResult.message,
      latency
    }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'INTERNAL_ERROR'));
  }
});

// ============================================================================
// DATABASE OPERATIONS
// ============================================================================

/**
 * Execute SQL query
 */
app.post('/queryDatabase', async (req, res) => {
  try {
    const { connectionId, query, parameters = [], timeout = 30000, maxRows = 1000 } = req.body;
    
    if (!connectionId) {
      return res.status(400).json(errorResponse('connectionId is required', 'VALIDATION_ERROR'));
    }
    if (!query) {
      return res.status(400).json(errorResponse('query is required', 'VALIDATION_ERROR'));
    }
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    const startTime = Date.now();
    let result;
    
    switch (connection.type) {
      case 'mssql':
        result = await executeMsSql(connection, query, parameters, { timeout, maxRows });
        break;
      case 'postgresql':
        result = await executePostgres(connection, query, parameters, { timeout, maxRows });
        break;
      case 'mysql':
        result = await executeMySql(connection, query, parameters, { timeout, maxRows });
        break;
      case 'oracle':
        result = await executeOracle(connection, query, parameters, { timeout, maxRows });
        break;
      default:
        return res.status(400).json(errorResponse(`Not a database connection: ${connection.type}`, 'VALIDATION_ERROR'));
    }
    
    res.json(successResponse({
      rows: result.rows,
      rowCount: result.rows.length,
      columns: result.columns,
      executionTime: Date.now() - startTime
    }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'DATABASE_ERROR'));
  }
});

/**
 * Execute stored procedure
 */
app.post('/executeStoredProcedure', async (req, res) => {
  try {
    const { connectionId, procedureName, parameters = {}, timeout = 60000 } = req.body;
    
    if (!connectionId) {
      return res.status(400).json(errorResponse('connectionId is required', 'VALIDATION_ERROR'));
    }
    if (!procedureName) {
      return res.status(400).json(errorResponse('procedureName is required', 'VALIDATION_ERROR'));
    }
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    const startTime = Date.now();
    const safeProcName = sanitizeSqlIdentifier(procedureName);
    let result;
    
    switch (connection.type) {
      case 'mssql':
        result = await executeMsSqlProc(connection, safeProcName, parameters, timeout);
        break;
      case 'postgresql':
        result = await executePostgresFunc(connection, safeProcName, parameters, timeout);
        break;
      default:
        return res.status(400).json(errorResponse(`Stored procedures not supported for: ${connection.type}`, 'VALIDATION_ERROR'));
    }
    
    res.json(successResponse({
      result: result.output,
      returnValue: result.returnValue,
      executionTime: Date.now() - startTime
    }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'DATABASE_ERROR'));
  }
});

// ============================================================================
// SQL SERVER IMPLEMENTATION
// ============================================================================

async function executeMsSql(connection, query, parameters, options) {
  const config = {
    server: connection.config.host,
    port: connection.config.port || 1433,
    database: connection.config.database,
    user: connection.credentials?.username,
    password: connection.credentials?.password ? decrypt(connection.credentials.password) : undefined,
    options: {
      encrypt: connection.config.encrypt !== false,
      trustServerCertificate: connection.config.trustServerCertificate || false,
      connectTimeout: options.timeout,
      requestTimeout: options.timeout
    }
  };
  
  const pool = await mssql.connect(config);
  
  try {
    const request = pool.request();
    
    // Add parameters
    parameters.forEach((param, index) => {
      if (typeof param === 'object' && param.name) {
        request.input(param.name, param.value);
      } else {
        request.input(`p${index}`, param);
      }
    });
    
    const result = await request.query(query);
    
    return {
      rows: result.recordset?.slice(0, options.maxRows) || [],
      columns: result.recordset?.columns ? Object.keys(result.recordset.columns) : []
    };
  } finally {
    await pool.close();
  }
}

async function executeMsSqlProc(connection, procedureName, parameters, timeout) {
  const config = {
    server: connection.config.host,
    port: connection.config.port || 1433,
    database: connection.config.database,
    user: connection.credentials?.username,
    password: connection.credentials?.password ? decrypt(connection.credentials.password) : undefined,
    options: {
      encrypt: connection.config.encrypt !== false,
      trustServerCertificate: connection.config.trustServerCertificate || false,
      connectTimeout: timeout,
      requestTimeout: timeout
    }
  };
  
  const pool = await mssql.connect(config);
  
  try {
    const request = pool.request();
    
    // Add parameters
    Object.entries(parameters).forEach(([name, value]) => {
      request.input(name, value);
    });
    
    const result = await request.execute(procedureName);
    
    return {
      output: result.recordset || result.recordsets,
      returnValue: result.returnValue
    };
  } finally {
    await pool.close();
  }
}

// ============================================================================
// POSTGRESQL IMPLEMENTATION
// ============================================================================

async function executePostgres(connection, query, parameters, options) {
  const pool = new PgPool({
    host: connection.config.host,
    port: connection.config.port || 5432,
    database: connection.config.database,
    user: connection.credentials?.username,
    password: connection.credentials?.password ? decrypt(connection.credentials.password) : undefined,
    ssl: connection.config.ssl ? { rejectUnauthorized: false } : false,
    connectionTimeoutMillis: options.timeout,
    query_timeout: options.timeout
  });
  
  try {
    // Convert named parameters to positional
    let processedQuery = query;
    const values = [];
    
    if (Array.isArray(parameters)) {
      parameters.forEach((param, index) => {
        if (typeof param === 'object' && param.name) {
          const regex = new RegExp(`@${param.name}\\b`, 'g');
          processedQuery = processedQuery.replace(regex, `$${values.length + 1}`);
          values.push(param.value);
        } else {
          values.push(param);
        }
      });
    }
    
    // Replace remaining @param with $n
    processedQuery = processedQuery.replace(/@(\w+)/g, (match, name) => {
      const param = parameters.find(p => p.name === name);
      if (param) {
        values.push(param.value);
        return `$${values.length}`;
      }
      return match;
    });
    
    const result = await pool.query(processedQuery, values);
    
    return {
      rows: result.rows.slice(0, options.maxRows),
      columns: result.fields?.map(f => f.name) || []
    };
  } finally {
    await pool.end();
  }
}

async function executePostgresFunc(connection, functionName, parameters, timeout) {
  const pool = new PgPool({
    host: connection.config.host,
    port: connection.config.port || 5432,
    database: connection.config.database,
    user: connection.credentials?.username,
    password: connection.credentials?.password ? decrypt(connection.credentials.password) : undefined,
    ssl: connection.config.ssl ? { rejectUnauthorized: false } : false,
    connectionTimeoutMillis: timeout,
    query_timeout: timeout
  });
  
  try {
    const paramNames = Object.keys(parameters);
    const paramValues = Object.values(parameters);
    const placeholders = paramNames.map((_, i) => `$${i + 1}`).join(', ');
    
    const query = `SELECT * FROM ${functionName}(${placeholders})`;
    const result = await pool.query(query, paramValues);
    
    return {
      output: result.rows,
      returnValue: result.rows[0]
    };
  } finally {
    await pool.end();
  }
}

// ============================================================================
// MYSQL IMPLEMENTATION
// ============================================================================

async function executeMySql(connection, query, parameters, options) {
  const pool = mysql.createPool({
    host: connection.config.host,
    port: connection.config.port || 3306,
    database: connection.config.database,
    user: connection.credentials?.username,
    password: connection.credentials?.password ? decrypt(connection.credentials.password) : undefined,
    ssl: connection.config.ssl ? { rejectUnauthorized: false } : undefined,
    connectTimeout: options.timeout
  });
  
  try {
    // Convert @param to ? placeholders
    let processedQuery = query;
    const values = [];
    
    if (Array.isArray(parameters)) {
      parameters.forEach(param => {
        if (typeof param === 'object' && param.name) {
          const regex = new RegExp(`@${param.name}\\b`, 'g');
          processedQuery = processedQuery.replace(regex, '?');
          values.push(param.value);
        } else {
          values.push(param);
        }
      });
    }
    
    const [rows, fields] = await pool.execute(processedQuery, values);
    
    return {
      rows: rows.slice(0, options.maxRows),
      columns: fields?.map(f => f.name) || []
    };
  } finally {
    await pool.end();
  }
}

// ============================================================================
// ORACLE IMPLEMENTATION
// ============================================================================

async function executeOracle(connection, query, parameters, options) {
  let conn;
  
  try {
    conn = await oracledb.getConnection({
      user: connection.credentials?.username,
      password: connection.credentials?.password ? decrypt(connection.credentials.password) : undefined,
      connectString: `${connection.config.host}:${connection.config.port || 1521}/${connection.config.database}`
    });
    
    // Convert @param to :param for Oracle
    let processedQuery = query.replace(/@(\w+)/g, ':$1');
    
    // Build bind parameters
    const binds = {};
    if (Array.isArray(parameters)) {
      parameters.forEach(param => {
        if (typeof param === 'object' && param.name) {
          binds[param.name] = param.value;
        }
      });
    }
    
    const result = await conn.execute(processedQuery, binds, {
      outFormat: oracledb.OUT_FORMAT_OBJECT,
      maxRows: options.maxRows
    });
    
    return {
      rows: result.rows || [],
      columns: result.metaData?.map(m => m.name) || []
    };
  } finally {
    if (conn) {
      await conn.close();
    }
  }
}

// ============================================================================
// API PROXY
// ============================================================================

app.post('/callInternalApi', async (req, res) => {
  try {
    const {
      connectionId,
      baseUrl,
      endpoint,
      method = 'GET',
      headers = {},
      body = null,
      queryParams = {},
      timeout = 30000
    } = req.body;
    
    let apiConfig;
    
    if (connectionId) {
      const connection = connectionStore.get(connectionId);
      if (!connection) {
        return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
      }
      apiConfig = {
        baseUrl: connection.config.baseUrl,
        headers: connection.config.headers || {},
        auth: connection.config.auth
      };
      
      // Decrypt auth credentials
      if (apiConfig.auth?.password) {
        apiConfig.auth.password = decrypt(connection.credentials?.password || apiConfig.auth.password);
      }
      if (apiConfig.auth?.token) {
        apiConfig.auth.token = decrypt(connection.credentials?.token || apiConfig.auth.token);
      }
      if (apiConfig.auth?.key) {
        apiConfig.auth.key = decrypt(connection.credentials?.apiKey || apiConfig.auth.key);
      }
    } else if (baseUrl) {
      apiConfig = { baseUrl, headers: {}, auth: null };
    } else {
      return res.status(400).json(errorResponse('connectionId or baseUrl is required', 'VALIDATION_ERROR'));
    }
    
    const url = new URL(endpoint, apiConfig.baseUrl);
    
    // Add query parameters
    Object.entries(queryParams).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
    
    // Merge headers
    const mergedHeaders = {
      ...apiConfig.headers,
      ...headers
    };
    
    if (body && !mergedHeaders['Content-Type']) {
      mergedHeaders['Content-Type'] = 'application/json';
    }
    
    // Add authentication
    if (apiConfig.auth) {
      switch (apiConfig.auth.type) {
        case 'basic':
          const creds = Buffer.from(`${apiConfig.auth.username}:${apiConfig.auth.password}`).toString('base64');
          mergedHeaders['Authorization'] = `Basic ${creds}`;
          break;
        case 'bearer':
          mergedHeaders['Authorization'] = `Bearer ${apiConfig.auth.token}`;
          break;
        case 'apikey':
          mergedHeaders[apiConfig.auth.headerName || 'X-API-Key'] = apiConfig.auth.key;
          break;
      }
    }
    
    const startTime = Date.now();
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url.toString(), {
        method,
        headers: mergedHeaders,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      const responseText = await response.text();
      let responseData;
      
      try {
        responseData = JSON.parse(responseText);
      } catch {
        responseData = responseText;
      }
      
      res.json(successResponse({
        statusCode: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        data: responseData,
        executionTime: Date.now() - startTime
      }));
    } catch (fetchError) {
      clearTimeout(timeoutId);
      
      if (fetchError.name === 'AbortError') {
        res.status(504).json(errorResponse('Request timeout', 'TIMEOUT'));
      } else {
        throw fetchError;
      }
    }
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'API_ERROR'));
  }
});

// ============================================================================
// FILE SYSTEM ACCESS
// ============================================================================

app.post('/listFiles', async (req, res) => {
  try {
    const {
      connectionId,
      path: relativePath,
      pattern = '*',
      recursive = false,
      includeMetadata = true
    } = req.body;
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    if (connection.type !== 'fileshare') {
      return res.status(400).json(errorResponse('Not a file share connection', 'VALIDATION_ERROR'));
    }
    
    const basePath = connection.config.basePath;
    const fullPath = path.resolve(basePath, relativePath || '');
    
    // Security: Ensure path doesn't escape base directory
    if (!fullPath.startsWith(path.resolve(basePath))) {
      return res.status(403).json(errorResponse('Access denied: Path outside allowed directory', 'FORBIDDEN'));
    }
    
    const files = await listDirectory(fullPath, basePath, pattern, recursive, includeMetadata);
    
    res.json(successResponse({
      path: relativePath,
      files,
      count: files.length
    }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'FILE_ERROR'));
  }
});

app.post('/readFile', async (req, res) => {
  try {
    const {
      connectionId,
      path: relativePath,
      encoding = 'utf8',
      maxSize = 10 * 1024 * 1024
    } = req.body;
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    if (connection.type !== 'fileshare') {
      return res.status(400).json(errorResponse('Not a file share connection', 'VALIDATION_ERROR'));
    }
    
    if (!connection.config.allowRead) {
      return res.status(403).json(errorResponse('Read access not permitted', 'FORBIDDEN'));
    }
    
    const basePath = connection.config.basePath;
    const fullPath = path.resolve(basePath, relativePath);
    
    // Security check
    if (!fullPath.startsWith(path.resolve(basePath))) {
      return res.status(403).json(errorResponse('Access denied: Path outside allowed directory', 'FORBIDDEN'));
    }
    
    const stats = await fs.stat(fullPath);
    
    if (stats.size > maxSize) {
      return res.status(413).json(errorResponse(`File too large: ${stats.size} bytes (max: ${maxSize})`, 'FILE_TOO_LARGE'));
    }
    
    let content;
    if (encoding === 'base64') {
      const buffer = await fs.readFile(fullPath);
      content = buffer.toString('base64');
    } else {
      content = await fs.readFile(fullPath, encoding);
    }
    
    res.json(successResponse({
      path: relativePath,
      content,
      size: stats.size,
      encoding,
      modified: stats.mtime.toISOString()
    }));
  } catch (error) {
    if (error.code === 'ENOENT') {
      res.status(404).json(errorResponse('File not found', 'NOT_FOUND'));
    } else {
      res.status(500).json(errorResponse(error.message, 'FILE_ERROR'));
    }
  }
});

app.post('/writeFile', async (req, res) => {
  try {
    const {
      connectionId,
      path: relativePath,
      content,
      encoding = 'utf8',
      overwrite = false
    } = req.body;
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    if (connection.type !== 'fileshare') {
      return res.status(400).json(errorResponse('Not a file share connection', 'VALIDATION_ERROR'));
    }
    
    if (!connection.config.allowWrite) {
      return res.status(403).json(errorResponse('Write access not permitted', 'FORBIDDEN'));
    }
    
    const basePath = connection.config.basePath;
    const fullPath = path.resolve(basePath, relativePath);
    
    // Security check
    if (!fullPath.startsWith(path.resolve(basePath))) {
      return res.status(403).json(errorResponse('Access denied: Path outside allowed directory', 'FORBIDDEN'));
    }
    
    // Check if file exists
    let exists = false;
    try {
      await fs.access(fullPath);
      exists = true;
    } catch {}
    
    if (exists && !overwrite) {
      return res.status(409).json(errorResponse('File already exists. Set overwrite=true to replace.', 'FILE_EXISTS'));
    }
    
    // Ensure directory exists
    await fs.mkdir(path.dirname(fullPath), { recursive: true });
    
    // Write file
    let buffer;
    if (encoding === 'base64') {
      buffer = Buffer.from(content, 'base64');
    } else {
      buffer = Buffer.from(content, encoding);
    }
    
    await fs.writeFile(fullPath, buffer);
    
    res.json(successResponse({
      path: relativePath,
      size: buffer.length,
      created: !exists,
      overwritten: exists && overwrite
    }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'FILE_ERROR'));
  }
});

async function listDirectory(dirPath, basePath, pattern, recursive, includeMetadata) {
  const files = [];
  const entries = await fs.readdir(dirPath, { withFileTypes: true });
  
  // Convert glob pattern to regex
  const regexPattern = pattern
    .replace(/\./g, '\\.')
    .replace(/\*/g, '.*')
    .replace(/\?/g, '.');
  const regex = new RegExp(`^${regexPattern}$`, 'i');
  
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    const relativePath = path.relative(basePath, fullPath);
    
    if (entry.isDirectory()) {
      if (recursive) {
        const subFiles = await listDirectory(fullPath, basePath, pattern, recursive, includeMetadata);
        files.push(...subFiles);
      }
      
      files.push({
        name: entry.name,
        path: relativePath,
        isDirectory: true
      });
    } else if (regex.test(entry.name)) {
      const fileInfo = {
        name: entry.name,
        path: relativePath,
        isDirectory: false
      };
      
      if (includeMetadata) {
        const stats = await fs.stat(fullPath);
        fileInfo.size = stats.size;
        fileInfo.modified = stats.mtime.toISOString();
        fileInfo.created = stats.birthtime.toISOString();
      }
      
      files.push(fileInfo);
    }
  }
  
  return files;
}

// ============================================================================
// LDAP / ACTIVE DIRECTORY
// ============================================================================

app.post('/ldapSearch', async (req, res) => {
  try {
    const {
      connectionId,
      baseDn,
      filter,
      attributes = ['*'],
      scope = 'sub',
      maxResults = 100
    } = req.body;
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    if (connection.type !== 'ldap') {
      return res.status(400).json(errorResponse('Not an LDAP connection', 'VALIDATION_ERROR'));
    }
    
    const results = await performLdapSearch(connection, {
      baseDn: baseDn || connection.config.baseDn,
      filter,
      attributes,
      scope,
      maxResults
    });
    
    res.json(successResponse({
      entries: results,
      count: results.length
    }));
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'LDAP_ERROR'));
  }
});

app.post('/ldapAuthenticate', async (req, res) => {
  try {
    const { connectionId, username, password } = req.body;
    
    const connection = connectionStore.get(connectionId);
    if (!connection) {
      return res.status(404).json(errorResponse('Connection not found', 'NOT_FOUND'));
    }
    
    if (connection.type !== 'ldap') {
      return res.status(400).json(errorResponse('Not an LDAP connection', 'VALIDATION_ERROR'));
    }
    
    try {
      const user = await ldapAuthenticate(connection, username, password);
      
      res.json(successResponse({
        authenticated: true,
        user: {
          dn: user.dn,
          username: user.sAMAccountName || user.uid || username,
          email: user.mail,
          displayName: user.displayName || user.cn,
          groups: user.memberOf || []
        }
      }));
    } catch (authError) {
      res.json(successResponse({
        authenticated: false,
        error: 'Invalid credentials'
      }));
    }
  } catch (error) {
    res.status(500).json(errorResponse(error.message, 'LDAP_ERROR'));
  }
});

function performLdapSearch(connection, options) {
  return new Promise((resolve, reject) => {
    const client = ldap.createClient({
      url: connection.config.url,
      tlsOptions: connection.config.tlsOptions || { rejectUnauthorized: false }
    });
    
    // Bind with service account
    const bindDn = connection.config.bindDn || connection.credentials?.username;
    const bindPassword = connection.credentials?.password ? decrypt(connection.credentials.password) : '';
    
    client.bind(bindDn, bindPassword, (bindErr) => {
      if (bindErr) {
        client.unbind();
        return reject(new Error(`LDAP bind failed: ${bindErr.message}`));
      }
      
      const searchOpts = {
        scope: options.scope,
        filter: options.filter,
        attributes: options.attributes,
        sizeLimit: options.maxResults
      };
      
      const results = [];
      
      client.search(options.baseDn, searchOpts, (searchErr, searchRes) => {
        if (searchErr) {
          client.unbind();
          return reject(new Error(`LDAP search failed: ${searchErr.message}`));
        }
        
        searchRes.on('searchEntry', (entry) => {
          const obj = {};
          entry.attributes.forEach(attr => {
            obj[attr.type] = attr.values.length === 1 ? attr.values[0] : attr.values;
          });
          obj.dn = entry.dn.toString();
          results.push(obj);
        });
        
        searchRes.on('error', (err) => {
          client.unbind();
          reject(new Error(`LDAP search error: ${err.message}`));
        });
        
        searchRes.on('end', () => {
          client.unbind();
          resolve(results);
        });
      });
    });
  });
}

function ldapAuthenticate(connection, username, password) {
  return new Promise((resolve, reject) => {
    const client = ldap.createClient({
      url: connection.config.url,
      tlsOptions: connection.config.tlsOptions || { rejectUnauthorized: false }
    });
    
    // First, find the user
    const bindDn = connection.config.bindDn || connection.credentials?.username;
    const bindPassword = connection.credentials?.password ? decrypt(connection.credentials.password) : '';
    
    client.bind(bindDn, bindPassword, (bindErr) => {
      if (bindErr) {
        client.unbind();
        return reject(new Error('Service account bind failed'));
      }
      
      // Search for user
      const filter = connection.config.userFilter
        ? connection.config.userFilter.replace('{username}', username)
        : `(|(sAMAccountName=${username})(userPrincipalName=${username})(uid=${username}))`;
      
      client.search(connection.config.baseDn, {
        scope: 'sub',
        filter,
        attributes: ['dn', 'sAMAccountName', 'uid', 'mail', 'displayName', 'cn', 'memberOf']
      }, (searchErr, searchRes) => {
        if (searchErr) {
          client.unbind();
          return reject(new Error('User search failed'));
        }
        
        let userEntry = null;
        
        searchRes.on('searchEntry', (entry) => {
          if (!userEntry) {
            userEntry = {};
            entry.attributes.forEach(attr => {
              userEntry[attr.type] = attr.values.length === 1 ? attr.values[0] : attr.values;
            });
            userEntry.dn = entry.dn.toString();
          }
        });
        
        searchRes.on('end', () => {
          if (!userEntry) {
            client.unbind();
            return reject(new Error('User not found'));
          }
          
          // Attempt to bind as the user
          const userClient = ldap.createClient({
            url: connection.config.url,
            tlsOptions: connection.config.tlsOptions || { rejectUnauthorized: false }
          });
          
          userClient.bind(userEntry.dn, password, (userBindErr) => {
            userClient.unbind();
            client.unbind();
            
            if (userBindErr) {
              return reject(new Error('Invalid credentials'));
            }
            
            resolve(userEntry);
          });
        });
        
        searchRes.on('error', (err) => {
          client.unbind();
          reject(new Error(`Search error: ${err.message}`));
        });
      });
    });
  });
}

// ============================================================================
// CONNECTION TESTING
// ============================================================================

async function testDatabaseConnection(connection) {
  try {
    switch (connection.type) {
      case 'mssql':
        await executeMsSql(connection, 'SELECT 1 AS test', [], { timeout: 5000, maxRows: 1 });
        break;
      case 'postgresql':
        await executePostgres(connection, 'SELECT 1 AS test', [], { timeout: 5000, maxRows: 1 });
        break;
      case 'mysql':
        await executeMySql(connection, 'SELECT 1 AS test', [], { timeout: 5000, maxRows: 1 });
        break;
      case 'oracle':
        await executeOracle(connection, 'SELECT 1 FROM DUAL', [], { timeout: 5000, maxRows: 1 });
        break;
    }
    return { success: true, message: 'Connection successful' };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

async function testApiConnection(connection) {
  try {
    const url = new URL(connection.config.healthEndpoint || '/', connection.config.baseUrl);
    const response = await fetch(url.toString(), { method: 'GET', timeout: 5000 });
    return { 
      success: response.ok, 
      message: response.ok ? 'API reachable' : `HTTP ${response.status}` 
    };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

async function testFileShareConnection(connection) {
  try {
    await fs.access(connection.config.basePath);
    const stats = await fs.stat(connection.config.basePath);
    if (!stats.isDirectory()) {
      return { success: false, message: 'Path is not a directory' };
    }
    return { success: true, message: 'File share accessible' };
  } catch (error) {
    return { success: false, message: error.message };
  }
}

async function testLdapConnection(connection) {
  return new Promise((resolve) => {
    const client = ldap.createClient({
      url: connection.config.url,
      tlsOptions: connection.config.tlsOptions || { rejectUnauthorized: false },
      connectTimeout: 5000
    });
    
    const bindDn = connection.config.bindDn || connection.credentials?.username;
    const bindPassword = connection.credentials?.password ? decrypt(connection.credentials.password) : '';
    
    client.bind(bindDn, bindPassword, (err) => {
      client.unbind();
      if (err) {
        resolve({ success: false, message: err.message });
      } else {
        resolve({ success: true, message: 'LDAP bind successful' });
      }
    });
    
    client.on('error', (err) => {
      resolve({ success: false, message: err.message });
    });
  });
}

// ============================================================================
// PERSISTENCE
// ============================================================================

const CONNECTIONS_FILE = process.env.CONNECTIONS_FILE || '/app/data/connections.json';

async function loadConnections() {
  try {
    const data = await fs.readFile(CONNECTIONS_FILE, 'utf8');
    const connections = JSON.parse(data);
    connections.forEach(c => connectionStore.set(c.id, c));
    console.log(`Loaded ${connections.length} connections`);
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.error('Error loading connections:', error.message);
    }
  }
}

async function saveConnections() {
  try {
    const dir = path.dirname(CONNECTIONS_FILE);
    await fs.mkdir(dir, { recursive: true });
    const connections = Array.from(connectionStore.values());
    await fs.writeFile(CONNECTIONS_FILE, JSON.stringify(connections, null, 2));
  } catch (error) {
    console.error('Error saving connections:', error.message);
  }
}

// ============================================================================
// HEALTH CHECK
// ============================================================================

app.get('/health', (req, res) => {
  res.json({ status: 'ok', connections: connectionStore.size });
});

// ============================================================================
// START SERVER
// ============================================================================

const PORT = process.env.PORT || 3001;

loadConnections().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`On-Prem Connector running on port ${PORT}`);
  });
});

module.exports = app;
