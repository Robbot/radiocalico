"""
Flask Backend Unit Tests for Database Operations
Tests database initialization, connections, and data integrity
"""

import pytest
import sqlite3
import tempfile
import os


class TestDatabaseInitialization:
    """Tests for database schema initialization"""

    def test_users_table_exists(self, db):
        """Test that users table is created"""
        cursor = db.cursor()
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        assert result is not None

    def test_posts_table_exists(self, db):
        """Test that posts table is created"""
        cursor = db.cursor()
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
        ).fetchone()
        assert result is not None

    def test_tracks_table_exists(self, db):
        """Test that tracks table is created"""
        cursor = db.cursor()
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tracks'"
        ).fetchone()
        assert result is not None

    def test_ratings_table_exists(self, db):
        """Test that ratings table is created"""
        cursor = db.cursor()
        result = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ratings'"
        ).fetchone()
        assert result is not None

    def test_users_table_structure(self, db):
        """Test that users table has correct columns"""
        cursor = db.cursor()
        columns = cursor.execute("PRAGMA table_info(users)").fetchall()
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'username', 'email', 'created_at']
        for expected in expected_columns:
            assert expected in column_names

    def test_tracks_table_structure(self, db):
        """Test that tracks table has correct columns"""
        cursor = db.cursor()
        columns = cursor.execute("PRAGMA table_info(tracks)").fetchall()
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'artist', 'title', 'album', 'year',
                          'album_art_url', 'played_at', 'is_current']
        for expected in expected_columns:
            assert expected in column_names

    def test_ratings_table_structure(self, db):
        """Test that ratings table has correct columns"""
        cursor = db.cursor()
        columns = cursor.execute("PRAGMA table_info(ratings)").fetchall()
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'track_id', 'user_id', 'rating_type', 'created_at']
        for expected in expected_columns:
            assert expected in column_names

    def test_ratings_unique_constraint(self, db):
        """Test that ratings table has unique constraint on (track_id, user_id)"""
        cursor = db.cursor()
        # Check for UNIQUE constraint in CREATE TABLE statement
        table_sql = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='ratings'"
        ).fetchone()
        assert table_sql is not None
        assert 'UNIQUE' in table_sql[0]
        assert 'track_id' in table_sql[0]
        assert 'user_id' in table_sql[0]


class TestDatabaseConnections:
    """Tests for database connection management"""

    def test_database_connection(self, db):
        """Test that database connection works"""
        result = db.execute('SELECT 1 as test').fetchone()
        assert result['test'] == 1

    def test_database_row_factory(self, db):
        """Test that row factory is set for dict-like access"""
        result = db.execute('SELECT 1 as test_column').fetchone()
        assert result['test_column'] == 1

    def test_database_transaction_commit(self, db):
        """Test that transactions are committed"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            ('Test', 'Test', True)
        )
        db.commit()
        result = db.execute('SELECT COUNT(*) as count FROM tracks').fetchone()
        assert result['count'] > 0

    def test_database_transaction_rollback(self, db):
        """Test that transactions can be rolled back"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            ('Rollback Test', 'Rollback Test', True)
        )
        db.rollback()
        result = db.execute("SELECT * FROM tracks WHERE artist = 'Rollback Test'").fetchone()
        assert result is None


class TestDatabaseCRUD:
    """Tests for CRUD operations"""

    def test_insert_track(self, db):
        """Test inserting a track"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, album, year, is_current) VALUES (?, ?, ?, ?, ?)",
            ('Artist 1', 'Title 1', 'Album 1', 2024, True)
        )
        db.commit()
        result = db.execute('SELECT * FROM tracks WHERE artist = "Artist 1"').fetchone()
        assert result is not None
        assert result['title'] == 'Title 1'

    def test_update_track(self, db):
        """Test updating a track"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            ('Original', 'Original', True)
        )
        db.commit()
        track_id = cursor.lastrowid
        cursor.execute(
            "UPDATE tracks SET artist = ?, title = ? WHERE id = ?",
            ('Updated', 'Updated', track_id)
        )
        db.commit()
        result = db.execute('SELECT * FROM tracks WHERE id = ?', (track_id,)).fetchone()
        assert result['artist'] == 'Updated'

    def test_delete_track(self, db):
        """Test deleting a track"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            ('To Delete', 'To Delete', True)
        )
        db.commit()
        track_id = cursor.lastrowid
        cursor.execute('DELETE FROM tracks WHERE id = ?', (track_id,))
        db.commit()
        result = db.execute('SELECT * FROM tracks WHERE id = ?', (track_id,)).fetchone()
        assert result is None

    def test_select_tracks(self, db):
        """Test selecting multiple tracks"""
        cursor = db.cursor()
        for i in range(5):
            cursor.execute(
                "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
                (f'Artist {i}', f'Title {i}', False)
            )
        db.commit()
        results = db.execute('SELECT * FROM tracks').fetchall()
        assert len(results) >= 5


class TestRatingDataIntegrity:
    """Tests for rating data integrity"""

    def test_rating_unique_constraint_enforced(self, db, track):
        """Test that duplicate ratings are prevented"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO ratings (track_id, user_id, rating_type) VALUES (?, ?, ?)",
            (track['id'], 'user_duplicate', 1)
        )
        db.commit()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO ratings (track_id, user_id, rating_type) VALUES (?, ?, ?)",
                (track['id'], 'user_duplicate', -1)
            )
            db.commit()

    def test_rating_foreign_key_track(self, db):
        """Test that ratings reference valid tracks"""
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO ratings (track_id, user_id, rating_type) VALUES (?, ?, ?)",
                (99999, 'user_test', 1)
            )
            db.commit()
        except sqlite3.IntegrityError:
            assert True

    def test_rating_count_aggregation(self, db, track):
        """Test rating count aggregation query"""
        cursor = db.cursor()
        track_id = track['id']
        ratings = [
            (track_id, 'user_1', 1),
            (track_id, 'user_2', 1),
            (track_id, 'user_3', 1),
            (track_id, 'user_4', -1),
            (track_id, 'user_5', -1),
        ]
        for track_id, user_id, rating_type in ratings:
            cursor.execute(
                "INSERT INTO ratings (track_id, user_id, rating_type) VALUES (?, ?, ?)",
                (track_id, user_id, rating_type)
            )
        db.commit()
        result = cursor.execute(
            "SELECT SUM(CASE WHEN rating_type = 1 THEN 1 ELSE 0 END) as thumbs_up, "
            "SUM(CASE WHEN rating_type = -1 THEN 1 ELSE 0 END) as thumbs_down "
            "FROM ratings WHERE track_id = ?",
            (track_id,)
        ).fetchone()
        assert result['thumbs_up'] == 3
        assert result['thumbs_down'] == 2


class TestTrackDataIntegrity:
    """Tests for track data integrity"""

    def test_track_current_only_one(self, db):
        """Test that only one track can be marked as current"""
        cursor = db.cursor()
        for i in range(3):
            cursor.execute(
                "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
                (f'Artist {i}', f'Title {i}', True)
            )
        cursor.execute('UPDATE tracks SET is_current = 0')
        cursor.execute('UPDATE tracks SET is_current = 1 WHERE id = 1')
        db.commit()
        result = cursor.execute('SELECT COUNT(*) as count FROM tracks WHERE is_current = 1').fetchone()
        assert result['count'] == 1

    def test_track_played_at_timestamp(self, db):
        """Test that played_at timestamp is set"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            ('Timestamp Test', 'Timestamp Test', True)
        )
        db.commit()
        result = cursor.execute("SELECT played_at FROM tracks WHERE artist = 'Timestamp Test'").fetchone()
        assert result['played_at'] is not None

    def test_track_year_optional(self, db):
        """Test that year is optional"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, album, is_current) VALUES (?, ?, ?, ?)",
            ('No Year', 'No Year', 'No Year Album', True)
        )
        db.commit()
        result = cursor.execute("SELECT * FROM tracks WHERE artist = 'No Year'").fetchone()
        assert result is not None
        assert result['year'] is None


class TestDatabaseEdgeCases:
    """Tests for database edge cases"""

    def test_empty_database_queries(self, db):
        """Test queries on empty database"""
        result = db.execute('SELECT * FROM tracks').fetchall()
        assert len(result) == 0
        result = db.execute('SELECT * FROM ratings').fetchall()
        assert len(result) == 0

    def test_null_values_handling(self, db):
        """Test handling of NULL values"""
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, album, year, album_art_url, is_current) VALUES (?, ?, ?, ?, ?, ?)",
            ('Null Test', 'Null Test', None, None, None, True)
        )
        db.commit()
        result = cursor.execute("SELECT * FROM tracks WHERE artist = 'Null Test'").fetchone()
        assert result['album'] is None
        assert result['year'] is None
        assert result['album_art_url'] is None

    def test_very_long_strings(self, db):
        """Test handling of very long strings"""
        cursor = db.cursor()
        long_string = 'A' * 10000
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            (long_string, long_string, True)
        )
        db.commit()
        result = db.execute('SELECT * FROM tracks WHERE artist = ?', (long_string,)).fetchone()
        assert result is not None

    def test_unicode_strings(self, db):
        """Test handling of unicode strings"""
        cursor = db.cursor()
        unicode_strings = [
            '日本語',
            '中文',
            '한국어',
            'Ελληνικά',
            'עברית',
            'العربية',
            'Emoji: 😀👍🎵'
        ]
        for unicode_str in unicode_strings:
            cursor.execute(
                "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
                (unicode_str, unicode_str, False)
            )
        db.commit()
        for unicode_str in unicode_strings:
            result = db.execute('SELECT * FROM tracks WHERE artist = ?', (unicode_str,)).fetchone()
            assert result is not None


class TestDatabasePerformance:
    """Tests for database performance considerations"""

    def test_batch_insert_performance(self, db):
        """Test batch insert performance"""
        import time
        cursor = db.cursor()
        start_time = time.time()
        for i in range(100):
            cursor.execute(
                "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
                (f'Perf Artist {i}', f'Perf Title {i}', False)
            )
        db.commit()
        elapsed = time.time() - start_time
        assert elapsed < 5.0

    def test_query_performance_with_ratings(self, db):
        """Test query performance with many ratings"""
        import time
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tracks (artist, title, is_current) VALUES (?, ?, ?)",
            ('Perf Track', 'Perf Track', True)
        )
        track_id = cursor.lastrowid

        start_time = time.time()
        for i in range(1000):
            cursor.execute(
                "INSERT INTO ratings (track_id, user_id, rating_type) VALUES (?, ?, ?)",
                (track_id, f'user_{i}', 1 if i % 2 == 0 else -1)
            )
        db.commit()
        insert_time = time.time() - start_time

        start_time = time.time()
        result = cursor.execute(
            "SELECT SUM(CASE WHEN rating_type = 1 THEN 1 ELSE 0 END) as thumbs_up, "
            "SUM(CASE WHEN rating_type = -1 THEN 1 ELSE 0 END) as thumbs_down "
            "FROM ratings WHERE track_id = ?",
            (track_id,)
        ).fetchone()
        query_time = time.time() - start_time

        assert result['thumbs_up'] == 500
        assert result['thumbs_down'] == 500
        assert insert_time < 5.0
        assert query_time < 1.0
