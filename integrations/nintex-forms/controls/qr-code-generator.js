/**
 * LeForge QR Code Generator Control for Nintex Forms
 * 
 * Generates QR codes from form field values.
 * 
 * @version 1.0.0
 * @author LeForge
 */

(function() {
  'use strict';

  const CONTROL_NAME = 'LeForgeQRCodeGenerator';
  const VERSION = '1.0.0';

  /**
   * LeForge QR Code Generator Control
   */
  class LeForgeQRCodeGenerator {
    constructor(element, options) {
      this.element = element;
      this.options = Object.assign({
        leforgeUrl: '',
        apiKey: '',
        dataField: '',          // Field containing data to encode
        outputField: '',        // Image field for QR code (optional)
        size: 200,              // QR code size in pixels
        errorCorrection: 'M',   // L, M, Q, H
        format: 'png',          // png, svg
        autoGenerate: false,
        debounceMs: 500,
        buttonText: 'Generate QR',
        showPreview: true,
        backgroundColor: '#ffffff',
        foregroundColor: '#000000',
        timeout: 15000
      }, options);

      this.isGenerating = false;
      this.debounceTimer = null;

      this.init();
    }

    init() {
      this.render();
      this.bindEvents();

      if (this.options.autoGenerate && this.options.dataField) {
        this.watchDataField();
      }
    }

    render() {
      this.container = document.createElement('div');
      this.container.className = 'leforge-qr-generator';
      this.container.innerHTML = `
        <div class="leforge-qr-wrapper">
          <div class="leforge-qr-controls">
            ${!this.options.autoGenerate ? `
              <button type="button" class="leforge-qr-btn">
                <span class="btn-icon">◼</span>
                <span class="btn-text">${this.options.buttonText}</span>
                <span class="btn-spinner" style="display: none;">⟳</span>
              </button>
            ` : ''}
            <div class="leforge-qr-status"></div>
          </div>
          ${this.options.showPreview ? `
            <div class="leforge-qr-preview">
              <div class="leforge-qr-placeholder">QR code will appear here</div>
            </div>
          ` : ''}
        </div>
      `;

      this.element.appendChild(this.container);
      
      this.button = this.container.querySelector('.leforge-qr-btn');
      this.statusEl = this.container.querySelector('.leforge-qr-status');
      this.previewEl = this.container.querySelector('.leforge-qr-preview');

      this.addStyles();
    }

    addStyles() {
      if (document.getElementById('leforge-qr-styles')) return;

      const styles = document.createElement('style');
      styles.id = 'leforge-qr-styles';
      styles.textContent = `
        .leforge-qr-generator {
          margin: 8px 0;
        }
        .leforge-qr-wrapper {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .leforge-qr-controls {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .leforge-qr-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 6px 12px;
          background: #7c3aed;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .leforge-qr-btn:hover:not(:disabled) {
          background: #6d28d9;
        }
        .leforge-qr-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .leforge-qr-btn .btn-spinner {
          animation: leforge-spin 1s linear infinite;
        }
        .leforge-qr-status {
          font-size: 12px;
          color: #666;
        }
        .leforge-qr-status.error {
          color: #dc2626;
        }
        .leforge-qr-preview {
          display: inline-block;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 12px;
          background: white;
        }
        .leforge-qr-placeholder {
          width: 150px;
          height: 150px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #9ca3af;
          font-size: 12px;
          text-align: center;
          background: #f9fafb;
          border-radius: 4px;
        }
        .leforge-qr-preview img {
          max-width: 100%;
          height: auto;
          display: block;
        }
        .leforge-qr-download {
          display: block;
          margin-top: 8px;
          font-size: 12px;
          color: #6366f1;
          text-decoration: none;
          text-align: center;
        }
        .leforge-qr-download:hover {
          text-decoration: underline;
        }
      `;
      document.head.appendChild(styles);
    }

    bindEvents() {
      if (this.button) {
        this.button.addEventListener('click', () => this.generate());
      }
    }

    watchDataField() {
      const field = this.getFormField(this.options.dataField);
      if (field) {
        field.addEventListener('input', () => this.scheduleGeneration());
        field.addEventListener('change', () => this.scheduleGeneration());
      }
    }

    scheduleGeneration() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        const value = this.getFieldValue(this.options.dataField);
        if (value) {
          this.generate();
        }
      }, this.options.debounceMs);
    }

    async generate() {
      if (this.isGenerating) return;

      const dataValue = this.options.dataField 
        ? this.getFieldValue(this.options.dataField)
        : '';

      if (!dataValue) {
        this.setStatus('Data field is empty', 'error');
        return;
      }

      this.setLoading(true);
      this.setStatus('');

      try {
        let imageData;

        if (this.options.leforgeUrl) {
          // Use LeForge QR Code Service
          imageData = await this.callLeForge(dataValue);
        } else {
          // Use local QR generation library if available
          imageData = await this.generateLocal(dataValue);
        }

        if (this.options.showPreview && this.previewEl) {
          this.showPreview(imageData);
        }

        if (this.options.outputField) {
          this.setFieldValue(this.options.outputField, imageData);
        }

        this.setStatus('QR code generated');
        this.triggerEvent('onGenerate', { data: dataValue, image: imageData });
      } catch (error) {
        console.error('LeForge QR Code Generator error:', error);
        this.setStatus(error.message || 'Generation failed', 'error');
        this.triggerEvent('onError', { error: error.message });
      } finally {
        this.setLoading(false);
      }
    }

    async callLeForge(data) {
      const url = `${this.options.leforgeUrl.replace(/\/$/, '')}/invoke/qrcode-utils/generate`;
      
      const body = {
        data: data,
        size: this.options.size,
        errorCorrection: this.options.errorCorrection,
        format: this.options.format,
        backgroundColor: this.options.backgroundColor,
        foregroundColor: this.options.foregroundColor
      };

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.options.timeout);

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': this.options.apiKey
          },
          body: JSON.stringify(body),
          signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.error || `HTTP ${response.status}`);
        }

        const result = await response.json();
        
        // Return base64 data URL or SVG string
        if (result.dataUrl) {
          return result.dataUrl;
        } else if (result.base64) {
          return `data:image/${this.options.format};base64,${result.base64}`;
        } else if (result.svg) {
          return `data:image/svg+xml;base64,${btoa(result.svg)}`;
        }
        
        throw new Error('Invalid response format');
      } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
          throw new Error('Request timed out');
        }
        throw error;
      }
    }

    async generateLocal(data) {
      // Check for QRCode.js library
      if (typeof QRCode !== 'undefined') {
        return new Promise((resolve, reject) => {
          const canvas = document.createElement('canvas');
          QRCode.toCanvas(canvas, data, {
            width: this.options.size,
            errorCorrectionLevel: this.options.errorCorrection,
            color: {
              dark: this.options.foregroundColor,
              light: this.options.backgroundColor
            }
          }, (error) => {
            if (error) reject(error);
            else resolve(canvas.toDataURL('image/png'));
          });
        });
      }

      // Check for qrcode-generator library
      if (typeof qrcode !== 'undefined') {
        const typeNumber = 0; // Auto-detect
        const errorLevel = {
          'L': 'L', 'M': 'M', 'Q': 'Q', 'H': 'H'
        }[this.options.errorCorrection] || 'M';
        
        const qr = qrcode(typeNumber, errorLevel);
        qr.addData(data);
        qr.make();
        
        return qr.createDataURL(4, 0);
      }

      // Fallback: Use a public API (for demo purposes only)
      throw new Error('No QR library found. Configure LeForge URL or include a QR code library.');
    }

    showPreview(imageData) {
      if (!this.previewEl) return;

      this.previewEl.innerHTML = `
        <img src="${imageData}" alt="QR Code" width="${this.options.size}" height="${this.options.size}">
        <a href="${imageData}" download="qrcode.${this.options.format}" class="leforge-qr-download">
          Download QR Code
        </a>
      `;
    }

    setLoading(loading) {
      this.isGenerating = loading;
      if (this.button) {
        this.button.disabled = loading;
        const spinner = this.button.querySelector('.btn-spinner');
        const text = this.button.querySelector('.btn-text');
        const icon = this.button.querySelector('.btn-icon');
        if (spinner) spinner.style.display = loading ? 'inline' : 'none';
        if (text) text.style.display = loading ? 'none' : 'inline';
        if (icon) icon.style.display = loading ? 'none' : 'inline';
      }
    }

    setStatus(message, type = '') {
      if (this.statusEl) {
        this.statusEl.textContent = message;
        this.statusEl.className = 'leforge-qr-status' + (type ? ` ${type}` : '');
      }
    }

    getFormField(fieldName) {
      if (typeof NWF$ !== 'undefined') {
        return NWF$(`[data-controlname="${fieldName}"]`).find('input, textarea').get(0);
      }
      return document.querySelector(`[data-controlname="${fieldName}"] input, [data-controlname="${fieldName}"] textarea`) ||
             document.querySelector(`[name="${fieldName}"]`) ||
             document.getElementById(fieldName);
    }

    getFieldValue(fieldName) {
      const field = this.getFormField(fieldName);
      return field ? field.value : '';
    }

    setFieldValue(fieldName, value) {
      const field = this.getFormField(fieldName);
      if (field) {
        field.value = value;
        field.dispatchEvent(new Event('change', { bubbles: true }));
        field.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    triggerEvent(eventName, detail) {
      this.element.dispatchEvent(new CustomEvent(`leforge:${eventName}`, {
        bubbles: true,
        detail: detail
      }));
    }

    // Public API
    setSize(size) {
      this.options.size = size;
    }

    setColors(foreground, background) {
      this.options.foregroundColor = foreground;
      this.options.backgroundColor = background;
    }

    getImageData() {
      const img = this.previewEl?.querySelector('img');
      return img ? img.src : null;
    }

    destroy() {
      clearTimeout(this.debounceTimer);
      if (this.container) {
        this.container.remove();
      }
    }
  }

  // Register with Nintex Forms
  if (typeof NWF !== 'undefined' && NWF.FormFiller) {
    NWF.FormFiller.Events.RegisterAfterReady(function() {
      document.querySelectorAll('[data-leforge-control="qr-code-generator"]').forEach(el => {
        const options = JSON.parse(el.dataset.leforgeOptions || '{}');
        new LeForgeQRCodeGenerator(el, options);
      });
    });
  }

  // Export
  window.LeForgeQRCodeGenerator = LeForgeQRCodeGenerator;
  window.LeForgeControls = window.LeForgeControls || {};
  window.LeForgeControls.QRCodeGenerator = LeForgeQRCodeGenerator;

  console.log(`LeForge QR Code Generator v${VERSION} loaded`);
})();
