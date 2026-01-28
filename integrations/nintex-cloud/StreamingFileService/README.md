# LeForge streaming-file-service - Nintex Workflow Cloud Xtension

## Overview
LeForge plugin Xtension for Nintex Workflow Cloud.

## Installation

1. Go to **Nintex Workflow Cloud** > **Settings** > **Xtensions**
2. Click **Add Xtension**
3. Choose **Add custom connector**
4. Upload `streaming-file-service.swagger.json`
5. Configure authentication (API Key)
6. Click **Publish**

## Configuration

### API Key Setup
1. In the Xtension settings, select **API Key** authentication
2. Set header name: `X-API-Key`
3. Enter your LeForge API key

### Base URL
Update the host in the Swagger file to your LeForge instance URL.

## Available Actions

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

## Usage in Workflows

After publishing the Xtension:
1. Open workflow designer
2. Find actions under **LeForge** category
3. Drag and drop actions into your workflow
4. Configure action parameters

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
