# RadioCalico - Local Development Setup

## Overview

Local web development environment with dual backend setup: Express.js and Flask, both using SQLite databases.

## Stack

- **Frontend Server**: Node.js with Express.js (Port 3000)
- **Backend API**: Python Flask (Port 5000)
- **Databases**: SQLite (separate databases for each backend)
- **Environment**: Node.js v18.20.4, Python 3.11.2

## Project Structure

```
radiocalico/
├── server.js              # Express server (port 3000)
├── database.js            # Express SQLite configuration
├── flask_app.py           # Flask API server (port 5000)
├── start_flask.sh         # Flask startup script
├── .env                   # Environment variables
├── package.json           # Node.js dependencies
├── venv/                  # Python virtual environment
├── database.sqlite        # Express SQLite database
├── flask_database.sqlite  # Flask SQLite database
└── public/                # Static files (HTML, CSS, JS)
    └── index.html         # Homepage
```

## Getting Started

### Start Express Server (Frontend)

```bash
npm start
```

The Express server will run on http://localhost:3000

### Start Flask Server (Backend API)

```bash
./start_flask.sh
```

The Flask server will run on http://localhost:5000

### Development

Edit these files to customize your application:

**Express (Frontend):**
- `server.js` - Add routes and serve frontend
- `database.js` - Modify Express database schema
- `public/` - Add HTML, CSS, and JavaScript files

**Flask (Backend API):**
- `flask_app.py` - Add API endpoints and business logic
- Flask database is auto-configured with SQLite

### Environment Variables

Edit `.env` to configure:

```
PORT=3000
DATABASE_PATH=./database.sqlite

FLASK_PORT=5000
FLASK_DATABASE_PATH=./flask_database.sqlite
```

## API Endpoints

### Express (http://localhost:3000)
- `GET /` - Homepage
- `GET /api/test` - Test database connection

### Flask (http://localhost:5000)
- `GET /` - API information
- `GET /api/test` - Test database connection
- `GET /api/users` - Get all users
- `GET /api/posts` - Get all posts

## Databases

### Express Database (database.sqlite)

Sample `users` table:

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

Add more tables by editing `database.js`.

### Flask Database (flask_database.sqlite)

Includes `users` and `posts` tables:

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  user_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (id)
)
```

Add more tables by editing `flask_app.py` in the `init_db()` function.

## Stopping the Servers

### Stop Express:
```bash
pkill -f "node server.js"
```

### Stop Flask:
```bash
pkill -f "flask_app.py"
```

### Stop both:
```bash
pkill -f "node server.js" && pkill -f "flask_app.py"
```
### Testing
