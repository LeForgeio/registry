# LeForge llm-service - OutSystems Integration

## Overview
LeForge plugin integration for OutSystems.

## Integration Methods

### Method 1: Consume REST API (Recommended)

1. Open **Service Studio**
2. Go to **Logic** > **Integrations** > **REST**
3. Right-click and select **Consume REST API**
4. Choose **Add Single Method** or **Add Multiple Methods**
5. Paste endpoints from the OpenAPI spec

### Method 2: Import OpenAPI Spec

1. Open **Integration Studio**
2. Create new extension
3. Import `llm-service-openapi.json`
4. Publish extension

## Configuration

### Base URL
Set the base URL to your LeForge instance in the REST API configuration.

### Authentication
1. Create a Site Property for the API Key
2. Add `X-API-Key` header to all REST calls
3. Use the Site Property value

## Server Actions

For each operation, create a Server Action wrapper:

```
ServerAction: LeForge_llm-service_Operation
    Input: 
        - RequestData (Structure)
    Output:
        - ResponseData (Structure)
        - Success (Boolean)
        - ErrorMessage (Text)
    
    Logic:
        1. Call REST API
        2. Handle response/errors
        3. Return results
```

## Available Operations

| Unknown | List available LLM providers |
| Unknown | Configure a provider with API credentials |
| Unknown | List available models for a provider |
| Unknown | Check provider health status |
| Unknown | Chat with a specific provider |
| Unknown | Generate embeddings with a specific provider |
| Unknown | Universal chat endpoint with provider selection |
| Unknown | Chat completion (vLLM/default provider) |
| Unknown | Simple chat with just a message |
| Unknown | Text generation/completion |
| Unknown | Generate text embeddings |
| Unknown | Classify text into categories |
| Unknown | Extract named entities from text |
| Unknown | Summarize text content |
| Unknown | Vision-based OCR from images |
| Unknown | Describe image content |
| Unknown | Extract structured data from images |
| Unknown | Transform data using natural language |
| Unknown | Transform data to match a target schema |
| Unknown | Convert between data formats |

## Best Practices

1. **Caching**: Cache responses where appropriate
2. **Error Handling**: Always handle API errors gracefully
3. **Timeouts**: Set appropriate timeout values
4. **Logging**: Log API calls for debugging

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
