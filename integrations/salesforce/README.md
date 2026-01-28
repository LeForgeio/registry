# LeForge Salesforce Integration

Salesforce integration for LeForge services using External Services and Apex Invocable Actions.

## Services

| Service | External Service | Apex Class | Flow Actions |
|---------|------------------|------------|--------------|
| LLM Service | ✅ | ✅ | Chat, Generate, Summarize, Classify |
| Formula Engine | ✅ | ✅ | Evaluate, BatchCalculate, Validate |
| Crypto Service | ✅ | ✅ | Encrypt, Decrypt, Hash, Sign, Verify |
| Streaming File Service | ✅ | ✅ | Upload, Download, Process |

## Installation

### Option 1: External Services (Recommended)
1. Go to **Setup > External Services**
2. Click **Add an External Service**
3. Upload the OpenAPI spec from `external-services/` folder
4. Configure Named Credential for authentication
5. Actions automatically appear in Flow Builder

### Option 2: Apex Package Deployment
```bash
# Using Salesforce CLI
sfdx force:source:deploy -p integrations/salesforce/apex
```

## Authentication Setup

### Named Credential
1. Go to **Setup > Named Credentials**
2. Create new credential:
   - **Label**: LeForge API
   - **URL**: `https://your-LeForge-instance.com/api/v1`
   - **Authentication**: Custom Header
   - **Header Name**: `X-API-Key`
   - **Header Value**: Your API key

## Usage in Flow Builder

1. Open **Flow Builder**
2. Add an **Action** element
3. Search for "LeForge"
4. Select desired action (e.g., "Chat with AI")
5. Map input/output variables

## Folder Structure

```
salesforce/
├── external-services/          # OpenAPI 3.0 specs for External Services
│   ├── LeForge_LLM.yaml
│   ├── LeForge_Formula.yaml
│   ├── LeForge_Crypto.yaml
│   └── LeForge_Files.yaml
├── apex/
│   ├── classes/                # Invocable Apex classes
│   └── namedCredentials/       # Credential metadata
├── package/
│   └── package.xml             # Deployment manifest
└── README.md
```

## Requirements

- Salesforce Enterprise Edition or higher
- External Services enabled
- API access for callouts
- Named Credentials permission

## Support

See [PLATFORM-INTEGRATION-PROPOSAL.md](../../docs/PLATFORM-INTEGRATION-PROPOSAL.md) for detailed documentation.
