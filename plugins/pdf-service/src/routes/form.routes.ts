import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { pdfService } from '../services';
import {
  FillFormRequestSchema,
  FillFormResponseSchema,
  PdfInfoRequestSchema,
  PdfInfoResponseSchema,
  ErrorResponseSchema,
  FillFormRequest,
  PdfInfoRequest,
} from '../schemas';
import { config } from '../config';

export async function formRoutes(fastify: FastifyInstance): Promise<void> {
  /**
   * Fill form fields in a PDF
   */
  fastify.post<{ Body: FillFormRequest }>(
    '/fill',
    {
      schema: {
        description: 'Fill form fields in a PDF document',
        tags: ['Form'],
        body: FillFormRequestSchema,
        response: {
          200: FillFormResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { file, fields, flatten } = request.body;

      // Validate file size
      const estimatedSize = Math.ceil(file.length * 0.75);
      if (estimatedSize > config.pdf.maxFileSize) {
        return reply.status(400).send({
          success: false,
          error: 'File exceeds maximum size',
          code: 'FILE_TOO_LARGE',
        });
      }

      // Validate fields
      if (fields.length === 0) {
        return reply.status(400).send({
          success: false,
          error: 'At least one field is required',
          code: 'NO_FIELDS',
        });
      }

      try {
        const result = await pdfService.fillForm({
          file,
          fields,
          flatten,
        });

        const base64Pdf = result.pdf.toString('base64');
        const filename = `filled-${Date.now()}.pdf`;

        return {
          success: true as const,
          data: {
            pdf: base64Pdf,
            filename,
            size: result.pdf.length,
            filledFields: result.filledFields,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to fill PDF form');
        const message = error instanceof Error ? error.message : 'Unknown error';
        
        // Check for common form errors
        if (message.includes('field') || message.includes('form')) {
          return reply.status(400).send({
            success: false,
            error: `Form error: ${message}`,
            code: 'FORM_ERROR',
          });
        }

        return reply.status(500).send({
          success: false,
          error: `Failed to fill form: ${message}`,
          code: 'FILL_FAILED',
        });
      }
    }
  );

  /**
   * Get PDF information including form fields
   */
  fastify.post<{ Body: PdfInfoRequest }>(
    '/info',
    {
      schema: {
        description: 'Get information about a PDF including form fields',
        tags: ['Form'],
        body: PdfInfoRequestSchema,
        response: {
          200: PdfInfoResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { file } = request.body;

      // Validate file size
      const estimatedSize = Math.ceil(file.length * 0.75);
      if (estimatedSize > config.pdf.maxFileSize) {
        return reply.status(400).send({
          success: false,
          error: 'File exceeds maximum size',
          code: 'FILE_TOO_LARGE',
        });
      }

      try {
        const info = await pdfService.getInfo(file);

        return {
          success: true as const,
          data: info,
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to get PDF info');
        const message = error instanceof Error ? error.message : 'Unknown error';
        
        if (message.includes('Invalid PDF') || message.includes('Password')) {
          return reply.status(400).send({
            success: false,
            error: `Invalid or protected PDF: ${message}`,
            code: 'PDF_INVALID',
          });
        }

        return reply.status(500).send({
          success: false,
          error: `Failed to get PDF info: ${message}`,
          code: 'INFO_FAILED',
        });
      }
    }
  );

  /**
   * Get PDF info from uploaded file
   */
  fastify.post(
    '/info/upload',
    {
      schema: {
        description: 'Get information about an uploaded PDF file',
        tags: ['Form'],
        consumes: ['multipart/form-data'],
        response: {
          200: PdfInfoResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      try {
        const data = await request.file();

        if (!data) {
          return reply.status(400).send({
            success: false,
            error: 'No file uploaded',
            code: 'NO_FILE',
          });
        }

        // Validate content type
        if (data.mimetype !== 'application/pdf') {
          return reply.status(400).send({
            success: false,
            error: 'Uploaded file is not a PDF',
            code: 'INVALID_FILE_TYPE',
          });
        }

        // Read file data
        const chunks: Buffer[] = [];
        for await (const chunk of data.file) {
          chunks.push(chunk);
        }
        const buffer = Buffer.concat(chunks);

        // Validate size
        if (buffer.length > config.pdf.maxFileSize) {
          return reply.status(400).send({
            success: false,
            error: 'File exceeds maximum size',
            code: 'FILE_TOO_LARGE',
          });
        }

        const info = await pdfService.getInfo(buffer);

        return {
          success: true as const,
          data: info,
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to get uploaded PDF info');
        const message = error instanceof Error ? error.message : 'Unknown error';
        return reply.status(500).send({
          success: false,
          error: `Failed to get PDF info: ${message}`,
          code: 'INFO_FAILED',
        });
      }
    }
  );
}
