# Claude Code Development Notes

This document tracks the AI-assisted development of RadioCalico, including setup decisions, architecture choices, and collaboration notes.

## Project Overview

**RadioCalico** is a high-fidelity radio streaming platform providing 24-bit/48kHz lossless audio streaming. The service is ad-free, data-free, and subscription-free, focusing on music from the 70s, 80s, and 90s.

## Project Genesis

**Date**: 2026-01-03
**AI Assistants**: Claude Sonnet 4.5, Claude Opus 4.5, Claude GLM-4.7
**Initial Request**: Install and configure a web server and database for local prototyping

**Evolution**: The project evolved from a generic web development setup to a full-featured radio streaming platform with HLS (HTTP Live Streaming), real-time metadata fetching, user ratings, and production deployment capabilities.

## Technology Stack

### Frontend
- **Server**: Express.js (Port 3000)
- **Streaming**: hls.js for browser-based HLS playback
- **Database**: SQLite (better-sqlite3)
- **Styling**: Custom CSS with RadioCalico brand design system

### Backend API
- **Server**: Flask (Port 5000)
- **Database**: SQLite with custom ORM
- **CORS**: Enabled for cross-origin requests
- **Features**: Track management, user ratings, metadata polling

### Streaming Technology
- **Protocol**: HLS (HTTP Live Streaming)
- **Quality**: 24-bit/48kHz lossless audio
- **Metadata**: Real-time JSON API integration (cloudfront.net)

## Project Structure

```
radiocalico/
├── server.js                  # Express frontend server (port 3000)
├── database.js                # Express SQLite configuration
├── flask_app.py               # Flask API backend (port 5000)
├── metadata_poller.py         # Live metadata fetching service
├── track_rotator.py           # Simulates live radio track rotation
├── start_flask.sh             # Flask startup script
├── install-services.sh        # Systemd service installation
├── uninstall-services.sh      # Systemd service removal
├── .env                       # Environment configuration
├── package.json               # Node.js dependencies and scripts
├── requirements.txt           # Python dependencies (for Docker)
├── requirements-test.txt      # Python testing dependencies
├── vitest.config.js           # Vitest config for frontend tests
├── vitest.express.config.js   # Vitest config for Express API tests
├── venv/                      # Python virtual environment
├── database.sqlite            # Express database
├── flask_database.sqlite      # Flask database (tracks, ratings)
├── radiocalico-express.service   # Systemd service config (Express)
├── radiocalico-flask.service     # Systemd service config (Flask)
├── Dockerfile.express         # Docker image for Express frontend
├── Dockerfile.flask           # Docker image for Flask backend + poller
├── docker-compose.dev.yml     # Development Docker compose
├── docker-compose.prod.yml    # Production Docker compose
├── .dockerignore              # Docker build exclusions
├── stream_URL.txt             # HLS stream URL
├── RadioCalico_Style_Guide.txt  # Brand guidelines
├── CLAUDE.md                  # This development documentation
├── README.md                  # User-facing documentation
├── tests/                     # Test suites
│   ├── frontend/              # Frontend JavaScript tests (Vitest)
│   │   ├── fixtures/          # Test data fixtures
│   │   ├── player.test.js     # Player functionality tests
│   │   └── ratings.test.js    # Rating UI tests
│   ├── express/               # Express API tests (Vitest)
│   │   ├── server.test.js     # Server endpoint tests
│   │   └── ratings.test.js    # Rating API tests
│   └── flask/                 # Flask API tests (pytest)
│       ├── conftest.py        # Pytest fixtures
│       ├── test_tracks.py     # Track API tests
│       ├── test_ratings.py    # Rating API tests
│       └── test_database.py   # Database tests
└── public/
    ├── index.html             # Main radio player interface
    ├── admin.html             # Administrative interface
    ├── player.js              # HLS streaming player logic
    └── style.css              # RadioCalico brand styling
```

## Database Schemas

### Express Database (database.sqlite)
- **users**: id, username, email, created_at

### Flask Database (flask_database.sqlite)
- **users**: id, username, email, created_at
- **posts**: id, title, content, user_id (FK), created_at
- **tracks**: id, artist, title, album, year, album_art_url, played_at, is_current
- **ratings**: id, track_id, user_id, rating_type, created_at

## Environment Variables

```
# Express (Node.js)
PORT=3000                          # Express port
DATABASE_PATH=./database.sqlite    # Express database
FLASK_HOST=localhost               # Flask hostname (use 'flask' for Docker)
FLASK_PORT=5000                    # Flask port

# Flask (Python)
FLASK_PORT=5000                    # Flask port
FLASK_DATABASE_PATH=./flask_database.sqlite  # Flask database
FLASK_ENV=development              # development|production (controls debug mode)

# Docker
NODE_ENV=development               # development|production
```

## Testing Framework

RadioCalico uses a comprehensive testing setup covering all components:

### Frontend Tests (Vitest + jsdom)
- **Framework**: Vitest with jsdom environment
- **Config**: `vitest.config.js`
- **Location**: `tests/frontend/`
- **Coverage**: V8 provider with HTML, text, and JSON reports

```bash
# Run frontend tests
npm run test:frontend

# Watch mode for development
npm run test:frontend:watch

# Generate coverage report
npm run test:frontend:coverage
```

### Express API Tests (Vitest + supertest)
- **Framework**: Vitest with supertest for HTTP assertions
- **Config**: `vitest.express.config.js`
- **Location**: `tests/express/`

```bash
# Run Express API tests
npm run test:express
```

### Flask API Tests (pytest)
- **Framework**: pytest with Flask plugin
- **Dependencies**: `requirements-test.txt`
- **Location**: `tests/flask/`
- **Features**: Coverage reporting, async support, mocking

```bash
# Run Flask tests
npm run test:flask

# Verbose output
npm run test:flask:verbose

# Generate HTML coverage
npm run test:flask:coverage
```

### Run All Tests
```bash
# Run all tests (Node.js only)
npm test

# Run all tests including Python
npm run test:all
```

## Development Workflow

### Starting Servers
- Express: `npm start`
- Flask: `./start_flask.sh`
- Metadata Poller: `python metadata_poller.py`

### Stopping Servers
- Express: `pkill -f "node server.js"`
- Flask: `pkill -f "flask_app.py"`
- Both: `pkill -f "node server.js" && pkill -f "flask_app.py"`

### Track Rotation Simulator
For testing without live metadata API, use the track rotator:
- Start: `python track_rotator.py`
- Rotates through classic tracks every 3 minutes
- Updates Flask database with simulated "now playing"
- Press Ctrl+C to stop

### Production Deployment
- Install systemd services: `sudo ./install-services.sh`
- Uninstall systemd services: `sudo ./uninstall-services.sh`
- Services auto-start on boot
- Express service: `radiocalico-express.service`
- Flask service: `radiocalico-flask.service`

## PostgreSQL + Nginx Production Deployment

**Date**: 2026-02-06
**Migration**: SQLite → PostgreSQL, Express → Nginx

For production environments requiring better scalability and performance, RadioCalico now supports PostgreSQL with Nginx as the web server.

### Architecture Changes

#### PostgreSQL Backend
- **Database**: PostgreSQL 16 (replaces SQLite)
- **Connection Pooling**: psycopg2 with SimpleConnectionPool
- **Benefits**: Better concurrent access, ACID compliance, production-ready

#### Nginx Frontend
- **Web Server**: Nginx (replaces Express.js)
- **Port**: 80 (standard HTTP port)
- **Benefits**: Better performance, lower memory, production-proven

### New File Structure (PostgreSQL Deployment)

```
radiocalico/
├── flask_app_postgres.py       # Flask app with PostgreSQL support
├── metadata_poller_postgres.py # Metadata poller with PostgreSQL
├── nginx.conf                  # Nginx configuration
├── Dockerfile.nginx            # Nginx Docker image
├── Dockerfile.flask-pg         # Flask + PostgreSQL Docker image
├── docker-compose.pgprod.yml   # PostgreSQL + Nginx compose file
├── radiocalico-nginx.service   # Nginx systemd service
├── radiocalico-flask-pg.service # Flask + PostgreSQL systemd service
├── radiocalico-metadata-poller-pg.service # Poller + PostgreSQL service
├── install-services-pg.sh      # PostgreSQL deployment installer
├── uninstall-services-pg.sh    # PostgreSQL deployment uninstaller
└── .env.postgres.example       # Environment variable template
```

### PostgreSQL Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Tracks table
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    album TEXT,
    year INTEGER,
    album_art_url TEXT,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT FALSE
);

-- Ratings table
CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    track_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    rating_type INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_id) REFERENCES tracks (id),
    UNIQUE (track_id, user_id)
);
```

### Environment Variables (PostgreSQL)

```
# PostgreSQL Configuration
POSTGRES_HOST=postgres          # PostgreSQL hostname (localhost or docker service)
POSTGRES_PORT=5432              # PostgreSQL port
POSTGRES_DB=radiocalico         # Database name
POSTGRES_USER=radiocalico       # Database user
POSTGRES_PASSWORD=your_password # Database password

# Flask Configuration
FLASK_ENV=production            # production|development
FLASK_PORT=5000                 # Flask port
```

### Docker Deployment (PostgreSQL)

```bash
# Set PostgreSQL password (optional, default is radiocalico123)
export POSTGRES_PASSWORD=your_secure_password

# Build and start all services
docker-compose -f docker-compose.pgprod.yml up -d

# View logs
docker-compose -f docker-compose.pgprod.yml logs -f

# Stop services
docker-compose -f docker-compose.pgprod.yml down

# Backup PostgreSQL database
docker exec radiocalico-postgres pg_dump -U radiocalico radiocalico > backup.sql

# Restore PostgreSQL database
docker exec -i radiocalico-postgres psql -U radiocalico radiocalico < backup.sql
```

### Systemd Deployment (PostgreSQL)

Prerequisites:
- PostgreSQL 16 installed
- Nginx installed
- Python virtual environment configured

```bash
# Install services (interactive setup)
sudo ./install-services-pg.sh

# Check service status
sudo systemctl status radiocalico-nginx
sudo systemctl status radiocalico-flask-pg
sudo systemctl status radiocalico-metadata-poller-pg

# View logs
sudo journalctl -u radiocalico-nginx -f
sudo journalctl -u radiocalico-flask-pg -f

# Uninstall services
sudo ./uninstall-services-pg.sh
```

### API Endpoints (Nginx + Flask)

All requests go through Nginx (port 80), which proxies API calls to Flask:

#### Nginx (http://localhost)
- `GET /` - Main radio player interface
- `GET /admin` - Administrative interface
- `GET /health` - Health check endpoint
- All static files served from `/usr/share/nginx/html`

#### Flask (via Nginx proxy)
- `GET /api/stream-url` - Fetch HLS stream URL
- `GET /api/test` - Database connection test
- `GET /api/now-playing` - Current track with ratings
- `GET /api/recently-played` - Previous 5 tracks
- `POST /api/tracks/:id/rate` - User rating (thumbs up/down)
- `POST /api/tracks/:id/rating-status` - Check user's rating
- `POST /api/update-track` - Manual track metadata update
- `GET /tracks` - Database view (admin)
- `GET /ratings` - Rating statistics

### Key Differences from SQLite Deployment

| Aspect | SQLite + Express | PostgreSQL + Nginx |
|--------|-----------------|-------------------|
| Database | SQLite file | PostgreSQL server |
| Connection | Direct file access | Network connection with pooling |
| Frontend Server | Express.js (Node.js) | Nginx (C) |
| Port | 3000 | 80 |
| Static Files | Express static middleware | Nginx static file serving |
| API Proxy | Express http.request | Nginx proxy_pass |
| Scalability | Limited by file locks | True concurrent access |
| Memory Usage | Higher (Node.js runtime) | Lower (Nginx efficiency) |

### Why PostgreSQL + Nginx for Production?

1. **PostgreSQL Benefits**:
   - True concurrent read/write operations
   - Better data integrity with foreign keys and constraints
   - Indexed lookups on large datasets
   - Backup/restore with pg_dump
   - Connection pooling for high-traffic scenarios
   - Transaction isolation levels

2. **Nginx Benefits**:
   - Lower memory footprint
   - Higher performance for static files
   - Built-in load balancing capabilities
   - Better SSL/TLS termination support
   - Industry-standard for production deployments
   - Efficient reverse proxy

### Migration Notes

When migrating from SQLite to PostgreSQL:

1. **Data Migration**:
   ```bash
   # Export SQLite data
   sqlite3 flask_database.sqlite .dump > dump.sql

   # Convert to PostgreSQL format (manual edits needed):
   # - Replace AUTOINCREMENT with SERIAL
   # - Replace ? with %s placeholders
   # - Change BOOLEAN to TRUE/FALSE
   ```

2. **Application Changes**:
   - All database queries use parameter substitution (%s instead of ?)
   - Connection pool management for better resource utilization
   - Retry logic for initial database connection

3. **Configuration Changes**:
   - Nginx handles all static file serving
   - Flask only handles API requests
   - `/api/stream-url` endpoint moved from Express to Flask

## API Endpoints

### Express (http://localhost:3000)
- `GET /` - Main radio player interface
- `GET /admin` - Administrative interface
- `GET /api/stream-url` - Fetch HLS stream URL
- `GET /api/test` - Database connection test
- `GET /api/now-playing` - Current track (proxies to Flask)
- `GET /api/recently-played` - Previous 5 tracks (proxies to Flask)
- `POST /api/tracks/:id/rate` - Rate a track (proxies to Flask)
- `POST /api/update-track` - Manual track update (proxies to Flask)

### Flask (http://localhost:5000)
- `GET /` - API information and available endpoints
- `GET /api/test` - Database connection test
- `GET /api/now-playing` - Current track with ratings
- `GET /api/recently-played` - Previous 5 tracks
- `POST /api/tracks/:id/rate` - User rating (thumbs up/down)
- `POST /api/update-track` - Manual track metadata update
- `GET /tracks` - Database view (admin)
- `GET /ratings` - Rating statistics

## Architecture Decisions

### Why Dual Backend?
- **Express**: Handles frontend assets, static files, HLS streaming proxy
- **Flask**: Provides RESTful API with Python's rich ecosystem for backend logic
- **Separation of Concerns**: Frontend and backend can be developed independently

### Why HLS?
- Industry-standard for HTTP-based streaming
- Browser support via hls.js
- Supports high-quality audio (24-bit/48kHz)
- Works well with lossless audio streams

### Why Separate Databases?
- Independent data management for each server
- Clearer separation between frontend and backend data
- Easier to migrate or scale independently in the future

### Why Metadata Poller?
- External metadata API doesn't support webhooks
- Polling ensures track info is always current
- 15-second interval balances freshness and load
- Stores history in database for "recently played" feature

### Why Systemd Services?
- Production-ready deployment
- Auto-restart on failure
- Boot-time startup
- Centralized logging via journald

## Brand & Design System

RadioCalico uses a comprehensive brand identity:

### Color Palette
- **Mint**: `#9BDDDE` - Primary accent
- **Forest Green**: `#2D5F4A` - Secondary accent
- **Teal**: `#1C7C8C` - Tertiary accent
- **Calico Orange**: `#FF6B35` - Call-to-action
- **Charcoal**: `#2D2D2D` - Text
- **Cream**: `#F5F5DC` - Background
- **White**: `#FFFFFF` - Clean backgrounds
- **Black**: `#000000` - Deep contrast (website background)

### Typography
- **Headings**: Montserrat (bold, modern)
- **Body**: Open Sans (readable, clean)

### Design Principles
- Clean, minimalist aesthetic
- Dark theme with vibrant accent colors
- Cat with headphones logo branding
- Emphasis on album artwork display

## Known Issues & Considerations

1. **better-sqlite3 version warning**: Prefers Node.js 20+, currently using 18.20.4
   - Works fine for local development
   - Consider upgrading Node.js for production

2. **Flask debug mode**: Currently enabled for development
   - Must be disabled for production deployment
   - Consider using gunicorn or waitress for production WSGI server

3. **No authentication**: Current setup has no user authentication
   - Ratings system tracks by user_id but no login
   - Consider adding JWT authentication for user accounts

4. **Metadata polling**: Runs continuously when started manually
   - Should run as separate systemd service in production
   - Consider adding error handling and backoff logic

5. **CORS**: Enabled for all origins in development
   - Restrict to specific domains in production

6. **Album art cache-busting**: Uses timestamp to prevent caching
   - May cause unnecessary image reloads
   - Consider proper cache headers

## Future Enhancements

- [ ] Add user authentication and accounts
- [ ] Implement playlist creation and sharing
- [ ] Add sleep timer and alarm features
- [ ] Create mobile apps (iOS/Android)
- [ ] Add podcast-style on-demand content
- [ ] Implement proper error handling and logging
- [ ] Add database migrations (Alembic for Flask)
- [x] Create Docker setup for easier deployment
- [x] Add test suites for both backends
- [ ] Implement CI/CD pipeline
- [ ] Add analytics and usage tracking
- [ ] Create user dashboard with listening history
- [ ] Add social sharing features

## Notes for Future AI Assistants

- Both servers run simultaneously on different ports
- Databases are independent - no shared state
- Express serves frontend and proxies some API calls to Flask
- Flask is the primary API for tracks, ratings, and metadata
- Metadata poller updates Flask database with current track info
- HLS stream URL is stored in `stream_URL.txt`
- Brand guidelines are in `RadioCalico_Style_Guide.txt`
- systemd services are configured for production deployment
- Docker containers are configured for both development and production
- All dependencies are locally installed (Node modules, Python venv)
- No sudo required for development (required for service installation)
- Testing framework uses Vitest (JS) and pytest (Python)
- Track rotator provides simulated live radio for development/testing

## Collaboration Tips

When working with Claude Code on this project:

### Development Commands
1. Use `npm start` to run Express frontend
2. Use `./start_flask.sh` to run Flask backend
3. Use `python metadata_poller.py` to fetch live metadata
4. Use `python track_rotator.py` for simulated track rotation (testing)
5. Check both databases are initialized before testing
6. Run `npm test` to execute all JavaScript tests
7. Run `npm run test:flask` to execute Python tests

### File Locations
- Frontend changes: `public/` directory
- Frontend tests: `tests/frontend/`
- Express server: `server.js`
- Express tests: `tests/express/`
- Flask API: `flask_app.py`
- Flask tests: `tests/flask/`
- Metadata polling: `metadata_poller.py`
- Track rotation simulator: `track_rotator.py`
- Database schemas: `database.js` (Express), `flask_app.py` init_db() (Flask)
- Test configs: `vitest.config.js`, `vitest.express.config.js`, `tests/flask/conftest.py`

### Testing
- Frontend: http://localhost:3000
- API: http://localhost:5000
- Admin: http://localhost:3000/admin
- Stream URL: GET /api/stream-url
- Track info: GET /api/now-playing

### Production
- Use systemd services for 24/7 operation
- Logs available via `journalctl -u radiocalico-express` and `journalctl -u radiocalico-flask`
- Restart services: `sudo systemctl restart radiocalico-express radiocalico-flask`

### Docker Deployment

#### Development
```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

#### Production
```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down

# Backup databases
docker run --rm -v radiocalico_flask_db:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
```

#### Docker Services
- **express**: Frontend server (port 3000) with hot reload in dev mode
- **flask**: Backend API (port 5000) with health checks
- **metadata-poller**: Background service fetching track metadata
- **volumes**: `express_db` and `flask_db` for data persistence
- **network**: `radiocalico-net` for service communication

#### Environment Variables
- `FLASK_HOST`: Docker service name for Flask (default: `flask`)
- `FLASK_PORT`: Flask port (default: 5000)
- `NODE_ENV`: development or production
- `FLASK_ENV`: development or production (controls debug mode)
- `DATABASE_PATH`: Express database path (default: `/app/data/database.sqlite`)
- `FLASK_DATABASE_PATH`: Flask database path (default: `/app/data/flask_database.sqlite`)
