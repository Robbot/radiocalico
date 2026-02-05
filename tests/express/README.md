# Express Backend Testing Framework

## Overview
This directory contains the Express backend unit tests for RadioCalico, built with Vitest and Supertest.

## Test Files
- `setup.js` - Test environment setup, mock Flask server
- `ratings.test.js` - Rating proxy endpoint tests
- `server.test.js` - General server and proxy tests

## Running Tests

### Run all Express tests
```bash
npm run test:express
```

### Run with Vitest directly
```bash
npx vitest --config vitest.express.config.js
```

### Run a specific test file
```bash
npx vitest tests/express/ratings.test.js
```

## Test Structure

### Rating Proxy Tests (`ratings.test.js`)
- Tests for `POST /api/tracks/:trackId/rate`
- Tests for `POST /api/tracks/:trackId/rating-status`
- Request validation
- Response forwarding
- Flask communication errors
- Edge cases (special characters, concurrent requests)

### Server Tests (`server.test.js`)
- Tests for `GET /api/now-playing`
- Tests for `GET /api/recently-played`
- Tests for `POST /api/update-track`
- Content type handling
- Proxy behavior
- Error handling

## Mock Flask Server
Tests use a mock Flask server (`setup.js`) that:
- Runs on port 5001 (to avoid conflicts)
- Implements Flask endpoints
- Returns configurable mock responses
- Simulates error conditions

### Configuring Mock Responses
```javascript
setMockFlaskResponse('/api/tracks/1/rate', {
  status: 'success',
  data: { thumbs_up: 42, thumbs_down: 7 }
});
```

## Test Fixtures
- `app` - Express application for testing
- `mockFlaskServer` - Mock Flask HTTP server
- `mockFlaskPort` - Port for mock Flask (5001)

## Coverage
Tests cover:
- Request proxying to Flask
- Request/response forwarding
- Error handling
- Status code passthrough
- Request validation
- Connection error handling
- Content-Type handling
