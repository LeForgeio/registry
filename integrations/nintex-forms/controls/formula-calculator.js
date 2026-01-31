/**
 * LeForge Formula Calculator Control for Nintex Forms
 * 
 * Evaluates Excel-style formulas using the LeForge Formula Engine.
 * 
 * @version 1.0.0
 * @author LeForge
 */

(function() {
  'use strict';

  const CONTROL_NAME = 'LeForgeFormulaCalculator';
  const VERSION = '1.0.0';

  /**
   * LeForge Formula Calculator Control
   */
  class LeForgeFormulaCalculator {
    constructor(element, options) {
      this.element = element;
      this.options = Object.assign({
        leforgeUrl: '',
        apiKey: '',
        formula: '',
        variables: {},  // Maps formula variables to form field names
        outputField: '',
        precision: 2,
        autoCalculate: true,
        debounceMs: 300,
        showFormula: false,
        errorValue: '#ERROR',
        timeout: 10000
      }, options);

      this.isCalculating = false;
      this.debounceTimer = null;
      this.variableFields = [];

      this.init();
    }

    init() {
      this.parseVariables();
      this.render();
      this.bindEvents();

      if (this.options.autoCalculate) {
        this.watchVariableFields();
        // Initial calculation
        setTimeout(() => this.calculate(), 100);
      }
    }

    parseVariables() {
      // Extract variables from formula (e.g., {FieldName} or just map from options)
      const formulaVars = this.options.formula.match(/\{([^}]+)\}/g) || [];
      formulaVars.forEach(v => {
        const varName = v.replace(/[{}]/g, '');
        if (!this.options.variables[varName]) {
          this.options.variables[varName] = varName;
        }
      });
    }

    render() {
      this.container = document.createElement('div');
      this.container.className = 'leforge-formula-calc';
      this.container.innerHTML = `
        <div class="leforge-formula-wrapper">
          ${this.options.showFormula ? `
            <div class="leforge-formula-display">
              <code>${this.escapeHtml(this.options.formula)}</code>
            </div>
          ` : ''}
          ${!this.options.autoCalculate ? `
            <button type="button" class="leforge-calc-btn">
              <span class="btn-text">Calculate</span>
              <span class="btn-spinner" style="display: none;">⟳</span>
            </button>
          ` : ''}
          <div class="leforge-calc-status"></div>
        </div>
      `;

      this.element.appendChild(this.container);
      
      this.button = this.container.querySelector('.leforge-calc-btn');
      this.statusEl = this.container.querySelector('.leforge-calc-status');

      this.addStyles();
    }

    addStyles() {
      if (document.getElementById('leforge-formula-styles')) return;

      const styles = document.createElement('style');
      styles.id = 'leforge-formula-styles';
      styles.textContent = `
        .leforge-formula-calc {
          margin: 4px 0;
        }
        .leforge-formula-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
        .leforge-formula-display {
          background: #f3f4f6;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
        }
        .leforge-formula-display code {
          color: #6366f1;
        }
        .leforge-calc-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 6px 12px;
          background: #6366f1;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 13px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .leforge-calc-btn:hover {
          background: #4f46e5;
        }
        .leforge-calc-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .leforge-calc-btn .btn-spinner {
          animation: leforge-spin 1s linear infinite;
        }
        .leforge-calc-status {
          font-size: 12px;
          color: #666;
        }
        .leforge-calc-status.error {
          color: #dc2626;
        }
      `;
      document.head.appendChild(styles);
    }

    bindEvents() {
      if (this.button) {
        this.button.addEventListener('click', () => this.calculate());
      }
    }

    watchVariableFields() {
      Object.values(this.options.variables).forEach(fieldName => {
        const field = this.getFormField(fieldName);
        if (field && !this.variableFields.includes(field)) {
          this.variableFields.push(field);
          field.addEventListener('input', () => this.scheduleCalculation());
          field.addEventListener('change', () => this.scheduleCalculation());
        }
      });
    }

    scheduleCalculation() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => this.calculate(), this.options.debounceMs);
    }

    async calculate() {
      if (this.isCalculating) return;
      if (!this.options.formula) {
        this.setStatus('No formula configured', 'error');
        return;
      }

      // Collect variable values
      const variables = {};
      let hasAllValues = true;

      for (const [varName, fieldName] of Object.entries(this.options.variables)) {
        const value = this.getFieldValue(fieldName);
        if (value === '' || value === null || value === undefined) {
          hasAllValues = false;
          variables[varName] = 0; // Default to 0 for missing values
        } else {
          // Try to parse as number
          const numValue = parseFloat(value);
          variables[varName] = isNaN(numValue) ? value : numValue;
        }
      }

      this.setLoading(true);
      this.setStatus('');

      try {
        // Prepare formula with variable substitution
        let formula = this.options.formula;
        for (const [varName, value] of Object.entries(variables)) {
          // Replace {VarName} with actual value
          formula = formula.replace(new RegExp(`\\{${varName}\\}`, 'g'), value);
          // Also replace bare variable names for simple formulas
          formula = formula.replace(new RegExp(`\\b${varName}\\b`, 'g'), value);
        }

        let result;

        if (this.options.leforgeUrl) {
          // Use LeForge Formula Engine
          result = await this.callLeForge(formula, variables);
        } else {
          // Local evaluation fallback (basic math only)
          result = this.evaluateLocal(formula);
        }

        // Format result
        if (typeof result === 'number') {
          result = parseFloat(result.toFixed(this.options.precision));
        }

        if (this.options.outputField) {
          this.setFieldValue(this.options.outputField, result);
        }

        this.triggerEvent('onCalculate', { formula, variables, result });
      } catch (error) {
        console.error('LeForge Formula Calculator error:', error);
        
        if (this.options.outputField) {
          this.setFieldValue(this.options.outputField, this.options.errorValue);
        }
        
        this.setStatus(error.message || 'Calculation failed', 'error');
        this.triggerEvent('onError', { error: error.message });
      } finally {
        this.setLoading(false);
      }
    }

    async callLeForge(formula, variables) {
      const url = `${this.options.leforgeUrl.replace(/\/$/, '')}/invoke/formula-engine/evaluate`;
      
      const body = {
        formula: formula,
        variables: variables
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

        const data = await response.json();
        return data.result !== undefined ? data.result : data.value;
      } catch (error) {
        clearTimeout(timeout);
        if (error.name === 'AbortError') {
          throw new Error('Request timed out');
        }
        throw error;
      }
    }

    evaluateLocal(formula) {
      // Basic local evaluation for simple math expressions
      // WARNING: This uses eval - only for simple trusted formulas
      try {
        // Remove Excel-style = prefix
        let expr = formula.replace(/^=/, '').trim();
        
        // Handle basic Excel functions
        expr = this.convertExcelFunctions(expr);
        
        // Safe evaluation using Function constructor
        const safeEval = new Function('return ' + expr);
        return safeEval();
      } catch (e) {
        throw new Error('Invalid formula: ' + e.message);
      }
    }

    convertExcelFunctions(expr) {
      // Convert common Excel functions to JavaScript
      const conversions = {
        'SUM': (args) => `(${args.split(',').join('+')})`,
        'AVERAGE': (args) => {
          const parts = args.split(',');
          return `((${parts.join('+')})//${parts.length})`;
        },
        'MIN': (args) => `Math.min(${args})`,
        'MAX': (args) => `Math.max(${args})`,
        'ROUND': (args) => {
          const [num, decimals = 0] = args.split(',');
          return `(Math.round(${num}*Math.pow(10,${decimals}))/Math.pow(10,${decimals}))`;
        },
        'ABS': (args) => `Math.abs(${args})`,
        'SQRT': (args) => `Math.sqrt(${args})`,
        'POWER': (args) => `Math.pow(${args})`,
        'IF': (args) => {
          const [condition, trueVal, falseVal] = this.splitArgs(args);
          return `(${condition}?${trueVal}:${falseVal})`;
        }
      };

      let result = expr;
      for (const [func, converter] of Object.entries(conversions)) {
        const regex = new RegExp(`${func}\\(([^)]+)\\)`, 'gi');
        result = result.replace(regex, (_, args) => converter(args));
      }

      return result;
    }

    splitArgs(args) {
      // Split function arguments, respecting nested parentheses
      const result = [];
      let current = '';
      let depth = 0;
      
      for (const char of args) {
        if (char === '(' || char === '[') depth++;
        else if (char === ')' || char === ']') depth--;
        else if (char === ',' && depth === 0) {
          result.push(current.trim());
          current = '';
          continue;
        }
        current += char;
      }
      result.push(current.trim());
      return result;
    }

    setLoading(loading) {
      this.isCalculating = loading;
      if (this.button) {
        this.button.disabled = loading;
        const spinner = this.button.querySelector('.btn-spinner');
        const text = this.button.querySelector('.btn-text');
        if (spinner) spinner.style.display = loading ? 'inline' : 'none';
        if (text) text.style.display = loading ? 'none' : 'inline';
      }
    }

    setStatus(message, type = '') {
      if (this.statusEl) {
        this.statusEl.textContent = message;
        this.statusEl.className = 'leforge-calc-status' + (type ? ` ${type}` : '');
      }
    }

    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
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
    setFormula(formula) {
      this.options.formula = formula;
      this.parseVariables();
      if (this.options.autoCalculate) {
        this.watchVariableFields();
        this.calculate();
      }
    }

    addVariable(name, fieldName) {
      this.options.variables[name] = fieldName;
      this.watchVariableFields();
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
      document.querySelectorAll('[data-leforge-control="formula-calculator"]').forEach(el => {
        const options = JSON.parse(el.dataset.leforgeOptions || '{}');
        new LeForgeFormulaCalculator(el, options);
      });
    });
  }

  // Export
  window.LeForgeFormulaCalculator = LeForgeFormulaCalculator;
  window.LeForgeControls = window.LeForgeControls || {};
  window.LeForgeControls.FormulaCalculator = LeForgeFormulaCalculator;

  console.log(`LeForge Formula Calculator v${VERSION} loaded`);
})();
