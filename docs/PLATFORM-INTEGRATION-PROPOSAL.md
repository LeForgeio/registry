# LeForge Plugin Integration Proposal
## Making Plugins Easy to Use Across Low-Code/No-Code Platforms

This document outlines the strategy and deliverables needed to make LeForge plugins easily consumable by major workflow automation and low-code platforms.

---

## Executive Summary

Each platform has its own integration mechanism, but they share a common thread: **OpenAPI/Swagger specifications** are the universal language. Our strategy:

1. **Generate platform-optimized OpenAPI specs** from each plugin
2. **Create platform-specific packages** where OpenAPI isn't sufficient
3. **Provide ready-to-import connectors** for each platform

---

## Platform Integration Matrix

| Platform | Integration Type | Primary Format | Auth Support | Effort |
|----------|------------------|----------------|--------------|--------|
| **Nintex Workflow Cloud** | Xtensions | OpenAPI 2.0 (Swagger) | API Key, OAuth2, Basic | Low |
| **Nintex K2** | REST Service Broker + SmartObjects | Swagger 2.0 | API Key, OAuth, Static | Medium |
| **n8n** | Custom Nodes (TypeScript) | npm package | Credentials system | High |
| **Power Automate** | Custom Connectors | OpenAPI 2.0/3.0 | API Key, OAuth2 | Low |
| **OutSystems** | REST Integration + Forge Component | OpenAPI/WSDL | API Key, OAuth2 | Medium |
| **Mendix** | Marketplace Module | REST + Microflow Actions | API Key, OAuth2 | High |
| **Salesforce** | External Services + Flow Actions | OpenAPI 3.0 + Apex | OAuth 2.0, Named Credentials | Medium |
| **ServiceNow** | IntegrationHub Spokes + Flow Designer | REST API Actions | OAuth 2.0, API Key | Medium |

---

## 1. Nintex Workflow Cloud (Xtensions)

### What We Need to Create
**OpenAPI 2.0 Specification files** (one per plugin) with:
- Proper security definitions (API Key in header)
- Well-defined request/response schemas
- Action-oriented operation IDs
- Rich descriptions for UI generation

### Deliverables
```
/integrations/nintex-cloud/
├── llm-service.swagger.json
├── formula-engine.swagger.json
├── streaming-file-service.swagger.json
├── crypto-service.swagger.json
├── icons/
│   ├── llm-service.png (64x64)
│   ├── formula-engine.png
│   └── ...
└── README.md (installation guide)
```

### Implementation
```json
{
  "swagger": "2.0",
  "info": {
    "title": "LeForge LLM Service",
    "description": "AI-powered text generation, chat, and analysis",
    "version": "2.0.0"
  },
  "host": "{{your-domain}}/api/v1",
  "schemes": ["https"],
  "securityDefinitions": {
    "api_key": {
      "type": "apiKey",
      "in": "header",
      "name": "X-API-Key"
    }
  },
  "paths": {
    "/chat": {
      "post": {
        "operationId": "SendChatMessage",
        "summary": "Send a chat message and get AI response",
        "x-ntx-summary": "Chat with AI",
        // ... full endpoint definition
      }
    }
  }
}
```

### User Experience
1. Admin uploads `.swagger.json` to Nintex Xtensions
2. Configures API key connection
3. Actions appear in workflow designer
4. Drag-and-drop to use

---

## 2. Nintex K2 (SmartObjects + Service Broker)

### What We Need to Create
**Swagger files + SmartObject templates** for K2's REST Service Broker

### Deliverables
```
/integrations/nintex-k2/
├── swagger/
│   ├── llm-service.json
│   ├── formula-engine.json
│   └── ...
├── smartobject-templates/
│   ├── LLM_ChatCompletion.xml
│   ├── LLM_TextGeneration.xml
│   └── ...
└── deployment-guide.md
```

### Implementation Notes
- K2 requires Swagger 2.0 format
- SmartObjects provide the UI abstraction
- Service Broker connects REST to SmartObjects
- Support OAuth and API Key authentication

### Key Features for K2
- **SmartObject Methods**: Create, Read, Execute operations
- **Complex Object Handling**: Serialize/deserialize JSON properly
- **Form Integration**: SmartObjects can bind to K2 Forms

---

## 3. n8n (Custom Nodes)

### What We Need to Create
**TypeScript npm packages** following n8n node structure

### Deliverables
```
/integrations/n8n/
├── n8n-nodes-LeForge/
│   ├── package.json
│   ├── tsconfig.json
│   ├── nodes/
│   │   ├── LeForgeLLM/
│   │   │   ├── LeForgeLLM.node.ts
│   │   │   ├── LeForgeLLM.node.json
│   │   │   └── LeForge-llm.svg
│   │   ├── LeForgeFormula/
│   │   │   ├── LeForgeFormula.node.ts
│   │   │   └── ...
│   │   └── LeForgeFiles/
│   │       └── ...
│   ├── credentials/
│   │   └── LeForgeApi.credentials.ts
│   └── README.md
└── publish-guide.md
```

### Implementation Example
```typescript
// LeForgeLLM.node.ts
import {
  INodeType,
  INodeTypeDescription,
  IExecuteFunctions,
  INodeExecutionData,
} from 'n8n-workflow';

export class LeForgeLLM implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'LeForge LLM',
    name: 'LeForgeLlm',
    icon: 'file:LeForge-llm.svg',
    group: ['transform'],
    version: 1,
    subtitle: '={{$parameter["operation"]}}',
    description: 'AI text generation, chat, and analysis',
    defaults: {
      name: 'LeForge LLM',
    },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [
      {
        name: 'LeForgeApi',
        required: true,
      },
    ],
    properties: [
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        noDataExpression: true,
        options: [
          { name: 'Chat', value: 'chat' },
          { name: 'Generate Text', value: 'generate' },
          { name: 'Summarize', value: 'summarize' },
          { name: 'Classify', value: 'classify' },
          { name: 'Extract Entities', value: 'extract' },
        ],
        default: 'chat',
      },
      // ... more properties per operation
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    // Implementation
  }
}
```

### Distribution
- Publish to npm: `npm publish`
- Users install: `npm install n8n-nodes-LeForge`
- Or submit to n8n Community Nodes

---

## 4. Microsoft Power Automate

### What We Need to Create
**Custom Connector packages** (OpenAPI + icons + apiProperties.json)

### Deliverables
```
/integrations/power-automate/
├── LeForge-LLM/
│   ├── apiDefinition.swagger.json
│   ├── apiProperties.json
│   ├── icon.png (32x32)
│   └── README.md
├── LeForge-Formula/
│   └── ...
├── LeForge-Files/
│   └── ...
└── deployment-guide.md
```

### Implementation
```json
// apiProperties.json
{
  "properties": {
    "connectionParameters": {
      "api_key": {
        "type": "securestring",
        "uiDefinition": {
          "displayName": "API Key",
          "description": "LeForge API Key",
          "tooltip": "Provide your LeForge API Key",
          "constraints": {
            "required": "true"
          }
        }
      }
    },
    "iconBrandColor": "#6366f1",
    "capabilities": [],
    "policyTemplateInstances": []
  }
}
```

### Key Features for Power Automate
- **Triggers**: Webhook-based triggers for events
- **Actions**: All plugin operations as actions
- **Dynamic Schema**: Response schemas for downstream use
- **Pagination**: Handle large result sets

### Certification Path
1. Create and test custom connector
2. Submit for Microsoft certification
3. Appear in public connector gallery

---

## 5. OutSystems

### What We Need to Create
**Forge Components** (OutSystems modules) + REST API definitions

### Deliverables
```
/integrations/outsystems/
├── LeForge_LLM/
│   ├── LeForge_LLM.oml        # OutSystems Module
│   ├── documentation/
│   │   └── README.md
│   └── resources/
│       └── icon.png
├── LeForge_Formula/
│   └── ...
├── LeForge_Files/
│   └── ...
└── REST-API-Specs/
    ├── llm-service.json
    └── ...
```

### Implementation Approach
1. **Create Service Studio Module**
   - Define REST API consumption
   - Create Server Actions wrapping each endpoint
   - Build reusable UI blocks (optional)
   
2. **Expose as Forge Component**
   - Package module with documentation
   - Publish to OutSystems Forge

### Server Action Example
```
// In OutSystems Service Studio
ServerAction: LLM_Chat
  Input: 
    - Message (Text)
    - SystemPrompt (Text, optional)
    - MaxTokens (Integer, default=512)
  Output:
    - Response (Text)
    - Success (Boolean)
    - ErrorMessage (Text)
  
  Logic:
    1. Call REST API (POST /api/v1/chat)
    2. Parse JSON response
    3. Return results
```

---

## 6. Mendix

### What We Need to Create
**Mendix Marketplace Modules** with Java actions and microflow activities

### Deliverables
```
/integrations/mendix/
├── LeForgeLLM/
│   ├── module/
│   │   ├── LeForgeLLM.mpk
│   │   ├── javasource/
│   │   │   └── LeForge/
│   │   │       └── actions/
│   │   ├── microflows/
│   │   └── pages/ (optional demo pages)
│   ├── documentation/
│   │   └── README.md
│   └── test-app/
├── LeForgeFormula/
│   └── ...
└── LeForgeFiles/
    └── ...
```

### Implementation Approach
1. **REST API Integration**
   - Use Mendix's Consume REST Service feature
   - Map endpoints to domain model
   
2. **Java Actions** (for complex operations)
   ```java
   // Chat.java
   public class Chat extends CustomJavaAction<String> {
       private String message;
       private String systemPrompt;
       
       @Override
       public String executeAction() throws Exception {
           // Call LeForge API
           return response;
       }
   }
   ```

3. **Microflow Activities**
   - Expose Java actions as toolbox items
   - Create helper microflows for common patterns

### Distribution
- Export as .mpk module
- Publish to Mendix Marketplace
- Users import directly into Studio Pro

---

## 7. Salesforce (External Services + Flow Actions)

### What We Need to Create
**External Services definitions** (OpenAPI 3.0) + **Apex wrapper classes** + **Flow-compatible invocable actions**

### Deliverables
```
/integrations/salesforce/
├── external-services/
│   ├── LeForge_LLM.yaml           # OpenAPI 3.0 spec
│   ├── LeForge_Formula.yaml
│   ├── LeForge_Files.yaml
│   └── LeForge_Crypto.yaml
├── apex/
│   ├── classes/
│   │   ├── LeForgeLLMService.cls
│   │   ├── LeForgeLLMService.cls-meta.xml
│   │   ├── LeForgeFormulaService.cls
│   │   ├── LeForgeCryptoService.cls
│   │   └── LeForgeFileService.cls
│   ├── namedCredentials/
│   │   └── LeForge_API.namedCredential-meta.xml
│   └── externalServiceRegistrations/
│       └── LeForge_LLM.externalServiceRegistration-meta.xml
├── package/
│   └── package.xml                  # Deployable metadata package
└── README.md
```

### Implementation Approach

#### Option A: External Services (Recommended for simplicity)
Salesforce can consume OpenAPI 3.0 specs directly via External Services:

```yaml
# LeForge_LLM.yaml (OpenAPI 3.0 for Salesforce)
openapi: "3.0.0"
info:
  title: LeForge LLM Service
  version: "2.0.0"
servers:
  - url: https://your-LeForge-instance.com/api/v1
paths:
  /chat:
    post:
      operationId: sendChatMessage
      summary: Send a chat message and get AI response
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                system_prompt:
                  type: string
                max_tokens:
                  type: integer
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  response:
                    type: string
                  tokens_used:
                    type: integer
```

#### Option B: Apex Invocable Actions (For complex logic)
```java
// LeForgeLLMService.cls
public class LeForgeLLMService {
    
    @InvocableMethod(label='Chat with AI' description='Send a message to LeForge LLM and get a response' category='LeForge')
    public static List<ChatResponse> chat(List<ChatRequest> requests) {
        List<ChatResponse> responses = new List<ChatResponse>();
        
        for (ChatRequest req : requests) {
            HttpRequest httpReq = new HttpRequest();
            httpReq.setEndpoint('callout:LeForge_API/chat');
            httpReq.setMethod('POST');
            httpReq.setHeader('Content-Type', 'application/json');
            httpReq.setBody(JSON.serialize(new Map<String, Object>{
                'message' => req.message,
                'system_prompt' => req.systemPrompt,
                'max_tokens' => req.maxTokens
            }));
            
            Http http = new Http();
            HttpResponse httpRes = http.send(httpReq);
            
            ChatResponse res = new ChatResponse();
            if (httpRes.getStatusCode() == 200) {
                Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(httpRes.getBody());
                res.response = (String) body.get('response');
                res.tokensUsed = (Integer) body.get('tokens_used');
                res.success = true;
            } else {
                res.success = false;
                res.errorMessage = httpRes.getBody();
            }
            responses.add(res);
        }
        return responses;
    }
    
    public class ChatRequest {
        @InvocableVariable(label='Message' required=true)
        public String message;
        
        @InvocableVariable(label='System Prompt')
        public String systemPrompt;
        
        @InvocableVariable(label='Max Tokens')
        public Integer maxTokens;
    }
    
    public class ChatResponse {
        @InvocableVariable(label='AI Response')
        public String response;
        
        @InvocableVariable(label='Tokens Used')
        public Integer tokensUsed;
        
        @InvocableVariable(label='Success')
        public Boolean success;
        
        @InvocableVariable(label='Error Message')
        public String errorMessage;
    }
}
```

### Named Credential Setup
```xml
<!-- LeForge_API.namedCredential-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>LeForge_API</fullName>
    <label>LeForge API</label>
    <endpoint>https://your-LeForge-instance.com/api/v1</endpoint>
    <principalType>NamedUser</principalType>
    <protocol>Custom</protocol>
    <customHeaders>
        <name>X-API-Key</name>
        <value>{!$Credential.LeForge_API.ApiKey}</value>
    </customHeaders>
</NamedCredential>
```

### User Experience in Salesforce Flow
1. Admin imports External Service or deploys Apex package
2. Configure Named Credential with API endpoint and key
3. Actions appear in Flow Builder under "LeForge" category
4. Drag actions into Screen Flows, Record-Triggered Flows, etc.

### Key Features for Salesforce
- **Flow Builder Integration**: Native actions in Flow Builder
- **Apex Callouts**: For complex integrations or triggers
- **Named Credentials**: Secure credential management
- **Platform Events**: Potential for async/streaming patterns
- **AppExchange**: Distribution via managed package

---

## 8. ServiceNow (IntegrationHub Spokes + Flow Designer)

### What We Need to Create
**IntegrationHub Spoke** with Flow Designer actions + REST message configurations

### Deliverables
```
/integrations/servicenow/
├── spoke/
│   ├── LeForge_Spoke/
│   │   ├── sys_hub_spoke.xml
│   │   ├── actions/
│   │   │   ├── llm_chat.xml
│   │   │   ├── llm_generate.xml
│   │   │   ├── llm_summarize.xml
│   │   │   ├── formula_evaluate.xml
│   │   │   ├── crypto_encrypt.xml
│   │   │   ├── crypto_decrypt.xml
│   │   │   └── file_upload.xml
│   │   ├── connection_alias/
│   │   │   └── LeForge_connection.xml
│   │   └── rest_messages/
│   │       ├── LeForge_LLM.xml
│   │       ├── LeForge_Formula.xml
│   │       └── LeForge_Crypto.xml
│   └── update_set.xml               # Deployable update set
├── scripted-rest/
│   └── LeForgeWebhook.js          # For async callbacks
├── documentation/
│   └── installation-guide.md
└── README.md
```

### Implementation Approach

#### IntegrationHub Spoke Structure
```javascript
// Spoke Action: LLM Chat
// sys_hub_action_type_definition
{
    "name": "LeForge LLM Chat",
    "description": "Send a message to LeForge AI and get a response",
    "category": "LeForge",
    "access": "public",
    "inputs": [
        {
            "name": "message",
            "label": "Message",
            "type": "string",
            "mandatory": true
        },
        {
            "name": "system_prompt", 
            "label": "System Prompt",
            "type": "string",
            "mandatory": false
        },
        {
            "name": "max_tokens",
            "label": "Max Tokens",
            "type": "integer",
            "default": 512
        }
    ],
    "outputs": [
        {
            "name": "response",
            "label": "AI Response",
            "type": "string"
        },
        {
            "name": "tokens_used",
            "label": "Tokens Used", 
            "type": "integer"
        },
        {
            "name": "success",
            "label": "Success",
            "type": "boolean"
        }
    ]
}
```

#### REST Message Configuration
```xml
<!-- LeForge_LLM REST Message -->
<REST_Message>
    <name>LeForge_LLM</name>
    <rest_endpoint>https://your-LeForge-instance.com/api/v1</rest_endpoint>
    <authentication_type>basic</authentication_type>
    
    <HTTP_Methods>
        <method name="chat" http_method="POST">
            <endpoint>/chat</endpoint>
            <headers>
                <header name="Content-Type">application/json</header>
                <header name="X-API-Key">${api_key}</header>
            </headers>
            <content>${request_body}</content>
        </method>
        
        <method name="generate" http_method="POST">
            <endpoint>/generate</endpoint>
            <headers>
                <header name="Content-Type">application/json</header>
                <header name="X-API-Key">${api_key}</header>
            </headers>
            <content>${request_body}</content>
        </method>
    </HTTP_Methods>
</REST_Message>
```

#### Action Script Implementation
```javascript
// Action Script for LLM Chat
(function execute(inputs, outputs) {
    var restMessage = new sn_ws.RESTMessageV2('LeForge_LLM', 'chat');
    
    // Get connection alias credentials
    var connectionAlias = inputs.connection_alias || 'LeForge_connection';
    restMessage.setStringParameterNoEscape('api_key', getApiKey(connectionAlias));
    
    // Build request body
    var requestBody = {
        message: inputs.message,
        system_prompt: inputs.system_prompt || '',
        max_tokens: inputs.max_tokens || 512
    };
    restMessage.setRequestBody(JSON.stringify(requestBody));
    
    var response = restMessage.execute();
    var httpStatus = response.getStatusCode();
    var responseBody = response.getBody();
    
    if (httpStatus == 200) {
        var result = JSON.parse(responseBody);
        outputs.response = result.response;
        outputs.tokens_used = result.tokens_used;
        outputs.success = true;
    } else {
        outputs.success = false;
        outputs.error_message = responseBody;
    }
    
})(inputs, outputs);

function getApiKey(aliasName) {
    var gr = new GlideRecord('sys_alias');
    gr.addQuery('name', aliasName);
    gr.query();
    if (gr.next()) {
        return gr.getValue('api_key');
    }
    return '';
}
```

### Connection Alias for Credentials
```xml
<!-- LeForge_connection alias -->
<sys_alias>
    <name>LeForge_connection</name>
    <type>connection</type>
    <configuration>
        <endpoint>https://your-LeForge-instance.com/api/v1</endpoint>
        <auth_type>api_key</auth_type>
        <api_key_header>X-API-Key</api_key_header>
    </configuration>
</sys_alias>
```

### User Experience in ServiceNow
1. Import Update Set containing the LeForge Spoke
2. Configure Connection Alias with API endpoint and credentials
3. LeForge actions appear in Flow Designer
4. Build flows using drag-and-drop actions
5. Use in Service Catalog, Incident Management, HR workflows, etc.

### Key Features for ServiceNow
- **Flow Designer**: Native low-code flow building
- **IntegrationHub**: Enterprise integration platform
- **Connection Aliases**: Secure, reusable credentials
- **Subflows**: Reusable action sequences
- **Service Catalog**: Self-service automation
- **Virtual Agent**: AI chatbot integration potential

### Use Cases in ServiceNow
| Use Case | LeForge Service | ServiceNow Application |
|----------|-------------------|------------------------|
| Auto-classify incidents | LLM Service | ITSM |
| Generate KB articles | LLM Service | Knowledge Management |
| Encrypt sensitive data | Crypto Service | Security Operations |
| Calculate SLA metrics | Formula Engine | Service Level Management |
| Process attachments | File Service | Any module with attachments |

### OpenAPI Generator Script
Create a script to generate platform-specific OpenAPI files from our base specs:

```python
# scripts/generate-openapi.py
"""
Generate platform-optimized OpenAPI specifications from forgehook.json
"""

def generate_nintex_swagger(plugin_path, output_path):
    """Generate Nintex-compatible Swagger 2.0"""
    pass

def generate_power_automate_connector(plugin_path, output_path):
    """Generate Power Automate connector package"""
    pass

def generate_n8n_node_skeleton(plugin_path, output_path):
    """Generate n8n node TypeScript skeleton"""
    pass
```

### Common Features to Expose

For each plugin, expose these as actions/operations:

#### LLM Service
| Action | Description |
|--------|-------------|
| Chat | Send message, get AI response |
| Generate Text | Complete/generate text |
| Summarize | Summarize documents |
| Classify | Categorize text |
| Extract Entities | Extract structured data |
| Generate Embeddings | Create vector embeddings |

#### Formula Engine
| Action | Description |
|--------|-------------|
| Evaluate Formula | Calculate Excel formula |
| Batch Calculate | Process multiple formulas |
| Validate Formula | Check formula syntax |
| List Functions | Get available functions |

#### Streaming File Service
| Action | Description |
|--------|-------------|
| Upload File | Upload large files |
| Download File | Stream download |
| Process CSV | Parse/transform CSV |
| Process Excel | Read/write Excel |
| Convert Format | Convert between formats |

#### Crypto Service
| Action | Description |
|--------|-------------|
| Encrypt Data | Encrypt with AES/RSA |
| Decrypt Data | Decrypt data |
| Hash Data | Generate hash (SHA256, etc.) |
| Sign Data | Create digital signature |
| Verify Signature | Verify digital signature |
| Generate Keys | Create key pairs |

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [x] Create OpenAPI 2.0 specs for all plugins
- [x] Create OpenAPI 3.0 specs for all plugins
- [x] Build OpenAPI generator script
- [ ] Create icons/branding for each plugin

### Phase 2: Microsoft & Nintex (Week 3-4)
- [x] Power Automate custom connectors (4 plugins)
- [x] Nintex Workflow Cloud Xtensions (4 plugins)
- [x] Nintex K2 Swagger + SmartObject templates
- [ ] Testing and documentation

### Phase 3: n8n (Week 5-6)
- [x] n8n node package structure
- [x] Implement all nodes with credentials
- [ ] Test with n8n self-hosted
- [ ] Publish to npm
- [ ] Submit to n8n Community Nodes

### Phase 4: Low-Code Platforms (Week 7-8)
- [ ] OutSystems Forge components
- [ ] Mendix Marketplace modules
- [ ] Integration testing
- [ ] Documentation and examples

### Phase 5: Enterprise Platforms (Week 9-10)
- [ ] Salesforce External Services + Apex package
- [ ] ServiceNow IntegrationHub Spoke
- [ ] Named Credentials / Connection Alias setup
- [ ] Testing in sandbox environments

### Phase 6: Certification & Publishing (Week 11-12)
- [ ] Power Automate connector certification
- [ ] Salesforce AppExchange listing
- [ ] ServiceNow Store submission
- [ ] OutSystems Forge publishing
- [ ] Mendix Marketplace publishing
- [ ] Marketing materials

---

## Recommended Priority

Based on market reach and implementation effort:

1. **Power Automate** - Largest user base, easy OpenAPI import ✅ In Progress
2. **Nintex Workflow Cloud** - Direct competitor, OpenAPI-based ✅ In Progress
3. **n8n** - Growing open-source community, good visibility ✅ In Progress
4. **Salesforce** - Massive enterprise market, Flow Builder adoption 🆕
5. **ServiceNow** - Enterprise ITSM leader, IntegrationHub growing 🆕
6. **OutSystems** - Enterprise low-code, REST-friendly
7. **Nintex K2** - Legacy but still used, more complex ✅ In Progress
8. **Mendix** - Requires most custom work

---

## 9. Integration Asset Distribution

### Strategy: Registry API Endpoint

Rather than bundling integration assets or requiring manual downloads, the LeForge Registry exposes an API endpoint that generates and serves platform-specific integration packages on-demand.

### API Design

```
GET /api/v1/plugins/{plugin}/integrations/{platform}
GET /api/v1/plugins/{plugin}/integrations/{platform}/{asset}
```

#### Endpoints

| Endpoint | Description | Response |
|----------|-------------|----------|
| `GET /plugins/llm-service/integrations` | List available platforms | JSON array of platforms |
| `GET /plugins/llm-service/integrations/nintex-cloud` | Get Nintex Cloud package | ZIP with swagger + readme |
| `GET /plugins/llm-service/integrations/nintex-cloud/swagger.json` | Swagger file only | JSON |
| `GET /plugins/llm-service/integrations/nintex-k2` | Get K2 package | ZIP with swagger + SmartObjects |
| `GET /plugins/llm-service/integrations/salesforce` | Salesforce package | ZIP with OpenAPI + Apex classes |
| `GET /plugins/llm-service/integrations/servicenow` | ServiceNow spoke | ZIP with spoke XML + scripts |

#### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `baseUrl` | Override default API base URL | `?baseUrl=https://api.mycompany.com` |
| `version` | Plugin version (default: latest) | `?version=2.1.0` |
| `format` | Response format: `zip`, `json`, `yaml` | `?format=json` |
| `auth` | Auth type hint for spec | `?auth=oauth2` |

### Example Requests

```bash
# Download Nintex Cloud Xtension package
curl -o llm-service-nintex.zip \
  "https://registry.LeForge.io/api/v1/plugins/llm-service/integrations/nintex-cloud?baseUrl=https://LeForge.mycompany.com"

# Get just the Swagger file
curl "https://registry.LeForge.io/api/v1/plugins/llm-service/integrations/nintex-cloud/swagger.json"

# Download K2 SmartObject templates
curl -o llm-service-k2.zip \
  "https://registry.LeForge.io/api/v1/plugins/llm-service/integrations/nintex-k2"

# Get Salesforce Apex classes
curl -o llm-salesforce.zip \
  "https://registry.LeForge.io/api/v1/plugins/llm-service/integrations/salesforce"
```

### Response Structure

#### List Integrations
```json
{
  "plugin": "llm-service",
  "version": "2.0.0",
  "integrations": [
    {
      "platform": "nintex-cloud",
      "name": "Nintex Workflow Cloud",
      "format": "OpenAPI 2.0 (Swagger)",
      "assets": ["swagger.json", "icon.png", "README.md"]
    },
    {
      "platform": "nintex-k2",
      "name": "Nintex K2",
      "format": "Swagger 2.0 + SmartObjects",
      "assets": ["swagger.json", "smartobjects/", "README.md"]
    },
    {
      "platform": "salesforce",
      "name": "Salesforce",
      "format": "OpenAPI 3.0 + Apex",
      "assets": ["openapi.yaml", "apex/", "package.xml", "README.md"]
    },
    {
      "platform": "servicenow",
      "name": "ServiceNow",
      "format": "IntegrationHub Spoke",
      "assets": ["spoke/", "rest_messages/", "README.md"]
    },
    {
      "platform": "power-automate",
      "name": "Power Automate",
      "format": "Custom Connector",
      "assets": ["apiDefinition.swagger.json", "apiProperties.json", "icon.png"]
    }
  ]
}
```

#### ZIP Package Contents

**Nintex Cloud (`nintex-cloud.zip`):**
```
llm-service-nintex-cloud/
├── llm-service.swagger.json
├── icon.png
├── README.md
└── INSTALLATION.md
```

**Nintex K2 (`nintex-k2.zip`):**
```
llm-service-k2/
├── swagger/
│   └── llm-service.swagger.json
├── smartobjects/
│   ├── LlmChat.xml
│   ├── LlmClassify.xml
│   └── LlmSummarize.xml
├── README.md
└── INSTALLATION.md
```

**Salesforce (`salesforce.zip`):**
```
llm-service-salesforce/
├── external-services/
│   └── LeForge_LLM.yaml
├── apex/
│   ├── classes/
│   │   ├── LeForgeLLMService.cls
│   │   └── LeForgeLLMService.cls-meta.xml
│   └── namedCredentials/
│       └── LeForge_API.namedCredential-meta.xml
├── package.xml
├── README.md
└── INSTALLATION.md
```

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LeForge Registry                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GET /plugins/{plugin}/integrations/{platform}               │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────┐               │
│  │         Integration Generator            │               │
│  │                                          │               │
│  │  1. Load forgehook.json                  │               │
│  │  2. Apply baseUrl override               │               │
│  │  3. Generate platform-specific assets    │               │
│  │  4. Package as ZIP or return single file │               │
│  └──────────────────────────────────────────┘               │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────┐               │
│  │              Asset Cache                  │               │
│  │  (Redis/filesystem, 1hr TTL)             │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### CLI Integration

The `LeForge` CLI can also fetch integration assets:

```bash
# Download integration package
LeForge integrations download llm-service --platform nintex-cloud --output ./

# List available integrations
LeForge integrations list llm-service

# Generate with custom base URL
LeForge integrations download crypto-service --platform salesforce \
  --base-url https://LeForge.mycompany.com
```

### Air-Gapped / Offline Distribution

For environments without internet access (air-gapped networks), integration assets are available through multiple offline channels:

#### Option 1: Bundled in Plugin Docker Images

Each plugin Docker image includes pre-generated integration assets at `/integrations/`:

```
/integrations/
├── nintex-cloud/
│   ├── swagger.json
│   ├── icon.png
│   └── README.md
├── nintex-k2/
│   ├── swagger.json
│   ├── smartobjects/
│   └── README.md
├── salesforce/
│   ├── openapi.yaml
│   ├── apex/
│   └── README.md
├── servicenow/
│   ├── spoke/
│   └── README.md
└── power-automate/
    ├── apiDefinition.swagger.json
    └── apiProperties.json
```

**Extract from running container:**
```bash
# Copy integration assets from running container
docker cp LeForge-llm-service:/integrations ./llm-service-integrations

# Or from image directly
docker run --rm -v $(pwd)/output:/out LeForge/llm-service:2.0.0 \
  cp -r /integrations /out/
```

**Air-Gapped K2 5.9 Workflow:**
```bash
# 1. On internet-connected machine, pull and save image
docker pull LeForge/llm-service:2.0.0
docker save LeForge/llm-service:2.0.0 -o llm-service.tar

# 2. Transfer llm-service.tar to air-gapped network (USB, etc.)

# 3. On air-gapped network, load image
docker load -i llm-service.tar

# 4. Extract K2 integration assets
docker run --rm -v /path/to/output:/out LeForge/llm-service:2.0.0 \
  cp -r /integrations/nintex-k2 /out/

# 5. Import swagger.json into K2 REST Service Broker
# 6. Import SmartObjects from smartobjects/ folder
```

#### Option 2: GitHub Release Artifacts

Each LeForge release includes downloadable integration bundles:

```
LeForge-v2.0.0-integrations.zip
├── llm-service/
│   ├── nintex-cloud.zip
│   ├── nintex-k2.zip
│   ├── salesforce.zip
│   ├── servicenow.zip
│   └── power-automate.zip
├── crypto-service/
│   └── ...
├── formula-engine/
│   └── ...
└── streaming-file-service/
    └── ...
```

Download once, transfer to air-gapped network, extract as needed.

#### Option 3: LeForge Installer Bundle

The enterprise LeForge installer includes all integration assets:

```
LeForge-enterprise-2.0.0/
├── docker-compose.yml
├── images/
│   ├── llm-service.tar
│   ├── crypto-service.tar
│   └── ...
├── integrations/           # Pre-extracted for convenience
│   ├── nintex-cloud/
│   ├── nintex-k2/
│   ├── salesforce/
│   └── ...
└── docs/
    └── air-gapped-install.md
```

#### Air-Gapped Customization

Since air-gapped assets are pre-generated, the `baseUrl` needs manual editing:

**Swagger files (Nintex Cloud/K2):**
```json
{
  "host": "LeForge.internal.company.com",
  "basePath": "/api/v1",
  "schemes": ["https"]
}
```

**Salesforce Named Credential:**
Edit `LeForge_API.namedCredential-meta.xml`:
```xml
<endpoint>https://LeForge.internal.company.com</endpoint>
```

**ServiceNow Connection Alias:**
Update `connection_alias.xml` or configure in ServiceNow UI after import.

#### Build-Time Integration Generation

For CI/CD pipelines in air-gapped environments, run the generator during build:

```bash
# In your build pipeline (before air-gap)
python scripts/generate-integrations.py \
  --plugin llm-service \
  --platform nintex-k2 \
  --base-url https://LeForge.internal.corp \
  --output ./release/integrations/

# Bundle output with your deployment artifacts
```

### Customer Workflow

#### Nintex Workflow Cloud
1. **Admin** visits LeForge registry or uses CLI
2. Downloads `llm-service-nintex-cloud.zip`
3. Extracts and uploads `swagger.json` to Nintex Xtensions
4. Configures API key
5. Actions available in workflow designer

#### Nintex K2 5.9 (Connected)
1. **Admin** downloads `llm-service-k2.zip`
2. Imports swagger via K2 REST Service Broker
3. Imports SmartObject templates from `smartobjects/`
4. Configures service instance with API key
5. SmartObjects available in K2 Designer

#### Nintex K2 5.9 (Air-Gapped)
1. **Admin** extracts assets from Docker image or installer bundle
2. Edits `swagger.json` to set internal `host` URL
3. Imports swagger via K2 REST Service Broker
4. Imports SmartObject templates from `smartobjects/`
5. Configures service instance with API key
6. SmartObjects available in K2 Designer

#### Salesforce
1. **Admin** downloads `llm-service-salesforce.zip`
2. Deploys via Salesforce CLI: `sf project deploy start --source-dir llm-service-salesforce/`
3. Configures Named Credential with OAuth/API key
4. Invocable Actions appear in Flow Builder

#### ServiceNow
1. **Admin** downloads `llm-service-servicenow.zip`
2. Imports spoke via Update Set or Studio
3. Configures Connection Alias
4. Actions available in Flow Designer

---

## Next Steps

1. **Approve this proposal** and prioritize platforms
2. **Set up integration folder structure** in repository
3. **Begin with OpenAPI generation** (foundation for most platforms)
4. **Create first Power Automate connector** as proof of concept
5. **Implement registry API endpoint** for asset distribution
6. **Iterate based on feedback**

---

## Questions to Resolve

1. Will plugins be self-hosted or SaaS? (Affects connector URLs)
2. What authentication method is preferred? (API Key recommended)
3. Do we want certified/published connectors or private only?
4. What's the branding/naming convention? (LeForge vs custom?)
5. ~~How do customers get integration assets?~~ ✅ Registry API endpoint
