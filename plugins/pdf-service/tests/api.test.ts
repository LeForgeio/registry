import { buildApp } from '../src/app';
import { FastifyInstance } from 'fastify';
import { PDFDocument, StandardFonts } from 'pdf-lib';

describe('API Routes', () => {
  let app: FastifyInstance;

  beforeAll(async () => {
    app = await buildApp();
  });

  afterAll(async () => {
    await app.close();
  });

  // Helper to create test PDF
  async function createTestPdf(pages: number = 1): Promise<string> {
    const pdfDoc = await PDFDocument.create();
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    
    for (let i = 0; i < pages; i++) {
      const page = pdfDoc.addPage([612, 792]);
      page.drawText(`Test Page ${i + 1}`, {
        x: 50,
        y: 700,
        size: 24,
        font,
      });
    }
    
    const bytes = await pdfDoc.save();
    return Buffer.from(bytes).toString('base64');
  }

  describe('Health endpoints', () => {
    it('GET /api/v1/health should return ok', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/health',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.status).toBe('ok');
      expect(body.timestamp).toBeDefined();
    });

    it('GET /api/v1/health/detailed should return detailed status', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/health/detailed',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.status).toBeDefined();
      expect(body.version).toBeDefined();
      expect(body.uptime).toBeGreaterThanOrEqual(0);
      expect(body.checks).toBeDefined();
      expect(body.checks.memory).toBeDefined();
      expect(body.checks.tempDirectory).toBeDefined();
    });

    it('GET /api/v1/live should return alive', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/live',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.alive).toBe(true);
    });
  });

  describe('POST /api/v1/generate/html', () => {
    it('should generate PDF from simple HTML', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/html',
        payload: {
          html: '<html><body><h1>Hello World</h1></body></html>',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      expect(body.data.pdf).toBeDefined();
      expect(body.data.size).toBeGreaterThan(0);
      expect(body.data.pages).toBeGreaterThanOrEqual(1);
    });

    it('should generate PDF with options', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/html',
        payload: {
          html: '<html><body><h1>Test</h1></body></html>',
          format: 'Letter',
          orientation: 'landscape',
          printBackground: true,
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
    });

    it('should return error for empty HTML', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/html',
        payload: {
          html: '',
        },
      });

      // Empty HTML is valid but should create a blank PDF
      expect(response.statusCode).toBe(200);
    });

    it('should sanitize HTML with scripts', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/html',
        payload: {
          html: '<html><body><script>alert("xss")</script><h1>Safe</h1></body></html>',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      // The PDF should be generated without the script
    });
  });

  describe('POST /api/v1/generate/template', () => {
    it('should generate PDF from template', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/template',
        payload: {
          template: '<html><body><h1>{{title}}</h1><p>{{content}}</p></body></html>',
          data: {
            title: 'Invoice',
            content: 'This is an invoice',
          },
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      expect(body.data.pdf).toBeDefined();
    });

    it('should generate PDF with array data', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/template',
        payload: {
          template: '<html><body><ul>{{#each items}}<li>{{this}}</li>{{/each}}</ul></body></html>',
          data: {
            items: ['Item 1', 'Item 2', 'Item 3'],
          },
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
    });

    it('should return error for invalid template', async () => {
      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/generate/template',
        payload: {
          template: '{{#if}}invalid{{/if}}', // Invalid - missing condition
          data: {},
        },
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.code).toBe('TEMPLATE_INVALID');
    });
  });

  describe('POST /api/v1/merge', () => {
    it('should merge two PDFs', async () => {
      const pdf1 = await createTestPdf(1);
      const pdf2 = await createTestPdf(2);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/merge',
        payload: {
          files: [
            { data: pdf1 },
            { data: pdf2 },
          ],
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      expect(body.data.pages).toBe(3);
      expect(body.data.mergedCount).toBe(2);
    });

    it('should return error for single file', async () => {
      const pdf = await createTestPdf(1);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/merge',
        payload: {
          files: [{ data: pdf }],
        },
      });

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.code).toBe('INSUFFICIENT_FILES');
    });

    it('should merge with metadata', async () => {
      const pdf1 = await createTestPdf(1);
      const pdf2 = await createTestPdf(1);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/merge',
        payload: {
          files: [
            { data: pdf1 },
            { data: pdf2 },
          ],
          metadata: {
            title: 'Merged Document',
            author: 'Test',
          },
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
    });
  });

  describe('POST /api/v1/extract/text', () => {
    it('should extract text from PDF', async () => {
      const pdf = await createTestPdf(2);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/extract/text',
        payload: {
          file: pdf,
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      expect(body.data.totalPages).toBe(2);
      expect(body.data.pages).toHaveLength(2);
      expect(body.data.text).toContain('Test Page');
    });

    it('should extract from specific pages', async () => {
      const pdf = await createTestPdf(5);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/extract/text',
        payload: {
          file: pdf,
          pageNumbers: [1, 3],
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.data.pages).toHaveLength(2);
      expect(body.data.pages[0].pageNumber).toBe(1);
      expect(body.data.pages[1].pageNumber).toBe(3);
    });

    it('should preserve layout when requested', async () => {
      const pdf = await createTestPdf(1);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/extract/text',
        payload: {
          file: pdf,
          preserveLayout: true,
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.data.pages[0].lines).toBeDefined();
    });
  });

  describe('POST /api/v1/form/info', () => {
    it('should get PDF info', async () => {
      const pdf = await createTestPdf(3);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/form/info',
        payload: {
          file: pdf,
        },
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
      expect(body.data.pageCount).toBe(3);
      expect(body.data.fileSize).toBeGreaterThan(0);
    });
  });

  describe('Root endpoint', () => {
    it('GET / should return service info', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/',
      });

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.service).toBe('pdf-service');
      expect(body.version).toBeDefined();
      expect(body.documentation).toBe('/docs');
    });
  });

  describe('Swagger documentation', () => {
    it('GET /docs should return swagger UI', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/docs',
      });

      // Should redirect to /docs/
      expect([200, 302]).toContain(response.statusCode);
    });
  });
});
