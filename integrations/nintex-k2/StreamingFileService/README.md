# LeForge streaming-file-service - Nintex K2 Integration

## Overview
LeForge plugin integration for Nintex K2.

## Installation

### 1. Register REST Service Broker

1. Open **K2 Management Console**
2. Navigate to **Integration** > **Service Types**
3. Add new **REST Service Broker**
4. Upload `swagger/streaming-file-service.json`
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

| Upload Init | Initialize a chunked upload session. Returns uploadId for su... |
| Update Upload Chunk | Upload a single chunk. Supports resume - re-upload failed ch... |
| Upload Complete | Complete chunked upload - assembles chunks and verifies inte... |
| Get Upload Status | Get upload progress - which chunks received, resume point. |
| Delete Upload | Cancel and cleanup an incomplete upload. |
| Get Download | Stream download with Range header support for resume. |
| Download Init | Initialize chunked download - get download manifest. |
| Cloud Upload | Stream upload directly to cloud storage (S3/Azure/GCS) witho... |
| Cloud Download | Stream download from cloud storage to local or another desti... |
| Cloud Copy | Copy files between cloud providers (S3 to Azure, GCS to S3, ... |
| Cloud Presigned Url | Generate presigned URLs for direct browser uploads/downloads... |
| Transform Split Pdf | Split large PDF into smaller files by page ranges. |
| Transform Merge Pdf | Merge multiple PDFs into one. |
| Transform Compress | Compress files (zip, gzip, tar.gz) with streaming. |
| Transform Extract | Extract compressed archives with streaming. |
| Transform Transcode | Transcode video/audio files. Runs asynchronously for large f... |
| Transform Extract Audio | Extract audio track from video file. |
| Transform Thumbnail | Generate thumbnails from video at specified timestamps. |
| Get Transform Status | Check status of async transformation job. |
| Checksum | Calculate checksum of file without loading into memory. |

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
