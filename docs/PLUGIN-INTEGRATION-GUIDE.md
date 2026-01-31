# Plugin-to-Integration Guide

> How to make your ForgeHook plugin work seamlessly with platform integrations

## The Relationship

```
┌─────────────────────────────────────────────────────────────────────────┐
│  YOUR PLUGIN (runs in LeForge)                                          │
│  forgehooks-registry/plugins/excel-utils/index.js                       │
│                                                                         │
│  Exports functions that LeForge exposes as REST endpoints:              │
│  module.exports = { parseCSV, toCSV, parseXLSX, filterRows }            │
│                    ↓                                                    │
│  LeForge creates: POST /api/v1/plugins/excel-utils/parseCSV             │
└────────────────────────────────────│────────────────────────────────────┘
                                     │
                                     │ HTTP REST API
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  INTEGRATION (runs in the target platform)                              │
│  forgehooks-registry/integrations/nintex-forms/controls/excel-parser.js │
│                                                                         │
│  Makes HTTP calls to your plugin:                                       │
│  fetch(`${leforgeUrl}/plugins/excel-utils/parseCSV`, {                  │
│    method: 'POST',                                                      │
│    body: JSON.stringify({ data: csvText, hasHeaders: true })            │
│  })                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Plugin Developer Checklist

### 1. Export Consistent Function Signatures

```javascript
// ✅ Good - accepts object with named parameters
function parseCSV(input, options = {}) {
  const text = input.data || input.text || input;
  const hasHeaders = input.hasHeaders ?? options.hasHeaders ?? true;
  // ...
}

// ❌ Bad - requires specific parameter order
function parseCSV(text, delimiter, hasHeaders, trimValues) {
  // Hard for integrations to call correctly
}
```

### 2. Document Your Endpoints in forgehook.json

```json
{
  "id": "excel-utils",
  "endpoints": [
    {
      "method": "POST",
      "path": "/parseCSV",
      "description": "Parse CSV text to array of objects",
      "requestBody": {
        "data": "Name,Age\nAlice,30\nBob,25",
        "hasHeaders": true,
        "delimiter": ","
      },
      "responseExample": {
        "success": true,
        "data": [
          { "Name": "Alice", "Age": 30 },
          { "Name": "Bob", "Age": 25 }
        ]
      }
    }
  ]
}
```

### 3. Return Standard Response Format

```javascript
// LeForge wraps your function output, but you can help:

// ✅ Return clear data structures
function parseCSV(input) {
  const rows = doParsing(input.data);
  return {
    headers: rows[0],
    data: rows.slice(1),
    rowCount: rows.length - 1
  };
}

// LeForge API returns:
// {
//   "success": true,
//   "data": {
//     "headers": ["Name", "Age"],
//     "data": [["Alice", 30], ["Bob", 25]],
//     "rowCount": 2
//   }
// }
```

### 4. Handle Errors Gracefully

```javascript
function parseCSV(input) {
  if (!input.data && !input.text) {
    throw new Error('Missing required field: data or text');
  }
  
  try {
    return doParsing(input.data);
  } catch (e) {
    throw new Error(`CSV parse error: ${e.message}`);
  }
}

// LeForge converts to:
// {
//   "success": false,
//   "error": {
//     "code": "PLUGIN_ERROR",
//     "message": "Missing required field: data or text"
//   }
// }
```

### 5. Accept Multiple Input Formats

Integration developers use different patterns. Support them all:

```javascript
function parseCSV(input, options = {}) {
  // Accept: parseCSV({ data: "..." })
  // Accept: parseCSV({ text: "..." })
  // Accept: parseCSV({ csv: "..." })
  // Accept: parseCSV("...") (raw string)
  
  const text = typeof input === 'string' 
    ? input 
    : (input.data || input.text || input.csv || '');
    
  // Merge options from input object and options parameter
  const opts = {
    delimiter: ',',
    hasHeaders: true,
    ...(typeof input === 'object' ? input : {}),
    ...options
  };
  
  // Ignore data fields in options
  delete opts.data;
  delete opts.text;
  delete opts.csv;
  
  return doParsing(text, opts);
}
```

## Integration Developer Workflow

### Step 1: Identify Which Plugin You Need

Browse the plugin registry or docs:
- `excel-utils` - Excel/CSV parsing
- `llm-service` - AI text generation
- `crypto-service` - Hashing, encryption
- `formula-engine` - Excel formulas
- `qrcode-utils` - QR code generation

### Step 2: Check the Plugin's Endpoints

Look at the plugin's `forgehook.json` or call the docs endpoint:

```bash
curl https://app.leforge.io/api/v1/plugins/excel-utils/docs
```

### Step 3: Create Your Integration Control

```javascript
class MyControl {
  async callPlugin(pluginId, endpoint, data) {
    const response = await fetch(
      `${this.config.leforgeUrl}/plugins/${pluginId}/${endpoint}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      }
    );
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Plugin call failed');
    }
    
    return result.data;
  }
  
  async parseExcel(fileBase64) {
    return this.callPlugin('excel-utils', 'parseXLSX', {
      data: fileBase64,
      hasHeaders: true
    });
  }
}
```

## Example: Complete Flow

### Plugin Side (excel-utils/index.js)

```javascript
function filterRows(input) {
  const { data, column, operator, value } = input;
  
  return data.filter(row => {
    const cellValue = row[column];
    switch (operator) {
      case 'equals': return cellValue == value;
      case 'contains': return String(cellValue).includes(value);
      case 'greater': return cellValue > value;
      case 'less': return cellValue < value;
      default: return true;
    }
  });
}

module.exports = { filterRows };
```

### Integration Side (nintex-forms/controls/data-filter.js)

```javascript
class LeForgeDataFilter {
  async filterData(data, column, operator, value) {
    const response = await fetch(
      `${this.config.leforgeUrl}/plugins/excel-utils/filterRows`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data, column, operator, value })
      }
    );
    
    const result = await response.json();
    return result.data;
  }
}
```

### Form Usage (Nintex Forms)

```html
<!-- In Nintex Forms HTML control -->
<div id="filter-control"></div>

<script>
  const filter = new LeForgeDataFilter(
    document.getElementById('filter-control'),
    {
      leforgeUrl: 'https://app.leforge.io/api/v1',
      apiKey: 'YOUR_API_KEY'
    }
  );
  
  // Filter data from another control
  const excelData = excelParser.getData();
  const filtered = await filter.filterData(
    excelData, 
    'Status', 
    'equals', 
    'Approved'
  );
</script>
```

## Testing Your Plugin for Integration Compatibility

```bash
# 1. Start LeForge locally
docker compose up -d

# 2. Test your plugin endpoint directly
curl -X POST http://localhost:4000/api/v1/plugins/excel-utils/parseCSV \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": "Name,Age\nAlice,30", "hasHeaders": true}'

# 3. Expected response format
{
  "success": true,
  "data": [
    { "Name": "Alice", "Age": "30" }
  ],
  "requestId": "...",
  "timestamp": "..."
}
```

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Integration gets `undefined` | Check you're returning data, not just assigning |
| CORS errors | LeForge handles CORS; check your domain whitelist |
| Auth failures | API key must be valid and have plugin permissions |
| Large file timeouts | Use streaming endpoints or increase timeout |
| Missing function | Ensure it's exported in `module.exports` |

---

*See [FORGEHOOK_SPECIFICATION.md](../docs/FORGEHOOK_SPECIFICATION.md) for complete plugin documentation.*
