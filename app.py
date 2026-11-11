import os
import sqlite3
import math
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "movies.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/featured")
def get_featured():
    """Returns top trending movies with backdrops for hero banner"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, original_title, overview, release_year, vote_average, 
               vote_count, popularity, poster_path, backdrop_path, genres, tagline
        FROM movies 
        WHERE backdrop_path != '' AND overview != '' AND vote_count > 100
        ORDER BY popularity DESC 
        LIMIT 6
    """)
    rows = cursor.fetchall()
    featured = [dict(row) for row in rows]
    conn.close()
    return jsonify({"featured": featured})

@app.route("/api/movies")
def get_movies():
    """Paginated, filterable, and searchable movie listing"""
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(60, max(12, int(request.args.get("per_page", 24))))
    offset = (page - 1) * per_page
    
    genre = request.args.get("genre", "").strip()
    year = request.args.get("year", "").strip()
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "trending").strip()

    where_clauses = ["poster_path != ''"]
    params = []

    if search:
        where_clauses.append("(title LIKE ? OR original_title LIKE ? OR overview LIKE ?)")
        s_param = f"%{search}%"
        params.extend([s_param, s_param, s_param])

    if genre and genre != "all":
        where_clauses.append("genres LIKE ?")
        params.append(f"%{genre}%")

    if year and year != "all":
        if year == "2026":
            where_clauses.append("release_year = 2026")
        elif year == "2025":
            where_clauses.append("release_year = 2025")
        elif year == "2024":
            where_clauses.append("release_year = 2024")
        elif year == "2023":
            where_clauses.append("release_year = 2023")
        elif year == "2020s":
            where_clauses.append("release_year >= 2020 AND release_year <= 2026")
        elif year == "2010s":
            where_clauses.append("release_year >= 2010 AND release_year < 2020")
        elif year == "2000s":
            where_clauses.append("release_year >= 2000 AND release_year < 2010")
        elif year == "classic":
            where_clauses.append("release_year < 2000 AND release_year > 1900")
        elif year.isdigit():
            where_clauses.append("release_year = ?")
            params.append(int(year))

    # Sorting
    if sort_by == "rating":
        # Filter minimum votes to avoid 1-vote skew
        where_clauses.append("vote_count >= 100")
        order_by = "vote_average DESC, vote_count DESC"
    elif sort_by == "newest":
        order_by = "release_year DESC, release_date DESC, popularity DESC"
    elif sort_by == "votes":
        order_by = "vote_count DESC"
    elif sort_by == "title":
        order_by = "title COLLATE NOCASE ASC"
    else:  # trending
        order_by = "popularity DESC, vote_average DESC"

    where_sql = " AND ".join(where_clauses)

    conn = get_db()
    cursor = conn.cursor()

    # Count total
    count_query = f"SELECT COUNT(*) FROM movies WHERE {where_sql}"
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Query items
    query = f"""
        SELECT id, title, original_title, overview, release_year, release_date,
               vote_average, vote_count, popularity, poster_path, backdrop_path, 
               genres, runtime, original_language
        FROM movies 
        WHERE {where_sql}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, params + [per_page, offset])
    rows = cursor.fetchall()
    movies = [dict(row) for row in rows]
    conn.close()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return jsonify({
        "movies": movies,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    })

@app.route("/api/movie/<int:movie_id>")
def get_movie_detail(movie_id):
    """Returns single movie full detail"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Kino topilmadi"}), 404

    movie = dict(row)
    
    # Format runtime (e.g. 148 -> "2s 28m")
    rt = movie.get("runtime") or 0
    if rt > 0:
        hours = rt // 60
        mins = rt % 60
        movie["formatted_runtime"] = f"{hours}s {mins}m" if hours > 0 else f"{mins}m"
    else:
        movie["formatted_runtime"] = "Noma'lum"

    # Format budget and revenue
    b = movie.get("budget") or 0
    r = movie.get("revenue") or 0
    movie["formatted_budget"] = f"${b:,}" if b > 0 else "Noma'lum"
    movie["formatted_revenue"] = f"${r:,}" if r > 0 else "Noma'lum"

    # YouTube trailer search query
    query_title = movie["title"].replace(" ", "+")
    year = movie.get("release_year") or ""
    movie["trailer_url"] = f"https://www.youtube.com/results?search_query={query_title}+{year}+official+trailer"
    movie["imdb_url"] = f"https://www.imdb.com/title/{movie['imdb_id']}" if movie.get("imdb_id") else None

    # Similar movies based on primary genre
    first_genre = movie["genres"].split(",")[0].strip() if movie.get("genres") else ""
    similar = []
    if first_genre:
        cursor.execute("""
            SELECT id, title, release_year, vote_average, poster_path, genres
            FROM movies
            WHERE id != ? AND genres LIKE ? AND poster_path != '' AND vote_count > 50
            ORDER BY popularity DESC
            LIMIT 4
        """, (movie_id, f"%{first_genre}%"))
        similar = [dict(s) for s in cursor.fetchall()]

    movie["similar_movies"] = similar
    conn.close()

    return jsonify(movie)

@app.route("/api/analytics")
def get_analytics():
    """Returns aggregated data for interactive charts and dataset analysis"""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Top 8 Box Office (Revenue)
    cursor.execute("""
        SELECT title, release_year, revenue, budget, vote_average
        FROM movies
        WHERE revenue > 100000000
        ORDER BY revenue DESC
        LIMIT 8
    """)
    top_revenue = [dict(r) for r in cursor.fetchall()]

    # 2. Yearly film counts (2005 - 2026)
    cursor.execute("""
        SELECT release_year, COUNT(*) as count
        FROM movies
        WHERE release_year >= 2005 AND release_year <= 2026
        GROUP BY release_year
        ORDER BY release_year ASC
    """)
    yearly = [dict(r) for r in cursor.fetchall()]

    # 3. Top Genres count
    popular_genres = [
        "Action", "Comedy", "Drama", "Science Fiction", 
        "Thriller", "Horror", "Adventure", "Animation", "Romance"
    ]
    genre_counts = []
    for g in popular_genres:
        cursor.execute("SELECT COUNT(*) FROM movies WHERE genres LIKE ?", (f"%{g}%",))
        genre_counts.append({"genre": g, "count": cursor.fetchone()[0]})
    genre_counts.sort(key=lambda x: x["count"], reverse=True)

    # 4. Rating distribution
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN vote_average >= 8.0 THEN 1 ELSE 0 END) as rate_8_10,
            SUM(CASE WHEN vote_average >= 7.0 AND vote_average < 8.0 THEN 1 ELSE 0 END) as rate_7_8,
            SUM(CASE WHEN vote_average >= 6.0 AND vote_average < 7.0 THEN 1 ELSE 0 END) as rate_6_7,
            SUM(CASE WHEN vote_average >= 5.0 AND vote_average < 6.0 THEN 1 ELSE 0 END) as rate_5_6,
            SUM(CASE WHEN vote_average < 5.0 THEN 1 ELSE 0 END) as rate_below_5
        FROM movies
        WHERE vote_count >= 50
    """)
    row = cursor.fetchone()
    rating_distribution = {
        "8.0 - 10.0 (A'lo)": row[0] or 0,
        "7.0 - 7.9 (Yaxshi)": row[1] or 0,
        "6.0 - 6.9 (O'rtacha)": row[2] or 0,
        "5.0 - 5.9 (Qoniqarli)": row[3] or 0,
        "0.0 - 4.9 (Past)": row[4] or 0
    }

    conn.close()

    return jsonify({
        "top_revenue": top_revenue,
        "yearly_trend": yearly,
        "genre_distribution": genre_counts,
        "rating_distribution": rating_distribution
    })

@app.route("/api/genres")
def get_genres():
    """Returns list of popular movie genres with counts"""
    genres_list = [
        {"id": "Action", "name": "Jangari", "en": "Action", "icon": "💥"},
        {"id": "Adventure", "name": "Sarguzasht", "en": "Adventure", "icon": "🧭"},
        {"id": "Animation", "name": "Animatsiya", "en": "Animation", "icon": "🎨"},
        {"id": "Comedy", "name": "Komediya", "en": "Comedy", "icon": "😂"},
        {"id": "Crime", "name": "Jinoyat", "en": "Crime", "icon": "🕵️"},
        {"id": "Drama", "name": "Drama", "en": "Drama", "icon": "🎭"},
        {"id": "Family", "name": "Oilaviy", "en": "Family", "icon": "👨‍👩‍👧"},
        {"id": "Fantasy", "name": "Fantastika", "en": "Fantasy", "icon": "🧙‍♂️"},
        {"id": "History", "name": "Tarixiy", "en": "History", "icon": "📜"},
        {"id": "Horror", "name": "Qo'rqinchli", "en": "Horror", "icon": "👻"},
        {"id": "Music", "name": "Musiqa", "en": "Music", "icon": "🎵"},
        {"id": "Mystery", "name": "Detektiv", "en": "Mystery", "icon": "🔍"},
        {"id": "Romance", "name": "Romantika", "en": "Romance", "icon": "💖"},
        {"id": "Science Fiction", "name": "Ilmiy-fantastik", "en": "Sci-Fi", "icon": "🚀"},
        {"id": "Thriller", "name": "Triller", "en": "Thriller", "icon": "⚡"},
        {"id": "War", "name": "Harbiy", "en": "War", "icon": "⚔️"},
        {"id": "Western", "name": "Vestern", "en": "Western", "icon": "🤠"}
    ]
    return jsonify({"genres": genres_list})

@app.route("/api/stats")
def get_stats():
    """Returns general database stats"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    total_movies = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(release_year), MAX(release_year) FROM movies WHERE release_year > 1900")
    min_year, max_year = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM movies WHERE release_year >= 2024")
    upcoming_count = cursor.fetchone()[0]

    conn.close()
    return jsonify({
        "total_movies": total_movies,
        "year_range": f"{min_year} - {max_year}",
        "new_and_upcoming": upcoming_count
    })

if __name__ == "__main__":
    print("🎬 'Jahon Kinolari' serveri ishga tushmoqda...")
    print("📍 Manzil: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

