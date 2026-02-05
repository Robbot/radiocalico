import os
import sqlite3
from flask import Flask, jsonify, g, request
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['DATABASE'] = os.getenv('FLASK_DATABASE_PATH', './flask_database.sqlite')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist TEXT NOT NULL,
                title TEXT NOT NULL,
                album TEXT,
                year INTEGER,
                album_art_url TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_current BOOLEAN DEFAULT 0
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                rating_type INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks (id),
                UNIQUE (track_id, user_id)
            )
        ''')
        db.commit()

        # Seed with sample data
        seed_sample_tracks(db)

        print(f'Database initialized at: {app.config["DATABASE"]}')

def seed_sample_tracks(db):
    # Check if tracks already exist
    count = db.execute('SELECT COUNT(*) as count FROM tracks').fetchone()['count']
    if count > 0:
        return

    # Sample tracks data
    sample_tracks = [
        ('Shandi Sinnamon', 'He\'s A Dream', 'Flashdance (Original Motion Picture Soundtrack)', 1983, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Shandi'),
        ('TLC', 'Ain\'t 2 Proud 2 Beg', 'Ooooooohhh... On the TLC Tip', 1992, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=TLC'),
        ('The Raconteurs', 'Steady, As She Goes', 'Broken Boy Soldiers', 2006, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Raconteurs'),
        ('Mick Jagger', 'Just Another Night', 'She\'s the Boss', 1985, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Jagger'),
        ('Beyoncé', 'Irreplaceable', 'B\'Day', 2006, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Beyonce'),
        ('Etta James', 'I\'d Rather Go Blind', 'Tell Mama', 1967, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Etta'),
    ]

    # Insert tracks with the first one as current
    for i, (artist, title, album, year, art_url) in enumerate(sample_tracks):
        is_current = 1 if i == 0 else 0
        db.execute('''
            INSERT INTO tracks (artist, title, album, year, album_art_url, is_current)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (artist, title, album, year, art_url, is_current))

    db.commit()

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radio Calico - Flask API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }
            h1 { color: #1F4E23; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid #38A29D; }
            .endpoint a { color: #1F4E23; text-decoration: none; font-weight: bold; }
            .endpoint a:hover { color: #38A29D; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #1F4E23; color: white; }
            tr:hover { background-color: #f5f5f5; }
        </style>
    </head>
    <body>
        <h1>Radio Calico - Flask API Backend</h1>
        <p><strong>Status:</strong> Running</p>

        <h2>API Endpoints</h2>
        <div class="endpoint">
            <a href="/api/now-playing">/api/now-playing</a> - Get currently playing track
        </div>
        <div class="endpoint">
            <a href="/api/recently-played">/api/recently-played</a> - Get 5 most recently played tracks
        </div>
        <div class="endpoint">
            <a href="/api/test">/api/test</a> - Test database connection
        </div>
        <div class="endpoint">
            <a href="/api/users">/api/users</a> - Get all users
        </div>
        <div class="endpoint">
            <a href="/api/posts">/api/posts</a> - Get all posts
        </div>

        <h2>Database Views</h2>
        <div class="endpoint">
            <a href="/tracks">/tracks</a> - View all tracks in database
        </div>
        <div class="endpoint">
            <a href="/ratings">/ratings</a> - View all ratings in database
        </div>
    </body>
    </html>
    '''

@app.route('/api/test')
def test_db():
    try:
        db = get_db()
        cursor = db.execute('SELECT 1 as test')
        result = dict(cursor.fetchone())
        return jsonify({
            'status': 'success',
            'message': 'Database connection working',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/users')
def get_users():
    try:
        db = get_db()
        cursor = db.execute('SELECT * FROM users')
        users = [dict(row) for row in cursor.fetchall()]
        return jsonify({
            'status': 'success',
            'data': users
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/posts')
def get_posts():
    try:
        db = get_db()
        cursor = db.execute('SELECT * FROM posts')
        posts = [dict(row) for row in cursor.fetchall()]
        return jsonify({
            'status': 'success',
            'data': posts
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/now-playing')
def now_playing():
    try:
        db = get_db()
        cursor = db.execute('''
            SELECT id, artist, title, album, year, album_art_url
            FROM tracks
            WHERE is_current = 1
            LIMIT 1
        ''')
        track = cursor.fetchone()

        if track:
            track_dict = dict(track)
            # Get ratings for this track
            ratings_cursor = db.execute('''
                SELECT
                    SUM(CASE WHEN rating_type = 1 THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN rating_type = -1 THEN 1 ELSE 0 END) as thumbs_down
                FROM ratings
                WHERE track_id = ?
            ''', (track_dict['id'],))
            ratings = ratings_cursor.fetchone()
            track_dict['thumbs_up'] = ratings['thumbs_up'] or 0
            track_dict['thumbs_down'] = ratings['thumbs_down'] or 0

            return jsonify({
                'status': 'success',
                'data': track_dict
            })
        else:
            return jsonify({
                'status': 'success',
                'data': {
                    'id': None,
                    'artist': 'Radio Calico',
                    'title': '24-bit Lossless Streaming',
                    'album': 'Crystal-Clear Audio',
                    'year': None,
                    'album_art_url': 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Radio+Calico',
                    'thumbs_up': 0,
                    'thumbs_down': 0
                }
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/recently-played')
def recently_played():
    try:
        db = get_db()
        cursor = db.execute('''
            SELECT artist, title, album, year, played_at
            FROM tracks
            WHERE is_current = 0
            ORDER BY played_at DESC
            LIMIT 5
        ''')
        tracks = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            'status': 'success',
            'data': tracks
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tracks/<int:track_id>/rate', methods=['POST'])
def rate_track(track_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        rating_type = data.get('rating_type')  # 1 for thumbs up, -1 for thumbs down

        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'user_id is required'
            }), 400

        if rating_type not in [1, -1]:
            return jsonify({
                'status': 'error',
                'message': 'rating_type must be 1 (thumbs up) or -1 (thumbs down)'
            }), 400

        db = get_db()

        # Check if track exists
        track = db.execute('SELECT id FROM tracks WHERE id = ?', (track_id,)).fetchone()
        if not track:
            return jsonify({
                'status': 'error',
                'message': 'Track not found'
            }), 404

        # Check if user has already rated this track
        existing_rating = db.execute('''
            SELECT rating_type FROM ratings
            WHERE track_id = ? AND user_id = ?
        ''', (track_id, user_id)).fetchone()

        if existing_rating:
            return jsonify({
                'status': 'error',
                'message': 'You have already rated this track',
                'existing_rating': existing_rating['rating_type']
            }), 409

        # Insert the rating
        db.execute('''
            INSERT INTO ratings (track_id, user_id, rating_type)
            VALUES (?, ?, ?)
        ''', (track_id, user_id, rating_type))
        db.commit()

        # Get updated rating counts
        ratings_cursor = db.execute('''
            SELECT
                SUM(CASE WHEN rating_type = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN rating_type = -1 THEN 1 ELSE 0 END) as thumbs_down
            FROM ratings
            WHERE track_id = ?
        ''', (track_id,))
        ratings = ratings_cursor.fetchone()

        return jsonify({
            'status': 'success',
            'message': 'Rating submitted successfully',
            'data': {
                'thumbs_up': ratings['thumbs_up'] or 0,
                'thumbs_down': ratings['thumbs_down'] or 0
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/tracks/<int:track_id>/rating-status', methods=['POST'])
def get_rating_status(track_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'user_id is required'
            }), 400

        db = get_db()

        # Check if user has rated this track
        existing_rating = db.execute('''
            SELECT rating_type FROM ratings
            WHERE track_id = ? AND user_id = ?
        ''', (track_id, user_id)).fetchone()

        if existing_rating:
            return jsonify({
                'status': 'success',
                'data': {
                    'has_rated': True,
                    'rating_type': existing_rating['rating_type']
                }
            })
        else:
            return jsonify({
                'status': 'success',
                'data': {
                    'has_rated': False,
                    'rating_type': None
                }
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/update-track', methods=['POST'])
def update_track():
    try:
        data = request.get_json()
        artist = data.get('artist', 'Unknown Artist')
        title = data.get('title', 'Unknown Track')
        album = data.get('album', 'Live Stream')
        year = data.get('year')

        db = get_db()

        # Mark all tracks as not current
        db.execute('UPDATE tracks SET is_current = 0')

        # Check if this track already exists in recently played
        existing = db.execute('''
            SELECT id FROM tracks
            WHERE artist = ? AND title = ?
            ORDER BY played_at DESC LIMIT 1
        ''', (artist, title)).fetchone()

        if existing:
            # Update existing track to current
            db.execute('''
                UPDATE tracks
                SET is_current = 1, played_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (existing['id'],))
        else:
            # Insert new track as current
            db.execute('''
                INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (artist, title, album, year, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Live'))

        db.commit()

        return jsonify({
            'status': 'success',
            'message': 'Track updated',
            'data': {
                'artist': artist,
                'title': title
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/tracks')
def view_tracks():
    try:
        db = get_db()
        cursor = db.execute('''
            SELECT id, artist, title, album, year, is_current, played_at
            FROM tracks
            ORDER BY is_current DESC, played_at DESC
        ''')
        tracks = cursor.fetchall()

        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Radio Calico - Tracks Database</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1400px; margin: 30px auto; padding: 20px; }
                h1 { color: #1F4E23; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #1F4E23; color: white; position: sticky; top: 0; }
                tr:hover { background-color: #D8F2D5; }
                .current { background-color: #38A29D; color: white; font-weight: bold; }
                .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
                .badge-current { background: #EFA63C; color: white; }
                a { color: #1F4E23; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Radio Calico - Tracks Database</h1>
            <p><a href="/">&larr; Back to API Home</a></p>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Artist</th>
                        <th>Title</th>
                        <th>Album</th>
                        <th>Year</th>
                        <th>Status</th>
                        <th>Played At</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for track in tracks:
            status = '<span class="badge badge-current">NOW PLAYING</span>' if track['is_current'] else 'Recently Played'
            html += f'''
                <tr>
                    <td>{track['id']}</td>
                    <td><strong>{track['artist']}</strong></td>
                    <td>{track['title']}</td>
                    <td>{track['album']}</td>
                    <td>{track['year'] or 'N/A'}</td>
                    <td>{status}</td>
                    <td>{track['played_at']}</td>
                </tr>
            '''

        html += '''
                </tbody>
            </table>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        return f'<h1>Error</h1><p>{str(e)}</p>', 500

@app.route('/ratings')
def view_ratings():
    try:
        db = get_db()
        cursor = db.execute('''
            SELECT
                r.id,
                r.track_id,
                t.artist,
                t.title,
                r.user_id,
                r.rating_type,
                r.created_at
            FROM ratings r
            JOIN tracks t ON r.track_id = t.id
            ORDER BY r.created_at DESC
        ''')
        ratings = cursor.fetchall()

        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Radio Calico - Ratings Database</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1400px; margin: 30px auto; padding: 20px; }
                h1 { color: #1F4E23; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #1F4E23; color: white; position: sticky; top: 0; }
                tr:hover { background-color: #D8F2D5; }
                .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 14px; }
                .badge-up { background: #38A29D; color: white; }
                .badge-down { background: #EFA63C; color: white; }
                a { color: #1F4E23; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .stats { background: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 4px solid #38A29D; }
            </style>
        </head>
        <body>
            <h1>Radio Calico - Ratings Database</h1>
            <p><a href="/">&larr; Back to API Home</a> | <a href="/tracks">View Tracks</a></p>
        '''

        # Calculate statistics
        thumbs_up_count = sum(1 for r in ratings if r['rating_type'] == 1)
        thumbs_down_count = sum(1 for r in ratings if r['rating_type'] == -1)
        total_ratings = len(ratings)

        html += f'''
            <div class="stats">
                <h3 style="margin-top: 0;">Rating Statistics</h3>
                <p><strong>Total Ratings:</strong> {total_ratings}</p>
                <p><strong>Thumbs Up:</strong> {thumbs_up_count} ({(thumbs_up_count/total_ratings*100) if total_ratings > 0 else 0:.1f}%)</p>
                <p><strong>Thumbs Down:</strong> {thumbs_down_count} ({(thumbs_down_count/total_ratings*100) if total_ratings > 0 else 0:.1f}%)</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Track ID</th>
                        <th>Artist</th>
                        <th>Title</th>
                        <th>User ID</th>
                        <th>Rating</th>
                        <th>Created At</th>
                    </tr>
                </thead>
                <tbody>
        '''

        if ratings:
            for rating in ratings:
                rating_badge = '<span class="badge badge-up">👍 Thumbs Up</span>' if rating['rating_type'] == 1 else '<span class="badge badge-down">👎 Thumbs Down</span>'
                html += f'''
                    <tr>
                        <td>{rating['id']}</td>
                        <td>{rating['track_id']}</td>
                        <td><strong>{rating['artist']}</strong></td>
                        <td>{rating['title']}</td>
                        <td>{rating['user_id']}</td>
                        <td>{rating_badge}</td>
                        <td>{rating['created_at']}</td>
                    </tr>
                '''
        else:
            html += '''
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: #999;">
                        No ratings yet. Start listening and rate some tracks!
                    </td>
                </tr>
            '''

        html += '''
                </tbody>
            </table>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        return f'<h1>Error</h1><p>{str(e)}</p>', 500

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('FLASK_PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
