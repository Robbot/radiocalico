/**
 * Express Backend Unit Tests for Server
 * Tests general server functionality and proxy endpoints
 */

const request = require('supertest');
const express = require('express');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { startMockFlask, stopMockFlask, setMockFlaskResponse, getMockFlaskPort } = require('./setup');

// Create Express app for testing
function createTestApp() {
  const app = express();
  const FLASK_PORT = getMockFlaskPort();

  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Now-playing proxy endpoint
  app.get('/api/now-playing', (req, res) => {
    const options = {
      hostname: 'localhost',
      port: FLASK_PORT,
      path: '/api/now-playing',
      method: 'GET'
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
        message: 'Failed to fetch from Flask API: ' + error.message
      });
    });

    proxyReq.end();
  });

  // Recently-played proxy endpoint
  app.get('/api/recently-played', (req, res) => {
    const options = {
      hostname: 'localhost',
      port: FLASK_PORT,
      path: '/api/recently-played',
      method: 'GET'
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
        message: 'Failed to fetch from Flask API: ' + error.message
      });
    });

    proxyReq.end();
  });

  // Update-track proxy endpoint
  app.post('/api/update-track', (req, res) => {
    const options = {
      hostname: 'localhost',
      port: FLASK_PORT,
      path: '/api/update-track',
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
        message: 'Failed to update track: ' + error.message
      });
    });

    proxyReq.write(JSON.stringify(req.body));
    proxyReq.end();
  });

  return app;
}

describe('Express Server Tests', () => {
  let app;

  beforeAll(async () => {
    await startMockFlask();
    app = createTestApp();
  });

  afterAll(async () => {
    await stopMockFlask();
  });

  describe('GET /api/now-playing', () => {
    it('should proxy request to Flask backend', async () => {
      const response = await request(app)
        .get('/api/now-playing')
        .expect('Content-Type', /json/);

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
    });

    it('should return track data from Flask', async () => {
      const response = await request(app)
        .get('/api/now-playing')
        .expect(200);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.artist).toBeDefined();
      expect(response.body.data.title).toBeDefined();
      expect(response.body.data.id).toBeDefined();
    });

    it('should include rating counts', async () => {
      const response = await request(app)
        .get('/api/now-playing')
        .expect(200);

      expect(response.body.data.thumbs_up).toBeDefined();
      expect(response.body.data.thumbs_down).toBeDefined();
    });

    it('should handle Flask connection errors', async () => {
      await stopMockFlask();

      const response = await request(app)
        .get('/api/now-playing');

      expect(response.status).toBe(500);
      expect(response.body.status).toBe('error');
      expect(response.body.message).toContain('Failed to fetch from Flask API');

      await startMockFlask();
    });
  });

  describe('GET /api/recently-played', () => {
    it('should proxy request to Flask backend', async () => {
      const response = await request(app)
        .get('/api/recently-played')
        .expect('Content-Type', /json/);

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
    });

    it('should return array of tracks', async () => {
      const response = await request(app)
        .get('/api/recently-played')
        .expect(200);

      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should return tracks with required fields', async () => {
      const response = await request(app)
        .get('/api/recently-played')
        .expect(200);

      if (response.body.data.length > 0) {
        const track = response.body.data[0];
        expect(track).toHaveProperty('artist');
        expect(track).toHaveProperty('title');
        expect(track).toHaveProperty('album');
      }
    });

    it('should handle empty recently played list', async () => {
      setMockFlaskResponse('/api/recently-played', {
        status: 'success',
        data: []
      });

      const response = await request(app)
        .get('/api/recently-played')
        .expect(200);

      expect(response.body.data).toEqual([]);
    });

    it('should handle Flask connection errors', async () => {
      await stopMockFlask();

      const response = await request(app)
        .get('/api/recently-played');

      expect(response.status).toBe(500);
      expect(response.body.status).toBe('error');

      await startMockFlask();
    });
  });

  describe('POST /api/update-track', () => {
    it('should proxy track update to Flask', async () => {
      const trackData = {
        artist: 'Test Artist',
        title: 'Test Track',
        album: 'Test Album',
        year: 2024
      };

      const response = await request(app)
        .post('/api/update-track')
        .send(trackData)
        .expect('Content-Type', /json/);

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
    });

    it('should forward request body to Flask', async () => {
      const trackData = {
        artist: 'New Artist',
        title: 'New Title',
        album: 'New Album',
        year: 2025
      };

      const response = await request(app)
        .post('/api/update-track')
        .send(trackData)
        .expect(200);

      expect(response.body.data.artist).toBe(trackData.artist);
    });

    it('should handle partial track data', async () => {
      const partialData = {
        artist: 'Partial Artist',
        title: 'Partial Title'
      };

      const response = await request(app)
        .post('/api/update-track')
        .send(partialData)
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should handle Flask connection errors', async () => {
      await stopMockFlask();

      const response = await request(app)
        .post('/api/update-track')
        .send({ artist: 'Test', title: 'Test' });

      expect(response.status).toBe(500);
      expect(response.body.status).toBe('error');

      await startMockFlask();
    });
  });

  describe('Content Type Handling', () => {
    it('should return JSON content type for all endpoints', async () => {
      const endpoints = [
        { method: 'get', path: '/api/now-playing' },
        { method: 'get', path: '/api/recently-played' },
        { method: 'post', path: '/api/update-track', body: { artist: 'Test', title: 'Test' } }
      ];

      for (const endpoint of endpoints) {
        const req = request(app)[endpoint.method](endpoint.path);
        if (endpoint.body) {
          req.send(endpoint.body);
        }
        const response = await req.expect('Content-Type', /json/);
        expect(response.body).toBeDefined();
      }
    });
  });

  describe('Proxy Request Methods', () => {
    it('should use GET method for now-playing', async () => {
      const response = await request(app)
        .get('/api/now-playing')
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should use GET method for recently-played', async () => {
      const response = await request(app)
        .get('/api/recently-played')
        .expect(200);

      expect(response.body.status).toBe('success');
    });

    it('should use POST method for update-track', async () => {
      const response = await request(app)
        .post('/api/update-track')
        .send({ artist: 'Test', title: 'Test' })
        .expect(200);

      expect(response.body.status).toBe('success');
    });
  });

  describe('Error Handling', () => {
    it('should return 500 on Flask connection failure', async () => {
      await stopMockFlask();

      const endpoints = [
        request(app).get('/api/now-playing'),
        request(app).get('/api/recently-played'),
        request(app).post('/api/update-track').send({ artist: 'Test' })
      ];

      for (const reqPromise of endpoints) {
        const response = await reqPromise;
        expect(response.status).toBe(500);
        expect(response.body.status).toBe('error');
      }

      await startMockFlask();
    });

    it('should include error message in response', async () => {
      await stopMockFlask();

      const response = await request(app)
        .get('/api/now-playing');

      expect(response.body.message).toBeDefined();
      expect(response.body.message).toBeTruthy();

      await startMockFlask();
    });
  });

  describe('Concurrent Requests', () => {
    it('should handle multiple simultaneous requests', async () => {
      const requests = Array(20).fill(null).map(() =>
        request(app).get('/api/now-playing')
      );

      const responses = await Promise.all(requests);

      responses.forEach(response => {
        expect(response.status).toBe(200);
        expect(response.body.status).toBe('success');
      });
    });
  });

  describe('Response Structure', () => {
    it('should maintain Flask response structure', async () => {
      setMockFlaskResponse('/api/now-playing', {
        status: 'success',
        data: {
          id: 999,
          artist: 'Structure Test Artist',
          title: 'Structure Test Track',
          custom_field: 'custom_value'
        }
      });

      const response = await request(app)
        .get('/api/now-playing')
        .expect(200);

      expect(response.body.status).toBe('success');
      expect(response.body.data.id).toBe(999);
      expect(response.body.data.custom_field).toBe('custom_value');
    });
  });
});
