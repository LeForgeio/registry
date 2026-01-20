import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { extractorService } from '../services';
import {
  ExtractTextRequestSchema,
  ExtractTextResponseSchema,
  ErrorResponseSchema,
  ExtractTextRequest,
} from '../schemas';
import { config } from '../config';

export async function extractRoutes(fastify: FastifyInstance): Promise<void> {
  /**
   * Extract text from a PDF
   */
  fastify.post<{ Body: ExtractTextRequest }>(
    '/text',
    {
      schema: {
        description: 'Extract text content from a PDF file',
        tags: ['Extract'],
        body: ExtractTextRequestSchema,
        response: {
          200: ExtractTextResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { file, pageNumbers, preserveLayout, includePageBreaks } = request.body;

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
        const result = await extractorService.extractText({
          file,
          pageNumbers,
          preserveLayout,
          includePageBreaks,
        });

        return {
          success: true as const,
          data: {
            text: result.text,
            pages: result.pages,
            totalPages: result.totalPages,
            metadata: result.metadata,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to extract text from PDF');
        const message = error instanceof Error ? error.message : 'Unknown error';
        
        // Check for common PDF parsing errors
        if (message.includes('Invalid PDF') || message.includes('Password')) {
          return reply.status(400).send({
            success: false,
            error: `Invalid or protected PDF: ${message}`,
            code: 'PDF_INVALID',
          });
        }

        return reply.status(500).send({
          success: false,
          error: `Failed to extract text: ${message}`,
          code: 'EXTRACTION_FAILED',
        });
      }
    }
  );

  /**
   * Extract text from uploaded PDF file
   */
  fastify.post(
    '/text/upload',
    {
      schema: {
        description: 'Extract text from an uploaded PDF file',
        tags: ['Extract'],
        consumes: ['multipart/form-data'],
        response: {
          200: ExtractTextResponseSchema,
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

        // Parse options from fields
        let pageNumbers: number[] | undefined;
        let preserveLayout = false;
        let includePageBreaks = false;

        // Options could be passed as query params or form fields
        const query = request.query as Record<string, string>;
        if (query.pageNumbers) {
          pageNumbers = query.pageNumbers.split(',').map(n => parseInt(n.trim(), 10));
        }
        if (query.preserveLayout === 'true') {
          preserveLayout = true;
        }
        if (query.includePageBreaks === 'true') {
          includePageBreaks = true;
        }

        const result = await extractorService.extractText({
          file: buffer,
          pageNumbers,
          preserveLayout,
          includePageBreaks,
        });

        return {
          success: true as const,
          data: {
            text: result.text,
            pages: result.pages,
            totalPages: result.totalPages,
            metadata: result.metadata,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to extract text from uploaded PDF');
        const message = error instanceof Error ? error.message : 'Unknown error';
        return reply.status(500).send({
          success: false,
          error: `Failed to extract text: ${message}`,
          code: 'EXTRACTION_FAILED',
        });
      }
    }
  );
}
