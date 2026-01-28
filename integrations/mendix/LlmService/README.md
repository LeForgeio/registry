# LeForge llm-service - Mendix Integration

## Overview
LeForge plugin integration for Mendix.

## Integration Methods

### Method 1: Consume REST Service (Recommended)

1. Open **Mendix Studio Pro**
2. Go to project directory
3. Right-click **App** > **Add other** > **Consumed REST service**
4. Import `llm-service-openapi.json`
5. Configure base URL and authentication

### Method 2: Java Actions

Use the provided Java action stubs in `javasource/LeForge/actions/`:

1. Copy Java files to your project's javasource folder
2. Implement the API call logic
3. Expose as microflow activities

## Configuration

### Constants
Create these constants in your Mendix app:

- `LeForge.BaseUrl` - Your LeForge instance URL
- `LeForge.ApiKey` - Your API key

### Request Handling
Use Mendix's **Call REST** activity with:
- Method: POST/GET as appropriate
- URL: `$LeForge.BaseUrl + '/api/v1/endpoint'`
- Headers: `X-API-Key: $LeForge.ApiKey`

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

## Microflow Example

```
Microflow: ACT_LeForge_Chat
    Input: Message (String)
    
    1. Create JSON structure for request
    2. Call REST (POST /api/v1/chat)
    3. Parse JSON response
    4. Return response text
```

## Marketplace Publishing

To publish as a Marketplace module:

1. Create module in Studio Pro
2. Add all integrations
3. Export as .mpk file
4. Upload to Marketplace

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
