import { JSDOM } from 'jsdom';
import DOMPurify from 'dompurify';

// Initialize DOMPurify with jsdom
const window = new JSDOM('').window;
const purify = DOMPurify(window as unknown as Window);

// Allowed tags for PDF HTML generation
const ALLOWED_TAGS = [
  // Document structure
  'html', 'head', 'body', 'title', 'meta', 'link', 'style',
  // Text content
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div',
  'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'small', 'big',
  'sub', 'sup', 'mark', 'del', 'ins', 'code', 'pre', 'kbd', 'samp', 'var',
  // Lists
  'ul', 'ol', 'li', 'dl', 'dt', 'dd',
  // Tables
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
  // Media (limited)
  'img', 'figure', 'figcaption', 'picture', 'source',
  // Links
  'a',
  // Forms (for display only)
  'form', 'fieldset', 'legend', 'label', 'input', 'textarea', 'select', 'option', 'optgroup', 'button',
  // Semantic elements
  'article', 'aside', 'footer', 'header', 'main', 'nav', 'section',
  'address', 'blockquote', 'cite', 'q', 'abbr', 'time', 'data',
  // Other
  'br', 'hr', 'wbr', 'details', 'summary', 'dialog',
  // SVG elements
  'svg', 'g', 'path', 'circle', 'ellipse', 'line', 'polyline', 'polygon',
  'rect', 'text', 'tspan', 'defs', 'clipPath', 'mask', 'use', 'symbol',
  'linearGradient', 'radialGradient', 'stop', 'pattern', 'image',
];

// Allowed attributes
const ALLOWED_ATTR = [
  // Global attributes
  'id', 'class', 'style', 'title', 'lang', 'dir', 'hidden', 'tabindex',
  'data-*', 'aria-*', 'role',
  // Links
  'href', 'target', 'rel', 'download',
  // Images
  'src', 'srcset', 'sizes', 'alt', 'width', 'height', 'loading',
  // Tables
  'colspan', 'rowspan', 'headers', 'scope',
  // Forms
  'type', 'name', 'value', 'placeholder', 'disabled', 'readonly', 'checked', 'selected',
  'required', 'min', 'max', 'step', 'pattern', 'maxlength', 'minlength', 'multiple', 'size',
  'for', 'form', 'autocomplete', 'autofocus', 'rows', 'cols', 'wrap',
  // Media
  'autoplay', 'controls', 'loop', 'muted', 'preload', 'poster',
  // Meta
  'charset', 'content', 'http-equiv', 'media',
  // SVG attributes
  'viewBox', 'xmlns', 'fill', 'stroke', 'stroke-width', 'stroke-linecap',
  'stroke-linejoin', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-opacity',
  'fill-opacity', 'opacity', 'd', 'cx', 'cy', 'r', 'rx', 'ry', 'x', 'y',
  'x1', 'y1', 'x2', 'y2', 'points', 'transform', 'text-anchor', 'font-family',
  'font-size', 'font-weight', 'dominant-baseline', 'offset', 'stop-color',
  'stop-opacity', 'gradientUnits', 'gradientTransform', 'patternUnits',
  'patternTransform', 'clip-path', 'mask', 'xlink:href', 'preserveAspectRatio',
  // Other
  'datetime', 'cite', 'open', 'start', 'reversed', 'type',
];

// Configure DOMPurify
const purifyConfig: DOMPurify.Config = {
  ALLOWED_TAGS,
  ALLOWED_ATTR,
  ALLOW_DATA_ATTR: true,
  ALLOW_ARIA_ATTR: true,
  KEEP_CONTENT: true,
  RETURN_DOM: false,
  RETURN_DOM_FRAGMENT: false,
  RETURN_TRUSTED_TYPE: false,
  FORCE_BODY: false,
  SANITIZE_DOM: true,
  WHOLE_DOCUMENT: true,
  // Allow safe protocols
  ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel|data):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
};

export class SanitizerService {
  /**
   * Sanitize HTML content for safe PDF generation
   * Removes potentially dangerous scripts and elements while preserving styling
   */
  sanitizeHtml(html: string): string {
    // Basic validation
    if (!html || typeof html !== 'string') {
      return '';
    }

    // Sanitize the HTML
    const sanitized = purify.sanitize(html, purifyConfig);

    return sanitized;
  }

  /**
   * Sanitize HTML with custom configuration
   */
  sanitizeHtmlWithConfig(html: string, customConfig: Partial<DOMPurify.Config>): string {
    if (!html || typeof html !== 'string') {
      return '';
    }

    const mergedConfig = { ...purifyConfig, ...customConfig };
    return purify.sanitize(html, mergedConfig);
  }

  /**
   * Sanitize a simple text string (escape HTML entities)
   */
  escapeHtml(text: string): string {
    if (!text || typeof text !== 'string') {
      return '';
    }

    const htmlEntities: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
      '/': '&#x2F;',
      '`': '&#x60;',
      '=': '&#x3D;',
    };

    return text.replace(/[&<>"'`=/]/g, (char) => htmlEntities[char]);
  }

  /**
   * Sanitize CSS styles
   * Removes potentially dangerous CSS properties
   */
  sanitizeCss(css: string): string {
    if (!css || typeof css !== 'string') {
      return '';
    }

    // Remove @import rules (can load external resources)
    let sanitized = css.replace(/@import\s+[^;]+;?/gi, '');

    // Remove url() values that aren't data: URIs or safe protocols
    sanitized = sanitized.replace(
      /url\s*\(\s*(['"]?)(?!data:|https?:\/\/)[^)]+\1\s*\)/gi,
      'url(about:blank)'
    );

    // Remove expression() (IE-specific, dangerous)
    sanitized = sanitized.replace(/expression\s*\([^)]*\)/gi, '');

    // Remove behavior (IE-specific, dangerous)
    sanitized = sanitized.replace(/behavior\s*:\s*[^;]+;?/gi, '');

    // Remove -moz-binding (Firefox-specific, dangerous)
    sanitized = sanitized.replace(/-moz-binding\s*:\s*[^;]+;?/gi, '');

    // Remove javascript: protocol in any form
    sanitized = sanitized.replace(/javascript\s*:/gi, '');

    return sanitized;
  }

  /**
   * Check if HTML contains potentially dangerous content
   * Returns an array of warnings
   */
  analyzeHtml(html: string): string[] {
    const warnings: string[] = [];

    if (!html || typeof html !== 'string') {
      return warnings;
    }

    // Check for script tags
    if (/<script\b/i.test(html)) {
      warnings.push('HTML contains <script> tags which will be removed');
    }

    // Check for event handlers
    if (/\bon\w+\s*=/i.test(html)) {
      warnings.push('HTML contains inline event handlers which will be removed');
    }

    // Check for javascript: protocol
    if (/javascript\s*:/i.test(html)) {
      warnings.push('HTML contains javascript: protocol which will be removed');
    }

    // Check for data: URIs (can be vectors for attacks)
    if (/data\s*:/i.test(html)) {
      warnings.push('HTML contains data: URIs which may be modified');
    }

    // Check for iframes
    if (/<iframe\b/i.test(html)) {
      warnings.push('HTML contains <iframe> tags which will be removed');
    }

    // Check for object/embed tags
    if (/<(?:object|embed)\b/i.test(html)) {
      warnings.push('HTML contains <object> or <embed> tags which will be removed');
    }

    // Check for form actions with javascript
    if (/<form[^>]+action\s*=\s*["']?javascript/i.test(html)) {
      warnings.push('HTML contains forms with javascript actions which will be sanitized');
    }

    return warnings;
  }

  /**
   * Validate and sanitize a URL
   */
  sanitizeUrl(url: string): string | null {
    if (!url || typeof url !== 'string') {
      return null;
    }

    try {
      const parsed = new URL(url);
      const allowedProtocols = ['http:', 'https:', 'mailto:', 'tel:'];
      
      if (!allowedProtocols.includes(parsed.protocol)) {
        return null;
      }

      return parsed.href;
    } catch {
      return null;
    }
  }

  /**
   * Sanitize filename for safe file operations
   */
  sanitizeFilename(filename: string): string {
    if (!filename || typeof filename !== 'string') {
      return 'document';
    }

    // Remove path separators and null bytes
    let sanitized = filename.replace(/[/\\:\0]/g, '_');

    // Remove leading dots (hidden files on Unix)
    sanitized = sanitized.replace(/^\.+/, '');

    // Remove reserved characters on Windows
    sanitized = sanitized.replace(/[<>:"|?*]/g, '_');

    // Truncate to reasonable length
    if (sanitized.length > 200) {
      const ext = sanitized.lastIndexOf('.');
      if (ext > 0) {
        const extension = sanitized.substring(ext);
        sanitized = sanitized.substring(0, 200 - extension.length) + extension;
      } else {
        sanitized = sanitized.substring(0, 200);
      }
    }

    // Default if empty after sanitization
    if (!sanitized || sanitized === '.' || sanitized === '..') {
      return 'document';
    }

    return sanitized;
  }
}

export const sanitizerService = new SanitizerService();
