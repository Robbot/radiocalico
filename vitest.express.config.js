import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // Test environment - Node for Express tests
    environment: 'node',

    // Global setup
    globals: true,

    // Test files location
    include: ['tests/express/**/*.test.js'],

    // Exclude patterns
    exclude: ['node_modules/', 'dist/', 'tests/frontend/'],

    // Reporter
    reporter: ['verbose', 'json'],

    // Timeout
    testTimeout: 10000,
    hookTimeout: 10000,

    // Sequencing
    sequence: {
      shuffle: false,
      concurrent: true
    }
  },

  // Resolve aliases
  resolve: {
    alias: {
      '@': __dirname
    }
  }
});
