# LeForge streaming-file-service - Mendix Integration

## Overview
LeForge plugin integration for Mendix.

## Integration Methods

### Method 1: Consume REST Service (Recommended)

1. Open **Mendix Studio Pro**
2. Go to project directory
3. Right-click **App** > **Add other** > **Consumed REST service**
4. Import `streaming-file-service-openapi.json`
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

| Unknown | Initialize a chunked upload session. Returns uploadId for su... |
| Unknown | Upload a single chunk. Supports resume - re-upload failed ch... |
| Unknown | Complete chunked upload - assembles chunks and verifies inte... |
| Unknown | Get upload progress - which chunks received, resume point. |
| Unknown | Cancel and cleanup an incomplete upload. |
| Unknown | Stream download with Range header support for resume. |
| Unknown | Initialize chunked download - get download manifest. |
| Unknown | Stream upload directly to cloud storage (S3/Azure/GCS) witho... |
| Unknown | Stream download from cloud storage to local or another desti... |
| Unknown | Copy files between cloud providers (S3 to Azure, GCS to S3, ... |
| Unknown | Generate presigned URLs for direct browser uploads/downloads... |
| Unknown | Split large PDF into smaller files by page ranges. |
| Unknown | Merge multiple PDFs into one. |
| Unknown | Compress files (zip, gzip, tar.gz) with streaming. |
| Unknown | Extract compressed archives with streaming. |
| Unknown | Transcode video/audio files. Runs asynchronously for large f... |
| Unknown | Extract audio track from video file. |
| Unknown | Generate thumbnails from video at specified timestamps. |
| Unknown | Check status of async transformation job. |
| Unknown | Calculate checksum of file without loading into memory. |

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
