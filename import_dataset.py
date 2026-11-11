"""
🎬 Jahon Kinolari — Kagglehub Dataset Import Skripti

Foydalanuvchi so'rovi bo'yicha Kaggle'dan datasetni yuklab oluvchi va
sayt uchun SQLite bazasiga tayyorlab beruvchi modul.
"""

import os
import sys
import glob
import sqlite3
import kagglehub
import pandas as pd

def download_and_import():
    print("=" * 60)
    print("📥 Kaggle'dan kinolar datasetini yuklab olish boshlandi...")
    print("=" * 60)
    
    target_dataset = "sahilk22/trending-movies-analysis-up-to-2026"
    path = None
    
    try:
        print(f"1. So'ralgan dataset tekshirilmoqda: '{target_dataset}'")
        path = kagglehub.dataset_download(target_dataset)
        print("Path to dataset files:", path)
    except Exception as e:
        print(f"⚠️ '{target_dataset}' ni yuklashda xatolik yuz berdi: {e}")
    
    # Check if files exist in that directory
    files = os.listdir(path) if (path and os.path.exists(path)) else []
    csv_files = [os.path.join(path, f) for f in files if f.endswith('.csv')] if path else []
    
    # If the user-specified dataset is empty (Kaggle returns 22 bytes empty zip for sahilk22 currently)
    if not csv_files:
        print("\nℹ️ Izoh: 'sahilk22/trending-movies-analysis-up-to-2026' Kaggle'da hozirda bo'sh (22 bayt).")
        print("🔄 Muqobil sifatida TMDB dunyo kinolari datasetidan (930,000+ film) foydalanamiz...")
        
        # Check cache or download TMDB
        cache_csvs = glob.glob(r'C:\Users\User\.cache\kagglehub\datasets\**\*.csv', recursive=True)
        if cache_csvs:
            csv_path = cache_csvs[0]
            print(f"✅ Keshdan topildi: {csv_path}")
        else:
            print("Kaggle'dan TMDB dataset yuklanmoqda...")
            tmdb_path = kagglehub.dataset_download("asaniczka/tmdb-movies-dataset-2023-930k-movies")
            csv_path = os.path.join(tmdb_path, "TMDB_movie_dataset_v11.csv")
    else:
        csv_path = csv_files[0]
        print(f"✅ CSV fayli topildi: {csv_path}")

    # Build database
    print("\n📦 SQLite ma'lumotlar bazasi (movies.db) yaratilmoqda...")
    db_path = os.path.join(os.getcwd(), "movies.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
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
    
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"ℹ️ Bazada allaqachon {count} ta film mavjud.")
        conn.close()
        return

    cols = ['id', 'title', 'vote_average', 'vote_count', 'release_date',
            'revenue', 'runtime', 'adult', 'backdrop_path', 'budget', 'imdb_id',
            'original_language', 'original_title', 'overview', 'popularity',
            'poster_path', 'tagline', 'genres', 'production_countries']

    total_inserted = 0
    for chunk in pd.read_csv(csv_path, usecols=cols, chunksize=50000, low_memory=False):
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
            
        filtered = filtered.drop(columns=['adult'])
        filtered['release_date'] = filtered['release_date'].fillna('')
        filtered['release_year'] = pd.to_datetime(filtered['release_date'], errors='coerce').dt.year.fillna(0).astype(int)
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

        filtered.to_sql('movies', conn, if_exists='append', index=False)
        total_inserted += len(filtered)
        print(f"Yuklandi: {total_inserted} ta film...")

    print("Indexlar optimallashmoqda...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_popularity ON movies (popularity DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vote_average ON movies (vote_average DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_release_year ON movies (release_year DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON movies (title COLLATE NOCASE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_genres ON movies (genres);")
    
    conn.commit()
    conn.close()
    print(f"🎉 Muvaffaqiyatli yakunlandi! Jami {total_inserted} ta film bazaga kiritildi.")

if __name__ == "__main__":
    download_and_import()

