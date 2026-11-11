import os
import glob
import sqlite3
import pandas as pd

def build_db():
    print("Looking for downloaded dataset...")
    # Find CSV in kaggle cache or local data directory
    csv_files = glob.glob(r'C:\Users\User\.cache\kagglehub\datasets\**\*.csv', recursive=True)
    if not csv_files:
        local_csvs = glob.glob(r'data\*.csv')
        csv_files = local_csvs
    
    if not csv_files:
        raise FileNotFoundError("CSV dataset file not found!")
    
    csv_file = csv_files[0]
    print(f"Reading from: {csv_file}")
    
    db_path = os.path.join(os.getcwd(), "movies.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE movies (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        original_title TEXT,
        overview TEXT,
        release_date TEXT,
        release_year INTEGER,
        vote_average REAL,
        vote_count INTEGER,
        popularity REAL,
        runtime INTEGER,
        budget INTEGER,
        revenue INTEGER,
        original_language TEXT,
        poster_path TEXT,
        backdrop_path TEXT,
        genres TEXT,
        production_countries TEXT,
        imdb_id TEXT,
        tagline TEXT
    );
    """)
    
    cols = ['id', 'title', 'vote_average', 'vote_count', 'release_date',
            'revenue', 'runtime', 'adult', 'backdrop_path', 'budget', 'imdb_id',
            'original_language', 'original_title', 'overview', 'popularity',
            'poster_path', 'tagline', 'genres', 'production_countries']
    
    total_inserted = 0
    print("Processing and filtering movie records...")
    for chunk in pd.read_csv(csv_file, usecols=cols, chunksize=50000, low_memory=False):
        # Filter condition: must have poster, title, and adult == False
        cond = (
            chunk['poster_path'].notna() &
            chunk['title'].notna() &
            (chunk['adult'] == False) &
            (
                (chunk['vote_count'] >= 15) |
                ((chunk['release_date'].astype(str) >= '2023') & (chunk['popularity'] >= 5)) |
                (chunk['popularity'] >= 15)
            )
        )
        filtered = chunk[cond].copy()
        if len(filtered) == 0:
            continue
            
        # Clean data
        filtered = filtered.drop(columns=['adult'])
        filtered['release_date'] = filtered['release_date'].fillna('')
        filtered['release_year'] = pd.to_datetime(filtered['release_date'], errors='coerce').dt.year.fillna(0).astype(int)
        
        # Keep release years up to 2026 and positive
        filtered = filtered[(filtered['release_year'] <= 2026) | (filtered['release_year'] == 0)]
        filtered['vote_average'] = filtered['vote_average'].fillna(0.0).round(1)
        filtered['vote_count'] = filtered['vote_count'].fillna(0).astype(int)
        filtered['popularity'] = filtered['popularity'].fillna(0.0).round(2)
        filtered['runtime'] = filtered['runtime'].fillna(0).astype(int)
        filtered['budget'] = filtered['budget'].fillna(0).astype(int)
        filtered['revenue'] = filtered['revenue'].fillna(0).astype(int)
        filtered['original_language'] = filtered['original_language'].fillna('en')
        filtered['genres'] = filtered['genres'].fillna('')
        filtered['overview'] = filtered['overview'].fillna('')
        filtered['tagline'] = filtered['tagline'].fillna('')
        filtered['production_countries'] = filtered['production_countries'].fillna('')
        filtered['imdb_id'] = filtered['imdb_id'].fillna('')
        filtered['backdrop_path'] = filtered['backdrop_path'].fillna('')
        filtered['original_title'] = filtered['original_title'].fillna('')

        # Insert into sqlite
        filtered.to_sql('movies', conn, if_exists='append', index=False)
        total_inserted += len(filtered)
        print(f"Inserted {total_inserted} movies so far...")
    
    print("Creating indexes for ultra-fast queries...")
    cursor.execute("CREATE INDEX idx_popularity ON movies (popularity DESC);")
    cursor.execute("CREATE INDEX idx_vote_average ON movies (vote_average DESC);")
    cursor.execute("CREATE INDEX idx_release_year ON movies (release_year DESC);")
    cursor.execute("CREATE INDEX idx_title ON movies (title COLLATE NOCASE);")
    cursor.execute("CREATE INDEX idx_genres ON movies (genres);")
    
    conn.commit()
    conn.close()
    print(f"Database successfully created with {total_inserted} movies at {db_path}!")

if __name__ == '__main__':
    build_db()
