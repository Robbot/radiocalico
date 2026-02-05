"""
Pytest configuration and fixtures for Flask backend testing
"""

import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask


@pytest.fixture
def db_path():
    """Create a temporary database path for testing"""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)
    yield path
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def db(db_path):
    """Create an in-memory database for testing"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.execute('''
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

    conn.execute('''
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

    conn.commit()

    yield conn

    conn.close()


@pytest.fixture
def app(db, db_path):
    """Create a Flask app for testing"""
    from flask import Flask, jsonify, g, request
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True

    def get_db():
        db_conn = getattr(g, '_database', None)
        if db_conn is None:
            db_conn = g._database = sqlite3.connect(db_path)
            db_conn.row_factory = sqlite3.Row
        return db_conn

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    @app.route('/api/test')
    def test_db():
        try:
            database = get_db()
            cursor = database.execute('SELECT 1 as test')
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

    @app.route('/api/now-playing')
    def now_playing():
        try:
            database = get_db()
            cursor = database.execute('''
                SELECT id, artist, title, album, year, album_art_url
                FROM tracks
                WHERE is_current = 1
                LIMIT 1
            ''')
            track = cursor.fetchone()

            if track:
                track_dict = dict(track)
                ratings_cursor = database.execute('''
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
            database = get_db()
            cursor = database.execute('''
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
            rating_type = data.get('rating_type')

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

            database = get_db()

            track = database.execute('SELECT id FROM tracks WHERE id = ?', (track_id,)).fetchone()
            if not track:
                return jsonify({
                    'status': 'error',
                    'message': 'Track not found'
                }), 404

            existing_rating = database.execute('''
                SELECT rating_type FROM ratings
                WHERE track_id = ? AND user_id = ?
            ''', (track_id, user_id)).fetchone()

            if existing_rating:
                return jsonify({
                    'status': 'error',
                    'message': 'You have already rated this track',
                    'existing_rating': existing_rating['rating_type']
                }), 409

            database.execute('''
                INSERT INTO ratings (track_id, user_id, rating_type)
                VALUES (?, ?, ?)
            ''', (track_id, user_id, rating_type))
            database.commit()

            ratings_cursor = database.execute('''
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

            database = get_db()

            existing_rating = database.execute('''
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

            database = get_db()

            database.execute('UPDATE tracks SET is_current = 0')

            existing = database.execute('''
                SELECT id FROM tracks
                WHERE artist = ? AND title = ?
                ORDER BY played_at DESC LIMIT 1
            ''', (artist, title)).fetchone()

            if existing:
                database.execute('''
                    UPDATE tracks
                    SET is_current = 1, played_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (existing['id'],))
            else:
                database.execute('''
                    INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
                    VALUES (?, ?, ?, ?, 1, ?)
                ''', (artist, title, album, year, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Live'))

            database.commit()

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

    yield app


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the app"""
    return app.test_cli_runner()


@pytest.fixture
def track(db):
    """Create a test track"""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO tracks (artist, title, album, year, is_current)
        VALUES (?, ?, ?, ?, ?)
    """, ('Test Artist', 'Test Song', 'Test Album', 2024, True))
    db.commit()
    track_id = cursor.lastrowid

    # Return track data
    track = db.execute('SELECT * FROM tracks WHERE id = ?', (track_id,)).fetchone()
    return track


@pytest.fixture
def tracks(db):
    """Create multiple test tracks"""
    track_data = [
        ('Artist 1', 'Track 1', 'Album 1', 2020, True),
        ('Artist 2', 'Track 2', 'Album 2', 2021, False),
        ('Artist 3', 'Track 3', 'Album 3', 2022, False),
    ]

    track_ids = []
    for artist, title, album, year, is_current in track_data:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO tracks (artist, title, album, year, is_current)
            VALUES (?, ?, ?, ?, ?)
        """, (artist, title, album, year, is_current))
        db.commit()
        track_ids.append(cursor.lastrowid)

    return track_ids


@pytest.fixture
def rating(db, track):
    """Create a test rating"""
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO ratings (track_id, user_id, rating_type)
        VALUES (?, ?, ?)
    """, (track['id'], 'user_test_123', 1))
    db.commit()

    rating = db.execute('SELECT * FROM ratings WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return rating


@pytest.fixture
def ratings(db, tracks):
    """Create multiple test ratings"""
    rating_data = [
        (tracks[0], 'user_1', 1),
        (tracks[0], 'user_2', 1),
        (tracks[0], 'user_3', -1),
        (tracks[1], 'user_4', 1),
    ]

    for track_id, user_id, rating_type in rating_data:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO ratings (track_id, user_id, rating_type)
            VALUES (?, ?, ?)
        """, (track_id, user_id, rating_type))
        db.commit()

    return rating_data


@pytest.fixture
def user_ids():
    """Provide test user IDs"""
    return [
        'user_test_1',
        'user_test_2',
        'user_1234567890_abc123',
        'user_with-dash',
        'user.with.dots'
    ]
