import puppeteer, { Browser, Page, PaperFormat, PDFOptions } from 'puppeteer';
import { config } from '../config';
import { sanitizerService } from './sanitizer.service';
import { templateService } from './template.service';
import {
  HtmlToPdfOptions,
  TemplateToPdfOptions,
  PageFormat,
  PageMargin,
} from '../types';

// Map our format names to Puppeteer formats
const FORMAT_MAP: Record<PageFormat, PaperFormat> = {
  A3: 'A3',
  A4: 'A4',
  A5: 'A5',
  Letter: 'Letter',
  Legal: 'Legal',
  Tabloid: 'Tabloid',
};

export class GeneratorService {
  private browser: Browser | null = null;
  private browserPromise: Promise<Browser> | null = null;

  /**
   * Initialize the Puppeteer browser instance
   * Uses lazy initialization and singleton pattern
   */
  private async getBrowser(): Promise<Browser> {
    if (this.browser && this.browser.connected) {
      return this.browser;
    }

    if (this.browserPromise) {
      return this.browserPromise;
    }

    this.browserPromise = puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu',
        '--font-render-hinting=none',
      ],
      timeout: config.pdf.puppeteerTimeout,
    });

    try {
      this.browser = await this.browserPromise;
      
      // Handle browser disconnection
      this.browser.on('disconnected', () => {
        this.browser = null;
        this.browserPromise = null;
      });

      return this.browser;
    } finally {
      this.browserPromise = null;
    }
  }

  /**
   * Generate PDF from HTML content
   */
  async generateFromHtml(options: HtmlToPdfOptions): Promise<{
    pdf: Buffer;
    pageCount: number;
  }> {
    // Sanitize HTML input
    const sanitizedHtml = sanitizerService.sanitizeHtml(options.html);

    const browser = await this.getBrowser();
    const page = await browser.newPage();

    try {
      // Set viewport for consistent rendering
      await page.setViewport({
        width: 1200,
        height: 800,
        deviceScaleFactor: 2,
      });

      // Set content with wait for resources
      await page.setContent(sanitizedHtml, {
        waitUntil: ['domcontentloaded', 'networkidle0'],
        timeout: config.pdf.puppeteerTimeout,
      });

      // Build PDF options
      const pdfOptions = this.buildPdfOptions(options);

      // Generate PDF
      const pdfBuffer = await page.pdf(pdfOptions);

      // Get page count by re-parsing (Puppeteer doesn't return this)
      const pageCount = await this.countPdfPages(Buffer.from(pdfBuffer));

      return {
        pdf: Buffer.from(pdfBuffer),
        pageCount,
      };
    } finally {
      await page.close();
    }
  }

  /**
   * Generate PDF from Handlebars template
   */
  async generateFromTemplate(options: TemplateToPdfOptions): Promise<{
    pdf: Buffer;
    pageCount: number;
  }> {
    // Parse helpers from string if provided
    let helpers: Record<string, (...args: unknown[]) => unknown> | undefined;
    if (options.helpers) {
      helpers = {};
      for (const [name, fnStr] of Object.entries(options.helpers)) {
        try {
          // Note: This is intentionally limited for security
          // Only simple expressions are supported
          helpers[name] = new Function('return ' + fnStr)();
        } catch {
          // Skip invalid helper functions
        }
      }
    }

    // Render template
    const html = templateService.render(options.template, options.data, {
      helpers,
      partials: options.partials,
    });

    // Generate PDF from rendered HTML
    return this.generateFromHtml({
      html,
      format: options.format,
      orientation: options.orientation,
      margin: options.margin,
      printBackground: options.printBackground,
    });
  }

  /**
   * Build Puppeteer PDF options from our options
   */
  private buildPdfOptions(options: HtmlToPdfOptions): PDFOptions {
    const format = options.format || config.pdf.defaultFormat;
    const margin = this.buildMargin(options.margin);

    const pdfOptions: PDFOptions = {
      format: FORMAT_MAP[format] || 'A4',
      landscape: options.orientation === 'landscape',
      margin,
      printBackground: options.printBackground !== false, // Default true
      displayHeaderFooter: options.displayHeaderFooter || false,
      scale: options.scale || 1,
      preferCSSPageSize: options.preferCSSPageSize || false,
    };

    if (options.displayHeaderFooter) {
      if (options.headerTemplate) {
        pdfOptions.headerTemplate = sanitizerService.sanitizeHtml(options.headerTemplate);
      }
      if (options.footerTemplate) {
        pdfOptions.footerTemplate = sanitizerService.sanitizeHtml(options.footerTemplate);
      }
    }

    if (options.pageRanges) {
      pdfOptions.pageRanges = options.pageRanges;
    }

    return pdfOptions;
  }

  /**
   * Build margin object
   */
  private buildMargin(margin?: PageMargin): PDFOptions['margin'] {
    const defaultMargin = config.pdf.defaultMargin;
    return {
      top: margin?.top || defaultMargin.top,
      right: margin?.right || defaultMargin.right,
      bottom: margin?.bottom || defaultMargin.bottom,
      left: margin?.left || defaultMargin.left,
    };
  }

  /**
   * Count pages in a PDF buffer using a simple method
   * (We'll use pdf-lib for more accurate counting in pdf.service)
   */
  private async countPdfPages(buffer: Buffer): Promise<number> {
    // Simple regex-based page count (works for most PDFs)
    const pdfString = buffer.toString('binary');
    const matches = pdfString.match(/\/Type\s*\/Page[^s]/g);
    return matches ? matches.length : 1;
  }

  /**
   * Check if browser is ready
   */
  async isReady(): Promise<boolean> {
    try {
      const browser = await this.getBrowser();
      return browser.connected;
    } catch {
      return false;
    }
  }

  /**
   * Get browser health info
   */
  async getHealthInfo(): Promise<{
    ready: boolean;
    pages: number;
    version: string;
  }> {
    try {
      const browser = await this.getBrowser();
      const pages = await browser.pages();
      const version = await browser.version();
      return {
        ready: browser.connected,
        pages: pages.length,
        version,
      };
    } catch (error) {
      return {
        ready: false,
        pages: 0,
        version: 'unknown',
      };
    }
  }

  /**
   * Close browser instance
   */
  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      this.browserPromise = null;
    }
  }
}

export const generatorService = new GeneratorService();
