# LeForge streaming-file-service - OutSystems Integration

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
3. Import `streaming-file-service-openapi.json`
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
ServerAction: LeForge_streaming-file-service_Operation
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

## Best Practices

1. **Caching**: Cache responses where appropriate
2. **Error Handling**: Always handle API errors gracefully
3. **Timeouts**: Set appropriate timeout values
4. **Logging**: Log API calls for debugging

## Support

For issues or questions, visit [LeForge Support](https://LeForge.io/support)
