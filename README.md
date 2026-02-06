# RadioCalico

> High-fidelity radio streaming with style

**RadioCalico** is a 24-bit/48kHz lossless audio streaming platform. Ad-free, data-free, subscription-free radio focusing on music from the 70s, 80s, and 90s.

## Features

- **High-Fidelity Audio**: 24-bit/48kHz lossless streaming
- **Live Metadata**: Real-time track information (artist, title, album, year)
- **Album Art**: Dynamic album artwork display
- **Previous Tracks**: Shows 5 recently played tracks
- **User Ratings**: Thumbs up/down system for tracks
- **Responsive Design**: Beautiful dark theme with RadioCalico brand styling
- **Production Ready**: systemd services for 24/7 operation

## Tech Stack

### Development/Simple Deployment
- **Frontend**: Express.js (Port 3000)
- **Backend**: Flask (Port 5000)
- **Databases**: SQLite (better-sqlite3, sqlite3)

### Production Deployment (Recommended)
- **Frontend**: Nginx (Port 80)
- **Backend**: Flask (Port 5000)
- **Database**: PostgreSQL 16
- **Streaming**: hls.js for HLS playback

### Streaming
- **Protocol**: HLS (HTTP Live Streaming)
- **Quality**: 24-bit/48kHz lossless

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
├── radiocalico-express.service   # Systemd service config (Express)
├── radiocalico-flask.service     # Systemd service config (Flask)
└── public/
    ├── index.html             # Main radio player interface
    ├── admin.html             # Administrative interface
    ├── player.js              # HLS streaming player logic
    └── style.css              # RadioCalico brand styling
```

## Getting Started

### Prerequisites

- Node.js v18+
- Python 3.11+
- npm

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd radiocalico
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Create and activate Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

4. Install Python dependencies:
```bash
pip install flask flask-cors python-dotenv requests
```

5. Configure environment variables (edit `.env`):
```
PORT=3000
DATABASE_PATH=./database.sqlite
FLASK_PORT=5000
FLASK_DATABASE_PATH=./flask_database.sqlite
```

### Running the Application

#### Development Mode

Start the Express frontend server:
```bash
npm start
```

Start the Flask backend API (in a separate terminal):
```bash
./start_flask.sh
```

Start the metadata poller for live track updates (in a third terminal):
```bash
python metadata_poller.py
```

#### Production Mode

**Option 1: SQLite + Express (Simple)**

Install as systemd services:
```bash
sudo ./install-services.sh
```

This will:
- Install and enable `radiocalico-express.service`
- Install and enable `radiocalico-flask.service`
- Start both services
- Enable auto-start on boot

Manage services:
```bash
# Check status
sudo systemctl status radiocalico-express radiocalico-flask

# Restart services
sudo systemctl restart radiocalico-express radiocalico-flask

# View logs
sudo journalctl -u radiocalico-express -f
sudo journalctl -u radiocalico-flask -f
```

**Option 2: PostgreSQL + Nginx (Recommended for Production)**

For production environments requiring better scalability:
- **PostgreSQL** for true concurrent database access
- **Nginx** for efficient static file serving and reverse proxy

Prerequisites:
- PostgreSQL 16
- Nginx
- Python 3.11+

Install using Docker (recommended):
```bash
# Set PostgreSQL password
export POSTGRES_PASSWORD=your_secure_password

# Build and start all services
docker-compose -f docker-compose.pgprod.yml up -d

# View logs
docker-compose -f docker-compose.pgprod.yml logs -f
```

Or install as systemd services:
```bash
sudo ./install-services-pg.sh
```

This will:
- Setup PostgreSQL database and user
- Configure Nginx with custom config
- Install systemd services for Nginx, Flask, and metadata poller
- Start all services

Manage services:
```bash
# Check status
sudo systemctl status radiocalico-nginx radiocalico-flask-pg radiocalico-metadata-poller-pg

# Restart services
sudo systemctl restart radiocalico-nginx radiocalico-flask-pg

# View logs
sudo journalctl -u radiocalico-nginx -f
sudo journalctl -u radiocalico-flask-pg -f
```

### Stopping the Application

#### Development Mode

Stop Express:
```bash
pkill -f "node server.js"
```

Stop Flask:
```bash
pkill -f "flask_app.py"
```

Stop both:
```bash
pkill -f "node server.js" && pkill -f "flask_app.py"
```

#### Production Mode

```bash
sudo systemctl stop radiocalico-express radiocalico-flask
```

## API Endpoints

### Express (http://localhost:3000)

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main radio player interface |
| `GET /admin` | Administrative interface |
| `GET /api/stream-url` | Fetch HLS stream URL |
| `GET /api/now-playing` | Current track info |
| `GET /api/recently-played` | Previous 5 tracks |
| `POST /api/tracks/:id/rate` | Rate a track |

### Flask (http://localhost:5000)

| Endpoint | Description |
|----------|-------------|
| `GET /` | API information |
| `GET /api/now-playing` | Current track with ratings |
| `GET /api/recently-played` | Previous 5 tracks |
| `POST /api/tracks/:id/rate` | Submit user rating |
| `GET /tracks` | Database view (admin) |
| `GET /ratings` | Rating statistics |

## Database Schemas

### Flask Database

**tracks**
```sql
CREATE TABLE tracks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artist TEXT NOT NULL,
  title TEXT NOT NULL,
  album TEXT,
  year INTEGER,
  album_art_url TEXT,
  played_at TIMESTAMP,
  is_current BOOLEAN DEFAULT 0
)
```

**ratings**
```sql
CREATE TABLE ratings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  track_id INTEGER NOT NULL,
  user_id INTEGER,
  rating_type INTEGER NOT NULL,  -- 1 (thumbs up) or -1 (thumbs down)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (track_id) REFERENCES tracks (id)
)
```

## Brand & Design

RadioCalico uses a distinctive brand identity with a dark theme and vibrant accent colors.

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Mint | `#9BDDDE` | Primary accent |
| Forest Green | `#2D5F4A` | Secondary accent |
| Teal | `#1C7C8C` | Tertiary accent |
| Calico Orange | `#FF6B35` | Call-to-action |
| Charcoal | `#2D2D2D` | Text |
| Black | `#000000` | Background |
| White | `#FFFFFF` | Clean backgrounds |

### Typography

- **Headings**: Montserrat (bold, modern)
- **Body**: Open Sans (readable, clean)

## Development Notes

See [CLAUDE.md](CLAUDE.md) for detailed development notes, architecture decisions, and collaboration guidelines.

## License

[Your License Here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
