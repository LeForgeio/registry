import express from 'express';
import cors from 'cors';
import helmet from 'helmet';

const app = express();
const PORT = process.env.PORT || 3008;

app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'data-transform-service',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

app.post('/api/v1/data/transform/json', async (req, res) => {
  // TODO: Implement JSON transformation
  res.json({ success: true, message: 'JSON transform endpoint - coming soon' });
});

app.post('/api/v1/data/convert', async (req, res) => {
  // TODO: Implement format conversion
  res.json({ success: true, message: 'Format convert endpoint - coming soon' });
});

app.listen(PORT, () => {
  console.log(`Data transform service running on port ${PORT}`);
});

export { app };
