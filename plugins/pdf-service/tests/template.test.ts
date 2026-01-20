import { templateService } from '../src/services/template.service';

describe('TemplateService', () => {
  describe('render', () => {
    it('should render a simple template', () => {
      const template = '<h1>{{title}}</h1>';
      const data = { title: 'Hello World' };
      const result = templateService.render(template, data);
      expect(result).toBe('<h1>Hello World</h1>');
    });

    it('should render nested data', () => {
      const template = '<p>{{user.name}} - {{user.email}}</p>';
      const data = { user: { name: 'John', email: 'john@example.com' } };
      const result = templateService.render(template, data);
      expect(result).toBe('<p>John - john@example.com</p>');
    });

    it('should render arrays with each helper', () => {
      const template = '<ul>{{#each items}}<li>{{this}}</li>{{/each}}</ul>';
      const data = { items: ['One', 'Two', 'Three'] };
      const result = templateService.render(template, data);
      expect(result).toBe('<ul><li>One</li><li>Two</li><li>Three</li></ul>');
    });

    it('should handle conditionals with if helper', () => {
      const template = '{{#if active}}Active{{else}}Inactive{{/if}}';
      expect(templateService.render(template, { active: true })).toBe('Active');
      expect(templateService.render(template, { active: false })).toBe('Inactive');
    });

    it('should escape HTML by default', () => {
      const template = '{{content}}';
      const data = { content: '<script>alert(1)</script>' };
      const result = templateService.render(template, data);
      expect(result).toContain('&lt;script&gt;');
      expect(result).not.toContain('<script>');
    });

    it('should render raw HTML with triple braces', () => {
      const template = '{{{content}}}';
      const data = { content: '<strong>Bold</strong>' };
      const result = templateService.render(template, data);
      expect(result).toBe('<strong>Bold</strong>');
    });
  });

  describe('custom helpers', () => {
    describe('conditional helpers', () => {
      it('eq helper should check equality', () => {
        const template = '{{#if (eq a b)}}equal{{else}}not equal{{/if}}';
        expect(templateService.render(template, { a: 1, b: 1 })).toBe('equal');
        expect(templateService.render(template, { a: 1, b: 2 })).toBe('not equal');
      });

      it('ne helper should check inequality', () => {
        const template = '{{#if (ne a b)}}different{{else}}same{{/if}}';
        expect(templateService.render(template, { a: 1, b: 2 })).toBe('different');
        expect(templateService.render(template, { a: 1, b: 1 })).toBe('same');
      });

      it('lt/lte/gt/gte helpers should work', () => {
        expect(templateService.render('{{#if (lt a b)}}yes{{/if}}', { a: 1, b: 2 })).toBe('yes');
        expect(templateService.render('{{#if (lte a b)}}yes{{/if}}', { a: 2, b: 2 })).toBe('yes');
        expect(templateService.render('{{#if (gt a b)}}yes{{/if}}', { a: 3, b: 2 })).toBe('yes');
        expect(templateService.render('{{#if (gte a b)}}yes{{/if}}', { a: 2, b: 2 })).toBe('yes');
      });

      it('and helper should work', () => {
        const template = '{{#if (and a b)}}yes{{/if}}';
        expect(templateService.render(template, { a: true, b: true })).toBe('yes');
        expect(templateService.render(template, { a: true, b: false })).toBe('');
      });

      it('or helper should work', () => {
        const template = '{{#if (or a b)}}yes{{/if}}';
        expect(templateService.render(template, { a: false, b: true })).toBe('yes');
        expect(templateService.render(template, { a: false, b: false })).toBe('');
      });

      it('not helper should work', () => {
        const template = '{{#if (not a)}}yes{{/if}}';
        expect(templateService.render(template, { a: false })).toBe('yes');
        expect(templateService.render(template, { a: true })).toBe('');
      });
    });

    describe('string helpers', () => {
      it('uppercase helper should work', () => {
        const template = '{{uppercase text}}';
        expect(templateService.render(template, { text: 'hello' })).toBe('HELLO');
      });

      it('lowercase helper should work', () => {
        const template = '{{lowercase text}}';
        expect(templateService.render(template, { text: 'HELLO' })).toBe('hello');
      });

      it('capitalize helper should work', () => {
        const template = '{{capitalize text}}';
        expect(templateService.render(template, { text: 'hello' })).toBe('Hello');
      });

      it('truncate helper should work', () => {
        const template = '{{truncate text 10}}';
        expect(templateService.render(template, { text: 'Hello World This Is Long' })).toBe('Hello Worl...');
      });

      it('replace helper should work', () => {
        const template = '{{replace text "world" "universe"}}';
        expect(templateService.render(template, { text: 'hello world' })).toBe('hello universe');
      });

      it('split helper should work', () => {
        const template = '{{#each (split text ",")}}{{this}} {{/each}}';
        expect(templateService.render(template, { text: 'a,b,c' })).toBe('a b c ');
      });

      it('join helper should work', () => {
        const template = '{{join arr ", "}}';
        expect(templateService.render(template, { arr: ['a', 'b', 'c'] })).toBe('a, b, c');
      });
    });

    describe('number helpers', () => {
      it('formatNumber helper should work', () => {
        const template = '{{formatNumber num 2}}';
        expect(templateService.render(template, { num: 123.4567 })).toBe('123.46');
      });

      it('formatCurrency helper should work', () => {
        const template = '{{formatCurrency num "USD" "en-US"}}';
        const result = templateService.render(template, { num: 1234.56 });
        expect(result).toContain('1,234.56');
      });

      it('formatPercent helper should work', () => {
        const template = '{{formatPercent num 1}}';
        expect(templateService.render(template, { num: 0.756 })).toBe('75.6%');
      });

      it('math helpers should work', () => {
        expect(templateService.render('{{add a b}}', { a: 5, b: 3 })).toBe('8');
        expect(templateService.render('{{subtract a b}}', { a: 5, b: 3 })).toBe('2');
        expect(templateService.render('{{multiply a b}}', { a: 5, b: 3 })).toBe('15');
        expect(templateService.render('{{divide a b}}', { a: 6, b: 3 })).toBe('2');
        expect(templateService.render('{{mod a b}}', { a: 7, b: 3 })).toBe('1');
      });

      it('rounding helpers should work', () => {
        expect(templateService.render('{{round num}}', { num: 4.6 })).toBe('5');
        expect(templateService.render('{{floor num}}', { num: 4.9 })).toBe('4');
        expect(templateService.render('{{ceil num}}', { num: 4.1 })).toBe('5');
        expect(templateService.render('{{abs num}}', { num: -5 })).toBe('5');
      });
    });

    describe('date helpers', () => {
      it('formatDate helper should work', () => {
        const template = '{{formatDate date "medium" "en-US"}}';
        const result = templateService.render(template, { date: '2024-01-15' });
        expect(result).toContain('Jan');
        expect(result).toContain('15');
        expect(result).toContain('2024');
      });

      it('year helper should work', () => {
        const template = '{{year date}}';
        expect(templateService.render(template, { date: '2024-01-15' })).toBe('2024');
      });

      it('month helper should work', () => {
        const template = '{{month date}}';
        expect(templateService.render(template, { date: '2024-03-15' })).toBe('3');
      });

      it('day helper should work', () => {
        const template = '{{day date}}';
        expect(templateService.render(template, { date: '2024-01-25' })).toBe('25');
      });
    });

    describe('array helpers', () => {
      it('first helper should work', () => {
        const template = '{{first arr}}';
        expect(templateService.render(template, { arr: [1, 2, 3] })).toBe('1');
      });

      it('last helper should work', () => {
        const template = '{{last arr}}';
        expect(templateService.render(template, { arr: [1, 2, 3] })).toBe('3');
      });

      it('length helper should work', () => {
        const template = '{{length arr}}';
        expect(templateService.render(template, { arr: [1, 2, 3, 4, 5] })).toBe('5');
      });

      it('includes helper should work', () => {
        const template = '{{#if (includes arr 2)}}yes{{/if}}';
        expect(templateService.render(template, { arr: [1, 2, 3] })).toBe('yes');
      });

      it('sum helper should work', () => {
        const template = '{{sum arr}}';
        expect(templateService.render(template, { arr: [1, 2, 3, 4] })).toBe('10');
      });

      it('avg helper should work', () => {
        const template = '{{avg arr}}';
        expect(templateService.render(template, { arr: [10, 20, 30] })).toBe('20');
      });
    });

    describe('object helpers', () => {
      it('keys helper should work', () => {
        const template = '{{#each (keys obj)}}{{this}} {{/each}}';
        const result = templateService.render(template, { obj: { a: 1, b: 2 } });
        expect(result).toContain('a');
        expect(result).toContain('b');
      });

      it('values helper should work', () => {
        const template = '{{#each (values obj)}}{{this}} {{/each}}';
        const result = templateService.render(template, { obj: { a: 1, b: 2 } });
        expect(result).toContain('1');
        expect(result).toContain('2');
      });

      it('lookup helper should work', () => {
        const template = '{{lookup obj key}}';
        expect(templateService.render(template, { obj: { name: 'John' }, key: 'name' })).toBe('John');
      });

      it('json helper should work', () => {
        const template = '{{json obj}}';
        const result = templateService.render(template, { obj: { a: 1 } });
        expect(result).toContain('"a": 1');
      });
    });

    describe('utility helpers', () => {
      it('default helper should work', () => {
        const template = '{{default value "N/A"}}';
        expect(templateService.render(template, { value: 'Hello' })).toBe('Hello');
        expect(templateService.render(template, { value: null })).toBe('N/A');
        expect(templateService.render(template, { value: '' })).toBe('N/A');
      });

      it('coalesce helper should work', () => {
        const template = '{{coalesce a b c}}';
        expect(templateService.render(template, { a: null, b: '', c: 'value' })).toBe('value');
      });

      it('repeat helper should work', () => {
        const template = '{{#repeat 3}}{{index}}-{{/repeat}}';
        expect(templateService.render(template, {})).toBe('0-1-2-');
      });
    });
  });

  describe('validate', () => {
    it('should validate correct templates', () => {
      const result = templateService.validate('<p>{{name}}</p>');
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should catch syntax errors', () => {
      const result = templateService.validate('<p>{{#if}}</p>'); // Missing condition
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should catch unclosed blocks', () => {
      const result = templateService.validate('{{#if condition}}content'); // Missing {{/if}}
      expect(result.valid).toBe(false);
    });
  });

  describe('getAvailableHelpers', () => {
    it('should return list of registered helpers', () => {
      const helpers = templateService.getAvailableHelpers();
      expect(helpers).toContain('eq');
      expect(helpers).toContain('uppercase');
      expect(helpers).toContain('formatNumber');
      expect(helpers).toContain('formatDate');
      expect(helpers).toContain('first');
      expect(helpers).toContain('default');
    });
  });

  describe('partials', () => {
    it('should render with partials', () => {
      const template = '{{> header}}<main>{{content}}</main>';
      const result = templateService.render(template, 
        { content: 'Main content' },
        { partials: { header: '<header>Header</header>' } }
      );
      expect(result).toBe('<header>Header</header><main>Main content</main>');
    });
  });
});
