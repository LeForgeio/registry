# FlowForge ServiceNow Installation Guide

## Prerequisites

- ServiceNow Rome release or later
- IntegrationHub subscription (Standard or Professional)
- Flow Designer access
- Outbound REST enabled

## Installation Steps

### Step 1: Import the Update Set

1. Navigate to **System Update Sets > Retrieved Update Sets**
2. Click **Import Update Set from XML**
3. Upload `update_set.xml` from the spoke folder
4. Click **Preview Update Set**
5. Review any conflicts and resolve if needed
6. Click **Commit Update Set**

### Step 2: Configure Connection Alias

1. Navigate to **Connections & Credentials > Connection & Credential Aliases**
2. Find **FlowForge Connection** (created by update set)
3. Click **New Connection** and fill in:

   | Field | Value |
   |-------|-------|
   | Name | FlowForge Production |
   | Connection URL | `https://your-flowforge-instance.com/api/v1` |
   
4. Add credential:
   - **Credential Type**: API Key
   - **API Key Header**: `X-API-Key`
   - **API Key Value**: Your FlowForge API key

5. Test the connection

### Step 3: Verify Spoke Installation

1. Navigate to **Flow Designer**
2. Create a new flow
3. Add an **Action**
4. Search for "FlowForge"
5. You should see the following actions:
   - Chat with AI
   - Classify Text
   - Summarize Text
   - Encrypt Data
   - Evaluate Formula

## Available Actions

### LLM Service

| Action | Description | Use Cases |
|--------|-------------|-----------|
| **Chat with AI** | Send messages and get AI responses | Virtual Agent, automated replies |
| **Classify Text** | Categorize text into predefined categories | Incident routing, ticket triage |
| **Summarize Text** | Generate concise summaries | KB article creation, report summaries |
| **Generate Text** | Complete prompts with AI | Email drafting, content generation |
| **Extract Entities** | Find people, orgs, dates in text | Data extraction, contact parsing |

### Crypto Service

| Action | Description | Use Cases |
|--------|-------------|-----------|
| **Encrypt Data** | AES encrypt sensitive data | PII protection, credential storage |
| **Decrypt Data** | Decrypt encrypted data | Retrieve protected information |
| **Hash Data** | Generate SHA256/MD5 hashes | Data integrity, checksums |
| **Generate Key** | Create random encryption keys | Key management |

### Formula Engine

| Action | Description | Use Cases |
|--------|-------------|-----------|
| **Evaluate Formula** | Run Excel-compatible formulas | SLA calculations, pricing |
| **Batch Evaluate** | Process multiple formulas | Bulk calculations |
| **Validate Formula** | Check formula syntax | Input validation |

## Example Flows

### Auto-Classify Incidents

```
Trigger: Record Created (Incident)
    ↓
Action: FlowForge Classify Text
  - Text: [Incident Short Description] + " " + [Incident Description]
  - Categories: "Hardware,Software,Network,Access,Other"
    ↓
Update Record: Incident
  - Category = [Classify Text.Category]
  - [Add work note with confidence score]
```

### Generate KB Article Summary

```
Trigger: Record Updated (Knowledge Article)
  - Condition: workflow_state = "Review"
    ↓
Action: FlowForge Summarize Text
  - Text: [Article Text]
  - Style: "bullet"
  - Max Length: 200
    ↓
Update Record: Knowledge Article
  - Short Description = [Summarize Text.Summary]
```

### Encrypt Sensitive Field

```
Subflow: Encrypt PII Data
  Input: sensitive_data (String)
  Input: encryption_key (String)
    ↓
Action: FlowForge Encrypt Data
  - Data: [sensitive_data]
  - Encryption Key: [encryption_key]
    ↓
Output: encrypted_data = [Encrypt Data.Encrypted]
Output: iv = [Encrypt Data.IV]
Output: tag = [Encrypt Data.Tag]
```

## Troubleshooting

### Connection Issues

1. **401 Unauthorized**: Check API key is correct in Connection Alias
2. **Connection timeout**: Verify FlowForge instance is accessible from ServiceNow
3. **SSL errors**: Ensure FlowForge uses valid SSL certificate

### Action Failures

1. Check Flow Designer execution details for error messages
2. Review System Logs for REST errors
3. Verify input data doesn't exceed size limits

### Performance

- LLM actions may take 10-30 seconds for long texts
- Use appropriate timeout settings in flows
- Consider async patterns for batch operations

## Support

- Documentation: [PLATFORM-INTEGRATION-PROPOSAL.md](../../docs/PLATFORM-INTEGRATION-PROPOSAL.md)
- Issues: Contact FlowForge support
