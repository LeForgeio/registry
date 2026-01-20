import { PDFDocument, StandardFonts } from 'pdf-lib';
import { pdfService } from '../src/services/pdf.service';

describe('PdfService', () => {
  // Helper to create a simple test PDF
  async function createTestPdf(pages: number = 1, text?: string): Promise<Buffer> {
    const pdfDoc = await PDFDocument.create();
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    
    for (let i = 0; i < pages; i++) {
      const page = pdfDoc.addPage([612, 792]); // Letter size
      page.drawText(text || `Page ${i + 1}`, {
        x: 50,
        y: 700,
        size: 24,
        font,
      });
    }
    
    pdfDoc.setTitle('Test Document');
    pdfDoc.setAuthor('Test Author');
    
    const bytes = await pdfDoc.save();
    return Buffer.from(bytes);
  }

  // Helper to create a PDF with form fields
  async function createFormPdf(): Promise<Buffer> {
    const pdfDoc = await PDFDocument.create();
    const page = pdfDoc.addPage([612, 792]);
    const form = pdfDoc.getForm();
    
    // Create text field
    const textField = form.createTextField('name');
    textField.addToPage(page, { x: 50, y: 700, width: 200, height: 30 });
    
    // Create checkbox
    const checkbox = form.createCheckBox('agree');
    checkbox.addToPage(page, { x: 50, y: 650, width: 20, height: 20 });
    
    // Create dropdown
    const dropdown = form.createDropdown('color');
    dropdown.addOptions(['Red', 'Green', 'Blue']);
    dropdown.addToPage(page, { x: 50, y: 600, width: 200, height: 30 });
    
    const bytes = await pdfDoc.save();
    return Buffer.from(bytes);
  }

  describe('mergePdfs', () => {
    it('should merge two PDFs', async () => {
      const pdf1 = await createTestPdf(2, 'PDF 1');
      const pdf2 = await createTestPdf(3, 'PDF 2');
      
      const result = await pdfService.mergePdfs({
        files: [
          { data: pdf1, filename: 'pdf1.pdf' },
          { data: pdf2, filename: 'pdf2.pdf' },
        ],
      });
      
      expect(result.pdf).toBeInstanceOf(Buffer);
      expect(result.pageCount).toBe(5);
      expect(result.mergedCount).toBe(2);
    });

    it('should merge PDFs with base64 input', async () => {
      const pdf1 = await createTestPdf(1);
      const pdf2 = await createTestPdf(2);
      
      const result = await pdfService.mergePdfs({
        files: [
          { data: pdf1.toString('base64') },
          { data: pdf2.toString('base64') },
        ],
      });
      
      expect(result.pageCount).toBe(3);
      expect(result.mergedCount).toBe(2);
    });

    it('should merge with page ranges', async () => {
      const pdf1 = await createTestPdf(5);
      const pdf2 = await createTestPdf(3);
      
      const result = await pdfService.mergePdfs({
        files: [
          { data: pdf1, pageRanges: '1-2' }, // Only first 2 pages
          { data: pdf2, pageRanges: '2-3' }, // Only pages 2 and 3
        ],
      });
      
      expect(result.pageCount).toBe(4); // 2 + 2
    });

    it('should set metadata on merged PDF', async () => {
      const pdf1 = await createTestPdf(1);
      const pdf2 = await createTestPdf(1);
      
      const result = await pdfService.mergePdfs({
        files: [
          { data: pdf1 },
          { data: pdf2 },
        ],
        metadata: {
          title: 'Merged Document',
          author: 'Test User',
          subject: 'Test Subject',
          keywords: ['test', 'merge'],
        },
      });
      
      // Verify by loading the result
      const mergedDoc = await PDFDocument.load(result.pdf);
      expect(mergedDoc.getTitle()).toBe('Merged Document');
      expect(mergedDoc.getAuthor()).toBe('Test User');
      expect(mergedDoc.getSubject()).toBe('Test Subject');
      expect(mergedDoc.getKeywords()).toBe('test,merge');
    });

    it('should throw error for invalid PDF', async () => {
      const invalidPdf = Buffer.from('not a pdf');
      const validPdf = await createTestPdf(1);
      
      await expect(pdfService.mergePdfs({
        files: [
          { data: invalidPdf, filename: 'invalid.pdf' },
          { data: validPdf },
        ],
      })).rejects.toThrow();
    });
  });

  describe('fillForm', () => {
    it('should fill text field', async () => {
      const formPdf = await createFormPdf();
      
      const result = await pdfService.fillForm({
        file: formPdf,
        fields: [
          { name: 'name', type: 'text', value: 'John Doe' },
        ],
      });
      
      expect(result.pdf).toBeInstanceOf(Buffer);
      expect(result.filledFields).toBe(1);
    });

    it('should fill checkbox', async () => {
      const formPdf = await createFormPdf();
      
      const result = await pdfService.fillForm({
        file: formPdf,
        fields: [
          { name: 'agree', type: 'checkbox', value: true },
        ],
      });
      
      expect(result.filledFields).toBe(1);
    });

    it('should fill dropdown', async () => {
      const formPdf = await createFormPdf();
      
      const result = await pdfService.fillForm({
        file: formPdf,
        fields: [
          { name: 'color', type: 'dropdown', value: 'Green' },
        ],
      });
      
      expect(result.filledFields).toBe(1);
    });

    it('should fill multiple fields', async () => {
      const formPdf = await createFormPdf();
      
      const result = await pdfService.fillForm({
        file: formPdf,
        fields: [
          { name: 'name', type: 'text', value: 'Jane Smith' },
          { name: 'agree', type: 'checkbox', value: true },
          { name: 'color', type: 'dropdown', value: 'Blue' },
        ],
      });
      
      expect(result.filledFields).toBe(3);
    });

    it('should flatten form when requested', async () => {
      const formPdf = await createFormPdf();
      
      const result = await pdfService.fillForm({
        file: formPdf,
        fields: [
          { name: 'name', type: 'text', value: 'Test' },
        ],
        flatten: true,
      });
      
      // Verify flattening by trying to get form from result
      const flattenedDoc = await PDFDocument.load(result.pdf);
      const form = flattenedDoc.getForm();
      expect(form.getFields()).toHaveLength(0);
    });

    it('should handle non-existent field gracefully', async () => {
      const formPdf = await createFormPdf();
      
      const result = await pdfService.fillForm({
        file: formPdf,
        fields: [
          { name: 'nonexistent', type: 'text', value: 'Test' },
        ],
      });
      
      // Should not throw, but should report 0 filled
      expect(result.filledFields).toBe(0);
    });
  });

  describe('getInfo', () => {
    it('should get basic PDF info', async () => {
      const pdf = await createTestPdf(3);
      
      const info = await pdfService.getInfo(pdf);
      
      expect(info.pageCount).toBe(3);
      expect(info.metadata.title).toBe('Test Document');
      expect(info.metadata.author).toBe('Test Author');
      expect(info.fileSize).toBe(pdf.length);
    });

    it('should detect form fields', async () => {
      const formPdf = await createFormPdf();
      
      const info = await pdfService.getInfo(formPdf);
      
      expect(info.hasForm).toBe(true);
      expect(info.formFields).toBeDefined();
      expect(info.formFields?.length).toBe(3);
      
      const fieldNames = info.formFields?.map(f => f.name);
      expect(fieldNames).toContain('name');
      expect(fieldNames).toContain('agree');
      expect(fieldNames).toContain('color');
    });

    it('should detect field types', async () => {
      const formPdf = await createFormPdf();
      
      const info = await pdfService.getInfo(formPdf);
      
      const nameField = info.formFields?.find(f => f.name === 'name');
      const agreeField = info.formFields?.find(f => f.name === 'agree');
      const colorField = info.formFields?.find(f => f.name === 'color');
      
      expect(nameField?.type).toBe('text');
      expect(agreeField?.type).toBe('checkbox');
      expect(colorField?.type).toBe('dropdown');
    });

    it('should work with base64 input', async () => {
      const pdf = await createTestPdf(2);
      const base64 = pdf.toString('base64');
      
      const info = await pdfService.getInfo(base64);
      
      expect(info.pageCount).toBe(2);
    });

    it('should report no form for simple PDF', async () => {
      const pdf = await createTestPdf(1);
      
      const info = await pdfService.getInfo(pdf);
      
      expect(info.hasForm).toBe(false);
      expect(info.formFields).toBeUndefined();
    });
  });

  describe('createBlankPdf', () => {
    it('should create a blank PDF with default options', async () => {
      const pdf = await pdfService.createBlankPdf();
      
      expect(pdf).toBeInstanceOf(Buffer);
      
      const doc = await PDFDocument.load(pdf);
      expect(doc.getPageCount()).toBe(1);
    });

    it('should create PDF with specified number of pages', async () => {
      const pdf = await pdfService.createBlankPdf({ pages: 5 });
      
      const doc = await PDFDocument.load(pdf);
      expect(doc.getPageCount()).toBe(5);
    });

    it('should create PDF with custom dimensions', async () => {
      const pdf = await pdfService.createBlankPdf({
        width: 300,
        height: 400,
      });
      
      const doc = await PDFDocument.load(pdf);
      const page = doc.getPage(0);
      const { width, height } = page.getSize();
      
      expect(width).toBe(300);
      expect(height).toBe(400);
    });

    it('should set metadata on blank PDF', async () => {
      const pdf = await pdfService.createBlankPdf({
        metadata: {
          title: 'New Document',
          author: 'Creator',
        },
      });
      
      const doc = await PDFDocument.load(pdf);
      expect(doc.getTitle()).toBe('New Document');
      expect(doc.getAuthor()).toBe('Creator');
    });
  });

  describe('temp file management', () => {
    it('should save and cleanup temp files', async () => {
      const pdf = await createTestPdf(1);
      
      const filepath = await pdfService.saveToTemp(pdf, 'test');
      expect(filepath).toContain('test-');
      expect(filepath).toContain('.pdf');
      
      // Cleanup should work
      await expect(pdfService.cleanupTemp(filepath)).resolves.not.toThrow();
    });

    it('should cleanup old temp files', async () => {
      // This mainly tests that the method doesn't throw
      const cleaned = await pdfService.cleanupOldTempFiles(1000);
      expect(typeof cleaned).toBe('number');
    });
  });
});
