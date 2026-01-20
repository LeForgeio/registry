import Handlebars from 'handlebars';
import { sanitizerService } from './sanitizer.service';

export class TemplateService {
  private handlebars: typeof Handlebars;

  constructor() {
    // Create a new Handlebars environment to avoid polluting the global instance
    this.handlebars = Handlebars.create();
    this.registerDefaultHelpers();
  }

  /**
   * Register default Handlebars helpers
   */
  private registerDefaultHelpers(): void {
    // Conditional helpers
    this.handlebars.registerHelper('eq', (a, b) => a === b);
    this.handlebars.registerHelper('ne', (a, b) => a !== b);
    this.handlebars.registerHelper('lt', (a, b) => a < b);
    this.handlebars.registerHelper('lte', (a, b) => a <= b);
    this.handlebars.registerHelper('gt', (a, b) => a > b);
    this.handlebars.registerHelper('gte', (a, b) => a >= b);
    this.handlebars.registerHelper('and', (...args) => {
      args.pop(); // Remove Handlebars options object
      return args.every(Boolean);
    });
    this.handlebars.registerHelper('or', (...args) => {
      args.pop(); // Remove Handlebars options object
      return args.some(Boolean);
    });
    this.handlebars.registerHelper('not', (value) => !value);

    // String helpers
    this.handlebars.registerHelper('uppercase', (str) => 
      typeof str === 'string' ? str.toUpperCase() : str
    );
    this.handlebars.registerHelper('lowercase', (str) => 
      typeof str === 'string' ? str.toLowerCase() : str
    );
    this.handlebars.registerHelper('capitalize', (str) => {
      if (typeof str !== 'string') return str;
      return str.charAt(0).toUpperCase() + str.slice(1);
    });
    this.handlebars.registerHelper('truncate', (str, length) => {
      if (typeof str !== 'string') return str;
      if (str.length <= length) return str;
      return str.substring(0, length) + '...';
    });
    this.handlebars.registerHelper('replace', (str, search, replace) => {
      if (typeof str !== 'string') return str;
      return str.replace(new RegExp(search, 'g'), replace);
    });
    this.handlebars.registerHelper('split', (str, separator) => {
      if (typeof str !== 'string') return [];
      return str.split(separator);
    });
    this.handlebars.registerHelper('join', (arr, separator) => {
      if (!Array.isArray(arr)) return arr;
      return arr.join(separator);
    });

    // Number helpers
    this.handlebars.registerHelper('formatNumber', (num, decimals = 2) => {
      if (typeof num !== 'number') return num;
      return num.toFixed(decimals);
    });
    this.handlebars.registerHelper('formatCurrency', (num, currency = 'USD', locale = 'en-US') => {
      if (typeof num !== 'number') return num;
      return new Intl.NumberFormat(locale, { style: 'currency', currency }).format(num);
    });
    this.handlebars.registerHelper('formatPercent', (num, decimals = 0) => {
      if (typeof num !== 'number') return num;
      return `${(num * 100).toFixed(decimals)}%`;
    });
    this.handlebars.registerHelper('add', (a, b) => Number(a) + Number(b));
    this.handlebars.registerHelper('subtract', (a, b) => Number(a) - Number(b));
    this.handlebars.registerHelper('multiply', (a, b) => Number(a) * Number(b));
    this.handlebars.registerHelper('divide', (a, b) => Number(a) / Number(b));
    this.handlebars.registerHelper('mod', (a, b) => Number(a) % Number(b));
    this.handlebars.registerHelper('round', (num) => Math.round(Number(num)));
    this.handlebars.registerHelper('floor', (num) => Math.floor(Number(num)));
    this.handlebars.registerHelper('ceil', (num) => Math.ceil(Number(num)));
    this.handlebars.registerHelper('abs', (num) => Math.abs(Number(num)));

    // Date helpers
    this.handlebars.registerHelper('formatDate', (date, format = 'YYYY-MM-DD', locale = 'en-US') => {
      const d = new Date(date);
      if (isNaN(d.getTime())) return date;
      
      // Simple format implementation
      const options: Record<string, Intl.DateTimeFormatOptions> = {
        'YYYY-MM-DD': { year: 'numeric', month: '2-digit', day: '2-digit' },
        'MM/DD/YYYY': { year: 'numeric', month: '2-digit', day: '2-digit' },
        'DD/MM/YYYY': { year: 'numeric', month: '2-digit', day: '2-digit' },
        'MMMM D, YYYY': { year: 'numeric', month: 'long', day: 'numeric' },
        'MMM D, YYYY': { year: 'numeric', month: 'short', day: 'numeric' },
        'full': { dateStyle: 'full' },
        'long': { dateStyle: 'long' },
        'medium': { dateStyle: 'medium' },
        'short': { dateStyle: 'short' },
      };
      
      const formatOptions = options[format] || options['YYYY-MM-DD'];
      return new Intl.DateTimeFormat(locale, formatOptions).format(d);
    });
    this.handlebars.registerHelper('now', () => new Date().toISOString());
    this.handlebars.registerHelper('year', (date) => new Date(date || Date.now()).getFullYear());
    this.handlebars.registerHelper('month', (date) => new Date(date || Date.now()).getMonth() + 1);
    this.handlebars.registerHelper('day', (date) => new Date(date || Date.now()).getDate());

    // Array helpers
    this.handlebars.registerHelper('first', (arr) => Array.isArray(arr) ? arr[0] : arr);
    this.handlebars.registerHelper('last', (arr) => Array.isArray(arr) ? arr[arr.length - 1] : arr);
    this.handlebars.registerHelper('length', (arr) => Array.isArray(arr) ? arr.length : 0);
    this.handlebars.registerHelper('includes', (arr, value) => 
      Array.isArray(arr) ? arr.includes(value) : false
    );
    this.handlebars.registerHelper('range', (start, end, step = 1) => {
      const result = [];
      for (let i = start; i <= end; i += step) {
        result.push(i);
      }
      return result;
    });
    this.handlebars.registerHelper('sum', (arr) => {
      if (!Array.isArray(arr)) return 0;
      return arr.reduce((acc, val) => acc + Number(val), 0);
    });
    this.handlebars.registerHelper('avg', (arr) => {
      if (!Array.isArray(arr) || arr.length === 0) return 0;
      return arr.reduce((acc, val) => acc + Number(val), 0) / arr.length;
    });

    // Object helpers
    this.handlebars.registerHelper('keys', (obj) => 
      typeof obj === 'object' && obj !== null ? Object.keys(obj) : []
    );
    this.handlebars.registerHelper('values', (obj) => 
      typeof obj === 'object' && obj !== null ? Object.values(obj) : []
    );
    this.handlebars.registerHelper('lookup', (obj, key) => 
      typeof obj === 'object' && obj !== null ? obj[key] : undefined
    );
    this.handlebars.registerHelper('json', (obj, indent = 2) => 
      JSON.stringify(obj, null, indent)
    );

    // Utility helpers
    this.handlebars.registerHelper('default', (value, defaultValue) => 
      value !== undefined && value !== null && value !== '' ? value : defaultValue
    );
    this.handlebars.registerHelper('coalesce', (...args) => {
      args.pop(); // Remove Handlebars options object
      return args.find(arg => arg !== undefined && arg !== null && arg !== '');
    });
    this.handlebars.registerHelper('repeat', (n, block) => {
      let result = '';
      for (let i = 0; i < n; i++) {
        result += block.fn({ index: i, first: i === 0, last: i === n - 1 });
      }
      return result;
    });

    // Safe HTML output (escapes HTML by default, use {{{safeHtml}}} for raw)
    this.handlebars.registerHelper('safeHtml', (html) => 
      new Handlebars.SafeString(sanitizerService.sanitizeHtml(html || ''))
    );
  }

  /**
   * Compile a Handlebars template
   */
  compile(template: string): Handlebars.TemplateDelegate {
    return this.handlebars.compile(template, {
      strict: false,
      noEscape: false, // Escape HTML by default
    });
  }

  /**
   * Render a template with data
   */
  render(
    template: string,
    data: Record<string, unknown>,
    options?: {
      helpers?: Record<string, (...args: unknown[]) => unknown>;
      partials?: Record<string, string>;
    }
  ): string {
    // Register custom helpers if provided
    if (options?.helpers) {
      for (const [name, fn] of Object.entries(options.helpers)) {
        // Validate helper function
        if (typeof fn === 'function') {
          this.handlebars.registerHelper(name, fn);
        }
      }
    }

    // Register partials if provided
    if (options?.partials) {
      for (const [name, partial] of Object.entries(options.partials)) {
        this.handlebars.registerPartial(name, partial);
      }
    }

    try {
      const compiled = this.compile(template);
      const rendered = compiled(data);
      return rendered;
    } finally {
      // Clean up custom helpers and partials
      if (options?.helpers) {
        for (const name of Object.keys(options.helpers)) {
          this.handlebars.unregisterHelper(name);
        }
      }
      if (options?.partials) {
        for (const name of Object.keys(options.partials)) {
          this.handlebars.unregisterPartial(name);
        }
      }
    }
  }

  /**
   * Pre-compile a template for validation
   * Returns any compilation errors
   */
  validate(template: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    try {
      this.handlebars.compile(template, { strict: true });
    } catch (error) {
      if (error instanceof Error) {
        errors.push(error.message);
      } else {
        errors.push('Unknown template compilation error');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Get list of available helpers
   */
  getAvailableHelpers(): string[] {
    return Object.keys(this.handlebars.helpers);
  }
}

export const templateService = new TemplateService();
