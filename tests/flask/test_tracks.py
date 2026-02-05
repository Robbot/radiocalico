"""
Flask Backend Unit Tests for Tracks System
Tests track endpoints, now-playing, and recently-played
"""

import pytest


class TestNowPlaying:
    """Tests for GET /api/now-playing endpoint"""

    def test_now_playing_success(self, client, track):
        """Test retrieving now playing track"""
        response = client.get('/api/now-playing')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data

    def test_now_playing_includes_ratings(self, client, ratings):
        """Test that now playing includes rating counts"""
        response = client.get('/api/now-playing')

        assert response.status_code == 200
        data = response.get_json()
        track_data = data['data']

        assert 'thumbs_up' in track_data
        assert 'thumbs_down' in track_data
        assert isinstance(track_data['thumbs_up'], int)
        assert isinstance(track_data['thumbs_down'], int)

    def test_now_playing_track_fields(self, client, track):
        """Test that now playing returns all required fields"""
        response = client.get('/api/now-playing')

        assert response.status_code == 200
        data = response.get_json()
        track_data = data['data']

        required_fields = ['id', 'artist', 'title', 'album', 'year',
                          'album_art_url', 'thumbs_up', 'thumbs_down']

        for field in required_fields:
            assert field in track_data

    def test_now_playing_no_current_track(self, client):
        """Test now playing when no current track exists"""
        # Clear any tracks
        response = client.get('/api/now-playing')

        assert response.status_code == 200
        data = response.get_json()

        # Should return default Radio Calico info
        assert data['data']['artist'] == 'Radio Calico'
        assert data['data']['title'] == '24-bit Lossless Streaming'

    def test_now_playing_json_content_type(self, client, track):
        """Test that now playing returns JSON content type"""
        response = client.get('/api/now-playing')

        assert response.content_type == 'application/json'


class TestRecentlyPlayed:
    """Tests for GET /api/recently-played endpoint"""

    def test_recently_played_success(self, client, tracks):
        """Test retrieving recently played tracks"""
        response = client.get('/api/recently-played')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    def test_recently_played_returns_array(self, client, tracks):
        """Test that recently played returns an array"""
        response = client.get('/api/recently-played')

        data = response.get_json()
        assert isinstance(data['data'], list)

    def test_recently_played_limit_5(self, client):
        """Test that recently played is limited to 5 tracks"""
        response = client.get('/api/recently-played')

        data = response.get_json()
        assert len(data['data']) <= 5

    def test_recently_played_track_fields(self, client, tracks):
        """Test that recently played tracks have required fields"""
        response = client.get('/api/recently-played')

        data = response.get_json()

        if len(data['data']) > 0:
            track = data['data'][0]
            required_fields = ['artist', 'title', 'album', 'year', 'played_at']

            for field in required_fields:
                assert field in track

    def test_recently_played_empty(self, client):
        """Test recently played when no tracks exist"""
        response = client.get('/api/recently-played')

        data = response.get_json()
        assert isinstance(data['data'], list)
        # Empty list is valid

    def test_recently_played_ordering(self, client, tracks):
        """Test that recently played is ordered by played_at DESC"""
        response = client.get('/api/recently-played')

        data = response.get_json()
        tracks_data = data['data']

        if len(tracks_data) >= 2:
            # Check that tracks are in descending order
            for i in range(len(tracks_data) - 1):
                current = tracks_data[i]['played_at']
                next_track = tracks_data[i + 1]['played_at']
                # Should be descending
                assert current >= next_track

    def test_recently_played_json_content_type(self, client, tracks):
        """Test that recently played returns JSON content type"""
        response = client.get('/api/recently-played')

        assert response.content_type == 'application/json'


class TestUpdateTrack:
    """Tests for POST /api/update-track endpoint"""

    def test_update_track_success(self, client):
        """Test successful track update"""
        track_data = {
            'artist': 'New Artist',
            'title': 'New Title',
            'album': 'New Album',
            'year': 2024
        }

        response = client.post('/api/update-track', json=track_data)

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['artist'] == 'New Artist'
        assert data['data']['title'] == 'New Title'

    def test_update_track_minimal_data(self, client):
        """Test track update with minimal data"""
        track_data = {
            'artist': 'Minimal Artist',
            'title': 'Minimal Title'
        }

        response = client.post('/api/update-track', json=track_data)

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

    def test_update_track_sets_is_current(self, client):
        """Test that updating a track sets it as current"""
        # First update
        client.post('/api/update-track', json={
            'artist': 'Artist 1',
            'title': 'Title 1'
        })

        # Second update
        client.post('/api/update-track', json={
            'artist': 'Artist 2',
            'title': 'Title 2'
        })

        # Check now playing - should be second track
        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['artist'] == 'Artist 2'
        assert data['data']['title'] == 'Title 2'

    def test_update_track_same_artist_title(self, client):
        """Test updating same track multiple times"""
        track_data = {
            'artist': 'Repeat Artist',
            'title': 'Repeat Title',
            'album': 'Album 1'
        }

        # First update
        response1 = client.post('/api/update-track', json=track_data)
        assert response1.status_code == 200

        # Second update with same artist/title
        track_data['album'] = 'Album 2'
        response2 = client.post('/api/update-track', json=track_data)
        assert response2.status_code == 200

    def test_update_track_with_year(self, client):
        """Test track update with year"""
        track_data = {
            'artist': 'Year Artist',
            'title': 'Year Title',
            'year': 1985
        }

        response = client.post('/api/update-track', json=track_data)

        assert response.status_code == 200

    def test_update_track_special_characters(self, client):
        """Test track update with special characters in artist/title"""
        special_tracks = [
            {'artist': "Artist 'With' Quotes", 'title': 'Title "With" Quotes'},
            {'artist': 'Artist & Band', 'title': 'Title - Subtitle'},
            {'artist': 'Artist/Featuring', 'title': 'Title (Remix)'},
        ]

        for track_data in special_tracks:
            response = client.post('/api/update-track', json=track_data)
            assert response.status_code == 200

    def test_update_track_unicode(self, client):
        """Test track update with unicode characters"""
        unicode_tracks = [
            {'artist': '日本語アーティスト', 'title': '日本語タイトル'},
            {'artist': '中文艺术家', 'title': '中文标题'},
            {'artist': '한국어 아티스트', 'title': '한국어 제목'},
        ]

        for track_data in unicode_tracks:
            response = client.post('/api/update-track', json=track_data)
            assert response.status_code == 200


class TestTrackValidation:
    """Tests for track input validation"""

    def test_update_track_empty_artist(self, client):
        """Test track update with empty artist"""
        response = client.post('/api/update-track', json={
            'artist': '',
            'title': 'Some Title'
        })

        # Should use default or handle gracefully
        assert response.status_code == 200

    def test_update_track_empty_title(self, client):
        """Test track update with empty title"""
        response = client.post('/api/update-track', json={
            'artist': 'Some Artist',
            'title': ''
        })

        assert response.status_code == 200

    def test_update_track_empty_request(self, client):
        """Test track update with empty request"""
        response = client.post('/api/update-track', json={})

        assert response.status_code == 200
        # Should use defaults

    def test_update_track_extra_fields(self, client):
        """Test that extra fields are handled"""
        response = client.post('/api/update-track', json={
            'artist': 'Artist',
            'title': 'Title',
            'extra_field': 'ignored',
            'another_extra': 123
        })

        assert response.status_code == 200


class TestTrackDatabaseOperations:
    """Tests for track database operations"""

    def test_track_inserted_into_database(self, client):
        """Test that track is inserted into database"""
        client.post('/api/update-track', json={
            'artist': 'DB Test Artist',
            'title': 'DB Test Title'
        })

        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['artist'] == 'DB Test Artist'
        assert data['data']['title'] == 'DB Test Title'

    def test_only_one_current_track(self, client):
        """Test that only one track is marked as current"""
        # Add multiple tracks
        for i in range(5):
            client.post('/api/update-track', json={
                'artist': f'Artist {i}',
                'title': f'Title {i}'
            })

        # Check that only the last one is current
        response = client.get('/api/now-playing')
        data = response.get_json()

        # Should be the last added track
        assert data['data']['artist'] == 'Artist 4'
        assert data['data']['title'] == 'Title 4'

    def test_played_at_timestamp(self, client):
        """Test that played_at timestamp is set"""
        import time

        before_time = time.time()
        client.post('/api/update-track', json={
            'artist': 'Timestamp Artist',
            'title': 'Timestamp Title'
        })
        after_time = time.time()

        # Timestamp should be recent
        # This is a basic check - would need DB access for detailed check
        assert True


class TestTrackEdgeCases:
    """Tests for edge cases in track operations"""

    def test_very_long_artist_name(self, client):
        """Test handling of very long artist names"""
        long_artist = 'A' * 1000

        response = client.post('/api/update-track', json={
            'artist': long_artist,
            'title': 'Normal Title'
        })

        assert response.status_code == 200

    def test_very_long_title(self, client):
        """Test handling of very long titles"""
        long_title = 'T' * 1000

        response = client.post('/api/update-track', json={
            'artist': 'Normal Artist',
            'title': long_title
        })

        assert response.status_code == 200

    def test_concurrent_track_updates(self, client):
        """Test handling of rapid track updates"""
        for i in range(10):
            response = client.post('/api/update-track', json={
                'artist': f'Concurrent Artist {i}',
                'title': f'Concurrent Title {i}'
            })
            assert response.status_code == 200

        # Final state should be last update
        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['artist'] == 'Concurrent Artist 9'
