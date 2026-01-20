import { PDFDocument, PDFForm, PDFTextField, PDFCheckBox, PDFDropdown, PDFRadioGroup } from 'pdf-lib';
import * as fs from 'fs/promises';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { config } from '../config';
import {
  MergePdfOptions,
  FillFormOptions,
  PdfInfo,
  PdfMetadata,
  FormFieldInfo,
  FormField,
} from '../types';

export class PdfService {
  private tempDir: string;

  constructor() {
    this.tempDir = config.pdf.tempDir;
    this.ensureTempDir();
  }

  /**
   * Ensure temp directory exists
   */
  private async ensureTempDir(): Promise<void> {
    try {
      await fs.mkdir(this.tempDir, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }
  }

  /**
   * Merge multiple PDF files into one
   */
  async mergePdfs(options: MergePdfOptions): Promise<{
    pdf: Buffer;
    pageCount: number;
    mergedCount: number;
  }> {
    // Validate file count
    if (options.files.length > config.pdf.maxMergeFiles) {
      throw new Error(`Maximum ${config.pdf.maxMergeFiles} files can be merged at once`);
    }

    // Create a new PDF document
    const mergedPdf = await PDFDocument.create();

    let totalPages = 0;
    let mergedCount = 0;

    for (const file of options.files) {
      try {
        // Load the source PDF
        const sourceData = this.toBuffer(file.data);
        const sourcePdf = await PDFDocument.load(sourceData, {
          ignoreEncryption: true,
        });

        // Determine which pages to copy
        const pageCount = sourcePdf.getPageCount();
        const pagesToCopy = this.parsePageRanges(file.pageRanges, pageCount);

        // Copy pages
        const copiedPages = await mergedPdf.copyPages(sourcePdf, pagesToCopy);
        for (const page of copiedPages) {
          mergedPdf.addPage(page);
          totalPages++;
        }

        mergedCount++;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        throw new Error(`Failed to process PDF ${file.filename || mergedCount + 1}: ${message}`);
      }
    }

    // Set metadata if provided
    if (options.metadata) {
      this.setMetadata(mergedPdf, options.metadata);
    }

    // Save the merged PDF
    const pdfBytes = await mergedPdf.save();

    return {
      pdf: Buffer.from(pdfBytes),
      pageCount: totalPages,
      mergedCount,
    };
  }

  /**
   * Fill form fields in a PDF
   */
  async fillForm(options: FillFormOptions): Promise<{
    pdf: Buffer;
    filledFields: number;
  }> {
    // Load the PDF
    const sourceData = this.toBuffer(options.file);
    const pdfDoc = await PDFDocument.load(sourceData, {
      ignoreEncryption: true,
    });

    const form = pdfDoc.getForm();
    let filledFields = 0;

    for (const field of options.fields) {
      try {
        const filled = this.fillFormField(form, field);
        if (filled) filledFields++;
      } catch (error) {
        // Field might not exist or be incompatible type
        console.warn(`Could not fill field "${field.name}": ${error}`);
      }
    }

    // Flatten the form if requested
    if (options.flatten) {
      form.flatten();
    }

    // Save the PDF
    const pdfBytes = await pdfDoc.save();

    return {
      pdf: Buffer.from(pdfBytes),
      filledFields,
    };
  }

  /**
   * Get information about a PDF
   */
  async getInfo(file: Buffer | string): Promise<PdfInfo> {
    const data = this.toBuffer(file);
    const pdfDoc = await PDFDocument.load(data, {
      ignoreEncryption: true,
    });

    const form = pdfDoc.getForm();
    const fields = form.getFields();

    const formFields: FormFieldInfo[] = fields.map(field => {
      const name = field.getName();
      const type = this.getFieldType(field);
      
      let options: string[] | undefined;
      if (field instanceof PDFDropdown) {
        options = field.getOptions();
      }

      return {
        name,
        type,
        required: false, // pdf-lib doesn't expose this
        readOnly: field.isReadOnly(),
        options,
      };
    });

    return {
      pageCount: pdfDoc.getPageCount(),
      metadata: {
        title: pdfDoc.getTitle(),
        author: pdfDoc.getAuthor(),
        subject: pdfDoc.getSubject(),
        keywords: pdfDoc.getKeywords()?.split(',').map(k => k.trim()),
        creator: pdfDoc.getCreator(),
        producer: pdfDoc.getProducer(),
        creationDate: pdfDoc.getCreationDate(),
        modificationDate: pdfDoc.getModificationDate(),
      },
      isEncrypted: false, // We're ignoring encryption
      hasForm: fields.length > 0,
      formFields: fields.length > 0 ? formFields : undefined,
      fileSize: data.length,
    };
  }

  /**
   * Create a new PDF from scratch
   */
  async createBlankPdf(options?: {
    pages?: number;
    width?: number;
    height?: number;
    metadata?: PdfMetadata;
  }): Promise<Buffer> {
    const pdfDoc = await PDFDocument.create();
    const pageCount = options?.pages || 1;
    const width = options?.width || 595.28; // A4 width in points
    const height = options?.height || 841.89; // A4 height in points

    for (let i = 0; i < pageCount; i++) {
      pdfDoc.addPage([width, height]);
    }

    if (options?.metadata) {
      this.setMetadata(pdfDoc, options.metadata);
    }

    const pdfBytes = await pdfDoc.save();
    return Buffer.from(pdfBytes);
  }

  /**
   * Save a PDF to a temporary file
   * Returns the file path
   */
  async saveToTemp(pdf: Buffer, prefix: string = 'pdf'): Promise<string> {
    await this.ensureTempDir();
    const filename = `${prefix}-${uuidv4()}.pdf`;
    const filepath = path.join(this.tempDir, filename);
    await fs.writeFile(filepath, pdf);
    return filepath;
  }

  /**
   * Clean up a temporary file
   */
  async cleanupTemp(filepath: string): Promise<void> {
    try {
      // Only delete if it's in our temp directory
      if (filepath.startsWith(this.tempDir)) {
        await fs.unlink(filepath);
      }
    } catch (error) {
      // File might not exist
    }
  }

  /**
   * Clean up old temporary files
   * Removes files older than maxAge milliseconds
   */
  async cleanupOldTempFiles(maxAge: number = 3600000): Promise<number> {
    try {
      const files = await fs.readdir(this.tempDir);
      const now = Date.now();
      let cleaned = 0;

      for (const file of files) {
        const filepath = path.join(this.tempDir, file);
        try {
          const stats = await fs.stat(filepath);
          if (now - stats.mtimeMs > maxAge) {
            await fs.unlink(filepath);
            cleaned++;
          }
        } catch {
          // Skip files we can't access
        }
      }

      return cleaned;
    } catch {
      return 0;
    }
  }

  /**
   * Fill a single form field
   */
  private fillFormField(form: PDFForm, field: FormField): boolean {
    const { name, type, value } = field;

    switch (type) {
      case 'text': {
        const textField = form.getTextField(name);
        if (textField && typeof value === 'string') {
          textField.setText(value);
          return true;
        }
        break;
      }
      case 'checkbox': {
        const checkbox = form.getCheckBox(name);
        if (checkbox) {
          if (value === true || value === 'true' || value === 'yes' || value === '1') {
            checkbox.check();
          } else {
            checkbox.uncheck();
          }
          return true;
        }
        break;
      }
      case 'dropdown': {
        const dropdown = form.getDropdown(name);
        if (dropdown && typeof value === 'string') {
          dropdown.select(value);
          return true;
        }
        break;
      }
      case 'radio': {
        const radioGroup = form.getRadioGroup(name);
        if (radioGroup && typeof value === 'string') {
          radioGroup.select(value);
          return true;
        }
        break;
      }
    }

    return false;
  }

  /**
   * Get the type of a form field
   */
  private getFieldType(field: ReturnType<PDFForm['getFields']>[0]): FormFieldInfo['type'] {
    if (field instanceof PDFTextField) return 'text';
    if (field instanceof PDFCheckBox) return 'checkbox';
    if (field instanceof PDFDropdown) return 'dropdown';
    if (field instanceof PDFRadioGroup) return 'radio';
    return 'text';
  }

  /**
   * Set PDF metadata
   */
  private setMetadata(pdfDoc: PDFDocument, metadata: PdfMetadata): void {
    if (metadata.title) pdfDoc.setTitle(metadata.title);
    if (metadata.author) pdfDoc.setAuthor(metadata.author);
    if (metadata.subject) pdfDoc.setSubject(metadata.subject);
    if (metadata.keywords) pdfDoc.setKeywords(metadata.keywords);
    if (metadata.creator) pdfDoc.setCreator(metadata.creator);
    if (metadata.producer) pdfDoc.setProducer(metadata.producer);
    if (metadata.creationDate) pdfDoc.setCreationDate(metadata.creationDate);
    if (metadata.modificationDate) pdfDoc.setModificationDate(metadata.modificationDate);
  }

  /**
   * Parse page ranges string into array of page indices
   * e.g., "1-3,5,7-9" -> [0, 1, 2, 4, 6, 7, 8]
   */
  private parsePageRanges(rangesStr: string | undefined, totalPages: number): number[] {
    if (!rangesStr) {
      return Array.from({ length: totalPages }, (_, i) => i);
    }

    const pages = new Set<number>();
    const ranges = rangesStr.split(',');

    for (const range of ranges) {
      const trimmed = range.trim();
      if (trimmed.includes('-')) {
        const [start, end] = trimmed.split('-').map(n => parseInt(n.trim(), 10));
        for (let i = start; i <= end && i <= totalPages; i++) {
          if (i >= 1) pages.add(i - 1); // Convert to 0-based index
        }
      } else {
        const page = parseInt(trimmed, 10);
        if (page >= 1 && page <= totalPages) {
          pages.add(page - 1); // Convert to 0-based index
        }
      }
    }

    return Array.from(pages).sort((a, b) => a - b);
  }

  /**
   * Convert input to Buffer
   */
  private toBuffer(input: Buffer | string): Buffer {
    if (Buffer.isBuffer(input)) {
      return input;
    }
    // Assume base64 string
    return Buffer.from(input, 'base64');
  }
}

export const pdfService = new PdfService();
