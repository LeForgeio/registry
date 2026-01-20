import express from 'express';
import cors from 'cors';
import helmet from 'helmet';

const app = express();
const PORT = process.env.PORT || 3005;

app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '50mb' }));

app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'image-service',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

app.post('/api/v1/image/resize', async (req, res) => {
  // TODO: Implement image resizing with Sharp
  res.json({ success: true, message: 'Image resize endpoint - coming soon' });
});

app.post('/api/v1/image/convert', async (req, res) => {
  // TODO: Implement format conversion
  res.json({ success: true, message: 'Image convert endpoint - coming soon' });
});

app.listen(PORT, () => {
  console.log(`Image service running on port ${PORT}`);
});

export { app };
