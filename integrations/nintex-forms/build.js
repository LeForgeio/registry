/**
 * Build script for LeForge Nintex Forms Controls
 * 
 * Concatenates and minifies all control scripts into a single bundle.
 */

const fs = require('fs');
const path = require('path');

// Try to use terser for minification, fall back to no minification
let terser;
try {
  terser = require('terser');
} catch (e) {
  console.log('Terser not installed, skipping minification');
}

const controlsDir = path.join(__dirname, 'controls');
const distDir = path.join(__dirname, 'dist');

// Ensure dist directory exists
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// Control files in order
const controlFiles = [
  'ai-text-generator.js',
  'formula-calculator.js',
  'data-lookup.js',
  'crypto-hash.js',
  'qr-code-generator.js'
];

// Banner
const banner = `/**
 * LeForge Nintex Forms Controls Bundle
 * Version: 1.0.0
 * Generated: ${new Date().toISOString()}
 * 
 * Controls included:
 * - AI Text Generator
 * - Formula Calculator
 * - Data Lookup
 * - Crypto Hash
 * - QR Code Generator
 * 
 * https://leforge.io
 */

`;

async function build() {
  console.log('Building LeForge Nintex Forms Controls...\n');

  let bundledCode = banner;

  // Read and concatenate all control files
  for (const file of controlFiles) {
    const filePath = path.join(controlsDir, file);
    if (fs.existsSync(filePath)) {
      console.log(`  Adding: ${file}`);
      const code = fs.readFileSync(filePath, 'utf8');
      bundledCode += `\n// ============ ${file} ============\n${code}\n`;
    } else {
      console.warn(`  Warning: ${file} not found`);
    }
  }

  // Write unminified bundle
  const bundlePath = path.join(distDir, 'leforge-controls.js');
  fs.writeFileSync(bundlePath, bundledCode);
  console.log(`\n  Created: dist/leforge-controls.js (${(bundledCode.length / 1024).toFixed(2)} KB)`);

  // Minify if terser is available
  if (terser) {
    try {
      const minified = await terser.minify(bundledCode, {
        compress: {
          drop_console: false,  // Keep console.log for version info
          passes: 2
        },
        mangle: {
          reserved: [
            'LeForgeAITextGenerator',
            'LeForgeFormulaCalculator',
            'LeForgeDataLookup',
            'LeForgeCryptoHash',
            'LeForgeQRCodeGenerator',
            'LeForgeControls'
          ]
        },
        format: {
          comments: /LeForge Nintex Forms Controls Bundle/
        }
      });

      const minPath = path.join(distDir, 'leforge-controls.min.js');
      fs.writeFileSync(minPath, minified.code);
      console.log(`  Created: dist/leforge-controls.min.js (${(minified.code.length / 1024).toFixed(2)} KB)`);
    } catch (e) {
      console.error('  Minification failed:', e.message);
    }
  }

  // Copy individual controls to dist
  console.log('\n  Copying individual controls...');
  for (const file of controlFiles) {
    const src = path.join(controlsDir, file);
    const dest = path.join(distDir, file);
    if (fs.existsSync(src)) {
      fs.copyFileSync(src, dest);
    }
  }

  console.log('\nBuild complete!');
}

build().catch(console.error);
