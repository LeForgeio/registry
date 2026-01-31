/**
 * LeForge AI Text Generator Control for Nintex Forms
 * 
 * Generates or completes text using the LeForge LLM service.
 * 
 * @version 1.0.0
 * @author LeForge
 */

(function() {
  'use strict';

  // Control registration
  if (typeof NWF$ === 'undefined' && typeof window.NWF$ === 'undefined') {
    console.warn('LeForge AI Text Generator: Nintex Forms runtime not detected');
  }

  const CONTROL_NAME = 'LeForgeAITextGenerator';
  const VERSION = '1.0.0';

  /**
   * LeForge AI Text Generator Control
   */
  class LeForgeAITextGenerator {
    constructor(element, options) {
      this.element = element;
      this.options = Object.assign({
        leforgeUrl: '',
        apiKey: '',
        prompt: 'You are a helpful assistant.',
        inputField: '',
        outputField: '',
        maxTokens: 512,
        provider: 'default',
        model: '',
        temperature: 0.7,
        buttonText: 'Generate',
        loadingText: 'Generating...',
        timeout: 30000,
        autoGenerate: false,
        debounceMs: 500
      }, options);

      this.isGenerating = false;
      this.debounceTimer = null;

      this.init();
    }

    init() {
      this.render();
      this.bindEvents();

      if (this.options.autoGenerate && this.options.inputField) {
        this.watchInputField();
      }
    }

    render() {
      this.container = document.createElement('div');
      this.container.className = 'leforge-ai-generator';
      this.container.innerHTML = `
        <div class="leforge-ai-generator-wrapper">
          <button type="button" class="leforge-ai-btn" ${!this.options.leforgeUrl ? 'disabled' : ''}>
            <span class="btn-text">${this.options.buttonText}</span>
            <span class="btn-spinner" style="display: none;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32">
                  <animate attributeName="stroke-dashoffset" dur="1s" values="32;0" repeatCount="indefinite"/>
                </circle>
              </svg>
            </span>
          </button>
          <div class="leforge-ai-status"></div>
        </div>
      `;

      this.element.appendChild(this.container);
      
      this.button = this.container.querySelector('.leforge-ai-btn');
      this.buttonText = this.container.querySelector('.btn-text');
      this.buttonSpinner = this.container.querySelector('.btn-spinner');
      this.statusEl = this.container.querySelector('.leforge-ai-status');

      this.addStyles();
    }

    addStyles() {
      if (document.getElementById('leforge-ai-styles')) return;

      const styles = document.createElement('style');
      styles.id = 'leforge-ai-styles';
      styles.textContent = `
        .leforge-ai-generator {
          margin: 8px 0;
        }
        .leforge-ai-generator-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .leforge-ai-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }
        .leforge-ai-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #4f46e5, #7c3aed);
          transform: translateY(-1px);
        }
        .leforge-ai-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .leforge-ai-btn .btn-spinner svg {
          animation: leforge-spin 1s linear infinite;
        }
        @keyframes leforge-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .leforge-ai-status {
          font-size: 12px;
          color: #666;
        }
        .leforge-ai-status.error {
          color: #dc2626;
        }
        .leforge-ai-status.success {
          color: #16a34a;
        }
      `;
      document.head.appendChild(styles);
    }

    bindEvents() {
      this.button.addEventListener('click', () => this.generate());
    }

    watchInputField() {
      const inputEl = this.getFormField(this.options.inputField);
      if (!inputEl) return;

      inputEl.addEventListener('input', () => {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
          if (inputEl.value.trim()) {
            this.generate();
          }
        }, this.options.debounceMs);
      });
    }

    async generate() {
      if (this.isGenerating) return;
      if (!this.options.leforgeUrl) {
        this.setStatus('LeForge URL not configured', 'error');
        return;
      }

      const inputValue = this.options.inputField 
        ? this.getFieldValue(this.options.inputField)
        : '';

      if (this.options.inputField && !inputValue) {
        this.setStatus('Input field is empty', 'error');
        return;
      }

      this.setLoading(true);
      this.setStatus('');

      try {
        const response = await this.callLeForge(inputValue);
        
        if (response.response || response.content || response.text) {
          const result = response.response || response.content || response.text;
          
          if (this.options.outputField) {
            this.setFieldValue(this.options.outputField, result);
          }

          this.setStatus('Generated successfully', 'success');
          this.triggerEvent('onGenerate', { input: inputValue, output: result });
        } else {
          throw new Error('Invalid response format');
        }
      } catch (error) {
        console.error('LeForge AI Generator error:', error);
        this.setStatus(error.message || 'Generation failed', 'error');
        this.triggerEvent('onError', { error: error.message });
      } finally {
        this.setLoading(false);
      }
    }

    async callLeForge(input) {
      const url = `${this.options.leforgeUrl.replace(/\/$/, '')}/invoke/llm-service/chat`;
      
      const body = {
        message: input,
        system_prompt: this.options.prompt,
        max_tokens: this.options.maxTokens,
        temperature: this.options.temperature
      };

      if (this.options.provider && this.options.provider !== 'default') {
        body.provider = this.options.provider;
      }
      if (this.options.model) {
        body.model = this.options.model;
      }

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

        return await response.json();
      } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
          throw new Error('Request timed out');
        }
        throw error;
      }
    }

    setLoading(loading) {
      this.isGenerating = loading;
      this.button.disabled = loading;
      this.buttonText.textContent = loading ? this.options.loadingText : this.options.buttonText;
      this.buttonSpinner.style.display = loading ? 'inline' : 'none';
    }

    setStatus(message, type = '') {
      this.statusEl.textContent = message;
      this.statusEl.className = 'leforge-ai-status' + (type ? ` ${type}` : '');
    }

    getFormField(fieldName) {
      // Nintex Forms field lookup
      if (typeof NWF$ !== 'undefined') {
        return NWF$(`[data-controlname="${fieldName}"]`).find('input, textarea').get(0);
      }
      // Fallback to standard DOM
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
        // Trigger change event for form validation
        field.dispatchEvent(new Event('change', { bubbles: true }));
        field.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    triggerEvent(eventName, detail) {
      const event = new CustomEvent(`leforge:${eventName}`, {
        bubbles: true,
        detail: detail
      });
      this.element.dispatchEvent(event);
    }

    // Public API
    setPrompt(prompt) {
      this.options.prompt = prompt;
    }

    setProvider(provider, model) {
      this.options.provider = provider;
      if (model) this.options.model = model;
    }

    destroy() {
      if (this.container) {
        this.container.remove();
      }
    }
  }

  // Register with Nintex Forms if available
  if (typeof NWF !== 'undefined' && NWF.FormFiller) {
    NWF.FormFiller.Events.RegisterAfterReady(function() {
      document.querySelectorAll('[data-leforge-control="ai-text-generator"]').forEach(el => {
        const options = JSON.parse(el.dataset.leforgeOptions || '{}');
        new LeForgeAITextGenerator(el, options);
      });
    });
  }

  // Export for manual initialization
  window.LeForgeAITextGenerator = LeForgeAITextGenerator;
  window.LeForgeControls = window.LeForgeControls || {};
  window.LeForgeControls.AITextGenerator = LeForgeAITextGenerator;

  console.log(`LeForge AI Text Generator v${VERSION} loaded`);
})();
