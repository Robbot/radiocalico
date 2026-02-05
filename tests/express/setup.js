/**
 * Express Backend Test Setup
 * Configures test environment for Express server testing
 */

const express = require('express');
const request = require('supertest');
const http = require('http');

// Mock Flask backend for testing
let mockFlaskServer;
let mockFlaskPort = 5001;

// Mock Flask responses
const mockFlaskResponses = {
  '/api/now-playing': {
    status: 'success',
    data: {
      id: 1,
      artist: 'Test Artist',
      title: 'Test Track',
      album: 'Test Album',
      year: 2024,
      album_art_url: 'https://example.com/art.jpg',
      thumbs_up: 10,
      thumbs_down: 2
    }
  },
  '/api/recently-played': {
    status: 'success',
    data: [
      {
        id: 2,
        artist: 'Previous Artist',
        title: 'Previous Track',
        album: 'Previous Album',
        year: 2023
      }
    ]
  },
  '/api/tracks/1/rate': {
    status: 'success',
    message: 'Rating submitted successfully',
    data: { thumbs_up: 11, thumbs_down: 2 }
  },
  '/api/tracks/1/rating-status': {
    status: 'success',
    data: { has_rated: false, rating_type: null }
  },
  '/api/update-track': {
    status: 'success',
    message: 'Track updated',
    data: { artist: 'New Artist', title: 'New Track' }
  }
};

// Create a simple mock Flask server
function createMockFlaskServer() {
  const app = express();

  app.use(express.json());

  // Mock now-playing endpoint
  app.get('/api/now-playing', (req, res) => {
    res.json(mockFlaskResponses['/api/now-playing']);
  });

  // Mock recently-played endpoint
  app.get('/api/recently-played', (req, res) => {
    res.json(mockFlaskResponses['/api/recently-played']);
  });

  // Mock rate endpoint
  app.post('/api/tracks/:trackId/rate', (req, res) => {
    const { user_id, rating_type } = req.body;

    if (!user_id) {
      return res.status(400).json({
        status: 'error',
        message: 'user_id is required'
      });
    }

    if (rating_type !== 1 && rating_type !== -1) {
      return res.status(400).json({
        status: 'error',
        message: 'rating_type must be 1 or -1'
      });
    }

    res.json(mockFlaskResponses['/api/tracks/1/rate']);
  });

  // Mock rating-status endpoint
  app.post('/api/tracks/:trackId/rating-status', (req, res) => {
    const { user_id } = req.body;

    if (!user_id) {
      return res.status(400).json({
        status: 'error',
        message: 'user_id is required'
      });
    }

    res.json(mockFlaskResponses['/api/tracks/1/rating-status']);
  });

  // Mock update-track endpoint
  app.post('/api/update-track', (req, res) => {
    res.json(mockFlaskResponses['/api/update-track']);
  });

  return app;
}

// Start mock Flask server before tests
async function startMockFlask() {
  return new Promise((resolve) => {
    const app = createMockFlaskServer();
    mockFlaskServer = app.listen(mockFlaskPort, () => {
      console.log(`Mock Flask server listening on port ${mockFlaskPort}`);
      resolve();
    });
  });
}

// Stop mock Flask server after tests
async function stopMockFlask() {
  return new Promise((resolve) => {
    if (mockFlaskServer) {
      mockFlaskServer.close(() => {
        console.log('Mock Flask server closed');
        resolve();
      });
    } else {
      resolve();
    }
  });
}

// Set mock response for testing
function setMockFlaskResponse(endpoint, response) {
  mockFlaskResponses[endpoint] = response;
}

// Get mock Flask port
function getMockFlaskPort() {
  return mockFlaskPort;
}

module.exports = {
  startMockFlask,
  stopMockFlask,
  setMockFlaskResponse,
  getMockFlaskPort
};
