require('dotenv').config();
const express = require('express');
const path = require('path');
const fs = require('fs');
const http = require('http');
const db = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;
const FLASK_PORT = process.env.FLASK_PORT || 5000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

app.get('/api/stream-url', (req, res) => {
  try {
    const streamUrl = fs.readFileSync(path.join(__dirname, 'stream_URL.txt'), 'utf8').trim();
    res.json({
      status: 'success',
      streamUrl: streamUrl
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

app.get('/api/test', (req, res) => {
  try {
    const result = db.prepare('SELECT 1 as test').get();
    res.json({
      status: 'success',
      message: 'Database connection working',
      result
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

// Proxy endpoints to Flask API
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

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
  console.log(`Database: ${process.env.DATABASE_PATH}`);
});
