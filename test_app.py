"""
DevOps Flix - Test Suite
pytest tests for Flask application with API mocking and watchlist functionality
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, watchlist


@pytest.fixture
def client():
    """Create a test client for the Flask application"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_watchlist():
    """Reset watchlist before each test"""
    global watchlist
    from app import watchlist as wl
    wl.clear()
    yield
    wl.clear()


# ===== TEST 1: API Mock Test =====
def test_trending_route_with_mocked_api(client):
    """
    Test 1: Mock the TMDB API response to ensure the 'Trending' route 
    returns status 200 and renders correctly
    """
    # Mock data simulating TMDB API response
    mock_trending_data = {
        "results": [
            {
                "id": 12345,
                "title": "Mock Movie 1",
                "overview": "This is a mock movie overview",
                "poster_path": "/mock_poster.jpg",
                "backdrop_path": "/mock_backdrop.jpg",
                "vote_average": 8.5,
                "release_date": "2024-01-15"
            },
            {
                "id": 67890,
                "title": "Mock Movie 2",
                "overview": "Another mock movie",
                "poster_path": "/mock_poster2.jpg",
                "backdrop_path": "/mock_backdrop2.jpg",
                "vote_average": 7.8,
                "release_date": "2024-02-20"
            }
        ]
    }
    
    mock_top_rated_data = {
        "results": [
            {
                "id": 11111,
                "title": "Top Rated Mock",
                "overview": "A top rated mock movie",
                "poster_path": "/top_poster.jpg",
                "backdrop_path": "/top_backdrop.jpg",
                "vote_average": 9.2,
                "release_date": "2023-12-01"
            }
        ]
    }
    
    # Create a mock response object
    def mock_get(url, params=None, timeout=None):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        if "trending" in url:
            mock_response.json.return_value = mock_trending_data
        elif "top_rated" in url:
            mock_response.json.return_value = mock_top_rated_data
        else:
            mock_response.json.return_value = {"results": []}
        
        return mock_response
    
    # Patch the requests.get function
    with patch('app.requests.get', side_effect=mock_get):
        response = client.get('/')
        
        # Assert status code is 200
        assert response.status_code == 200
        
        # Assert the page contains expected content
        assert b'DevOps Flix' in response.data or b'DEVOPSFLIX' in response.data
        assert b'Trending' in response.data
        assert b'Top Rated' in response.data


# ===== TEST 2: Add to Watchlist Test =====
def test_add_movie_to_watchlist(client):
    """
    Test 2: Add a dummy movie to watchlist and verify the list length increases
    """
    from app import watchlist as wl
    
    # Verify watchlist is initially empty
    initial_length = len(wl)
    assert initial_length == 0
    
    # Dummy movie data
    movie_data = {
        "id": 99999,
        "title": "Test Movie for Watchlist",
        "poster_path": "/test_poster.jpg"
    }
    
    # Add movie to watchlist
    response = client.post(
        '/watchlist/add',
        json=movie_data,
        content_type='application/json'
    )
    
    # Assert the request was successful
    assert response.status_code == 200
    
    response_data = response.get_json()
    assert response_data['success'] == True
    assert response_data['message'] == "Movie added to watchlist"
    
    # Verify watchlist length increased by 1
    assert len(wl) == initial_length + 1
    
    # Verify the movie is in the watchlist with correct data
    assert wl[0]['id'] == 99999
    assert wl[0]['title'] == "Test Movie for Watchlist"
    assert wl[0]['poster_path'] == "/test_poster.jpg"


# ===== TEST 3: Remove from Watchlist Test =====
def test_remove_movie_from_watchlist(client):
    """
    Test 3: Add a movie, then remove it, and verify the watchlist is empty
    """
    from app import watchlist as wl
    
    # First, add a movie
    movie_data = {
        "id": 88888,
        "title": "Movie to Remove",
        "poster_path": "/remove_poster.jpg"
    }
    
    # Add the movie
    add_response = client.post(
        '/watchlist/add',
        json=movie_data,
        content_type='application/json'
    )
    assert add_response.status_code == 200
    
    # Verify movie was added
    assert len(wl) == 1
    
    # Now remove the movie
    remove_response = client.post(
        '/watchlist/remove',
        json={"id": 88888},
        content_type='application/json'
    )
    
    # Assert the removal was successful
    assert remove_response.status_code == 200
    
    response_data = remove_response.get_json()
    assert response_data['success'] == True
    assert response_data['message'] == "Movie removed from watchlist"
    
    # Verify the watchlist is now empty
    assert len(wl) == 0


# ===== ADDITIONAL HELPER TESTS =====

def test_add_duplicate_movie_fails(client):
    """Test that adding a duplicate movie to watchlist fails"""
    from app import watchlist as wl
    
    movie_data = {
        "id": 77777,
        "title": "Duplicate Test Movie",
        "poster_path": "/dup_poster.jpg"
    }
    
    # Add movie first time
    response1 = client.post('/watchlist/add', json=movie_data, content_type='application/json')
    assert response1.status_code == 200
    
    # Try to add same movie again
    response2 = client.post('/watchlist/add', json=movie_data, content_type='application/json')
    assert response2.status_code == 400
    
    response_data = response2.get_json()
    assert response_data['success'] == False
    assert "already in watchlist" in response_data['message']
    
    # Watchlist should still have only 1 movie
    assert len(wl) == 1


def test_remove_nonexistent_movie_fails(client):
    """Test that removing a non-existent movie returns 404"""
    response = client.post(
        '/watchlist/remove',
        json={"id": 99999999},
        content_type='application/json'
    )
    
    assert response.status_code == 404
    
    response_data = response.get_json()
    assert response_data['success'] == False


def test_search_endpoint(client):
    """Test the search endpoint returns proper JSON"""
    mock_search_data = {
        "results": [
            {
                "id": 55555,
                "title": "Searched Movie",
                "poster_path": "/search_poster.jpg",
                "vote_average": 7.5
            }
        ]
    }
    
    def mock_get(url, params=None, timeout=None):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = mock_search_data
        return mock_response
    
    with patch('app.requests.get', side_effect=mock_get):
        response = client.get('/search?q=test')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert len(data['results']) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
