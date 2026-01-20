import * as pdfjs from 'pdfjs-dist';
import {
  ExtractTextOptions,
  ExtractedText,
  PageText,
  PdfMetadata,
} from '../types';

// Set up the worker for pdfjs (required for Node.js)
// The worker file will be bundled with the package
const pdfjsWorker = require('pdfjs-dist/build/pdf.worker.mjs');
pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export class ExtractorService {
  /**
   * Extract text from a PDF
   */
  async extractText(options: ExtractTextOptions): Promise<ExtractedText> {
    // Convert input to Uint8Array
    const data = this.toUint8Array(options.file);

    // Load the PDF document
    const loadingTask = pdfjs.getDocument({
      data,
      useSystemFonts: true,
      disableFontFace: true,
    });

    const pdf = await loadingTask.promise;

    // Get metadata
    const metadata = await this.extractMetadata(pdf);

    // Determine which pages to extract
    const totalPages = pdf.numPages;
    const pagesToExtract = options.pageNumbers?.length
      ? options.pageNumbers.filter(p => p >= 1 && p <= totalPages)
      : Array.from({ length: totalPages }, (_, i) => i + 1);

    // Extract text from each page
    const pages: PageText[] = [];
    const textParts: string[] = [];

    for (const pageNum of pagesToExtract) {
      const page = await pdf.getPage(pageNum);
      const textContent = await page.getTextContent();

      // Process text items
      let pageText: string;
      let lines: string[] | undefined;

      if (options.preserveLayout) {
        const result = this.processTextWithLayout(textContent);
        pageText = result.text;
        lines = result.lines;
      } else {
        pageText = this.processTextSimple(textContent);
        lines = pageText.split('\n').filter(line => line.trim());
      }

      pages.push({
        pageNumber: pageNum,
        text: pageText,
        lines,
      });

      textParts.push(pageText);

      if (options.includePageBreaks && pageNum !== pagesToExtract[pagesToExtract.length - 1]) {
        textParts.push('\n--- Page Break ---\n');
      }
    }

    return {
      text: textParts.join('\n'),
      pages,
      totalPages,
      metadata,
    };
  }

  /**
   * Extract metadata from a PDF
   */
  private async extractMetadata(pdf: pdfjs.PDFDocumentProxy): Promise<PdfMetadata> {
    try {
      const metadataObj = await pdf.getMetadata();
      const info = metadataObj.info as Record<string, unknown>;

      return {
        title: this.getString(info.Title),
        author: this.getString(info.Author),
        subject: this.getString(info.Subject),
        keywords: this.parseKeywords(this.getString(info.Keywords)),
        creator: this.getString(info.Creator),
        producer: this.getString(info.Producer),
        creationDate: this.parseDate(this.getString(info.CreationDate)),
        modificationDate: this.parseDate(this.getString(info.ModDate)),
      };
    } catch {
      return {};
    }
  }

  /**
   * Process text content with layout preservation
   */
  private processTextWithLayout(textContent: pdfjs.TextContent): {
    text: string;
    lines: string[];
  } {
    const items = textContent.items as pdfjs.TextItem[];
    
    if (items.length === 0) {
      return { text: '', lines: [] };
    }

    // Sort items by vertical position (y), then horizontal (x)
    const sortedItems = [...items].sort((a, b) => {
      const yDiff = b.transform[5] - a.transform[5]; // y is inverted
      if (Math.abs(yDiff) > 2) return yDiff;
      return a.transform[4] - b.transform[4]; // x position
    });

    const lines: string[] = [];
    let currentLine: string[] = [];
    let lastY = sortedItems[0]?.transform[5] || 0;
    let lastX = 0;

    for (const item of sortedItems) {
      const y = item.transform[5];
      const x = item.transform[4];
      const text = item.str;

      // Check if we're on a new line
      if (Math.abs(y - lastY) > 5) {
        if (currentLine.length > 0) {
          lines.push(currentLine.join(''));
          currentLine = [];
        }
        lastX = 0;
      }

      // Add spacing if there's a gap
      if (currentLine.length > 0 && x - lastX > 10) {
        currentLine.push(' ');
      }

      currentLine.push(text);
      lastY = y;
      lastX = x + (item.width || text.length * 6);
    }

    // Don't forget the last line
    if (currentLine.length > 0) {
      lines.push(currentLine.join(''));
    }

    return {
      text: lines.join('\n'),
      lines,
    };
  }

  /**
   * Process text content simply (concatenate all text)
   */
  private processTextSimple(textContent: pdfjs.TextContent): string {
    const items = textContent.items as pdfjs.TextItem[];
    const textParts: string[] = [];

    for (const item of items) {
      if (item.str) {
        textParts.push(item.str);
        // Add space if item has end-of-line flag
        if (item.hasEOL) {
          textParts.push('\n');
        }
      }
    }

    return textParts.join(' ').replace(/\s+/g, ' ').trim();
  }

  /**
   * Convert input to Uint8Array
   */
  private toUint8Array(input: Buffer | string): Uint8Array {
    if (Buffer.isBuffer(input)) {
      return new Uint8Array(input);
    }
    // Assume base64 string
    const buffer = Buffer.from(input, 'base64');
    return new Uint8Array(buffer);
  }

  /**
   * Safely get string value
   */
  private getString(value: unknown): string | undefined {
    if (typeof value === 'string') {
      return value;
    }
    return undefined;
  }

  /**
   * Parse keywords string into array
   */
  private parseKeywords(keywords?: string): string[] | undefined {
    if (!keywords) return undefined;
    return keywords.split(/[,;]/).map(k => k.trim()).filter(Boolean);
  }

  /**
   * Parse PDF date string (format: D:YYYYMMDDHHmmSSOHH'mm')
   */
  private parseDate(dateStr?: string): Date | undefined {
    if (!dateStr) return undefined;

    // Remove "D:" prefix if present
    const cleaned = dateStr.replace(/^D:/, '');

    // Try to parse PDF date format
    const match = cleaned.match(/^(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?/);
    if (!match) return undefined;

    const year = parseInt(match[1], 10);
    const month = parseInt(match[2] || '1', 10) - 1;
    const day = parseInt(match[3] || '1', 10);
    const hour = parseInt(match[4] || '0', 10);
    const minute = parseInt(match[5] || '0', 10);
    const second = parseInt(match[6] || '0', 10);

    return new Date(year, month, day, hour, minute, second);
  }
}

export const extractorService = new ExtractorService();
