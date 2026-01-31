/**
 * LeForge Data Lookup Control for Nintex Forms
 * 
 * Fetches data from LeForge services and populates form fields.
 * 
 * @version 1.0.0
 * @author LeForge
 */

(function() {
  'use strict';

  const CONTROL_NAME = 'LeForgeDataLookup';
  const VERSION = '1.0.0';

  /**
   * LeForge Data Lookup Control
   */
  class LeForgeDataLookup {
    constructor(element, options) {
      this.element = element;
      this.options = Object.assign({
        leforgeUrl: '',
        apiKey: '',
        endpoint: '',           // API endpoint (e.g., '/invoke/plugin/action')
        method: 'GET',          // HTTP method
        inputMapping: {},       // Maps form fields to request params
        outputMapping: {},      // Maps response fields to form fields
        triggerField: '',       // Field that triggers lookup on change
        buttonText: 'Lookup',
        loadingText: 'Looking up...',
        autoLookup: false,
        debounceMs: 500,
        cacheTime: 0,           // Cache results for N seconds (0 = no cache)
        timeout: 15000,
        showButton: true
      }, options);

      this.isLoading = false;
      this.debounceTimer = null;
      this.cache = new Map();

      this.init();
    }

    init() {
      this.render();
      this.bindEvents();

      if (this.options.autoLookup && this.options.triggerField) {
        this.watchTriggerField();
      }
    }

    render() {
      this.container = document.createElement('div');
      this.container.className = 'leforge-data-lookup';
      this.container.innerHTML = `
        <div class="leforge-lookup-wrapper">
          ${this.options.showButton ? `
            <button type="button" class="leforge-lookup-btn" ${!this.options.leforgeUrl ? 'disabled' : ''}>
              <span class="btn-icon">🔍</span>
              <span class="btn-text">${this.options.buttonText}</span>
              <span class="btn-spinner" style="display: none;">⟳</span>
            </button>
          ` : ''}
          <div class="leforge-lookup-status"></div>
        </div>
      `;

      this.element.appendChild(this.container);
      
      this.button = this.container.querySelector('.leforge-lookup-btn');
      this.statusEl = this.container.querySelector('.leforge-lookup-status');

      this.addStyles();
    }

    addStyles() {
      if (document.getElementById('leforge-lookup-styles')) return;

      const styles = document.createElement('style');
      styles.id = 'leforge-lookup-styles';
      styles.textContent = `
        .leforge-data-lookup {
          margin: 4px 0;
        }
        .leforge-lookup-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .leforge-lookup-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 6px 12px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .leforge-lookup-btn:hover:not(:disabled) {
          background: #2563eb;
        }
        .leforge-lookup-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .leforge-lookup-btn .btn-spinner {
          animation: leforge-spin 1s linear infinite;
        }
        .leforge-lookup-status {
          font-size: 12px;
          color: #666;
        }
        .leforge-lookup-status.error {
          color: #dc2626;
        }
        .leforge-lookup-status.success {
          color: #16a34a;
        }
      `;
      document.head.appendChild(styles);
    }

    bindEvents() {
      if (this.button) {
        this.button.addEventListener('click', () => this.lookup());
      }
    }

    watchTriggerField() {
      const field = this.getFormField(this.options.triggerField);
      if (field) {
        field.addEventListener('change', () => this.scheduleLookup());
        field.addEventListener('blur', () => this.scheduleLookup());
      }
    }

    scheduleLookup() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        const triggerValue = this.getFieldValue(this.options.triggerField);
        if (triggerValue) {
          this.lookup();
        }
      }, this.options.debounceMs);
    }

    async lookup() {
      if (this.isLoading) return;
      if (!this.options.leforgeUrl || !this.options.endpoint) {
        this.setStatus('Lookup not configured', 'error');
        return;
      }

      // Build request parameters from input mapping
      const params = {};
      for (const [paramName, fieldName] of Object.entries(this.options.inputMapping)) {
        params[paramName] = this.getFieldValue(fieldName);
      }

      // Check cache
      const cacheKey = JSON.stringify({ endpoint: this.options.endpoint, params });
      if (this.options.cacheTime > 0) {
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.options.cacheTime * 1000) {
          this.applyOutputMapping(cached.data);
          this.setStatus('Loaded from cache', 'success');
          return;
        }
      }

      this.setLoading(true);
      this.setStatus('');

      try {
        const data = await this.callLeForge(params);
        
        // Cache the result
        if (this.options.cacheTime > 0) {
          this.cache.set(cacheKey, { data, timestamp: Date.now() });
        }

        // Apply output mapping
        this.applyOutputMapping(data);

        this.setStatus('Lookup complete', 'success');
        this.triggerEvent('onLookup', { params, data });
      } catch (error) {
        console.error('LeForge Data Lookup error:', error);
        this.setStatus(error.message || 'Lookup failed', 'error');
        this.triggerEvent('onError', { error: error.message });
      } finally {
        this.setLoading(false);
      }
    }

    async callLeForge(params) {
      let url = `${this.options.leforgeUrl.replace(/\/$/, '')}${this.options.endpoint}`;
      
      const fetchOptions = {
        method: this.options.method,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.options.apiKey
        }
      };

      if (this.options.method === 'GET') {
        // Append params to URL
        const searchParams = new URLSearchParams();
        for (const [key, value] of Object.entries(params)) {
          if (value !== undefined && value !== null && value !== '') {
            searchParams.append(key, value);
          }
        }
        const queryString = searchParams.toString();
        if (queryString) {
          url += (url.includes('?') ? '&' : '?') + queryString;
        }
      } else {
        fetchOptions.body = JSON.stringify(params);
      }

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.options.timeout);
      fetchOptions.signal = controller.signal;

      try {
        const response = await fetch(url, fetchOptions);
        clearTimeout(timeout);

        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(error.error || `HTTP ${response.status}`);
        }

        return await response.json();
      } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
          throw new Error('Request timed out');
        }
        throw error;
      }
    }

    applyOutputMapping(data) {
      for (const [responsePath, fieldName] of Object.entries(this.options.outputMapping)) {
        const value = this.getNestedValue(data, responsePath);
        if (value !== undefined) {
          this.setFieldValue(fieldName, value);
        }
      }
    }

    getNestedValue(obj, path) {
      // Support dot notation: "data.items[0].name"
      const parts = path.replace(/\[(\d+)\]/g, '.$1').split('.');
      let current = obj;
      
      for (const part of parts) {
        if (current === undefined || current === null) return undefined;
        current = current[part];
      }
      
      return current;
    }

    setLoading(loading) {
      this.isLoading = loading;
      if (this.button) {
        this.button.disabled = loading;
        const spinner = this.button.querySelector('.btn-spinner');
        const text = this.button.querySelector('.btn-text');
        const icon = this.button.querySelector('.btn-icon');
        if (spinner) spinner.style.display = loading ? 'inline' : 'none';
        if (text) text.textContent = loading ? this.options.loadingText : this.options.buttonText;
        if (icon) icon.style.display = loading ? 'none' : 'inline';
      }
    }

    setStatus(message, type = '') {
      if (this.statusEl) {
        this.statusEl.textContent = message;
        this.statusEl.className = 'leforge-lookup-status' + (type ? ` ${type}` : '');
      }
    }

    getFormField(fieldName) {
      if (typeof NWF$ !== 'undefined') {
        return NWF$(`[data-controlname="${fieldName}"]`).find('input, textarea, select').get(0);
      }
      return document.querySelector(`[data-controlname="${fieldName}"] input, [data-controlname="${fieldName}"] textarea, [data-controlname="${fieldName}"] select`) ||
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
        field.value = typeof value === 'object' ? JSON.stringify(value) : value;
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
    setEndpoint(endpoint, method = 'GET') {
      this.options.endpoint = endpoint;
      this.options.method = method;
    }

    clearCache() {
      this.cache.clear();
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
      document.querySelectorAll('[data-leforge-control="data-lookup"]').forEach(el => {
        const options = JSON.parse(el.dataset.leforgeOptions || '{}');
        new LeForgeDataLookup(el, options);
      });
    });
  }

  // Export
  window.LeForgeDataLookup = LeForgeDataLookup;
  window.LeForgeControls = window.LeForgeControls || {};
  window.LeForgeControls.DataLookup = LeForgeDataLookup;

  console.log(`LeForge Data Lookup v${VERSION} loaded`);
})();
