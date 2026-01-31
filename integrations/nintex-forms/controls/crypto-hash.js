/**
 * LeForge Crypto Hash Control for Nintex Forms
 * 
 * Generates cryptographic hashes of form field values.
 * 
 * @version 1.0.0
 * @author LeForge
 */

(function() {
  'use strict';

  const CONTROL_NAME = 'LeForgeCryptoHash';
  const VERSION = '1.0.0';

  /**
   * LeForge Crypto Hash Control
   */
  class LeForgeCryptoHash {
    constructor(element, options) {
      this.element = element;
      this.options = Object.assign({
        leforgeUrl: '',
        apiKey: '',
        algorithm: 'sha256',    // sha256, sha512, sha1, md5
        inputField: '',
        outputField: '',
        encoding: 'hex',        // hex, base64
        autoHash: false,
        debounceMs: 300,
        buttonText: 'Generate Hash',
        showAlgorithm: true,
        timeout: 10000
      }, options);

      this.isHashing = false;
      this.debounceTimer = null;

      this.init();
    }

    init() {
      this.render();
      this.bindEvents();

      if (this.options.autoHash && this.options.inputField) {
        this.watchInputField();
      }
    }

    render() {
      this.container = document.createElement('div');
      this.container.className = 'leforge-crypto-hash';
      this.container.innerHTML = `
        <div class="leforge-hash-wrapper">
          ${this.options.showAlgorithm ? `
            <select class="leforge-hash-algo">
              <option value="sha256" ${this.options.algorithm === 'sha256' ? 'selected' : ''}>SHA-256</option>
              <option value="sha512" ${this.options.algorithm === 'sha512' ? 'selected' : ''}>SHA-512</option>
              <option value="sha1" ${this.options.algorithm === 'sha1' ? 'selected' : ''}>SHA-1</option>
              <option value="md5" ${this.options.algorithm === 'md5' ? 'selected' : ''}>MD5</option>
            </select>
          ` : ''}
          ${!this.options.autoHash ? `
            <button type="button" class="leforge-hash-btn">
              <span class="btn-icon">🔐</span>
              <span class="btn-text">${this.options.buttonText}</span>
              <span class="btn-spinner" style="display: none;">⟳</span>
            </button>
          ` : ''}
          <div class="leforge-hash-status"></div>
        </div>
      `;

      this.element.appendChild(this.container);
      
      this.button = this.container.querySelector('.leforge-hash-btn');
      this.algoSelect = this.container.querySelector('.leforge-hash-algo');
      this.statusEl = this.container.querySelector('.leforge-hash-status');

      this.addStyles();
    }

    addStyles() {
      if (document.getElementById('leforge-hash-styles')) return;

      const styles = document.createElement('style');
      styles.id = 'leforge-hash-styles';
      styles.textContent = `
        .leforge-crypto-hash {
          margin: 4px 0;
        }
        .leforge-hash-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
        .leforge-hash-algo {
          padding: 6px 8px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 13px;
          background: white;
        }
        .leforge-hash-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 6px 12px;
          background: #059669;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .leforge-hash-btn:hover:not(:disabled) {
          background: #047857;
        }
        .leforge-hash-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .leforge-hash-btn .btn-spinner {
          animation: leforge-spin 1s linear infinite;
        }
        .leforge-hash-status {
          font-size: 12px;
          color: #666;
        }
        .leforge-hash-status.error {
          color: #dc2626;
        }
        .leforge-hash-status.success {
          color: #16a34a;
        }
      `;
      document.head.appendChild(styles);
    }

    bindEvents() {
      if (this.button) {
        this.button.addEventListener('click', () => this.hash());
      }
      if (this.algoSelect) {
        this.algoSelect.addEventListener('change', (e) => {
          this.options.algorithm = e.target.value;
          if (this.options.autoHash) {
            this.hash();
          }
        });
      }
    }

    watchInputField() {
      const field = this.getFormField(this.options.inputField);
      if (field) {
        field.addEventListener('input', () => this.scheduleHash());
        field.addEventListener('change', () => this.scheduleHash());
      }
    }

    scheduleHash() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        const value = this.getFieldValue(this.options.inputField);
        if (value) {
          this.hash();
        }
      }, this.options.debounceMs);
    }

    async hash() {
      if (this.isHashing) return;

      const inputValue = this.options.inputField 
        ? this.getFieldValue(this.options.inputField)
        : '';

      if (!inputValue) {
        this.setStatus('Input field is empty', 'error');
        return;
      }

      this.setLoading(true);
      this.setStatus('');

      try {
        let hashValue;

        if (this.options.leforgeUrl) {
          // Use LeForge Crypto Service
          hashValue = await this.callLeForge(inputValue);
        } else {
          // Use Web Crypto API fallback
          hashValue = await this.hashLocal(inputValue);
        }

        if (this.options.outputField) {
          this.setFieldValue(this.options.outputField, hashValue);
        }

        this.setStatus(`${this.options.algorithm.toUpperCase()} hash generated`, 'success');
        this.triggerEvent('onHash', { 
          algorithm: this.options.algorithm, 
          hash: hashValue 
        });
      } catch (error) {
        console.error('LeForge Crypto Hash error:', error);
        this.setStatus(error.message || 'Hash failed', 'error');
        this.triggerEvent('onError', { error: error.message });
      } finally {
        this.setLoading(false);
      }
    }

    async callLeForge(data) {
      const url = `${this.options.leforgeUrl.replace(/\/$/, '')}/invoke/crypto-service/hash`;
      
      const body = {
        data: data,
        algorithm: this.options.algorithm,
        encoding: this.options.encoding
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
        return result.hash || result.result || result.data;
      } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
          throw new Error('Request timed out');
        }
        throw error;
      }
    }

    async hashLocal(data) {
      // Web Crypto API fallback
      const encoder = new TextEncoder();
      const dataBuffer = encoder.encode(data);

      const algoMap = {
        'sha256': 'SHA-256',
        'sha512': 'SHA-512',
        'sha1': 'SHA-1',
        'md5': null  // Not supported in Web Crypto
      };

      const algo = algoMap[this.options.algorithm];
      if (!algo) {
        throw new Error(`${this.options.algorithm} not supported locally. Configure LeForge URL.`);
      }

      const hashBuffer = await crypto.subtle.digest(algo, dataBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));

      if (this.options.encoding === 'base64') {
        return btoa(String.fromCharCode(...hashArray));
      }
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    setLoading(loading) {
      this.isHashing = loading;
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
        this.statusEl.className = 'leforge-hash-status' + (type ? ` ${type}` : '');
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
    setAlgorithm(algorithm) {
      this.options.algorithm = algorithm;
      if (this.algoSelect) {
        this.algoSelect.value = algorithm;
      }
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
      document.querySelectorAll('[data-leforge-control="crypto-hash"]').forEach(el => {
        const options = JSON.parse(el.dataset.leforgeOptions || '{}');
        new LeForgeCryptoHash(el, options);
      });
    });
  }

  // Export
  window.LeForgeCryptoHash = LeForgeCryptoHash;
  window.LeForgeControls = window.LeForgeControls || {};
  window.LeForgeControls.CryptoHash = LeForgeCryptoHash;

  console.log(`LeForge Crypto Hash v${VERSION} loaded`);
})();
