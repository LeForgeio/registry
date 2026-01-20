import { sanitizerService } from '../src/services/sanitizer.service';

describe('SanitizerService', () => {
  describe('sanitizeHtml', () => {
    it('should return empty string for null/undefined input', () => {
      expect(sanitizerService.sanitizeHtml('')).toBe('');
      expect(sanitizerService.sanitizeHtml(null as any)).toBe('');
      expect(sanitizerService.sanitizeHtml(undefined as any)).toBe('');
    });

    it('should allow safe HTML elements', () => {
      const html = '<p>Hello <strong>World</strong></p>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('<p>');
      expect(result).toContain('<strong>');
      expect(result).toContain('Hello');
      expect(result).toContain('World');
    });

    it('should preserve table structures', () => {
      const html = '<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('<table>');
      expect(result).toContain('<th>');
      expect(result).toContain('<td>');
    });

    it('should preserve lists', () => {
      const html = '<ul><li>Item 1</li><li>Item 2</li></ul>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('<ul>');
      expect(result).toContain('<li>');
    });

    it('should remove script tags', () => {
      const html = '<p>Hello</p><script>alert("xss")</script>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).not.toContain('<script>');
      expect(result).not.toContain('alert');
      expect(result).toContain('<p>Hello</p>');
    });

    it('should remove onclick and other event handlers', () => {
      const html = '<button onclick="alert(1)">Click</button>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).not.toContain('onclick');
      expect(result).toContain('Click');
    });

    it('should remove javascript: URLs', () => {
      const html = '<a href="javascript:alert(1)">Click</a>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).not.toContain('javascript:');
    });

    it('should preserve safe URLs', () => {
      const html = '<a href="https://example.com">Link</a>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('https://example.com');
    });

    it('should preserve style attributes', () => {
      const html = '<p style="color: red; font-size: 14px;">Text</p>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('style');
      expect(result).toContain('color');
    });

    it('should preserve image tags with safe src', () => {
      const html = '<img src="https://example.com/image.png" alt="Image">';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('<img');
      expect(result).toContain('src=');
      expect(result).toContain('alt=');
    });

    it('should preserve SVG elements', () => {
      const html = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).toContain('<svg');
      expect(result).toContain('<circle');
      expect(result).toContain('viewBox');
    });

    it('should remove iframes', () => {
      const html = '<iframe src="https://evil.com"></iframe><p>Text</p>';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).not.toContain('<iframe');
      expect(result).toContain('<p>Text</p>');
    });

    it('should remove object and embed tags', () => {
      const html = '<object data="data.swf"></object><embed src="plugin.swf">';
      const result = sanitizerService.sanitizeHtml(html);
      expect(result).not.toContain('<object');
      expect(result).not.toContain('<embed');
    });
  });

  describe('escapeHtml', () => {
    it('should escape HTML entities', () => {
      const text = '<script>alert("xss")</script>';
      const result = sanitizerService.escapeHtml(text);
      expect(result).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
    });

    it('should handle empty string', () => {
      expect(sanitizerService.escapeHtml('')).toBe('');
    });

    it('should handle null/undefined', () => {
      expect(sanitizerService.escapeHtml(null as any)).toBe('');
      expect(sanitizerService.escapeHtml(undefined as any)).toBe('');
    });

    it('should escape ampersands', () => {
      expect(sanitizerService.escapeHtml('Tom & Jerry')).toBe('Tom &amp; Jerry');
    });
  });

  describe('sanitizeCss', () => {
    it('should allow normal CSS', () => {
      const css = 'body { color: red; font-size: 14px; }';
      const result = sanitizerService.sanitizeCss(css);
      expect(result).toContain('color: red');
      expect(result).toContain('font-size: 14px');
    });

    it('should remove @import rules', () => {
      const css = '@import url("evil.css"); body { color: red; }';
      const result = sanitizerService.sanitizeCss(css);
      expect(result).not.toContain('@import');
      expect(result).toContain('body { color: red; }');
    });

    it('should remove expression()', () => {
      const css = 'body { width: expression(alert(1)); color: red; }';
      const result = sanitizerService.sanitizeCss(css);
      expect(result).not.toContain('expression');
      expect(result).toContain('color: red');
    });

    it('should remove behavior property', () => {
      const css = 'body { behavior: url(evil.htc); color: red; }';
      const result = sanitizerService.sanitizeCss(css);
      expect(result).not.toContain('behavior');
      expect(result).toContain('color: red');
    });

    it('should handle empty input', () => {
      expect(sanitizerService.sanitizeCss('')).toBe('');
      expect(sanitizerService.sanitizeCss(null as any)).toBe('');
    });
  });

  describe('analyzeHtml', () => {
    it('should return empty array for safe HTML', () => {
      const html = '<p>Hello World</p>';
      const warnings = sanitizerService.analyzeHtml(html);
      expect(warnings).toEqual([]);
    });

    it('should warn about script tags', () => {
      const html = '<script>alert(1)</script>';
      const warnings = sanitizerService.analyzeHtml(html);
      expect(warnings.some(w => w.includes('script'))).toBe(true);
    });

    it('should warn about event handlers', () => {
      const html = '<button onclick="alert(1)">Click</button>';
      const warnings = sanitizerService.analyzeHtml(html);
      expect(warnings.some(w => w.includes('event handlers'))).toBe(true);
    });

    it('should warn about javascript: protocol', () => {
      const html = '<a href="javascript:void(0)">Link</a>';
      const warnings = sanitizerService.analyzeHtml(html);
      expect(warnings.some(w => w.includes('javascript:'))).toBe(true);
    });

    it('should warn about iframes', () => {
      const html = '<iframe src="test.html"></iframe>';
      const warnings = sanitizerService.analyzeHtml(html);
      expect(warnings.some(w => w.includes('iframe'))).toBe(true);
    });
  });

  describe('sanitizeUrl', () => {
    it('should allow http URLs', () => {
      const url = 'http://example.com/page';
      expect(sanitizerService.sanitizeUrl(url)).toBe(url);
    });

    it('should allow https URLs', () => {
      const url = 'https://example.com/page';
      expect(sanitizerService.sanitizeUrl(url)).toBe(url);
    });

    it('should allow mailto URLs', () => {
      const url = 'mailto:test@example.com';
      expect(sanitizerService.sanitizeUrl(url)).toBe(url);
    });

    it('should allow tel URLs', () => {
      const url = 'tel:+1234567890';
      expect(sanitizerService.sanitizeUrl(url)).toBe(url);
    });

    it('should reject javascript URLs', () => {
      const url = 'javascript:alert(1)';
      expect(sanitizerService.sanitizeUrl(url)).toBeNull();
    });

    it('should reject data URLs', () => {
      const url = 'data:text/html,<script>alert(1)</script>';
      expect(sanitizerService.sanitizeUrl(url)).toBeNull();
    });

    it('should reject invalid URLs', () => {
      expect(sanitizerService.sanitizeUrl('not a url')).toBeNull();
    });

    it('should handle empty input', () => {
      expect(sanitizerService.sanitizeUrl('')).toBeNull();
      expect(sanitizerService.sanitizeUrl(null as any)).toBeNull();
    });
  });

  describe('sanitizeFilename', () => {
    it('should keep safe filenames', () => {
      expect(sanitizerService.sanitizeFilename('document.pdf')).toBe('document.pdf');
    });

    it('should remove path separators', () => {
      expect(sanitizerService.sanitizeFilename('../../../etc/passwd')).toBe('______etc_passwd');
    });

    it('should remove leading dots', () => {
      expect(sanitizerService.sanitizeFilename('.hidden')).toBe('hidden');
    });

    it('should remove Windows reserved characters', () => {
      expect(sanitizerService.sanitizeFilename('file<>:"|?*.pdf')).toBe('file_______.pdf');
    });

    it('should truncate long filenames', () => {
      const longName = 'a'.repeat(250) + '.pdf';
      const result = sanitizerService.sanitizeFilename(longName);
      expect(result.length).toBeLessThanOrEqual(200);
      expect(result.endsWith('.pdf')).toBe(true);
    });

    it('should return default for empty input', () => {
      expect(sanitizerService.sanitizeFilename('')).toBe('document');
      expect(sanitizerService.sanitizeFilename(null as any)).toBe('document');
    });

    it('should return default for . or ..', () => {
      expect(sanitizerService.sanitizeFilename('.')).toBe('document');
      expect(sanitizerService.sanitizeFilename('..')).toBe('document');
    });
  });
});
