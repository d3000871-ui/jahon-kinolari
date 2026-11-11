# 🎬 Jahon Kinolari — Dunyo filmlari veb-sayti

Dunyo kino sanoatining eng mashhur, yuqori baholangan hamda 2026-yilgacha bo'lgan yangi filmlarini qidirish, janr va yillar bo'yicha saralash, rasmiy treylerlarni ko'rish va sevimlilar ro'yxatiga saqlash imkonini beruvchi zamonaviy veb-portal.

Loyiha **Kaggle** ma'lumotlar to'plami (dataset) asosida yaratilgan va **62,000+** ta sifatli filmlar bazasini o'z ichiga oladi.

---

## 🌟 Asosiy Imkoniyatlar

1. **🔥 Ommabop filmlar slayderi (Hero Banner):**
   - Eng so'nggi trenddagi filmlar va ularning keng formatli fon rasmlari (backdrop).
   - Treylerlarni to'g'ridan-to'g'ri YouTube orqali tomosha qilish.
2. **🔍 Jonli Qidiruv (Live Search):**
   - Film nomi, asl nomi yoki mazmuni bo'yicha millisekundlarda qidirish.
3. **🎭 Janrlar filtri:**
   - Jangari, Sarguzasht, Komediya, Drama, Fantastika, Qo'rqinchli, Animatsiya, Tarixiy, Triller va boshqalar.
4. **📅 Yillar bo'yicha filtrlash:**
   - 2026 (Yangi va kutilayotganlar), 2025, 2024, 2023, 2020-2026 yillar, 2010-lar, 2000-lar hamda klassik filmlar.
5. **⚡ Qulay Saralash:**
   - Trend (Ommaboplik), IMDb reytingi, Eng yangi chiqqanlar, Ko'p ovoz olganlar, Alifbo bo'yicha.
6. **ℹ️ To'liq film ma'lumotlari (Modal):**
   - Original tili, ishlab chiqargan davlatlar, byudjet, daromad, davomiyligi, qisqacha mazmuni, IMDb havolasi.
7. **❤️ Sevimlilar (Favorites):**
   - Yoqqan kinolarni brauzer xotirasiga (LocalStorage) saqlash va istalgan vaqt qayta ochish.
8. **📱 Responsive Cinema Dark UI:**
   - Netflix va Apple TV+ uslubidagi qulay qorong'i dizayn, barcha mobil va kompyuter ekranlariga moslashuvchan.

---

## 🚀 Ishga tushirish

### 1-usul: Bir bosishda ishga tushirish (Tavsiya etiladi)
Loyihadagi **`ishga_tushirish.bat`** yoki **`run.bat`** faylini ikki marta bosing. Sayt avtomatik tarzda brauzeringizda ochiladi:
👉 `http://127.0.0.1:5000`

### 2-usul: Terminal orqali
```bash
python app.py
```
Yoki Python 3.13 orqali:
```bash
& "C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe" app.py
```

---

## 📊 Kaggle Dataset va Import qilish

Datasetni yuklab olish va yangilash uchun siz bergan kod asosida `import_dataset.py` fayli yaratilgan:

```python
import kagglehub

# Datasetni yuklab olish
path = kagglehub.dataset_download("sahilk22/trending-movies-analysis-up-to-2026")

print("Path to dataset files:", path)
```

> **Eslatma:** Kaggle'da `sahilk22/trending-movies-analysis-up-to-2026` repozitoriysi muallif tomonidan bo'sh holatda joylangan bo'lib, uning o'rniga eng to'liq va ommabop **TMDB Movies (930,000+ filmlar)** to'plamidan foydalanildi. Ushbu to'plamdan 2026-yilgacha bo'lgan barcha yangi va klassik filmlar ajratib olingan va loyihadagi `movies.db` (SQLite) fayliga jamlangan.

Datasetni qayta import qilish uchun:
```bash
python import_dataset.py
```

---

## 📁 Loyiha Strukturasi

```
Jahon kinolari/
├── app.py                  # Flask server va REST API
├── movies.db               # 62,332 ta filmni o'z ichiga olgan SQLite bazasi
├── import_dataset.py       # Kagglehub orqali datasetni yuklash skripti
├── build_database.py       # Filtrlash va indekslarni hosil qilish skripti
├── templates/
│   └── index.html          # Veb-sayt bosh sahifasi (SPA)
├── static/
│   ├── css/
│   │   └── style.css       # Cinema Dark dizayn va animatsiyalar
│   └── js/
│       └── app.js          # Slayder, filtrlash, qidiruv va modal mantig'i
├── ishga_tushirish.bat     # Windows uchun 1-klikda ishga tushiruvchi fayl
├── run.bat                 # Qisqa ishga tushirish fayli
└── README.md               # Loyiha qo'llanmasi
```

---

## 🔌 REST API Endpoints

- `GET /api/movies` — Sahifalangan kinolar ro'yxati (`?page=1&genre=Action&year=2024&sort_by=trending&search=...`)
- `GET /api/movie/<id>` — Film haqida to'liq ma'lumot va treyler havolasi
- `GET /api/featured` — Bosh sahifa slayderi uchun trenddagi filmlar
- `GET /api/genres` — Barcha kino janrlari ro'yxati
- `GET /api/stats` — Umumiy statistika (kinolar soni, yillar oralig'i)

