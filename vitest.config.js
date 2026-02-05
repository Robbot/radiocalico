import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Test environment
    environment: 'jsdom',

    // Global setup
    globals: true,

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.js',
        'public/'
      ]
    },

    // Test files location
    include: ['tests/frontend/**/*.test.js'],

    // Exclude patterns
    exclude: ['node_modules/', 'dist/'],

    // Reporter
    reporter: ['verbose', 'json'],

    // Timeout
    testTimeout: 10000,
    hookTimeout: 10000
  },

  // Resolve aliases
  resolve: {
    alias: {
      '@': __dirname
    }
  }
});
