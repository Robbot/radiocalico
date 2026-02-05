# Flask Backend Testing Framework

## Overview
This directory contains the Flask backend unit tests for RadioCalico, built with pytest.

## Test Files
- `conftest.py` - Pytest configuration and fixtures
- `test_ratings.py` - Rating endpoint tests
- `test_tracks.py` - Track endpoint tests
- `test_database.py` - Database operation tests

## Running Tests

### Run all Flask tests
```bash
npm run test:flask
```

### Run with pytest directly
```bash
pytest tests/flask/
```

### Run with verbose output
```bash
npm run test:flask:verbose
# or
pytest tests/flask/ -v
```

### Run with coverage
```bash
npm run test:flask:coverage
# or
pytest tests/flask/ --cov=../flask_app.py --cov-report=html
```

### Run a specific test file
```bash
pytest tests/flask/test_ratings.py
```

### Run a specific test class
```bash
pytest tests/flask/test_ratings.py::TestRatingSubmission
```

### Run a specific test
```bash
pytest tests/flask/test_ratings.py::TestRatingSubmission::test_submit_rating_success_thumbs_up
```

## Test Structure

### Rating Tests (`test_ratings.py`)
- `TestRatingSubmission` - Rating submission endpoints
- `TestRatingStatus` - Rating status checking
- `TestRatingDatabaseOperations` - Database constraints and operations
- `TestRatingValidation` - Input validation
- `TestRatingAggregation` - Rating count calculations
- `TestRatingEdgeCases` - Boundary conditions

### Track Tests (`test_tracks.py`)
- `TestNowPlaying` - Now playing endpoint
- `TestRecentlyPlayed` - Recently played endpoint
- `TestUpdateTrack` - Track update endpoint
- `TestTrackValidation` - Input validation
- `TestTrackDatabaseOperations` - Database operations
- `TestTrackEdgeCases` - Edge cases

### Database Tests (`test_database.py`)
- `TestDatabaseInitialization` - Schema creation
- `TestDatabaseConnections` - Connection management
- `TestDatabaseCRUD` - Basic CRUD operations
- `TestRatingDataIntegrity` - Data integrity constraints
- `TestTrackDataIntegrity` - Track data constraints
- `TestDatabaseEdgeCases` - Edge cases
- `TestDatabasePerformance` - Performance considerations

## Fixtures

### Database Fixtures
- `db` - In-memory SQLite database
- `db_path` - Temporary database file path

### Data Fixtures
- `track` - Single test track
- `tracks` - Multiple test tracks
- `rating` - Single test rating
- `ratings` - Multiple test ratings
- `user_ids` - Test user ID strings

### App Fixtures
- `app` - Flask application with test configuration
- `client` - Test client for making requests
- `runner` - CLI test runner

## Test Configuration

### Pytest Configuration (conftest.py)
- In-memory database for each test
- Flask app with testing mode
- Row factory for dict-like access
- Automatic cleanup after tests

### Database Schema
Tests create the following tables:
- `users` - User accounts
- `posts` - Blog posts
- `tracks` - Music tracks
- `ratings` - Track ratings

## Coverage
Tests cover:
- All API endpoints
- Input validation
- Error handling
- Database operations
- Data integrity constraints
- Edge cases and boundary conditions
- Performance considerations

## Writing New Tests

### Test Class Template
```python
class TestFeatureName:
    """Description of what is being tested"""

    def test_specific_behavior(self, client, track):
        """Test description"""
        response = client.post('/api/endpoint', json={...})
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
```

### Using Fixtures
```python
def test_with_track(self, client, track):
    """Use the track fixture"""
    track_id = track['id']
    response = client.get(f'/api/tracks/{track_id}')
    assert response.status_code == 200
```
