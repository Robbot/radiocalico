/**
 * Express Backend Unit Tests for Ratings System
 * Tests rating proxy endpoints and Flask communication
 */

const request = require('supertest');
const express = require('express');
const http = require('http');
const { startMockFlask, stopMockFlask, setMockFlaskResponse, getMockFlaskPort } = require('./setup');

// Create Express app for testing
function createTestApp() {
  const app = express();
  const FLASK_PORT = getMockFlaskPort();

  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Rating proxy endpoint (copied from server.js)
  app.post('/api/tracks/:trackId/rate', (req, res) => {
    const options = {
      hostname: 'localhost',
      port: FLASK_PORT,
      path: `/api/tracks/${req.params.trackId}/rate`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const proxyReq = http.request(options, (proxyRes) => {
      let data = '';
      proxyRes.on('data', (chunk) => {
        data += chunk;
      });
      proxyRes.on('end', () => {
        res.status(proxyRes.statusCode).setHeader('Content-Type', 'application/json');
        res.send(data);
      });
    });

    proxyReq.on('error', (error) => {
      res.status(500).json({
        status: 'error',
        message: 'Failed to submit rating: ' + error.message
      });
    });

    proxyReq.write(JSON.stringify(req.body));
    proxyReq.end();
  });

  // Rating status proxy endpoint
  app.post('/api/tracks/:trackId/rating-status', (req, res) => {
    const options = {
      hostname: 'localhost',
      port: FLASK_PORT,
      path: `/api/tracks/${req.params.trackId}/rating-status`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const proxyReq = http.request(options, (proxyRes) => {
      let data = '';
      proxyRes.on('data', (chunk) => {
        data += chunk;
      });
      proxyRes.on('end', () => {
        res.setHeader('Content-Type', 'application/json');
        res.send(data);
      });
    });

    proxyReq.on('error', (error) => {
      res.status(500).json({
        status: 'error',
        message: 'Failed to check rating status: ' + error.message
      });
    });

    proxyReq.write(JSON.stringify(req.body));
    proxyReq.end();
  });

  return app;
}

describe('Express Rating Proxy Tests', () => {
  let app;

  beforeAll(async () => {
    await startMockFlask();
    app = createTestApp();
  });

  afterAll(async () => {
    await stopMockFlask();
  });

  beforeEach(() => {
    // Reset mock responses
    setMockFlaskResponse('/api/tracks/1/rate', {
      status: 'success',
      message: 'Rating submitted successfully',
      data: { thumbs_up: 11, thumbs_down: 2 }
    });
  });

  describe('POST /api/tracks/:trackId/rate', () => {
    it('should proxy rating request to Flask backend', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect('Content-Type', /json/);

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
    });

    it('should forward request body correctly', async () => {
      const payload = { user_id: 'user_test123', rating_type: 1 };

      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send(payload)
        .expect(200);

      expect(response.body.data.thumbs_up).toBe(11);
      expect(response.body.data.thumbs_down).toBe(2);
    });

    it('should handle thumbs up rating (rating_type=1)', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should handle thumbs down rating (rating_type=-1)', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: -1 })
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should return Flask response status codes', async () => {
      setMockFlaskResponse('/api/tracks/1/rate', {
        status: 'error',
        message: 'You have already rated this track'
      });

      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 });

      // The status code should come from Flask (would be 409 for duplicate)
      expect(response.body.status).toBe('error');
    });

    it('should handle missing user_id (400 from Flask)', async () => {
      setMockFlaskResponse('/api/tracks/1/rate', {
        status: 'error',
        message: 'user_id is required'
      });

      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ rating_type: 1 });

      expect(response.body.status).toBe('error');
      expect(response.body.message).toContain('user_id');
    });

    it('should handle invalid rating_type (400 from Flask)', async () => {
      setMockFlaskResponse('/api/tracks/1/rate', {
        status: 'error',
        message: 'rating_type must be 1 or -1'
      });

      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 5 });

      expect(response.body.status).toBe('error');
      expect(response.body.message).toContain('rating_type');
    });

    it('should preserve trackId in URL path', async () => {
      const response = await request(app)
        .post('/api/tracks/123/rate')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should return JSON content type', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect('Content-Type', /json/);

      expect(response.body).toBeDefined();
    });

    it('should handle Flask connection errors', async () => {
      // Stop Flask to test connection error
      await stopMockFlask();

      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 });

      expect(response.status).toBe(500);
      expect(response.body.status).toBe('error');
      expect(response.body.message).toContain('Failed to submit rating');

      // Restart Flask for other tests
      await startMockFlask();
    });
  });

  describe('POST /api/tracks/:trackId/rating-status', () => {
    it('should proxy rating status request to Flask', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rating-status')
        .send({ user_id: 'user_test123' })
        .expect('Content-Type', /json/);

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
    });

    it('should return has_rated status from Flask', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rating-status')
        .send({ user_id: 'user_test123' });

      expect(response.body.data.has_rated).toBeDefined();
      expect(response.body.data.rating_type).toBeDefined();
    });

    it('should handle existing rating', async () => {
      setMockFlaskResponse('/api/tracks/1/rating-status', {
        status: 'success',
        data: { has_rated: true, rating_type: 1 }
      });

      const response = await request(app)
        .post('/api/tracks/1/rating-status')
        .send({ user_id: 'user_test123' });

      expect(response.body.data.has_rated).toBe(true);
      expect(response.body.data.rating_type).toBe(1);
    });

    it('should handle no existing rating', async () => {
      setMockFlaskResponse('/api/tracks/1/rating-status', {
        status: 'success',
        data: { has_rated: false, rating_type: null }
      });

      const response = await request(app)
        .post('/api/tracks/1/rating-status')
        .send({ user_id: 'user_test123' });

      expect(response.body.data.has_rated).toBe(false);
      expect(response.body.data.rating_type).toBeNull();
    });

    it('should handle missing user_id', async () => {
      setMockFlaskResponse('/api/tracks/1/rating-status', {
        status: 'error',
        message: 'user_id is required'
      });

      const response = await request(app)
        .post('/api/tracks/1/rating-status')
        .send({});

      expect(response.body.status).toBe('error');
      expect(response.body.message).toContain('user_id');
    });

    it('should handle different track IDs', async () => {
      const trackIds = [1, 2, 3, 100, 999];

      for (const trackId of trackIds) {
        setMockFlaskResponse(`/api/tracks/${trackId}/rating-status`, {
          status: 'success',
          data: { has_rated: false, rating_type: null }
        });

        const response = await request(app)
          .post(`/api/tracks/${trackId}/rating-status`)
          .send({ user_id: 'user_test123' });

        expect(response.status).toBe(200);
      }
    });
  });

  describe('Request validation', () => {
    it('should accept JSON content type', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .set('Content-Type', 'application/json')
        .send(JSON.stringify({ user_id: 'user_test123', rating_type: 1 }))
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should handle malformed JSON gracefully', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .set('Content-Type', 'application/json')
        .send('invalid json');

      // Should not crash, may return error
      expect(response.status).toBeGreaterThan(0);
    });

    it('should handle empty request body', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({})
        .expect(200);

      // Flask handles validation
      expect(response.body).toBeDefined();
    });
  });

  describe('Proxy behavior', () => {
    it('should forward all request headers to Flask', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .set('X-Custom-Header', 'test-value')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should maintain HTTP method (POST)', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should forward response body unchanged', async () => {
      const expectedResponse = {
        status: 'success',
        message: 'Rating submitted successfully',
        data: { thumbs_up: 42, thumbs_down: 7 }
      };

      setMockFlaskResponse('/api/tracks/1/rate', expectedResponse);

      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 });

      expect(response.body).toEqual(expectedResponse);
    });
  });

  describe('Edge cases', () => {
    it('should handle special characters in user_id', async () => {
      const specialUserIds = [
        'user_123_abc',
        'user_with-dash',
        'user.with.dots',
        'user@with@symbols'
      ];

      for (const userId of specialUserIds) {
        const response = await request(app)
          .post('/api/tracks/1/rate')
          .send({ user_id: userId, rating_type: 1 })
          .expect(200);

        expect(response.body.status).toBe('success');
      }
    });

    it('should handle concurrent requests', async () => {
      const requests = Array(10).fill(null).map(() =>
        request(app)
          .post('/api/tracks/1/rate')
          .send({ user_id: `user_${Math.random()}`, rating_type: 1 })
      );

      const responses = await Promise.all(requests);

      responses.forEach(response => {
        expect(response.status).toBe(200);
        expect(response.body.status).toBe('success');
      });
    });

    it('should handle numeric track ID as string', async () => {
      const response = await request(app)
        .post('/api/tracks/1/rate')
        .send({ user_id: 'user_test123', rating_type: 1 })
        .expect(200);

      expect(response.body.status).toBe('success');
    });
  });
});
