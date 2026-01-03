#!/usr/bin/env python3
"""
Radio Calico Track Rotator
Automatically rotates through tracks to simulate live radio
"""

import sqlite3
import time
import random
from datetime import datetime

# Sample track pool
TRACK_POOL = [
    ("Shandi Sinnamon", "He's A Dream", "Flashdance Soundtrack", 1983),
    ("TLC", "Ain't 2 Proud 2 Beg", "Ooooooohhh... On the TLC Tip", 1992),
    ("The Raconteurs", "Steady, As She Goes", "Broken Boy Soldiers", 2006),
    ("Mick Jagger", "Just Another Night", "She's the Boss", 1985),
    ("Beyoncé", "Irreplaceable", "B'Day", 2006),
    ("Etta James", "I'd Rather Go Blind", "Tell Mama", 1967),
    ("The Beatles", "Come Together", "Abbey Road", 1969),
    ("Fleetwood Mac", "Dreams", "Rumours", 1977),
    ("Prince", "When Doves Cry", "Purple Rain", 1984),
    ("Whitney Houston", "I Wanna Dance with Somebody", "Whitney", 1987),
    ("Queen", "Bohemian Rhapsody", "A Night at the Opera", 1975),
    ("David Bowie", "Heroes", "Heroes", 1977),
    ("Madonna", "Like a Prayer", "Like a Prayer", 1989),
    ("Michael Jackson", "Billie Jean", "Thriller", 1982),
    ("Stevie Wonder", "Superstition", "Talking Book", 1972),
]

DATABASE = './flask_database.sqlite'
ROTATION_INTERVAL = 180  # 3 minutes between tracks

def get_db():
    """Connect to database"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def rotate_track():
    """Rotate to a new random track"""
    db = get_db()
    cursor = db.cursor()

    # Get current track
    current = cursor.execute('SELECT artist, title FROM tracks WHERE is_current = 1').fetchone()

    # Choose a random new track
    new_track = random.choice(TRACK_POOL)
    artist, title, album, year = new_track

    # Don't repeat the same track
    if current and current['artist'] == artist and current['title'] == title:
        # Try another one
        other_tracks = [t for t in TRACK_POOL if not (t[0] == artist and t[1] == title)]
        if other_tracks:
            new_track = random.choice(other_tracks)
            artist, title, album, year = new_track

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print(f"🎵 Now Playing: {artist} - {title}")

    # Mark all tracks as not current
    cursor.execute('UPDATE tracks SET is_current = 0')

    # Check if track exists
    existing = cursor.execute('''
        SELECT id FROM tracks
        WHERE artist = ? AND title = ?
    ''', (artist, title)).fetchone()

    if existing:
        # Update existing to current
        cursor.execute('''
            UPDATE tracks
            SET is_current = 1, played_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (existing['id'],))
    else:
        # Insert new track
        cursor.execute('''
            INSERT INTO tracks (artist, title, album, year, is_current, album_art_url)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (artist, title, album, year, 'https://via.placeholder.com/300x300/231F20/D8F2D5?text=Live'))

    db.commit()
    db.close()

    print(f"✓ Database updated")

def main():
    """Main loop"""
    print("=" * 60)
    print("Radio Calico - Automatic Track Rotator")
    print("=" * 60)
    print(f"Rotation interval: {ROTATION_INTERVAL} seconds ({ROTATION_INTERVAL/60:.1f} minutes)")
    print(f"Database: {DATABASE}")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Initial rotation
    rotate_track()

    try:
        while True:
            time.sleep(ROTATION_INTERVAL)
            rotate_track()
    except KeyboardInterrupt:
        print("\n\n👋 Track rotator stopped")

if __name__ == '__main__':
    main()
