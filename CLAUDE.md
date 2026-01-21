# Claude Code Development Notes

This document tracks the AI-assisted development of RadioCalico, including setup decisions, architecture choices, and collaboration notes.

## Project Overview

**RadioCalico** is a high-fidelity radio streaming platform providing 24-bit/48kHz lossless audio streaming. The service is ad-free, data-free, and subscription-free, focusing on music from the 70s, 80s, and 90s.

## Project Genesis

**Date**: 2026-01-03
**AI Assistant**: Claude Sonnet 4.5
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
├── start_flask.sh             # Flask startup script
├── install-services.sh        # Systemd service installation
├── .env                       # Environment configuration
├── package.json               # Node.js dependencies
├── venv/                      # Python virtual environment
├── database.sqlite            # Express database
├── flask_database.sqlite      # Flask database (tracks, ratings)
├── radiocalico-express.service   # Systemd service config (Express)
├── radiocalico-flask.service     # Systemd service config (Flask)
├── stream_URL.txt             # HLS stream URL
├── RadioCalico_Style_Guide.txt  # Brand guidelines
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
PORT=3000                          # Express port
DATABASE_PATH=./database.sqlite    # Express database

FLASK_PORT=5000                    # Flask port
FLASK_DATABASE_PATH=./flask_database.sqlite  # Flask database
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

### Production Deployment
- Install systemd services: `sudo ./install-services.sh`
- Services auto-start on boot
- Express service: `radiocalico-express.service`
- Flask service: `radiocalico-flask.service`

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
- [ ] Create Docker setup for easier deployment
- [ ] Add test suites for both backends
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
- All dependencies are locally installed (Node modules, Python venv)
- No sudo required for development (required for service installation)

## Collaboration Tips

When working with Claude Code on this project:

### Development Commands
1. Use `npm start` to run Express frontend
2. Use `./start_flask.sh` to run Flask backend
3. Use `python metadata_poller.py` to fetch live metadata
4. Check both databases are initialized before testing

### File Locations
- Frontend changes: `public/` directory
- Express server: `server.js`
- Flask API: `flask_app.py`
- Metadata polling: `metadata_poller.py`
- Database schemas: `database.js` (Express), `flask_app.py` init_db() (Flask)

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
