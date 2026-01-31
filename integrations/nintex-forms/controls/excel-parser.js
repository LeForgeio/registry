/**
 * LeForge Excel Parser Control for Nintex Forms
 * Wraps the excel-utils ForgeHook plugin for use in forms
 * 
 * This demonstrates how an INTEGRATION CONTROL calls a PLUGIN.
 */

(function() {
  'use strict';

  /**
   * Excel Parser Control
   * Allows users to upload Excel/CSV files and parse them in forms
   */
  class LeForgeExcelParser {
    constructor(container, config = {}) {
      this.container = container;
      this.config = {
        leforgeUrl: config.leforgeUrl || '',
        apiKey: config.apiKey || '',
        
        // File input configuration
        acceptedTypes: config.acceptedTypes || '.xlsx,.xls,.csv',
        maxFileSize: config.maxFileSize || 10 * 1024 * 1024, // 10MB
        
        // Parse options
        hasHeaders: config.hasHeaders !== false,
        delimiter: config.delimiter || ',',
        sheetIndex: config.sheetIndex || 0,
        
        // Output configuration
        outputField: config.outputField || null,     // Field to populate with parsed data
        outputFormat: config.outputFormat || 'json', // 'json', 'table', 'dropdown'
        
        // UI options
        showPreview: config.showPreview !== false,
        previewRows: config.previewRows || 5,
        buttonText: config.buttonText || 'Parse File',
        
        // Callbacks (for Nintex Forms integration)
        onParse: config.onParse || null,
        onError: config.onError || null
      };
      
      this.parsedData = null;
      this.init();
    }

    init() {
      this.render();
      this.attachEvents();
    }

    render() {
      this.container.innerHTML = `
        <div class="leforge-excel-parser">
          <div class="file-input-wrapper">
            <input type="file" 
                   class="file-input" 
                   accept="${this.config.acceptedTypes}"
                   style="display: none;">
            <button type="button" class="select-file-btn">
              📁 Select File
            </button>
            <span class="file-name">No file selected</span>
          </div>
          
          <div class="options-row" style="margin: 10px 0;">
            <label style="margin-right: 15px;">
              <input type="checkbox" class="has-headers" ${this.config.hasHeaders ? 'checked' : ''}>
              First row is headers
            </label>
            <label>
              Delimiter: 
              <select class="delimiter-select">
                <option value="," ${this.config.delimiter === ',' ? 'selected' : ''}>Comma (,)</option>
                <option value=";" ${this.config.delimiter === ';' ? 'selected' : ''}>Semicolon (;)</option>
                <option value="\t" ${this.config.delimiter === '\t' ? 'selected' : ''}>Tab</option>
                <option value="|" ${this.config.delimiter === '|' ? 'selected' : ''}>Pipe (|)</option>
              </select>
            </label>
          </div>
          
          <button type="button" class="parse-btn" disabled>
            ${this.config.buttonText}
          </button>
          
          <div class="status-message" style="margin: 10px 0; display: none;"></div>
          
          ${this.config.showPreview ? `
            <div class="preview-container" style="margin-top: 15px; display: none;">
              <h4>Preview (first ${this.config.previewRows} rows):</h4>
              <div class="preview-table" style="overflow-x: auto;"></div>
              <div class="data-info"></div>
            </div>
          ` : ''}
        </div>
        
        <style>
          .leforge-excel-parser { font-family: inherit; }
          .leforge-excel-parser .file-input-wrapper { display: flex; align-items: center; gap: 10px; }
          .leforge-excel-parser .select-file-btn,
          .leforge-excel-parser .parse-btn {
            padding: 8px 16px;
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
          }
          .leforge-excel-parser .select-file-btn:hover,
          .leforge-excel-parser .parse-btn:hover:not(:disabled) { background: #4f46e5; }
          .leforge-excel-parser .parse-btn:disabled { background: #9ca3af; cursor: not-allowed; }
          .leforge-excel-parser .file-name { color: #6b7280; font-size: 0.9em; }
          .leforge-excel-parser .status-message { padding: 8px; border-radius: 4px; }
          .leforge-excel-parser .status-message.error { background: #fee2e2; color: #dc2626; }
          .leforge-excel-parser .status-message.success { background: #dcfce7; color: #16a34a; }
          .leforge-excel-parser .status-message.loading { background: #e0e7ff; color: #4338ca; }
          .leforge-excel-parser .preview-table table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
          }
          .leforge-excel-parser .preview-table th,
          .leforge-excel-parser .preview-table td {
            border: 1px solid #e5e7eb;
            padding: 6px 8px;
            text-align: left;
          }
          .leforge-excel-parser .preview-table th { background: #f3f4f6; }
          .leforge-excel-parser .data-info { margin-top: 10px; font-size: 0.9em; color: #6b7280; }
        </style>
      `;
    }

    attachEvents() {
      const fileInput = this.container.querySelector('.file-input');
      const selectBtn = this.container.querySelector('.select-file-btn');
      const parseBtn = this.container.querySelector('.parse-btn');
      const fileNameEl = this.container.querySelector('.file-name');

      selectBtn.addEventListener('click', () => fileInput.click());

      fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
          if (file.size > this.config.maxFileSize) {
            this.showStatus(`File too large. Max size: ${this.config.maxFileSize / 1024 / 1024}MB`, 'error');
            return;
          }
          fileNameEl.textContent = file.name;
          parseBtn.disabled = false;
          this.selectedFile = file;
        }
      });

      parseBtn.addEventListener('click', () => this.parseFile());
    }

    async parseFile() {
      if (!this.selectedFile) return;

      this.showStatus('Reading file...', 'loading');

      try {
        // Read file as base64
        const base64 = await this.readFileAsBase64(this.selectedFile);
        const isCSV = this.selectedFile.name.toLowerCase().endsWith('.csv');

        this.showStatus('Parsing with LeForge...', 'loading');

        // Determine which plugin endpoint to call
        const endpoint = isCSV ? 'parseCSV' : 'parseXLSX';
        
        // ============================================================
        // THIS IS THE KEY PART: Integration calls Plugin via REST API
        // ============================================================
        const response = await this.callLeForgePlugin('excel-utils', endpoint, {
          data: isCSV ? atob(base64.split(',')[1]) : base64.split(',')[1],
          hasHeaders: this.container.querySelector('.has-headers').checked,
          delimiter: this.container.querySelector('.delimiter-select').value,
          sheet: this.config.sheetIndex
        });

        if (!response.success) {
          throw new Error(response.error?.message || 'Parse failed');
        }

        // Store parsed data
        this.parsedData = response.data;

        // Update preview
        if (this.config.showPreview) {
          this.renderPreview(response.data);
        }

        // Populate output field if configured
        if (this.config.outputField) {
          this.setFieldValue(this.config.outputField, response.data);
        }

        this.showStatus(`Parsed ${this.getRowCount(response.data)} rows`, 'success');

        // Fire event
        this.dispatchEvent('onParse', {
          fileName: this.selectedFile.name,
          data: response.data,
          rowCount: this.getRowCount(response.data)
        });

      } catch (error) {
        this.showStatus(error.message, 'error');
        this.dispatchEvent('onError', { error: error.message });
      }
    }

    /**
     * Call a LeForge plugin endpoint
     * This is the bridge between the integration and the plugin
     */
    async callLeForgePlugin(pluginId, endpoint, payload) {
      const url = `${this.config.leforgeUrl}/plugins/${pluginId}/${endpoint}`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return response.json();
    }

    readFileAsBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    getRowCount(data) {
      if (Array.isArray(data)) return data.length;
      if (data?.data) return data.data.length;
      return 0;
    }

    renderPreview(data) {
      const container = this.container.querySelector('.preview-container');
      const tableDiv = this.container.querySelector('.preview-table');
      const infoDiv = this.container.querySelector('.data-info');

      const rows = Array.isArray(data) ? data : (data.data || []);
      const previewRows = rows.slice(0, this.config.previewRows);
      
      if (previewRows.length === 0) {
        container.style.display = 'none';
        return;
      }

      // Get headers
      const headers = typeof previewRows[0] === 'object' && !Array.isArray(previewRows[0])
        ? Object.keys(previewRows[0])
        : previewRows[0]?.map((_, i) => `Column ${i + 1}`) || [];

      // Build table
      let html = '<table><thead><tr>';
      headers.forEach(h => html += `<th>${this.escapeHtml(String(h))}</th>`);
      html += '</tr></thead><tbody>';

      previewRows.forEach(row => {
        html += '<tr>';
        if (typeof row === 'object' && !Array.isArray(row)) {
          headers.forEach(h => html += `<td>${this.escapeHtml(String(row[h] ?? ''))}</td>`);
        } else if (Array.isArray(row)) {
          row.forEach(cell => html += `<td>${this.escapeHtml(String(cell ?? ''))}</td>`);
        }
        html += '</tr>';
      });

      html += '</tbody></table>';
      tableDiv.innerHTML = html;

      // Show row count info
      infoDiv.textContent = `Total rows: ${rows.length}${data.sheets ? ` | Sheets: ${data.sheets.join(', ')}` : ''}`;
      
      container.style.display = 'block';
    }

    escapeHtml(str) {
      const div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    }

    showStatus(message, type) {
      const el = this.container.querySelector('.status-message');
      el.textContent = message;
      el.className = `status-message ${type}`;
      el.style.display = 'block';
    }

    setFieldValue(fieldId, value) {
      // For Nintex Forms, use NWF$ or NF API
      // For standard HTML, use document.getElementById
      const field = document.getElementById(fieldId);
      if (field) {
        if (field.tagName === 'INPUT' || field.tagName === 'TEXTAREA') {
          field.value = typeof value === 'string' ? value : JSON.stringify(value);
        }
      }
      
      // Nintex Forms specific
      if (typeof NWF$ !== 'undefined') {
        NWF$(`#${fieldId}`).val(JSON.stringify(value)).trigger('change');
      }
    }

    dispatchEvent(eventName, detail) {
      // Call configured callback
      if (this.config[eventName]) {
        this.config[eventName](detail);
      }
      
      // Dispatch DOM event
      document.dispatchEvent(new CustomEvent(`leforge:${eventName}`, { detail }));
    }

    // Public API for external access
    getData() {
      return this.parsedData;
    }

    getHeaders() {
      if (!this.parsedData) return [];
      const data = Array.isArray(this.parsedData) ? this.parsedData : (this.parsedData.data || []);
      if (data.length === 0) return [];
      return typeof data[0] === 'object' && !Array.isArray(data[0]) 
        ? Object.keys(data[0]) 
        : [];
    }

    getColumn(columnName) {
      if (!this.parsedData) return [];
      const data = Array.isArray(this.parsedData) ? this.parsedData : (this.parsedData.data || []);
      return data.map(row => row[columnName]);
    }
  }

  // Export for different module systems
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = LeForgeExcelParser;
  } else if (typeof window !== 'undefined') {
    window.LeForgeExcelParser = LeForgeExcelParser;
  }
})();
