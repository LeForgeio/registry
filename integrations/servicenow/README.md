# LeForge ServiceNow Integration

ServiceNow IntegrationHub Spoke for LeForge services, enabling AI and automation capabilities in Flow Designer.

## Services

| Service | Spoke Actions | Use Cases |
|---------|---------------|-----------|
| LLM Service | Chat, Generate, Summarize, Classify, Extract | Incident classification, KB generation, Virtual Agent |
| Formula Engine | Evaluate, BatchCalculate, Validate | SLA calculations, metrics, reporting |
| Crypto Service | Encrypt, Decrypt, Hash, Sign, Verify | Security Operations, data protection |
| Streaming File Service | Upload, Download, Process | Attachment processing, data import |

## Installation

### Import Update Set
1. Navigate to **System Update Sets > Retrieved Update Sets**
2. Click **Import Update Set from XML**
3. Upload `spoke/update_set.xml`
4. Preview and commit the update set

### Configure Connection
1. Go to **Connections & Credentials > Connection & Credential Aliases**
2. Find **LeForge Connection**
3. Create new connection:
   - **Name**: LeForge Production
   - **Endpoint**: `https://your-LeForge-instance.com/api/v1`
   - **API Key**: Your LeForge API key

## Usage in Flow Designer

1. Open **Flow Designer**
2. Add an **Action**
3. Search for "LeForge"
4. Select desired action (e.g., "LLM Chat")
5. Configure inputs and map outputs
6. Activate flow

## Folder Structure

```
servicenow/
├── spoke/
│   ├── LeForge_Spoke/
│   │   ├── sys_hub_spoke.xml
│   │   ├── actions/              # Flow Designer actions
│   │   ├── connection_alias/     # Credential configuration
│   │   └── rest_messages/        # REST API definitions
│   └── update_set.xml            # Deployable package
├── scripted-rest/                # Webhook handlers (optional)
├── documentation/
│   └── installation-guide.md
└── README.md
```

## Example Use Cases

### Auto-Classify Incidents
```
Trigger: Incident Created
Action: LeForge LLM Classify
  - Input: incident.short_description + incident.description
  - Categories: Hardware, Software, Network, Access
Update: incident.category = classification_result
```

### Generate Knowledge Articles
```
Trigger: Incident Resolved (major incident)
Action: LeForge LLM Generate
  - Input: incident details + resolution notes
  - Template: KB Article format
Create: Knowledge article from generated content
```

### Encrypt Sensitive Fields
```
Trigger: Before Insert (sensitive record)
Action: LeForge Crypto Encrypt
  - Input: sensitive_field_value
Update: encrypted_field = encrypted_result
```

## Requirements

- ServiceNow Rome or later
- IntegrationHub subscription (Standard or Professional)
- Flow Designer access
- Outbound REST enabled

## Support

See [PLATFORM-INTEGRATION-PROPOSAL.md](../../docs/PLATFORM-INTEGRATION-PROPOSAL.md) for detailed documentation.
