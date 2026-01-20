import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { generatorService } from '../services';
import { sanitizerService } from '../services';
import {
  GenerateHtmlRequestSchema,
  GeneratePdfResponseSchema,
  GenerateTemplateRequestSchema,
  ErrorResponseSchema,
  GenerateHtmlRequest,
  GenerateTemplateRequest,
} from '../schemas';
import { config } from '../config';

export async function generateRoutes(fastify: FastifyInstance): Promise<void> {
  /**
   * Generate PDF from HTML
   */
  fastify.post<{ Body: GenerateHtmlRequest }>(
    '/html',
    {
      schema: {
        description: 'Generate a PDF from HTML content',
        tags: ['Generate'],
        body: GenerateHtmlRequestSchema,
        response: {
          200: GeneratePdfResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { html, ...options } = request.body;

      // Validate HTML size
      if (html.length > config.pdf.maxFileSize) {
        return reply.status(400).send({
          success: false,
          error: 'HTML content exceeds maximum size',
          code: 'HTML_TOO_LARGE',
        });
      }

      // Analyze HTML for potential issues
      const warnings = sanitizerService.analyzeHtml(html);
      if (warnings.length > 0) {
        request.log.info({ warnings }, 'HTML content contains elements that will be sanitized');
      }

      try {
        const result = await generatorService.generateFromHtml({
          html,
          ...options,
        });

        const base64Pdf = result.pdf.toString('base64');
        const filename = `generated-${Date.now()}.pdf`;

        return {
          success: true as const,
          data: {
            pdf: base64Pdf,
            filename,
            size: result.pdf.length,
            pages: result.pageCount,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to generate PDF from HTML');
        const message = error instanceof Error ? error.message : 'Unknown error';
        return reply.status(500).send({
          success: false,
          error: `Failed to generate PDF: ${message}`,
          code: 'GENERATION_FAILED',
        });
      }
    }
  );

  /**
   * Generate PDF from Handlebars template
   */
  fastify.post<{ Body: GenerateTemplateRequest }>(
    '/template',
    {
      schema: {
        description: 'Generate a PDF from a Handlebars template with data',
        tags: ['Generate'],
        body: GenerateTemplateRequestSchema,
        response: {
          200: GeneratePdfResponseSchema,
          400: ErrorResponseSchema,
          500: ErrorResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { template, data, helpers, partials, ...options } = request.body;

      // Validate template size
      if (template.length > config.pdf.maxFileSize) {
        return reply.status(400).send({
          success: false,
          error: 'Template exceeds maximum size',
          code: 'TEMPLATE_TOO_LARGE',
        });
      }

      try {
        const result = await generatorService.generateFromTemplate({
          template,
          data,
          helpers,
          partials,
          ...options,
        });

        const base64Pdf = result.pdf.toString('base64');
        const filename = `generated-${Date.now()}.pdf`;

        return {
          success: true as const,
          data: {
            pdf: base64Pdf,
            filename,
            size: result.pdf.length,
            pages: result.pageCount,
          },
        };
      } catch (error) {
        request.log.error({ error }, 'Failed to generate PDF from template');
        const message = error instanceof Error ? error.message : 'Unknown error';
        
        // Check if it's a template error
        if (message.includes('Parse error') || message.includes('Expecting')) {
          return reply.status(400).send({
            success: false,
            error: `Template error: ${message}`,
            code: 'TEMPLATE_INVALID',
          });
        }

        return reply.status(500).send({
          success: false,
          error: `Failed to generate PDF: ${message}`,
          code: 'GENERATION_FAILED',
        });
      }
    }
  );
}
