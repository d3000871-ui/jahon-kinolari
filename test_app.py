from app import app

def run_tests():
    client = app.test_client()

    # 1. Test index page
    r = client.get('/')
    assert r.status_code == 200, f'Status {r.status_code}'
    assert b'Jahon Kinolari' in r.data, 'Missing title'
    print('[PASS] Index page rendered successfully (200 OK)')

    # 2. Test static CSS & JS
    r_css = client.get('/static/css/style.css')
    assert r_css.status_code == 200, f'CSS Status {r_css.status_code}'
    print('[PASS] Static style.css loaded successfully (200 OK)')

    r_js = client.get('/static/js/app.js')
    assert r_js.status_code == 200, f'JS Status {r_js.status_code}'
    print('[PASS] Static app.js loaded successfully (200 OK)')

    # 3. Test API featured
    r_feat = client.get('/api/featured')
    assert r_feat.status_code == 200
    feat_count = len(r_feat.json['featured'])
    assert feat_count > 0
    print(f'[PASS] /api/featured returned {feat_count} movies')

    # 4. Test API movies with filtering & search
    r_search = client.get('/api/movies?search=Inception')
    assert r_search.status_code == 200
    total = r_search.json['total']
    assert total >= 1
    print(f'[PASS] /api/movies?search=Inception returned {total} matches')

    # 5. Test single movie detail
    first_id = r_search.json['movies'][0]['id']
    r_detail = client.get(f'/api/movie/{first_id}')
    assert r_detail.status_code == 200
    print(f'[PASS] /api/movie/{first_id} -> {r_detail.json["title"]}, Runtime: {r_detail.json["formatted_runtime"]}')

    # 6. Test genres
    r_genres = client.get('/api/genres')
    assert r_genres.status_code == 200
    print(f'[PASS] /api/genres returned {len(r_genres.json["genres"])} genres')

    # 7. Test stats
    r_stats = client.get('/api/stats')
    assert r_stats.status_code == 200
    print(f'[PASS] /api/stats -> Total: {r_stats.json["total_movies"]}, Range: {r_stats.json["year_range"]}')
    print('\nAll tests passed successfully!')

if __name__ == '__main__':
    run_tests()

