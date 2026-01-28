/**
 * Streaming File Service - Enterprise Large File Handling
 * LeForge ForgeHook Plugin
 * 
 * Features:
 * - Chunked uploads with resume capability
 * - Multi-cloud storage (S3, Azure Blob, GCS)
 * - File transformations (PDF split/merge, video transcoding)
 * - Presigned URLs for direct browser access
 */

require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const fs = require('fs').promises;
const fsSync = require('fs');
const crypto = require('crypto');

// Cloud providers
const { S3Client, PutObjectCommand, GetObjectCommand, CopyObjectCommand, DeleteObjectCommand, HeadObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { Upload } = require('@aws-sdk/lib-storage');
const { BlobServiceClient } = require('@azure/storage-blob');
const { Storage: GCSStorage } = require('@google-cloud/storage');

// File processing
const ffmpeg = require('fluent-ffmpeg');
const { PDFDocument } = require('pdf-lib');
const archiver = require('archiver');
const unzipper = require('unzipper');
const mime = require('mime-types');

const app = express();
const PORT = process.env.PORT || 3020;

// Configuration
const config = {
  storagePath: process.env.STORAGE_PATH || '/data/files',
  chunksPath: process.env.CHUNKS_PATH || '/data/chunks',
  transformsPath: process.env.TRANSFORMS_PATH || '/data/transforms',
  maxFileSizeGB: parseInt(process.env.MAX_FILE_SIZE_GB || '0'),
  chunkSizeMB: parseInt(process.env.CHUNK_SIZE_MB || '10'),
  uploadExpiryHours: parseInt(process.env.UPLOAD_EXPIRY_HOURS || '24'),
  fileRetentionHours: parseInt(process.env.FILE_RETENTION_HOURS || '72'),
  ffmpegThreads: parseInt(process.env.FFMPEG_THREADS || '4'),
  concurrentTransforms: parseInt(process.env.CONCURRENT_TRANSFORMS || '2')
};

// In-memory stores (use Redis in production)
const uploadSessions = new Map();
const files = new Map();
const transformJobs = new Map();

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('combined'));
app.use(express.json());

// Ensure directories exist
async function ensureDirectories() {
  const dirs = [config.storagePath, config.chunksPath, config.transformsPath];
  for (const dir of dirs) {
    await fs.mkdir(dir, { recursive: true });
  }
}

// ============================================================================
// CLOUD STORAGE CLIENTS
// ============================================================================

function getS3Client(credentials) {
  return new S3Client({
    region: credentials?.region || process.env.AWS_REGION || 'us-east-1',
    credentials: credentials?.accessKeyId ? {
      accessKeyId: credentials.accessKeyId,
      secretAccessKey: credentials.secretAccessKey
    } : undefined
  });
}

function getAzureClient(connectionString) {
  const connStr = connectionString || process.env.AZURE_STORAGE_CONNECTION_STRING;
  return BlobServiceClient.fromConnectionString(connStr);
}

function getGCSClient(credentialsJson) {
  const creds = credentialsJson || process.env.GCS_CREDENTIALS_JSON;
  if (creds) {
    const credentials = typeof creds === 'string' ? JSON.parse(creds) : creds;
    return new GCSStorage({ credentials });
  }
  return new GCSStorage();
}

// ============================================================================
// CHUNKED UPLOAD ENDPOINTS
// ============================================================================

// Initialize chunked upload
app.post('/api/v1/files/upload/init', async (req, res) => {
  try {
    const { filename, totalSize, mimeType, chunkSize, metadata } = req.body;
    
    const actualChunkSize = (chunkSize || config.chunkSizeMB * 1024 * 1024);
    const totalChunks = Math.ceil(totalSize / actualChunkSize);
    
    const uploadId = uuidv4();
    const sessionPath = path.join(config.chunksPath, uploadId);
    await fs.mkdir(sessionPath, { recursive: true });
    
    const session = {
      uploadId,
      filename,
      totalSize,
      mimeType: mimeType || mime.lookup(filename) || 'application/octet-stream',
      chunkSize: actualChunkSize,
      totalChunks,
      receivedChunks: [],
      metadata: metadata || {},
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + config.uploadExpiryHours * 3600000).toISOString()
    };
    
    uploadSessions.set(uploadId, session);
    
    res.json({
      uploadId,
      chunkSize: actualChunkSize,
      totalChunks,
      expiresAt: session.expiresAt
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Upload chunk
app.put('/api/v1/files/upload/:uploadId/chunk/:chunkIndex', express.raw({ type: '*/*', limit: '100mb' }), async (req, res) => {
  try {
    const { uploadId, chunkIndex } = req.params;
    const index = parseInt(chunkIndex);
    
    const session = uploadSessions.get(uploadId);
    if (!session) {
      return res.status(404).json({ error: 'Upload session not found' });
    }
    
    const chunkPath = path.join(config.chunksPath, uploadId, `chunk_${index}`);
    await fs.writeFile(chunkPath, req.body);
    
    // Calculate checksum
    const checksum = crypto.createHash('sha256').update(req.body).digest('hex');
    
    // Track received chunk
    if (!session.receivedChunks.includes(index)) {
      session.receivedChunks.push(index);
      session.receivedChunks.sort((a, b) => a - b);
    }
    
    res.json({
      chunkIndex: index,
      bytesReceived: req.body.length,
      checksum
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Complete upload
app.post('/api/v1/files/upload/:uploadId/complete', async (req, res) => {
  try {
    const { uploadId } = req.params;
    const { checksums } = req.body;
    
    const session = uploadSessions.get(uploadId);
    if (!session) {
      return res.status(404).json({ error: 'Upload session not found' });
    }
    
    // Verify all chunks received
    if (session.receivedChunks.length !== session.totalChunks) {
      return res.status(400).json({
        error: 'Missing chunks',
        received: session.receivedChunks.length,
        expected: session.totalChunks,
        missing: Array.from({ length: session.totalChunks }, (_, i) => i)
          .filter(i => !session.receivedChunks.includes(i))
      });
    }
    
    // Assemble file
    const fileId = uuidv4();
    const outputPath = path.join(config.storagePath, fileId);
    await fs.mkdir(outputPath, { recursive: true });
    
    const filePath = path.join(outputPath, session.filename);
    const writeStream = fsSync.createWriteStream(filePath);
    const hash = crypto.createHash('sha256');
    
    for (let i = 0; i < session.totalChunks; i++) {
      const chunkPath = path.join(config.chunksPath, uploadId, `chunk_${i}`);
      const chunkData = await fs.readFile(chunkPath);
      hash.update(chunkData);
      writeStream.write(chunkData);
    }
    
    writeStream.end();
    
    await new Promise((resolve, reject) => {
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });
    
    const fullChecksum = hash.digest('hex');
    const stats = await fs.stat(filePath);
    
    // Store file metadata
    const fileInfo = {
      fileId,
      filename: session.filename,
      path: filePath,
      size: stats.size,
      mimeType: session.mimeType,
      checksum: fullChecksum,
      metadata: session.metadata,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + config.fileRetentionHours * 3600000).toISOString()
    };
    
    files.set(fileId, fileInfo);
    
    // Cleanup chunks
    await fs.rm(path.join(config.chunksPath, uploadId), { recursive: true, force: true });
    uploadSessions.delete(uploadId);
    
    res.json({
      fileId,
      path: `/files/${fileId}/${session.filename}`,
      size: stats.size,
      checksum: fullChecksum
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get upload status
app.get('/api/v1/files/upload/:uploadId/status', (req, res) => {
  const { uploadId } = req.params;
  const session = uploadSessions.get(uploadId);
  
  if (!session) {
    return res.status(404).json({ error: 'Upload session not found' });
  }
  
  const bytesUploaded = session.receivedChunks.length * session.chunkSize;
  const percentComplete = Math.round((session.receivedChunks.length / session.totalChunks) * 100);
  
  res.json({
    uploadId,
    receivedChunks: session.receivedChunks,
    missingChunks: Array.from({ length: session.totalChunks }, (_, i) => i)
      .filter(i => !session.receivedChunks.includes(i)),
    bytesUploaded: Math.min(bytesUploaded, session.totalSize),
    percentComplete
  });
});

// Cancel upload
app.delete('/api/v1/files/upload/:uploadId', async (req, res) => {
  try {
    const { uploadId } = req.params;
    
    await fs.rm(path.join(config.chunksPath, uploadId), { recursive: true, force: true });
    uploadSessions.delete(uploadId);
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// DOWNLOAD ENDPOINTS
// ============================================================================

// Stream download with Range support
app.get('/api/v1/files/download/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    const fileInfo = files.get(fileId);
    
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const stat = await fs.stat(fileInfo.path);
    const range = req.headers.range;
    
    res.setHeader('Content-Type', fileInfo.mimeType);
    res.setHeader('Content-Disposition', `attachment; filename="${fileInfo.filename}"`);
    res.setHeader('Accept-Ranges', 'bytes');
    
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : stat.size - 1;
      const chunkSize = end - start + 1;
      
      res.status(206);
      res.setHeader('Content-Range', `bytes ${start}-${end}/${stat.size}`);
      res.setHeader('Content-Length', chunkSize);
      
      const stream = fsSync.createReadStream(fileInfo.path, { start, end });
      stream.pipe(res);
    } else {
      res.setHeader('Content-Length', stat.size);
      const stream = fsSync.createReadStream(fileInfo.path);
      stream.pipe(res);
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Initialize chunked download
app.post('/api/v1/files/download/init', async (req, res) => {
  try {
    const { fileId, chunkSize } = req.body;
    const fileInfo = files.get(fileId);
    
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const actualChunkSize = chunkSize || config.chunkSizeMB * 1024 * 1024;
    const totalChunks = Math.ceil(fileInfo.size / actualChunkSize);
    const downloadId = uuidv4();
    
    const chunks = [];
    for (let i = 0; i < totalChunks; i++) {
      const start = i * actualChunkSize;
      const end = Math.min(start + actualChunkSize - 1, fileInfo.size - 1);
      chunks.push({
        index: i,
        start,
        end,
        url: `/api/v1/files/download/${fileId}?start=${start}&end=${end}`
      });
    }
    
    res.json({
      downloadId,
      totalSize: fileInfo.size,
      totalChunks,
      chunks
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// CLOUD STORAGE ENDPOINTS
// ============================================================================

// Upload to cloud storage
app.post('/api/v1/files/cloud/upload', async (req, res) => {
  try {
    const { provider, bucket, container, key, blob, sourceUrl, fileId, credentials } = req.body;
    
    let sourceStream;
    let contentLength;
    
    if (fileId) {
      const fileInfo = files.get(fileId);
      if (!fileInfo) {
        return res.status(404).json({ error: 'Source file not found' });
      }
      sourceStream = fsSync.createReadStream(fileInfo.path);
      contentLength = fileInfo.size;
    } else if (sourceUrl) {
      const response = await fetch(sourceUrl);
      sourceStream = response.body;
      contentLength = parseInt(response.headers.get('content-length'));
    } else {
      return res.status(400).json({ error: 'Either fileId or sourceUrl required' });
    }
    
    let result;
    
    switch (provider) {
      case 's3': {
        const s3 = getS3Client(credentials);
        const upload = new Upload({
          client: s3,
          params: {
            Bucket: bucket,
            Key: key,
            Body: sourceStream,
            ContentLength: contentLength
          }
        });
        
        await upload.done();
        result = { provider, bucket, key, url: `s3://${bucket}/${key}`, size: contentLength };
        break;
      }
      
      case 'azure': {
        const azure = getAzureClient(credentials?.connectionString);
        const containerClient = azure.getContainerClient(container);
        const blobClient = containerClient.getBlockBlobClient(blob);
        
        await blobClient.uploadStream(sourceStream, undefined, undefined, {
          blobHTTPHeaders: { blobContentLength: contentLength }
        });
        
        result = { provider, container, blob, url: blobClient.url, size: contentLength };
        break;
      }
      
      case 'gcs': {
        const gcs = getGCSClient(credentials?.credentialsJson);
        const file = gcs.bucket(bucket).file(key);
        
        await new Promise((resolve, reject) => {
          sourceStream
            .pipe(file.createWriteStream())
            .on('finish', resolve)
            .on('error', reject);
        });
        
        result = { provider, bucket, key, url: `gs://${bucket}/${key}`, size: contentLength };
        break;
      }
      
      default:
        return res.status(400).json({ error: `Unknown provider: ${provider}` });
    }
    
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Generate presigned URL
app.post('/api/v1/files/cloud/presigned-url', async (req, res) => {
  try {
    const { provider, bucket, container, key, blob, operation, expiresIn, contentType, credentials } = req.body;
    
    const expiry = expiresIn || 3600;
    
    switch (provider) {
      case 's3': {
        const s3 = getS3Client(credentials);
        const command = operation === 'PUT'
          ? new PutObjectCommand({ Bucket: bucket, Key: key, ContentType: contentType })
          : new GetObjectCommand({ Bucket: bucket, Key: key });
        
        const url = await getSignedUrl(s3, command, { expiresIn: expiry });
        
        res.json({
          url,
          expiresAt: new Date(Date.now() + expiry * 1000).toISOString(),
          headers: contentType ? { 'Content-Type': contentType } : {}
        });
        break;
      }
      
      case 'azure': {
        const azure = getAzureClient(credentials?.connectionString);
        const containerClient = azure.getContainerClient(container);
        const blobClient = containerClient.getBlobClient(blob);
        
        const url = await blobClient.generateSasUrl({
          permissions: operation === 'PUT' ? 'w' : 'r',
          expiresOn: new Date(Date.now() + expiry * 1000)
        });
        
        res.json({
          url,
          expiresAt: new Date(Date.now() + expiry * 1000).toISOString(),
          headers: {}
        });
        break;
      }
      
      case 'gcs': {
        const gcs = getGCSClient(credentials?.credentialsJson);
        const file = gcs.bucket(bucket).file(key);
        
        const [url] = await file.getSignedUrl({
          version: 'v4',
          action: operation === 'PUT' ? 'write' : 'read',
          expires: Date.now() + expiry * 1000,
          contentType
        });
        
        res.json({
          url,
          expiresAt: new Date(Date.now() + expiry * 1000).toISOString(),
          headers: contentType ? { 'Content-Type': contentType } : {}
        });
        break;
      }
      
      default:
        return res.status(400).json({ error: `Unknown provider: ${provider}` });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ============================================================================
// FILE TRANSFORMATION ENDPOINTS
// ============================================================================

// Split PDF
app.post('/api/v1/files/transform/split-pdf', async (req, res) => {
  try {
    const { fileId, ranges } = req.body;
    const fileInfo = files.get(fileId);
    
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const pdfBytes = await fs.readFile(fileInfo.path);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    const totalPages = pdfDoc.getPageCount();
    
    const outputFiles = [];
    
    for (const [start, end] of ranges) {
      const actualEnd = end === -1 ? totalPages : end;
      const newPdf = await PDFDocument.create();
      
      const pageIndices = [];
      for (let i = start - 1; i < actualEnd; i++) {
        pageIndices.push(i);
      }
      
      const copiedPages = await newPdf.copyPages(pdfDoc, pageIndices);
      copiedPages.forEach(page => newPdf.addPage(page));
      
      const newPdfBytes = await newPdf.save();
      
      const outputFileId = uuidv4();
      const outputPath = path.join(config.storagePath, outputFileId);
      await fs.mkdir(outputPath, { recursive: true });
      
      const outputFilename = `${path.basename(fileInfo.filename, '.pdf')}_pages_${start}-${actualEnd}.pdf`;
      const outputFilePath = path.join(outputPath, outputFilename);
      await fs.writeFile(outputFilePath, newPdfBytes);
      
      const outputFileInfo = {
        fileId: outputFileId,
        filename: outputFilename,
        path: outputFilePath,
        size: newPdfBytes.length,
        mimeType: 'application/pdf',
        createdAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + config.fileRetentionHours * 3600000).toISOString()
      };
      
      files.set(outputFileId, outputFileInfo);
      outputFiles.push({
        fileId: outputFileId,
        pages: `${start}-${actualEnd}`,
        size: newPdfBytes.length
      });
    }
    
    res.json({ files: outputFiles });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Merge PDFs
app.post('/api/v1/files/transform/merge-pdf', async (req, res) => {
  try {
    const { fileIds, outputFilename } = req.body;
    
    const mergedPdf = await PDFDocument.create();
    
    for (const fid of fileIds) {
      const fileInfo = files.get(fid);
      if (!fileInfo) {
        return res.status(404).json({ error: `File not found: ${fid}` });
      }
      
      const pdfBytes = await fs.readFile(fileInfo.path);
      const pdf = await PDFDocument.load(pdfBytes);
      const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
      copiedPages.forEach(page => mergedPdf.addPage(page));
    }
    
    const mergedBytes = await mergedPdf.save();
    
    const outputFileId = uuidv4();
    const outputPath = path.join(config.storagePath, outputFileId);
    await fs.mkdir(outputPath, { recursive: true });
    
    const finalFilename = outputFilename || 'merged.pdf';
    const outputFilePath = path.join(outputPath, finalFilename);
    await fs.writeFile(outputFilePath, mergedBytes);
    
    const outputFileInfo = {
      fileId: outputFileId,
      filename: finalFilename,
      path: outputFilePath,
      size: mergedBytes.length,
      mimeType: 'application/pdf',
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + config.fileRetentionHours * 3600000).toISOString()
    };
    
    files.set(outputFileId, outputFileInfo);
    
    res.json({
      fileId: outputFileId,
      filename: finalFilename,
      size: mergedBytes.length
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Video transcoding (async)
app.post('/api/v1/files/transform/transcode', async (req, res) => {
  try {
    const { fileId, outputFormat, videoCodec, audioCodec, resolution, bitrate, preset } = req.body;
    
    const fileInfo = files.get(fileId);
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const jobId = uuidv4();
    const outputFileId = uuidv4();
    const outputPath = path.join(config.transformsPath, outputFileId);
    await fs.mkdir(outputPath, { recursive: true });
    
    const outputFilename = `${path.basename(fileInfo.filename, path.extname(fileInfo.filename))}.${outputFormat || 'mp4'}`;
    const outputFilePath = path.join(outputPath, outputFilename);
    
    const job = {
      jobId,
      status: 'processing',
      progress: 0,
      startedAt: new Date().toISOString(),
      inputFileId: fileId,
      outputFileId: null
    };
    
    transformJobs.set(jobId, job);
    
    // Start transcoding in background
    const command = ffmpeg(fileInfo.path)
      .outputOptions([
        `-threads ${config.ffmpegThreads}`,
        `-preset ${preset || 'medium'}`
      ]);
    
    if (videoCodec) command.videoCodec(videoCodec);
    if (audioCodec) command.audioCodec(audioCodec);
    if (resolution) command.size(resolution);
    if (bitrate) command.videoBitrate(bitrate);
    
    command
      .on('progress', (progress) => {
        job.progress = Math.round(progress.percent || 0);
      })
      .on('end', async () => {
        const stats = await fs.stat(outputFilePath);
        
        const outputFileInfo = {
          fileId: outputFileId,
          filename: outputFilename,
          path: outputFilePath,
          size: stats.size,
          mimeType: mime.lookup(outputFilename) || 'video/mp4',
          createdAt: new Date().toISOString(),
          expiresAt: new Date(Date.now() + config.fileRetentionHours * 3600000).toISOString()
        };
        
        files.set(outputFileId, outputFileInfo);
        
        job.status = 'completed';
        job.progress = 100;
        job.outputFileId = outputFileId;
        job.completedAt = new Date().toISOString();
      })
      .on('error', (err) => {
        job.status = 'failed';
        job.error = err.message;
      })
      .save(outputFilePath);
    
    res.json({
      jobId,
      status: 'processing',
      statusUrl: `/api/v1/files/transform/status/${jobId}`
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get transformation status
app.get('/api/v1/files/transform/status/:jobId', (req, res) => {
  const { jobId } = req.params;
  const job = transformJobs.get(jobId);
  
  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  
  res.json(job);
});

// Compress files
app.post('/api/v1/files/transform/compress', async (req, res) => {
  try {
    const { fileIds, format, compressionLevel, password } = req.body;
    
    const outputFileId = uuidv4();
    const outputPath = path.join(config.transformsPath, outputFileId);
    await fs.mkdir(outputPath, { recursive: true });
    
    const outputFilename = `archive.${format || 'zip'}`;
    const outputFilePath = path.join(outputPath, outputFilename);
    
    const output = fsSync.createWriteStream(outputFilePath);
    const archive = archiver(format || 'zip', {
      zlib: { level: compressionLevel || 6 }
    });
    
    archive.pipe(output);
    
    for (const fid of fileIds) {
      const fileInfo = files.get(fid);
      if (fileInfo) {
        archive.file(fileInfo.path, { name: fileInfo.filename });
      }
    }
    
    await archive.finalize();
    
    await new Promise((resolve) => output.on('close', resolve));
    
    const stats = await fs.stat(outputFilePath);
    
    const outputFileInfo = {
      fileId: outputFileId,
      filename: outputFilename,
      path: outputFilePath,
      size: stats.size,
      mimeType: 'application/zip',
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + config.fileRetentionHours * 3600000).toISOString()
    };
    
    files.set(outputFileId, outputFileInfo);
    
    res.json({
      fileId: outputFileId,
      filename: outputFilename,
      size: stats.size
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Calculate checksum
app.post('/api/v1/files/checksum', async (req, res) => {
  try {
    const { fileId, algorithm } = req.body;
    const fileInfo = files.get(fileId);
    
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const algo = algorithm || 'sha256';
    const hash = crypto.createHash(algo);
    const stream = fsSync.createReadStream(fileInfo.path);
    
    await new Promise((resolve, reject) => {
      stream.on('data', chunk => hash.update(chunk));
      stream.on('end', resolve);
      stream.on('error', reject);
    });
    
    res.json({
      algorithm: algo,
      checksum: hash.digest('hex')
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get file metadata
app.get('/api/v1/files/:fileId/metadata', async (req, res) => {
  try {
    const { fileId } = req.params;
    const fileInfo = files.get(fileId);
    
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    const response = { ...fileInfo };
    
    // Get media info for video/audio files
    if (fileInfo.mimeType.startsWith('video/') || fileInfo.mimeType.startsWith('audio/')) {
      try {
        const mediaInfo = await new Promise((resolve, reject) => {
          ffmpeg.ffprobe(fileInfo.path, (err, metadata) => {
            if (err) reject(err);
            else resolve(metadata);
          });
        });
        
        response.mediaInfo = {
          duration: mediaInfo.format.duration,
          bitrate: mediaInfo.format.bit_rate,
          format: mediaInfo.format.format_name
        };
        
        const videoStream = mediaInfo.streams.find(s => s.codec_type === 'video');
        if (videoStream) {
          response.mediaInfo.videoCodec = videoStream.codec_name;
          response.mediaInfo.resolution = `${videoStream.width}x${videoStream.height}`;
          response.mediaInfo.fps = eval(videoStream.r_frame_rate);
        }
        
        const audioStream = mediaInfo.streams.find(s => s.codec_type === 'audio');
        if (audioStream) {
          response.mediaInfo.audioCodec = audioStream.codec_name;
          response.mediaInfo.sampleRate = audioStream.sample_rate;
          response.mediaInfo.channels = audioStream.channels;
        }
      } catch (e) {
        // Media info not available
      }
    }
    
    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete file
app.delete('/api/v1/files/:fileId', async (req, res) => {
  try {
    const { fileId } = req.params;
    const fileInfo = files.get(fileId);
    
    if (!fileInfo) {
      return res.status(404).json({ error: 'File not found' });
    }
    
    await fs.rm(path.dirname(fileInfo.path), { recursive: true, force: true });
    files.delete(fileId);
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    activeUploads: uploadSessions.size,
    storedFiles: files.size,
    pendingJobs: [...transformJobs.values()].filter(j => j.status === 'processing').length
  });
});

// Start server
ensureDirectories().then(() => {
  app.listen(PORT, () => {
    console.log(`Streaming File Service running on port ${PORT}`);
  });
});
