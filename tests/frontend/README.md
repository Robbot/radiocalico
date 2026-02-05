# Frontend Testing Framework

## Overview
This directory contains the frontend unit tests for RadioCalico, built with Vitest.

## Test Files
- `player.test.js` - Core player functionality, user ID management, event handlers
- `ratings.test.js` - Rating-specific functionality, edge cases, validation
- `fixtures/tracks.json` - Mock data for testing

## Running Tests

### Run all frontend tests
```bash
npm run test:frontend
```

### Run in watch mode
```bash
npm run test:frontend:watch
```

### Run with coverage
```bash
npm run test:frontend:coverage
```

### Run a specific test file
```bash
npx vitest tests/frontend/player.test.js
```

## Test Structure

### User ID Management Tests
- Tests for `initializeUserId()` function
- Validates user ID format (`user_<timestamp>_<random>`)
- Tests localStorage persistence
- Tests uniqueness of generated IDs

### Rating Handler Tests
- Thumbs up (rating_type=1) submissions
- Thumbs down (rating_type=-1) submissions
- Success and error responses
- Duplicate rating handling
- Network error handling

### Rating Status Tests
- Checking if user has rated a track
- Retrieving existing rating type
- Handling unrated tracks

### Edge Cases
- Rating without current track ID
- Rating without user ID
- Invalid rating types
- Empty request bodies
- Concurrent rating attempts

## Mocking
Tests use Vitest's built-in mocking:
- `localStorage` is mocked for user ID persistence
- `fetch` is mocked for API calls
- DOM elements are mocked for UI testing

## Coverage
Tests cover:
- User ID generation and persistence
- Rating submission logic
- API request structure
- Error handling
- UI state management
- Rating count updates
