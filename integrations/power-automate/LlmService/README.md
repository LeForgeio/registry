# LeForge llm-service - Power Automate Connector

## Overview
LeForge plugin connector for Microsoft Power Automate.

## Installation

### Method 1: Import from file
1. Go to **Power Automate** > **Data** > **Custom connectors**
2. Click **+ New custom connector** > **Import an OpenAPI file**
3. Select `apiDefinition.swagger.json` from this folder
4. Configure the connector settings
5. Click **Create connector**

### Method 2: Import from URL
1. Host this connector on a web server
2. Use the URL to import directly

## Configuration

After importing the connector:

1. Click **Test** tab
2. Create a new connection
3. Enter your LeForge API Key
4. Test a simple operation

## Available Actions

| Action | Description |
|--------|-------------|
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

## Authentication

This connector uses API Key authentication:
- Header name: `X-API-Key`
- Get your API key from LeForge dashboard

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
