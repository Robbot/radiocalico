#!/usr/bin/env python3
"""
Radio Calico Metadata Poller (PostgreSQL version)
Fetches real track information from the stream's metadata API
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import requests
from datetime import datetime

METADATA_URL = 'https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json'
COVER_ART_URL = 'https://d3d4yli4hf5bmh.cloudfront.net/cover.jpg'
POLL_INTERVAL = 15  # Check every 15 seconds

# PostgreSQL connection configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'radiocalico'),
    'user': os.getenv('POSTGRES_USER', 'radiocalico'),
    'password': os.getenv('POSTGRES_PASSWORD', 'radiocalico')
}

def get_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.cursor_factory = RealDictCursor
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed: {e}")

def update_tracks(metadata):
    """Update database with current and previous tracks"""
    db = get_db()
    cursor = db.cursor()

    # Current track
    artist = metadata.get('artist', 'Unknown Artist')
    title = metadata.get('title', 'Unknown Track')
    album = metadata.get('album', '')
    year = metadata.get('date', '')

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}]")
    print(f"🎵 Now Playing: {artist} - {title}")
    if album:
        print(f"   Album: {album} ({year})")

    # Mark all tracks as not current
    cursor.execute('UPDATE tracks SET is_current = FALSE')

    # Check if current track exists
    cursor.execute('''
        SELECT id FROM tracks
        WHERE artist = %s AND title = %s
    ''', (artist, title))
    existing = cursor.fetchone()

    # Use live cover art URL with cache-busting timestamp
    cover_url = f"{COVER_ART_URL}?t={int(time.time())}"

    if existing:
        cursor.execute('''
            UPDATE tracks
            SET is_current = TRUE, played_at = CURRENT_TIMESTAMP,
                album = %s, year = %s, album_art_url = %s
            WHERE id = %s
        ''', (album, year, cover_url, existing['id']))
    else:
        cursor.execute('''
            INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
            VALUES (%s, %s, %s, %s, TRUE, %s)
        ''', (artist, title, album, year, cover_url))

    # Update previous tracks
    for i in range(1, 6):
        prev_artist = metadata.get(f'prev_artist_{i}')
        prev_title = metadata.get(f'prev_title_{i}')

        if prev_artist and prev_title:
            # Check if previous track exists
            cursor.execute('''
                SELECT id FROM tracks
                WHERE artist = %s AND title = %s
            ''', (prev_artist, prev_title))
            prev_exists = cursor.fetchone()

            if not prev_exists:
                # Add to database as a previously played track (no album art for old tracks)
                cursor.execute('''
                    INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
                    VALUES (%s, %s, %s, %s, FALSE, %s)
                ''', (prev_artist, prev_title, '', None, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Previous'))

    db.commit()
    cursor.close()
    db.close()

    print(f"✓ Database updated")

def poll_metadata():
    """Fetch and process metadata"""
    try:
        response = requests.get(METADATA_URL, timeout=5)
        response.raise_for_status()
        metadata = response.json()

        update_tracks(metadata)
        return True

    except requests.RequestException as e:
        print(f"❌ Error fetching metadata: {e}")
        return False
    except Exception as e:
        print(f"❌ Error processing metadata: {e}")
        return False

def main():
    """Main polling loop"""
    print("=" * 70)
    print("Radio Calico - Live Metadata Poller (PostgreSQL)")
    print("=" * 70)
    print(f"Metadata URL: {METADATA_URL}")
    print(f"Poll interval: {POLL_INTERVAL} seconds")
    print(f"Database: PostgreSQL at {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    # Initial fetch
    poll_metadata()

    consecutive_errors = 0
    max_errors = 5

    try:
        while True:
            time.sleep(POLL_INTERVAL)

            if poll_metadata():
                consecutive_errors = 0
            else:
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    print(f"\n⚠️  Too many errors ({max_errors}), stopping poller")
                    break

    except KeyboardInterrupt:
        print("\n\n👋 Metadata poller stopped")

if __name__ == '__main__':
    main()
