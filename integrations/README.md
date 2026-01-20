# FlowForge Platform Integrations

This folder contains ready-to-use connectors and integration packages for various workflow automation and low-code platforms.

## Available Integrations

| Platform | Folder | Status | Format |
|----------|--------|--------|--------|
| **Power Automate** | `power-automate/` | 🚧 In Development | OpenAPI Custom Connector |
| **Nintex Workflow Cloud** | `nintex-cloud/` | 🚧 In Development | OpenAPI Xtension |
| **Nintex K2** | `nintex-k2/` | 🚧 In Development | Swagger + SmartObjects |
| **n8n** | `n8n/` | 🚧 In Development | TypeScript npm package |
| **Salesforce** | `salesforce/` | 📋 Planned | External Services + Apex |
| **ServiceNow** | `servicenow/` | 📋 Planned | IntegrationHub Spoke |
| **OutSystems** | `outsystems/` | 📋 Planned | Forge Component |
| **Mendix** | `mendix/` | 📋 Planned | Marketplace Module |

## Quick Start

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

### n8n
```bash
npm install n8n-nodes-flowforge
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
4. Use FlowForge actions in Flow Designer

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
- **Formula Engine** - 118 Excel-compatible functions
- **Streaming File Service** - Large file processing
- **Crypto Service** - Encryption, hashing, signatures

## Authentication

All integrations support:
- **API Key** (header: `X-API-Key`)
- **OAuth 2.0** (where platform supports)

## Documentation

See [PLATFORM-INTEGRATION-PROPOSAL.md](../docs/PLATFORM-INTEGRATION-PROPOSAL.md) for detailed integration strategy.
