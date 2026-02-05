#!/usr/bin/env python3
"""
Radio Calico Metadata Poller
Fetches real track information from the stream's metadata API
"""

import os
import sqlite3
import time
import requests
from datetime import datetime

METADATA_URL = 'https://d3d4yli4hf5bmh.cloudfront.net/metadatav2.json'
COVER_ART_URL = 'https://d3d4yli4hf5bmh.cloudfront.net/cover.jpg'
DATABASE = os.getenv('FLASK_DATABASE_PATH', './flask_database.sqlite')
POLL_INTERVAL = 15  # Check every 15 seconds

def get_db():
    """Connect to database"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
    cursor.execute('UPDATE tracks SET is_current = 0')

    # Check if current track exists
    existing = cursor.execute('''
        SELECT id FROM tracks
        WHERE artist = ? AND title = ?
    ''', (artist, title)).fetchone()

    # Use live cover art URL with cache-busting timestamp
    cover_url = f"{COVER_ART_URL}?t={int(time.time())}"

    if existing:
        cursor.execute('''
            UPDATE tracks
            SET is_current = 1, played_at = CURRENT_TIMESTAMP,
                album = ?, year = ?, album_art_url = ?
            WHERE id = ?
        ''', (album, year, cover_url, existing['id']))
    else:
        cursor.execute('''
            INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (artist, title, album, year, cover_url))

    # Update previous tracks
    for i in range(1, 6):
        prev_artist = metadata.get(f'prev_artist_{i}')
        prev_title = metadata.get(f'prev_title_{i}')

        if prev_artist and prev_title:
            # Check if previous track exists
            prev_exists = cursor.execute('''
                SELECT id FROM tracks
                WHERE artist = ? AND title = ?
            ''', (prev_artist, prev_title)).fetchone()

            if not prev_exists:
                # Add to database as a previously played track (no album art for old tracks)
                cursor.execute('''
                    INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
                    VALUES (?, ?, ?, ?, 0, ?)
                ''', (prev_artist, prev_title, '', None, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Previous'))

    db.commit()
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
    print("Radio Calico - Live Metadata Poller")
    print("=" * 70)
    print(f"Metadata URL: {METADATA_URL}")
    print(f"Poll interval: {POLL_INTERVAL} seconds")
    print(f"Database: {DATABASE}")
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
