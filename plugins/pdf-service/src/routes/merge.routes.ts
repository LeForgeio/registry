import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { pdfService } from '../services';
import {
  MergePdfRequestSchema,
  MergePdfResponseSchema,
  ErrorResponseSchema,
  MergePdfRequest,
} from '../schemas';
import { config } from '../config';

export async function mergeRoutes(fastify: FastifyInstance): Promise<void> {
  /**
   * Merge multiple PDFs into one
   */
  fastify.post<{ Body: MergePdfRequest }>(
    '/',
    {
      schema: {
        description: 'Merge multiple PDF files into a single PDF',
        tags: ['Merge'],
        body: MergePdfRequestSchema,
        response: {
          200: MergePdfResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { files, metadata } = request.body;

      // Validate file count
      if (files.length < 2) {
        return reply.status(400).send({
          success: false,
          error: 'At least 2 files are required for merging',
          code: 'INSUFFICIENT_FILES',
        });
      }

      if (files.length > config.pdf.maxMergeFiles) {
        return reply.status(400).send({
          success: false,
          error: `Maximum ${config.pdf.maxMergeFiles} files can be merged at once`,
          code: 'TOO_MANY_FILES',
        });
      }

      // Validate individual file sizes
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        // Base64 is ~33% larger than binary, so check accordingly
        const estimatedSize = Math.ceil(file.data.length * 0.75);
        if (estimatedSize > config.pdf.maxFileSize) {
          return reply.status(400).send({
            success: false,
            error: `File ${i + 1} exceeds maximum size of ${config.pdf.maxFileSize} bytes`,
            code: 'FILE_TOO_LARGE',
          });
        }
      }

      try {
        const result = await pdfService.mergePdfs({
          files: files.map(f => ({
            data: f.data,
            filename: f.filename,
            pageRanges: f.pageRanges,
          })),
          metadata,
        });

        const base64Pdf = result.pdf.toString('base64');
        const filename = `merged-${Date.now()}.pdf`;

        return {
          success: true as const,
          data: {
            pdf: base64Pdf,
            filename,
            size: result.pdf.length,
            pages: result.pageCount,
            mergedCount: result.mergedCount,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to merge PDFs');
        const message = error instanceof Error ? error.message : 'Unknown error';
        return reply.status(500).send({
          success: false,
          error: `Failed to merge PDFs: ${message}`,
          code: 'MERGE_FAILED',
        });
      }
    }
  );

  /**
   * Merge PDFs via multipart/form-data (file upload)
   */
  fastify.post(
    '/upload',
    {
      schema: {
        description: 'Merge multiple PDF files uploaded via multipart/form-data',
        tags: ['Merge'],
        consumes: ['multipart/form-data'],
        response: {
          200: MergePdfResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      try {
        const parts = request.parts();
        const files: { data: Buffer; filename?: string }[] = [];
        let metadata: Record<string, string> | undefined;

        for await (const part of parts) {
          if (part.type === 'file') {
            // Validate content type
            if (part.mimetype !== 'application/pdf') {
              return reply.status(400).send({
                success: false,
                error: `File "${part.filename}" is not a PDF`,
                code: 'INVALID_FILE_TYPE',
              });
            }

            // Read file data
            const chunks: Buffer[] = [];
            for await (const chunk of part.file) {
              chunks.push(chunk);
            }
            const buffer = Buffer.concat(chunks);

            // Validate size
            if (buffer.length > config.pdf.maxFileSize) {
              return reply.status(400).send({
                success: false,
                error: `File "${part.filename}" exceeds maximum size`,
                code: 'FILE_TOO_LARGE',
              });
            }

            files.push({
              data: buffer,
              filename: part.filename,
            });
          } else if (part.fieldname === 'metadata') {
            try {
              metadata = JSON.parse(part.value as string);
            } catch {
              // Ignore invalid metadata JSON
            }
          }
        }

        // Validate file count
        if (files.length < 2) {
          return reply.status(400).send({
            success: false,
            error: 'At least 2 files are required for merging',
            code: 'INSUFFICIENT_FILES',
          });
        }

        if (files.length > config.pdf.maxMergeFiles) {
          return reply.status(400).send({
            success: false,
            error: `Maximum ${config.pdf.maxMergeFiles} files can be merged at once`,
            code: 'TOO_MANY_FILES',
          });
        }

        const result = await pdfService.mergePdfs({
          files,
          metadata,
        });

        const base64Pdf = result.pdf.toString('base64');
        const filename = `merged-${Date.now()}.pdf`;

        return {
          success: true as const,
          data: {
            pdf: base64Pdf,
            filename,
            size: result.pdf.length,
            pages: result.pageCount,
            mergedCount: result.mergedCount,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to merge uploaded PDFs');
        const message = error instanceof Error ? error.message : 'Unknown error';
        return reply.status(500).send({
          success: false,
          error: `Failed to merge PDFs: ${message}`,
          code: 'MERGE_FAILED',
        });
      }
    }
  );
}
