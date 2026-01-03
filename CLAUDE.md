# Claude Code Development Notes

This document tracks the AI-assisted development of RadioCalico, including setup decisions, architecture choices, and collaboration notes.

## Project Genesis

**Date**: 2026-01-03
**AI Assistant**: Claude Sonnet 4.5
**Initial Request**: Install and configure a web server and database for local prototyping

## Technology Stack Decisions

### Initial Setup (Express + SQLite)
- **Web Server**: Express.js chosen as default development server
- **Database**: SQLite selected for lightweight local development
- **Reason**: No sudo access required, simple setup, perfect for prototyping

### Dual Backend Architecture (Express + Flask)
- **Frontend**: Express.js (Port 3000) - Static file serving and frontend routing
- **Backend API**: Flask (Port 5000) - RESTful API and business logic
- **Databases**: Separate SQLite databases for each backend
- **Reason**: User preference for Flask backend while keeping Express for frontend

## Setup Process

### Phase 1: Express + SQLite
1. Initialized Node.js project with npm
2. Installed Express, better-sqlite3, sqlite3, and dotenv
3. Created `server.js` with basic routing and database test endpoint
4. Created `database.js` with SQLite configuration and sample users table
5. Added static file serving from `public/` directory
6. Created sample homepage with server status

### Phase 2: Flask + SQLite
1. Created Python virtual environment (required for externally-managed Python environment)
2. Installed Flask and python-dotenv in venv
3. Created `flask_app.py` with REST API endpoints
4. Configured separate SQLite database for Flask
5. Added users and posts tables with foreign key relationship
6. Created `start_flask.sh` startup script

## Project Structure

```
radiocalico/
├── server.js              # Express frontend server (port 3000)
├── database.js            # Express SQLite config
├── flask_app.py           # Flask API backend (port 5000)
├── start_flask.sh         # Flask startup script
├── .env                   # Environment configuration
├── package.json           # Node.js dependencies
├── venv/                  # Python virtual environment
├── database.sqlite        # Express database
├── flask_database.sqlite  # Flask database
└── public/
    └── index.html         # Homepage
```

## Database Schemas

### Express Database
- **users**: id, username, email, created_at

### Flask Database
- **users**: id, username, email, created_at
- **posts**: id, title, content, user_id (FK), created_at

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

### Stopping Servers
- Express: `pkill -f "node server.js"`
- Flask: `pkill -f "flask_app.py"`
- Both: `pkill -f "node server.js" && pkill -f "flask_app.py"`

## API Endpoints

### Express (http://localhost:3000)
- `GET /` - Homepage with server status
- `GET /api/test` - Database connection test

### Flask (http://localhost:5000)
- `GET /` - API information and available endpoints
- `GET /api/test` - Database connection test
- `GET /api/users` - List all users
- `GET /api/posts` - List all posts

## Architecture Decisions

### Why Dual Backend?
- **Express**: Handles frontend assets, static files, and frontend routing
- **Flask**: Provides RESTful API with Python's rich ecosystem for backend logic
- **Separation of Concerns**: Frontend and backend can be developed independently

### Why Separate Databases?
- Independent data management for each server
- Clearer separation between frontend and backend data
- Easier to migrate or scale independently in the future

### Why better-sqlite3 for Express?
- Synchronous API, simpler for local development
- Better performance than async sqlite3
- Note: Requires Node.js 20+ officially, but works with Node.js 18.20.4

### Why Virtual Environment for Flask?
- Modern Debian/Ubuntu systems use externally-managed Python environments
- Prevents system Python package conflicts
- Standard best practice for Python development

## Known Issues & Considerations

1. **better-sqlite3 version warning**: Prefers Node.js 20+, currently using 18.20.4
   - Works fine for local development
   - Consider upgrading Node.js for production

2. **Flask debug mode**: Currently enabled for development
   - Must be disabled for production deployment
   - Add production WSGI server (gunicorn, waitress) for production

3. **No authentication**: Current setup has no auth
   - Add authentication before deploying
   - Consider JWT for API authentication

4. **CORS**: Not configured
   - May need CORS setup if frontend and backend are on different domains
   - Use flask-cors if needed

## Future Enhancements

- [ ] Add user authentication and authorization
- [ ] Configure CORS for cross-origin requests
- [ ] Add API documentation (Swagger/OpenAPI)
- [ ] Implement proper error handling and logging
- [ ] Add database migrations (Alembic for Flask)
- [ ] Create Docker setup for easier deployment
- [ ] Add test suites for both backends
- [ ] Implement CI/CD pipeline

## Notes for Future AI Assistants

- Both servers run simultaneously on different ports
- Databases are independent - no shared state
- Express is for frontend/static files, Flask is for API/backend logic
- All dependencies are locally installed (Node modules, Python venv)
- No sudo required for this setup

## Collaboration Tips

When working with Claude Code on this project:
1. Use `npm start` to run Express
2. Use `./start_flask.sh` to run Flask
3. Check both databases are initialized before testing
4. Frontend changes go in `public/` or `server.js`
5. Backend API changes go in `flask_app.py`
6. Database schema changes need manual migration (no ORM migrations set up yet)
