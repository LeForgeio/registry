# n8n-nodes-LeForge-streamingfileservice

n8n community node for LeForge streaming-file-service.



## Installation

### Community Nodes (Recommended)

1. Go to **Settings** > **Community Nodes**
2. Click **Install**
3. Enter `n8n-nodes-LeForge-streamingfileservice`
4. Agree to the risks
5. Click **Install**

### Manual Installation

```bash
npm install n8n-nodes-LeForge-streamingfileservice
```

Then restart n8n.

## Configuration

1. Add LeForge credentials:
   - Go to **Credentials** > **Add Credential**
   - Search for "LeForge"
   - Enter your API Key and Base URL

2. Use the node in your workflows

## Operations

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

## Compatibility

- n8n version: 0.200.0+
- Node.js version: 18+

## Resources

- [LeForge Documentation](https://LeForge.io/docs)
- [n8n Community Nodes Documentation](https://docs.n8n.io/integrations/community-nodes/)

## License

MIT
