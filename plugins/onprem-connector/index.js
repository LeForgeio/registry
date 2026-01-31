/**
 * On-Premises Connector Plugin
 * 
 * Provides secure access to on-premises resources through LeForge.
 * Used with Cloudflare Tunnel to enable cloud-to-on-prem connectivity.
 * 
 * Supported backends:
 * - SQL Server, PostgreSQL, MySQL, Oracle
 * - REST APIs (internal endpoints)
 * - File shares (SMB/CIFS)
 * - LDAP/Active Directory
 */

// ============================================================================
// DATABASE CONNECTORS
// ============================================================================

/**
 * Execute a SQL query against an on-prem database
 * Supports parameterized queries to prevent SQL injection
 */
async function queryDatabase(input, context) {
  const {
    connectionId,      // Pre-configured connection ID (from LeForge settings)
    connectionString,  // Or direct connection string (if allowed)
    query,
    parameters = [],
    timeout = 30000,
    maxRows = 1000
  } = input;

  // Validate input
  if (!connectionId && !connectionString) {
    throw new Error('Either connectionId or connectionString is required');
  }
  if (!query) {
    throw new Error('Query is required');
  }

  // Get connection config
  const connConfig = connectionId 
    ? await getConnectionConfig(connectionId, context)
    : parseConnectionString(connectionString);

  // Execute based on database type
  let result;
  switch (connConfig.type) {
    case 'mssql':
      result = await executeMsSql(connConfig, query, parameters, { timeout, maxRows });
      break;
    case 'postgresql':
      result = await executePostgres(connConfig, query, parameters, { timeout, maxRows });
      break;
    case 'mysql':
      result = await executeMySql(connConfig, query, parameters, { timeout, maxRows });
      break;
    case 'oracle':
      result = await executeOracle(connConfig, query, parameters, { timeout, maxRows });
      break;
    default:
      throw new Error(`Unsupported database type: ${connConfig.type}`);
  }

  return {
    success: true,
    rows: result.rows,
    rowCount: result.rows.length,
    columns: result.columns,
    executionTime: result.executionTime
  };
}

/**
 * Execute a stored procedure
 */
async function executeStoredProcedure(input, context) {
  const {
    connectionId,
    procedureName,
    parameters = {},
    timeout = 60000
  } = input;

  if (!connectionId) throw new Error('connectionId is required');
  if (!procedureName) throw new Error('procedureName is required');

  const connConfig = await getConnectionConfig(connectionId, context);
  
  // Build procedure call based on database type
  let result;
  switch (connConfig.type) {
    case 'mssql':
      result = await executeMsSqlProc(connConfig, procedureName, parameters, timeout);
      break;
    case 'postgresql':
      result = await executePostgresFunc(connConfig, procedureName, parameters, timeout);
      break;
    default:
      throw new Error(`Stored procedures not supported for: ${connConfig.type}`);
  }

  return {
    success: true,
    result: result.output,
    returnValue: result.returnValue,
    executionTime: result.executionTime
  };
}

// ============================================================================
// REST API PROXY
// ============================================================================

/**
 * Proxy a request to an internal REST API
 * Allows cloud workflows to call on-prem APIs securely
 */
async function callInternalApi(input, context) {
  const {
    connectionId,      // Pre-configured API connection
    baseUrl,           // Or direct base URL (if allowed)
    endpoint,
    method = 'GET',
    headers = {},
    body = null,
    queryParams = {},
    timeout = 30000,
    validateSsl = true
  } = input;

  // Get API config
  const apiConfig = connectionId
    ? await getApiConfig(connectionId, context)
    : { baseUrl, headers: {}, auth: null };

  const url = new URL(endpoint, apiConfig.baseUrl);
  
  // Add query parameters
  Object.entries(queryParams).forEach(([key, value]) => {
    url.searchParams.append(key, value);
  });

  // Merge headers (connection config headers + request headers)
  const mergedHeaders = {
    ...apiConfig.headers,
    ...headers,
    'Content-Type': 'application/json'
  };

  // Add authentication if configured
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

  try {
    const response = await fetch(url.toString(), {
      method,
      headers: mergedHeaders,
      body: body ? JSON.stringify(body) : undefined,
      timeout,
      // Note: In production, use proper SSL certificate validation
    });

    const responseText = await response.text();
    let responseData;
    
    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = responseText;
    }

    return {
      success: response.ok,
      statusCode: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      data: responseData,
      executionTime: Date.now() - startTime
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      executionTime: Date.now() - startTime
    };
  }
}

// ============================================================================
// FILE SYSTEM ACCESS
// ============================================================================

/**
 * List files in an on-prem file share
 */
async function listFiles(input, context) {
  const {
    connectionId,
    path,
    pattern = '*',
    recursive = false,
    includeMetadata = true
  } = input;

  const shareConfig = await getFileShareConfig(connectionId, context);
  const fullPath = resolvePath(shareConfig.basePath, path);

  // Security: Ensure path doesn't escape base directory
  if (!fullPath.startsWith(shareConfig.basePath)) {
    throw new Error('Access denied: Path outside allowed directory');
  }

  const files = await listDirectory(fullPath, {
    pattern,
    recursive,
    includeMetadata
  });

  return {
    success: true,
    path: path,
    files: files.map(f => ({
      name: f.name,
      path: f.relativePath,
      size: f.size,
      modified: f.modified,
      isDirectory: f.isDirectory
    })),
    count: files.length
  };
}

/**
 * Read a file from on-prem file share
 */
async function readFile(input, context) {
  const {
    connectionId,
    path,
    encoding = 'utf8',  // 'utf8', 'base64', 'binary'
    maxSize = 10 * 1024 * 1024  // 10MB default limit
  } = input;

  const shareConfig = await getFileShareConfig(connectionId, context);
  const fullPath = resolvePath(shareConfig.basePath, path);

  // Security check
  if (!fullPath.startsWith(shareConfig.basePath)) {
    throw new Error('Access denied: Path outside allowed directory');
  }

  const stats = await getFileStats(fullPath);
  if (stats.size > maxSize) {
    throw new Error(`File too large: ${stats.size} bytes (max: ${maxSize})`);
  }

  const content = await readFileContent(fullPath, encoding);

  return {
    success: true,
    path: path,
    content: content,
    size: stats.size,
    encoding: encoding,
    modified: stats.modified
  };
}

/**
 * Write a file to on-prem file share
 */
async function writeFile(input, context) {
  const {
    connectionId,
    path,
    content,
    encoding = 'utf8',
    overwrite = false
  } = input;

  const shareConfig = await getFileShareConfig(connectionId, context);
  
  // Check write permission
  if (!shareConfig.allowWrite) {
    throw new Error('Write access not permitted for this connection');
  }

  const fullPath = resolvePath(shareConfig.basePath, path);

  // Security check
  if (!fullPath.startsWith(shareConfig.basePath)) {
    throw new Error('Access denied: Path outside allowed directory');
  }

  // Check if file exists
  const exists = await fileExists(fullPath);
  if (exists && !overwrite) {
    throw new Error('File already exists. Set overwrite=true to replace.');
  }

  await writeFileContent(fullPath, content, encoding);

  return {
    success: true,
    path: path,
    size: Buffer.byteLength(content, encoding),
    created: !exists,
    overwritten: exists && overwrite
  };
}

// ============================================================================
// LDAP / ACTIVE DIRECTORY
// ============================================================================

/**
 * Search Active Directory / LDAP
 */
async function ldapSearch(input, context) {
  const {
    connectionId,
    baseDn,
    filter,
    attributes = ['*'],
    scope = 'subtree',  // 'base', 'one', 'subtree'
    maxResults = 100
  } = input;

  const ldapConfig = await getLdapConfig(connectionId, context);

  const results = await performLdapSearch(ldapConfig, {
    baseDn: baseDn || ldapConfig.defaultBaseDn,
    filter,
    attributes,
    scope,
    maxResults
  });

  return {
    success: true,
    entries: results,
    count: results.length
  };
}

/**
 * Authenticate user against Active Directory
 */
async function ldapAuthenticate(input, context) {
  const {
    connectionId,
    username,
    password
  } = input;

  const ldapConfig = await getLdapConfig(connectionId, context);

  try {
    const user = await ldapBind(ldapConfig, username, password);
    
    return {
      success: true,
      authenticated: true,
      user: {
        dn: user.dn,
        username: user.sAMAccountName,
        email: user.mail,
        displayName: user.displayName,
        groups: user.memberOf
      }
    };
  } catch (error) {
    return {
      success: true,
      authenticated: false,
      error: 'Invalid credentials'
    };
  }
}

// ============================================================================
// CONNECTION MANAGEMENT (requires LeForge admin)
// ============================================================================

/**
 * Test a connection configuration
 */
async function testConnection(input, context) {
  const { connectionId, type } = input;

  let result;
  switch (type) {
    case 'database':
      result = await testDatabaseConnection(connectionId, context);
      break;
    case 'api':
      result = await testApiConnection(connectionId, context);
      break;
    case 'fileshare':
      result = await testFileShareConnection(connectionId, context);
      break;
    case 'ldap':
      result = await testLdapConnection(connectionId, context);
      break;
    default:
      throw new Error(`Unknown connection type: ${type}`);
  }

  return {
    success: result.success,
    message: result.message,
    latency: result.latency
  };
}

/**
 * List configured connections (admin only)
 */
async function listConnections(input, context) {
  // Verify admin permission
  if (!context.isAdmin) {
    throw new Error('Admin permission required');
  }

  const connections = await getAllConnections();

  return {
    success: true,
    connections: connections.map(c => ({
      id: c.id,
      name: c.name,
      type: c.type,
      description: c.description,
      lastTested: c.lastTested,
      status: c.status
    }))
  };
}

// ============================================================================
// HELPER FUNCTIONS (STUBS - implement based on actual requirements)
// ============================================================================

async function getConnectionConfig(connectionId, context) {
  // In production: fetch from LeForge's encrypted connection store
  // This would decrypt and return the connection configuration
  throw new Error('Connection management not yet implemented');
}

async function getApiConfig(connectionId, context) {
  throw new Error('API config management not yet implemented');
}

async function getFileShareConfig(connectionId, context) {
  throw new Error('File share config management not yet implemented');
}

async function getLdapConfig(connectionId, context) {
  throw new Error('LDAP config management not yet implemented');
}

function parseConnectionString(connectionString) {
  // Parse database connection string into config object
  // Support formats: mssql://, postgresql://, mysql://, oracle://
  const url = new URL(connectionString);
  return {
    type: url.protocol.replace(':', ''),
    host: url.hostname,
    port: url.port,
    database: url.pathname.slice(1),
    username: url.username,
    password: url.password
  };
}

function resolvePath(basePath, relativePath) {
  // Safely resolve path, preventing directory traversal
  const path = require('path');
  const resolved = path.resolve(basePath, relativePath);
  return resolved;
}

// Database execution stubs
async function executeMsSql(config, query, params, options) {
  throw new Error('MS SQL connector not yet implemented');
}

async function executePostgres(config, query, params, options) {
  throw new Error('PostgreSQL connector not yet implemented');
}

async function executeMySql(config, query, params, options) {
  throw new Error('MySQL connector not yet implemented');
}

async function executeOracle(config, query, params, options) {
  throw new Error('Oracle connector not yet implemented');
}

// File system stubs
async function listDirectory(path, options) {
  throw new Error('File system access not yet implemented');
}

async function readFileContent(path, encoding) {
  throw new Error('File system access not yet implemented');
}

async function writeFileContent(path, content, encoding) {
  throw new Error('File system access not yet implemented');
}

async function fileExists(path) {
  throw new Error('File system access not yet implemented');
}

async function getFileStats(path) {
  throw new Error('File system access not yet implemented');
}

// LDAP stubs
async function performLdapSearch(config, options) {
  throw new Error('LDAP connector not yet implemented');
}

async function ldapBind(config, username, password) {
  throw new Error('LDAP connector not yet implemented');
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  // Database
  queryDatabase,
  executeStoredProcedure,
  
  // REST API proxy
  callInternalApi,
  
  // File system
  listFiles,
  readFile,
  writeFile,
  
  // LDAP / Active Directory
  ldapSearch,
  ldapAuthenticate,
  
  // Connection management
  testConnection,
  listConnections
};
