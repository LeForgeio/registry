# LeForge Nintex Forms Integration

JavaScript Form Plugins that extend Nintex Forms with AI, calculations, and data processing capabilities.

## Available Controls

| Control | Description | Use Cases |
|---------|-------------|-----------|
| **AI Text Generator** | Generate or complete text using AI | Auto-fill descriptions, summaries, suggestions |
| **Formula Calculator** | Evaluate Excel-style formulas | Complex calculations, conditional logic |
| **Data Lookup** | Fetch data from external sources | Auto-populate fields, validate data |
| **Crypto Hash** | Generate secure hashes | Document fingerprints, checksums |
| **QR Code Generator** | Create QR codes from form data | Asset labels, quick links |

## Installation

### 1. Configure LeForge Connection

In Nintex Forms Admin:
1. Go to **Settings** → **Custom Connections**
2. Add new connection:
   - **Name**: `LeForge`
   - **Base URL**: `https://your-leforge-instance.com/api/v1`
   - **Authentication**: API Key Header
   - **Header Name**: `X-API-Key`
   - **Header Value**: Your LeForge API key

### 2. Install Form Plugins

For each control you want to use:

1. Go to **Settings** → **Custom Controls**
2. Click **Add Control**
3. Upload the control's `.js` file from `controls/`
4. Configure default settings

### 3. Use in Forms

Controls appear in the **Custom** section of the form designer toolbox.

## Control Configuration

Each control supports these common properties:

| Property | Type | Description |
|----------|------|-------------|
| `leforgeUrl` | string | LeForge API base URL |
| `apiKey` | string | API key (use form variable for security) |
| `timeout` | number | Request timeout in ms (default: 30000) |

## Development

### Building Controls

```bash
cd controls
npm install
npm run build
```

### Testing Locally

```bash
npm run dev
```

Opens a test harness at `http://localhost:3000` to preview controls.

## Control Details

### AI Text Generator

Generate or complete text using LeForge LLM service.

**Properties:**
- `prompt` - System prompt for AI behavior
- `inputField` - Form field to use as input
- `outputField` - Form field to write result
- `maxTokens` - Maximum response length
- `provider` - LLM provider (openai, ollama, etc.)

**Events:**
- `onGenerate` - Fired when generation completes
- `onError` - Fired on API error

### Formula Calculator

Evaluate Excel-style formulas with form field values.

**Properties:**
- `formula` - Excel formula (e.g., `=SUM(A1:A5)`)
- `variables` - Map form fields to formula variables
- `outputField` - Field to write result
- `precision` - Decimal precision

**Supported Functions:**
- Math: SUM, AVERAGE, MIN, MAX, ROUND, ABS, SQRT, POWER
- Logic: IF, AND, OR, NOT, IFERROR
- Text: CONCAT, LEFT, RIGHT, MID, LEN, UPPER, LOWER
- Date: TODAY, NOW, DATEDIF, YEAR, MONTH, DAY

### Data Lookup

Fetch and display data from LeForge services.

**Properties:**
- `endpoint` - API endpoint to call
- `method` - HTTP method (GET, POST)
- `inputMapping` - Map form fields to request params
- `outputMapping` - Map response to form fields
- `cacheTime` - Cache results for N seconds

### Crypto Hash

Generate cryptographic hashes of form values.

**Properties:**
- `algorithm` - Hash algorithm (sha256, sha512, md5)
- `inputField` - Field to hash
- `outputField` - Field for hash result
- `encoding` - Output encoding (hex, base64)

### QR Code Generator

Generate QR codes from form data.

**Properties:**
- `dataField` - Field containing QR data
- `size` - QR code size in pixels
- `errorCorrection` - Error correction level (L, M, Q, H)
- `outputField` - Image field for QR code

## Examples

### Auto-Generate Description

```javascript
// AI Text Generator configuration
{
  "prompt": "Generate a professional product description based on the provided details.",
  "inputField": "ProductName",
  "outputField": "Description",
  "maxTokens": 200
}
```

### Calculate Total with Tax

```javascript
// Formula Calculator configuration
{
  "formula": "=ROUND(Subtotal * (1 + TaxRate), 2)",
  "variables": {
    "Subtotal": "SubtotalField",
    "TaxRate": "TaxRateField"
  },
  "outputField": "TotalField"
}
```

### Generate Document Hash

```javascript
// Crypto Hash configuration
{
  "algorithm": "sha256",
  "inputField": "DocumentContent",
  "outputField": "DocumentHash",
  "encoding": "hex"
}
```

## Support

- Documentation: https://docs.leforge.io/integrations/nintex-forms
- Issues: https://github.com/LeForgeio/leforge/issues
- Community: https://community.leforge.io
