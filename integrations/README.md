# LeForge Platform Integrations

This folder contains ready-to-use connectors and integration packages for various workflow automation and low-code platforms.

## Available Integrations

| Platform | Folder | Status | Format |
|----------|--------|--------|--------|
| **Nintex Forms** | `nintex-forms/` | ✅ Ready | JavaScript Form Controls |
| **Nintex Workflow Cloud** | `nintex-cloud/` | ✅ Ready | OpenAPI Xtension |
| **Nintex K2** | `nintex-k2/` | 🚧 In Development | Swagger + SmartObjects |
| **Power Automate** | `power-automate/` | 🚧 In Development | OpenAPI Custom Connector |
| **n8n** | `n8n/` | 🚧 In Development | TypeScript npm package |
| **Salesforce** | `salesforce/` | 📋 Planned | External Services + Apex |
| **ServiceNow** | `servicenow/` | 📋 Planned | IntegrationHub Spoke |
| **OutSystems** | `outsystems/` | 📋 Planned | Forge Component |
| **Mendix** | `mendix/` | 📋 Planned | Marketplace Module |

## Quick Start

### Nintex Forms
1. Go to `nintex-forms/` folder
2. Run `npm install && npm run build` to create bundled control
3. Host `dist/leforge-nintex-controls.min.js` on a CDN or SharePoint
4. Add HTML control in Nintex Forms Designer
5. Include script and initialize controls

```html
<script src="https://your-cdn.com/leforge-nintex-controls.min.js"></script>
<div id="ai-generator"></div>
<script>
  new LeForgeAITextGenerator(
    document.getElementById('ai-generator'),
    { leforgeUrl: 'https://app.leforge.io/api/v1', apiKey: 'KEY' }
  );
</script>
```

### Power Automate
1. Go to `power-automate/` folder
2. Import the connector package in Power Automate
3. Configure your API connection
4. Use actions in your flows

### Nintex Workflow Cloud

1. Go to `nintex-cloud/` folder
2. Upload the Swagger file as an Xtension
3. Configure authentication
4. Drag-and-drop actions in workflows

**Available Xtensions:**
- `onprem-connector.xtension.json` - Access on-prem databases, APIs, file shares

See [Hybrid Cloud Architecture](../docs/HYBRID-CLOUD-ARCHITECTURE.md) for setup guide.

### n8n
```bash
npm install n8n-nodes-LeForge
```

### Salesforce
1. Go to `salesforce/` folder
2. Import External Service spec or deploy Apex package
3. Configure Named Credential with API key
4. Use actions in Flow Builder

### ServiceNow
1. Go to `servicenow/` folder
2. Import the Update Set
3. Configure Connection Alias
4. Use LeForge actions in Flow Designer

## Generating Integrations

Run the generator script to create/update integrations from plugin definitions:

```bash
# Generate all integrations
python scripts/generate-integrations.py

# Generate for specific platform
python scripts/generate-integrations.py --platform power-automate

# Generate for specific plugin
python scripts/generate-integrations.py --plugin llm-service
```

## Supported Plugins

- **LLM Service** - AI chat, text generation, embeddings
- **Formula Engine** - 150+ Excel-compatible functions (VLOOKUP, SUMIF, etc.)
- **Streaming File Service** - Large file handling, chunked uploads, cloud storage
- **Crypto Service** - Encryption, hashing, JWT, signatures
- **Math Service** - Advanced calculations, statistics, matrix operations
- **Vector Service** - Vector database for semantic search and RAG
- **String Utils** - String manipulation (slugify, camelCase, sanitize)
- **Date Utils** - Date/time formatting, parsing, arithmetic

## Authentication

All integrations support:
- **API Key** (header: `X-API-Key`)
- **OAuth 2.0** (where platform supports)

## Documentation

| Guide | Description |
|-------|-------------|
| [Creating ForgeHooks](../docs/creating-forgehooks.md) | Build plugins + integrations |
| [Plugin-Integration Guide](../docs/PLUGIN-INTEGRATION-GUIDE.md) | Connect plugins to platforms |
| [Platform Proposal](../docs/PLATFORM-INTEGRATION-PROPOSAL.md) | Integration roadmap |
