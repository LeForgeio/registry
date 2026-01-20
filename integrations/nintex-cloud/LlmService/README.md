# FlowForge llm-service - Nintex Workflow Cloud Xtension

## Overview
FlowForge plugin Xtension for Nintex Workflow Cloud.

## Installation

1. Go to **Nintex Workflow Cloud** > **Settings** > **Xtensions**
2. Click **Add Xtension**
3. Choose **Add custom connector**
4. Upload `llm-service.swagger.json`
5. Configure authentication (API Key)
6. Click **Publish**

## Configuration

### API Key Setup
1. In the Xtension settings, select **API Key** authentication
2. Set header name: `X-API-Key`
3. Enter your FlowForge API key

### Base URL
Update the host in the Swagger file to your FlowForge instance URL.

## Available Actions

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

## Usage in Workflows

After publishing the Xtension:
1. Open workflow designer
2. Find actions under **FlowForge** category
3. Drag and drop actions into your workflow
4. Configure action parameters

## Support

For issues or questions, visit [FlowForge Support](https://flowforge.io/support)
