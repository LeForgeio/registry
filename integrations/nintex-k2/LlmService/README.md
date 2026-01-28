# LeForge llm-service - Nintex K2 Integration

## Overview
LeForge plugin integration for Nintex K2.

## Installation

### 1. Register REST Service Broker

1. Open **K2 Management Console**
2. Navigate to **Integration** > **Service Types**
3. Add new **REST Service Broker**
4. Upload `swagger/llm-service.json`
5. Configure base URL and authentication

### 2. Create Service Instance

1. Go to **Service Instances**
2. Create new instance from the registered service type
3. Configure connection:
   - Base URL: Your LeForge server URL
   - Authentication: API Key
   - Header: `X-API-Key`

### 3. Generate SmartObjects

1. Navigate to **SmartObjects**
2. Click **Generate SmartObjects** from service instance
3. Select operations to expose
4. Publish SmartObjects

## SmartObject Templates

Pre-configured SmartObject templates are available in the `smartobjects/` folder.
Import these for common operations.

## Available Operations

| Get Providers | List available LLM providers |
| Providers Configure | Configure a provider with API credentials |
| Get Providers Models | List available models for a provider |
| Get Providers Health | Check provider health status |
| Providers Chat | Chat with a specific provider |
| Providers Embed | Generate embeddings with a specific provider |
| Providers Chat | Universal chat endpoint with provider selection |
| Chat | Chat completion (vLLM/default provider) |
| Chat Simple | Simple chat with just a message |
| Generate | Text generation/completion |
| Embeddings | Generate text embeddings |
| Classify | Classify text into categories |
| Extract | Extract named entities from text |
| Summarize | Summarize text content |
| Vision Ocr | Vision-based OCR from images |
| Vision Describe | Describe image content |
| Vision Extract | Extract structured data from images |
| Transform | Transform data using natural language |
| Transform Schema | Transform data to match a target schema |
| Transform Convert | Convert between data formats |

## Using in K2 Forms & Workflows

### In Forms
1. Add SmartObject data source
2. Bind to form controls
3. Execute methods on form events

### In Workflows
1. Add SmartObject event
2. Configure method and parameters
3. Map inputs/outputs

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
