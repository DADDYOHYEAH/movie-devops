"""
DevOps Flix - Netflix Clone Web Application
Flask backend with TMDB API integration and watchlist functionality
"""

from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# TMDB API Configuration
# Replace with your actual TMDB API key
TMDB_API_KEY = "c98a3689e4042e45c726454885e21739"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# In-memory watchlist storage
watchlist = []


def fetch_trending_movies():
    """Fetch trending movies of the week from TMDB API"""
    url = f"{TMDB_BASE_URL}/trending/movie/week"
    params = {"api_key": TMDB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException:
        return []


def fetch_top_rated_movies():
    """Fetch top rated movies from TMDB API"""
    url = f"{TMDB_BASE_URL}/movie/top_rated"
    params = {"api_key": TMDB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException:
        return []


def search_movies(query):
    """Search movies by query from TMDB API"""
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException:
        return []


def fetch_movie_details(movie_id):
    """Fetch detailed movie info including cast and crew"""
    # Get movie details
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "append_to_response": "credits"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant info
        movie_details = {
            "id": data.get("id"),
            "title": data.get("title"),
            "overview": data.get("overview"),
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "release_date": data.get("release_date"),
            "runtime": data.get("runtime"),
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "tagline": data.get("tagline"),
            "status": data.get("status"),
            "budget": data.get("budget"),
            "revenue": data.get("revenue"),
        }
        
        # Get cast (top 10)
        credits = data.get("credits", {})
        cast = credits.get("cast", [])[:10]
        movie_details["cast"] = [{
            "name": c.get("name"),
            "character": c.get("character"),
            "profile_path": c.get("profile_path")
        } for c in cast]
        
        # Get crew (directors, writers)
        crew = credits.get("crew", [])
        directors = [c for c in crew if c.get("job") == "Director"]
        writers = [c for c in crew if c.get("department") == "Writing"][:3]
        movie_details["directors"] = [{"name": d.get("name")} for d in directors]
        movie_details["writers"] = [{"name": w.get("name"), "job": w.get("job")} for w in writers]
        
        return movie_details
    except requests.RequestException:
        return None


@app.route("/")
def index():
    """Main page with trending, top rated movies and watchlist"""
    trending = fetch_trending_movies()
    top_rated = fetch_top_rated_movies()
    
    # Select a featured movie for the hero banner (first trending movie)
    hero_movie = trending[0] if trending else None
    
    return render_template(
        "index.html",
        trending=trending,
        top_rated=top_rated,
        watchlist=watchlist,
        hero_movie=hero_movie,
        image_base=TMDB_IMAGE_BASE
    )


@app.route("/search")
def search_page():
    """Render the dedicated search page"""
    trending = fetch_trending_movies()
    return render_template(
        "search.html",
        trending=trending,
        image_base=TMDB_IMAGE_BASE
    )

@app.route("/api/search")
def search():
    """Search endpoint for querying movies"""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"results": []})
    
    results = search_movies(query)
    return jsonify({"results": results, "image_base": TMDB_IMAGE_BASE})


@app.route("/movie/<int:movie_id>")
def get_movie_details(movie_id):
    """Get detailed movie information including cast and crew"""
    details = fetch_movie_details(movie_id)
    if details:
        return jsonify({"success": True, "movie": details, "image_base": TMDB_IMAGE_BASE})
    return jsonify({"success": False, "message": "Movie not found"}), 404


@app.route("/watchlist/add", methods=["POST"])
def add_to_watchlist():
    """Add a movie to the watchlist"""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    movie_id = data.get("id")
    title = data.get("title")
    poster_path = data.get("poster_path")
    
    if not all([movie_id, title]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Check if movie already in watchlist
    for movie in watchlist:
        if movie["id"] == movie_id:
            return jsonify({"success": False, "message": "Movie already in watchlist"}), 400
    
    movie_entry = {
        "id": movie_id,
        "title": title,
        "poster_path": poster_path
    }
    watchlist.append(movie_entry)
    
    return jsonify({"success": True, "message": "Movie added to watchlist", "watchlist": watchlist})


@app.route("/watchlist/remove", methods=["POST"])
def remove_from_watchlist():
    """Remove a movie from the watchlist"""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    movie_id = data.get("id")
    
    if not movie_id:
        return jsonify({"success": False, "message": "Movie ID required"}), 400
    
    original_length = len(watchlist)
    # Find and remove the movie in place (don't reassign the list)
    for i, movie in enumerate(watchlist):
        if movie["id"] == movie_id:
            watchlist.pop(i)
            break
    
    if len(watchlist) == original_length:
        return jsonify({"success": False, "message": "Movie not found in watchlist"}), 404
    
    return jsonify({"success": True, "message": "Movie removed from watchlist", "watchlist": watchlist})


@app.route("/watchlist")
def get_watchlist():
    """Get current watchlist"""
    return jsonify({"watchlist": watchlist})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
