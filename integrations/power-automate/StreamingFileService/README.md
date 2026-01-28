# LeForge streaming-file-service - Power Automate Connector

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

## Authentication

This connector uses API Key authentication:
- Header name: `X-API-Key`
- Get your API key from LeForge dashboard

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
