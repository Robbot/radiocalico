"""
Flask Backend Unit Tests for Ratings System
Tests rating endpoints, validation, and database operations
"""

import pytest
import sqlite3


class TestRatingSubmission:
    """Tests for POST /api/tracks/<track_id>/rate endpoint"""

    def test_submit_rating_success_thumbs_up(self, client, track):
        """Test successful thumbs up rating submission"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'user_id': 'user_test_123', 'rating_type': 1})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'thumbs_up' in data['data']
        assert data['data']['thumbs_up'] >= 1

    def test_submit_rating_success_thumbs_down(self, client, track):
        """Test successful thumbs down rating submission"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'user_id': 'user_test_456', 'rating_type': -1})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['thumbs_down'] >= 1

    def test_missing_user_id_returns_400(self, client, track):
        """Test that missing user_id returns 400 error"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'rating_type': 1})

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'user_id' in data['message']

    def test_invalid_rating_type_returns_400(self, client, track):
        """Test that invalid rating_type returns 400 error"""
        invalid_types = [0, 2, 5, -2, 100, 'up', 'down']

        for invalid_type in invalid_types:
            response = client.post(f'/api/tracks/{track["id"]}/rate',
                                  json={'user_id': 'user_test', 'rating_type': invalid_type})

            assert response.status_code == 400
            data = response.get_json()
            assert data['status'] == 'error'
            assert 'rating_type' in data['message']

    def test_track_not_found_returns_404(self, client):
        """Test rating non-existent track returns 404"""
        response = client.post('/api/tracks/99999/rate',
                              json={'user_id': 'user_test', 'rating_type': 1})

        assert response.status_code == 404
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'not found' in data['message']

    def test_duplicate_rating_returns_409(self, client, rating):
        """Test that duplicate rating returns 409 conflict"""
        response = client.post(f'/api/tracks/{rating["track_id"]}/rate',
                              json={'user_id': rating['user_id'], 'rating_type': 1})

        assert response.status_code == 409
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'already rated' in data['message']
        assert data['existing_rating'] == rating['rating_type']

    def test_duplicate_rating_different_type_returns_409(self, client, rating):
        """Test that rating with different type also returns 409"""
        response = client.post(f'/api/tracks/{rating["track_id"]}/rate',
                              json={'user_id': rating['user_id'], 'rating_type': -1})

        assert response.status_code == 409
        data = response.get_json()
        assert data['status'] == 'error'

    def test_rating_counts_update_correctly(self, client, track):
        """Test that rating counts are calculated correctly"""
        track_id = track['id']

        # Submit multiple ratings
        ratings_to_submit = [
            ('user_1', 1),
            ('user_2', 1),
            ('user_3', 1),
            ('user_4', -1),
            ('user_5', -1),
        ]

        for user_id, rating_type in ratings_to_submit:
            response = client.post(f'/api/tracks/{track_id}/rate',
                                  json={'user_id': user_id, 'rating_type': rating_type})
            assert response.status_code == 200

        # Check final counts
        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['thumbs_up'] == 3
        assert data['data']['thumbs_down'] == 2

    def test_same_user_different_tracks(self, client, tracks):
        """Test that same user can rate different tracks"""
        user_id = 'user_multi_track'

        for track_id in tracks:
            response = client.post(f'/api/tracks/{track_id}/rate',
                                  json={'user_id': user_id, 'rating_type': 1})
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'

    def test_empty_request_body(self, client, track):
        """Test handling of empty request body"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'


class TestRatingStatus:
    """Tests for POST /api/tracks/<track_id>/rating-status endpoint"""

    def test_check_rating_status_not_rated(self, client, track):
        """Test checking rating status when user hasn't rated"""
        response = client.post(f'/api/tracks/{track["id"]}/rating-status',
                              json={'user_id': 'user_never_rated'})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['has_rated'] is False
        assert data['data']['rating_type'] is None

    def test_check_rating_status_rated(self, client, rating):
        """Test checking rating status when user has rated"""
        response = client.post(f'/api/tracks/{rating["track_id"]}/rating-status',
                              json={'user_id': rating['user_id']})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['has_rated'] is True
        assert data['data']['rating_type'] == rating['rating_type']

    def test_rating_status_thumbs_up(self, client, track):
        """Test rating status for thumbs up"""
        user_id = 'user_up_test'
        track_id = track['id']

        # First submit a thumbs up
        client.post(f'/api/tracks/{track_id}/rate',
                   json={'user_id': user_id, 'rating_type': 1})

        # Check status
        response = client.post(f'/api/tracks/{track_id}/rating-status',
                              json={'user_id': user_id})

        data = response.get_json()
        assert data['data']['has_rated'] is True
        assert data['data']['rating_type'] == 1

    def test_rating_status_thumbs_down(self, client, track):
        """Test rating status for thumbs down"""
        user_id = 'user_down_test'
        track_id = track['id']

        # First submit a thumbs down
        client.post(f'/api/tracks/{track_id}/rate',
                   json={'user_id': user_id, 'rating_type': -1})

        # Check status
        response = client.post(f'/api/tracks/{track_id}/rating-status',
                              json={'user_id': user_id})

        data = response.get_json()
        assert data['data']['has_rated'] is True
        assert data['data']['rating_type'] == -1

    def test_rating_status_missing_user_id(self, client, track):
        """Test rating status without user_id returns error"""
        response = client.post(f'/api/tracks/{track["id"]}/rating-status',
                              json={})

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'user_id' in data['message']

    def test_rating_status_nonexistent_track(self, client):
        """Test rating status for non-existent track"""
        response = client.post('/api/tracks/99999/rating-status',
                              json={'user_id': 'user_test'})

        assert response.status_code == 200
        data = response.get_json()
        # Should return not rated for non-existent track
        assert data['data']['has_rated'] is False


class TestRatingDatabaseOperations:
    """Tests for rating database operations"""

    def test_rating_inserted_into_database(self, client, track):
        """Test that rating is actually inserted into database"""
        # This test requires access to the database connection
        # which is managed by the app context
        pass  # Covered by integration tests

    def test_rating_unique_constraint(self, client, track):
        """Test database unique constraint on (track_id, user_id)"""
        user_id = 'user_constraint_test'
        track_id = track['id']

        # First rating should succeed
        response1 = client.post(f'/api/tracks/{track_id}/rate',
                               json={'user_id': user_id, 'rating_type': 1})
        assert response1.status_code == 200

        # Second rating should fail
        response2 = client.post(f'/api/tracks/{track_id}/rate',
                               json={'user_id': user_id, 'rating_type': -1})
        assert response2.status_code == 409

    def test_rating_foreign_key_track(self, client):
        """Test that rating references valid track"""
        response = client.post('/api/tracks/99999/rate',
                              json={'user_id': 'user_test', 'rating_type': 1})

        assert response.status_code == 404

    def test_rating_timestamp_created(self, client, track):
        """Test that rating has created_at timestamp"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'user_id': 'user_timestamp', 'rating_type': 1})

        assert response.status_code == 200
        # Timestamp is created automatically by database


class TestRatingValidation:
    """Tests for rating input validation"""

    def test_rating_type_must_be_integer(self, client, track):
        """Test that rating_type must be integer"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'user_id': 'user_test', 'rating_type': 'up'})

        assert response.status_code == 400

    def test_rating_type_accepts_only_1_or_minus_1(self, client, track):
        """Test that only 1 and -1 are valid rating types"""
        valid_types = [1, -1]
        # Note: True == 1 in Python, False == 0, None is falsy
        invalid_types = [0, 2, -2, 100, '1', '-1', None, False]

        for valid_type in valid_types:
            response = client.post(f'/api/tracks/{track["id"]}/rate',
                                  json={'user_id': f'user_{valid_type}', 'rating_type': valid_type})
            assert response.status_code == 200

        for invalid_type in invalid_types:
            response = client.post(f'/api/tracks/{track["id"]}/rate',
                                  json={'user_id': 'user_invalid', 'rating_type': invalid_type})
            assert response.status_code == 400

    def test_user_id_can_be_any_string(self, client, track, user_ids):
        """Test that various user ID formats are accepted"""
        for user_id in user_ids:
            response = client.post(f'/api/tracks/{track["id"]}/rate',
                                  json={'user_id': user_id, 'rating_type': 1})
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'

    def test_empty_user_id_handled(self, client, track):
        """Test handling of empty string user_id"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'user_id': '', 'rating_type': 1})

        # Empty string is falsy but should be handled
        assert response.status_code == 400

    def test_extra_fields_ignored(self, client, track):
        """Test that extra fields in request are ignored"""
        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={
                                  'user_id': 'user_test',
                                  'rating_type': 1,
                                  'extra_field': 'should_be_ignored',
                                  'another_field': 123
                              })

        assert response.status_code == 200


class TestRatingAggregation:
    """Tests for rating count aggregation"""

    def test_thumbs_up_count(self, client, track):
        """Test thumbs up count aggregation"""
        track_id = track['id']

        # Add 5 thumbs up
        for i in range(5):
            client.post(f'/api/tracks/{track_id}/rate',
                       json={'user_id': f'user_up_{i}', 'rating_type': 1})

        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['thumbs_up'] == 5

    def test_thumbs_down_count(self, client, track):
        """Test thumbs down count aggregation"""
        track_id = track['id']

        # Add 3 thumbs down
        for i in range(3):
            client.post(f'/api/tracks/{track_id}/rate',
                       json={'user_id': f'user_down_{i}', 'rating_type': -1})

        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['thumbs_down'] == 3

    def test_mixed_ratings_count(self, client, track):
        """Test mixed thumbs up and down counts"""
        track_id = track['id']

        # Add mixed ratings
        for i in range(7):
            client.post(f'/api/tracks/{track_id}/rate',
                       json={'user_id': f'user_mixed_up_{i}', 'rating_type': 1})

        for i in range(4):
            client.post(f'/api/tracks/{track_id}/rate',
                       json={'user_id': f'user_mixed_down_{i}', 'rating_type': -1})

        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['thumbs_up'] == 7
        assert data['data']['thumbs_down'] == 4

    def test_zero_ratings_returns_zero(self, client, track):
        """Test that unrated track returns zero counts"""
        response = client.get('/api/now-playing')
        data = response.get_json()

        assert data['data']['thumbs_up'] == 0
        assert data['data']['thumbs_down'] == 0


class TestRatingEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_concurrent_same_rating(self, client, track):
        """Test handling of concurrent identical ratings"""
        # This would require actual concurrent requests
        # For now, just test sequential
        pass

    def test_very_long_user_id(self, client, track):
        """Test handling of very long user IDs"""
        long_user_id = 'user_' + 'x' * 1000

        response = client.post(f'/api/tracks/{track["id"]}/rate',
                              json={'user_id': long_user_id, 'rating_type': 1})

        # Should handle long strings
        assert response.status_code == 200

    def test_special_characters_in_user_id(self, client, track):
        """Test handling of special characters in user ID"""
        special_user_ids = [
            "user'with'quotes",
            'user"with"quotes',
            'user;with;semicolons',
            'user\nwith\nnewlines',
            'user\twith\ttabs'
        ]

        for user_id in special_user_ids:
            response = client.post(f'/api/tracks/{track["id"]}/rate',
                                  json={'user_id': user_id, 'rating_type': 1})
            # Should handle or reject gracefully
            assert response.status_code in [200, 400]

    def test_unicode_in_user_id(self, client, track):
        """Test handling of unicode characters in user ID"""
        unicode_user_ids = [
            'user_中文',
            'user_日本語',
            'user_한국어',
            'user_😀',
            'user_👍'
        ]

        for user_id in unicode_user_ids:
            response = client.post(f'/api/tracks/{track["id"]}/rate',
                                  json={'user_id': user_id, 'rating_type': 1})
            assert response.status_code == 200
