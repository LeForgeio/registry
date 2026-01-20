import { Type, Static } from '@sinclair/typebox';

// ============ Common Schemas ============

export const PageFormatSchema = Type.Union([
  Type.Literal('A4'),
  Type.Literal('A3'),
  Type.Literal('A5'),
  Type.Literal('Letter'),
  Type.Literal('Legal'),
  Type.Literal('Tabloid'),
]);

export const PageOrientationSchema = Type.Union([
  Type.Literal('portrait'),
  Type.Literal('landscape'),
]);

export const PageMarginSchema = Type.Object({
  top: Type.Optional(Type.String()),
  right: Type.Optional(Type.String()),
  bottom: Type.Optional(Type.String()),
  left: Type.Optional(Type.String()),
});

export const PdfMetadataSchema = Type.Object({
  title: Type.Optional(Type.String()),
  author: Type.Optional(Type.String()),
  subject: Type.Optional(Type.String()),
  keywords: Type.Optional(Type.Array(Type.String())),
  creator: Type.Optional(Type.String()),
  producer: Type.Optional(Type.String()),
});

export const ErrorResponseSchema = Type.Object({
  success: Type.Literal(false),
  error: Type.String(),
  code: Type.Optional(Type.String()),
  details: Type.Optional(Type.Unknown()),
});

// ============ Generate HTML to PDF ============

export const GenerateHtmlRequestSchema = Type.Object({
  html: Type.String({ description: 'HTML content to convert to PDF' }),
  format: Type.Optional(PageFormatSchema),
  orientation: Type.Optional(PageOrientationSchema),
  margin: Type.Optional(PageMarginSchema),
  printBackground: Type.Optional(Type.Boolean({ default: true })),
  displayHeaderFooter: Type.Optional(Type.Boolean({ default: false })),
  headerTemplate: Type.Optional(Type.String()),
  footerTemplate: Type.Optional(Type.String()),
  scale: Type.Optional(Type.Number({ minimum: 0.1, maximum: 2, default: 1 })),
  pageRanges: Type.Optional(Type.String({ description: 'e.g., "1-3,5,7-9"' })),
  preferCSSPageSize: Type.Optional(Type.Boolean({ default: false })),
});

export const GeneratePdfResponseSchema = Type.Object({
  success: Type.Literal(true),
  data: Type.Object({
    pdf: Type.String({ description: 'Base64 encoded PDF' }),
    filename: Type.String(),
    size: Type.Number(),
    pages: Type.Number(),
  }),
});

export type GenerateHtmlRequest = Static<typeof GenerateHtmlRequestSchema>;
export type GeneratePdfResponse = Static<typeof GeneratePdfResponseSchema>;

// ============ Generate Template to PDF ============

export const GenerateTemplateRequestSchema = Type.Object({
  template: Type.String({ description: 'Handlebars template' }),
  data: Type.Record(Type.String(), Type.Unknown(), { description: 'Template data' }),
  format: Type.Optional(PageFormatSchema),
  orientation: Type.Optional(PageOrientationSchema),
  margin: Type.Optional(PageMarginSchema),
  printBackground: Type.Optional(Type.Boolean({ default: true })),
  helpers: Type.Optional(Type.Record(Type.String(), Type.String())),
  partials: Type.Optional(Type.Record(Type.String(), Type.String())),
});

export type GenerateTemplateRequest = Static<typeof GenerateTemplateRequestSchema>;

// ============ Merge PDFs ============

export const MergePdfFileSchema = Type.Object({
  data: Type.String({ description: 'Base64 encoded PDF' }),
  filename: Type.Optional(Type.String()),
  pageRanges: Type.Optional(Type.String({ description: 'e.g., "1-3,5,7-9"' })),
});

export const MergePdfRequestSchema = Type.Object({
  files: Type.Array(MergePdfFileSchema, { minItems: 2 }),
  metadata: Type.Optional(PdfMetadataSchema),
});

export const MergePdfResponseSchema = Type.Object({
  success: Type.Literal(true),
  data: Type.Object({
    pdf: Type.String({ description: 'Base64 encoded PDF' }),
    filename: Type.String(),
    size: Type.Number(),
    pages: Type.Number(),
    mergedCount: Type.Number(),
  }),
});

export type MergePdfRequest = Static<typeof MergePdfRequestSchema>;
export type MergePdfResponse = Static<typeof MergePdfResponseSchema>;

// ============ Extract Text ============

export const ExtractTextRequestSchema = Type.Object({
  file: Type.String({ description: 'Base64 encoded PDF' }),
  pageNumbers: Type.Optional(Type.Array(Type.Number({ minimum: 1 }))),
  preserveLayout: Type.Optional(Type.Boolean({ default: false })),
  includePageBreaks: Type.Optional(Type.Boolean({ default: false })),
});

export const PageTextSchema = Type.Object({
  pageNumber: Type.Number(),
  text: Type.String(),
  lines: Type.Optional(Type.Array(Type.String())),
});

export const ExtractTextResponseSchema = Type.Object({
  success: Type.Literal(true),
  data: Type.Object({
    text: Type.String(),
    pages: Type.Array(PageTextSchema),
    totalPages: Type.Number(),
    metadata: Type.Optional(PdfMetadataSchema),
  }),
});

export type ExtractTextRequest = Static<typeof ExtractTextRequestSchema>;
export type ExtractTextResponse = Static<typeof ExtractTextResponseSchema>;

// ============ Fill Form ============

export const FormFieldTypeSchema = Type.Union([
  Type.Literal('text'),
  Type.Literal('checkbox'),
  Type.Literal('radio'),
  Type.Literal('dropdown'),
  Type.Literal('signature'),
]);

export const FormFieldSchema = Type.Object({
  name: Type.String(),
  type: FormFieldTypeSchema,
  value: Type.Union([Type.String(), Type.Boolean()]),
  page: Type.Optional(Type.Number()),
});

export const FillFormRequestSchema = Type.Object({
  file: Type.String({ description: 'Base64 encoded PDF' }),
  fields: Type.Array(FormFieldSchema, { minItems: 1 }),
  flatten: Type.Optional(Type.Boolean({ default: false })),
});

export const FillFormResponseSchema = Type.Object({
  success: Type.Literal(true),
  data: Type.Object({
    pdf: Type.String({ description: 'Base64 encoded PDF' }),
    filename: Type.String(),
    size: Type.Number(),
    filledFields: Type.Number(),
  }),
});

export type FillFormRequest = Static<typeof FillFormRequestSchema>;
export type FillFormResponse = Static<typeof FillFormResponseSchema>;

// ============ PDF Info ============

export const PdfInfoRequestSchema = Type.Object({
  file: Type.String({ description: 'Base64 encoded PDF' }),
});

export const FormFieldInfoSchema = Type.Object({
  name: Type.String(),
  type: FormFieldTypeSchema,
  required: Type.Boolean(),
  readOnly: Type.Boolean(),
  options: Type.Optional(Type.Array(Type.String())),
  defaultValue: Type.Optional(Type.Union([Type.String(), Type.Boolean()])),
});

export const PdfInfoResponseSchema = Type.Object({
  success: Type.Literal(true),
  data: Type.Object({
    pageCount: Type.Number(),
    metadata: PdfMetadataSchema,
    isEncrypted: Type.Boolean(),
    hasForm: Type.Boolean(),
    formFields: Type.Optional(Type.Array(FormFieldInfoSchema)),
    fileSize: Type.Number(),
  }),
});

export type PdfInfoRequest = Static<typeof PdfInfoRequestSchema>;
export type PdfInfoResponse = Static<typeof PdfInfoResponseSchema>;

// ============ Health Check ============

export const ComponentHealthSchema = Type.Object({
  status: Type.Union([Type.Literal('healthy'), Type.Literal('unhealthy')]),
  message: Type.Optional(Type.String()),
  latency: Type.Optional(Type.Number()),
});

export const HealthResponseSchema = Type.Object({
  status: Type.Union([
    Type.Literal('healthy'),
    Type.Literal('unhealthy'),
    Type.Literal('degraded'),
  ]),
  timestamp: Type.String(),
  uptime: Type.Number(),
  version: Type.String(),
  checks: Type.Object({
    puppeteer: ComponentHealthSchema,
    tempDirectory: ComponentHealthSchema,
    memory: ComponentHealthSchema,
  }),
});

export type HealthResponse = Static<typeof HealthResponseSchema>;
