// PDF page formats
export type PageFormat = 'A4' | 'A3' | 'A5' | 'Letter' | 'Legal' | 'Tabloid';

// PDF orientation
export type PageOrientation = 'portrait' | 'landscape';

// Margin configuration
export interface PageMargin {
  top?: string;
  right?: string;
  bottom?: string;
  left?: string;
}

// PDF generation options from HTML
export interface HtmlToPdfOptions {
  html: string;
  format?: PageFormat;
  orientation?: PageOrientation;
  margin?: PageMargin;
  printBackground?: boolean;
  displayHeaderFooter?: boolean;
  headerTemplate?: string;
  footerTemplate?: string;
  scale?: number;
  pageRanges?: string;
  preferCSSPageSize?: boolean;
}

// Template-based PDF generation
export interface TemplateToPdfOptions {
  template: string;
  data: Record<string, unknown>;
  format?: PageFormat;
  orientation?: PageOrientation;
  margin?: PageMargin;
  printBackground?: boolean;
  helpers?: Record<string, string>;
  partials?: Record<string, string>;
}

// PDF merge options
export interface MergePdfOptions {
  files: PdfFileInput[];
  metadata?: PdfMetadata;
}

// PDF file input (supports both base64 and multipart)
export interface PdfFileInput {
  data: Buffer | string; // Buffer for multipart, base64 string otherwise
  filename?: string;
  pageRanges?: string; // e.g., "1-3,5,7-9"
}

// PDF metadata
export interface PdfMetadata {
  title?: string;
  author?: string;
  subject?: string;
  keywords?: string[];
  creator?: string;
  producer?: string;
  creationDate?: Date;
  modificationDate?: Date;
}

// Text extraction options
export interface ExtractTextOptions {
  file: Buffer | string;
  pageNumbers?: number[]; // Extract from specific pages only
  preserveLayout?: boolean;
  includePageBreaks?: boolean;
}

// Extracted text result
export interface ExtractedText {
  text: string;
  pages: PageText[];
  totalPages: number;
  metadata?: PdfMetadata;
}

// Text from a single page
export interface PageText {
  pageNumber: number;
  text: string;
  lines?: string[];
}

// Form field types
export type FormFieldType = 'text' | 'checkbox' | 'radio' | 'dropdown' | 'signature';

// Form field definition
export interface FormField {
  name: string;
  type: FormFieldType;
  value: string | boolean;
  page?: number;
}

// Form fill options
export interface FillFormOptions {
  file: Buffer | string;
  fields: FormField[];
  flatten?: boolean; // Remove form fields and make the PDF non-editable
}

// PDF info
export interface PdfInfo {
  pageCount: number;
  metadata: PdfMetadata;
  isEncrypted: boolean;
  hasForm: boolean;
  formFields?: FormFieldInfo[];
  fileSize: number;
}

// Form field info
export interface FormFieldInfo {
  name: string;
  type: FormFieldType;
  required: boolean;
  readOnly: boolean;
  options?: string[]; // For dropdowns/radio buttons
  defaultValue?: string | boolean;
}

// API Response types
export interface GeneratePdfResponse {
  success: boolean;
  data?: {
    pdf: string; // base64 encoded
    filename: string;
    size: number;
    pages: number;
  };
  error?: string;
}

export interface MergePdfResponse {
  success: boolean;
  data?: {
    pdf: string; // base64 encoded
    filename: string;
    size: number;
    pages: number;
    mergedCount: number;
  };
  error?: string;
}

export interface ExtractTextResponse {
  success: boolean;
  data?: ExtractedText;
  error?: string;
}

export interface FillFormResponse {
  success: boolean;
  data?: {
    pdf: string; // base64 encoded
    filename: string;
    size: number;
    filledFields: number;
  };
  error?: string;
}

export interface PdfInfoResponse {
  success: boolean;
  data?: PdfInfo;
  error?: string;
}

// Health check types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  uptime: number;
  version: string;
  checks: {
    puppeteer: ComponentHealth;
    tempDirectory: ComponentHealth;
    memory: ComponentHealth;
  };
}

export interface ComponentHealth {
  status: 'healthy' | 'unhealthy';
  message?: string;
  latency?: number;
}
